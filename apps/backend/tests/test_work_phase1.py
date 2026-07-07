"""WorkOS Phase 1 tests — real SQLite, no mocks (WORKOS_PHASE1_SCHEMA §13)."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from domains.work.drafts import TaskDraft
from domains.work.errors import WorkConflictError, WorkValidationError
from domains.work.insights import build_briefing_shell
from domains.work.mutations import (
    build_action_item_promoted,
    build_item_transitioned,
    build_note_captured,
)
from domains.work.planning import PriorityPolicyService, build_priority_queue
from domains.work.planning.prioritization import DEADLINE_HORIZON_DAYS
from domains.work.project_service import ProjectService
from domains.work.repository_adapters import SqliteWorkItemRepository
from domains.work.validation import Deadline, Estimate
from domains.work.work_item_service import WorkItemService
from domains.work.workspace import CaptureService, PromotionService
from memory import _connection
from memory.schema import init_db
from memory.work.migrations import (
    FORBIDDEN_DERIVED_COLUMNS,
    assert_migration_source_governance,
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]
_FIXED_NOW = datetime(2026, 7, 7, 9, 0, tzinfo=timezone.utc)


class WorkPhase1TestCase(unittest.TestCase):
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
        self.projects = ProjectService()
        self.items = WorkItemService()
        self.capture = CaptureService()
        self.promotion = PromotionService()
        self.policy = PriorityPolicyService()

    def tearDown(self) -> None:
        for patcher in self._patches:
            patcher.stop()
        self._tmpdir.cleanup()

    def _project(self, name: str = "Nova"):
        return self.projects.create_project(name)


class SchemaGovernanceTests(WorkPhase1TestCase):
    def test_ddl_source_governance(self) -> None:
        source = (BACKEND_ROOT / "memory" / "work" / "migrations.py").read_text(encoding="utf-8")
        assert_migration_source_governance(source)

    def test_five_tables_present_and_fk_clean(self) -> None:
        with _connection.connect(rows=True) as con:
            tables = {
                row[0]
                for row in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'work_%'"
                ).fetchall()
            }
            fk_problems = con.execute("PRAGMA foreign_key_check").fetchall()
        self.assertEqual(
            tables,
            {
                "work_notes",
                "work_action_items",
                "work_projects",
                "work_items",
                "work_priority_policies",
            },
        )
        self.assertEqual(fk_problems, [])

    def test_no_forbidden_or_missing_owner_columns(self) -> None:
        with _connection.connect() as con:
            for table in ("work_notes", "work_action_items", "work_projects", "work_items"):
                columns = {row[1] for row in con.execute(f"PRAGMA table_info({table})").fetchall()}
                self.assertIn("owner_id", columns)
                self.assertEqual(FORBIDDEN_DERIVED_COLUMNS & columns, set())


class MemoryIntegrationTests(WorkPhase1TestCase):
    def test_capture_idempotency_key(self) -> None:
        first, created_first = self.capture.capture_note("call bank", idempotency_key="k1")
        second, created_second = self.capture.capture_note("call bank", idempotency_key="k1")
        self.assertTrue(created_first)
        self.assertFalse(created_second)
        self.assertEqual(first.id, second.id)
        self.assertEqual(len(self.capture.list_inbox()), 1)

    def test_project_name_unique_live_case_insensitive(self) -> None:
        self._project("Nova")
        with self.assertRaises(WorkValidationError):
            self._project("nova")

    def test_work_item_estimate_requires_confidence(self) -> None:
        with self.assertRaises(WorkValidationError):
            Estimate.create(30, "")  # missing/invalid confidence

    def test_soft_delete_excludes_from_open_commitments(self) -> None:
        project = self._project()
        item = self.items.create_task(TaskDraft(project_id=project.id, title="draft"))
        self.items.delete_task(item.id, item.updated_at)
        opens = SqliteWorkItemRepository().list_open_commitments(1)
        self.assertEqual(opens, [])

    def test_priority_policy_singleton_seed(self) -> None:
        self.policy.get_active_policy()
        with _connection.connect() as con:
            count = con.execute(
                "SELECT COUNT(*) FROM work_priority_policies WHERE owner_id = 1 AND is_active = 1"
            ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_optimistic_concurrency_conflict(self) -> None:
        project = self._project()
        with self.assertRaises(WorkConflictError):
            self.projects.update_project(project.id, "1999-01-01T00:00:00+00:00", {"name": "New"})

    def test_promote_action_item_idempotent(self) -> None:
        project = self._project()
        action = self.capture.create_action_item("ship changelog")
        first_item, work_one = self.promotion.promote_action_item(
            action.id, action.updated_at, project.id
        )
        again_item, work_two = self.promotion.promote_action_item(
            first_item.id, first_item.updated_at, project.id
        )
        self.assertEqual(work_one.id, work_two.id)
        self.assertEqual(first_item.status, "promoted")
        with self.assertRaises(sqlite3.IntegrityError):
            self._force_second_work_item(action.id, project.id)

    def _force_second_work_item(self, action_id: int, project_id: int) -> None:
        with _connection.connect() as con:
            now = _connection.now()
            con.execute(
                """
                INSERT INTO work_items (owner_id, project_id, title, action_item_id,
                                        created_at, updated_at)
                VALUES (1, ?, 'dup', ?, ?, ?)
                """,
                (project_id, action_id, now, now),
            )

    def test_triage_to_task_is_atomic_and_links_outcome(self) -> None:
        project = self._project()
        note, _created = self.capture.capture_note("email lead", source="chat")
        triaged, item = self.capture.triage_to_task(
            note.id, note.updated_at, TaskDraft(project_id=project.id, title="email lead")
        )
        self.assertEqual(triaged.status, "triaged")
        self.assertEqual(triaged.outcome_kind, "work_item")
        self.assertEqual(triaged.outcome_id, item.id)
        self.assertEqual(self.capture.list_inbox(), [])

    def test_cannot_create_task_under_archived_project(self) -> None:
        project = self._project()
        archived = self.projects.archive_project(project.id, project.updated_at)
        with self.assertRaises(WorkValidationError):
            self.items.create_task(TaskDraft(project_id=archived.id, title="late"))


class PrioritizationTests(WorkPhase1TestCase):
    def _task(self, project_id, title, deadline=None):
        return self.items.create_task(
            TaskDraft(project_id=project_id, title=title, deadline=deadline)
        )

    def test_deadline_ordering_earlier_hard_ranks_higher(self) -> None:
        project = self._project()
        soon = self._task(project.id, "soon", Deadline.create("2026-07-08", "hard"))
        later = self._task(project.id, "later", Deadline.create("2026-07-20", "hard"))
        queue = build_priority_queue(
            SqliteWorkItemRepository().list_open_commitments(1),
            self.policy.get_active_policy(),
            _FIXED_NOW,
        )
        ordered = [entry.item.id for entry in queue.entries]
        self.assertLess(ordered.index(soon.id), ordered.index(later.id))

    def test_decay_promotes_stale_items(self) -> None:
        project = self._project()
        fresh = self._task(project.id, "fresh")
        stale = self._task(project.id, "stale")
        self._age_item(stale.id, "2026-06-01T09:00:00+00:00")
        opens = SqliteWorkItemRepository().list_open_commitments(1)
        queue = build_priority_queue(opens, self.policy.get_active_policy(), _FIXED_NOW)
        ordered = [entry.item.id for entry in queue.entries]
        self.assertLess(ordered.index(stale.id), ordered.index(fresh.id))

    def test_no_deadline_scores_from_decay_only(self) -> None:
        project = self._project()
        item = self._task(project.id, "someday")
        queue = build_priority_queue(
            SqliteWorkItemRepository().list_open_commitments(1),
            self.policy.get_active_policy(),
            _FIXED_NOW,
        )
        entry = next(e for e in queue.entries if e.item.id == item.id)
        self.assertEqual(entry.deadline_term, 0)
        self.assertIsNone(entry.days_to_deadline)

    def test_queue_output_not_persisted(self) -> None:
        project = self._project()
        self._task(project.id, "x", Deadline.create("2026-07-08", "hard"))
        build_priority_queue(
            SqliteWorkItemRepository().list_open_commitments(1),
            self.policy.get_active_policy(),
            _FIXED_NOW,
        )
        with _connection.connect() as con:
            for table in ("work_notes", "work_action_items", "work_projects", "work_items"):
                columns = {row[1] for row in con.execute(f"PRAGMA table_info({table})").fetchall()}
                self.assertNotIn("priority_score", columns)
                self.assertNotIn("priority_rank", columns)

    def test_briefing_shell_counts(self) -> None:
        project = self._project()
        self._task(project.id, "overdue", Deadline.create("2026-07-01", "hard"))
        self._task(project.id, "future", Deadline.create("2026-07-30", "soft"))
        self.capture.capture_note("loose thought")
        queue = build_priority_queue(
            SqliteWorkItemRepository().list_open_commitments(1),
            self.policy.get_active_policy(),
            _FIXED_NOW,
        )
        briefing = build_briefing_shell(queue, inbox_count=1, now=_FIXED_NOW)
        self.assertEqual(briefing.open_commitment_count, 2)
        self.assertEqual(briefing.inbox_count, 1)
        self.assertEqual(briefing.overdue_hard_deadline_count, 1)

    def test_deadline_horizon_bounds_far_future(self) -> None:
        project = self._project()
        item = self._task(project.id, "far", Deadline.create("2027-01-01", "hard"))
        queue = build_priority_queue(
            SqliteWorkItemRepository().list_open_commitments(1),
            self.policy.get_active_policy(),
            _FIXED_NOW,
        )
        entry = next(e for e in queue.entries if e.item.id == item.id)
        self.assertGreater(entry.days_to_deadline, DEADLINE_HORIZON_DAYS)
        self.assertEqual(entry.deadline_term, 0)

    def _age_item(self, item_id: int, updated_at: str) -> None:
        with _connection.connect() as con:
            con.execute("UPDATE work_items SET updated_at = ? WHERE id = ?", (updated_at, item_id))


class MutationEventTests(WorkPhase1TestCase):
    def test_note_captured_event_shape(self) -> None:
        note, _created = self.capture.capture_note("ship it", source="voice")
        event = build_note_captured(note)
        self.assertEqual(event.event_type, "work.note.captured")
        self.assertEqual(event.entity_type, "note")
        self.assertEqual(event.operation, "capture")
        self.assertEqual(event.entity["body"], "ship it")
        self.assertEqual(event.metadata["owner_id"], 1)

    def test_promote_composite_event_carries_both_aggregates(self) -> None:
        project = self._project()
        action = self.capture.create_action_item("wire demo")
        action_item, work_item = self.promotion.promote_action_item(
            action.id, action.updated_at, project.id
        )
        event = build_action_item_promoted(action_item, work_item)
        self.assertEqual(event.event_type, "work.actionitem.promoted")
        self.assertIn("action_item", event.entity)
        self.assertIn("work_item", event.entity)
        self.assertEqual(event.metadata["project_id"], project.id)

    def test_done_transition_emits_completed_event(self) -> None:
        project = self._project()
        item = self.items.create_task(TaskDraft(project_id=project.id, title="close"))
        done = self.items.transition_task(item.id, item.updated_at, "done")
        event = build_item_transitioned(done)
        self.assertEqual(event.event_type, "work.item.completed")
        self.assertEqual(event.operation, "complete")


if __name__ == "__main__":
    unittest.main()
