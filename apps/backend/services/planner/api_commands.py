"""REST-facing commands — ID-based, deterministic."""

from __future__ import annotations

from typing import Optional

import memory
from services import calendar


class TaskNotFoundError(LookupError):
    def __init__(self, task_id: int) -> None:
        super().__init__(f"Task {task_id} not found")
        self.task_id = task_id


class TaskNotOpenError(LookupError):
    def __init__(self, task_id: int) -> None:
        super().__init__(f"Task {task_id} is not open")
        self.task_id = task_id


def create_task(text: str, due: Optional[str] = None) -> dict:
    return memory.add_task(text, due=due)


def complete_task_by_id(task_id: int) -> dict:
    row = memory.complete_task_by_id(task_id)
    if row is not None:
        return row
    existing = memory.get_task_by_id(task_id)
    if existing is None:
        raise TaskNotFoundError(task_id)
    raise TaskNotOpenError(task_id)


class ReminderDateInvalidError(ValueError):
    def __init__(self, remind_date: str) -> None:
        super().__init__(f"Invalid reminder date: {remind_date}")
        self.remind_date = remind_date


class ReminderTimeInvalidError(ValueError):
    def __init__(self, remind_time: str) -> None:
        super().__init__(f"Invalid reminder time: {remind_time}")
        self.remind_time = remind_time


class SpendingTypeInvalidError(ValueError):
    def __init__(self, type_: str) -> None:
        super().__init__(f"Invalid spending type: {type_}")
        self.type_ = type_


def create_reminder(text: str, remind_date: str, remind_time: Optional[str] = None) -> tuple[dict, str]:
    date_obj = calendar.parse_date(remind_date)
    if date_obj is None:
        raise ReminderDateInvalidError(remind_date)

    remind_time_canonical = None
    time_label = ""
    if remind_time:
        time_tuple = calendar.parse_time(remind_time)
        if time_tuple is None:
            raise ReminderTimeInvalidError(remind_time)
        hour, minute = time_tuple
        remind_time_canonical = f"{hour:02d}:{minute:02d}"
        suffix = "AM" if hour < 12 else "PM"
        time_label = f" at {hour % 12 or 12}:{minute:02d} {suffix}"

    row = memory.add_reminder(text, date_obj, remind_time_canonical)
    message = f"Reminder saved: {text} on {date_obj.strftime('%B %d')}{time_label}."
    return row, message


def log_spending(type_: str, amount: float, note: str = "") -> tuple[dict, str]:
    if type_ not in {"earned", "spent"}:
        raise SpendingTypeInvalidError(type_)
    row = memory.add_money(type_, amount, note)
    message = "Logged earnings." if type_ == "earned" else "Logged expense."
    return row, message
