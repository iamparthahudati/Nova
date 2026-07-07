"""Finance routes — dashboard, accounts, credit cards, statements."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from runtime.mutation_builders import (
    build_finance_account_archived,
    build_finance_account_created,
    build_finance_account_restored,
    build_finance_account_updated,
    build_finance_credit_card_created,
    build_finance_credit_card_updated,
    build_finance_statement_paid,
    build_finance_statement_updated,
)
from runtime.side_effects import finalize_mutations
from services.planner import finance_commands as finance_cmd
from services.planner import finance_queries as finance_q

from ...dependencies import RequestContext, get_request_context
from ...schemas.common import MutationMeta
from ...schemas.finance import (
    AccountMutationResponse,
    AccountResponse,
    AccountsResponse,
    CreateAccountRequest,
    CreateCreditCardRequest,
    CreditCardMutationResponse,
    CreditCardResponse,
    CreditCardsResponse,
    FinanceDashboardResponse,
    PayStatementRequest,
    StatementMutationResponse,
    StatementResponse,
    StatementsResponse,
    TransferGroupResponse,
    TransferMutationResponse,
    UpdateAccountRequest,
    UpdateCreditCardRequest,
    UpdateStatementRequest,
)
from ._support import finalize_statement_materializations, finance_error

router = APIRouter()


@router.get("/dashboard", response_model=FinanceDashboardResponse)
def finance_dashboard(
    _ctx: RequestContext = Depends(get_request_context),
) -> FinanceDashboardResponse:
    payload, created = finance_q.get_finance_dashboard()
    finalize_statement_materializations(created)
    return FinanceDashboardResponse(**payload)


@router.get("/accounts", response_model=AccountsResponse)
def list_accounts(
    include_archived: bool = Query(False),
    _ctx: RequestContext = Depends(get_request_context),
) -> AccountsResponse:
    rows = finance_q.list_accounts(include_archived=include_archived)
    return AccountsResponse(accounts=[AccountResponse(**row) for row in rows])


@router.get("/accounts/{account_id}", response_model=dict)
def get_account(
    account_id: int,
    _ctx: RequestContext = Depends(get_request_context),
):
    try:
        return finance_q.get_account(account_id)
    except finance_cmd.AccountNotFoundError as exc:
        raise finance_error(exc) from None


@router.post("/accounts", response_model=AccountMutationResponse, status_code=201)
def post_account(
    body: CreateAccountRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> AccountMutationResponse:
    try:
        row, message = finance_cmd.create_account(
            body.name,
            body.account_type,
            body.opening_balance,
            body.opening_balance_on,
        )
    except finance_cmd.FinanceValidationError as exc:
        raise finance_error(exc) from None
    finalize_mutations([build_finance_account_created(row)])
    return AccountMutationResponse(
        item=AccountResponse(**row),
        meta=MutationMeta(message=message),
    )


@router.patch("/accounts/{account_id}", response_model=AccountMutationResponse)
def patch_account(
    account_id: int,
    body: UpdateAccountRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> AccountMutationResponse:
    try:
        row, message = finance_cmd.update_account(
            account_id,
            name=body.name,
            opening_balance=body.opening_balance,
            opening_balance_on=body.opening_balance_on,
        )
    except (
        finance_cmd.AccountNotFoundError,
        finance_cmd.AccountArchivedError,
        finance_cmd.FinanceValidationError,
    ) as exc:
        raise finance_error(exc) from None
    finalize_mutations([build_finance_account_updated(row)])
    return AccountMutationResponse(
        item=AccountResponse(**row),
        meta=MutationMeta(message=message),
    )


@router.post("/accounts/{account_id}/archive", response_model=AccountMutationResponse)
def post_archive_account(
    account_id: int,
    _ctx: RequestContext = Depends(get_request_context),
) -> AccountMutationResponse:
    try:
        row, message = finance_cmd.archive_account(account_id)
    except (
        finance_cmd.AccountNotFoundError,
        finance_cmd.AccountArchivedError,
    ) as exc:
        raise finance_error(exc) from None
    finalize_mutations([build_finance_account_archived(row)])
    return AccountMutationResponse(
        item=AccountResponse(**row),
        meta=MutationMeta(message=message),
    )


@router.post("/accounts/{account_id}/restore", response_model=AccountMutationResponse)
def post_restore_account(
    account_id: int,
    _ctx: RequestContext = Depends(get_request_context),
) -> AccountMutationResponse:
    try:
        row, message = finance_cmd.restore_account(account_id)
    except (
        finance_cmd.AccountNotFoundError,
        finance_cmd.FinanceValidationError,
    ) as exc:
        raise finance_error(exc) from None
    finalize_mutations([build_finance_account_restored(row)])
    return AccountMutationResponse(
        item=AccountResponse(**row),
        meta=MutationMeta(message=message),
    )


@router.get("/credit-cards", response_model=CreditCardsResponse)
def list_credit_cards(
    _ctx: RequestContext = Depends(get_request_context),
) -> CreditCardsResponse:
    rows, created = finance_q.list_credit_cards()
    finalize_statement_materializations(created)
    return CreditCardsResponse(cards=[CreditCardResponse(**row) for row in rows])


@router.get("/credit-cards/{account_id}", response_model=dict)
def get_credit_card(
    account_id: int,
    _ctx: RequestContext = Depends(get_request_context),
):
    try:
        row, created = finance_q.get_credit_card(account_id)
    except finance_cmd.CreditCardNotFoundError as exc:
        raise finance_error(exc) from None
    finalize_statement_materializations(created)
    return row


@router.post("/credit-cards", response_model=CreditCardMutationResponse, status_code=201)
def post_credit_card(
    body: CreateCreditCardRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> CreditCardMutationResponse:
    try:
        row, message = finance_cmd.create_credit_card(
            body.name,
            body.credit_limit,
            body.statement_day,
            body.due_day_offset,
            body.opening_balance,
            body.opening_balance_on,
            body.network,
            body.last4,
            body.autopay,
        )
    except finance_cmd.FinanceValidationError as exc:
        raise finance_error(exc) from None
    finalize_mutations([build_finance_credit_card_created(row)])
    return CreditCardMutationResponse(
        item=CreditCardResponse(**row),
        meta=MutationMeta(message=message),
    )


@router.patch("/credit-cards/{account_id}", response_model=CreditCardMutationResponse)
def patch_credit_card(
    account_id: int,
    body: UpdateCreditCardRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> CreditCardMutationResponse:
    try:
        row, message = finance_cmd.update_credit_card(
            account_id,
            name=body.name,
            credit_limit=body.credit_limit,
            statement_day=body.statement_day,
            due_day_offset=body.due_day_offset,
            network=body.network,
            last4=body.last4,
            autopay=body.autopay,
        )
    except (
        finance_cmd.CreditCardNotFoundError,
        finance_cmd.FinanceValidationError,
    ) as exc:
        raise finance_error(exc) from None
    finalize_mutations([build_finance_credit_card_updated(row)])
    return CreditCardMutationResponse(
        item=CreditCardResponse(**row),
        meta=MutationMeta(message=message),
    )


@router.get("/statements", response_model=StatementsResponse)
def list_statements(
    account_id: int = Query(...),
    limit: int = Query(24, ge=1, le=100),
    _ctx: RequestContext = Depends(get_request_context),
) -> StatementsResponse:
    rows, created = finance_q.list_statements(account_id, limit)
    finalize_statement_materializations(created)
    return StatementsResponse(statements=[StatementResponse(**row) for row in rows])


@router.get("/statements/{statement_id}", response_model=StatementResponse)
def get_statement(
    statement_id: int,
    _ctx: RequestContext = Depends(get_request_context),
) -> StatementResponse:
    try:
        row, created = finance_q.get_statement(statement_id)
    except finance_cmd.StatementNotFoundError as exc:
        raise finance_error(exc) from None
    finalize_statement_materializations(created)
    return StatementResponse(**row)


@router.patch("/statements/{statement_id}", response_model=StatementMutationResponse)
def patch_statement(
    statement_id: int,
    body: UpdateStatementRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> StatementMutationResponse:
    try:
        row, message = finance_cmd.update_statement(
            statement_id,
            total_due=body.total_due,
            min_due=body.min_due,
        )
    except (
        finance_cmd.StatementNotFoundError,
        finance_cmd.FinanceValidationError,
    ) as exc:
        raise finance_error(exc) from None
    finalize_mutations([build_finance_statement_updated(row)])
    return StatementMutationResponse(
        item=StatementResponse(**row),
        meta=MutationMeta(message=message),
    )


@router.post(
    "/statements/{statement_id}/pay",
    response_model=TransferMutationResponse,
    status_code=201,
)
def post_pay_statement(
    statement_id: int,
    body: PayStatementRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> TransferMutationResponse:
    try:
        entity, message, _paid_statement_id = finance_cmd.pay_statement(
            statement_id,
            body.from_account_id,
            payment_mode=body.payment_mode,
            amount=body.amount,
            note=body.note,
            confirm_overpayment=body.confirm_overpayment,
        )
    except (
        finance_cmd.StatementNotFoundError,
        finance_cmd.AccountNotFoundError,
        finance_cmd.AccountArchivedError,
        finance_cmd.PaymentConfirmationRequiredError,
        finance_cmd.FinanceValidationError,
    ) as exc:
        raise finance_error(exc) from None
    finalize_mutations([build_finance_statement_paid(entity)])
    return TransferMutationResponse(
        item=TransferGroupResponse(**entity),
        meta=MutationMeta(message=message),
    )
