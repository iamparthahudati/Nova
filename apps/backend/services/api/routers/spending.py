from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

import memory
from runtime.mutation_builders import build_spending_logged
from runtime.side_effects import finalize_mutations
from services import planner
from services.planner.api_commands import SpendingTypeInvalidError, log_spending

from ..dependencies import RequestContext, get_request_context
from ..schemas import (
    LogSpendingRequest,
    MutationMeta,
    SpendingMutationResponse,
    SpendingResponse,
    SpendingSummaryResponse,
    SpendingTransactionResponse,
)

router = APIRouter(prefix="/spending", tags=["spending"])


@router.get("", response_model=SpendingResponse)
def get_spending(
    transaction_limit: int = Query(30, ge=1, le=200, alias="limit"),
    _ctx: RequestContext = Depends(get_request_context),
) -> SpendingResponse:
    month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")
    earned, spent = memory.get_money_totals_between(month_start, today)
    transactions = memory.get_recent_money(transaction_limit)
    return SpendingResponse(
        earned_month=earned,
        spent_month=spent,
        transactions=[SpendingTransactionResponse(**row) for row in transactions],
    )


@router.post("", response_model=SpendingMutationResponse, status_code=201)
def post_spending(
    body: LogSpendingRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> SpendingMutationResponse:
    try:
        row, message = log_spending(body.type, body.amount, body.note or "")
    except SpendingTypeInvalidError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

    finalize_mutations([build_spending_logged(row)])
    return SpendingMutationResponse(
        item=SpendingTransactionResponse(**row),
        meta=MutationMeta(message=message),
    )


@router.get("/summary", response_model=SpendingSummaryResponse)
def spending_summary(
    period: str = Query("this week"),
    _ctx: RequestContext = Depends(get_request_context),
) -> SpendingSummaryResponse:
    text = planner.get_spending_summary(period)
    month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")
    earned, spent = memory.get_money_totals_between(month_start, today)
    return SpendingSummaryResponse(
        period=period,
        earned=earned,
        spent=spent,
        summary=text,
    )
