"""SQLite repository adapters — call memory.work only. No SQL in the domain."""

from __future__ import annotations

from typing import Optional

from memory.work import action_items as action_item_store
from memory.work import items as item_store
from memory.work import notes as note_store
from memory.work import priority_policies as policy_store
from memory.work import projects as project_store

from .aggregates import ActionItem, Note, PriorityPolicy, Project, WorkItem


class SqliteNoteRepository:
    def get_by_id(self, note_id: int, owner_id: int) -> Optional[Note]:
        row = note_store.get_note_by_id(note_id, owner_id)
        return Note.from_row(row) if row else None

    def find_by_idempotency_key(self, owner_id: int, key: str) -> Optional[Note]:
        row = note_store.find_by_idempotency_key(owner_id, key)
        return Note.from_row(row) if row else None

    def list_capture_inbox(self, owner_id: int, limit: int) -> list[Note]:
        return [Note.from_row(row) for row in note_store.list_capture_inbox(owner_id, limit)]

    def insert(self, fields: dict) -> Note:
        return Note.from_row(note_store.create_note(fields))

    def triage(self, fields: dict) -> Optional[Note]:
        row = note_store.triage_note(fields)
        return Note.from_row(row) if row else None

    def triage_to_task(self, fields: dict) -> Optional[tuple[Note, WorkItem]]:
        result = note_store.triage_note_to_task(fields)
        if result is None:
            return None
        note_row, item_row = result
        return Note.from_row(note_row), WorkItem.from_row(item_row)

    def soft_delete(self, note_id: int, owner_id: int, expected_updated_at: str) -> Optional[Note]:
        row = note_store.soft_delete_note(note_id, owner_id, expected_updated_at)
        return Note.from_row(row) if row else None


class SqliteActionItemRepository:
    def get_by_id(self, item_id: int, owner_id: int) -> Optional[ActionItem]:
        row = action_item_store.get_action_item_by_id(item_id, owner_id)
        return ActionItem.from_row(row) if row else None

    def list_open(self, owner_id: int, limit: int) -> list[ActionItem]:
        rows = action_item_store.list_open_action_items(owner_id, limit)
        return [ActionItem.from_row(row) for row in rows]

    def insert(self, fields: dict) -> ActionItem:
        return ActionItem.from_row(action_item_store.create_action_item(fields))

    def promote(self, fields: dict) -> Optional[tuple[ActionItem, WorkItem]]:
        result = action_item_store.promote_action_item(fields)
        if result is None:
            return None
        action_row, item_row = result
        return ActionItem.from_row(action_row), WorkItem.from_row(item_row)

    def mark_dismissed(
        self, item_id: int, owner_id: int, expected_updated_at: str
    ) -> Optional[ActionItem]:
        row = action_item_store.mark_dismissed(item_id, owner_id, expected_updated_at)
        return ActionItem.from_row(row) if row else None


class SqliteProjectRepository:
    def get_by_id(self, project_id: int, owner_id: int) -> Optional[Project]:
        row = project_store.get_project_by_id(project_id, owner_id)
        return Project.from_row(row) if row else None

    def find_live_by_name(self, owner_id: int, name: str) -> Optional[Project]:
        row = project_store.find_live_by_name(owner_id, name)
        return Project.from_row(row) if row else None

    def list_live(self, owner_id: int) -> list[Project]:
        return [Project.from_row(row) for row in project_store.list_live_projects(owner_id)]

    def insert(self, fields: dict) -> Project:
        return Project.from_row(project_store.create_project(fields))

    def update(self, fields: dict) -> Optional[Project]:
        row = project_store.update_project(fields)
        return Project.from_row(row) if row else None

    def archive(
        self, project_id: int, owner_id: int, expected_updated_at: str
    ) -> Optional[Project]:
        row = project_store.archive_project(project_id, owner_id, expected_updated_at)
        return Project.from_row(row) if row else None

    def complete(
        self, project_id: int, owner_id: int, expected_updated_at: str
    ) -> Optional[Project]:
        row = project_store.complete_project(project_id, owner_id, expected_updated_at)
        return Project.from_row(row) if row else None


class SqliteWorkItemRepository:
    def get_by_id(self, item_id: int, owner_id: int) -> Optional[WorkItem]:
        row = item_store.get_work_item_by_id(item_id, owner_id)
        return WorkItem.from_row(row) if row else None

    def find_by_action_item_id(self, action_item_id: int, owner_id: int) -> Optional[WorkItem]:
        row = item_store.find_by_action_item_id(action_item_id, owner_id)
        return WorkItem.from_row(row) if row else None

    def list_live_for_project(self, project_id: int, owner_id: int) -> list[WorkItem]:
        rows = item_store.list_live_items_for_project(project_id, owner_id)
        return [WorkItem.from_row(row) for row in rows]

    def list_open_commitments(self, owner_id: int) -> list[WorkItem]:
        return [WorkItem.from_row(row) for row in item_store.list_open_commitments(owner_id)]

    def insert(self, fields: dict) -> WorkItem:
        return WorkItem.from_row(item_store.create_work_item(fields))

    def update(self, fields: dict) -> Optional[WorkItem]:
        row = item_store.update_work_item(fields)
        return WorkItem.from_row(row) if row else None

    def transition(self, fields: dict) -> Optional[WorkItem]:
        row = item_store.transition_work_item(fields)
        return WorkItem.from_row(row) if row else None

    def soft_delete(
        self, item_id: int, owner_id: int, expected_updated_at: str
    ) -> Optional[WorkItem]:
        row = item_store.soft_delete_work_item(item_id, owner_id, expected_updated_at)
        return WorkItem.from_row(row) if row else None


class SqlitePriorityPolicyRepository:
    def get_active(self, owner_id: int) -> Optional[PriorityPolicy]:
        row = policy_store.get_active_policy(owner_id)
        return PriorityPolicy.from_row(row) if row else None

    def ensure_default(self, owner_id: int) -> PriorityPolicy:
        return PriorityPolicy.from_row(policy_store.ensure_default_policy(owner_id))

    def update_weights(self, fields: dict) -> Optional[PriorityPolicy]:
        row = policy_store.update_policy_weights(fields)
        return PriorityPolicy.from_row(row) if row else None
