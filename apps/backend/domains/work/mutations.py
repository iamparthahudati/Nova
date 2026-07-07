"""Pure MutationEvent builders for WorkOS operations (WORKOS_PHASE1_SCHEMA §8).

Event names follow `work.<entity>.<operation>`. The `entity` payload is the full
aggregate snapshot; `metadata` carries invalidation routing ids only — never
business data, never derived values.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Optional

from runtime.mutation_event import MutationEvent

from .aggregates import ActionItem, Note, PriorityPolicy, Project, WorkItem


def _routing(owner_id: int, entity_id: int, project_id: Optional[int] = None) -> dict:
    metadata: dict = {"entity_id": entity_id, "owner_id": owner_id}
    if project_id is not None:
        metadata["project_id"] = project_id
    return metadata


def build_note_captured(note: Note) -> MutationEvent:
    return MutationEvent(
        event_type="work.note.captured",
        entity_type="note",
        operation="capture",
        entity=asdict(note),
        metadata=_routing(note.owner_id, note.id),
    )


def build_note_triaged(note: Note) -> MutationEvent:
    return MutationEvent(
        event_type="work.note.triaged",
        entity_type="note",
        operation="triage",
        entity=asdict(note),
        metadata=_routing(note.owner_id, note.id),
    )


def build_action_item_created(item: ActionItem) -> MutationEvent:
    return MutationEvent(
        event_type="work.actionitem.created",
        entity_type="action_item",
        operation="create",
        entity=asdict(item),
        metadata=_routing(item.owner_id, item.id),
    )


def build_action_item_promoted(item: ActionItem, work_item: WorkItem) -> MutationEvent:
    return MutationEvent(
        event_type="work.actionitem.promoted",
        entity_type="action_item",
        operation="promote",
        entity={"action_item": asdict(item), "work_item": asdict(work_item)},
        metadata=_routing(item.owner_id, item.id, work_item.project_id),
    )


def build_action_item_dismissed(item: ActionItem) -> MutationEvent:
    return MutationEvent(
        event_type="work.actionitem.dismissed",
        entity_type="action_item",
        operation="dismiss",
        entity=asdict(item),
        metadata=_routing(item.owner_id, item.id),
    )


def build_project_created(project: Project) -> MutationEvent:
    return MutationEvent(
        event_type="work.project.created",
        entity_type="project",
        operation="create",
        entity=asdict(project),
        metadata=_routing(project.owner_id, project.id),
    )


def build_project_updated(project: Project) -> MutationEvent:
    return MutationEvent(
        event_type="work.project.updated",
        entity_type="project",
        operation="update",
        entity=asdict(project),
        metadata=_routing(project.owner_id, project.id),
    )


def build_project_archived(project: Project) -> MutationEvent:
    return MutationEvent(
        event_type="work.project.archived",
        entity_type="project",
        operation="archive",
        entity=asdict(project),
        metadata=_routing(project.owner_id, project.id),
    )


def build_project_completed(project: Project) -> MutationEvent:
    return MutationEvent(
        event_type="work.project.completed",
        entity_type="project",
        operation="complete",
        entity=asdict(project),
        metadata=_routing(project.owner_id, project.id),
    )


def build_item_created(item: WorkItem) -> MutationEvent:
    return MutationEvent(
        event_type="work.item.created",
        entity_type="work_item",
        operation="create",
        entity=asdict(item),
        metadata=_routing(item.owner_id, item.id, item.project_id),
    )


def build_item_updated(item: WorkItem) -> MutationEvent:
    return MutationEvent(
        event_type="work.item.updated",
        entity_type="work_item",
        operation="update",
        entity=asdict(item),
        metadata=_routing(item.owner_id, item.id, item.project_id),
    )


def build_item_transitioned(item: WorkItem) -> MutationEvent:
    """Status change. `done`/`cancelled` carry their own semantic event_type."""
    event_type = "work.item.transitioned"
    operation = "transition"
    if item.status == "done":
        event_type, operation = "work.item.completed", "complete"
    elif item.status == "cancelled":
        event_type, operation = "work.item.cancelled", "cancel"
    return MutationEvent(
        event_type=event_type,
        entity_type="work_item",
        operation=operation,
        entity=asdict(item),
        metadata=_routing(item.owner_id, item.id, item.project_id),
    )


def build_item_deleted(item: WorkItem) -> MutationEvent:
    return MutationEvent(
        event_type="work.item.deleted",
        entity_type="work_item",
        operation="delete",
        entity=asdict(item),
        metadata=_routing(item.owner_id, item.id, item.project_id),
    )


def build_priority_reweighted(policy: PriorityPolicy) -> MutationEvent:
    return MutationEvent(
        event_type="work.priority.reweighted",
        entity_type="priority_policy",
        operation="reweight",
        entity=asdict(policy),
        metadata=_routing(policy.owner_id, policy.id),
    )
