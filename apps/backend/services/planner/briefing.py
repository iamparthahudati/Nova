"""Morning briefing: weather, reminders, calendar events, top tasks, money."""

from datetime import datetime, timedelta
from typing import Callable, Optional

import memory

from .schedule import generate_schedule


def build_morning_briefing(weather_provider: Optional[Callable[[], str]] = None) -> str:
    """Build the spoken morning briefing.

    `weather_provider` is injected rather than imported: weather isn't a
    service yet (Milestone 7 — Knowledge Service), so Planner takes it as a
    plain callable instead of reaching outside its Memory/Brain/Calendar
    dependency set. Pass None to omit the weather line.
    """
    today = datetime.now()
    sched = generate_schedule(today)
    earned, spent = memory.get_money_totals_for_date(today - timedelta(days=1))

    parts = ["Good morning."]

    if weather_provider is not None:
        try:
            parts.append(weather_provider())
        except Exception:
            pass

    if sched["due_reminders"]:
        reminder_text = "; ".join(r["text"] for r in sched["due_reminders"])
        parts.append(f"Reminder today: {reminder_text}.")

    if sched["events"]:
        event_text = "; ".join(f"{e['title']} at {e['time']}" for e in sched["events"][:3])
        parts.append(f"On your calendar: {event_text}.")
    else:
        parts.append("Nothing on your calendar today.")

    if sched["top_tasks"]:
        parts.append("Top tasks: " + "; ".join(t["text"] for t in sched["top_tasks"]) + ".")
    else:
        parts.append("No open tasks.")

    if earned > 0 or spent > 0:
        parts.append(f"Yesterday: earned {earned:.0f} rupees, spent {spent:.0f} rupees.")

    return " ".join(parts)
