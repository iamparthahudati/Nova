from fastapi import APIRouter, Depends, HTTPException, Query

import memory
from ..dependencies import RequestContext, get_request_context
from ..schemas import (
    GraphEdgeResponse,
    GraphEntityResponse,
    GraphRelatedResponse,
    GraphSnapshotResponse,
    GraphStatsResponse,
)

router = APIRouter(prefix="/graph", tags=["graph"])


def _entity(row: dict) -> GraphEntityResponse:
    return GraphEntityResponse(
        id=row["id"],
        type=row["type"],
        canonical_name=row["canonical_name"],
        attributes=row.get("attributes") or {},
        created_at=row.get("created_at"),
    )


@router.get("", response_model=GraphSnapshotResponse)
def graph_snapshot(
    entity_limit: int = Query(500, ge=1, le=5000),
    edge_limit: int = Query(500, ge=1, le=5000),
    _ctx: RequestContext = Depends(get_request_context),
) -> GraphSnapshotResponse:
    snapshot = memory.list_graph_snapshot(
        entity_limit=entity_limit,
        edge_limit=edge_limit,
    )
    return GraphSnapshotResponse(
        entities=[_entity(e) for e in snapshot["entities"]],
        edges=[GraphEdgeResponse(**e) for e in snapshot["edges"]],
    )


@router.get("/stats", response_model=GraphStatsResponse)
def graph_stats(
    _ctx: RequestContext = Depends(get_request_context),
) -> GraphStatsResponse:
    stats = memory.graph_stats()
    return GraphStatsResponse(**stats)


@router.get("/entities/lookup", response_model=GraphEntityResponse)
def lookup_entity(
    name: str = Query(..., min_length=1),
    type: str | None = Query(None, alias="type"),
    _ctx: RequestContext = Depends(get_request_context),
) -> GraphEntityResponse:
    row = memory.find_entity(name, type)
    if row is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return _entity(row)


@router.get("/entities/{entity_id}/related", response_model=GraphRelatedResponse)
def related_entities(
    entity_id: str,
    depth: int = Query(1, ge=1, le=3),
    relation_type: str | None = Query(None),
    _ctx: RequestContext = Depends(get_request_context),
) -> GraphRelatedResponse:
    entity = memory.get_entity(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    related = memory.related_entities(entity_id, relation_type=relation_type, depth=depth)
    edges = memory.entity_edges(entity_id, relation_type=relation_type)
    return GraphRelatedResponse(
        entity=_entity(entity),
        related=[_entity(r) for r in related],
        edges=[GraphEdgeResponse(**e) for e in edges],
    )
