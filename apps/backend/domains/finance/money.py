"""Finance date value objects and re-exports of shared Money."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta

from money import MoneyAmount

from .errors import FinanceValidationError
from .value_objects import AccountType

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class OccurredOn:
    value: str

    @classmethod
    def from_iso(cls, value: str) -> OccurredOn:
        if not _DATE_RE.match(value):
            raise FinanceValidationError(f"Invalid date: {value}")
        date.fromisoformat(value)
        return cls(value)

    @classmethod
    def today(cls, today: date) -> OccurredOn:
        return cls(today.isoformat())

    def validate_not_before(self, opening_balance_on: str) -> None:
        if self.value < opening_balance_on:
            raise FinanceValidationError(
                f"occurred_on {self.value} is before account opening date {opening_balance_on}",
            )

    def validate_not_far_future(self, today: date, max_future_days: int = 1) -> None:
        limit = today + timedelta(days=max_future_days)
        if date.fromisoformat(self.value) > limit:
            raise FinanceValidationError(f"occurred_on {self.value} is too far in the future")


def classification_for_type(account_type: str) -> str:
    if account_type in {AccountType.CREDIT_CARD.value, AccountType.LOAN.value}:
        return "liability"
    return "asset"


__all__ = ["MoneyAmount", "OccurredOn", "classification_for_type"]
