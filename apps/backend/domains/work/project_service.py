"""Project aggregate service — Holding lifecycle (Delivery context)."""

from __future__ import annotations

from datetime import date
from typing import Callable, Optional

from .aggregates import Project
from .errors import WorkConflictError, WorkNotFoundError, WorkValidationError
from .repositories import ProjectRepository
from .repository_adapters import SqliteProjectRepository
from .validation import (
    validate_non_empty_name,
    validate_project_dates,
    validate_project_status,
)

DEFAULT_OWNER_ID = 1


class ProjectService:
    def __init__(
        self,
        projects: Optional[ProjectRepository] = None,
        clock: Callable[[], date] = date.today,
    ) -> None:
        self._projects = projects or SqliteProjectRepository()
        self._clock = clock

    def get_project(self, project_id: int, owner_id: int = DEFAULT_OWNER_ID) -> Project:
        project = self._projects.get_by_id(project_id, owner_id)
        if project is None:
            raise WorkNotFoundError(f"Project {project_id} not found")
        return project

    def list_projects(self, owner_id: int = DEFAULT_OWNER_ID) -> list[Project]:
        return self._projects.list_live(owner_id)

    def create_project(
        self,
        name: str,
        objective: Optional[str] = None,
        dates: Optional[tuple[Optional[str], Optional[str]]] = None,
        source: str = "manual",
        owner_id: int = DEFAULT_OWNER_ID,
    ) -> Project:
        clean_name = validate_non_empty_name(name)
        start_on, end_on = dates or (None, None)
        validate_project_dates(start_on, end_on)
        if self._projects.find_live_by_name(owner_id, clean_name) is not None:
            raise WorkValidationError(f"A live project named {clean_name!r} already exists")
        return self._projects.insert(
            {
                "owner_id": owner_id,
                "name": clean_name,
                "objective": objective,
                "planned_start_on": start_on,
                "planned_end_on": end_on,
                "source": source,
            },
        )

    def update_project(
        self,
        project_id: int,
        expected_updated_at: str,
        patch: dict,
        owner_id: int = DEFAULT_OWNER_ID,
    ) -> Project:
        current = self.get_project(project_id, owner_id)
        if current.archived_at is not None:
            raise WorkConflictError(f"Project {project_id} is archived")
        fields = self._validated_patch(patch, current, owner_id)
        fields.update(
            {
                "project_id": project_id,
                "owner_id": owner_id,
                "expected_updated_at": expected_updated_at,
            }
        )
        updated = self._projects.update(fields)
        if updated is None:
            raise WorkConflictError(f"Project {project_id} was modified concurrently")
        return updated

    def archive_project(
        self, project_id: int, expected_updated_at: str, owner_id: int = DEFAULT_OWNER_ID
    ) -> Project:
        self.get_project(project_id, owner_id)
        archived = self._projects.archive(project_id, owner_id, expected_updated_at)
        if archived is None:
            raise WorkConflictError(f"Project {project_id} was modified concurrently or archived")
        return archived

    def complete_project(
        self, project_id: int, expected_updated_at: str, owner_id: int = DEFAULT_OWNER_ID
    ) -> Project:
        self.get_project(project_id, owner_id)
        completed = self._projects.complete(project_id, owner_id, expected_updated_at)
        if completed is None:
            raise WorkConflictError(f"Project {project_id} was modified concurrently or archived")
        return completed

    def _validated_patch(self, patch: dict, current: Project, owner_id: int) -> dict:
        fields: dict = {}
        if "name" in patch:
            clean_name = validate_non_empty_name(patch["name"])
            existing = self._projects.find_live_by_name(owner_id, clean_name)
            if existing is not None and existing.id != current.id:
                raise WorkValidationError(f"A live project named {clean_name!r} already exists")
            fields["name"] = clean_name
        if "objective" in patch:
            fields["objective"] = patch["objective"]
        if "status" in patch:
            fields["status"] = validate_project_status(patch["status"])
        start_on = patch.get("planned_start_on", current.planned_start_on)
        end_on = patch.get("planned_end_on", current.planned_end_on)
        if "planned_start_on" in patch or "planned_end_on" in patch:
            validate_project_dates(start_on, end_on)
            fields["planned_start_on"] = start_on
            fields["planned_end_on"] = end_on
        return fields
