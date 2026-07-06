from fastapi import APIRouter, Depends, Query

import memory

from ..dependencies import RequestContext, get_request_context
from ..schemas import MemoryRecallResponse, MemoryResponse

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/recall", response_model=MemoryRecallResponse)
def recall_memories(
    q: str = Query(..., min_length=1, description="Semantic search query"),
    k: int = Query(5, ge=1, le=50),
    source_type: str | None = Query(None),
    _ctx: RequestContext = Depends(get_request_context),
) -> MemoryRecallResponse:
    rows = memory.recall(q, k=k, source_type=source_type)
    return MemoryRecallResponse(
        query=q,
        memories=[MemoryResponse(**row) for row in rows],
    )
