"""WorkOS Phase 1 API + chat/voice parity tests — real SQLite via TestClient."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from memory import _connection
from memory.schema import init_db
from services.api import create_app
from services.planner import work_commands as work_cmd


class WorkApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._patches = [
            patch.object(_connection, "DB_PATH", Path(self._tmpdir.name) / "test.db"),
            patch.object(_connection, "LANCEDB_PATH", Path(self._tmpdir.name) / "lancedb"),
        ]
        for patcher in self._patches:
            patcher.start()
        _connection.ensure_storage_paths()
        init_db()
        self.client = TestClient(create_app())

    def tearDown(self) -> None:
        for patcher in self._patches:
            patcher.stop()
        self._tmpdir.cleanup()

    def _create_project(self, name: str = "Nova") -> dict:
        resp = self.client.post("/work/projects", json={"name": name})
        self.assertEqual(resp.status_code, 201)
        return resp.json()["item"]

    def test_capture_and_inbox(self) -> None:
        resp = self.client.post(
            "/work/captures", json={"body": "call supplier", "capture_source": "chat"}
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["item"]["status"], "captured")
        inbox = self.client.get("/work/captures/inbox").json()
        self.assertEqual(len(inbox), 1)
        self.assertEqual(inbox[0]["body"], "call supplier")

    def test_capture_idempotent_returns_same_row(self) -> None:
        body = {"body": "same", "idempotency_key": "abc"}
        first = self.client.post("/work/captures", json=body).json()["item"]
        second = self.client.post("/work/captures", json=body).json()["item"]
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(len(self.client.get("/work/captures/inbox").json()), 1)

    def test_project_task_and_priority_queue(self) -> None:
        project = self._create_project()
        resp = self.client.post(
            "/work/items",
            json={
                "project_id": project["id"],
                "title": "ship",
                "estimate_minutes": 90,
                "estimate_confidence": "medium",
                "deadline_on": "2026-07-08",
                "deadline_hardness": "hard",
            },
        )
        self.assertEqual(resp.status_code, 201)
        queue = self.client.get("/work/priority/queue").json()
        self.assertEqual(len(queue["entries"]), 1)
        self.assertGreater(queue["entries"][0]["score"], 0)

    def test_triage_capture_to_task(self) -> None:
        project = self._create_project()
        note = self.client.post("/work/captures", json={"body": "fix bug"}).json()["item"]
        resp = self.client.post(
            f"/work/captures/{note['id']}/triage/task",
            json={
                "project_id": project["id"],
                "title": "fix bug",
                "updated_at": note["updated_at"],
            },
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(self.client.get("/work/captures/inbox").json(), [])

    def test_stale_update_returns_409(self) -> None:
        project = self._create_project()
        resp = self.client.patch(
            f"/work/projects/{project['id']}",
            json={"name": "Renamed", "updated_at": "1999-01-01T00:00:00+00:00"},
        )
        self.assertEqual(resp.status_code, 409)

    def test_missing_project_returns_404(self) -> None:
        resp = self.client.patch(
            "/work/projects/9999",
            json={"name": "Ghost", "updated_at": "2026-07-07T00:00:00+00:00"},
        )
        self.assertEqual(resp.status_code, 404)

    def test_briefing_and_policy_endpoints(self) -> None:
        project = self._create_project()
        self.client.post("/work/items", json={"project_id": project["id"], "title": "a"})
        briefing = self.client.get("/work/briefing/today").json()
        self.assertEqual(briefing["open_commitment_count"], 1)
        policy = self.client.get("/work/priority/policy").json()
        resp = self.client.patch(
            "/work/priority/policy",
            json={"deadline_weight": 500, "decay_weight": 50, "updated_at": policy["updated_at"]},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["item"]["deadline_weight"], 500)

    def test_chat_voice_capture_parity(self) -> None:
        """Same capture via REST and planner → identical row shape + one event."""
        rest_item = self.client.post(
            "/work/captures", json={"body": "parity", "capture_source": "voice"}
        ).json()["item"]
        planner_item, _message, events = work_cmd.capture_note("parity", "voice")
        ignore = {"id", "created_at", "updated_at"}
        rest_norm = {k: v for k, v in rest_item.items() if k not in ignore}
        planner_norm = {k: v for k, v in planner_item.items() if k not in ignore}
        self.assertEqual(rest_norm, planner_norm)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "work.note.captured")


if __name__ == "__main__":
    unittest.main()
