import { CheckCircle2, Circle, Clock3 } from 'lucide-react'
import { activeTimelinePhase, type TimelinePhase } from '@/lib/finance/statement-display'
import { cn, formatShortDate } from '@/lib/utils'
import type { FinanceStatement } from '@/view-models/finance'

const PHASES: { id: TimelinePhase; label: string }[] = [
  { id: 'generated', label: 'Generated' },
  { id: 'current', label: 'Current' },
  { id: 'due', label: 'Due' },
  { id: 'paid', label: 'Paid' },
]

interface StatementTimelineProps {
  statement: FinanceStatement
}

export function StatementTimeline({ statement }: StatementTimelineProps) {
  const active = activeTimelinePhase(statement)
  const activeIndex = PHASES.findIndex((phase) => phase.id === active)

  return (
    <div className="rounded-lg border border-border bg-muted/10 p-4">
      <p className="mb-4 text-sm font-medium">Statement timeline</p>
      <div className="flex flex-col gap-0 sm:flex-row sm:items-start sm:justify-between">
        {PHASES.map((phase, index) => {
          const complete = index < activeIndex || active === 'paid'
          const current = phase.id === active
          const Icon = complete ? CheckCircle2 : current ? Clock3 : Circle
          return (
            <div key={phase.id} className="flex flex-1 items-start gap-3 sm:flex-col sm:items-center sm:text-center">
              <div className="flex flex-col items-center sm:w-full">
                <Icon
                  className={cn(
                    'size-5 shrink-0',
                    complete && 'text-emerald-400',
                    current && !complete && 'text-amber-400',
                    !complete && !current && 'text-muted-foreground',
                  )}
                />
                {index < PHASES.length - 1 ? (
                  <div
                    className={cn(
                      'my-1 hidden h-0.5 w-full sm:block',
                      index < activeIndex ? 'bg-emerald-500/60' : 'bg-border',
                    )}
                  />
                ) : null}
              </div>
              <div className="pb-4 sm:pb-0">
                <p className={cn('text-sm font-medium', current && 'text-foreground')}>{phase.label}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">{phaseDateLabel(phase.id, statement)}</p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function phaseDateLabel(phase: TimelinePhase, statement: FinanceStatement): string {
  if (phase === 'generated') return formatShortDate(statement.statementDate) ?? statement.statementDate
  if (phase === 'current') return formatBillingWindow(statement.periodStart, statement.periodEnd)
  if (phase === 'due') return formatShortDate(statement.dueDate) ?? statement.dueDate
  if ((statement.paid ?? 0) > 0 && (statement.remainingDue ?? 1) <= 0) {
    return 'Fully settled'
  }
  return 'Pending settlement'
}

function formatBillingWindow(start: string, end: string): string {
  const startLabel = formatShortDate(start) ?? start
  const endLabel = formatShortDate(end) ?? end
  return `${startLabel} – ${endLabel}`
}
