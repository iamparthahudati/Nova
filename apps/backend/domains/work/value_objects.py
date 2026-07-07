"""Closed enums and WorkOS mutation vocabulary — pure, no I/O."""

from __future__ import annotations

from enum import Enum

# Additive entity_type values for MutationEvent.entity_type (ADR 0021 §8).
# The MutationEvent dataclass shape is frozen; only this vocabulary grows.
WORK_ENTITY_TYPES: frozenset[str] = frozenset(
    {
        "action_item",
        "client",
        "day_plan",
        "deliverable",
        "dependency",
        "document_ref",
        "engagement",
        "focus_session",
        "goal",
        "interaction",
        "key_result",
        "learning_path",
        "life_goal",
        "meeting",
        "milestone",
        "note",
        "pinned_risk",
        "priority_policy",
        "product",
        "project",
        "release",
        "report",
        "revenue_expectation",
        "roadmap_plan",
        "saved_view",
        "sprint",
        "time_block",
        "time_entry",
        "work_item",
    },
)


class LedgerKind(str, Enum):
    COMMITMENT = "commitment"
    TIME = "time"
    HOLDING = "holding"
    ARTIFACT = "artifact"


class CaptureSource(str, Enum):
    MANUAL = "manual"
    CHAT = "chat"
    VOICE = "voice"


class NoteStatus(str, Enum):
    CAPTURED = "captured"
    TRIAGED = "triaged"
    ARCHIVED = "archived"


class TriageOutcomeKind(str, Enum):
    WORK_ITEM = "work_item"
    NOTE = "note"
    DISMISSED = "dismissed"


class ActionItemStatus(str, Enum):
    OPEN = "open"
    PROMOTED = "promoted"
    DISMISSED = "dismissed"


class ProjectStatus(str, Enum):
    IDEA = "idea"
    PLANNED = "planned"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class WorkItemStatus(str, Enum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    CANCELLED = "cancelled"


class EstimateConfidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DeadlineHardness(str, Enum):
    HARD = "hard"
    SOFT = "soft"


# Terminal statuses excluded from the open-commitment / PriorityQueue set.
CLOSED_WORK_ITEM_STATUSES: frozenset[str] = frozenset(
    {WorkItemStatus.DONE.value, WorkItemStatus.CANCELLED.value},
)
