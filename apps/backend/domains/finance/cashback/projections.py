"""Cashback projection helpers — read-only folds for caps."""

from __future__ import annotations

from datetime import date
from typing import Optional


def month_bounds(occurred_on: str) -> tuple[str, str]:
    occurred = date.fromisoformat(occurred_on)
    start = occurred.replace(day=1).isoformat()
    if occurred.month == 12:
        end = occurred.replace(year=occurred.year + 1, month=1, day=1)
    else:
        end = occurred.replace(month=occurred.month + 1, day=1)
    last_day = end.fromordinal(end.toordinal() - 1)
    return start, last_day.isoformat()


def apply_monthly_cap(
    gross_reward_minor: int,
    monthly_earned_before: int,
    monthly_cap_minor: Optional[int],
) -> int:
    if gross_reward_minor <= 0:
        return 0
    if monthly_cap_minor is None:
        return gross_reward_minor
    remaining = monthly_cap_minor - monthly_earned_before
    if remaining <= 0:
        return 0
    return min(gross_reward_minor, remaining)
