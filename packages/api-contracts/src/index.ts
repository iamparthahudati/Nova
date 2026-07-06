/**
 * Canonical HTTP API contracts for Nova backend ↔ clients.
 * Keep in sync with apps/backend/services/api/schemas/.
 */

export interface MutationMeta {
  message: string
}

export interface EntityMutationResponse<T> {
  item: T
  meta: MutationMeta
}

export interface CreateTaskRequest {
  text: string
  due?: string | null
}

export interface TaskMutationResponse {
  item: TaskResponse
  meta: MutationMeta
}

export interface ErrorDetail {
  code: string
  message: string
  details?: Record<string, unknown>
}

export interface ErrorResponse {
  error: ErrorDetail
}

export interface HealthResponse {
  status: string
  service: string
  version: string
}

export interface ChatRequest {
  message: string
  conversation_id?: string
}

export interface ToolCallRecord {
  name: string
  args: Record<string, unknown>
  result: string
}

export interface ChatResponse {
  reply: string
  conversation_id: string
  tools_called: ToolCallRecord[]
  error?: string | null
}

export interface TaskResponse {
  id: number
  text: string
  status: string
  created_at: string
  due?: string | null
}

export interface TasksResponse {
  tasks: TaskResponse[]
}

export interface ReminderResponse {
  id: number
  text: string
  remind_date: string
  remind_time?: string | null
  created_at: string
}

export interface RemindersResponse {
  reminders: ReminderResponse[]
}

export interface CreateReminderRequest {
  text: string
  remind_date: string
  remind_time?: string | null
}

export interface ReminderMutationResponse {
  item: ReminderResponse
  meta: MutationMeta
}

export interface MemoryResponse {
  id: string
  text: string
  source_type: string
  source_id?: string | null
  metadata: Record<string, unknown>
  tier: string
  importance: number
  access_count: number
  created_at: string
  similarity?: number | null
  score?: number | null
}

export interface MemoryRecallResponse {
  query: string
  memories: MemoryResponse[]
}

export interface CalendarEventResponse {
  title: string
  time: string
}

export interface CalendarResponse {
  date: string
  events: CalendarEventResponse[]
  unavailable: boolean
}

export interface GraphEntityResponse {
  id: string
  type: string
  canonical_name: string
  attributes: Record<string, unknown>
  created_at?: string | null
}

export interface GraphEdgeResponse {
  id: string
  from_entity_id: string
  to_entity_id: string
  relation_type: string
  weight: number
  source_memory_id?: string | null
  created_at?: string | null
}

export interface GraphRelatedResponse {
  entity: GraphEntityResponse
  related: GraphEntityResponse[]
  edges: GraphEdgeResponse[]
}

export interface GraphSnapshotResponse {
  entities: GraphEntityResponse[]
  edges: GraphEdgeResponse[]
}

export interface GraphStatsResponse {
  entity_count: number
  edge_count: number
  entities_by_type: Record<string, number>
  edges_by_relation: Record<string, number>
}

export interface MemoriesListResponse {
  memories: MemoryResponse[]
  total: number
  limit: number
  offset: number
}

export interface MemoriesStatsResponse {
  count: number
  by_tier: Record<string, number>
}

export interface HomeCard {
  id: string
  label: string
  value: string
  icon?: string | null
}

export interface HomePanelItem {
  id: string
  primary: string
  secondary?: string | null
  meta?: Record<string, unknown>
}

export interface HomePanel {
  id: string
  title: string
  items: HomePanelItem[]
}

export interface HomeResponse {
  cards: HomeCard[]
  panels: HomePanel[]
}

export type SubsystemStatus = 'ok' | 'degraded' | 'unavailable'

export interface SubsystemDiagnostic {
  name: string
  status: SubsystemStatus
  message?: string | null
}

export interface SystemStatusResponse {
  status: SubsystemStatus
  version: string
  subsystems: SubsystemDiagnostic[]
}

export interface SpendingTransactionResponse {
  id: number
  type: string
  amount: number
  note?: string | null
  created_at: string
}

export interface SpendingSummaryResponse {
  period: string
  earned: number
  spent: number
  summary: string
}

export interface SpendingResponse {
  earned_month: number
  spent_month: number
  transactions: SpendingTransactionResponse[]
}

export interface LogSpendingRequest {
  type: 'earned' | 'spent'
  amount: number
  note?: string | null
}

export interface SpendingMutationResponse {
  item: SpendingTransactionResponse
  meta: MutationMeta
}

export interface ProductResponse {
  id: number
  name: string
  store?: string | null
  status: string
  price?: number | null
  sold_count: number
  created_at: string
}

export interface ProductsResponse {
  products: ProductResponse[]
}

export interface ProfileObservationResponse {
  observation: string
  category: string
  confidence: number
}

export interface SettingsResponse {
  assistant_name: string
  voice_name: string
  briefing_time: string
  evening_wrapup_time?: string | null
  claude_model: string
  semantic_memory_enabled: boolean
  entity_extraction_enabled: boolean
  graph_context_enabled: boolean
  observations: ProfileObservationResponse[]
}

/** WebSocket envelope: { event: string, data: Record<string, unknown> } */
export interface WebSocketEvent {
  event: string
  data: Record<string, unknown>
}

export type ChatWebSocketEvent =
  | 'chat.started'
  | 'chat.routing'
  | 'chat.tool_called'
  | 'chat.reply'
  | 'chat.finished'
  | 'chat.error'

export type EventsWebSocketEvent =
  | 'api.started'
  | 'task.created'
  | 'task.updated'
  | 'spending.logged'
  | 'progress.logged'
  | 'product.created'
  | 'product.updated'
  | 'calendar.updated'
  | 'reminder.created'
  | 'memory.created'
  | 'habit.logged'
  | 'graph.updated'
  | 'reminder.triggered'
  | 'pomodoro.completed'
  | 'reflection.completed'
  | 'entity_extraction.completed'
