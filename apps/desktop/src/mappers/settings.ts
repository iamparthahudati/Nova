import type { ProfileObservationResponse, SettingsResponse } from '@nova/api-contracts'
import type { ProfileObservation, SettingsViewModel } from '@/view-models'

function observationKey(row: ProfileObservationResponse): string {
  return `${row.category}:${row.observation}`
}

export function mapProfileObservation(row: ProfileObservationResponse): ProfileObservation {
  return {
    id: observationKey(row),
    observation: row.observation,
    category: row.category,
    confidence: row.confidence,
  }
}

export function mapSettings(response: SettingsResponse): SettingsViewModel {
  return {
    assistantName: response.assistant_name,
    voiceName: response.voice_name,
    briefingTime: response.briefing_time,
    eveningWrapupTime: response.evening_wrapup_time ?? undefined,
    claudeModel: response.claude_model,
    semanticMemoryEnabled: response.semantic_memory_enabled,
    entityExtractionEnabled: response.entity_extraction_enabled,
    graphContextEnabled: response.graph_context_enabled,
    observations: response.observations.map(mapProfileObservation),
  }
}
