"""Context Engine data model — the structured pieces every provider speaks.

One vocabulary, three nouns:

  ContextRequest  — what this turn is about (query, history, clock). Read-only
                    input to every provider; providers never see each other.
  ContextItem     — one candidate fact a provider contributes: a payload text
                    (identity, used for cross-provider dedup), a display line
                    (what the prompt shows), a relevance score (ranking within
                    its section), and free-form meta (e.g. the full recall dict
                    a semantic item carries so reinforcement can target it).
  Section         — one titled block of the final system prompt, holding the
                    items that *survived* dedup and budgeting. prompts.py
                    renders sections; it never sees providers or raw candidates.

AssembledContext is the engine's complete answer for a turn: the final system
string, the messages channel (recent conversation — threaded, never duplicated
into the system text), the exact semantic memories injected (for the
reinforcement loop in reinforcement.py), the surviving sections (for tests and
debugging), and the names of any providers that failed (graceful degradation is
a recorded fact, not a silent one).
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Sequence

# chars-per-token approximation — deliberately no tokenizer dependency; budgets
# are soft ceilings, not exact accounting. (Moved here from prompts.py, which
# no longer does any accounting at all.)
_CHARS_PER_TOKEN = 4

_WS = re.compile(r"\s+")


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // _CHARS_PER_TOKEN)


def dedup_key(text: str) -> str:
    """Cross-provider identity of a fact: lowercased, whitespace-collapsed.

    Same normalization family as memory's content hash — "Ship  the App" and
    "ship the app" are one fact whether it arrives as an open task or as a
    semantic memory echoing that task.
    """
    return _WS.sub(" ", text.strip().lower())


@dataclass(frozen=True)
class ContextRequest:
    """The turn, as providers are allowed to see it."""
    query: str
    history: tuple = ()
    now: Optional[datetime] = None


@dataclass
class ContextItem:
    """One candidate fact from one provider."""
    text: str                    # payload — identity for dedup
    render: Optional[str] = None  # display line; defaults to "- {text}"
    score: float = 0.0           # relevance within the section (higher = keep first)
    meta: dict = field(default_factory=dict)

    @property
    def display(self) -> str:
        return self.render if self.render is not None else f"- {self.text}"

    @property
    def key(self) -> str:
        return dedup_key(self.text)


@dataclass
class Section:
    """One titled block of the assembled prompt, post-dedup, post-budget."""
    name: str
    title: str
    items: list[ContextItem] = field(default_factory=list)
    omit_when_empty: bool = False
    empty_text: str = "None"

    @property
    def include(self) -> bool:
        return bool(self.items) or not self.omit_when_empty

    def rendered(self) -> str:
        """The section body. Items carrying a `group` meta render as titled
        sub-blocks in first-seen group order (the Recent Context shape:
        'Recent progress:' / 'Recent money entries:' / 'Products:')."""
        if not self.items:
            return self.empty_text
        if any("group" in i.meta for i in self.items):
            groups: dict[str, list[str]] = {}
            for item in self.items:
                groups.setdefault(item.meta.get("group", ""), []).append(item.display)
            return "\n\n".join(
                (f"{label}:\n" if label else "") + "\n".join(lines)
                for label, lines in groups.items()
            )
        return "\n".join(i.display for i in self.items)


@dataclass
class AssembledContext:
    """Everything one turn's context assembly produced."""
    system: str
    memories: list[dict] = field(default_factory=list)   # exact semantic dicts injected
    messages: list[dict] = field(default_factory=list)   # recent-conversation channel
    sections: list[Section] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)    # provider names that degraded


class ContextProvider(ABC):
    """One independent context source.

    A provider turns a ContextRequest into candidate ContextItems and nothing
    else: no calls to other providers, no Claude, no writes. Failures may
    propagate freely — the engine isolates them per-provider, so one broken
    source degrades to an empty section instead of a broken turn.

    `budget` is the section's token ceiling (engine-enforced, score order,
    always keeping at least one surviving item so a single oversized fact can't
    blank its own section). `omit_when_empty` distinguishes sections that
    should disappear entirely (calendar, graph) from ones that render "None"
    (the Phase-1 blocks, whose empty rendering is existing behavior).
    """

    name: str = ""
    title: str = ""
    budget: int = 400
    omit_when_empty: bool = False

    @abstractmethod
    def collect(self, request: ContextRequest) -> Sequence[ContextItem]:
        ...


class MessagesProvider(ABC):
    """A provider for the messages channel (recent conversation).

    Same independence rules as ContextProvider, different output shape: it
    yields Claude `messages` entries (role/content dicts), because dialogue is
    threaded to Claude as messages, never flattened into the system string.
    """

    name: str = ""

    @abstractmethod
    def collect(self, request: ContextRequest) -> Sequence[dict]:
        ...
