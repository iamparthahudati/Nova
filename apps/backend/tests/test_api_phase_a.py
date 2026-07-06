"""Phase A API foundation tests — memory verbs, HTTP routes, domain events.

Run:  cd apps/backend && python -m unittest discover tests -v
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import memory
from memory import _connection
from memory.schema import init_db
from runtime.domain_events import publish_mutation_events
from runtime.events import publish, subscribe
from runtime.mutation_chat import tool_calls_to_mutations, tool_mutation_succeeded
from runtime.mutation_event import MutationEvent
from services.api import create_app


class PhaseAMemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmpdir.name) / "test.db"
        self.lance_path = Path(self._tmpdir.name) / "lancedb"
        self._patches = [
            patch.object(_connection, "DB_PATH", self.db_path),
            patch.object(_connection, "LANCEDB_PATH", self.lance_path),
        ]
        for p in self._patches:
            p.start()
        _connection.ensure_storage_paths()
        init_db()

    def tearDown(self) -> None:
        for p in self._patches:
            p.stop()
        self._tmpdir.cleanup()

    def test_ping_database(self) -> None:
        memory.ping_database()

    def test_semantic_index_exists_false_when_missing(self) -> None:
        self.assertFalse(memory.semantic_index_exists())

    def test_list_and_count_memories(self) -> None:
        from memory.semantic import ledger

        ledger.insert(
            memory_id="mem-a",
            text="Alpha note",
            source_type="journal",
            source_id=None,
            metadata={},
            content_hash="hash-a",
            importance=0.5,
            tier="short_term",
            embedding_model="test",
            embedding_version="0",
            embedding_dimension=384,
        )
        ledger.insert(
            memory_id="mem-b",
            text="Beta note",
            source_type="task",
            source_id=None,
            metadata={},
            content_hash="hash-b",
            importance=0.5,
            tier="short_term",
            embedding_model="test",
            embedding_version="0",
            embedding_dimension=384,
        )

        rows = memory.list_memories(limit=10, sort="created_at", order="asc")
        self.assertEqual(len(rows), 2)
        self.assertEqual(memory.count_active_memories(), 2)

        filtered = memory.list_memories(search="Alpha")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["text"], "Alpha note")

    def test_get_all_tasks_open_first(self) -> None:
        memory.add_task("Done task")
        memory.complete_task("Done task")
        memory.add_task("Open task")

        rows = memory.get_all_tasks()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["status"], "open")
        self.assertEqual(rows[1]["status"], "done")

    def test_graph_snapshot_and_stats(self) -> None:
        e1 = memory.create_entity("project", "Nova")
        e2 = memory.create_entity("person", "Alex")
        memory.link_entities(e1, e2, "OWNED_BY")

        snapshot = memory.list_graph_snapshot()
        self.assertEqual(len(snapshot["entities"]), 2)
        self.assertEqual(len(snapshot["edges"]), 1)

        stats = memory.graph_stats()
        self.assertEqual(stats["entity_count"], 2)
        self.assertEqual(stats["edge_count"], 1)
        self.assertIn("project", stats["entities_by_type"])


class PhaseAApiTests(unittest.TestCase):
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
        ]
        for p in self._patches:
            p.start()
        _connection.ensure_storage_paths()
        init_db()
        from datetime import datetime

        memory.add_task("Ship API", due="2026-07-10")
        memory.add_reminder("Review docs", datetime.now())
        self._seed_memory("Indexed thought", "insight")
        self.client = TestClient(create_app())

    def _seed_memory(self, text: str, source_type: str) -> None:
        """Insert a memory row without loading the embedding model."""
        from memory.semantic import ledger

        ledger.insert(
            memory_id="test-mem-1",
            text=text,
            source_type=source_type,
            source_id=None,
            metadata={},
            content_hash="testhash",
            importance=0.5,
            tier="short_term",
            embedding_model="test",
            embedding_version="0",
            embedding_dimension=384,
        )

    def tearDown(self) -> None:
        for p in self._patches:
            p.stop()
        self._tmpdir.cleanup()

    def test_health(self) -> None:
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")

    def test_home_projection(self) -> None:
        resp = self.client.get("/home")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("cards", body)
        self.assertIn("panels", body)
        card_ids = {c["id"] for c in body["cards"]}
        self.assertIn("open_tasks", card_ids)
        self.assertIn("memory_count", card_ids)
        panel_ids = {p["id"] for p in body["panels"]}
        self.assertEqual(panel_ids, {"reminders", "open_tasks", "calendar"})

    def test_memories_browse_and_stats(self) -> None:
        resp = self.client.get("/memories?search=Indexed&sort=created_at&order=desc")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertGreaterEqual(body["total"], 1)
        self.assertTrue(any("Indexed" in m["text"] for m in body["memories"]))

        stats = self.client.get("/memories/stats")
        self.assertEqual(stats.status_code, 200)
        self.assertGreaterEqual(stats.json()["count"], 1)

    def test_graph_snapshot_and_stats(self) -> None:
        e1 = memory.create_entity("project", "Desktop")
        e2 = memory.create_entity("person", "Sam")
        memory.link_entities(e1, e2, "WORKS_ON")

        snap = self.client.get("/graph")
        self.assertEqual(snap.status_code, 200)
        self.assertGreaterEqual(len(snap.json()["entities"]), 2)

        stats = self.client.get("/graph/stats")
        self.assertEqual(stats.status_code, 200)
        self.assertGreaterEqual(stats.json()["entity_count"], 2)

    def test_tasks_include_done(self) -> None:
        memory.complete_task("Ship API")
        memory.add_task("Another open task")
        resp = self.client.get("/tasks")
        self.assertEqual(resp.status_code, 200)
        statuses = {t["status"] for t in resp.json()["tasks"]}
        self.assertIn("open", statuses)
        self.assertIn("done", statuses)

    def test_system_status(self) -> None:
        resp = self.client.get("/system/status")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn(body["status"], ("ok", "degraded", "unavailable"))
        names = {s["name"] for s in body["subsystems"]}
        self.assertTrue({"database", "semantic_memory", "graph", "brain"}.issubset(names))
        db = next(s for s in body["subsystems"] if s["name"] == "database")
        self.assertEqual(db["status"], "ok")


class PhaseADomainEventTests(unittest.TestCase):
    def test_chat_tool_event_mapping(self) -> None:
        events = tool_calls_to_mutations(
            [
                {"name": "add_task", "args": {"text": "x"}, "result": "Task logged."},
            ]
        )
        self.assertEqual(events[0].event_type, "task.created")
        events = tool_calls_to_mutations(
            [
                {"name": "complete_task", "args": {"text": "x"}, "result": "Task marked done."},
            ]
        )
        self.assertEqual(events[0].event_type, "task.updated")

    def test_tool_mutation_succeeded(self) -> None:
        self.assertTrue(
            tool_mutation_succeeded(
                "complete_task",
                {"text": "x"},
                "Task marked done.",
            )
        )
        self.assertFalse(
            tool_mutation_succeeded(
                "complete_task",
                {"text": "x"},
                "No matching task found.",
            )
        )

    def test_publish_mutation_events_skips_empty_event_type(self) -> None:
        received: list[tuple] = []

        def handler(channel, event_type, payload):
            received.append((channel, event_type, payload))

        subscribe(handler)
        publish_mutation_events(
            [
                MutationEvent(
                    event_type="",
                    entity_type="journal",
                    operation="create",
                    entity={"text": "entry"},
                ),
                MutationEvent(
                    event_type="task.created",
                    entity_type="task",
                    operation="create",
                    entity={"id": 1, "text": "x"},
                ),
            ]
        )
        events = {e[1] for e in received if e[0] == "events"}
        self.assertEqual(events, {"task.created"})

    def test_publish_mutation_events_emits_successful_mutations(self) -> None:
        received: list[tuple] = []

        def handler(channel, event_type, payload):
            received.append((channel, event_type, payload))

        subscribe(handler)
        publish_mutation_events(
            [
                MutationEvent(
                    event_type="task.created",
                    entity_type="task",
                    operation="create",
                    entity={"id": 1, "text": "x"},
                ),
                MutationEvent(
                    event_type="task.updated",
                    entity_type="task",
                    operation="complete",
                    entity={"id": 1, "text": "x", "status": "done"},
                ),
            ]
        )
        events = {e[1] for e in received if e[0] == "events"}
        self.assertIn("task.created", events)
        self.assertIn("task.updated", events)


class PhaseAWebSocketIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmpdir.name) / "test.db"
        self.lance_path = Path(self._tmpdir.name) / "lancedb"
        self._patches = [
            patch.object(_connection, "DB_PATH", self.db_path),
            patch.object(_connection, "LANCEDB_PATH", self.lance_path),
        ]
        for p in self._patches:
            p.start()
        _connection.ensure_storage_paths()
        init_db()

    def tearDown(self) -> None:
        for p in self._patches:
            p.stop()
        self._tmpdir.cleanup()

    def test_websocket_hub_delivers_runtime_event(self) -> None:
        with TestClient(create_app()) as client:
            with client.websocket_connect("/ws/events") as ws:
                publish(
                    "events",
                    "task.updated",
                    {
                        "entity_type": "task",
                        "operation": "complete",
                        "entity_id": 1,
                    },
                )
                msg = json.loads(ws.receive_text())
                self.assertEqual(msg["event"], "task.updated")
                self.assertEqual(msg["data"]["entity_type"], "task")
                self.assertEqual(msg["data"]["operation"], "complete")
                ws.send_text("ping")


if __name__ == "__main__":
    unittest.main()
