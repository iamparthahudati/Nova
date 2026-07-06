import type {
  CalendarResponse,
  CreateReminderRequest,
  CreateTaskRequest,
  GraphSnapshotResponse,
  HomeResponse,
  LogSpendingRequest,
  MemoriesListResponse,
  ProductsResponse,
  ReminderMutationResponse,
  RemindersResponse,
  SettingsResponse,
  SpendingMutationResponse,
  SpendingResponse,
  SystemStatusResponse,
  TaskMutationResponse,
  TasksResponse,
} from '@nova/api-contracts'
import { apiGet, apiPost } from '@/lib/api-client'
import { mapCalendar } from '@/mappers/calendar'
import { mapGraph } from '@/mappers/graph'
import { mapHome } from '@/mappers/home'
import { mapMemories } from '@/mappers/memories'
import { mapProducts } from '@/mappers/products'
import { mapReminders } from '@/mappers/reminders'
import { mapSettings } from '@/mappers/settings'
import { mapSpending } from '@/mappers/spending'
import { mapSystemStatus } from '@/mappers/system'
import { mapTasks } from '@/mappers/tasks'
import type {
  CalendarViewModel,
  GraphViewModel,
  HomeViewModel,
  MemoriesViewModel,
  Product,
  Reminder,
  SettingsViewModel,
  SpendingViewModel,
  SystemStatusViewModel,
  Task,
} from '@/view-models'

export async function fetchProducts(): Promise<Product[]> {
  const response = await apiGet<ProductsResponse>('/products')
  return mapProducts(response)
}

export async function fetchTasks(limit = 200): Promise<Task[]> {
  const response = await apiGet<TasksResponse>('/tasks', { limit })
  return mapTasks(response)
}

export async function createTaskRaw(input: CreateTaskRequest): Promise<TaskMutationResponse> {
  return apiPost<CreateTaskRequest, TaskMutationResponse>('/tasks', input)
}

export async function completeTaskRaw(taskId: number): Promise<TaskMutationResponse> {
  return apiPost<Record<string, never>, TaskMutationResponse>(`/tasks/${taskId}/complete`, {})
}

export async function createReminderRaw(input: CreateReminderRequest): Promise<ReminderMutationResponse> {
  return apiPost<CreateReminderRequest, ReminderMutationResponse>('/reminders', input)
}

export async function logSpendingRaw(input: LogSpendingRequest): Promise<SpendingMutationResponse> {
  return apiPost<LogSpendingRequest, SpendingMutationResponse>('/spending', input)
}

export async function fetchSpending(limit = 30): Promise<SpendingViewModel> {
  const response = await apiGet<SpendingResponse>('/spending', { limit })
  return mapSpending(response)
}

export async function fetchReminders(limit = 50): Promise<Reminder[]> {
  const response = await apiGet<RemindersResponse>('/reminders', { limit })
  return mapReminders(response)
}

export async function fetchHome(): Promise<HomeViewModel> {
  const response = await apiGet<HomeResponse>('/home')
  return mapHome(response)
}

export async function fetchMemories(params?: {
  limit?: number
  offset?: number
  tier?: string
  sourceType?: string
  search?: string
  sort?: string
  order?: string
}): Promise<MemoriesViewModel> {
  const response = await apiGet<MemoriesListResponse>('/memories', {
    limit: params?.limit ?? 50,
    offset: params?.offset ?? 0,
    tier: params?.tier,
    source_type: params?.sourceType,
    search: params?.search,
    sort: params?.sort ?? 'created_at',
    order: params?.order ?? 'desc',
  })
  return mapMemories(response)
}

export async function fetchGraph(entityLimit = 500, edgeLimit = 500): Promise<GraphViewModel> {
  const response = await apiGet<GraphSnapshotResponse>('/graph', {
    entity_limit: entityLimit,
    edge_limit: edgeLimit,
  })
  return mapGraph(response)
}

export async function fetchCalendar(day = 'today'): Promise<CalendarViewModel> {
  const response = await apiGet<CalendarResponse>('/calendar', { day })
  return mapCalendar(response)
}

export async function fetchSettings(): Promise<SettingsViewModel> {
  const response = await apiGet<SettingsResponse>('/settings')
  return mapSettings(response)
}

export async function fetchSystemStatus(): Promise<SystemStatusViewModel> {
  const response = await apiGet<SystemStatusResponse>('/system/status')
  return mapSystemStatus(response)
}
