"""Daily plan: reminders, calendar, open tasks, habits, notes, money — for today."""

from datetime import datetime

import memory

from .schedule import generate_schedule


def build_daily_plan() -> str:
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    sched = generate_schedule(today, task_limit=5)
    earned, spent = memory.get_money_totals_for_date(today)
    prog_notes = memory.get_progress_notes_for_date(today_str, exclude_area="journal", limit=3)

    parts = ["Here's your day."]
    if sched["due_reminders"]:
        parts.append(
            "Reminders today: " + "; ".join(r["text"] for r in sched["due_reminders"]) + "."
        )
    if sched["events"]:
        parts.append(
            "Calendar: "
            + "; ".join(f"{e['title']} at {e['time']}" for e in sched["events"][:3])
            + "."
        )
    else:
        parts.append("Nothing on the calendar today.")
    if sched["top_tasks"]:
        parts.append("Open tasks: " + "; ".join(t["text"] for t in sched["top_tasks"]) + ".")
    else:
        parts.append("No open tasks.")
    if sched["habits"]:
        parts.append("Habits done: " + "; ".join(h["name"] for h in sched["habits"]) + ".")
    if prog_notes:
        parts.append("Notes today: " + "; ".join(prog_notes) + ".")
    if earned > 0 or spent > 0:
        parts.append(f"Money today: earned {earned:.0f}, spent {spent:.0f} rupees.")
    return " ".join(parts)
