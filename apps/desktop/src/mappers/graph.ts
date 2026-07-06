import type { GraphEdgeResponse, GraphEntityResponse, GraphSnapshotResponse } from '@nova/api-contracts'
import type { GraphEdge, GraphEntity, GraphViewModel } from '@/view-models'

export function mapGraphEntity(row: GraphEntityResponse): GraphEntity {
  return {
    id: row.id,
    type: row.type,
    canonicalName: row.canonical_name,
    attributes: row.attributes,
  }
}

export function mapGraphEdge(row: GraphEdgeResponse): GraphEdge {
  return {
    id: row.id,
    fromEntityId: row.from_entity_id,
    toEntityId: row.to_entity_id,
    relationType: row.relation_type,
    weight: row.weight,
    sourceMemoryId: row.source_memory_id ?? undefined,
  }
}

export function mapGraph(response: GraphSnapshotResponse): GraphViewModel {
  return {
    entities: response.entities.map(mapGraphEntity),
    edges: response.edges.map(mapGraphEdge),
  }
}
