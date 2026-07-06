import { useState } from 'react'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScreenHeader } from '@/components/layout/screen-header'
import { QueryBoundary } from '@/components/query-boundary'
import { useCalendar } from '@/hooks/use-calendar'
import { useCreateReminder } from '@/hooks/use-reminder-mutations'
import { useReminders } from '@/hooks/use-reminders'
import { ApiError } from '@/lib/api-client'

export function CalendarScreen() {
  const calendar = useCalendar('today')
  const reminders = useReminders()
  const createReminder = useCreateReminder()
  const [showAddForm, setShowAddForm] = useState(false)
  const [text, setText] = useState('')
  const [remindDate, setRemindDate] = useState('')
  const [remindTime, setRemindTime] = useState('')
  const [feedback, setFeedback] = useState<{ tone: 'success' | 'error'; message: string } | null>(null)

  const pending = createReminder.isPending

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault()
    setFeedback(null)
    const trimmed = text.trim()
    if (!trimmed || !remindDate.trim()) {
      return
    }
    try {
      const result = await createReminder.mutateAsync({
        text: trimmed,
        remindDate: remindDate.trim(),
        remindTime: remindTime.trim() || undefined,
      })
      setText('')
      setRemindDate('')
      setRemindTime('')
      setShowAddForm(false)
      setFeedback({ tone: 'success', message: result.meta?.message ?? 'Reminder saved.' })
    } catch (error) {
      setFeedback({
        tone: 'error',
        message: error instanceof ApiError ? error.message : 'Could not save reminder.',
      })
    }
  }

  return (
    <section>
      <ScreenHeader
        title="Calendar"
        description="Daily schedule from the backend calendar and reminders endpoints."
        actions={
          <Button
            type="button"
            variant={showAddForm ? 'secondary' : 'default'}
            size="sm"
            disabled={pending}
            onClick={() => setShowAddForm((open) => !open)}
          >
            <Plus className="h-4 w-4" />
            Add reminder
          </Button>
        }
      />

      {feedback ? (
        <p
          className={`mb-4 text-sm ${feedback.tone === 'success' ? 'text-emerald-400' : 'text-rose-400'}`}
          role="status"
        >
          {feedback.message}
        </p>
      ) : null}

      {showAddForm ? (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>New reminder</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="space-y-3" onSubmit={handleCreate}>
              <label className="block space-y-1">
                <span className="text-xs text-muted-foreground">Reminder text</span>
                <input
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  value={text}
                  onChange={(event) => setText(event.target.value)}
                  placeholder="What should Nova remind you about?"
                  disabled={pending}
                  autoFocus
                />
              </label>
              <label className="block space-y-1">
                <span className="text-xs text-muted-foreground">Date (YYYY-MM-DD)</span>
                <input
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  type="date"
                  value={remindDate}
                  onChange={(event) => setRemindDate(event.target.value)}
                  disabled={pending}
                />
              </label>
              <label className="block space-y-1">
                <span className="text-xs text-muted-foreground">Time (optional, HH:MM)</span>
                <input
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  type="time"
                  value={remindTime}
                  onChange={(event) => setRemindTime(event.target.value)}
                  disabled={pending}
                />
              </label>
              <div className="flex gap-2">
                <Button type="submit" size="sm" disabled={pending || !text.trim() || !remindDate.trim()}>
                  {createReminder.isPending ? 'Saving…' : 'Save reminder'}
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  disabled={pending}
                  onClick={() => setShowAddForm(false)}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Events</CardTitle>
          </CardHeader>
          <CardContent>
            <QueryBoundary query={calendar} loadingMessage="Loading calendar events…">
              {(data) =>
                data.unavailable ? (
                  <p className="text-sm text-muted-foreground">Calendar access is unavailable on this device.</p>
                ) : data.events.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No events today.</p>
                ) : (
                  <div className="space-y-2">
                    {data.events.map((event) => (
                      <div key={event.id} className="rounded-md bg-muted/40 p-3 text-sm">
                        <p className="font-medium">{event.title}</p>
                        <p className="text-xs text-muted-foreground">{event.timeLabel || data.date}</p>
                      </div>
                    ))}
                  </div>
                )
              }
            </QueryBoundary>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Reminder timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <QueryBoundary
              query={reminders}
              isEmpty={(data) => data.length === 0}
              loadingMessage="Loading reminders…"
              emptyMessage="No reminders scheduled."
            >
              {(data) => (
                <div className="space-y-2">
                  {data.map((reminder) => (
                    <div key={reminder.id} className="rounded-md bg-muted/40 p-3 text-sm">
                      <p className="font-medium">{reminder.text}</p>
                      <p className="text-xs text-muted-foreground">
                        {reminder.remindDate} {reminder.remindTime ?? 'all day'}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </QueryBoundary>
          </CardContent>
        </Card>
      </div>
    </section>
  )
}
