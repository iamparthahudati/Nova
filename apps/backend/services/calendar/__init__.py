"""Nova's Calendar service — macOS Calendar.app integration via AppleScript.

Owns every Apple Calendar concern: event creation, event retrieval, and the
natural-language date/time parsing calendar commands need. A true leaf
dependency, same shape as Memory and Voice — it imports nothing from
memory, services.brain, services.voice, or services.planner, and nothing
outside this package should shell out to `osascript` for Calendar.

Callers (nova.py, services.planner) consume only the four names below.
Brain never imports this package directly — it only knows tool names and
calls whatever handler nova.py wires up, which in turn calls here.
"""

from .applescript import add_calendar_event, get_events
from .commands import create_event, describe_events
from .parsing import parse_date, parse_relative, parse_time

__all__ = [
    "add_calendar_event",
    "get_events",
    "parse_date",
    "parse_relative",
    "parse_time",
    "create_event",
    "describe_events",
]
