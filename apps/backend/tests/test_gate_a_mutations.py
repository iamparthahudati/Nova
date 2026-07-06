"""Gate A tests — mutation pipeline, task REST writes, chat/REST parity."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import memory
from memory import _connection
from memory.schema import init_db
from memory_producers import memory_from_mutation
from runtime.domain_events import publish_mutation_events
from runtime.events import subscribe
from runtime.mutation_builders import build_task_completed, build_task_created
from runtime.mutation_chat import tool_calls_to_mutations, tool_mutation_succeeded
from runtime.mutation_event import MutationEvent
from runtime.side_effects import finalize_mutations, schedule_entity_extraction
from services.api import create_app


class MutationPipelineTestCase(unittest.TestCase):
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

    def test_memory_from_mutation_complete_task(self) -> None:
        event = MutationEvent(
            event_type="task.updated",
            entity_type="task",
            operation="complete",
            entity={"id": 1, "text": "Ship API", "status": "done"},
        )
        record = memory_from_mutation(event)
        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual(record["text"], "Completed task: Ship API")
        self.assertEqual(record["source_type"], "task")

    def test_publish_mutation_events_uses_event_type(self) -> None:
        received: list[tuple] = []

        def handler(channel, event_type, payload):
            received.append((channel, event_type, payload))

        subscribe(handler)
        publish_mutation_events([
            MutationEvent(
                event_type="task.created",
                entity_type="task",
                operation="create",
                entity={"id": 1, "text": "A"},
                metadata={"entity_id": 1},
            ),
        ])
        self.assertEqual(received[0][1], "task.created")
        self.assertEqual(received[0][2]["entity_type"], "task")
        self.assertEqual(received[0][2]["operation"], "create")
        self.assertEqual(received[0][2]["entity_id"], 1)

    def test_chat_and_rest_builders_produce_equivalent_mutations(self) -> None:
        memory.add_task("Parity task")
        row = memory.find_task_by_text("Parity task", status="open")
        self.assertIsNotNone(row)
        assert row is not None
        completed = memory.complete_task_by_id(row["id"])
        assert completed is not None

        rest_event = build_task_completed(completed)
        chat_events = tool_calls_to_mutations([
            {
                "name": "complete_task",
                "args": {"text": "Parity task"},
                "result": "Task marked done.",
            },
        ])
        self.assertEqual(len(chat_events), 1)
        chat_event = chat_events[0]

        self.assertEqual(rest_event.event_type, chat_event.event_type)
        self.assertEqual(rest_event.entity_type, chat_event.entity_type)
        self.assertEqual(rest_event.operation, chat_event.operation)
        self.assertEqual(rest_event.entity["text"], chat_event.entity["text"])
        self.assertEqual(rest_event.entity["status"], chat_event.entity["status"])

        from datetime import datetime, timezone

        fixed_now = datetime(2026, 7, 6, 12, 0, 0, tzinfo=timezone.utc)
        rest_memory = memory_from_mutation(rest_event, fixed_now)
        chat_memory = memory_from_mutation(chat_event, fixed_now)
        self.assertEqual(rest_memory, chat_memory)

    def test_finalize_mutations_parity_domain_events(self) -> None:
        memory.add_task("Event parity")
        row = memory.find_task_by_text("Event parity", status="open")
        assert row is not None

        rest_event = build_task_created(row)
        chat_events = tool_calls_to_mutations([
            {"name": "add_task", "args": {"text": "Other"}, "result": "Task logged."},
        ])

        received: list[str] = []

        def handler(channel, event_type, _payload):
            if channel == "events":
                received.append(event_type)

        subscribe(handler)

        finalize_mutations([rest_event])
        rest_events = list(received)

        received.clear()
        finalize_mutations(chat_events)
        chat_event_types = list(received)

        self.assertEqual(rest_events, ["task.created"])
        self.assertEqual(chat_event_types, ["task.created"])

    def test_tool_mutation_succeeded_chat_only(self) -> None:
        self.assertTrue(tool_mutation_succeeded(
            "complete_task", {"text": "x"}, "Task marked done.",
        ))
        self.assertFalse(tool_mutation_succeeded(
            "complete_task", {"text": "x"}, "No matching task found.",
        ))


class GateATaskApiTests(unittest.TestCase):
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

    def test_create_task(self) -> None:
        received: list[str] = []

        def handler(channel, event_type, _payload):
            if channel == "events":
                received.append(event_type)

        subscribe(handler)

        resp = self.client.post("/tasks", json={"text": "Write docs", "due": "2026-07-10"})
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertEqual(body["item"]["text"], "Write docs")
        self.assertEqual(body["item"]["status"], "open")
        self.assertEqual(body["item"]["due"], "2026-07-10")
        self.assertIn("Task logged", body["meta"]["message"])
        self.assertIn("task.created", received)

    def test_complete_task(self) -> None:
        memory.add_task("Finish Gate A")
        task_id = memory.find_task_by_text("Finish Gate A", status="open")["id"]

        received: list[str] = []

        def handler(channel, event_type, _payload):
            if channel == "events":
                received.append(event_type)

        subscribe(handler)

        resp = self.client.post(f"/tasks/{task_id}/complete")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["item"]["status"], "done")
        self.assertEqual(body["meta"]["message"], "Task marked done.")
        self.assertIn("task.updated", received)

    def test_complete_task_not_found(self) -> None:
        resp = self.client.post("/tasks/99999/complete")
        self.assertEqual(resp.status_code, 404)

    def test_complete_task_already_done(self) -> None:
        memory.add_task("Already done")
        task_id = memory.find_task_by_text("Already done", status="open")["id"]
        memory.complete_task_by_id(task_id)
        resp = self.client.post(f"/tasks/{task_id}/complete")
        self.assertEqual(resp.status_code, 409)

    def test_create_task_validation(self) -> None:
        resp = self.client.post("/tasks", json={"text": ""})
        self.assertEqual(resp.status_code, 422)

    def test_websocket_delivers_mutation_event(self) -> None:
        with TestClient(create_app()) as client:
            with client.websocket_connect("/ws/events") as ws:
                publish_mutation_events([
                    MutationEvent(
                        event_type="task.updated",
                        entity_type="task",
                        operation="complete",
                        entity={"id": 1, "text": "x", "status": "done"},
                        metadata={"entity_id": 1},
                    ),
                ])
                msg = json.loads(ws.receive_text())
                self.assertEqual(msg["event"], "task.updated")
                self.assertEqual(msg["data"]["entity_type"], "task")
                self.assertEqual(msg["data"]["operation"], "complete")
                ws.send_text("ping")


if __name__ == "__main__":
    unittest.main()
