"""Reward bounded context — immutable domain shapes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RewardProgram:
    """Reward program attached to a credit-card account — no balance column."""

    id: int
    account_id: int
    name: str
    unit: str
    earn_rate_note: Optional[str]
    expiry_note: Optional[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: dict) -> RewardProgram:
        return cls(
            id=int(row["id"]),
            account_id=int(row["account_id"]),
            name=str(row["name"]),
            unit=str(row["unit"]),
            earn_rate_note=row.get("earn_rate_note"),
            expiry_note=row.get("expiry_note"),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )


@dataclass(frozen=True)
class RewardEvent:
    """Single ledger entry — the source of truth for reward balances."""

    id: int
    program_id: int
    kind: str
    direction: str
    amount: int
    transaction_id: Optional[int]
    note: Optional[str]
    occurred_on: str
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: dict) -> RewardEvent:
        return cls(
            id=int(row["id"]),
            program_id=int(row["program_id"]),
            kind=str(row["kind"]),
            direction=str(row["direction"]),
            amount=int(row["amount"]),
            transaction_id=row.get("transaction_id"),
            note=row.get("note"),
            occurred_on=str(row["occurred_on"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )
