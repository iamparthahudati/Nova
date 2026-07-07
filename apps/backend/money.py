"""Shared money value object — root utility for Finance and WorkOS.

Engagements stores revenue expectations; Finance stores realized cash. Both
domains import this module; neither domain imports the other.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


class MoneyValidationError(ValueError):
    """Input failed money validation."""


@dataclass(frozen=True)
class MoneyAmount:
    minor: int

    @classmethod
    def from_rupees(cls, amount: float) -> MoneyAmount:
        if amount <= 0:
            raise MoneyValidationError("Amount must be positive")
        paise = int((Decimal(str(amount)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        if paise <= 0:
            raise MoneyValidationError("Amount must be positive")
        return cls(paise)

    def to_rupees(self) -> float:
        return self.minor / 100.0
