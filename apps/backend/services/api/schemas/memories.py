from typing import Optional

from pydantic import BaseModel, Field

from .memory import MemoryResponse


class MemoriesListResponse(BaseModel):
    memories: list[MemoryResponse] = Field(default_factory=list)
    total: int
    limit: int
    offset: int


class MemoriesStatsResponse(BaseModel):
    count: int
    by_tier: dict[str, int] = Field(default_factory=dict)
