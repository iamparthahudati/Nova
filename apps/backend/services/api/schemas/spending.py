from typing import Literal, Optional

from pydantic import BaseModel, Field

from .common import MutationMeta


class SpendingTransactionResponse(BaseModel):
    id: int
    type: str
    amount: float
    note: Optional[str] = None
    created_at: str


class SpendingSummaryResponse(BaseModel):
    period: str
    earned: float
    spent: float
    summary: str


class SpendingResponse(BaseModel):
    earned_month: float
    spent_month: float
    transactions: list[SpendingTransactionResponse]


class LogSpendingRequest(BaseModel):
    type: Literal["earned", "spent"]
    amount: float = Field(..., gt=0)
    note: Optional[str] = None


class SpendingMutationResponse(BaseModel):
    item: SpendingTransactionResponse
    meta: MutationMeta
