"""Nova's Planner service — morning briefing, evening wrap-up, daily plan,
and task prioritization.

Owns no storage and no AppleScript/Claude access of its own: it reads
Memory directly (a leaf dependency, same as Brain), and reads Calendar
through services.calendar's public API. Anything not yet extracted as a
service (weather, etc.) is taken as an injected callable rather than
imported directly. Brain is a reserved dependency: no planning function
calls Claude yet.
"""

from .briefing import build_morning_briefing
from .daily import build_daily_plan
from .evening import build_evening_wrapup
from .priorities import prioritize_tasks
from .schedule import generate_schedule
from .commands import (
    log_task, complete_task, log_money, log_progress,
    add_product, ship_product, log_sale, save_reminder,
    due_timed_reminders, log_habit, describe_habits_today,
    get_spending_summary,
)
from .config import BRIEFING_TIME, EVENING_WRAPUP_TIME

__all__ = [
    "build_morning_briefing",
    "build_evening_wrapup",
    "build_daily_plan",
    "prioritize_tasks",
    "generate_schedule",
    "log_task",
    "complete_task",
    "log_money",
    "log_progress",
    "add_product",
    "ship_product",
    "log_sale",
    "save_reminder",
    "due_timed_reminders",
    "log_habit",
    "describe_habits_today",
    "get_spending_summary",
    "BRIEFING_TIME",
    "EVENING_WRAPUP_TIME",
]
