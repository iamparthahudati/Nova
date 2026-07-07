import { MetricCard } from '@/components/finance/metric-card'
import { formatRewardAmount } from '@/lib/finance/reward-display'
import { formatINR } from '@/lib/utils'
import type { RewardsOverview } from '@/view-models/finance'

function balanceSubtitle(overview: RewardsOverview): string {
  const parts: string[] = []
  if (overview.totalBalance > 0) {
    parts.push(`${overview.totalBalance.toLocaleString('en-IN')} pts`)
  }
  if (overview.totalBalanceCashback > 0) {
    parts.push(formatINR(overview.totalBalanceCashback))
  }
  return parts.length > 0 ? parts.join(' · ') : 'Across all programs'
}

function earnedSubtitle(overview: RewardsOverview, period: 'month' | 'year' | 'lifetime'): string {
  const points =
    period === 'month'
      ? overview.earnedMonth
      : period === 'year'
        ? overview.earnedYear
        : overview.earnedLifetime
  const cashback =
    period === 'month'
      ? overview.earnedMonthCashback
      : period === 'year'
        ? overview.earnedYearCashback
        : overview.earnedLifetimeCashback

  const parts: string[] = []
  if (points > 0) parts.push(`${points.toLocaleString('en-IN')} pts`)
  if (cashback > 0) parts.push(formatINR(cashback))
  return parts.length > 0 ? parts.join(' · ') : 'No earnings recorded'
}

export function RewardsOverviewPanel({ overview }: { overview: RewardsOverview }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <MetricCard
        title="Total balance"
        value={formatRewardAmount(overview.totalBalance, 'points')}
        subtitle={balanceSubtitle(overview)}
        tone="positive"
      />
      <MetricCard
        title="This month"
        value={overview.earnedMonth.toLocaleString('en-IN')}
        subtitle={earnedSubtitle(overview, 'month')}
      />
      <MetricCard
        title="This year"
        value={overview.earnedYear.toLocaleString('en-IN')}
        subtitle={earnedSubtitle(overview, 'year')}
      />
      <MetricCard
        title="Lifetime"
        value={overview.earnedLifetime.toLocaleString('en-IN')}
        subtitle={earnedSubtitle(overview, 'lifetime')}
        tone="positive"
      />
    </div>
  )
}
