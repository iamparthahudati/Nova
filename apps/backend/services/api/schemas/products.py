from typing import Optional

from pydantic import BaseModel


class ProductResponse(BaseModel):
    id: int
    name: str
    store: Optional[str] = None
    status: str
    price: Optional[float] = None
    sold_count: int
    created_at: str


class ProductsResponse(BaseModel):
    products: list[ProductResponse]
