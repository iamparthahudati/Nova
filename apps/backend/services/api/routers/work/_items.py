"""Work item routes — task commitments."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from runtime.side_effects import finalize_mutations
from services.planner import work_commands as work_cmd

from ...dependencies import RequestContext, get_request_context
from ...schemas.common import MutationMeta
from ...schemas.work import (
    ConcurrencyRequest,
    CreateTaskRequest,
    TransitionTaskRequest,
    UpdateTaskRequest,
    WorkMutationResponse,
)
from ._support import work_error

router = APIRouter()

_ITEM_ERRORS = (
    work_cmd.WorkNotFoundError,
    work_cmd.WorkConflictError,
    work_cmd.WorkValidationError,
)


@router.post("/items", response_model=WorkMutationResponse, status_code=201)
def post_item(
    body: CreateTaskRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> WorkMutationResponse:
    try:
        item, message, events = work_cmd.create_task(body.model_dump())
    except _ITEM_ERRORS as exc:
        raise work_error(exc) from None
    finalize_mutations(events)
    return WorkMutationResponse(item=item, meta=MutationMeta(message=message))


@router.patch("/items/{item_id}", response_model=WorkMutationResponse)
def patch_item(
    item_id: int,
    body: UpdateTaskRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> WorkMutationResponse:
    patch = body.model_dump(exclude={"updated_at"}, exclude_unset=True)
    try:
        item, message, events = work_cmd.update_task(item_id, body.updated_at, patch)
    except _ITEM_ERRORS as exc:
        raise work_error(exc) from None
    finalize_mutations(events)
    return WorkMutationResponse(item=item, meta=MutationMeta(message=message))


@router.post("/items/{item_id}/transition", response_model=WorkMutationResponse)
def post_transition_item(
    item_id: int,
    body: TransitionTaskRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> WorkMutationResponse:
    try:
        item, message, events = work_cmd.transition_task(item_id, body.updated_at, body.to_status)
    except _ITEM_ERRORS as exc:
        raise work_error(exc) from None
    finalize_mutations(events)
    return WorkMutationResponse(item=item, meta=MutationMeta(message=message))


@router.delete("/items/{item_id}", response_model=WorkMutationResponse)
def delete_item(
    item_id: int,
    body: ConcurrencyRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> WorkMutationResponse:
    try:
        item, message, events = work_cmd.delete_task(item_id, body.updated_at)
    except _ITEM_ERRORS as exc:
        raise work_error(exc) from None
    finalize_mutations(events)
    return WorkMutationResponse(item=item, meta=MutationMeta(message=message))
