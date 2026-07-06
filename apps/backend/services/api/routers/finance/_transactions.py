"""Finance routes — transactions, transfers, and card payments."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from runtime.mutation_builders import (
    build_finance_card_payment_created,
    build_finance_cashback_earned,
    build_finance_transaction_created,
    build_finance_transaction_deleted,
    build_finance_transaction_updated,
    build_finance_transfer_created,
)
from runtime.side_effects import finalize_mutations
from services.planner import finance_commands as finance_cmd
from services.planner import finance_queries as finance_q

from ...dependencies import RequestContext, get_request_context
from ...schemas.common import MutationMeta
from ...schemas.finance import (
    CreateCardPaymentRequest,
    CreateTransactionRequest,
    CreateTransferRequest,
    TransactionMutationResponse,
    TransactionResponse,
    TransactionsResponse,
    TransferGroupResponse,
    TransferMutationResponse,
    UpdateTransactionRequest,
)
from ._support import finance_error

router = APIRouter()


@router.get("/transactions", response_model=TransactionsResponse)
def list_transactions(
    account_id: int | None = Query(None),
    category_id: int | None = Query(None),
    merchant_id: int | None = Query(None),
    direction: str | None = Query(None),
    kind: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _ctx: RequestContext = Depends(get_request_context),
) -> TransactionsResponse:
    rows, total = finance_q.list_transactions(
        account_id=account_id,
        category_id=category_id,
        merchant_id=merchant_id,
        direction=direction,
        kind=kind,
        start_date=start_date,
        end_date=end_date,
        search=search,
        limit=limit,
        offset=offset,
    )
    return TransactionsResponse(
        transactions=[TransactionResponse(**row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/transactions", response_model=TransactionMutationResponse, status_code=201)
def post_transaction(
    body: CreateTransactionRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> TransactionMutationResponse:
    try:
        row, message, extras = finance_cmd.create_transaction(
            body.account_id,
            body.kind,
            body.amount,
            body.occurred_on,
            body.category_id,
            body.merchant_id,
            body.note,
            body.direction,
        )
    except (
        finance_cmd.AccountNotFoundError,
        finance_cmd.AccountArchivedError,
        finance_cmd.FinanceValidationError,
    ) as exc:
        raise finance_error(exc) from None
    events = [build_finance_transaction_created(row)]
    events.extend(build_finance_cashback_earned(extra) for extra in extras)
    finalize_mutations(events)
    return TransactionMutationResponse(
        item=TransactionResponse(**row),
        meta=MutationMeta(message=message),
    )


@router.patch("/transactions/{transaction_id}", response_model=TransactionMutationResponse)
def patch_transaction(
    transaction_id: int,
    body: UpdateTransactionRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> TransactionMutationResponse:
    try:
        row, message = finance_cmd.update_transaction(
            transaction_id,
            amount=body.amount,
            category_id=body.category_id,
            merchant_id=body.merchant_id,
            note=body.note,
            occurred_on=body.occurred_on,
        )
    except (
        finance_cmd.TransactionNotFoundError,
        finance_cmd.FinanceValidationError,
    ) as exc:
        raise finance_error(exc) from None
    finalize_mutations([build_finance_transaction_updated(row)])
    return TransactionMutationResponse(
        item=TransactionResponse(**row),
        meta=MutationMeta(message=message),
    )


@router.delete("/transactions/{transaction_id}", response_model=TransactionMutationResponse)
def delete_transaction(
    transaction_id: int,
    _ctx: RequestContext = Depends(get_request_context),
) -> TransactionMutationResponse:
    try:
        row, message = finance_cmd.delete_transaction(transaction_id)
    except finance_cmd.TransactionNotFoundError as exc:
        raise finance_error(exc) from None
    finalize_mutations([build_finance_transaction_deleted(row)])
    return TransactionMutationResponse(
        item=TransactionResponse(**row),
        meta=MutationMeta(message=message),
    )


@router.post("/transfers", response_model=TransferMutationResponse, status_code=201)
def post_transfer(
    body: CreateTransferRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> TransferMutationResponse:
    try:
        entity, message = finance_cmd.create_transfer(
            body.from_account_id,
            body.to_account_id,
            body.amount,
            body.occurred_on,
            body.note,
        )
    except (
        finance_cmd.AccountNotFoundError,
        finance_cmd.AccountArchivedError,
        finance_cmd.FinanceValidationError,
    ) as exc:
        raise finance_error(exc) from None
    finalize_mutations([build_finance_transfer_created(entity)])
    return TransferMutationResponse(
        item=TransferGroupResponse(**entity),
        meta=MutationMeta(message=message),
    )


@router.delete("/transfers/{transfer_group_id}", response_model=TransactionsResponse)
def delete_transfer(
    transfer_group_id: str,
    _ctx: RequestContext = Depends(get_request_context),
) -> TransactionsResponse:
    try:
        legs, message = finance_cmd.delete_transfer(transfer_group_id)
    except (
        finance_cmd.TransferInvariantError,
        finance_cmd.FinanceValidationError,
    ) as exc:
        raise finance_error(exc) from None
    finalize_mutations([build_finance_transaction_deleted(leg) for leg in legs])
    return TransactionsResponse(
        transactions=[TransactionResponse(**leg) for leg in legs],
        total=len(legs),
        limit=len(legs),
        offset=0,
    )


@router.post("/payments/card", response_model=TransferMutationResponse, status_code=201)
def post_card_payment(
    body: CreateCardPaymentRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> TransferMutationResponse:
    try:
        entity, message = finance_cmd.create_card_payment(
            body.from_account_id,
            body.card_account_id,
            body.amount,
            body.occurred_on,
            body.statement_id,
            body.note,
            body.confirm_overpayment,
        )
    except (
        finance_cmd.AccountNotFoundError,
        finance_cmd.AccountArchivedError,
        finance_cmd.StatementNotFoundError,
        finance_cmd.PaymentConfirmationRequiredError,
        finance_cmd.FinanceValidationError,
    ) as exc:
        raise finance_error(exc) from None
    finalize_mutations([build_finance_card_payment_created(entity)])
    return TransferMutationResponse(
        item=TransferGroupResponse(**entity),
        meta=MutationMeta(message=message),
    )


@router.delete("/payments/card/{transfer_group_id}", response_model=TransactionsResponse)
def delete_card_payment(
    transfer_group_id: str,
    _ctx: RequestContext = Depends(get_request_context),
) -> TransactionsResponse:
    try:
        legs, message = finance_cmd.delete_card_payment(transfer_group_id)
    except (
        finance_cmd.TransferInvariantError,
        finance_cmd.FinanceValidationError,
    ) as exc:
        raise finance_error(exc) from None
    finalize_mutations([build_finance_transaction_deleted(leg) for leg in legs])
    return TransactionsResponse(
        transactions=[TransactionResponse(**leg) for leg in legs],
        total=len(legs),
        limit=len(legs),
        offset=0,
    )
