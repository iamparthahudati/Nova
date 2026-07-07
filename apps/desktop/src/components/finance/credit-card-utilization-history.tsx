import { UtilizationBar } from '@/components/finance/metric-card'
import { statementUtilizationPercent } from '@/lib/finance/credit-card-display'
import { formatINR, formatShortDate } from '@/lib/utils'
import type { FinanceStatement } from '@/view-models/finance'

interface CreditCardUtilizationHistoryProps {
  statements: FinanceStatement[]
  creditLimit: number
  currentUtilization?: number | null
}

export function CreditCardUtilizationHistory({
  statements,
  creditLimit,
  currentUtilization,
}: CreditCardUtilizationHistoryProps) {
  const historical = statements
    .slice(0, 6)
    .map((statement) => ({
      id: statement.id,
      label: formatShortDate(statement.periodEnd) ?? statement.periodEnd,
      percent: statementUtilizationPercent(statement, creditLimit),
      spend: statement.spend ?? 0,
    }))
    .reverse()

  const points =
    historical.length > 0
      ? historical
      : currentUtilization != null
        ? [{ id: 0, label: 'Now', percent: currentUtilization, spend: 0 }]
        : []

  if (points.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
        Utilization history appears after statement cycles are generated.
      </div>
    )
  }

  const maxPercent = Math.max(...points.map((point) => point.percent), 1)

  return (
    <div className="space-y-4">
      <div className="flex h-40 items-end gap-2">
        {points.map((point) => {
          const height = Math.max((point.percent / maxPercent) * 100, 8)
          const tone =
            point.percent >= 80 ? 'bg-rose-500' : point.percent >= 50 ? 'bg-amber-500' : 'bg-emerald-500'
          return (
            <div key={point.id} className="flex min-w-0 flex-1 flex-col items-center gap-2">
              <span className="text-xs font-medium text-muted-foreground">{point.percent.toFixed(0)}%</span>
              <div className="flex w-full flex-1 items-end">
                <div
                  className={`w-full rounded-t-md transition-all ${tone}`}
                  style={{ height: `${height}%` }}
                  title={`${point.label}: ${point.percent.toFixed(1)}%`}
                />
              </div>
              <span className="w-full truncate text-center text-[10px] text-muted-foreground">{point.label}</span>
            </div>
          )
        })}
      </div>
      {currentUtilization != null ? (
        <div>
          <UtilizationBar percent={currentUtilization} />
          <p className="mt-1 text-xs text-muted-foreground">Current live utilization against {formatINR(creditLimit)} limit</p>
        </div>
      ) : null}
    </div>
  )
}
