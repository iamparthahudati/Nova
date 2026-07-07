"""Project routes — holdings and their work items."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from runtime.side_effects import finalize_mutations
from services.planner import work_commands as work_cmd
from services.planner import work_queries as work_q

from ...dependencies import RequestContext, get_request_context
from ...schemas.common import MutationMeta
from ...schemas.work import (
    ConcurrencyRequest,
    CreateProjectRequest,
    UpdateProjectRequest,
    WorkMutationResponse,
)
from ._support import work_error

router = APIRouter()


@router.get("/projects", response_model=list)
def list_projects(_ctx: RequestContext = Depends(get_request_context)) -> list:
    return work_q.list_projects()


@router.post("/projects", response_model=WorkMutationResponse, status_code=201)
def post_project(
    body: CreateProjectRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> WorkMutationResponse:
    try:
        item, message, events = work_cmd.create_project(
            body.name, body.objective, body.planned_start_on, body.planned_end_on
        )
    except work_cmd.WorkValidationError as exc:
        raise work_error(exc) from None
    finalize_mutations(events)
    return WorkMutationResponse(item=item, meta=MutationMeta(message=message))


@router.patch("/projects/{project_id}", response_model=WorkMutationResponse)
def patch_project(
    project_id: int,
    body: UpdateProjectRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> WorkMutationResponse:
    patch = body.model_dump(exclude={"updated_at"}, exclude_unset=True)
    try:
        item, message, events = work_cmd.update_project(project_id, body.updated_at, patch)
    except (
        work_cmd.WorkNotFoundError,
        work_cmd.WorkConflictError,
        work_cmd.WorkValidationError,
    ) as exc:
        raise work_error(exc) from None
    finalize_mutations(events)
    return WorkMutationResponse(item=item, meta=MutationMeta(message=message))


@router.post("/projects/{project_id}/archive", response_model=WorkMutationResponse)
def post_archive_project(
    project_id: int,
    body: ConcurrencyRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> WorkMutationResponse:
    try:
        item, message, events = work_cmd.archive_project(project_id, body.updated_at)
    except (work_cmd.WorkNotFoundError, work_cmd.WorkConflictError) as exc:
        raise work_error(exc) from None
    finalize_mutations(events)
    return WorkMutationResponse(item=item, meta=MutationMeta(message=message))


@router.post("/projects/{project_id}/complete", response_model=WorkMutationResponse)
def post_complete_project(
    project_id: int,
    body: ConcurrencyRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> WorkMutationResponse:
    try:
        item, message, events = work_cmd.complete_project(project_id, body.updated_at)
    except (work_cmd.WorkNotFoundError, work_cmd.WorkConflictError) as exc:
        raise work_error(exc) from None
    finalize_mutations(events)
    return WorkMutationResponse(item=item, meta=MutationMeta(message=message))


@router.get("/projects/{project_id}/items", response_model=list)
def list_project_items(
    project_id: int,
    _ctx: RequestContext = Depends(get_request_context),
) -> list:
    return work_q.list_project_items(project_id)
