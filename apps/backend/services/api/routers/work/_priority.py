"""Priority + briefing routes — deterministic read models and policy tuning."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from runtime.side_effects import finalize_mutations
from services.planner import work_commands as work_cmd
from services.planner import work_queries as work_q

from ...dependencies import RequestContext, get_request_context
from ...schemas.common import MutationMeta
from ...schemas.work import ReweightPolicyRequest, WorkMutationResponse
from ._support import work_error

router = APIRouter()


@router.get("/priority/queue", response_model=dict)
def priority_queue(
    limit: int = Query(0, ge=0, le=200),
    _ctx: RequestContext = Depends(get_request_context),
) -> dict:
    return work_q.get_priority_queue(limit)


@router.get("/briefing/today", response_model=dict)
def briefing_today(_ctx: RequestContext = Depends(get_request_context)) -> dict:
    return work_q.get_briefing()


@router.get("/priority/policy", response_model=dict)
def priority_policy(_ctx: RequestContext = Depends(get_request_context)) -> dict:
    return work_q.get_priority_policy()


@router.patch("/priority/policy", response_model=WorkMutationResponse)
def patch_priority_policy(
    body: ReweightPolicyRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> WorkMutationResponse:
    try:
        item, message, events = work_cmd.reweight_priority(
            body.deadline_weight, body.decay_weight, body.updated_at
        )
    except (work_cmd.WorkConflictError, work_cmd.WorkValidationError) as exc:
        raise work_error(exc) from None
    finalize_mutations(events)
    return WorkMutationResponse(item=item, meta=MutationMeta(message=message))
