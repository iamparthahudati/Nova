"""Gate C tests — reminder and spending REST writes, chat/REST parity."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import memory
from memory import _connection
from memory.schema import init_db
from runtime.domain_events import publish_mutation_events
from runtime.events import subscribe
from runtime.mutation_builders import build_reminder_created, build_spending_logged
from runtime.mutation_chat import tool_calls_to_mutations
from runtime.mutation_event import MutationEvent
from runtime.side_effects import finalize_mutations
from services.api import create_app


class GateCMutationParityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmpdir.name) / "test.db"
        self.lance_path = Path(self._tmpdir.name) / "lancedb"
        self._patches = [
            patch.object(_connection, "DB_PATH", self.db_path),
            patch.object(_connection, "LANCEDB_PATH", self.lance_path),
            patch("runtime.side_effects.schedule_entity_extraction"),
            patch("runtime.side_effects.remember"),
        ]
        for p in self._patches:
            p.start()
        _connection.ensure_storage_paths()
        init_db()

    def tearDown(self) -> None:
        for p in self._patches:
            p.stop()
        self._tmpdir.cleanup()

    def test_chat_and_rest_reminder_mutations_equivalent(self) -> None:
        memory.add_reminder("Pay rent", datetime(2026, 7, 15), "09:00")
        row = memory.get_latest_reminder("Pay rent")
        assert row is not None

        rest_event = build_reminder_created(row)
        chat_events = tool_calls_to_mutations([
            {
                "name": "add_reminder",
                "args": {
                    "text": "Pay rent",
                    "remind_date": "2026-07-15",
                    "remind_time": "09:00",
                },
                "result": "Reminder saved: Pay rent on July 15 at 9:00 AM.",
            },
        ])
        self.assertEqual(len(chat_events), 1)
        chat_event = chat_events[0]

        self.assertEqual(rest_event.event_type, chat_event.event_type)
        self.assertEqual(rest_event.entity_type, chat_event.entity_type)
        self.assertEqual(rest_event.operation, chat_event.operation)
        self.assertEqual(rest_event.entity["text"], chat_event.entity["text"])

    def test_chat_and_rest_spending_mutations_equivalent(self) -> None:
        memory.add_money("spent", 42.5, "Lunch")
        row = memory.get_latest_money("spent", 42.5)
        assert row is not None

        rest_event = build_spending_logged(row)
        chat_events = tool_calls_to_mutations([
            {
                "name": "add_money",
                "args": {"type": "spent", "amount": 42.5, "note": "Lunch"},
                "result": "Logged expense.",
            },
        ])
        self.assertEqual(len(chat_events), 1)
        chat_event = chat_events[0]

        self.assertEqual(rest_event.event_type, chat_event.event_type)
        self.assertEqual(rest_event.entity_type, chat_event.entity_type)
        self.assertEqual(rest_event.operation, chat_event.operation)
        self.assertEqual(rest_event.entity["amount"], chat_event.entity["amount"])

    def test_finalize_mutations_publishes_gate_c_events(self) -> None:
        received: list[str] = []

        def handler(channel, event_type, _payload):
            if channel == "events":
                received.append(event_type)

        subscribe(handler)

        finalize_mutations([
            MutationEvent(
                event_type="reminder.created",
                entity_type="reminder",
                operation="create",
                entity={"id": 1, "text": "Call mom"},
                metadata={"entity_id": 1},
            ),
            MutationEvent(
                event_type="spending.logged",
                entity_type="money",
                operation="log",
                entity={"id": 2, "type": "earned", "amount": 100.0},
                metadata={"entity_id": 2},
            ),
        ])
        self.assertEqual(received, ["reminder.created", "spending.logged"])


class GateCApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmpdir.name) / "test.db"
        self.lance_path = Path(self._tmpdir.name) / "lancedb"
        self._patches = [
            patch.object(_connection, "DB_PATH", self.db_path),
            patch.object(_connection, "LANCEDB_PATH", self.lance_path),
            patch(
                "services.calendar.get_events",
                return_value=[{"title": "Standup", "time": "9:00 AM"}],
            ),
            patch("runtime.side_effects.schedule_entity_extraction"),
            patch("runtime.side_effects.remember"),
        ]
        for p in self._patches:
            p.start()
        _connection.ensure_storage_paths()
        init_db()
        self.client = TestClient(create_app())

    def tearDown(self) -> None:
        for p in self._patches:
            p.stop()
        self._tmpdir.cleanup()

    def test_create_reminder(self) -> None:
        received: list[str] = []

        def handler(channel, event_type, _payload):
            if channel == "events":
                received.append(event_type)

        subscribe(handler)

        resp = self.client.post(
            "/reminders",
            json={"text": "Team standup", "remind_date": "2026-07-10", "remind_time": "09:30"},
        )
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertEqual(body["item"]["text"], "Team standup")
        self.assertEqual(body["item"]["remind_date"], "2026-07-10")
        self.assertEqual(body["item"]["remind_time"], "09:30")
        self.assertIn("Reminder saved", body["meta"]["message"])
        self.assertIn("reminder.created", received)

    def test_create_reminder_invalid_date(self) -> None:
        resp = self.client.post(
            "/reminders",
            json={"text": "Bad date", "remind_date": "not-a-date"},
        )
        self.assertEqual(resp.status_code, 400)

    def test_log_spending(self) -> None:
        received: list[str] = []

        def handler(channel, event_type, _payload):
            if channel == "events":
                received.append(event_type)

        subscribe(handler)

        resp = self.client.post(
            "/spending",
            json={"type": "spent", "amount": 250.0, "note": "Office supplies"},
        )
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertEqual(body["item"]["type"], "spent")
        self.assertEqual(body["item"]["amount"], 250.0)
        self.assertEqual(body["item"]["note"], "Office supplies")
        self.assertEqual(body["meta"]["message"], "Logged expense.")
        self.assertIn("spending.logged", received)

    def test_log_spending_validation(self) -> None:
        resp = self.client.post("/spending", json={"type": "spent", "amount": 0})
        self.assertEqual(resp.status_code, 422)


if __name__ == "__main__":
    unittest.main()
