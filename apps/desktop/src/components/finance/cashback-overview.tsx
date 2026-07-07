import { MetricCard } from '@/components/finance/metric-card'
import { formatINR } from '@/lib/utils'
import type { CashbackSummary } from '@/view-models/finance'

export function CashbackOverviewPanel({ summary }: { summary: CashbackSummary }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <MetricCard
        title="Total earned"
        value={formatINR(summary.totalBalance)}
        subtitle="Available cashback balance"
        tone="positive"
      />
      <MetricCard
        title="This month"
        value={formatINR(summary.monthlyEarned)}
        subtitle={`${summary.activeRulesCount} active rule${summary.activeRulesCount === 1 ? '' : 's'}`}
      />
      <MetricCard title="This year" value={formatINR(summary.earnedYear)} />
      <MetricCard
        title="Lifetime"
        value={formatINR(summary.earnedLifetime)}
        subtitle={
          summary.remainingMonthlyCap != null
            ? `${formatINR(summary.remainingMonthlyCap)} cap remaining`
            : 'No monthly caps configured'
        }
        tone="positive"
      />
    </div>
  )
}

export function CashbackCapSummary({ summary }: { summary: CashbackSummary }) {
  if (summary.remainingMonthlyCap == null) return null
  return (
    <p className="text-sm text-muted-foreground">
      Combined monthly cap headroom across capped rules:{' '}
      <span className="font-medium text-foreground">{formatINR(summary.remainingMonthlyCap)}</span>
    </p>
  )
}
