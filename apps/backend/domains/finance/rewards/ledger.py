"""Derived reward balance and ledger — never stored."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

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


def derive_program_status(
    balance: int,
    total_earned: int,
    expiry_note: Optional[str],
) -> str:
    if balance > 0 and expiry_note:
        return "expiring"
    if balance > 0:
        return "active"
    if total_earned > 0:
        return "depleted"
    return "new"


def fold_monthly_activity(
    events: list[RewardEvent],
    months: int,
    end_on: date,
) -> list[dict]:
    """Return month buckets (newest first) with earned/redeemed/expired totals."""
    buckets: dict[str, dict[str, int]] = {}
    for event in events:
        month_key = event.occurred_on[:7]
        bucket = buckets.setdefault(
            month_key,
            {"earned": 0, "redeemed": 0, "expired": 0, "adjusted": 0},
        )
        if event.kind in bucket:
            bucket[event.kind] += event.amount

    rows = []
    cursor = end_on.replace(day=1)
    for _ in range(months):
        key = cursor.strftime("%Y-%m")
        activity = buckets.get(
            key,
            {"earned": 0, "redeemed": 0, "expired": 0, "adjusted": 0},
        )
        rows.append({"month": key, **activity})
        if cursor.month == 1:
            cursor = cursor.replace(year=cursor.year - 1, month=12)
        else:
            cursor = cursor.replace(month=cursor.month - 1)
    return rows
