import type {
  CreateReminderRequest,
  CreateTaskRequest,
  LogSpendingRequest,
  ReminderMutationResponse,
  ReminderResponse,
  SpendingMutationResponse,
  SpendingTransactionResponse,
  TaskMutationResponse,
  TaskResponse,
} from '@nova/api-contracts'
import { mockReminders, mockSpending, mockTasks } from '@/dev/mocks/data'

const latency = async (ms = 140) => new Promise((resolve) => setTimeout(resolve, ms))

let nextTaskId = Math.max(0, ...mockTasks.map((task) => task.id)) + 1
let nextReminderId = Math.max(0, ...mockReminders.map((reminder) => reminder.id)) + 1
let nextSpendingId = Math.max(0, ...mockSpending.map((entry) => entry.id)) + 1

function toTaskResponse(task: (typeof mockTasks)[number]): TaskResponse {
  return {
    id: task.id,
    text: task.text,
    status: task.status,
    created_at: task.createdAt,
    due: task.due ?? null,
  }
}

export async function createTask(input: CreateTaskRequest): Promise<TaskMutationResponse> {
  await latency()
  const task = {
    id: nextTaskId++,
    text: input.text,
    status: 'open',
    due: input.due ?? undefined,
    createdAt: new Date().toISOString(),
  }
  mockTasks.unshift(task)
  const message = 'Task logged.' + (task.due ? ` Due ${task.due}.` : '')
  return {
    item: toTaskResponse(task),
    meta: { message },
  }
}

export async function completeTask(taskId: number): Promise<TaskMutationResponse> {
  await latency()
  const index = mockTasks.findIndex((task) => task.id === taskId)
  if (index === -1) {
    throw new Error(`Task ${taskId} not found`)
  }
  const task = mockTasks[index]
  if (task.status !== 'open') {
    throw new Error(`Task ${taskId} is not open`)
  }
  mockTasks[index] = { ...task, status: 'done' }
  return {
    item: toTaskResponse(mockTasks[index]),
    meta: { message: 'Task marked done.' },
  }
}

function toReminderResponse(reminder: (typeof mockReminders)[number]): ReminderResponse {
  return {
    id: reminder.id,
    text: reminder.text,
    remind_date: reminder.remindDate,
    remind_time: reminder.remindTime ?? null,
    created_at: reminder.createdAt,
  }
}

export async function createReminder(input: CreateReminderRequest): Promise<ReminderMutationResponse> {
  await latency()
  const reminder = {
    id: nextReminderId++,
    text: input.text,
    remindDate: input.remind_date,
    remindTime: input.remind_time ?? undefined,
    createdAt: new Date().toISOString(),
  }
  mockReminders.unshift(reminder)
  const timeLabel = reminder.remindTime ? ` at ${reminder.remindTime}` : ''
  const dateLabel = new Date(`${reminder.remindDate}T00:00:00`).toLocaleDateString(undefined, {
    month: 'long',
    day: 'numeric',
  })
  return {
    item: toReminderResponse(reminder),
    meta: { message: `Reminder saved: ${reminder.text} on ${dateLabel}${timeLabel}.` },
  }
}

function toSpendingResponse(entry: (typeof mockSpending)[number]): SpendingTransactionResponse {
  return {
    id: entry.id,
    type: entry.type,
    amount: entry.amount,
    note: entry.note ?? null,
    created_at: entry.createdAt,
  }
}

export async function logSpending(input: LogSpendingRequest): Promise<SpendingMutationResponse> {
  await latency()
  const entry = {
    id: nextSpendingId++,
    type: input.type,
    amount: input.amount,
    note: input.note ?? undefined,
    createdAt: new Date().toISOString(),
  }
  mockSpending.unshift(entry)
  return {
    item: toSpendingResponse(entry),
    meta: { message: input.type === 'earned' ? 'Logged earnings.' : 'Logged expense.' },
  }
}
