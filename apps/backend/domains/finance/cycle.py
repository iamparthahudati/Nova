"""Statement cycle computation — pure, no I/O."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta

from .errors import FinanceValidationError


def clamp_statement_day(year: int, month: int, statement_day: int) -> int:
    """Clamp statement_day to the month's length (Feb → 28/29)."""
    if statement_day < 1 or statement_day > 31:
        raise FinanceValidationError("statement_day must be between 1 and 31")
    last_day = calendar.monthrange(year, month)[1]
    return min(statement_day, last_day)


def _statement_date_in_month(year: int, month: int, statement_day: int) -> date:
    day = clamp_statement_day(year, month, statement_day)
    return date(year, month, day)


def _add_months(year: int, month: int, delta: int) -> tuple[int, int]:
    month += delta
    while month > 12:
        month -= 12
        year += 1
    while month < 1:
        month += 12
        year -= 1
    return year, month


@dataclass(frozen=True)
class StatementCycle:
    """One billing period: [period_start, period_end] inclusive."""

    period_start: str
    period_end: str
    statement_date: str

    def contains(self, occurred_on: str) -> bool:
        return self.period_start <= occurred_on <= self.period_end


@dataclass(frozen=True)
class BillingCycle:
    """Statement cycle plus payment due date."""

    cycle: StatementCycle
    due_date: str

    @property
    def period_start(self) -> str:
        return self.cycle.period_start

    @property
    def period_end(self) -> str:
        return self.cycle.period_end

    @property
    def statement_date(self) -> str:
        return self.cycle.statement_date


def compute_billing_cycle(
    statement_day: int,
    due_day_offset: int,
    reference: date,
) -> BillingCycle:
    """Derive the billing cycle containing reference."""
    if due_day_offset <= 0:
        raise FinanceValidationError("due_day_offset must be positive")

    year, month = reference.year, reference.month
    end_this_month = _statement_date_in_month(year, month, statement_day)
    if reference >= end_this_month:
        period_end = end_this_month
    else:
        prev_year, prev_month = _add_months(year, month, -1)
        period_end = _statement_date_in_month(prev_year, prev_month, statement_day)

    prev_year, prev_month = _add_months(period_end.year, period_end.month, -1)
    prev_end = _statement_date_in_month(prev_year, prev_month, statement_day)
    period_start = (prev_end + timedelta(days=1)).isoformat()
    statement_date = period_end.isoformat()
    due = period_end + timedelta(days=due_day_offset)
    if due <= period_end:
        raise FinanceValidationError("due_date must be after period_end")

    cycle = StatementCycle(
        period_start=period_start,
        period_end=statement_date,
        statement_date=statement_date,
    )
    return BillingCycle(cycle=cycle, due_date=due.isoformat())


def compute_previous_billing_cycle(
    statement_day: int,
    due_day_offset: int,
    current: BillingCycle,
) -> BillingCycle:
    """Derive the billing cycle immediately before current."""
    reference = date.fromisoformat(current.period_start) - timedelta(days=1)
    return compute_billing_cycle(statement_day, due_day_offset, reference)
