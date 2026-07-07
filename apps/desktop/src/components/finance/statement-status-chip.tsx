import { statementStatusClass } from '@/lib/finance/credit-card-display'
import {
  displayStatusLabel,
  displayStatusTone,
  resolveDisplayStatus,
  type DisplayStatementStatus,
} from '@/lib/finance/statement-display'
import { cn } from '@/lib/utils'
import type { FinanceStatement } from '@/view-models/finance'

interface StatementStatusChipProps {
  statement: FinanceStatement
  className?: string
  status?: DisplayStatementStatus
}

export function StatementStatusChip({ statement, className, status }: StatementStatusChipProps) {
  const resolved = status ?? resolveDisplayStatus(statement)
  const tone = displayStatusTone(resolved)
  const label = displayStatusLabel(resolved)

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium',
        statementStatusClass(tone),
        className,
      )}
    >
      {label}
    </span>
  )
}
