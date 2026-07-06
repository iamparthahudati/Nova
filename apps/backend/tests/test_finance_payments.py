"""Card payment and statement payment tests — real SQLite, no mocks."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from domains.finance.errors import FinanceValidationError, PaymentConfirmationRequiredError
from domains.finance.mutations import build_card_payment_created, build_statement_paid
from domains.finance.payments.service import PaymentService
from domains.finance.payments.status import StatementStatus
from domains.finance.payments.validation import PaymentMode
from domains.finance.services.account_service import AccountService
from domains.finance.services.credit_card_service import CreditCardService
from domains.finance.services.projection_service import ProjectionService
from domains.finance.services.statement_service import StatementService
from domains.finance.services.transaction_service import TransactionService
from memory import _connection
from memory.schema import init_db


class CardPaymentTestCase(unittest.TestCase):
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
        self.accounts = AccountService()
        self.cards = CreditCardService()
        self.statements = StatementService()
        self.transactions = TransactionService()
        self.payments = PaymentService()
        self.projections = ProjectionService()

    def tearDown(self) -> None:
        for patcher in self._patches:
            patcher.stop()
        self._tmpdir.cleanup()

    def _bank_account(self):
        return self.accounts.create_account("HDFC Savings", "bank", today=self.today)

    def _card(self, statement_day: int = 15, due_day_offset: int = 20):
        return self.cards.create_credit_card(
            name="HDFC Millennia",
            credit_limit_minor=500_000_00,
            statement_day=statement_day,
            due_day_offset=due_day_offset,
            opening_balance_on="2026-01-01",
            today=self.today,
        )

    def _statement_with_totals(
        self,
        card_id: int,
        total_due_minor: int = 10_000_00,
        min_due_minor: int = 1_000_00,
    ):
        statement = self.statements.generate_statement(card_id, self.today)
        return self.statements.update_statement(
            statement.id,
            total_due_minor=total_due_minor,
            min_due_minor=min_due_minor,
        )

    def test_card_payment_pair_and_balance(self) -> None:
        bank = self._bank_account()
        card = self._card()
        self.transactions.create_transaction(
            card.id,
            "expense",
            20_000_00,
            self.today.isoformat(),
            today=self.today,
        )
        legs, group_id = self.payments.create_card_payment(
            bank.id,
            card.id,
            5_000_00,
            self.today.isoformat(),
            today=self.today,
        )
        event = build_card_payment_created(legs, group_id)
        self.assertEqual(event.event_type, "finance.card_payment.created")
        self.assertEqual(len(legs), 2)
        self.assertEqual(legs[0].kind, "card_payment")
        self.assertEqual(legs[1].kind, "card_payment")

        bank_balance = self.projections.compute_account_balance(bank.id)
        card_balance = self.projections.compute_account_balance(card.id)
        self.assertEqual(bank_balance, -5_000_00)
        self.assertEqual(card_balance, -15_000_00)

    def test_pay_statement_full(self) -> None:
        bank = self._bank_account()
        card = self._card()
        statement = self._statement_with_totals(card.id)

        legs, group_id = self.payments.pay_statement(
            statement.id,
            bank.id,
            payment_mode=PaymentMode.FULL.value,
            today=self.today,
        )
        event = build_statement_paid(legs, group_id, statement.id)
        self.assertEqual(event.event_type, "finance.statement.paid")
        self.assertEqual(event.metadata["statement_id"], statement.id)

        credit_leg = next(leg for leg in legs if leg.direction == "credit")
        self.assertEqual(credit_leg.statement_id, statement.id)
        self.assertEqual(credit_leg.amount_minor, 10_000_00)

        summary = self.projections.compute_statement_summary(statement.id, self.today)
        self.assertEqual(summary.status, StatementStatus.PAID)
        self.assertEqual(summary.paid_minor, 10_000_00)
        self.assertEqual(summary.remaining_due_minor, 0)

    def test_pay_statement_minimum(self) -> None:
        bank = self._bank_account()
        card = self._card()
        statement = self._statement_with_totals(
            card.id, total_due_minor=10_000_00, min_due_minor=2_000_00
        )

        legs, _group_id = self.payments.pay_statement(
            statement.id,
            bank.id,
            payment_mode=PaymentMode.MINIMUM.value,
            today=self.today,
        )
        credit_leg = next(leg for leg in legs if leg.direction == "credit")
        self.assertEqual(credit_leg.amount_minor, 2_000_00)

        summary = self.projections.compute_statement_summary(statement.id, self.today)
        self.assertEqual(summary.status, StatementStatus.PARTIAL)
        self.assertEqual(summary.paid_minor, 2_000_00)

    def test_pay_statement_partial(self) -> None:
        bank = self._bank_account()
        card = self._card()
        statement = self._statement_with_totals(card.id)

        self.payments.pay_statement(
            statement.id,
            bank.id,
            payment_mode=PaymentMode.PARTIAL.value,
            amount_minor=3_500_00,
            today=self.today,
        )
        summary = self.projections.compute_statement_summary(statement.id, self.today)
        self.assertEqual(summary.status, StatementStatus.PARTIAL)
        self.assertEqual(summary.paid_minor, 3_500_00)
        self.assertEqual(summary.remaining_due_minor, 6_500_00)

    def test_statement_status_open_due_overdue(self) -> None:
        card = self._card()
        statement = self.statements.generate_statement(card.id, self.today)

        summary_open = self.projections.compute_statement_summary(statement.id, self.today)
        self.assertEqual(summary_open.status, StatementStatus.OPEN)

        updated = self.statements.update_statement(
            statement.id,
            total_due_minor=5_000_00,
            min_due_minor=500_00,
        )
        before_due = date(2026, 7, 1)
        summary_due = self.projections.compute_statement_summary(updated.id, before_due)
        self.assertEqual(summary_due.status, StatementStatus.DUE)

        past_due = date.fromisoformat(updated.due_date) + timedelta(days=1)
        summary_overdue = self.projections.compute_statement_summary(updated.id, past_due)
        self.assertEqual(summary_overdue.status, StatementStatus.OVERDUE)

    def test_overpayment_requires_confirmation(self) -> None:
        bank = self._bank_account()
        card = self._card()
        statement = self._statement_with_totals(
            card.id, total_due_minor=5_000_00, min_due_minor=500_00
        )

        with self.assertRaises(PaymentConfirmationRequiredError):
            self.payments.pay_statement(
                statement.id,
                bank.id,
                payment_mode=PaymentMode.PARTIAL.value,
                amount_minor=6_000_00,
                today=self.today,
            )

        legs, _group_id = self.payments.pay_statement(
            statement.id,
            bank.id,
            payment_mode=PaymentMode.PARTIAL.value,
            amount_minor=6_000_00,
            confirm_overpayment=True,
            today=self.today,
        )
        credit_leg = next(leg for leg in legs if leg.direction == "credit")
        self.assertEqual(credit_leg.amount_minor, 6_000_00)
        summary = self.projections.compute_statement_summary(statement.id, self.today)
        self.assertEqual(summary.status, StatementStatus.PAID)

    def test_spend_excludes_payment_legs(self) -> None:
        bank = self._bank_account()
        card = self._card()
        statement = self._statement_with_totals(
            card.id, total_due_minor=10_000_00, min_due_minor=1_000_00
        )
        self.transactions.create_transaction(
            card.id,
            "expense",
            10_000_00,
            "2026-06-10",
            today=self.today,
        )
        from memory.finance import transactions as txn_store

        txn_store.update_transaction(
            self.transactions.list_transactions(card.id)[0].id,
            {"statement_id": statement.id},
        )
        self.payments.pay_statement(
            statement.id,
            bank.id,
            payment_mode=PaymentMode.PARTIAL.value,
            amount_minor=2_000_00,
            today=self.today,
        )
        spend = self.projections.compute_statement_spend(statement.id)
        self.assertEqual(spend, 10_000_00)

    def test_delete_card_payment_soft_deletes_both_legs(self) -> None:
        bank = self._bank_account()
        card = self._card()
        _legs, group_id = self.payments.create_card_payment(
            bank.id,
            card.id,
            1_000_00,
            self.today.isoformat(),
            today=self.today,
        )
        deleted = self.payments.delete_card_payment(group_id)
        self.assertEqual(len(deleted), 2)
        remaining = self.transactions.list_transactions()
        payment_rows = [row for row in remaining if row.transfer_group_id == group_id]
        self.assertEqual(payment_rows, [])

    def test_payment_rejects_non_asset_source(self) -> None:
        card_a = self._card()
        card_b = self.cards.create_credit_card(
            name="ICICI",
            credit_limit_minor=100_000_00,
            statement_day=15,
            due_day_offset=20,
            today=self.today,
        )
        with self.assertRaises(FinanceValidationError):
            self.payments.create_card_payment(
                card_b.id,
                card_a.id,
                1_000_00,
                self.today.isoformat(),
                today=self.today,
            )

    def test_full_payment_requires_total_due(self) -> None:
        bank = self._bank_account()
        card = self._card()
        statement = self.statements.generate_statement(card.id, self.today)
        with self.assertRaises(FinanceValidationError):
            self.payments.pay_statement(
                statement.id,
                bank.id,
                payment_mode=PaymentMode.FULL.value,
                today=self.today,
            )

    def test_list_statement_summaries(self) -> None:
        card = self._card()
        statement = self._statement_with_totals(card.id)
        before_due = date(2026, 7, 1)
        summaries = self.projections.list_statement_summaries(card.id, before_due)
        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0].statement_id, statement.id)
        self.assertEqual(summaries[0].status, StatementStatus.DUE)


if __name__ == "__main__":
    unittest.main()
