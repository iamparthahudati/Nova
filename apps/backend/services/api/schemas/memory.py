from typing import Any, Optional

from pydantic import BaseModel, Field


class MemoryResponse(BaseModel):
    id: str
    text: str
    source_type: str
    source_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    tier: str
    importance: float
    access_count: int
    created_at: str
    similarity: Optional[float] = None
    score: Optional[float] = None


class MemoryRecallResponse(BaseModel):
    query: str
    memories: list[MemoryResponse]
