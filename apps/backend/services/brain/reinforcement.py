"""Reinforcement — the second half of the recall loop (ARCHITECTURE_v2 §3).

The Context Engine decides which memories *enter* a turn. This module
decides which of them *earned* the turn, and tells Memory so via its public
`record_access()`. The rule the whole memory-scoring model depends on:

    recall() returning a memory is NOT a use.
    A memory is used only if it survives into the final response.

So reinforcement runs *after* the reply exists, and reinforces a recalled memory
only when the reply is lexically grounded in it — enough of the memory's
significant words actually reappear in what the assistant said. This is a local, cheap
proxy for "the model leaned on this memory"; it needs no second Claude call and
adds nothing to the prompt (the "no prompt explosion" constraint). Its failure
modes (a heavy paraphrase that shares no words → under-credit; an incidental
word overlap → over-credit) are tuning noise on a signal that is itself only a
prior, and are far safer than the forbidden alternative of crediting everything
recall() returned.

Brain still only touches Memory through public verbs: recall() (in prompts.py)
and record_access() (here). No vectors, no ranking, no ledger.
"""

import re

from memory import record_access

from .config import MEMORY_REINFORCE_MIN_OVERLAP

# Function words carry no grounding signal — a reply and a memory sharing "the"
# or "a" says nothing about whether the memory was used. Kept small on purpose;
# this is a stop-list, not a linguistics project.
_STOPWORDS = frozenset("""
a an and are as at be but by for from has have he her him his i in is it its me my
of on or our she that the their them they this to was we were what when where which
who will with you your do does did not no yes if so then than too very can could would
should i'm it's that's is am me my mine ours yours
""".split())

_WORD_RE = re.compile(r"[a-z0-9']+")


def _significant_words(text: str) -> set[str]:
    """Content words of `text`, lowercased, stop-words and 1-char tokens dropped."""
    return {
        w for w in _WORD_RE.findall(text.lower())
        if len(w) > 1 and w not in _STOPWORDS
    }


def _grounding_overlap(memory_text: str, reply_words: set[str]) -> float:
    """Fraction of a memory's significant words that appear in the reply, [0, 1]."""
    mem_words = _significant_words(memory_text)
    if not mem_words:
        return 0.0
    return len(mem_words & reply_words) / len(mem_words)


def grounded_memory_ids(reply: str, memories: list[dict]) -> list[str]:
    """The subset of injected `memories` that are grounded in `reply`. Pure."""
    if not reply or not memories:
        return []
    reply_words = _significant_words(reply)
    if not reply_words:
        return []
    return [
        m["id"]
        for m in memories
        if _grounding_overlap(m["text"], reply_words) >= MEMORY_REINFORCE_MIN_OVERLAP
    ]


def reinforce(reply: str, memories: list[dict]) -> list[str]:
    """Reinforce the memories that survived into `reply`. Returns the ids bumped.

    `memories` must be exactly the list injected into the prompt for this turn
    (from AssembledContext.memories) — never the raw recall() candidates, or dropped
    near-misses would be rewarded. Reinforcement never breaks a turn: a failure
    to record is logged and swallowed, because the reply has already been made.
    """
    ids = grounded_memory_ids(reply, memories)
    if not ids:
        return []
    try:
        record_access(ids)
    except Exception as exc:
        print(f"[reinforcement] skipped: {exc}")
        return []
    return ids
