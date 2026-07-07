"""WorkOS REST/chat write commands — delegate to domain services, build events.

Both the API routers and the chat/voice tool handlers call these functions, so a
mutation issued over either channel produces an identical row and event
(WORKOS_PHASE1_SCHEMA §13.4 parity).
"""

from __future__ import annotations

from typing import Optional

from domains.work.drafts import TaskDraft
from domains.work.errors import WorkConflictError, WorkNotFoundError, WorkValidationError
from domains.work.mutations import (
    build_action_item_created,
    build_action_item_dismissed,
    build_action_item_promoted,
    build_item_created,
    build_item_deleted,
    build_item_transitioned,
    build_item_updated,
    build_note_captured,
    build_note_triaged,
    build_priority_reweighted,
    build_project_archived,
    build_project_completed,
    build_project_created,
    build_project_updated,
)
from domains.work.planning import PriorityPolicyService
from domains.work.project_service import ProjectService
from domains.work.validation import Deadline, Estimate
from domains.work.work_item_service import WorkItemService
from domains.work.workspace import CaptureService, PromotionService

from . import work_serializers as ser

_capture = CaptureService()
_promotion = PromotionService()
_projects = ProjectService()
_items = WorkItemService()
_policy = PriorityPolicyService()

# Third element is a list of runtime.MutationEvent built by domains.work.mutations
# and passed through opaquely — the planner never constructs them (keeps
# services.planner off the runtime edge; events stay a domain concern).
_Command = tuple[dict, str, list]


def capture_note(
    body: str,
    capture_source: str = "manual",
    captured_on: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    owner_id: int = 1,
) -> _Command:
    note, created = _capture.capture_note(
        body, capture_source, captured_on, idempotency_key, owner_id
    )
    events = [build_note_captured(note)] if created else []
    return ser.serialize_note(note), "Captured.", events


def triage_to_task(note_id: int, updated_at: str, task: dict, owner_id: int = 1) -> _Command:
    note, item = _capture.triage_to_task(note_id, updated_at, _task_draft(task), owner_id)
    events = [build_note_triaged(note), build_item_created(item)]
    return ser.serialize_work_item(item), "Triaged to task.", events


def triage_to_dismiss(note_id: int, updated_at: str, owner_id: int = 1) -> _Command:
    note = _capture.triage_to_dismiss(note_id, updated_at, owner_id)
    return ser.serialize_note(note), "Dismissed.", [build_note_triaged(note)]


def create_action_item(title: str, note_id: Optional[int] = None, owner_id: int = 1) -> _Command:
    item = _capture.create_action_item(title, note_id, "manual", owner_id)
    return ser.serialize_action_item(item), "Action item added.", [build_action_item_created(item)]


def promote_action_item(
    action_item_id: int, updated_at: str, project_id: int, owner_id: int = 1
) -> _Command:
    action_item, work_item = _promotion.promote_action_item(
        action_item_id, updated_at, project_id, owner_id
    )
    event = build_action_item_promoted(action_item, work_item)
    return ser.serialize_work_item(work_item), "Promoted to task.", [event]


def dismiss_action_item(action_item_id: int, updated_at: str, owner_id: int = 1) -> _Command:
    item = _promotion.dismiss_action_item(action_item_id, updated_at, owner_id)
    return ser.serialize_action_item(item), "Dismissed.", [build_action_item_dismissed(item)]


def create_project(
    name: str,
    objective: Optional[str] = None,
    planned_start_on: Optional[str] = None,
    planned_end_on: Optional[str] = None,
    owner_id: int = 1,
) -> _Command:
    project = _projects.create_project(
        name, objective, (planned_start_on, planned_end_on), "manual", owner_id
    )
    return (
        ser.serialize_project(project),
        f"Project {project.name} created.",
        [build_project_created(project)],
    )


def update_project(project_id: int, updated_at: str, patch: dict, owner_id: int = 1) -> _Command:
    project = _projects.update_project(project_id, updated_at, patch, owner_id)
    return ser.serialize_project(project), "Project updated.", [build_project_updated(project)]


def archive_project(project_id: int, updated_at: str, owner_id: int = 1) -> _Command:
    project = _projects.archive_project(project_id, updated_at, owner_id)
    return ser.serialize_project(project), "Project archived.", [build_project_archived(project)]


def complete_project(project_id: int, updated_at: str, owner_id: int = 1) -> _Command:
    project = _projects.complete_project(project_id, updated_at, owner_id)
    return ser.serialize_project(project), "Project completed.", [build_project_completed(project)]


def create_task(task: dict, owner_id: int = 1) -> _Command:
    item = _items.create_task(_task_draft(task), owner_id)
    return ser.serialize_work_item(item), "Task created.", [build_item_created(item)]


def update_task(item_id: int, updated_at: str, patch: dict, owner_id: int = 1) -> _Command:
    item = _items.update_task(item_id, updated_at, _item_patch(patch), owner_id)
    return ser.serialize_work_item(item), "Task updated.", [build_item_updated(item)]


def transition_task(item_id: int, updated_at: str, to_status: str, owner_id: int = 1) -> _Command:
    item = _items.transition_task(item_id, updated_at, to_status, owner_id)
    return ser.serialize_work_item(item), "Task updated.", [build_item_transitioned(item)]


def delete_task(item_id: int, updated_at: str, owner_id: int = 1) -> _Command:
    item = _items.delete_task(item_id, updated_at, owner_id)
    return ser.serialize_work_item(item), "Task deleted.", [build_item_deleted(item)]


def reweight_priority(
    deadline_weight: int, decay_weight: int, updated_at: str, owner_id: int = 1
) -> _Command:
    policy = _policy.reweight(deadline_weight, decay_weight, updated_at, owner_id)
    return (
        ser.serialize_priority_policy(policy),
        "Priorities reweighted.",
        [build_priority_reweighted(policy)],
    )


def _task_draft(task: dict) -> TaskDraft:
    return TaskDraft(
        project_id=task["project_id"],
        title=task["title"],
        estimate=_estimate(task),
        deadline=_deadline(task),
        source=task.get("source", "manual"),
    )


def _item_patch(patch: dict) -> dict:
    fields: dict = {}
    if "title" in patch:
        fields["title"] = patch["title"]
    if "estimate_minutes" in patch or "estimate_confidence" in patch:
        fields["estimate"] = _estimate(patch)
    if "deadline_on" in patch or "deadline_hardness" in patch:
        fields["deadline"] = _deadline(patch)
    return fields


def _estimate(fields: dict) -> Optional[Estimate]:
    minutes = fields.get("estimate_minutes")
    if minutes is None:
        return None
    confidence = fields.get("estimate_confidence")
    if confidence is None:
        raise WorkValidationError("estimate_confidence is required when an estimate is set")
    return Estimate.create(minutes, confidence)


def _deadline(fields: dict) -> Optional[Deadline]:
    deadline_on = fields.get("deadline_on")
    if deadline_on is None:
        return None
    hardness = fields.get("deadline_hardness")
    if hardness is None:
        raise WorkValidationError("deadline_hardness is required when a deadline is set")
    return Deadline.create(deadline_on, hardness)


__all__ = [
    "WorkConflictError",
    "WorkNotFoundError",
    "WorkValidationError",
    "capture_note",
    "triage_to_task",
    "triage_to_dismiss",
    "create_action_item",
    "promote_action_item",
    "dismiss_action_item",
    "create_project",
    "update_project",
    "archive_project",
    "complete_project",
    "create_task",
    "update_task",
    "transition_task",
    "delete_task",
    "reweight_priority",
]
