"""Finance routes — categories and merchants."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from runtime.mutation_builders import (
    build_finance_category_created,
    build_finance_category_deleted,
    build_finance_category_updated,
    build_finance_merchant_created,
    build_finance_merchant_deleted,
    build_finance_merchant_updated,
)
from runtime.side_effects import finalize_mutations
from services.planner import finance_commands as finance_cmd
from services.planner import finance_queries as finance_q

from ...dependencies import RequestContext, get_request_context
from ...schemas.common import MutationMeta
from ...schemas.finance import (
    CategoriesResponse,
    CategoryMutationResponse,
    CategoryResponse,
    CreateCategoryRequest,
    CreateMerchantRequest,
    MerchantMutationResponse,
    MerchantResponse,
    MerchantsResponse,
    UpdateCategoryRequest,
    UpdateMerchantRequest,
)
from ._support import finance_error

router = APIRouter()


@router.get("/categories", response_model=CategoriesResponse)
def list_categories(
    _ctx: RequestContext = Depends(get_request_context),
) -> CategoriesResponse:
    rows = finance_q.list_categories()
    return CategoriesResponse(categories=[CategoryResponse(**row) for row in rows])


@router.post("/categories", response_model=CategoryMutationResponse, status_code=201)
def post_category(
    body: CreateCategoryRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> CategoryMutationResponse:
    try:
        row, message = finance_cmd.create_category(body.name)
    except finance_cmd.FinanceValidationError as exc:
        raise finance_error(exc) from None
    finalize_mutations([build_finance_category_created(row)])
    return CategoryMutationResponse(
        item=CategoryResponse(**row),
        meta=MutationMeta(message=message),
    )


@router.patch("/categories/{category_id}", response_model=CategoryMutationResponse)
def patch_category(
    category_id: int,
    body: UpdateCategoryRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> CategoryMutationResponse:
    try:
        row, message = finance_cmd.update_category(category_id, body.name)
    except (
        finance_cmd.CategoryNotFoundError,
        finance_cmd.FinanceValidationError,
    ) as exc:
        raise finance_error(exc) from None
    finalize_mutations([build_finance_category_updated(row)])
    return CategoryMutationResponse(
        item=CategoryResponse(**row),
        meta=MutationMeta(message=message),
    )


@router.delete("/categories/{category_id}", response_model=CategoryMutationResponse)
def delete_category(
    category_id: int,
    _ctx: RequestContext = Depends(get_request_context),
) -> CategoryMutationResponse:
    try:
        row, message = finance_cmd.delete_category(category_id)
    except finance_cmd.CategoryNotFoundError as exc:
        raise finance_error(exc) from None
    finalize_mutations([build_finance_category_deleted(row)])
    return CategoryMutationResponse(
        item=CategoryResponse(**row),
        meta=MutationMeta(message=message),
    )


@router.get("/merchants", response_model=MerchantsResponse)
def list_merchants(
    _ctx: RequestContext = Depends(get_request_context),
) -> MerchantsResponse:
    rows = finance_q.list_merchants()
    return MerchantsResponse(merchants=[MerchantResponse(**row) for row in rows])


@router.post("/merchants", response_model=MerchantMutationResponse, status_code=201)
def post_merchant(
    body: CreateMerchantRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> MerchantMutationResponse:
    try:
        row, message = finance_cmd.create_merchant(body.name)
    except finance_cmd.FinanceValidationError as exc:
        raise finance_error(exc) from None
    finalize_mutations([build_finance_merchant_created(row)])
    return MerchantMutationResponse(
        item=MerchantResponse(**row),
        meta=MutationMeta(message=message),
    )


@router.patch("/merchants/{merchant_id}", response_model=MerchantMutationResponse)
def patch_merchant(
    merchant_id: int,
    body: UpdateMerchantRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> MerchantMutationResponse:
    try:
        row, message = finance_cmd.update_merchant(merchant_id, body.name)
    except (
        finance_cmd.MerchantNotFoundError,
        finance_cmd.FinanceValidationError,
    ) as exc:
        raise finance_error(exc) from None
    finalize_mutations([build_finance_merchant_updated(row)])
    return MerchantMutationResponse(
        item=MerchantResponse(**row),
        meta=MutationMeta(message=message),
    )


@router.delete("/merchants/{merchant_id}", response_model=MerchantMutationResponse)
def delete_merchant(
    merchant_id: int,
    _ctx: RequestContext = Depends(get_request_context),
) -> MerchantMutationResponse:
    try:
        row, message = finance_cmd.delete_merchant(merchant_id)
    except finance_cmd.MerchantNotFoundError as exc:
        raise finance_error(exc) from None
    finalize_mutations([build_finance_merchant_deleted(row)])
    return MerchantMutationResponse(
        item=MerchantResponse(**row),
        meta=MutationMeta(message=message),
    )
