"""Schedule assembly — one day's events, due reminders, open tasks, habits.

Shared by briefing.py and daily.py so both draw from a single fetch instead
of independently querying Memory and Calendar and reformatting the same
shape twice (which is what the pre-extraction composition root did).
"""

from datetime import datetime
from typing import Optional

import memory
from services import calendar

from .priorities import prioritize_tasks


def generate_schedule(day: Optional[datetime] = None, task_limit: int = 3) -> dict:
    """Return events/reminders/tasks/habits for `day` (default today).

    `habits` always reflects *today* regardless of `day` — Memory's habit
    log only supports a "today" query, not an arbitrary date.
    """
    day = day or datetime.now()
    tasks = memory.get_open_tasks()
    return {
        "day": day,
        "events": calendar.get_events(day),
        "due_reminders": memory.get_due_reminders(day),
        "tasks": tasks,
        "top_tasks": prioritize_tasks(tasks, limit=task_limit),
        "habits": memory.get_habits_today(),
    }
