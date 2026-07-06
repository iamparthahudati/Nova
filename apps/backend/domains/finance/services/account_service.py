"""Account aggregate service."""

from __future__ import annotations

from datetime import date
from typing import Optional

from ..aggregates import Account
from ..errors import AccountArchivedError, AccountNotFoundError, FinanceValidationError
from ..money import classification_for_type
from ..repository_adapters import SqliteAccountRepository
from ..validation import validate_account_name, validate_account_type


class AccountService:
    def __init__(self, accounts: Optional[SqliteAccountRepository] = None) -> None:
        self._accounts = accounts or SqliteAccountRepository()

    def create_account(
        self,
        name: str,
        account_type: str,
        opening_balance_minor: int = 0,
        opening_balance_on: Optional[str] = None,
        today: Optional[date] = None,
    ) -> Account:
        today = today or date.today()
        clean_name = validate_account_name(name)
        clean_type = validate_account_type(account_type)
        balance_on = opening_balance_on or today.isoformat()
        fields = {
            "name": clean_name,
            "type": clean_type,
            "classification": classification_for_type(clean_type),
            "opening_balance_minor": opening_balance_minor,
            "opening_balance_on": balance_on,
        }
        return self._accounts.create(fields)

    def get_account(self, account_id: int) -> Account:
        account = self._accounts.get_by_id(account_id)
        if account is None:
            raise AccountNotFoundError(account_id)
        return account

    def list_accounts(self) -> list[Account]:
        return self._accounts.list_live()

    def update_account(
        self,
        account_id: int,
        name: Optional[str] = None,
        opening_balance_minor: Optional[int] = None,
        opening_balance_on: Optional[str] = None,
    ) -> Account:
        account = self.get_account(account_id)
        if account.archived_at is not None:
            raise AccountArchivedError(account_id)
        if self._accounts.count_live_transactions(account_id) > 0:
            if opening_balance_minor is not None or opening_balance_on is not None:
                raise FinanceValidationError(
                    "Opening balance is locked after the first transaction",
                )
        fields: dict = {}
        if name is not None:
            fields["name"] = validate_account_name(name)
        if opening_balance_minor is not None:
            fields["opening_balance_minor"] = opening_balance_minor
        if opening_balance_on is not None:
            fields["opening_balance_on"] = opening_balance_on
        updated = self._accounts.update(account_id, fields)
        if updated is None:
            raise AccountNotFoundError(account_id)
        return updated

    def archive_account(self, account_id: int) -> Account:
        account = self.get_account(account_id)
        if account.archived_at is not None:
            raise AccountArchivedError(account_id)
        archived = self._accounts.archive(account_id)
        if archived is None:
            raise AccountNotFoundError(account_id)
        return archived
