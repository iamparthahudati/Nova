"""Shared finance validation — pure, no I/O."""

from __future__ import annotations

from datetime import date

from .credit_card import CreditLimit
from .cycle import clamp_statement_day
from .errors import FinanceValidationError
from .money import OccurredOn
from .value_objects import AccountType, Direction, TransactionKind


def validate_account_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise FinanceValidationError("Account name is required")
    return cleaned


def validate_account_type(account_type: str) -> str:
    try:
        return AccountType(account_type).value
    except ValueError as exc:
        raise FinanceValidationError(f"Invalid account type: {account_type}") from exc


def validate_category_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise FinanceValidationError("Category name is required")
    return cleaned


def validate_merchant_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise FinanceValidationError("Merchant name is required")
    return cleaned


def validate_transaction_kind(kind: str) -> TransactionKind:
    try:
        return TransactionKind(kind)
    except ValueError as exc:
        raise FinanceValidationError(f"Invalid transaction kind: {kind}") from exc


def direction_for_kind(kind: TransactionKind, explicit: str | None = None) -> str:
    if kind == TransactionKind.ADJUSTMENT:
        if explicit not in {Direction.DEBIT.value, Direction.CREDIT.value}:
            raise FinanceValidationError("Adjustment requires explicit direction")
        return explicit
    if kind == TransactionKind.EXPENSE:
        return Direction.DEBIT.value
    if kind == TransactionKind.INCOME:
        return Direction.CREDIT.value
    if kind == TransactionKind.TRANSFER:
        raise FinanceValidationError("Use TransferService for transfer transactions")
    if kind == TransactionKind.CARD_PAYMENT:
        raise FinanceValidationError("Use PaymentService for card payment transactions")
    raise FinanceValidationError(f"Unsupported kind: {kind.value}")


def validate_occurred_on(
    occurred_on: str,
    opening_balance_on: str,
    today: date,
) -> OccurredOn:
    occurred = OccurredOn.from_iso(occurred_on)
    occurred.validate_not_before(opening_balance_on)
    occurred.validate_not_far_future(today)
    return occurred


def validate_credit_limit(credit_limit_minor: int) -> int:
    return CreditLimit.from_minor(credit_limit_minor).minor


def validate_statement_day(statement_day: int) -> int:
    if statement_day < 1 or statement_day > 31:
        raise FinanceValidationError("statement_day must be between 1 and 31")
    return statement_day


def validate_due_day_offset(due_day_offset: int) -> int:
    if due_day_offset <= 0:
        raise FinanceValidationError("due_day_offset must be positive")
    return due_day_offset


def validate_statement_totals(
    total_due_minor: int | None,
    min_due_minor: int | None,
) -> None:
    if total_due_minor is not None and total_due_minor < 0:
        raise FinanceValidationError("total_due_minor must be >= 0")
    if min_due_minor is not None and min_due_minor < 0:
        raise FinanceValidationError("min_due_minor must be >= 0")
    if (
        total_due_minor is not None
        and min_due_minor is not None
        and min_due_minor > total_due_minor
    ):
        raise FinanceValidationError("min_due_minor cannot exceed total_due_minor")


def validate_statement_dates(
    period_start: str,
    period_end: str,
    due_date: str,
) -> None:
    start = date.fromisoformat(period_start)
    end = date.fromisoformat(period_end)
    due = date.fromisoformat(due_date)
    if end < start:
        raise FinanceValidationError("period_end must be >= period_start")
    if due <= end:
        raise FinanceValidationError("due_date must be after period_end")


def validate_credit_card_profile_fields(
    credit_limit_minor: int,
    statement_day: int,
    due_day_offset: int,
) -> tuple[int, int, int]:
    limit = validate_credit_limit(credit_limit_minor)
    day = validate_statement_day(statement_day)
    clamp_statement_day(2024, 1, day)
    offset = validate_due_day_offset(due_day_offset)
    return limit, day, offset
