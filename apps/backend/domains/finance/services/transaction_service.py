"""Transaction aggregate service."""

from __future__ import annotations

from datetime import date
from typing import Optional

from ..aggregates import Transaction
from ..errors import (
    AccountArchivedError,
    AccountNotFoundError,
    FinanceValidationError,
    TransactionNotFoundError,
)
from ..money import MoneyAmount, OccurredOn
from ..repository_adapters import SqliteAccountRepository, SqliteTransactionRepository
from ..validation import direction_for_kind, validate_occurred_on, validate_transaction_kind
from ..value_objects import TransactionKind, TransactionSource


class TransactionService:
    def __init__(
        self,
        transactions: Optional[SqliteTransactionRepository] = None,
        accounts: Optional[SqliteAccountRepository] = None,
    ) -> None:
        self._transactions = transactions or SqliteTransactionRepository()
        self._accounts = accounts or SqliteAccountRepository()

    def _require_live_account(self, account_id: int):
        account = self._accounts.get_by_id(account_id)
        if account is None:
            raise AccountNotFoundError(account_id)
        if account.archived_at is not None:
            raise AccountArchivedError(account_id)
        return account

    def create_transaction(
        self,
        account_id: int,
        kind: str,
        amount_minor: int,
        occurred_on: str,
        category_id: Optional[int] = None,
        merchant_id: Optional[int] = None,
        note: Optional[str] = None,
        direction: Optional[str] = None,
        source: str = TransactionSource.MANUAL.value,
        today: Optional[date] = None,
    ) -> Transaction:
        today = today or date.today()
        if amount_minor <= 0:
            raise FinanceValidationError("amount_minor must be positive")
        txn_kind = validate_transaction_kind(kind)
        account = self._require_live_account(account_id)
        occurred = validate_occurred_on(occurred_on, account.opening_balance_on, today)
        txn_direction = direction_for_kind(txn_kind, direction)
        fields = {
            "account_id": account_id,
            "direction": txn_direction,
            "kind": txn_kind.value,
            "amount_minor": amount_minor,
            "category_id": category_id,
            "merchant_id": merchant_id,
            "note": note,
            "occurred_on": occurred.value,
            "source": source,
        }
        return self._transactions.create(fields)

    def log_legacy_spending(
        self,
        type_: str,
        amount: float,
        note: str = "",
        source: str = TransactionSource.CHAT.value,
        today: Optional[date] = None,
    ) -> Transaction:
        """Bridge from legacy earned/spent to ledger transactions on Cash."""
        today = today or date.today()
        if type_ not in {"earned", "spent"}:
            raise FinanceValidationError(f"Invalid spending type: {type_}")
        money = MoneyAmount.from_rupees(amount)
        account_id = self._transactions.ensure_default_cash_account_id()
        kind = TransactionKind.INCOME.value if type_ == "earned" else TransactionKind.EXPENSE.value
        return self.create_transaction(
            account_id=account_id,
            kind=kind,
            amount_minor=money.minor,
            occurred_on=OccurredOn.today(today).value,
            note=note,
            source=source,
            today=today,
        )

    def get_transaction(self, transaction_id: int) -> Transaction:
        txn = self._transactions.get_by_id(transaction_id)
        if txn is None:
            raise TransactionNotFoundError(transaction_id)
        return txn

    def list_transactions(
        self,
        account_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Transaction]:
        return self._transactions.list_live(account_id, limit, offset)

    def update_transaction(
        self,
        transaction_id: int,
        amount_minor: Optional[int] = None,
        category_id: Optional[int] = None,
        merchant_id: Optional[int] = None,
        note: Optional[str] = None,
        occurred_on: Optional[str] = None,
        today: Optional[date] = None,
    ) -> Transaction:
        today = today or date.today()
        txn = self.get_transaction(transaction_id)
        if txn.transfer_group_id:
            if txn.kind == "card_payment":
                raise FinanceValidationError("Use PaymentService to edit card payment legs")
            raise FinanceValidationError("Use TransferService to edit transfer legs")
        account = self._accounts.get_by_id(txn.account_id)
        if account is None:
            raise AccountNotFoundError(txn.account_id)
        fields: dict = {}
        if amount_minor is not None:
            if amount_minor <= 0:
                raise FinanceValidationError("amount_minor must be positive")
            fields["amount_minor"] = amount_minor
        if category_id is not None:
            fields["category_id"] = category_id
        if merchant_id is not None:
            fields["merchant_id"] = merchant_id
        if note is not None:
            fields["note"] = note
        if occurred_on is not None:
            occurred = validate_occurred_on(occurred_on, account.opening_balance_on, today)
            fields["occurred_on"] = occurred.value
        updated = self._transactions.update(transaction_id, fields)
        if updated is None:
            raise TransactionNotFoundError(transaction_id)
        return updated

    def delete_transaction(self, transaction_id: int) -> Transaction:
        txn = self.get_transaction(transaction_id)
        if txn.transfer_group_id:
            self._transactions.soft_delete_transfer_group(txn.transfer_group_id)
            return txn
        if not self._transactions.soft_delete(transaction_id):
            raise TransactionNotFoundError(transaction_id)
        return txn
