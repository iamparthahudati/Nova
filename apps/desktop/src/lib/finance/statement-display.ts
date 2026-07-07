import type { FinanceStatement, FinanceTransaction } from '@/view-models/finance'
import type { StatusTone } from '@/lib/finance/credit-card-display'

export type DisplayStatementStatus =
  | 'open'
  | 'due-soon'
  | 'due-today'
  | 'overdue'
  | 'partially-paid'
  | 'paid'

export interface SpendBreakdownRow {
  key: string
  label: string
  amount: number
  percent: number
}

const DUE_SOON_DAYS = 7

export function statementMonthLabel(periodEnd: string): string {
  const date = new Date(periodEnd)
  if (Number.isNaN(date.getTime())) return periodEnd.slice(0, 7)
  return date.toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })
}

export function formatBillingPeriod(periodStart: string, periodEnd: string): string {
  return `${periodStart} → ${periodEnd}`
}

export function daysUntilDue(dueDate: string, today = new Date()): number {
  const due = new Date(dueDate)
  if (Number.isNaN(due.getTime())) return 0
  const start = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const end = new Date(due.getFullYear(), due.getMonth(), due.getDate())
  return Math.round((end.getTime() - start.getTime()) / 86_400_000)
}

export function resolveDisplayStatus(
  statement: Pick<FinanceStatement, 'status' | 'dueDate' | 'remainingDue' | 'paid' | 'totalDue'>,
  today = new Date(),
): DisplayStatementStatus {
  const backend = statement.status?.toLowerCase() ?? ''
  if (backend === 'paid') return 'paid'
  if (backend === 'partial') return 'partially-paid'
  if (backend === 'overdue') return 'overdue'
  if (backend === 'open' || backend === 'generated') return 'open'

  const daysLeft = daysUntilDue(statement.dueDate, today)
  if (backend === 'due') {
    if (daysLeft <= 0) return 'due-today'
    return 'due-soon'
  }
  if (daysLeft <= 0) return 'due-today'
  if (daysLeft <= DUE_SOON_DAYS) return 'due-soon'
  return 'open'
}

export function displayStatusLabel(status: DisplayStatementStatus): string {
  if (status === 'due-soon') return 'Due Soon'
  if (status === 'due-today') return 'Due Today'
  if (status === 'partially-paid') return 'Partially Paid'
  if (status === 'open') return 'Open'
  if (status === 'overdue') return 'Overdue'
  return 'Paid'
}

export function displayStatusTone(status: DisplayStatementStatus): StatusTone {
  if (status === 'paid') return 'positive'
  if (status === 'overdue') return 'negative'
  if (status === 'due-today') return 'negative'
  if (status === 'due-soon') return 'warning'
  if (status === 'partially-paid') return 'warning'
  return 'default'
}

export function paymentProgressPercent(statement: FinanceStatement): number {
  const total = statement.totalDue ?? statement.spend ?? 0
  if (!total || total <= 0) return 0
  const paid = statement.paid ?? 0
  return Math.min(Math.max((paid / total) * 100, 0), 100)
}

export function aggregateSpendByCategory(transactions: FinanceTransaction[]): SpendBreakdownRow[] {
  return aggregateSpend(
    transactions,
    (txn) => txn.categoryName ?? 'Uncategorized',
    (txn) => String(txn.categoryId ?? 'none'),
  )
}

export function aggregateSpendByMerchant(transactions: FinanceTransaction[]): SpendBreakdownRow[] {
  return aggregateSpend(
    transactions,
    (txn) => txn.merchantName ?? 'Unknown merchant',
    (txn) => String(txn.merchantId ?? 'none'),
  )
}

function aggregateSpend(
  transactions: FinanceTransaction[],
  labelFor: (txn: FinanceTransaction) => string,
  keyFor: (txn: FinanceTransaction) => string,
): SpendBreakdownRow[] {
  const totals = new Map<string, { label: string; amount: number }>()
  for (const txn of transactions) {
    if (txn.kind !== 'expense' && txn.direction !== 'debit') continue
    const key = keyFor(txn)
    const current = totals.get(key) ?? { label: labelFor(txn), amount: 0 }
    current.amount += txn.amount
    totals.set(key, current)
  }
  const rows = [...totals.values()].sort((a, b) => b.amount - a.amount)
  const grandTotal = rows.reduce((sum, row) => sum + row.amount, 0)
  if (grandTotal <= 0) return []
  return rows.map((row, index) => ({
    key: `${index}-${row.label}`,
    label: row.label,
    amount: row.amount,
    percent: (row.amount / grandTotal) * 100,
  }))
}

export type TimelinePhase = 'generated' | 'current' | 'due' | 'paid'

export function activeTimelinePhase(
  statement: FinanceStatement,
  today = new Date(),
): TimelinePhase {
  const display = resolveDisplayStatus(statement, today)
  if (display === 'paid') return 'paid'
  const daysLeft = daysUntilDue(statement.dueDate, today)
  if (daysLeft <= 0) return 'due'
  const statementDay = new Date(statement.statementDate)
  if (!Number.isNaN(statementDay.getTime()) && today >= statementDay) return 'current'
  return 'generated'
}
