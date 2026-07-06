"""SQLite repository adapters — call memory.finance only."""

from __future__ import annotations

from typing import Optional

from memory.finance import accounts as account_store
from memory.finance import card_profiles as card_profile_store
from memory.finance import categories as category_store
from memory.finance import merchants as merchant_store
from memory.finance import seed
from memory.finance import statements as statement_store
from memory.finance import transactions as transaction_store

from .aggregates import (
    Account,
    Category,
    CreditCard,
    CreditCardProfile,
    Merchant,
    Statement,
    Transaction,
)


class SqliteAccountRepository:
    def create(self, fields: dict) -> Account:
        return Account.from_row(account_store.create_account(fields))

    def get_by_id(self, account_id: int) -> Optional[Account]:
        row = account_store.get_account_by_id(account_id)
        return Account.from_row(row) if row else None

    def list_live(self) -> list[Account]:
        return [Account.from_row(row) for row in account_store.list_accounts()]

    def update(self, account_id: int, fields: dict) -> Optional[Account]:
        row = account_store.update_account(account_id, fields)
        return Account.from_row(row) if row else None

    def archive(self, account_id: int) -> Optional[Account]:
        row = account_store.archive_account(account_id)
        return Account.from_row(row) if row else None

    def count_live_transactions(self, account_id: int) -> int:
        return account_store.count_live_transactions(account_id)


class SqliteCategoryRepository:
    def create(self, name: str) -> Category:
        return Category.from_row(category_store.create_category(name))

    def get_by_id(self, category_id: int) -> Optional[Category]:
        row = category_store.get_category_by_id(category_id)
        return Category.from_row(row) if row else None

    def get_by_name(self, name: str) -> Optional[Category]:
        row = category_store.get_category_by_name(name)
        return Category.from_row(row) if row else None

    def list_live(self) -> list[Category]:
        return [Category.from_row(row) for row in category_store.list_categories()]

    def update(self, category_id: int, name: str) -> Optional[Category]:
        row = category_store.update_category(category_id, name)
        return Category.from_row(row) if row else None

    def soft_delete(self, category_id: int) -> bool:
        return category_store.soft_delete_category(category_id)


class SqliteMerchantRepository:
    def create(self, name: str) -> Merchant:
        return Merchant.from_row(merchant_store.create_merchant(name))

    def get_by_id(self, merchant_id: int) -> Optional[Merchant]:
        row = merchant_store.get_merchant_by_id(merchant_id)
        return Merchant.from_row(row) if row else None

    def get_by_name(self, name: str) -> Optional[Merchant]:
        row = merchant_store.get_merchant_by_name(name)
        return Merchant.from_row(row) if row else None

    def list_live(self) -> list[Merchant]:
        return [Merchant.from_row(row) for row in merchant_store.list_merchants()]

    def update(self, merchant_id: int, name: str) -> Optional[Merchant]:
        row = merchant_store.update_merchant(merchant_id, name)
        return Merchant.from_row(row) if row else None

    def soft_delete(self, merchant_id: int) -> bool:
        return merchant_store.soft_delete_merchant(merchant_id)


class SqliteTransactionRepository:
    def create(self, fields: dict) -> Transaction:
        return Transaction.from_row(transaction_store.create_transaction(fields))

    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        row = transaction_store.get_transaction_by_id(transaction_id)
        return Transaction.from_row(row) if row else None

    def list_live(
        self,
        account_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Transaction]:
        rows = transaction_store.list_transactions(account_id, limit, offset)
        return [Transaction.from_row(row) for row in rows]

    def list_by_transfer_group(self, transfer_group_id: str) -> list[Transaction]:
        rows = transaction_store.list_by_transfer_group(transfer_group_id)
        return [Transaction.from_row(row) for row in rows]

    def update(self, transaction_id: int, fields: dict) -> Optional[Transaction]:
        row = transaction_store.update_transaction(transaction_id, fields)
        return Transaction.from_row(row) if row else None

    def soft_delete(self, transaction_id: int) -> bool:
        return transaction_store.soft_delete_transaction(transaction_id)

    def soft_delete_transfer_group(self, transfer_group_id: str) -> int:
        return transaction_store.soft_delete_transfer_group(transfer_group_id)

    def sum_by_direction(self, account_id: int, as_of: Optional[str] = None) -> tuple[int, int]:
        return transaction_store.sum_by_direction(account_id, as_of)

    def totals_between(self, start_date: str, end_date: str) -> tuple[int, int]:
        return transaction_store.totals_between(start_date, end_date)

    def get_latest_income_expense(self, kind: str, amount_minor: int) -> Optional[Transaction]:
        row = transaction_store.get_latest_income_expense(kind, amount_minor)
        return Transaction.from_row(row) if row else None

    def ensure_default_cash_account_id(self) -> int:
        return seed.ensure_default_cash_account()


class SqliteCreditCardRepository:
    def create(self, account_fields: dict, profile_fields: dict) -> CreditCard:
        account_row, profile_row = card_profile_store.create_credit_card_account(
            account_fields,
            profile_fields,
        )
        return CreditCard(
            account=Account.from_row(account_row),
            profile=CreditCardProfile.from_row(profile_row),
        )

    def get_by_id(self, account_id: int) -> Optional[CreditCard]:
        account_row = account_store.get_account_by_id(account_id)
        if account_row is None or account_row["type"] != "credit_card":
            return None
        profile_row = card_profile_store.get_card_profile(account_id)
        if profile_row is None:
            return None
        return CreditCard(
            account=Account.from_row(account_row),
            profile=CreditCardProfile.from_row(profile_row),
        )

    def list_live(self) -> list[CreditCard]:
        cards = []
        for profile_row in card_profile_store.list_card_profiles():
            account_row = account_store.get_account_by_id(profile_row["account_id"])
            if account_row is None:
                continue
            cards.append(
                CreditCard(
                    account=Account.from_row(account_row),
                    profile=CreditCardProfile.from_row(profile_row),
                ),
            )
        return cards

    def update_profile(self, account_id: int, fields: dict) -> Optional[CreditCardProfile]:
        row = card_profile_store.update_card_profile(account_id, fields)
        return CreditCardProfile.from_row(row) if row else None


class SqliteStatementRepository:
    def create(self, fields: dict) -> Statement:
        return Statement.from_row(statement_store.create_statement(fields))

    def get_by_id(self, statement_id: int) -> Optional[Statement]:
        row = statement_store.get_statement_by_id(statement_id)
        return Statement.from_row(row) if row else None

    def get_by_period(self, account_id: int, period_start: str) -> Optional[Statement]:
        row = statement_store.get_statement_by_period(account_id, period_start)
        return Statement.from_row(row) if row else None

    def list_for_account(self, account_id: int, limit: int = 24) -> list[Statement]:
        rows = statement_store.list_statements(account_id, limit)
        return [Statement.from_row(row) for row in rows]

    def update(self, statement_id: int, fields: dict) -> Optional[Statement]:
        row = statement_store.update_statement(statement_id, fields)
        return Statement.from_row(row) if row else None

    def soft_delete(self, statement_id: int) -> bool:
        return statement_store.soft_delete_statement(statement_id)

    def count_overlapping(
        self,
        account_id: int,
        period_start: str,
        period_end: str,
        exclude_id: Optional[int] = None,
    ) -> int:
        return statement_store.count_overlapping_periods(
            account_id,
            period_start,
            period_end,
            exclude_id,
        )

    def count_linked_transactions(self, statement_id: int) -> int:
        return statement_store.count_linked_transactions(statement_id)

    def sum_statement_spend(self, statement_id: int) -> tuple[int, int]:
        return statement_store.sum_statement_spend(statement_id)

    def sum_spend_in_period(
        self, account_id: int, period_start: str, period_end: str
    ) -> tuple[int, int]:
        return statement_store.sum_spend_in_period(account_id, period_start, period_end)

    def sum_statement_paid(self, statement_id: int) -> int:
        return statement_store.sum_statement_paid(statement_id)
