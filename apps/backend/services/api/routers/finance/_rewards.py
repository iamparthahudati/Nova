"""Finance routes — reward programs and cashback."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from services.planner import finance_rewards_queries as rewards_q

from ...dependencies import RequestContext, get_request_context
from ...schemas.finance import (
    RewardLedgerResponse,
    RewardProgramDetailResponse,
    RewardProgramResponse,
    RewardProgramsResponse,
    RewardsOverviewResponse,
)

router = APIRouter()


@router.get("/rewards/overview", response_model=RewardsOverviewResponse)
def get_rewards_overview(
    _ctx: RequestContext = Depends(get_request_context),
) -> RewardsOverviewResponse:
    return RewardsOverviewResponse(**rewards_q.get_rewards_overview())


@router.get("/rewards/programs", response_model=RewardProgramsResponse)
def list_reward_programs(
    account_id: int | None = Query(None),
    _ctx: RequestContext = Depends(get_request_context),
) -> RewardProgramsResponse:
    rows = rewards_q.list_reward_programs(account_id)
    return RewardProgramsResponse(programs=[RewardProgramResponse(**row) for row in rows])


@router.get("/rewards/programs/{program_id}", response_model=RewardProgramDetailResponse)
def get_reward_program_detail(
    program_id: int,
    _ctx: RequestContext = Depends(get_request_context),
) -> RewardProgramDetailResponse:
    return RewardProgramDetailResponse(**rewards_q.get_reward_program_detail(program_id))


@router.get("/rewards/programs/{program_id}/ledger", response_model=RewardLedgerResponse)
def get_reward_ledger(
    program_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _ctx: RequestContext = Depends(get_request_context),
) -> RewardLedgerResponse:
    return RewardLedgerResponse(**rewards_q.get_reward_ledger(program_id, limit, offset))
