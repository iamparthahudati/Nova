"""Context providers — one independent module per source (Milestone 2.8).

Each provider reads exactly one context source through public APIs (Memory's
verbs, or a root-injected callable for Calendar) and returns structured
ContextItems. Providers never import one another, never call Claude, and never
write — cross-source judgment (dedup, ranking, budgets) belongs to the engine.
"""

from .activity import RecentActivityProvider
from .calendar import CalendarContextProvider, set_calendar_source
from .conversation import RecentConversationProvider
from .graph import GraphContextProvider
from .profile import ProfileContextProvider
from .semantic import SemanticContextProvider
from .tasks import TaskContextProvider

__all__ = [
    "RecentActivityProvider",
    "CalendarContextProvider",
    "set_calendar_source",
    "RecentConversationProvider",
    "GraphContextProvider",
    "ProfileContextProvider",
    "SemanticContextProvider",
    "TaskContextProvider",
]
