"""Home dashboard projection — cards + panels, presentation only."""

from __future__ import annotations

from datetime import datetime

import memory
from services import calendar

from ..schemas.home import HomeCard, HomePanel, HomePanelItem, HomeResponse

_REMINDER_LIMIT = 5
_TASK_LIMIT = 5


def build_home_response() -> HomeResponse:
    """Assemble the home screen from Memory reads and Calendar events."""
    month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")
    earned, spent = memory.get_money_totals_between(month_start, today)
    open_tasks = memory.count_open_tasks()
    memory_count = memory.count_active_memories()
    reminder_count = memory.count_reminders()
    products = memory.get_products()
    products_building = sum(1 for p in products if p.get("status") == "building")

    cards = [
        HomeCard(id="open_tasks", label="Open tasks", value=str(open_tasks), icon="list-todo"),
        HomeCard(id="earned_month", label="Monthly earned", value=f"{earned:.0f}", icon="wallet"),
        HomeCard(id="spent_month", label="Monthly spent", value=f"{spent:.0f}", icon="activity"),
        HomeCard(id="memory_count", label="Memories indexed", value=str(memory_count), icon="brain"),
        HomeCard(
            id="reminder_count",
            label="Upcoming reminders",
            value=str(reminder_count),
            icon="bell",
        ),
        HomeCard(
            id="products_building",
            label="Products in progress",
            value=str(products_building),
            icon="package",
        ),
    ]

    reminders = memory.get_upcoming_reminders(_REMINDER_LIMIT)
    reminder_items = [
        HomePanelItem(
            id=str(r["id"]),
            primary=r["text"],
            secondary=_format_reminder_secondary(r),
            meta={
                "remind_date": r["remind_date"],
                "remind_time": r.get("remind_time"),
            },
        )
        for r in reminders
    ]

    tasks = memory.get_open_tasks(limit=_TASK_LIMIT)
    task_items = [
        HomePanelItem(
            id=str(t["id"]),
            primary=t["text"],
            secondary=f"Due {t['due']}" if t.get("due") else "No due date",
            meta={"status": t["status"], "due": t.get("due")},
        )
        for t in tasks
    ]

    date_obj = datetime.now()
    try:
        events = calendar.get_events(date_obj)
        unavailable = False
    except Exception:
        events = []
        unavailable = True

    calendar_items = [
        HomePanelItem(
            id=f"event-{idx}",
            primary=e["title"],
            secondary=e.get("time") or "",
            meta={"date": date_obj.strftime("%Y-%m-%d"), "unavailable": unavailable},
        )
        for idx, e in enumerate(events)
    ]

    panels = [
        HomePanel(id="reminders", title="Upcoming reminders", items=reminder_items),
        HomePanel(id="open_tasks", title="Today's tasks", items=task_items),
        HomePanel(
            id="calendar",
            title="Calendar events",
            items=calendar_items,
        ),
    ]

    return HomeResponse(cards=cards, panels=panels)


def _format_reminder_secondary(reminder: dict) -> str:
    parts = [reminder["remind_date"]]
    if reminder.get("remind_time"):
        parts.append(f"at {reminder['remind_time']}")
    return " ".join(parts)
