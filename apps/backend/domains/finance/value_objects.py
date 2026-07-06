"""Closed enums and constants for the finance domain."""

from __future__ import annotations

from enum import Enum


class AccountType(str, Enum):
    CASH = "cash"
    BANK = "bank"
    WALLET = "wallet"
    CREDIT_CARD = "credit_card"


class Classification(str, Enum):
    ASSET = "asset"
    LIABILITY = "liability"


class Direction(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"


class TransactionKind(str, Enum):
    EXPENSE = "expense"
    INCOME = "income"
    TRANSFER = "transfer"
    CARD_PAYMENT = "card_payment"
    ADJUSTMENT = "adjustment"


class TransactionSource(str, Enum):
    MANUAL = "manual"
    CHAT = "chat"
    VOICE = "voice"
    MIGRATED_MONEY = "migrated_money"


ASSET_ACCOUNT_TYPES = {AccountType.CASH, AccountType.BANK, AccountType.WALLET}
LIABILITY_ACCOUNT_TYPES = {AccountType.CREDIT_CARD}

KIND_DIRECTION: dict[TransactionKind, Direction] = {
    TransactionKind.EXPENSE: Direction.DEBIT,
    TransactionKind.INCOME: Direction.CREDIT,
    TransactionKind.TRANSFER: Direction.DEBIT,
    TransactionKind.ADJUSTMENT: Direction.DEBIT,
}
