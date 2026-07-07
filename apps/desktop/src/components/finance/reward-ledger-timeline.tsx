import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  groupRewardEventsByDate,
  rewardEventKindLabel,
  rewardEventKindTone,
  rewardEventSignedAmount,
} from '@/lib/finance/reward-display'
import { cn } from '@/lib/utils'
import type { RewardEvent } from '@/view-models/finance'

interface RewardLedgerTimelineProps {
  title?: string
  unit: string
  events: RewardEvent[]
  emptyMessage?: string
}

export function RewardLedgerTimeline({
  title = 'Reward ledger',
  unit,
  events,
  emptyMessage = 'No reward events yet.',
}: RewardLedgerTimelineProps) {
  const groups = groupRewardEventsByDate(events)

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
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge variant="outline" className={cn('text-xs', rewardEventKindTone(event.kind))}>
                            {rewardEventKindLabel(event.kind)}
                          </Badge>
                          {event.note ? (
                            <p className="truncate text-sm font-medium">{event.note}</p>
                          ) : null}
                        </div>
                      </div>
                      <p
                        className={cn(
                          'shrink-0 text-sm font-semibold',
                          event.direction === 'credit' ? 'text-emerald-400' : 'text-rose-400',
                        )}
                      >
                        {rewardEventSignedAmount(event, unit)}
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
