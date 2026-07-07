import { Badge } from '@/components/ui/badge'
import { UtilizationBar } from '@/components/finance/metric-card'
import {
  cardProductName,
  deriveBankName,
  formatBillingSchedule,
  formatDueDay,
  networkAccentClass,
  networkLabel,
  statementStatusClass,
  statementStatusTone,
} from '@/lib/finance/credit-card-display'
import { cn, formatINR, formatShortDate } from '@/lib/utils'
import type { FinanceStatement } from '@/view-models/finance'

interface CreditCardStatementBlockProps {
  title: string
  statement: FinanceStatement
  creditLimit: number
  variant?: 'current' | 'previous'
}

export function CreditCardStatementBlock({
  title,
  statement,
  creditLimit,
  variant = 'current',
}: CreditCardStatementBlockProps) {
  const tone = statementStatusTone(statement.status)
  const statusClass = statementStatusClass(tone)

  return (
    <div
      className={cn(
        'rounded-lg border p-4',
        variant === 'current' ? 'border-border bg-muted/20' : 'border-dashed border-border/80 bg-transparent',
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium">{title}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {statement.periodStart} → {statement.periodEnd}
          </p>
        </div>
        <span className={cn('rounded-full border px-2 py-0.5 text-xs font-medium capitalize', statusClass)}>
          {statement.status ?? 'unknown'}
        </span>
      </div>
      <div className="mt-3 grid gap-3 text-sm sm:grid-cols-3">
        <div>
          <p className="text-xs text-muted-foreground">Statement spend</p>
          <p className="font-semibold">{formatINR(statement.spend ?? 0)}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Paid</p>
          <p className="font-semibold text-emerald-400">{formatINR(statement.paid ?? 0)}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Remaining</p>
          <p className="font-semibold text-rose-400">{formatINR(statement.remainingDue ?? 0)}</p>
        </div>
      </div>
      <p className="mt-2 text-xs text-muted-foreground">Due {formatShortDate(statement.dueDate) ?? statement.dueDate}</p>
      {creditLimit > 0 ? (
        <div className="mt-3">
          <UtilizationBar percent={((statement.spend ?? 0) / creditLimit) * 100} />
        </div>
      ) : null}
    </div>
  )
}

interface CreditCardFaceProps {
  name: string
  network?: string | null
  last4?: string | null
  className?: string
}

export function CreditCardFace({ name, network, last4, className }: CreditCardFaceProps) {
  const bank = deriveBankName(name)
  const cardName = cardProductName(name)
  const networkText = networkLabel(network)

  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-xl bg-gradient-to-br p-4 text-white shadow-lg',
        networkAccentClass(network),
        className,
      )}
    >
      <div className="pointer-events-none absolute -right-8 -top-8 size-32 rounded-full bg-white/10" />
      <div className="pointer-events-none absolute -bottom-10 -left-6 size-40 rounded-full bg-white/5" />
      <div className="relative space-y-4">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="text-xs uppercase tracking-wider text-white/70">{bank}</p>
            <p className="mt-1 text-lg font-semibold">{cardName}</p>
          </div>
          {networkText ? (
            <Badge className="border-white/20 bg-white/15 text-white hover:bg-white/15">{networkText}</Badge>
          ) : null}
        </div>
        <p className="font-mono text-xl tracking-[0.3em]">{last4 ? `•••• ${last4}` : '•••• ••••'}</p>
      </div>
    </div>
  )
}

export function CreditCardMetricsGrid({
  creditLimit,
  availableLimit,
  outstanding,
  utilizationPercent,
  statementDay,
  dueDayOffset,
}: {
  creditLimit: number
  availableLimit?: number | null
  outstanding?: number | null
  utilizationPercent?: number | null
  statementDay: number
  dueDayOffset: number
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <MetricCell label="Credit limit" value={formatINR(creditLimit)} />
      <MetricCell label="Available limit" value={formatINR(availableLimit ?? 0)} tone="positive" />
      <MetricCell label="Outstanding" value={formatINR(outstanding ?? 0)} tone="negative" />
      <MetricCell label="Utilization" value={`${(utilizationPercent ?? 0).toFixed(1)}%`} />
      <MetricCell label="Billing day" value={`Day ${statementDay}`} />
      <MetricCell label="Due day" value={formatDueDay(statementDay, dueDayOffset)} subtitle={formatBillingSchedule(statementDay, dueDayOffset)} />
    </div>
  )
}

function MetricCell({
  label,
  value,
  subtitle,
  tone = 'default',
}: {
  label: string
  value: string
  subtitle?: string
  tone?: 'default' | 'positive' | 'negative'
}) {
  const toneClass =
    tone === 'positive' ? 'text-emerald-400' : tone === 'negative' ? 'text-rose-400' : 'text-foreground'
  return (
    <div className="rounded-md border border-border/60 bg-background/50 px-3 py-2">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={cn('text-sm font-semibold', toneClass)}>{value}</p>
      {subtitle ? <p className="mt-0.5 text-xs text-muted-foreground">{subtitle}</p> : null}
    </div>
  )
}
