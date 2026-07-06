"""Nova's Knowledge service — read-only information providers.

Owns weather, RSS, GitHub notifications, the reflection trigger, and the
journal helper. Knowledge gathers information; Brain reasons over it —
reflection.py and journal.py call into services.brain (and journal.py
into memory) as leaf dependencies, the same pattern Planner uses for
Memory/Calendar, but Knowledge holds no Claude API logic and no storage
of its own.
"""

from .weather import get_weather
from .rss import get_rss_updates
from .github import get_github_notifications
from .reflection import run_reflection, should_run_reflection
from .journal import handle_journal

__all__ = [
    "get_weather",
    "get_rss_updates",
    "get_github_notifications",
    "run_reflection",
    "should_run_reflection",
    "handle_journal",
]
