import { useState } from 'react'
import { ScreenHeader } from '@/components/layout/screen-header'
import { RewardLedgerTimeline } from '@/components/finance/reward-ledger-timeline'
import { RewardProgramCard } from '@/components/finance/reward-program-card'
import { RewardsEmpty } from '@/components/finance/rewards-empty'
import { RewardsOverviewPanel } from '@/components/finance/rewards-overview'
import { RewardsSkeleton } from '@/components/finance/rewards-skeleton'
import { Button } from '@/components/ui/button'
import { useRewardLedger, useRewardPrograms, useRewardsOverview } from '@/hooks/use-finance'

export function FinanceRewardsScreen() {
  const overview = useRewardsOverview()
  const programs = useRewardPrograms()
  const [selectedProgramId, setSelectedProgramId] = useState<number | null>(null)
  const activeProgramId = selectedProgramId ?? programs.data?.[0]?.id ?? null
  const ledger = useRewardLedger(activeProgramId)

  const loading = overview.isLoading || programs.isLoading
  const error = overview.isError ? overview : programs.isError ? programs : null

  if (loading) {
    return (
      <section>
        <ScreenHeader
          title="Rewards"
          description="Reward programs are tied to credit cards. Regular bank/cash transactions do not earn rewards until a card program is configured."
        />
        <RewardsSkeleton />
      </section>
    )
  }

  if (error) {
    return (
      <section>
        <ScreenHeader title="Rewards" description="Track points and cashback across your credit card programs." />
        <div className="rounded-md border border-destructive/40 bg-destructive/10 p-4 text-sm">
          <p className="font-medium text-destructive">Failed to load rewards</p>
          <p className="mt-1 text-muted-foreground">{error.error.message}</p>
          <Button className="mt-3" size="sm" variant="secondary" onClick={() => void error.refetch()}>
            Retry
          </Button>
        </div>
      </section>
    )
  }

  const programList = programs.data ?? []

  if (programList.length === 0) {
    return (
      <section>
        <ScreenHeader
          title="Rewards"
          description="Reward programs are tied to credit cards. Regular bank/cash transactions do not earn rewards until a card program is configured."
        />
        <RewardsEmpty />
      </section>
    )
  }

  return (
    <section className="space-y-8">
      <ScreenHeader
        title="Rewards"
        description="Track points and cashback across your credit card programs."
      />

      {overview.data ? <RewardsOverviewPanel overview={overview.data} /> : null}

      <div>
        <h2 className="mb-4 text-base font-semibold">Reward programs</h2>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {programList.map((program) => (
            <RewardProgramCard
              key={program.id}
              program={program}
              selected={activeProgramId === program.id}
              onSelect={() => setSelectedProgramId(program.id)}
            />
          ))}
        </div>
      </div>

      {activeProgramId !== null ? (
        ledger.isLoading ? (
          <RewardsSkeleton />
        ) : ledger.isError ? (
          <div className="rounded-md border border-destructive/40 bg-destructive/10 p-4 text-sm">
            <p className="font-medium text-destructive">Failed to load ledger</p>
            <p className="mt-1 text-muted-foreground">{ledger.error.message}</p>
            <Button className="mt-3" size="sm" variant="secondary" onClick={() => void ledger.refetch()}>
              Retry
            </Button>
          </div>
        ) : ledger.data ? (
          <RewardLedgerTimeline
            unit={ledger.data.program.unit}
            events={ledger.data.events}
            title={`Ledger · ${ledger.data.program.name}`}
          />
        ) : null
      ) : null}
    </section>
  )
}
