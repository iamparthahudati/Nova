"""Calendar provider — today's events, via a source injected by the
composition root (Milestone 2.8).

Brain never imports services.calendar: v1's "Brain stays agnostic" rule and
v2 §10's dependency graph (brain → memory only) both forbid the edge. Instead
nova.py wires `calendar.get_events` in at startup through
set_calendar_source() — the same dependency-injection precedent as
TOOL_HANDLERS and automation.start_pomodoro's injected `speak`. Unwired
(tests, dashboard, anything that isn't the assistant process), the provider
contributes nothing and the prompt is exactly what it was before 2.8.

Events are fetched through AppleScript (~seconds), far too slow for every
turn, so one fetch is cached per (day, TTL window). A fetch failure inside
get_events already degrades to [] in the Calendar service; a raising source
is isolated by the engine like any other provider failure.
"""

import time
from datetime import datetime
from typing import Callable, Optional

from ...config import (
    CALENDAR_CONTEXT_ENABLED,
    CALENDAR_CONTEXT_TOKEN_BUDGET,
    CALENDAR_CONTEXT_TTL_SECONDS,
)
from ..base import ContextItem, ContextProvider, ContextRequest

# The injected fetch: (day: datetime | None) -> list[{"title", "time"}].
# Module-level so the root can wire it once, before or after engine creation.
_source: Optional[Callable[[Optional[datetime]], list[dict]]] = None
_cache: Optional[tuple[float, str, list[dict]]] = None   # (monotonic, day-key, events)


def set_calendar_source(fetch: Optional[Callable[[Optional[datetime]], list[dict]]]) -> None:
    """Wire (or clear, with None) the calendar events source. Root-only call."""
    global _source, _cache
    _source = fetch
    _cache = None


class CalendarContextProvider(ContextProvider):
    name = "calendar"
    title = "Today's Calendar"
    budget = CALENDAR_CONTEXT_TOKEN_BUDGET
    omit_when_empty = True   # empty day → no section; never a "None" block

    def collect(self, request: ContextRequest) -> list[ContextItem]:
        if not CALENDAR_CONTEXT_ENABLED or _source is None:
            return []
        events = self._events_today(request.now or datetime.now())
        return [
            ContextItem(
                text=f"{e['title']} at {e['time']}",
                render=f"- {e['time']} — {e['title']}",
            )
            for e in events
        ]

    @staticmethod
    def _events_today(now: datetime) -> list[dict]:
        global _cache
        day_key = now.strftime("%Y-%m-%d")   # midnight rollover invalidates
        if _cache is not None:
            fetched_at, cached_day, events = _cache
            if cached_day == day_key and (
                time.monotonic() - fetched_at < CALENDAR_CONTEXT_TTL_SECONDS
            ):
                return events
        events = list(_source(now))
        _cache = (time.monotonic(), day_key, events)
        return events
