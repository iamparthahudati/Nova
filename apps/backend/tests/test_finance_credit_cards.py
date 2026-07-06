"""Credit card and statement foundation tests — real SQLite, no mocks."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from domains.finance.cycle import compute_billing_cycle
from domains.finance.errors import FinanceValidationError, StatementInvariantError
from domains.finance.mutations import (
    build_credit_card_created,
    build_statement_created,
    build_statement_updated,
)
from domains.finance.services.credit_card_service import CreditCardService
from domains.finance.services.projection_service import ProjectionService
from domains.finance.services.statement_service import StatementService
from domains.finance.services.transaction_service import TransactionService
from memory import _connection
from memory.schema import init_db


class CreditCardFoundationTestCase(unittest.TestCase):
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
        self.today = date(2026, 7, 7)
        self.cards = CreditCardService()
        self.statements = StatementService()
        self.transactions = TransactionService()
        self.projections = ProjectionService()

    def tearDown(self) -> None:
        for patcher in self._patches:
            patcher.stop()
        self._tmpdir.cleanup()

    def _create_card(
        self, statement_day: int = 15, due_day_offset: int = 20, opening_on: str = "2026-01-01"
    ):
        return self.cards.create_credit_card(
            name="HDFC Millennia",
            credit_limit_minor=500_000_00,
            statement_day=statement_day,
            due_day_offset=due_day_offset,
            opening_balance_on=opening_on,
            network="Visa",
            last4="1234",
            today=self.today,
        )

    def test_credit_card_create_and_profile(self) -> None:
        card = self._create_card()
        event = build_credit_card_created(card)
        self.assertEqual(event.event_type, "finance.credit_card.created")
        self.assertEqual(card.account.type, "credit_card")
        self.assertEqual(card.account.classification, "liability")
        self.assertEqual(card.profile.credit_limit_minor, 500_000_00)
        self.assertEqual(card.profile.statement_day, 15)
        self.assertEqual(card.profile.due_day_offset, 20)

    def test_credit_card_crud(self) -> None:
        card = self._create_card()
        updated = self.cards.update_credit_card(
            card.id,
            name="HDFC Card",
            credit_limit_minor=600_000_00,
            autopay=True,
        )
        self.assertEqual(updated.name, "HDFC Card")
        self.assertEqual(updated.profile.credit_limit_minor, 600_000_00)
        self.assertTrue(updated.profile.autopay)

        archived = self.cards.archive_credit_card(card.id)
        self.assertIsNotNone(archived.account.archived_at)

    def test_billing_cycle_computation(self) -> None:
        billing = compute_billing_cycle(15, 20, self.today)
        self.assertEqual(billing.period_end, "2026-06-15")
        self.assertEqual(billing.period_start, "2026-05-16")
        self.assertEqual(billing.due_date, "2026-07-05")

    def test_statement_generation_idempotent(self) -> None:
        card = self._create_card()
        first = self.statements.generate_statement(card.id, self.today)
        second = self.statements.generate_statement(card.id, self.today)
        self.assertEqual(first.id, second.id)
        event = build_statement_created(first)
        self.assertEqual(event.event_type, "finance.statement.created")
        self.assertEqual(first.period_end, "2026-06-15")

    def test_current_and_previous_statements(self) -> None:
        card = self._create_card()
        current, previous, _created = self.statements.ensure_current_and_previous(
            card.id, self.today
        )
        self.assertEqual(current.period_end, "2026-06-15")
        self.assertIsNotNone(previous)
        assert previous is not None
        self.assertEqual(previous.period_end, "2026-05-15")
        self.assertEqual(
            self.statements.get_previous_statement(card.id, self.today).id, previous.id
        )

    def test_utilization_and_available_limit_derived(self) -> None:
        card = self._create_card()
        self.transactions.create_transaction(
            card.id,
            "expense",
            50_000_00,
            self.today.isoformat(),
            today=self.today,
        )
        utilization = self.projections.compute_utilization(card.id)
        available = self.projections.compute_available_limit(card.id)
        self.assertEqual(utilization.outstanding_minor, 50_000_00)
        self.assertAlmostEqual(utilization.ratio, 0.1)
        self.assertEqual(available.minor, 450_000_00)
        balance = self.projections.compute_account_balance(card.id)
        self.assertEqual(balance, -50_000_00)

    def test_statement_totals_from_transactions(self) -> None:
        card = self._create_card(statement_day=31)
        current = self.statements.generate_statement(card.id, self.today)
        self.transactions.create_transaction(
            card.id,
            "expense",
            12_500_00,
            "2026-06-10",
            today=self.today,
        )
        self.transactions.create_transaction(
            card.id,
            "income",
            2_500_00,
            "2026-06-12",
            today=self.today,
        )
        spend = self.statements.compute_period_spend_minor(
            card.id,
            current.period_start,
            current.period_end,
        )
        self.assertEqual(spend, 10_000_00)

        updated = self.statements.update_statement(
            current.id,
            total_due_minor=10_500_00,
            min_due_minor=1_000_00,
        )
        event = build_statement_updated(updated)
        self.assertEqual(event.event_type, "finance.statement.updated")
        self.assertEqual(updated.total_due_minor, 10_500_00)

    def test_validation_rejects_invalid_profile(self) -> None:
        with self.assertRaises(FinanceValidationError):
            self.cards.create_credit_card(
                "Bad Card",
                credit_limit_minor=0,
                statement_day=15,
                due_day_offset=20,
                today=self.today,
            )
        with self.assertRaises(FinanceValidationError):
            self.cards.create_credit_card(
                "Bad Card",
                credit_limit_minor=100_000_00,
                statement_day=32,
                due_day_offset=20,
                today=self.today,
            )

    def test_statement_delete_blocked_with_linked_transactions(self) -> None:
        card = self._create_card()
        statement = self.statements.generate_statement(card.id, self.today)
        txn = self.transactions.create_transaction(
            card.id,
            "expense",
            1000,
            self.today.isoformat(),
            today=self.today,
        )
        from memory.finance import transactions as txn_store

        txn_store.update_transaction(txn.id, {"statement_id": statement.id})
        with self.assertRaises(StatementInvariantError):
            self.statements.delete_statement(statement.id)

    def test_list_card_utilization_projection(self) -> None:
        card = self._create_card()
        self.transactions.create_transaction(
            card.id,
            "expense",
            25_000_00,
            self.today.isoformat(),
            today=self.today,
        )
        rows = self.projections.list_card_utilization()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["account_id"], card.id)
        self.assertEqual(rows[0]["outstanding_minor"], 25_000_00)
        self.assertAlmostEqual(rows[0]["utilization_ratio"], 0.05)


if __name__ == "__main__":
    unittest.main()
