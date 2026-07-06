"""Finance REST integration tests — end-to-end planner/API/mutation flows."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from domains.finance.cashback import CashbackRuleService
from domains.finance.rewards import RewardProgramService
from domains.finance.services.account_service import AccountService
from domains.finance.services.credit_card_service import CreditCardService
from memory import _connection
from memory.schema import init_db
from runtime.events import subscribe
from services.api import create_app


class FinanceIntegrationTestCase(unittest.TestCase):
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
        self.client = TestClient(create_app())
        self.events: list[str] = []

        def handler(channel, event_type, _payload):
            if channel == "events":
                self.events.append(event_type)

        subscribe(handler)
        self.today = date(2026, 7, 7)
        self.accounts = AccountService()
        self.cards = CreditCardService()
        self.programs = RewardProgramService()
        self.cashback_rules = CashbackRuleService()
        self.bank = self.accounts.create_account(
            "HDFC Savings", "bank", opening_balance_on="2026-01-01"
        )
        self.card = self.cards.create_credit_card(
            "HDFC Millennia",
            500_000_00,
            15,
            20,
            opening_balance_on="2026-01-01",
            today=self.today,
        )

    def tearDown(self) -> None:
        for patcher in self._patches:
            patcher.stop()
        self._tmpdir.cleanup()

    def test_category_crud_emits_events(self) -> None:
        create = self.client.post("/finance/categories", json={"name": "Dining"})
        self.assertEqual(create.status_code, 201)
        category_id = create.json()["item"]["id"]
        self.assertIn("finance.category.created", self.events)

        update = self.client.patch(f"/finance/categories/{category_id}", json={"name": "Food"})
        self.assertEqual(update.status_code, 200)
        self.assertIn("finance.category.updated", self.events)

        delete = self.client.delete(f"/finance/categories/{category_id}")
        self.assertEqual(delete.status_code, 200)
        self.assertIn("finance.category.deleted", self.events)

        listing = self.client.get("/finance/categories")
        self.assertEqual(listing.status_code, 200)

    def test_merchant_crud_emits_events(self) -> None:
        create = self.client.post("/finance/merchants", json={"name": "Amazon"})
        self.assertEqual(create.status_code, 201)
        merchant_id = create.json()["item"]["id"]
        self.assertIn("finance.merchant.created", self.events)

        update = self.client.patch(f"/finance/merchants/{merchant_id}", json={"name": "Amazon IN"})
        self.assertEqual(update.status_code, 200)
        self.assertIn("finance.merchant.updated", self.events)

        delete = self.client.delete(f"/finance/merchants/{merchant_id}")
        self.assertEqual(delete.status_code, 200)
        self.assertIn("finance.merchant.deleted", self.events)

    def test_transfer_create_and_delete_emit_events(self) -> None:
        wallet = self.accounts.create_account("Wallet", "wallet", opening_balance_on="2026-01-01")
        create = self.client.post(
            "/finance/transfers",
            json={
                "from_account_id": self.bank.id,
                "to_account_id": wallet.id,
                "amount": 1000.0,
                "occurred_on": "2026-06-01",
            },
        )
        self.assertEqual(create.status_code, 201)
        group_id = create.json()["item"]["transfer_group_id"]
        self.assertIn("finance.transfer.created", self.events)

        delete = self.client.delete(f"/finance/transfers/{group_id}")
        self.assertEqual(delete.status_code, 200)
        self.assertIn("finance.transaction.deleted", self.events)

    def test_statement_materialization_emits_created_event(self) -> None:
        self.events.clear()
        response = self.client.get("/finance/statements", params={"account_id": self.card.id})
        self.assertEqual(response.status_code, 200)
        self.assertIn("finance.statement.created", self.events)
        self.assertGreaterEqual(len(response.json()["statements"]), 1)

    def test_statement_update_and_pay_emit_events(self) -> None:
        listing = self.client.get("/finance/statements", params={"account_id": self.card.id})
        statement_id = listing.json()["statements"][0]["id"]

        patch = self.client.patch(
            f"/finance/statements/{statement_id}",
            json={"total_due": 5000.0, "min_due": 500.0},
        )
        self.assertEqual(patch.status_code, 200)
        self.assertIn("finance.statement.updated", self.events)

        pay = self.client.post(
            f"/finance/statements/{statement_id}/pay",
            json={
                "from_account_id": self.bank.id,
                "payment_mode": "partial",
                "amount": 500.0,
            },
        )
        self.assertEqual(pay.status_code, 201)
        self.assertIn("finance.statement.paid", self.events)

    def test_card_payment_emits_event(self) -> None:
        response = self.client.post(
            "/finance/payments/card",
            json={
                "from_account_id": self.bank.id,
                "card_account_id": self.card.id,
                "amount": 250.0,
                "occurred_on": "2026-06-10",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("finance.card_payment.created", self.events)
        group_id = response.json()["item"]["transfer_group_id"]

        delete = self.client.delete(f"/finance/payments/card/{group_id}")
        self.assertEqual(delete.status_code, 200)

    def test_transaction_create_earns_cashback(self) -> None:
        program = self.programs.create_program(self.card.id, "Cashback", "cashback_minor")
        self.cashback_rules.create_rule(program.id, "Flat 1%", flat_rate_bps=100)

        response = self.client.post(
            "/finance/transactions",
            json={
                "account_id": self.card.id,
                "kind": "expense",
                "amount": 10000.0,
                "occurred_on": "2026-06-15",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("finance.transaction.created", self.events)
        self.assertIn("finance.cashback.earned", self.events)

        ledger = self.client.get(f"/finance/rewards/programs/{program.id}/ledger")
        self.assertEqual(ledger.status_code, 200)
        self.assertGreaterEqual(ledger.json()["balance"]["balance"], 10000)


if __name__ == "__main__":
    unittest.main()
