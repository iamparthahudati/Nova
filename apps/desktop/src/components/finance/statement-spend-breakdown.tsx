import { UtilizationBar } from '@/components/finance/metric-card'
import type { SpendBreakdownRow } from '@/lib/finance/statement-display'
import { formatINR } from '@/lib/utils'

interface StatementSpendBreakdownProps {
  title: string
  rows: SpendBreakdownRow[]
  emptyMessage: string
}

export function StatementSpendBreakdown({ title, rows, emptyMessage }: StatementSpendBreakdownProps) {
  return (
    <div className="space-y-3">
      <p className="text-sm font-medium">{title}</p>
      {rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">{emptyMessage}</p>
      ) : (
        <div className="space-y-3">
          {rows.map((row) => (
            <div key={row.key} className="space-y-1">
              <div className="flex items-center justify-between gap-2 text-sm">
                <span className="truncate">{row.label}</span>
                <span className="shrink-0 font-medium">{formatINR(row.amount)}</span>
              </div>
              <UtilizationBar percent={row.percent} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
