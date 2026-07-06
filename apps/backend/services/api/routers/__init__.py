"""API routers — thin delegates to existing public service APIs."""

from . import (
    calendar,
    chat,
    graph,
    health,
    home,
    memories,
    memory,
    products,
    reminders,
    settings,
    spending,
    system,
    tasks,
)

__all__ = [
    "health",
    "chat",
    "tasks",
    "calendar",
    "reminders",
    "memory",
    "memories",
    "graph",
    "spending",
    "products",
    "settings",
    "home",
    "system",
]
