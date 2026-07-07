"""Money and date value objects — pure, no I/O."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from .errors import FinanceValidationError

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class MoneyAmount:
    minor: int

    @classmethod
    def from_rupees(cls, amount: float) -> MoneyAmount:
        if amount <= 0:
            raise FinanceValidationError("Amount must be positive")
        paise = int((Decimal(str(amount)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        if paise <= 0:
            raise FinanceValidationError("Amount must be positive")
        return cls(paise)

    def to_rupees(self) -> float:
        return self.minor / 100.0


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
    if account_type in {"credit_card", "loan"}:
        return "liability"
    return "asset"
