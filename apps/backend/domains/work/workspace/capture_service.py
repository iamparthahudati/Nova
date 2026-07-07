"""CaptureService — frictionless intake and triage (Workspace context)."""

from __future__ import annotations

from datetime import date
from typing import Callable, Optional

from ..aggregates import ActionItem, Note, WorkItem
from ..drafts import TaskDraft
from ..errors import WorkConflictError, WorkNotFoundError, WorkValidationError
from ..repositories import ActionItemRepository, NoteRepository, ProjectRepository
from ..repository_adapters import (
    SqliteActionItemRepository,
    SqliteNoteRepository,
    SqliteProjectRepository,
)
from ..validation import (
    validate_capture_source,
    validate_captured_on,
    validate_non_empty_name,
)

DEFAULT_OWNER_ID = 1


class CaptureService:
    def __init__(
        self,
        notes: Optional[NoteRepository] = None,
        projects: Optional[ProjectRepository] = None,
        action_items: Optional[ActionItemRepository] = None,
        clock: Callable[[], date] = date.today,
    ) -> None:
        self._notes = notes or SqliteNoteRepository()
        self._projects = projects or SqliteProjectRepository()
        self._action_items = action_items or SqliteActionItemRepository()
        self._clock = clock

    def list_inbox(self, owner_id: int = DEFAULT_OWNER_ID, limit: int = 50) -> list[Note]:
        return self._notes.list_capture_inbox(owner_id, limit)

    def get_note(self, note_id: int, owner_id: int = DEFAULT_OWNER_ID) -> Note:
        note = self._notes.get_by_id(note_id, owner_id)
        if note is None:
            raise WorkNotFoundError(f"Note {note_id} not found")
        return note

    def capture_note(
        self,
        body: str,
        source: str = "manual",
        captured_on: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        owner_id: int = DEFAULT_OWNER_ID,
    ) -> tuple[Note, bool]:
        """Log a thought. Returns (note, created) — created=False on idempotent hit."""
        clean_body = validate_non_empty_name(body, "body")
        clean_source = validate_capture_source(source)
        day = captured_on or self._clock().isoformat()
        validate_captured_on(day, self._clock())
        if idempotency_key is not None:
            existing = self._notes.find_by_idempotency_key(owner_id, idempotency_key)
            if existing is not None:
                return existing, False
        note = self._notes.insert(
            {
                "owner_id": owner_id,
                "body": clean_body,
                "capture_source": clean_source,
                "captured_on": day,
                "capture_idempotency_key": idempotency_key,
                "source": clean_source,
            },
        )
        return note, True

    def triage_to_task(
        self,
        note_id: int,
        expected_updated_at: str,
        draft: TaskDraft,
        owner_id: int = DEFAULT_OWNER_ID,
    ) -> tuple[Note, WorkItem]:
        self._require_live_captured_note(note_id, owner_id)
        self._require_live_project(draft.project_id, owner_id)
        result = self._notes.triage_to_task(
            {
                "note_id": note_id,
                "owner_id": owner_id,
                "expected_updated_at": expected_updated_at,
                "work_item_fields": draft.to_item_fields(owner_id),
            },
        )
        if result is None:
            raise WorkConflictError(f"Note {note_id} was modified concurrently or already triaged")
        return result

    def triage_to_dismiss(
        self, note_id: int, expected_updated_at: str, owner_id: int = DEFAULT_OWNER_ID
    ) -> Note:
        self._require_live_captured_note(note_id, owner_id)
        note = self._notes.triage(
            {
                "note_id": note_id,
                "owner_id": owner_id,
                "expected_updated_at": expected_updated_at,
                "status": "triaged",
                "outcome_kind": "dismissed",
                "outcome_id": None,
            },
        )
        if note is None:
            raise WorkConflictError(f"Note {note_id} was modified concurrently or already triaged")
        return note

    def create_action_item(
        self,
        title: str,
        note_id: Optional[int] = None,
        source: str = "manual",
        owner_id: int = DEFAULT_OWNER_ID,
    ) -> ActionItem:
        clean_title = validate_non_empty_name(title, "title")
        if note_id is not None:
            self._require_live_captured_note(note_id, owner_id)
        return self._action_items.insert(
            {
                "owner_id": owner_id,
                "title": clean_title,
                "note_id": note_id,
                "source": source,
            },
        )

    def _require_live_captured_note(self, note_id: int, owner_id: int) -> None:
        note = self._notes.get_by_id(note_id, owner_id)
        if note is None or note.deleted_at is not None:
            raise WorkNotFoundError(f"Note {note_id} not found")
        if note.status != "captured":
            raise WorkValidationError(f"Note {note_id} is not in the capture inbox")

    def _require_live_project(self, project_id: int, owner_id: int) -> None:
        project = self._projects.get_by_id(project_id, owner_id)
        if project is None:
            raise WorkNotFoundError(f"Project {project_id} not found")
        if project.archived_at is not None:
            raise WorkValidationError(f"Cannot triage into archived project {project_id}")
