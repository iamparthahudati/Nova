import { Link } from 'react-router-dom'
import { CalendarDays, ChevronRight, FileText, PlusCircle } from 'lucide-react'
import { StatementStatusChip } from '@/components/finance/statement-status-chip'
import { UtilizationBar } from '@/components/finance/metric-card'
import { Button, buttonVariants } from '@/components/ui/button'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import {
  daysUntilDue,
  formatBillingPeriod,
  paymentProgressPercent,
  resolveDisplayStatus,
  statementMonthLabel,
} from '@/lib/finance/statement-display'
import { cn, formatINR, formatShortDate } from '@/lib/utils'
import type { FinanceStatement } from '@/view-models/finance'

interface StatementCardProps {
  statement: FinanceStatement
  cardName?: string
}

export function StatementCard({ statement, cardName }: StatementCardProps) {
  const displayStatus = resolveDisplayStatus(statement)
  const daysLeft = daysUntilDue(statement.dueDate)
  const progress = paymentProgressPercent(statement)

  return (
    <Card className="overflow-hidden transition-colors hover:border-emerald-500/30">
      <CardHeader className="space-y-3 border-b border-border/60 bg-muted/10 pb-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-lg font-semibold">{statementMonthLabel(statement.periodEnd)}</p>
            {cardName ? <p className="mt-0.5 text-sm text-muted-foreground">{cardName}</p> : null}
          </div>
          <StatementStatusChip statement={statement} status={displayStatus} />
        </div>
        <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <CalendarDays className="size-3.5" />
            {formatBillingPeriod(statement.periodStart, statement.periodEnd)}
          </span>
          <span>Statement {formatShortDate(statement.statementDate) ?? statement.statementDate}</span>
          <span>Due {formatShortDate(statement.dueDate) ?? statement.dueDate}</span>
          {displayStatus !== 'paid' && daysLeft >= 0 ? (
            <span className="text-amber-400">
              {daysLeft === 0 ? 'Due today' : `${daysLeft} day${daysLeft === 1 ? '' : 's'} remaining`}
            </span>
          ) : null}
        </div>
      </CardHeader>
      <CardContent className="space-y-4 p-4">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Metric label="Total spend" value={formatINR(statement.spend ?? 0)} />
          <Metric label="Total paid" value={formatINR(statement.paid ?? 0)} tone="positive" />
          <Metric label="Remaining due" value={formatINR(statement.remainingDue ?? 0)} tone="negative" />
          <Metric label="Minimum due" value={formatINR(statement.minDue ?? 0)} />
        </div>
        {(statement.totalDue ?? 0) > 0 ? (
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Payment progress</span>
              <span>{progress.toFixed(0)}%</span>
            </div>
            <UtilizationBar percent={progress} />
          </div>
        ) : null}
        <div className="flex justify-end">
          <Link
            to={`/finance/statements/${statement.id}`}
            className={cn(buttonVariants({ variant: 'outline', size: 'sm' }), 'inline-flex')}
          >
            View details
            <ChevronRight className="size-4" />
          </Link>
        </div>
      </CardContent>
    </Card>
  )
}

function Metric({
  label,
  value,
  tone = 'default',
}: {
  label: string
  value: string
  tone?: 'default' | 'positive' | 'negative'
}) {
  const toneClass =
    tone === 'positive' ? 'text-emerald-400' : tone === 'negative' ? 'text-rose-400' : 'text-foreground'
  return (
    <div className="rounded-md border border-border/70 bg-background/60 p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={`mt-1 text-sm font-semibold ${toneClass}`}>{value}</p>
    </div>
  )
}

export function StatementEmptyState({ onBrowseCards }: { onBrowseCards: () => void }) {
  return (
    <div className="rounded-xl border border-dashed border-border bg-muted/10 p-10 text-center">
      <div className="mx-auto flex size-14 items-center justify-center rounded-full border border-border bg-muted/30">
        <FileText className="size-7 text-muted-foreground" />
      </div>
      <p className="mt-4 text-base font-medium">No statements yet</p>
      <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
        Statement cycles appear after you add a credit card and transactions post to billing periods.
      </p>
      <Button className="mt-5" size="sm" onClick={onBrowseCards}>
        <PlusCircle className="size-4" />
        Go to credit cards
      </Button>
    </div>
  )
}

export function StatementLoadingGrid() {
  return (
    <div className="space-y-4">
      {[0, 1, 2].map((key) => (
        <Card key={key} className="overflow-hidden">
          <div className="h-20 animate-pulse bg-muted/40" />
          <CardContent className="space-y-3 p-4">
            <div className="grid gap-2 sm:grid-cols-4">
              {[0, 1, 2, 3].map((cell) => (
                <div key={cell} className="h-14 animate-pulse rounded bg-muted/60" />
              ))}
            </div>
            <div className="h-2 animate-pulse rounded-full bg-muted" />
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
