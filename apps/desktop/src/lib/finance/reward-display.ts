import { formatINR, formatShortDate } from '@/lib/utils'
import type { RewardEvent, RewardProgram } from '@/view-models/finance'

export type RewardProgramStatus = 'active' | 'expiring' | 'depleted' | 'new'

export function formatRewardAmount(amount: number, unit: string): string {
  if (unit === 'cashback_minor') return formatINR(amount / 100)
  return `${amount.toLocaleString('en-IN')} pts`
}

export function formatRewardUnit(unit: string): string {
  if (unit === 'cashback_minor') return 'Cashback'
  return 'Points'
}

export function rewardStatusLabel(status: string): string {
  switch (status) {
    case 'active':
      return 'Active'
    case 'expiring':
      return 'Expiring'
    case 'depleted':
      return 'Depleted'
    case 'new':
      return 'New'
    default:
      return status
  }
}

export function rewardStatusTone(status: string): string {
  switch (status) {
    case 'active':
      return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
    case 'expiring':
      return 'border-amber-500/30 bg-amber-500/10 text-amber-400'
    case 'depleted':
      return 'border-muted-foreground/30 bg-muted/40 text-muted-foreground'
    case 'new':
      return 'border-sky-500/30 bg-sky-500/10 text-sky-400'
    default:
      return 'border-border text-muted-foreground'
  }
}

export function rewardEventKindLabel(kind: string): string {
  switch (kind) {
    case 'earned':
      return 'Earned'
    case 'redeemed':
      return 'Redeemed'
    case 'expired':
      return 'Expired'
    case 'adjusted':
      return 'Adjustment'
    default:
      return kind
  }
}

export function rewardEventKindTone(kind: string): string {
  switch (kind) {
    case 'earned':
      return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
    case 'redeemed':
      return 'border-rose-500/30 bg-rose-500/10 text-rose-400'
    case 'expired':
      return 'border-amber-500/30 bg-amber-500/10 text-amber-400'
    case 'adjusted':
      return 'border-sky-500/30 bg-sky-500/10 text-sky-400'
    default:
      return 'border-border text-muted-foreground'
  }
}

export function rewardEventSignedAmount(event: RewardEvent, unit: string): string {
  const prefix = event.direction === 'credit' ? '+' : '−'
  return `${prefix}${formatRewardAmount(event.amount, unit)}`
}

export interface RewardEventDayGroup {
  date: string
  label: string
  events: RewardEvent[]
}

export function groupRewardEventsByDate(events: RewardEvent[]): RewardEventDayGroup[] {
  const groups = new Map<string, RewardEvent[]>()
  for (const event of events) {
    const bucket = groups.get(event.occurredOn) ?? []
    bucket.push(event)
    groups.set(event.occurredOn, bucket)
  }
  return [...groups.entries()]
    .sort(([left], [right]) => right.localeCompare(left))
    .map(([date, dayEvents]) => ({
      date,
      label: formatShortDate(date) ?? date,
      events: dayEvents,
    }))
}

export function programBalanceDisplay(program: RewardProgram): string {
  const balance = program.balance?.balance ?? 0
  return formatRewardAmount(balance, program.unit)
}
