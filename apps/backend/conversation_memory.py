"""Conversation → memory write policy (Milestone 2.4).

Pure heuristics + record construction. This module has NO I/O and NO persistence:
it never imports memory, sqlite, lancedb, or any service. It answers two questions —
"is this message worth remembering?" and "how should it be tagged?" — and the
composition root (nova.py) performs the actual `memory.remember()` write.

That split is deliberate and load-bearing:

  * Deciding a greeting isn't worth keeping is *interpretation*, which Memory's
    charter forbids it from doing — so the judgment can't live in memory/.
  * Persistence is Memory's alone, and the milestone says the root (not Brain)
    decides the write — so the write can't live here either.

So this file holds only the judgment, as side-effect-free functions that are
trivially unit-testable without a database. Duplicate suppression is NOT done
here: identical text is left for `memory.remember()`'s existing content-hash
dedup to collapse (the milestone's "reuse, don't reinvent" rule).
"""

import re
from datetime import datetime, timezone

from identity import ASSISTANT_NAME

SOURCE_TYPE = "conversation"

# A user turn can be a short-but-real question ("who is priya"); an assistant
# turn worth keeping is a genuine answer, and the assistant's own system prompt
# tells it to answer in 2–4 sentences, so a substantive reply is comfortably
# long. Tool confirmations ("Task logged.") and acks ("Got it.") fall below
# this — which is exactly how we drop them without enumerating every
# confirmation string.
MIN_WORDS_USER = 3
MIN_WORDS_ASSISTANT = 6

# Exact-match throwaways (either speaker). Normalised (lowercased, ws-collapsed).
# Name-addressed variants ("hi nova") are derived from the configured identity
# so they survive any future rename; "rai" spellings kept for old transcripts.
_NAME_VARIANTS = (ASSISTANT_NAME.lower(), "rai")
_GREETINGS = frozenset(
    {
        "hi",
        "hii",
        "hey",
        "yo",
        "sup",
        "hello",
        "hello there",
        "good morning",
        "good afternoon",
        "good evening",
        "good night",
        "morning",
        "evening",
        "night",
        "thanks",
        "thank you",
        "thx",
        "ty",
        "ok",
        "okay",
        "k",
        "cool",
        "nice",
        "great",
        "awesome",
        "bye",
        "goodbye",
        "see you",
        "see ya",
        "later",
        "how are you",
        "how's it going",
        "hows it going",
        "what's up",
        "whats up",
        "test",
        "testing",
    }
    | {
        f"{greeting} {name}"
        for name in _NAME_VARIANTS
        for greeting in ("hi", "hey", "hello", "thanks", "thank you")
    }
)

# User utterances that are *commands* (already captured as structured rows by the
# tool that handles them) — storing them again as "conversation" is redundant
# noise. Prefix match on the normalised text. NB: "remember …" is deliberately
# absent — "remember my sister is allergic to peanuts" IS the fact to keep.
_USER_COMMAND_PREFIXES = (
    "log ",
    "add ",
    "open ",
    "launch ",
    "start ",
    "stop ",
    "play ",
    "pause ",
    "send ",
    "text ",
    "message ",
    "whatsapp ",
    "remind me",
    "set a reminder",
    "delete ",
    "remove ",
    "mark ",
    "complete ",
    "task done",
    "create event",
    "add event",
    "ship ",
    "sold ",
    "read my day",
    "what's my day",
)

# Longer assistant acks that clear the word floor but carry no memory value.
_ASSISTANT_ACK_PREFIXES = (
    "sure",
    "okay",
    "ok ",
    "got it",
    "no problem",
    "of course",
    "will do",
    "noted",
    "happy to",
    "you're welcome",
    "youre welcome",
    "done",
    "task ",
    "logged ",
    "reminder ",
    "progress ",
    "no matching",
)

_WS = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _WS.sub(" ", text.strip().lower())


def _word_count(norm: str) -> int:
    return len(norm.split()) if norm else 0


def should_remember_user(text: str) -> bool:
    """True if a user message carries lasting signal (a question, fact, or preference)."""
    norm = _normalize(text)
    if not norm or norm in _GREETINGS:
        return False
    if any(norm.startswith(p) for p in _USER_COMMAND_PREFIXES):
        return False
    return _word_count(norm) >= MIN_WORDS_USER


def should_remember_assistant(text: str) -> bool:
    """True if an assistant reply is a substantive answer, not a confirmation/ack."""
    norm = _normalize(text)
    if not norm or norm in _GREETINGS:
        return False
    if any(norm.startswith(p) for p in _ASSISTANT_ACK_PREFIXES):
        return False
    return _word_count(norm) >= MIN_WORDS_ASSISTANT


def _record(text: str, speaker: str, conversation_id: str | None, timestamp: str) -> dict:
    """Build the kwargs for one memory.remember() call. Metadata is EXACTLY the
    three fields the milestone allows — timestamp, conversation_id, speaker."""
    return {
        "text": text.strip(),
        "source_type": SOURCE_TYPE,
        "source_id": conversation_id,
        "metadata": {
            "timestamp": timestamp,
            "conversation_id": conversation_id,
            "speaker": speaker,
        },
    }


def memories_from_exchange(
    user_text: str,
    assistant_text: str,
    conversation_id: str | None = None,
    now: datetime | None = None,
) -> list[dict]:
    """Turn one (user, assistant) exchange into 0–2 memory-write records.

    Each surviving message becomes its own record with a `speaker` tag, so recall
    can later match on either the question or the answer. Returns records only;
    the caller passes each to `memory.remember(**record)`.

    The assistant turn is gated on the *exchange* being memory-worthy, not just on
    its own length: a reply to a greeting ("Hello! How can I help?") is small talk
    however long it runs, so if the user turn was a greeting/command/trivial, the
    whole exchange is dropped. This is what keeps pleasantries out without having
    to enumerate every possible greeting-response.
    """
    timestamp = (now or datetime.now(timezone.utc)).isoformat()
    user_worthy = should_remember_user(user_text)

    records: list[dict] = []
    if user_worthy:
        records.append(_record(user_text, "user", conversation_id, timestamp))
    if user_worthy and should_remember_assistant(assistant_text):
        records.append(_record(assistant_text, "assistant", conversation_id, timestamp))
    return records
