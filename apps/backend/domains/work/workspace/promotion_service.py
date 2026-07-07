"""PromotionService — idempotent ActionItem → WorkItem (MT1)."""

from __future__ import annotations

from typing import Optional

from ..aggregates import ActionItem, WorkItem
from ..drafts import TaskDraft
from ..errors import WorkConflictError, WorkNotFoundError, WorkValidationError
from ..repositories import ActionItemRepository, ProjectRepository, WorkItemRepository
from ..repository_adapters import (
    SqliteActionItemRepository,
    SqliteProjectRepository,
    SqliteWorkItemRepository,
)
from ..validation import validate_non_empty_name

DEFAULT_OWNER_ID = 1


class PromotionService:
    def __init__(
        self,
        action_items: Optional[ActionItemRepository] = None,
        work_items: Optional[WorkItemRepository] = None,
        projects: Optional[ProjectRepository] = None,
    ) -> None:
        self._action_items = action_items or SqliteActionItemRepository()
        self._work_items = work_items or SqliteWorkItemRepository()
        self._projects = projects or SqliteProjectRepository()

    def get_action_item(self, item_id: int, owner_id: int = DEFAULT_OWNER_ID) -> ActionItem:
        item = self._action_items.get_by_id(item_id, owner_id)
        if item is None:
            raise WorkNotFoundError(f"Action item {item_id} not found")
        return item

    def list_open(self, owner_id: int = DEFAULT_OWNER_ID, limit: int = 50) -> list[ActionItem]:
        return self._action_items.list_open(owner_id, limit)

    def promote_action_item(
        self,
        action_item_id: int,
        expected_updated_at: str,
        project_id: int,
        owner_id: int = DEFAULT_OWNER_ID,
    ) -> tuple[ActionItem, WorkItem]:
        """MT1 — idempotent: an already-promoted item returns its existing pair."""
        item = self.get_action_item(action_item_id, owner_id)
        if item.status == "promoted":
            return self._existing_promotion(item, owner_id)
        if item.status != "open":
            raise WorkValidationError(f"Action item {action_item_id} cannot be promoted")
        self._require_live_project(project_id, owner_id)
        draft = TaskDraft(project_id=project_id, title=validate_non_empty_name(item.title, "title"))
        result = self._action_items.promote(
            {
                "item_id": action_item_id,
                "owner_id": owner_id,
                "expected_updated_at": expected_updated_at,
                "work_item_fields": draft.to_item_fields(owner_id),
            },
        )
        if result is None:
            raise WorkConflictError(
                f"Action item {action_item_id} was modified concurrently or already promoted"
            )
        return result

    def dismiss_action_item(
        self, action_item_id: int, expected_updated_at: str, owner_id: int = DEFAULT_OWNER_ID
    ) -> ActionItem:
        self.get_action_item(action_item_id, owner_id)
        dismissed = self._action_items.mark_dismissed(action_item_id, owner_id, expected_updated_at)
        if dismissed is None:
            raise WorkConflictError(
                f"Action item {action_item_id} was modified concurrently or not open"
            )
        return dismissed

    def _existing_promotion(self, item: ActionItem, owner_id: int) -> tuple[ActionItem, WorkItem]:
        work_item = self._work_items.find_by_action_item_id(item.id, owner_id)
        if work_item is None:
            raise WorkConflictError(
                f"Action item {item.id} is promoted but its work item is missing"
            )
        return item, work_item

    def _require_live_project(self, project_id: int, owner_id: int) -> None:
        project = self._projects.get_by_id(project_id, owner_id)
        if project is None:
            raise WorkNotFoundError(f"Project {project_id} not found")
        if project.archived_at is not None:
            raise WorkValidationError(f"Cannot promote into archived project {project_id}")
