"""Transfer orchestration — writes paired transaction legs."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from ..aggregates import Transaction
from ..errors import (
    AccountArchivedError,
    AccountNotFoundError,
    FinanceValidationError,
    TransferInvariantError,
)
from ..repository_adapters import SqliteAccountRepository, SqliteTransactionRepository
from ..validation import validate_occurred_on
from ..value_objects import Direction, TransactionKind, TransactionSource


class TransferService:
    def __init__(
        self,
        transactions: Optional[SqliteTransactionRepository] = None,
        accounts: Optional[SqliteAccountRepository] = None,
    ) -> None:
        self._transactions = transactions or SqliteTransactionRepository()
        self._accounts = accounts or SqliteAccountRepository()

    def create_transfer(
        self,
        from_account_id: int,
        to_account_id: int,
        amount_minor: int,
        occurred_on: str,
        note: Optional[str] = None,
        source: str = TransactionSource.MANUAL.value,
        today: Optional[date] = None,
    ) -> tuple[list[Transaction], str]:
        today = today or date.today()
        if from_account_id == to_account_id:
            raise FinanceValidationError("Transfer accounts must differ")
        if amount_minor <= 0:
            raise FinanceValidationError("amount_minor must be positive")

        from_account = self._accounts.get_by_id(from_account_id)
        to_account = self._accounts.get_by_id(to_account_id)
        if from_account is None:
            raise AccountNotFoundError(from_account_id)
        if to_account is None:
            raise AccountNotFoundError(to_account_id)
        if from_account.archived_at is not None:
            raise AccountArchivedError(from_account_id)
        if to_account.archived_at is not None:
            raise AccountArchivedError(to_account_id)

        occurred = validate_occurred_on(
            occurred_on,
            max(from_account.opening_balance_on, to_account.opening_balance_on),
            today,
        )
        group_id = str(uuid.uuid4())
        debit_leg = self._transactions.create(
            {
                "account_id": from_account_id,
                "direction": Direction.DEBIT.value,
                "kind": TransactionKind.TRANSFER.value,
                "amount_minor": amount_minor,
                "note": note,
                "occurred_on": occurred.value,
                "transfer_group_id": group_id,
                "source": source,
            },
        )
        credit_leg = self._transactions.create(
            {
                "account_id": to_account_id,
                "direction": Direction.CREDIT.value,
                "kind": TransactionKind.TRANSFER.value,
                "amount_minor": amount_minor,
                "note": note,
                "occurred_on": occurred.value,
                "transfer_group_id": group_id,
                "source": source,
            },
        )
        legs = [debit_leg, credit_leg]
        self._assert_transfer_pair(legs, group_id)
        return legs, group_id

    def delete_transfer(self, transfer_group_id: str) -> list[Transaction]:
        legs = self._transactions.list_by_transfer_group(transfer_group_id)
        if len(legs) != 2:
            raise TransferInvariantError("Transfer group must have exactly two live legs")
        self._transactions.soft_delete_transfer_group(transfer_group_id)
        return legs

    def _assert_transfer_pair(self, legs: list[Transaction], group_id: str) -> None:
        if len(legs) != 2:
            raise TransferInvariantError("Transfer requires exactly two legs")
        directions = {leg.direction for leg in legs}
        if directions != {Direction.DEBIT.value, Direction.CREDIT.value}:
            raise TransferInvariantError("Transfer legs must have opposite directions")
        if legs[0].amount_minor != legs[1].amount_minor:
            raise TransferInvariantError("Transfer legs must have equal amounts")
        if legs[0].account_id == legs[1].account_id:
            raise TransferInvariantError("Transfer legs must use distinct accounts")
        if any(leg.transfer_group_id != group_id for leg in legs):
            raise TransferInvariantError("Transfer legs must share transfer_group_id")
