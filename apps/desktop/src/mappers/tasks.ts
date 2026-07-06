import type { TaskResponse, TasksResponse } from '@nova/api-contracts'
import type { Task } from '@/view-models'

export function mapTask(row: TaskResponse): Task {
  return {
    id: row.id,
    text: row.text,
    status: row.status,
    due: row.due ?? undefined,
    createdAt: row.created_at,
  }
}

export function mapTasks(response: TasksResponse): Task[] {
  return response.tasks.map(mapTask)
}
