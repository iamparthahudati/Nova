from fastapi import APIRouter, Depends

import memory
from ..dependencies import RequestContext, get_request_context
from ..schemas import ProductResponse, ProductsResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductsResponse)
def list_products(
    _ctx: RequestContext = Depends(get_request_context),
) -> ProductsResponse:
    rows = memory.get_products()
    return ProductsResponse(products=[ProductResponse(**row) for row in rows])
