import type {
  CreateReminderRequest,
  CreateTaskRequest,
  LogSpendingRequest,
  ReminderMutationResponse,
  SpendingMutationResponse,
  TaskMutationResponse,
} from '@nova/api-contracts'
import { isMockMode } from '@/config/env'
import * as mockMutations from '@/dev/mocks/mutations'
import * as mockApi from '@/dev/mocks/api'
import * as novaApi from '@/services/nova-api'
import { mapReminder } from '@/mappers/reminders'
import { mapSpendingTransaction } from '@/mappers/spending'
import { mapTask } from '@/mappers/tasks'
import type { Reminder, SpendingEntry, Task } from '@/view-models'

export interface TaskMutationResult {
  task: Task
  meta: { message: string }
}

export interface ReminderMutationResult {
  reminder: Reminder
  meta: { message: string }
}

export interface SpendingMutationResult {
  transaction: SpendingEntry
  meta: { message: string }
}

async function normalizeTaskMutation(response: TaskMutationResponse): Promise<TaskMutationResult> {
  return {
    task: mapTask(response.item),
    meta: response.meta,
  }
}

async function normalizeReminderMutation(response: ReminderMutationResponse): Promise<ReminderMutationResult> {
  return {
    reminder: mapReminder(response.item),
    meta: response.meta,
  }
}

async function normalizeSpendingMutation(response: SpendingMutationResponse): Promise<SpendingMutationResult> {
  return {
    transaction: mapSpendingTransaction(response.item),
    meta: response.meta,
  }
}

export const dataSource = {
  getProducts: () => (isMockMode() ? mockApi.listProducts() : novaApi.fetchProducts()),
  getTasks: (limit?: number) => (isMockMode() ? mockApi.listTasks() : novaApi.fetchTasks(limit)),
  getSpending: (limit?: number) => (isMockMode() ? mockApi.getSpending() : novaApi.fetchSpending(limit)),
  getReminders: (limit?: number) => (isMockMode() ? mockApi.listReminders() : novaApi.fetchReminders(limit)),
  getHome: () => (isMockMode() ? mockApi.getHome() : novaApi.fetchHome()),
  getMemories: (params?: Parameters<typeof novaApi.fetchMemories>[0]) =>
    isMockMode() ? mockApi.listMemories() : novaApi.fetchMemories(params),
  getGraph: () => (isMockMode() ? mockApi.listGraph() : novaApi.fetchGraph()),
  getCalendar: (day?: string) => (isMockMode() ? mockApi.getCalendar() : novaApi.fetchCalendar(day)),
  getSettings: () => (isMockMode() ? mockApi.getSettings() : novaApi.fetchSettings()),
  getSystemStatus: () => (isMockMode() ? mockApi.getSystemStatus() : novaApi.fetchSystemStatus()),
  createTask: async (input: CreateTaskRequest): Promise<TaskMutationResult> =>
    normalizeTaskMutation(
      isMockMode() ? await mockMutations.createTask(input) : await novaApi.createTaskRaw(input),
    ),
  completeTask: async (taskId: number): Promise<TaskMutationResult> =>
    normalizeTaskMutation(
      isMockMode() ? await mockMutations.completeTask(taskId) : await novaApi.completeTaskRaw(taskId),
    ),
  createReminder: async (input: CreateReminderRequest): Promise<ReminderMutationResult> =>
    normalizeReminderMutation(
      isMockMode() ? await mockMutations.createReminder(input) : await novaApi.createReminderRaw(input),
    ),
  logSpending: async (input: LogSpendingRequest): Promise<SpendingMutationResult> =>
    normalizeSpendingMutation(
      isMockMode() ? await mockMutations.logSpending(input) : await novaApi.logSpendingRaw(input),
    ),
}
