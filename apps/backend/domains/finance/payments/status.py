"""Statement status — derived read model, never stored."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional


class StatementStatus(str, Enum):
    OPEN = "open"
    DUE = "due"
    OVERDUE = "overdue"
    PARTIAL = "partial"
    PAID = "paid"


@dataclass(frozen=True)
class StatementSummary:
    """Derived statement projection — never persisted."""

    statement_id: int
    spend_minor: int
    paid_minor: int
    total_due_minor: Optional[int]
    min_due_minor: Optional[int]
    remaining_due_minor: Optional[int]
    status: StatementStatus

    @property
    def paid_ratio(self) -> Optional[float]:
        if self.total_due_minor is None or self.total_due_minor == 0:
            return None
        return self.paid_minor / self.total_due_minor


def compute_statement_status(
    total_due_minor: Optional[int],
    paid_minor: int,
    due_date: str,
    today: date,
) -> StatementStatus:
    """Derived status per FINANCE_DATA_MODEL §6.5 (S4)."""
    if total_due_minor is None:
        return StatementStatus.OPEN
    if paid_minor >= total_due_minor:
        return StatementStatus.PAID
    if paid_minor > 0:
        return StatementStatus.PARTIAL
    due = date.fromisoformat(due_date)
    if today <= due:
        return StatementStatus.DUE
    return StatementStatus.OVERDUE


def compute_remaining_due(total_due_minor: Optional[int], paid_minor: int) -> Optional[int]:
    if total_due_minor is None:
        return None
    return max(total_due_minor - paid_minor, 0)
