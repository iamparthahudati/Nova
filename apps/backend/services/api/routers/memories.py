from typing import Literal

from fastapi import APIRouter, Depends, Query

import memory

from ..dependencies import RequestContext, get_request_context
from ..schemas import MemoriesListResponse, MemoriesStatsResponse, MemoryResponse

router = APIRouter(prefix="/memories", tags=["memories"])

SortField = Literal["created_at", "importance", "access_count", "tier"]
SortOrder = Literal["asc", "desc"]


@router.get("", response_model=MemoriesListResponse)
def list_memories(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    tier: str | None = Query(None),
    source_type: str | None = Query(None),
    search: str | None = Query(None, description="Substring text search"),
    sort: SortField = Query("created_at"),
    order: SortOrder = Query("desc"),
    _ctx: RequestContext = Depends(get_request_context),
) -> MemoriesListResponse:
    rows = memory.list_memories(
        limit=limit,
        offset=offset,
        tier=tier,
        source_type=source_type,
        search=search,
        sort=sort,
        order=order,
    )
    total = memory.count_active_memories(
        tier=tier,
        source_type=source_type,
        search=search,
    )
    return MemoriesListResponse(
        memories=[MemoryResponse(**row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/stats", response_model=MemoriesStatsResponse)
def memory_stats(
    _ctx: RequestContext = Depends(get_request_context),
) -> MemoriesStatsResponse:
    return MemoriesStatsResponse(
        count=memory.count_active_memories(),
        by_tier=memory.count_active_memories_by_tier(),
    )
