"""Finance domain foundation tests — real SQLite, no mocks."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from domains.finance.errors import (
    AccountArchivedError,
    FinanceValidationError,
)
from domains.finance.mutations import (
    build_account_created,
    build_spending_logged_from_transaction,
    build_transfer_created,
)
from domains.finance.services.account_service import AccountService
from domains.finance.services.category_service import CategoryService
from domains.finance.services.merchant_service import MerchantService
from domains.finance.services.projection_service import ProjectionService
from domains.finance.services.transaction_service import TransactionService
from domains.finance.services.transfer_service import TransferService
from memory import _connection
from memory.schema import init_db


class FinanceDomainTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmpdir.name) / "test.db"
        self.lance_path = Path(self._tmpdir.name) / "lancedb"
        self._patches = [
            patch.object(_connection, "DB_PATH", self.db_path),
            patch.object(_connection, "LANCEDB_PATH", self.lance_path),
        ]
        for patcher in self._patches:
            patcher.start()
        _connection.ensure_storage_paths()
        init_db()
        self.today = date.today()
        self.accounts = AccountService()
        self.categories = CategoryService()
        self.merchants = MerchantService()
        self.transactions = TransactionService()
        self.transfers = TransferService()
        self.projections = ProjectionService()

    def tearDown(self) -> None:
        for patcher in self._patches:
            patcher.stop()
        self._tmpdir.cleanup()

    def _cash_account(self):
        return next(account for account in self.accounts.list_accounts() if account.name == "Cash")

    def test_default_cash_account_seeded(self) -> None:
        accounts = self.accounts.list_accounts()
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0].name, "Cash")
        self.assertEqual(accounts[0].type, "cash")

    def test_account_crud_and_archive(self) -> None:
        account = self.accounts.create_account("HDFC Savings", "bank", today=self.today)
        event = build_account_created(account)
        self.assertEqual(event.event_type, "finance.account.created")
        self.assertEqual(event.entity_type, "account")

        updated = self.accounts.update_account(account.id, name="HDFC Bank")
        self.assertEqual(updated.name, "HDFC Bank")

        archived = self.accounts.archive_account(account.id)
        self.assertIsNotNone(archived.archived_at)
        with self.assertRaises(AccountArchivedError):
            self.transactions.create_transaction(
                account.id,
                "expense",
                10000,
                self.today.isoformat(),
                today=self.today,
            )

    def test_category_and_merchant_crud(self) -> None:
        category = self.categories.create_category("Food")
        merchant = self.merchants.create_merchant("Swiggy")
        self.assertEqual(category.name, "Food")
        self.assertEqual(merchant.name, "Swiggy")

        updated_category = self.categories.update_category(category.id, "Dining")
        self.assertEqual(updated_category.name, "Dining")

        self.categories.delete_category(category.id)
        self.merchants.delete_merchant(merchant.id)

    def test_transaction_create_and_balance_projection(self) -> None:
        cash = self._cash_account()
        txn = self.transactions.create_transaction(
            cash.id,
            "expense",
            25000,
            self.today.isoformat(),
            note="Groceries",
            today=self.today,
        )
        self.assertEqual(txn.amount_minor, 25000)
        balance = self.projections.compute_account_balance(cash.id)
        self.assertEqual(balance, -25000)

        income = self.transactions.create_transaction(
            cash.id,
            "income",
            50000,
            self.today.isoformat(),
            today=self.today,
        )
        balance = self.projections.compute_account_balance(cash.id)
        self.assertEqual(balance, 25000)

        legacy = build_spending_logged_from_transaction(income)
        self.assertEqual(legacy.event_type, "spending.logged")
        self.assertEqual(legacy.entity["type"], "earned")

    def test_transfer_pair_invariant(self) -> None:
        bank = self.accounts.create_account("Bank", "bank", today=self.today)
        cash = self._cash_account()
        legs, group_id = self.transfers.create_transfer(
            bank.id,
            cash.id,
            100000,
            self.today.isoformat(),
            today=self.today,
        )
        event = build_transfer_created(legs, group_id)
        self.assertEqual(event.event_type, "finance.transfer.created")
        self.assertEqual(len(legs), 2)
        self.assertEqual(legs[0].transfer_group_id, legs[1].transfer_group_id)

        bank_balance = self.projections.compute_account_balance(bank.id)
        cash_balance = self.projections.compute_account_balance(cash.id)
        self.assertEqual(bank_balance, -100000)
        self.assertEqual(cash_balance, 100000)

    def test_transfer_delete_soft_deletes_both_legs(self) -> None:
        bank = self.accounts.create_account("Wallet", "wallet", today=self.today)
        cash = self._cash_account()
        legs, group_id = self.transfers.create_transfer(
            bank.id,
            cash.id,
            5000,
            self.today.isoformat(),
            today=self.today,
        )
        deleted = self.transfers.delete_transfer(group_id)
        self.assertEqual(len(deleted), 2)
        remaining = self.transactions.list_transactions()
        transfer_rows = [row for row in remaining if row.transfer_group_id == group_id]
        self.assertEqual(transfer_rows, [])

    def test_legacy_spending_bridge(self) -> None:
        txn = self.transactions.log_legacy_spending("spent", 42.5, "Lunch", today=self.today)
        self.assertEqual(txn.kind, "expense")
        self.assertEqual(txn.amount_minor, 4250)

        earned, spent = self.projections.compute_period_totals(
            self.today.isoformat(),
            self.today.isoformat(),
        )
        self.assertEqual(earned, 0.0)
        self.assertEqual(spent, 42.5)

    def test_validation_rejects_invalid_amount(self) -> None:
        cash = self._cash_account()
        with self.assertRaises(FinanceValidationError):
            self.transactions.create_transaction(
                cash.id,
                "expense",
                0,
                self.today.isoformat(),
                today=self.today,
            )

    def test_transfer_rejects_same_account(self) -> None:
        cash = self._cash_account()
        with self.assertRaises(FinanceValidationError):
            self.transfers.create_transfer(
                cash.id,
                cash.id,
                1000,
                self.today.isoformat(),
                today=self.today,
            )

    def test_opening_balance_locked_after_first_transaction(self) -> None:
        account = self.accounts.create_account("Locked", "bank", today=self.today)
        self.transactions.create_transaction(
            account.id,
            "income",
            100,
            self.today.isoformat(),
            today=self.today,
        )
        with self.assertRaises(FinanceValidationError):
            self.accounts.update_account(account.id, opening_balance_minor=500)

    def test_transaction_update_and_delete(self) -> None:
        cash = self._cash_account()
        txn = self.transactions.create_transaction(
            cash.id,
            "expense",
            1000,
            self.today.isoformat(),
            today=self.today,
        )
        updated = self.transactions.update_transaction(txn.id, note="Updated")
        self.assertEqual(updated.note, "Updated")
        deleted = self.transactions.delete_transaction(txn.id)
        self.assertEqual(deleted.id, txn.id)


if __name__ == "__main__":
    unittest.main()
