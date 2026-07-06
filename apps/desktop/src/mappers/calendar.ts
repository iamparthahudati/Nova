import type { CalendarResponse } from '@nova/api-contracts'
import type { CalendarViewModel } from '@/view-models'

export function mapCalendar(response: CalendarResponse): CalendarViewModel {
  return {
    date: response.date,
    unavailable: response.unavailable,
    events: response.events.map((event, index) => ({
      id: `event-${response.date}-${index}`,
      title: event.title,
      timeLabel: event.time,
      date: response.date,
      unavailable: response.unavailable,
    })),
  }
}
