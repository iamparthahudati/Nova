"""Cashback product read query tests — real SQLite, no mocks."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from domains.finance.cashback import CashbackRuleService
from domains.finance.cashback.errors import CashbackRuleNotFoundError
from domains.finance.rewards import RewardEventService, RewardProgramService
from domains.finance.services.credit_card_service import CreditCardService
from memory import _connection
from memory.schema import init_db
from services.api import create_app
from services.planner import finance_cashback_queries as cashback_q


class CashbackQueriesTestCase(unittest.TestCase):
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
        self.programs = RewardProgramService()
        self.rules = CashbackRuleService()
        self.events = RewardEventService()
        self.card = self.cards.create_credit_card(
            "HDFC Millennia",
            500_000_00,
            15,
            20,
            opening_balance_on="2026-01-01",
            today=self.today,
        )
        self.program = self.programs.create_program(self.card.id, "Cashback", "cashback_minor")
        self.rule = self.rules.create_rule(self.program.id, "Flat 1%", flat_rate_bps=100)

    def tearDown(self) -> None:
        for patcher in self._patches:
            patcher.stop()
        self._tmpdir.cleanup()

    def test_cashback_summary_includes_overview_and_enriched_rules(self) -> None:
        self.events.create_earned_event(
            self.program.id,
            5000,
            "2026-07-02",
            note=f"cashback rule {self.rule.id}",
            today=self.today,
        )

        summary = cashback_q.get_cashback_summary(self.today)
        self.assertEqual(summary["active_rules_count"], 1)
        self.assertEqual(summary["monthly_earned_minor"], 5000)
        self.assertEqual(summary["earned_lifetime_minor"], 5000)
        self.assertEqual(summary["rules"][0]["status"], "active")
        self.assertEqual(summary["rules"][0]["card_name"], "HDFC Millennia")

    def test_cashback_rule_detail_and_activity(self) -> None:
        self.events.create_earned_event(
            self.program.id,
            2500,
            "2026-07-03",
            note=f"cashback rule {self.rule.id}",
            today=self.today,
        )

        detail = cashback_q.get_cashback_rule_detail(self.rule.id, self.today)
        self.assertEqual(detail["rule"]["id"], self.rule.id)
        self.assertEqual(detail["earned_month"], 2500)
        self.assertEqual(len(detail["recent_events"]), 1)

        activity = cashback_q.get_cashback_activity(limit=10)
        self.assertEqual(len(activity["events"]), 1)
        self.assertEqual(activity["events"][0]["rule_id"], self.rule.id)

    def test_missing_rule_raises(self) -> None:
        with self.assertRaises(CashbackRuleNotFoundError):
            cashback_q.get_cashback_rule_detail(9999, self.today)


class CashbackApiTestCase(unittest.TestCase):
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
        self.today = date(2026, 7, 7)
        self.cards = CreditCardService()
        self.programs = RewardProgramService()
        self.rules = CashbackRuleService()
        self.card = self.cards.create_credit_card(
            "HDFC Millennia",
            500_000_00,
            15,
            20,
            opening_balance_on="2026-01-01",
            today=self.today,
        )
        self.program = self.programs.create_program(self.card.id, "Cashback", "cashback_minor")
        self.rule = self.rules.create_rule(self.program.id, "Flat 1%", flat_rate_bps=100)

    def tearDown(self) -> None:
        for patcher in self._patches:
            patcher.stop()
        self._tmpdir.cleanup()

    def test_cashback_rest_endpoints(self) -> None:
        summary = self.client.get("/finance/cashback")
        self.assertEqual(summary.status_code, 200)
        body = summary.json()
        self.assertEqual(body["active_rules_count"], 1)
        self.assertEqual(len(body["rules"]), 1)

        detail = self.client.get(f"/finance/cashback/rules/{self.rule.id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["rule"]["name"], "Flat 1%")

        missing = self.client.get("/finance/cashback/rules/9999")
        self.assertEqual(missing.status_code, 404)

        activity = self.client.get("/finance/cashback/activity")
        self.assertEqual(activity.status_code, 200)
        self.assertIn("events", activity.json())
