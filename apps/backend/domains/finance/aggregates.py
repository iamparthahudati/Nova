"""Aggregate root records — immutable domain shapes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Account:
    id: int
    name: str
    type: str
    classification: str
    currency: str
    opening_balance_minor: int
    opening_balance_on: str
    archived_at: Optional[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: dict) -> Account:
        return cls(
            id=int(row["id"]),
            name=str(row["name"]),
            type=str(row["type"]),
            classification=str(row["classification"]),
            currency=str(row["currency"]),
            opening_balance_minor=int(row["opening_balance_minor"]),
            opening_balance_on=str(row["opening_balance_on"]),
            archived_at=row.get("archived_at"),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )


@dataclass(frozen=True)
class Category:
    id: int
    name: str
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: dict) -> Category:
        return cls(
            id=int(row["id"]),
            name=str(row["name"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )


@dataclass(frozen=True)
class Merchant:
    id: int
    name: str
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: dict) -> Merchant:
        return cls(
            id=int(row["id"]),
            name=str(row["name"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )


@dataclass(frozen=True)
class CreditCardProfile:
    account_id: int
    network: Optional[str]
    last4: Optional[str]
    credit_limit_minor: int
    statement_day: int
    due_day_offset: int
    autopay: bool
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: dict) -> CreditCardProfile:
        return cls(
            account_id=int(row["account_id"]),
            network=row.get("network"),
            last4=row.get("last4"),
            credit_limit_minor=int(row["credit_limit_minor"]),
            statement_day=int(row["statement_day"]),
            due_day_offset=int(row["due_day_offset"]),
            autopay=bool(row.get("autopay", 0)),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )


@dataclass(frozen=True)
class CreditCard:
    """Account + profile satellite — the credit-card aggregate."""

    account: Account
    profile: CreditCardProfile

    @property
    def id(self) -> int:
        return self.account.id

    @property
    def name(self) -> str:
        return self.account.name


@dataclass(frozen=True)
class Statement:
    id: int
    account_id: int
    period_start: str
    period_end: str
    statement_date: str
    due_date: str
    total_due_minor: Optional[int]
    min_due_minor: Optional[int]
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: dict) -> Statement:
        return cls(
            id=int(row["id"]),
            account_id=int(row["account_id"]),
            period_start=str(row["period_start"]),
            period_end=str(row["period_end"]),
            statement_date=str(row["statement_date"]),
            due_date=str(row["due_date"]),
            total_due_minor=row.get("total_due_minor"),
            min_due_minor=row.get("min_due_minor"),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )


@dataclass(frozen=True)
class Transaction:
    id: int
    account_id: int
    direction: str
    kind: str
    amount_minor: int
    category_id: Optional[int]
    merchant_id: Optional[int]
    note: Optional[str]
    occurred_on: str
    transfer_group_id: Optional[str]
    statement_id: Optional[int]
    source: str
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: dict) -> Transaction:
        return cls(
            id=int(row["id"]),
            account_id=int(row["account_id"]),
            direction=str(row["direction"]),
            kind=str(row["kind"]),
            amount_minor=int(row["amount_minor"]),
            category_id=row.get("category_id"),
            merchant_id=row.get("merchant_id"),
            note=row.get("note"),
            occurred_on=str(row["occurred_on"]),
            transfer_group_id=row.get("transfer_group_id"),
            statement_id=row.get("statement_id"),
            source=str(row["source"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )
