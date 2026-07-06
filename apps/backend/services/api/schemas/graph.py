from typing import Any, Optional

from pydantic import BaseModel, Field


class GraphEntityResponse(BaseModel):
    id: str
    type: str
    canonical_name: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None


class GraphEdgeResponse(BaseModel):
    id: str
    from_entity_id: str
    to_entity_id: str
    relation_type: str
    weight: float
    source_memory_id: Optional[str] = None
    created_at: Optional[str] = None


class GraphRelatedResponse(BaseModel):
    entity: GraphEntityResponse
    related: list[GraphEntityResponse]
    edges: list[GraphEdgeResponse] = Field(default_factory=list)


class GraphSnapshotResponse(BaseModel):
    entities: list[GraphEntityResponse] = Field(default_factory=list)
    edges: list[GraphEdgeResponse] = Field(default_factory=list)


class GraphStatsResponse(BaseModel):
    entity_count: int
    edge_count: int
    entities_by_type: dict[str, int] = Field(default_factory=dict)
    edges_by_relation: dict[str, int] = Field(default_factory=dict)
