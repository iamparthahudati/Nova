"""Shared helpers for finance REST routes."""

from __future__ import annotations

from fastapi import HTTPException

from runtime.mutation_builders import build_finance_statement_created
from runtime.side_effects import finalize_mutations
from services.planner import finance_commands as finance_cmd


def finance_error(exc: Exception) -> HTTPException:
    if isinstance(
        exc,
        (
            finance_cmd.AccountNotFoundError,
            finance_cmd.CreditCardNotFoundError,
            finance_cmd.StatementNotFoundError,
            finance_cmd.TransactionNotFoundError,
            finance_cmd.CategoryNotFoundError,
            finance_cmd.MerchantNotFoundError,
        ),
    ):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, finance_cmd.AccountArchivedError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, finance_cmd.PaymentConfirmationRequiredError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(
        exc,
        (
            finance_cmd.FinanceValidationError,
            finance_cmd.TransferInvariantError,
        ),
    ):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=400, detail=str(exc))


def finalize_statement_materializations(created_rows: list[dict]) -> None:
    if not created_rows:
        return
    finalize_mutations([build_finance_statement_created(row) for row in created_rows])
