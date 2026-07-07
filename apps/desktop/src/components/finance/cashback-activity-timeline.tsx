import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatShortDate, formatINR, cn } from '@/lib/utils'
import type { CashbackActivityEvent } from '@/view-models/finance'

interface CashbackActivityTimelineProps {
  title?: string
  events: CashbackActivityEvent[]
  emptyMessage?: string
}

function groupEventsByDate(events: CashbackActivityEvent[]) {
  const groups = new Map<string, CashbackActivityEvent[]>()
  for (const event of events) {
    const bucket = groups.get(event.occurredOn) ?? []
    bucket.push(event)
    groups.set(event.occurredOn, bucket)
  }
  return [...groups.entries()]
    .sort(([left], [right]) => right.localeCompare(left))
    .map(([date, dayEvents]) => ({
      date,
      label: formatShortDate(date) ?? date,
      events: dayEvents,
    }))
}

export function CashbackActivityTimeline({
  title = 'Cashback activity',
  events,
  emptyMessage = 'No cashback earned yet.',
}: CashbackActivityTimelineProps) {
  const groups = groupEventsByDate(events)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {groups.length === 0 ? (
          <p className="text-sm text-muted-foreground">{emptyMessage}</p>
        ) : (
          <div className="space-y-6">
            {groups.map((group) => (
              <div key={group.date}>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  {group.label}
                </p>
                <div className="space-y-2">
                  {group.events.map((event) => (
                    <div
                      key={event.id}
                      className="flex items-center justify-between rounded-lg border border-border bg-muted/20 px-3 py-2.5"
                    >
                      <div className="min-w-0 space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge
                            variant="outline"
                            className="border-emerald-500/30 bg-emerald-500/10 text-xs text-emerald-400"
                          >
                            Earned
                          </Badge>
                          {event.ruleName ? (
                            <p className="truncate text-sm font-medium">{event.ruleName}</p>
                          ) : null}
                        </div>
                        <p className="truncate text-xs text-muted-foreground">
                          {event.transactionNote ?? event.programName}
                        </p>
                      </div>
                      <p className={cn('shrink-0 text-sm font-semibold text-emerald-400')}>
                        +{formatINR(event.amount)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
