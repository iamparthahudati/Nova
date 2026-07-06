"""Payment validation — pure, no I/O."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from ..errors import FinanceValidationError, PaymentConfirmationRequiredError
from ..value_objects import ASSET_ACCOUNT_TYPES, AccountType


class PaymentMode(str, Enum):
    FULL = "full"
    MINIMUM = "minimum"
    PARTIAL = "partial"


def validate_payment_amount(amount_minor: int) -> int:
    if amount_minor <= 0:
        raise FinanceValidationError("Payment amount must be positive")
    return amount_minor


def validate_asset_account(account_type: str, account_id: int) -> None:
    try:
        kind = AccountType(account_type)
    except ValueError as exc:
        raise FinanceValidationError(
            f"Invalid payment source account type: {account_type}"
        ) from exc
    if kind not in ASSET_ACCOUNT_TYPES:
        raise FinanceValidationError(
            f"Payment source account {account_id} must be an asset account",
        )


def validate_credit_card_account(account_type: str, account_id: int) -> None:
    if account_type != AccountType.CREDIT_CARD.value:
        raise FinanceValidationError(
            f"Payment target account {account_id} must be a credit card",
        )


def resolve_statement_payment_amount(
    payment_mode: PaymentMode,
    amount_minor: Optional[int],
    total_due_minor: Optional[int],
    min_due_minor: Optional[int],
    paid_minor: int,
) -> int:
    if payment_mode == PaymentMode.PARTIAL:
        if amount_minor is None:
            raise FinanceValidationError("amount_minor is required for partial payment")
        return validate_payment_amount(amount_minor)

    if payment_mode == PaymentMode.FULL:
        if total_due_minor is None:
            raise FinanceValidationError("total_due_minor must be entered before full payment")
        remaining = total_due_minor - paid_minor
        if remaining <= 0:
            raise FinanceValidationError("Statement is already fully paid")
        return remaining

    if min_due_minor is None:
        raise FinanceValidationError("min_due_minor must be entered before minimum payment")
    remaining_min = max(min_due_minor - paid_minor, 0)
    if remaining_min <= 0:
        raise FinanceValidationError("Minimum payment obligation is already satisfied")
    return remaining_min


def validate_overpayment(
    amount_minor: int,
    total_due_minor: Optional[int],
    paid_minor: int,
    confirm_overpayment: bool,
) -> None:
    if total_due_minor is None:
        return
    remaining = total_due_minor - paid_minor
    if amount_minor > remaining and not confirm_overpayment:
        raise PaymentConfirmationRequiredError(
            "Payment exceeds remaining statement due; confirm overpayment to proceed",
        )
