"""Finance routes — reward programs and cashback."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from services.planner import finance_queries as finance_q

from ...dependencies import RequestContext, get_request_context
from ...schemas.finance import (
    CashbackSummaryResponse,
    RewardLedgerResponse,
    RewardProgramResponse,
    RewardProgramsResponse,
)

router = APIRouter()


@router.get("/rewards/programs", response_model=RewardProgramsResponse)
def list_reward_programs(
    account_id: int | None = Query(None),
    _ctx: RequestContext = Depends(get_request_context),
) -> RewardProgramsResponse:
    rows = finance_q.list_reward_programs(account_id)
    return RewardProgramsResponse(programs=[RewardProgramResponse(**row) for row in rows])


@router.get("/rewards/programs/{program_id}/ledger", response_model=RewardLedgerResponse)
def get_reward_ledger(
    program_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _ctx: RequestContext = Depends(get_request_context),
) -> RewardLedgerResponse:
    return RewardLedgerResponse(**finance_q.get_reward_ledger(program_id, limit, offset))


@router.get("/cashback", response_model=CashbackSummaryResponse)
def get_cashback_summary(
    _ctx: RequestContext = Depends(get_request_context),
) -> CashbackSummaryResponse:
    return CashbackSummaryResponse(**finance_q.get_cashback_summary())
