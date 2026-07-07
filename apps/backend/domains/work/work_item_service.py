"""WorkItem aggregate service — Commitment ledger (Delivery context)."""

from __future__ import annotations

from typing import Optional

from .aggregates import WorkItem
from .drafts import TaskDraft
from .errors import WorkConflictError, WorkNotFoundError, WorkValidationError
from .repositories import ProjectRepository, WorkItemRepository
from .repository_adapters import SqliteProjectRepository, SqliteWorkItemRepository
from .validation import (
    Deadline,
    Estimate,
    validate_non_empty_name,
    validate_work_item_transition,
)
from .value_objects import WorkItemStatus

DEFAULT_OWNER_ID = 1


class WorkItemService:
    def __init__(
        self,
        items: Optional[WorkItemRepository] = None,
        projects: Optional[ProjectRepository] = None,
    ) -> None:
        self._items = items or SqliteWorkItemRepository()
        self._projects = projects or SqliteProjectRepository()

    def get_task(self, item_id: int, owner_id: int = DEFAULT_OWNER_ID) -> WorkItem:
        item = self._items.get_by_id(item_id, owner_id)
        if item is None:
            raise WorkNotFoundError(f"Work item {item_id} not found")
        return item

    def list_for_project(self, project_id: int, owner_id: int = DEFAULT_OWNER_ID) -> list[WorkItem]:
        return self._items.list_live_for_project(project_id, owner_id)

    def create_task(self, draft: TaskDraft, owner_id: int = DEFAULT_OWNER_ID) -> WorkItem:
        self._require_live_project(draft.project_id, owner_id)
        return self._items.insert(draft.to_item_fields(owner_id))

    def update_task(
        self,
        item_id: int,
        expected_updated_at: str,
        patch: dict,
        owner_id: int = DEFAULT_OWNER_ID,
    ) -> WorkItem:
        self.get_task(item_id, owner_id)
        fields = _validated_item_patch(patch)
        fields.update(
            {"item_id": item_id, "owner_id": owner_id, "expected_updated_at": expected_updated_at}
        )
        updated = self._items.update(fields)
        if updated is None:
            raise WorkConflictError(f"Work item {item_id} was modified concurrently")
        return updated

    def transition_task(
        self,
        item_id: int,
        expected_updated_at: str,
        to_status: str,
        owner_id: int = DEFAULT_OWNER_ID,
    ) -> WorkItem:
        target = validate_work_item_transition(to_status)
        self.get_task(item_id, owner_id)
        transitioned = self._items.transition(
            {
                "item_id": item_id,
                "owner_id": owner_id,
                "expected_updated_at": expected_updated_at,
                "to_status": target,
            },
        )
        if transitioned is None:
            raise WorkConflictError(f"Work item {item_id} was modified concurrently")
        return transitioned

    def cancel_task(
        self, item_id: int, expected_updated_at: str, owner_id: int = DEFAULT_OWNER_ID
    ) -> WorkItem:
        return self.transition_task(
            item_id, expected_updated_at, WorkItemStatus.CANCELLED.value, owner_id
        )

    def delete_task(
        self, item_id: int, expected_updated_at: str, owner_id: int = DEFAULT_OWNER_ID
    ) -> WorkItem:
        self.get_task(item_id, owner_id)
        deleted = self._items.soft_delete(item_id, owner_id, expected_updated_at)
        if deleted is None:
            raise WorkConflictError(f"Work item {item_id} was modified concurrently")
        return deleted

    def _require_live_project(self, project_id: int, owner_id: int) -> None:
        project = self._projects.get_by_id(project_id, owner_id)
        if project is None:
            raise WorkNotFoundError(f"Project {project_id} not found")
        if project.archived_at is not None:
            raise WorkValidationError(f"Cannot add tasks to archived project {project_id}")


def _validated_item_patch(patch: dict) -> dict:
    fields: dict = {}
    if "title" in patch:
        fields["title"] = validate_non_empty_name(patch["title"], "title")
    if "estimate" in patch:
        estimate: Optional[Estimate] = patch["estimate"]
        fields["estimate_minutes"] = estimate.minutes if estimate else None
        fields["estimate_confidence"] = estimate.confidence if estimate else None
    if "deadline" in patch:
        deadline: Optional[Deadline] = patch["deadline"]
        fields["deadline_on"] = deadline.on if deadline else None
        fields["deadline_hardness"] = deadline.hardness if deadline else None
    return fields
