"""Finance routes — cashback product reads."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from services.planner import finance_cashback_queries as cashback_q

from ...dependencies import RequestContext, get_request_context
from ...schemas.finance import (
    CashbackActivityResponse,
    CashbackRuleDetailResponse,
    CashbackSummaryResponse,
)

router = APIRouter()


@router.get("/cashback", response_model=CashbackSummaryResponse)
def get_cashback_summary(
    _ctx: RequestContext = Depends(get_request_context),
) -> CashbackSummaryResponse:
    return CashbackSummaryResponse(**cashback_q.get_cashback_summary())


@router.get("/cashback/activity", response_model=CashbackActivityResponse)
def get_cashback_activity(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _ctx: RequestContext = Depends(get_request_context),
) -> CashbackActivityResponse:
    return CashbackActivityResponse(**cashback_q.get_cashback_activity(limit, offset))


@router.get("/cashback/rules/{rule_id}", response_model=CashbackRuleDetailResponse)
def get_cashback_rule_detail(
    rule_id: int,
    _ctx: RequestContext = Depends(get_request_context),
) -> CashbackRuleDetailResponse:
    try:
        return CashbackRuleDetailResponse(**cashback_q.get_cashback_rule_detail(rule_id))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
