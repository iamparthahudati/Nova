"""Command layer — natural-language tool-call args in, spoken confirmation
string out. Planner already depends on both Memory and Calendar (see
schedule.py), so the write-side commands that touch Memory alone, or Memory
plus a Calendar date parse, live here rather than duplicating that
dependency edge elsewhere.
"""

from datetime import datetime, timedelta
from typing import Optional

import memory
from services import calendar


def log_task(text: str, due_str: Optional[str] = None) -> str:
    due = None
    if due_str:
        date_obj = calendar.parse_date(due_str)
        due = date_obj.strftime("%Y-%m-%d") if date_obj else due_str
    memory.add_task(text, due=due)
    return "Task logged." + (f" Due {due}." if due else "")


def complete_task(text: str) -> str:
    found = memory.complete_task(text)
    return "Task marked done." if found else "No matching task found."


def log_money(kind: str, amount: float, note: str = "") -> str:
    memory.add_money(kind, amount, note)
    return "Logged earnings." if kind == "earned" else "Logged expense."


def log_progress(note: str, area: str = "") -> str:
    memory.add_progress(note, area)
    return "Progress logged."


def add_product(name: str, store: str = "", price: Optional[float] = None) -> str:
    memory.add_product(name, store, price)
    return "Product added."


def ship_product(name: str) -> str:
    found = memory.ship_product(name)
    return "Product marked shipped." if found else "No matching product found."


def log_sale(name: str) -> str:
    found = memory.log_sale(name)
    return "Sale logged." if found else "No matching product found."


def save_reminder(text: str, remind_date_str: str, remind_time_str: Optional[str] = None) -> str:
    # Relative offsets ('in 20 minutes', 'after 2 hours') arrive verbatim from
    # Brain and resolve against the system clock here — the user is never asked
    # for the current time. An explicit remind_time still wins over the
    # offset's clock component ('in 3 days' + '06:00').
    moment = calendar.parse_relative(remind_date_str)
    if moment is not None:
        date_obj = moment.replace(hour=0, minute=0, second=0, microsecond=0)
        if remind_time_str is None:
            remind_time_str = f"{moment.hour:02d}:{moment.minute:02d}"
    else:
        date_obj = calendar.parse_date(remind_date_str)
    if not date_obj:
        return f"Sorry, I couldn't understand the date '{remind_date_str}'."
    time_label = ""
    remind_time = None
    if remind_time_str:
        time_tuple = calendar.parse_time(remind_time_str)
        if not time_tuple:
            return f"Sorry, I couldn't understand the time '{remind_time_str}'."
        hour, minute = time_tuple
        remind_time = f"{hour:02d}:{minute:02d}"  # canonical form, sortable as text
        suffix = "AM" if hour < 12 else "PM"
        time_label = f" at {hour % 12 or 12}:{minute:02d} {suffix}"
    memory.add_reminder(text, date_obj, remind_time)
    return f"Reminder saved: {text} on {date_obj.strftime('%B %d')}{time_label}."


def due_timed_reminders(now: Optional[datetime] = None) -> list[dict]:
    """Today's reminders whose remind_time has arrived (remind_time <= now).

    Canonical 'HH:MM' strings compare correctly as text. The caller owns
    announced-once tracking; this is a pure 'what is due' query so a late
    start still surfaces reminders whose time already passed today.
    """
    now = now or datetime.now()
    now_hhmm = now.strftime("%H:%M")
    return [
        r
        for r in memory.get_due_reminders(now)
        if r.get("remind_time") and r["remind_time"] <= now_hhmm
    ]


def log_habit(name: str) -> str:
    memory.log_habit(name)
    return f"Habit logged: {name}."


def describe_habits_today() -> str:
    habits = memory.get_habits_today()
    if not habits:
        return "No habits logged today yet."
    return "Today's habits: " + "; ".join(h["name"] for h in habits) + "."


def get_spending_summary(period: str = "this week") -> str:
    today = datetime.now()
    t = period.lower().strip()
    if t == "today":
        start = end = today.strftime("%Y-%m-%d")
        label = "today"
    elif t == "last week":
        last_monday = today - timedelta(days=today.weekday() + 7)
        start = last_monday.strftime("%Y-%m-%d")
        end = (last_monday + timedelta(days=6)).strftime("%Y-%m-%d")
        label = "last week"
    elif t in ("this month", "month"):
        start = today.replace(day=1).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
        label = "this month"
    else:  # "this week" default
        monday = today - timedelta(days=today.weekday())
        start = monday.strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
        label = "this week"

    earned, spent = memory.get_money_totals_between(start, end)
    if earned == 0 and spent == 0:
        return f"No money logged {label}."
    parts = []
    if earned > 0:
        parts.append(f"earned {earned:.0f}")
    if spent > 0:
        parts.append(f"spent {spent:.0f}")
    summary = " and ".join(parts)
    net = earned - spent
    net_str = (
        f" Net: {'+' if net >= 0 else ''}{net:.0f} rupees." if earned > 0 and spent > 0 else ""
    )
    return f"{label.capitalize()}: {summary} rupees.{net_str}"
