import type { LucideIcon } from 'lucide-react'
import { ArrowLeftRight, CircleDollarSign, TrendingDown, TrendingUp } from 'lucide-react'

export interface TransactionKindMeta {
  value: string
  label: string
  icon: LucideIcon
  amountTone: 'positive' | 'negative' | 'neutral'
}

export const TRANSACTION_KINDS: TransactionKindMeta[] = [
  { value: 'expense', label: 'Expense', icon: TrendingDown, amountTone: 'negative' },
  { value: 'income', label: 'Income', icon: TrendingUp, amountTone: 'positive' },
  { value: 'adjustment', label: 'Adjustment', icon: ArrowLeftRight, amountTone: 'neutral' },
]

export function transactionKindMeta(kind: string): TransactionKindMeta {
  return TRANSACTION_KINDS.find((row) => row.value === kind) ?? {
    value: kind,
    label: kind,
    icon: CircleDollarSign,
    amountTone: 'neutral',
  }
}
