"""WorkOS aggregate roots — immutable domain shapes built from storage rows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Note:
    id: int
    owner_id: int
    body: str
    capture_source: str
    captured_on: str
    status: str
    outcome_kind: Optional[str]
    outcome_id: Optional[int]
    capture_idempotency_key: Optional[str]
    source: str
    created_at: str
    updated_at: str
    deleted_at: Optional[str]

    @classmethod
    def from_row(cls, row: dict) -> "Note":
        return cls(
            id=int(row["id"]),
            owner_id=int(row["owner_id"]),
            body=str(row["body"]),
            capture_source=str(row["capture_source"]),
            captured_on=str(row["captured_on"]),
            status=str(row["status"]),
            outcome_kind=row.get("outcome_kind"),
            outcome_id=row.get("outcome_id"),
            capture_idempotency_key=row.get("capture_idempotency_key"),
            source=str(row["source"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            deleted_at=row.get("deleted_at"),
        )


@dataclass(frozen=True)
class ActionItem:
    id: int
    owner_id: int
    title: str
    status: str
    note_id: Optional[int]
    promoted_work_item_id: Optional[int]
    source: str
    created_at: str
    updated_at: str
    deleted_at: Optional[str]

    @classmethod
    def from_row(cls, row: dict) -> "ActionItem":
        return cls(
            id=int(row["id"]),
            owner_id=int(row["owner_id"]),
            title=str(row["title"]),
            status=str(row["status"]),
            note_id=row.get("note_id"),
            promoted_work_item_id=row.get("promoted_work_item_id"),
            source=str(row["source"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            deleted_at=row.get("deleted_at"),
        )


@dataclass(frozen=True)
class Project:
    id: int
    owner_id: int
    name: str
    objective: Optional[str]
    status: str
    planned_start_on: Optional[str]
    planned_end_on: Optional[str]
    release_id: Optional[int]
    engagement_id: Optional[int]
    source: str
    created_at: str
    updated_at: str
    archived_at: Optional[str]

    @classmethod
    def from_row(cls, row: dict) -> "Project":
        return cls(
            id=int(row["id"]),
            owner_id=int(row["owner_id"]),
            name=str(row["name"]),
            objective=row.get("objective"),
            status=str(row["status"]),
            planned_start_on=row.get("planned_start_on"),
            planned_end_on=row.get("planned_end_on"),
            release_id=row.get("release_id"),
            engagement_id=row.get("engagement_id"),
            source=str(row["source"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            archived_at=row.get("archived_at"),
        )


@dataclass(frozen=True)
class WorkItem:
    id: int
    owner_id: int
    project_id: int
    parent_id: Optional[int]
    type: str
    title: str
    status: str
    estimate_minutes: Optional[int]
    estimate_confidence: Optional[str]
    deadline_on: Optional[str]
    deadline_hardness: Optional[str]
    action_item_id: Optional[int]
    source: str
    created_at: str
    updated_at: str
    deleted_at: Optional[str]

    @classmethod
    def from_row(cls, row: dict) -> "WorkItem":
        return cls(
            id=int(row["id"]),
            owner_id=int(row["owner_id"]),
            project_id=int(row["project_id"]),
            parent_id=row.get("parent_id"),
            type=str(row["type"]),
            title=str(row["title"]),
            status=str(row["status"]),
            estimate_minutes=row.get("estimate_minutes"),
            estimate_confidence=row.get("estimate_confidence"),
            deadline_on=row.get("deadline_on"),
            deadline_hardness=row.get("deadline_hardness"),
            action_item_id=row.get("action_item_id"),
            source=str(row["source"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            deleted_at=row.get("deleted_at"),
        )


@dataclass(frozen=True)
class PriorityPolicy:
    id: int
    owner_id: int
    deadline_weight: int
    decay_weight: int
    is_active: bool
    source: str
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: dict) -> "PriorityPolicy":
        return cls(
            id=int(row["id"]),
            owner_id=int(row["owner_id"]),
            deadline_weight=int(row["deadline_weight"]),
            decay_weight=int(row["decay_weight"]),
            is_active=bool(row["is_active"]),
            source=str(row["source"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )
