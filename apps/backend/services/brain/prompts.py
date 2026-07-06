"""System-prompt formatting — and nothing else (Milestone 2.8).

Context selection, ranking, token budgets, dedup, and ordering all live in
context_engine/; this module renders the sections the engine already decided
on into the final system string. It imports no Memory verbs and makes no
judgments — if a change here alters *what* Claude knows rather than how it
reads, the change belongs in the engine instead.

The frame is unchanged from Phase 1: identity + clock header, titled context
sections, spoken-style footer. Sections render as "{title}:\n{body}", joined
by blank lines, in exactly the order the engine handed them over.
"""

from datetime import datetime

from identity import ASSISTANT_NAME

from .config import REPLY_LANGUAGE


def format_system_prompt(sections: list, now: datetime) -> str:
    """Render assembled context sections into the final system prompt string.

    `sections` is the engine's list of context_engine.base.Section objects;
    a section with omit_when_empty and no items is skipped entirely, the
    Phase-1 sections render their "None" placeholder instead.
    """
    today = now.strftime("%A, %B %d, %Y")
    current_time = now.strftime("%I:%M %p").lstrip("0")

    header = (
        f"You are {ASSISTANT_NAME}, a personal assistant. Today is {today}. "
        f"The current time is {current_time}. Never ask the user for the current date or time."
    )
    body = "\n\n".join(
        f"{section.title}:\n{section.rendered()}" for section in sections if section.include
    )
    lang_instruction = (
        f" Reply in {REPLY_LANGUAGE} — keep it natural and spoken-friendly."
        if REPLY_LANGUAGE
        else ""
    )
    footer = (
        "Keep replies short and natural — 2 to 4 spoken sentences, no lists or markdown. "
        "Ask a clarifying question when a request is too vague to act on confidently."
        + lang_instruction
    )
    return f"{header}\n\n{body}\n\n{footer}"
