import type { EventsWebSocketEvent } from '@nova/api-contracts'
import { queryKeys } from '@/query/keys'

type InvalidationKey = readonly unknown[]

export const eventInvalidationMap: Partial<Record<EventsWebSocketEvent, InvalidationKey[]>> = {
  'api.started': [queryKeys.system.status()],
  'task.created': [queryKeys.tasks(), queryKeys.home()],
  'task.updated': [queryKeys.tasks(), queryKeys.home()],
  'spending.logged': [queryKeys.spending(), queryKeys.home()],
  'progress.logged': [queryKeys.home()],
  'product.created': [queryKeys.products(), queryKeys.home()],
  'product.updated': [queryKeys.products(), queryKeys.home()],
  'calendar.updated': [queryKeys.calendar(), queryKeys.home()],
  'reminder.created': [queryKeys.reminders(), queryKeys.home()],
  'reminder.triggered': [queryKeys.reminders(), queryKeys.home()],
  'memory.created': [queryKeys.memories(), queryKeys.home()],
  'habit.logged': [queryKeys.home()],
  'graph.updated': [queryKeys.graph()],
  'entity_extraction.completed': [queryKeys.graph(), queryKeys.memories()],
  'reflection.completed': [queryKeys.home()],
  'pomodoro.completed': [queryKeys.home()],
}
