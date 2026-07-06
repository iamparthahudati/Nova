"""Derived reward balance and ledger — never stored."""

from __future__ import annotations

from dataclasses import dataclass

from .aggregates import RewardEvent, RewardProgram


@dataclass(frozen=True)
class RewardBalance:
    """Computed balance for a reward program."""

    program_id: int
    unit: str
    balance: int
    total_earned: int
    total_redeemed: int
    total_expired: int

    @property
    def available(self) -> int:
        return self.balance


@dataclass(frozen=True)
class RewardLedger:
    """Event-sourced ledger view for a program."""

    program: RewardProgram
    balance: RewardBalance
    events: tuple[RewardEvent, ...]


def compute_balance(
    program_id: int,
    unit: str,
    credit_total: int,
    debit_total: int,
    earned_total: int = 0,
    redeemed_total: int = 0,
    expired_total: int = 0,
) -> RewardBalance:
    return RewardBalance(
        program_id=program_id,
        unit=unit,
        balance=credit_total - debit_total,
        total_earned=earned_total,
        total_redeemed=redeemed_total,
        total_expired=expired_total,
    )


def fold_event_totals(events: list[RewardEvent]) -> tuple[int, int, int, int, int]:
    """Return (credit, debit, earned, redeemed, expired) from event rows."""
    credit = 0
    debit = 0
    earned = 0
    redeemed = 0
    expired = 0
    for event in events:
        if event.direction == "credit":
            credit += event.amount
        else:
            debit += event.amount
        if event.kind == "earned":
            earned += event.amount
        elif event.kind == "redeemed":
            redeemed += event.amount
        elif event.kind == "expired":
            expired += event.amount
    return credit, debit, earned, redeemed, expired
