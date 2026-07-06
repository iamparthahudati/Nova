"""Card payment and statement pay orchestration."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from ..aggregates import Transaction
from ..errors import (
    AccountArchivedError,
    AccountNotFoundError,
    FinanceValidationError,
    StatementNotFoundError,
    TransferInvariantError,
)
from ..repository_adapters import (
    SqliteAccountRepository,
    SqliteCreditCardRepository,
    SqliteStatementRepository,
    SqliteTransactionRepository,
)
from ..validation import validate_occurred_on
from ..value_objects import Direction, TransactionKind, TransactionSource
from .validation import (
    PaymentMode,
    resolve_statement_payment_amount,
    validate_asset_account,
    validate_credit_card_account,
    validate_overpayment,
    validate_payment_amount,
)


class PaymentService:
    def __init__(
        self,
        transactions: Optional[SqliteTransactionRepository] = None,
        accounts: Optional[SqliteAccountRepository] = None,
        cards: Optional[SqliteCreditCardRepository] = None,
        statements: Optional[SqliteStatementRepository] = None,
    ) -> None:
        self._transactions = transactions or SqliteTransactionRepository()
        self._accounts = accounts or SqliteAccountRepository()
        self._cards = cards or SqliteCreditCardRepository()
        self._statements = statements or SqliteStatementRepository()

    def create_card_payment(
        self,
        from_account_id: int,
        card_account_id: int,
        amount_minor: int,
        occurred_on: str,
        statement_id: Optional[int] = None,
        note: Optional[str] = None,
        confirm_overpayment: bool = False,
        source: str = TransactionSource.MANUAL.value,
        today: Optional[date] = None,
    ) -> tuple[list[Transaction], str]:
        """Pay a credit card from an asset account — paired card_payment legs."""
        today = today or date.today()
        amount = validate_payment_amount(amount_minor)
        from_account, card = self._validate_payment_accounts(from_account_id, card_account_id)
        self._validate_statement_payment(
            statement_id,
            card_account_id,
            amount,
            confirm_overpayment,
        )
        occurred = validate_occurred_on(
            occurred_on,
            max(from_account.opening_balance_on, card.account.opening_balance_on),
            today,
        )
        return self._write_payment_pair(
            from_account_id,
            card_account_id,
            amount,
            occurred.value,
            statement_id,
            note,
            source,
        )

    def pay_statement(
        self,
        statement_id: int,
        from_account_id: int,
        payment_mode: str = PaymentMode.PARTIAL.value,
        amount_minor: Optional[int] = None,
        note: Optional[str] = None,
        confirm_overpayment: bool = False,
        source: str = TransactionSource.MANUAL.value,
        today: Optional[date] = None,
    ) -> tuple[list[Transaction], str]:
        """Orchestrate a statement payment via a card_payment pair."""
        today = today or date.today()
        statement = self._statements.get_by_id(statement_id)
        if statement is None:
            raise StatementNotFoundError(statement_id)

        mode = PaymentMode(payment_mode)
        paid_minor = self._statements.sum_statement_paid(statement_id)
        resolved = resolve_statement_payment_amount(
            mode,
            amount_minor,
            statement.total_due_minor,
            statement.min_due_minor,
            paid_minor,
        )
        return self.create_card_payment(
            from_account_id=from_account_id,
            card_account_id=statement.account_id,
            amount_minor=resolved,
            occurred_on=today.isoformat(),
            statement_id=statement_id,
            note=note,
            confirm_overpayment=confirm_overpayment,
            source=source,
            today=today,
        )

    def delete_card_payment(self, transfer_group_id: str) -> list[Transaction]:
        legs = self._transactions.list_by_transfer_group(transfer_group_id)
        if len(legs) != 2:
            raise TransferInvariantError("Card payment group must have exactly two live legs")
        if legs[0].kind != TransactionKind.CARD_PAYMENT.value:
            raise FinanceValidationError("Not a card payment transfer group")
        self._transactions.soft_delete_transfer_group(transfer_group_id)
        return legs

    def _validate_payment_accounts(self, from_account_id: int, card_account_id: int):
        if from_account_id == card_account_id:
            raise FinanceValidationError("Payment accounts must differ")
        from_account = self._accounts.get_by_id(from_account_id)
        card = self._cards.get_by_id(card_account_id)
        if from_account is None:
            raise AccountNotFoundError(from_account_id)
        if card is None:
            raise AccountNotFoundError(card_account_id)
        if from_account.archived_at is not None:
            raise AccountArchivedError(from_account_id)
        if card.account.archived_at is not None:
            raise AccountArchivedError(card_account_id)
        validate_asset_account(from_account.type, from_account_id)
        validate_credit_card_account(card.account.type, card_account_id)
        return from_account, card

    def _validate_statement_payment(
        self,
        statement_id: Optional[int],
        card_account_id: int,
        amount: int,
        confirm_overpayment: bool,
    ) -> None:
        if statement_id is None:
            return
        statement = self._statements.get_by_id(statement_id)
        if statement is None:
            raise StatementNotFoundError(statement_id)
        if statement.account_id != card_account_id:
            raise FinanceValidationError("Statement does not belong to this card")
        paid_minor = self._statements.sum_statement_paid(statement_id)
        validate_overpayment(
            amount,
            statement.total_due_minor,
            paid_minor,
            confirm_overpayment,
        )

    def _write_payment_pair(
        self,
        from_account_id: int,
        card_account_id: int,
        amount: int,
        occurred_on: str,
        statement_id: Optional[int],
        note: Optional[str],
        source: str,
    ) -> tuple[list[Transaction], str]:
        group_id = str(uuid.uuid4())
        debit_leg = self._transactions.create(
            {
                "account_id": from_account_id,
                "direction": Direction.DEBIT.value,
                "kind": TransactionKind.CARD_PAYMENT.value,
                "amount_minor": amount,
                "note": note,
                "occurred_on": occurred_on,
                "transfer_group_id": group_id,
                "source": source,
            },
        )
        credit_fields: dict = {
            "account_id": card_account_id,
            "direction": Direction.CREDIT.value,
            "kind": TransactionKind.CARD_PAYMENT.value,
            "amount_minor": amount,
            "note": note,
            "occurred_on": occurred_on,
            "transfer_group_id": group_id,
            "source": source,
        }
        if statement_id is not None:
            credit_fields["statement_id"] = statement_id
        credit_leg = self._transactions.create(credit_fields)
        legs = [debit_leg, credit_leg]
        self._assert_payment_pair(legs, group_id)
        return legs, group_id

    def _assert_payment_pair(self, legs: list[Transaction], group_id: str) -> None:
        if len(legs) != 2:
            raise TransferInvariantError("Card payment requires exactly two legs")
        directions = {leg.direction for leg in legs}
        if directions != {Direction.DEBIT.value, Direction.CREDIT.value}:
            raise TransferInvariantError("Card payment legs must have opposite directions")
        if legs[0].amount_minor != legs[1].amount_minor:
            raise TransferInvariantError("Card payment legs must have equal amounts")
        if legs[0].account_id == legs[1].account_id:
            raise TransferInvariantError("Card payment legs must use distinct accounts")
        if any(leg.kind != TransactionKind.CARD_PAYMENT.value for leg in legs):
            raise TransferInvariantError("Card payment legs must use kind card_payment")
        if any(leg.transfer_group_id != group_id for leg in legs):
            raise TransferInvariantError("Card payment legs must share transfer_group_id")
