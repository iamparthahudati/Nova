import { useState } from 'react'
import { ScreenHeader } from '@/components/layout/screen-header'
import { CashbackActivityTimeline } from '@/components/finance/cashback-activity-timeline'
import { CashbackCapSummary, CashbackOverviewPanel } from '@/components/finance/cashback-overview'
import { CashbackEmpty } from '@/components/finance/cashback-empty'
import { CashbackRuleCard } from '@/components/finance/cashback-rule-card'
import { CashbackSkeleton } from '@/components/finance/cashback-skeleton'
import { Button } from '@/components/ui/button'
import { useCashbackActivity, useCashbackSummary } from '@/hooks/use-finance'

export function FinanceCashbackScreen() {
  const summary = useCashbackSummary()
  const activity = useCashbackActivity()
  const [selectedRuleId, setSelectedRuleId] = useState<number | null>(null)

  const loading = summary.isLoading
  const error = summary.isError ? summary : null

  if (loading) {
    return (
      <section>
        <ScreenHeader
          title="Cashback"
          description="Cashback is earned on credit card spend when cashback rules are linked to a card's reward program."
        />
        <CashbackSkeleton />
      </section>
    )
  }

  if (error) {
    return (
      <section>
        <ScreenHeader
          title="Cashback"
          description="Track cashback rules, caps, and earned activity across your credit cards."
        />
        <div className="rounded-md border border-destructive/40 bg-destructive/10 p-4 text-sm">
          <p className="font-medium text-destructive">Failed to load cashback</p>
          <p className="mt-1 text-muted-foreground">{error.error.message}</p>
          <Button className="mt-3" size="sm" variant="secondary" onClick={() => void error.refetch()}>
            Retry
          </Button>
        </div>
      </section>
    )
  }

  const data = summary.data
  if (!data || data.rules.length === 0) {
    return (
      <section>
        <ScreenHeader
          title="Cashback"
          description="Cashback is earned on credit card spend when cashback rules are linked to a card's reward program."
        />
        <CashbackEmpty />
      </section>
    )
  }

  const filteredActivity =
    selectedRuleId === null
      ? (activity.data ?? [])
      : (activity.data ?? []).filter((event) => event.ruleId === selectedRuleId)

  return (
    <section className="space-y-8">
      <ScreenHeader
        title="Cashback"
        description="Track cashback rules, monthly caps, and earned activity across your credit cards."
      />

      <CashbackOverviewPanel summary={data} />
      <CashbackCapSummary summary={data} />

      <div>
        <h2 className="mb-4 text-base font-semibold">Active cashback rules</h2>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {data.rules.map((rule) => (
            <CashbackRuleCard
              key={rule.id}
              rule={rule}
              selected={selectedRuleId === rule.id}
              onSelect={() => setSelectedRuleId((current) => (current === rule.id ? null : rule.id))}
            />
          ))}
        </div>
      </div>

      {activity.isLoading ? (
        <CashbackSkeleton />
      ) : activity.isError ? (
        <div className="rounded-md border border-destructive/40 bg-destructive/10 p-4 text-sm">
          <p className="font-medium text-destructive">Failed to load activity</p>
          <p className="mt-1 text-muted-foreground">{activity.error.message}</p>
          <Button className="mt-3" size="sm" variant="secondary" onClick={() => void activity.refetch()}>
            Retry
          </Button>
        </div>
      ) : (
        <CashbackActivityTimeline
          title={selectedRuleId === null ? 'Cashback activity' : 'Filtered activity'}
          events={filteredActivity}
        />
      )}
    </section>
  )
}
