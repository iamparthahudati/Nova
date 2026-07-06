"""The Context Engine — Brain's single context-assembly pipeline (Milestone 2.8).

Everything Claude sees about the world is assembled here, from independent
providers, through one orchestration pipeline (engine.py: collect → dedup →
rank → budget → format). prompts.py only formats; client.py only sends.

Public surface (what the rest of Brain, and brain/__init__.py, consume):

    assemble(query, history)   → AssembledContext (system, messages, memories)
    build_system_prompt(query) → str — the Phase-1-compatible entry point
    set_calendar_source(fn)    → root-injection point for calendar events

Render order is fixed and deterministic: Recent Context, Semantic Memories,
Known Connections (graph), Current Tasks, Today's Calendar, Profile — the
Phase-1 sections keep their exact positions and titles; the two new sections
(graph, calendar) appear only when they have content, so with an empty graph
and no calendar source the prompt is byte-compatible with the pre-2.8 shape.
"""

from datetime import datetime
from typing import Optional

from ..config import CONTEXT_TOTAL_TOKEN_BUDGET
from .base import (
    AssembledContext, ContextItem, ContextProvider, ContextRequest,
    MessagesProvider, Section,
)
from .engine import ContextEngine
from .providers import (
    CalendarContextProvider,
    GraphContextProvider,
    ProfileContextProvider,
    RecentActivityProvider,
    RecentConversationProvider,
    SemanticContextProvider,
    TaskContextProvider,
    set_calendar_source,
)

__all__ = [
    "AssembledContext",
    "ContextEngine",
    "ContextItem",
    "ContextProvider",
    "ContextRequest",
    "MessagesProvider",
    "Section",
    "assemble",
    "build_default_engine",
    "build_system_prompt",
    "set_calendar_source",
]

_engine: Optional[ContextEngine] = None


def build_default_engine() -> ContextEngine:
    """The production wiring: all providers, fixed render order, global budget."""
    return ContextEngine(
        providers=[
            RecentActivityProvider(),
            SemanticContextProvider(),
            GraphContextProvider(),
            TaskContextProvider(),
            CalendarContextProvider(),
            ProfileContextProvider(),
        ],
        conversation=RecentConversationProvider(),
        total_budget=CONTEXT_TOTAL_TOKEN_BUDGET,
    )


def _get_engine() -> ContextEngine:
    global _engine
    if _engine is None:
        _engine = build_default_engine()
    return _engine


def assemble(
    query: Optional[str] = None,
    history: Optional[list[dict]] = None,
    now: Optional[datetime] = None,
) -> AssembledContext:
    """Assemble one turn's full context through the default engine."""
    return _get_engine().assemble(query, history, now)


def build_system_prompt(query: Optional[str] = None) -> str:
    """Back-compatible string entry point (kept in Brain's public API).

    Equivalent to assemble(query).system. Callers that also need the
    injected-memory list for reinforcement use assemble() directly.
    """
    return assemble(query).system
