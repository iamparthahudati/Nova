import { formatINR } from '@/lib/utils'

export type CashbackRuleStatus = 'active' | 'capped'

export function cashbackStatusLabel(status: string): string {
  switch (status) {
    case 'active':
      return 'Active'
    case 'capped':
      return 'Cap reached'
    default:
      return status
  }
}

export function cashbackStatusTone(status: string): string {
  switch (status) {
    case 'active':
      return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
    case 'capped':
      return 'border-amber-500/30 bg-amber-500/10 text-amber-400'
    default:
      return 'border-border text-muted-foreground'
  }
}

export function formatMultiplierBps(bps: number): string {
  return `${(bps / 100).toFixed(2)}%`
}

export function formatCashbackEarned(minor: number): string {
  return formatINR(minor / 100)
}

export function formatMultiplierMap(multipliers: Record<number, number>): string {
  const entries = Object.entries(multipliers)
  if (entries.length === 0) return 'None'
  return entries.map(([id, bps]) => `#${id}: ${formatMultiplierBps(bps)}`).join(', ')
}
