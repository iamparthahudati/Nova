import type { ReminderResponse, RemindersResponse } from '@nova/api-contracts'
import type { Reminder } from '@/view-models'

export function mapReminder(row: ReminderResponse): Reminder {
  return {
    id: row.id,
    text: row.text,
    remindDate: row.remind_date,
    remindTime: row.remind_time ?? undefined,
    createdAt: row.created_at,
  }
}

export function mapReminders(response: RemindersResponse): Reminder[] {
  return response.reminders.map(mapReminder)
}
