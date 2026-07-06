"""Evening wrap-up: what got done today, open tasks, tomorrow's first event."""

from datetime import datetime, timedelta

import memory
from services import calendar


def build_evening_wrapup() -> str:
    tasks = memory.get_open_tasks()
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_events = calendar.get_events(tomorrow)

    today_str = datetime.now().strftime("%Y-%m-%d")
    done_tasks = memory.get_done_task_texts_for_date(today_str)

    parts = ["Evening wrap-up."]

    if done_tasks:
        parts.append("Done today: " + "; ".join(done_tasks[:3]) + ".")
    else:
        parts.append("Nothing marked done today.")

    if tasks:
        parts.append(f"{len(tasks)} task{'s' if len(tasks) != 1 else ''} still open.")
    else:
        parts.append("All tasks cleared.")

    if tomorrow_events:
        first = tomorrow_events[0]
        parts.append(f"Tomorrow starts with {first['title']} at {first['time']}.")

    return " ".join(parts)
