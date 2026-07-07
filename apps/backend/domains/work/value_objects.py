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
