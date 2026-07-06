import type { MemoriesListResponse, MemoryResponse } from '@nova/api-contracts'
import type { MemoriesViewModel, MemoryItem } from '@/view-models'

export function mapMemory(row: MemoryResponse): MemoryItem {
  return {
    id: row.id,
    text: row.text,
    sourceType: row.source_type,
    sourceId: row.source_id ?? undefined,
    tier: row.tier,
    importance: row.importance,
    accessCount: row.access_count,
    createdAt: row.created_at,
  }
}

export function mapMemories(response: MemoriesListResponse): MemoriesViewModel {
  return {
    memories: response.memories.map(mapMemory),
    total: response.total,
    limit: response.limit,
    offset: response.offset,
  }
}
