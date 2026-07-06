"""Credit-card value objects — pure, no I/O."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import FinanceValidationError


@dataclass(frozen=True)
class CreditLimit:
    minor: int

    def __post_init__(self) -> None:
        if self.minor <= 0:
            raise FinanceValidationError("credit_limit_minor must be positive")

    @classmethod
    def from_minor(cls, minor: int) -> CreditLimit:
        return cls(minor)


@dataclass(frozen=True)
class DueDate:
    value: str

    @classmethod
    def from_iso(cls, value: str) -> DueDate:
        from datetime import date

        date.fromisoformat(value)
        return cls(value)


@dataclass(frozen=True)
class AvailableLimit:
    """Derived headroom — never stored."""

    minor: int

    @classmethod
    def compute(cls, credit_limit_minor: int, balance_minor: int) -> AvailableLimit:
        outstanding = max(0, -balance_minor)
        return cls(max(0, credit_limit_minor - outstanding))


@dataclass(frozen=True)
class Utilization:
    """Derived utilization ratio — never stored."""

    ratio: float
    outstanding_minor: int
    credit_limit_minor: int

    @classmethod
    def compute(cls, credit_limit_minor: int, balance_minor: int) -> Utilization:
        if credit_limit_minor <= 0:
            raise FinanceValidationError("credit_limit_minor must be positive")
        outstanding = max(0, -balance_minor)
        ratio = outstanding / credit_limit_minor
        return cls(
            ratio=ratio,
            outstanding_minor=outstanding,
            credit_limit_minor=credit_limit_minor,
        )

    @property
    def percent(self) -> float:
        return self.ratio * 100.0
