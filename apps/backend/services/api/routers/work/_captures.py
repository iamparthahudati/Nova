"""Capture routes — notes, triage, action items, promotion."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from runtime.side_effects import finalize_mutations
from services.planner import work_commands as work_cmd
from services.planner import work_queries as work_q

from ...dependencies import RequestContext, get_request_context
from ...schemas.common import MutationMeta
from ...schemas.work import (
    CaptureNoteRequest,
    ConcurrencyRequest,
    CreateActionItemRequest,
    PromoteActionItemRequest,
    TriageTaskRequest,
    WorkMutationResponse,
)
from ._support import work_error

router = APIRouter()


@router.get("/captures/inbox", response_model=list)
def capture_inbox(_ctx: RequestContext = Depends(get_request_context)) -> list:
    return work_q.list_capture_inbox()


@router.post("/captures", response_model=WorkMutationResponse, status_code=201)
def post_capture(
    body: CaptureNoteRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> WorkMutationResponse:
    try:
        item, message, events = work_cmd.capture_note(
            body.body, body.capture_source, body.captured_on, body.idempotency_key
        )
    except work_cmd.WorkValidationError as exc:
        raise work_error(exc) from None
    finalize_mutations(events)
    return WorkMutationResponse(item=item, meta=MutationMeta(message=message))


@router.post(
    "/captures/{note_id}/triage/task", response_model=WorkMutationResponse, status_code=201
)
def post_triage_task(
    note_id: int,
    body: TriageTaskRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> WorkMutationResponse:
    task = body.model_dump(exclude={"updated_at"})
    try:
        item, message, events = work_cmd.triage_to_task(note_id, body.updated_at, task)
    except (
        work_cmd.WorkNotFoundError,
        work_cmd.WorkConflictError,
        work_cmd.WorkValidationError,
    ) as exc:
        raise work_error(exc) from None
    finalize_mutations(events)
    return WorkMutationResponse(item=item, meta=MutationMeta(message=message))


@router.post("/captures/{note_id}/triage/dismiss", response_model=WorkMutationResponse)
def post_triage_dismiss(
    note_id: int,
    body: ConcurrencyRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> WorkMutationResponse:
    try:
        item, message, events = work_cmd.triage_to_dismiss(note_id, body.updated_at)
    except (
        work_cmd.WorkNotFoundError,
        work_cmd.WorkConflictError,
        work_cmd.WorkValidationError,
    ) as exc:
        raise work_error(exc) from None
    finalize_mutations(events)
    return WorkMutationResponse(item=item, meta=MutationMeta(message=message))


@router.get("/action-items", response_model=list)
def list_action_items(_ctx: RequestContext = Depends(get_request_context)) -> list:
    return work_q.list_open_action_items()


@router.post("/action-items", response_model=WorkMutationResponse, status_code=201)
def post_action_item(
    body: CreateActionItemRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> WorkMutationResponse:
    try:
        item, message, events = work_cmd.create_action_item(body.title, body.note_id)
    except (work_cmd.WorkNotFoundError, work_cmd.WorkValidationError) as exc:
        raise work_error(exc) from None
    finalize_mutations(events)
    return WorkMutationResponse(item=item, meta=MutationMeta(message=message))


@router.post(
    "/action-items/{item_id}/promote", response_model=WorkMutationResponse, status_code=201
)
def post_promote_action_item(
    item_id: int,
    body: PromoteActionItemRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> WorkMutationResponse:
    try:
        item, message, events = work_cmd.promote_action_item(
            item_id, body.updated_at, body.project_id
        )
    except (
        work_cmd.WorkNotFoundError,
        work_cmd.WorkConflictError,
        work_cmd.WorkValidationError,
    ) as exc:
        raise work_error(exc) from None
    finalize_mutations(events)
    return WorkMutationResponse(item=item, meta=MutationMeta(message=message))


@router.post("/action-items/{item_id}/dismiss", response_model=WorkMutationResponse)
def post_dismiss_action_item(
    item_id: int,
    body: ConcurrencyRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> WorkMutationResponse:
    try:
        item, message, events = work_cmd.dismiss_action_item(item_id, body.updated_at)
    except (work_cmd.WorkNotFoundError, work_cmd.WorkConflictError) as exc:
        raise work_error(exc) from None
    finalize_mutations(events)
    return WorkMutationResponse(item=item, meta=MutationMeta(message=message))
