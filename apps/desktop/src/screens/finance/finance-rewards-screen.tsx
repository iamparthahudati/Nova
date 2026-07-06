import { useState } from 'react'
import { ScreenHeader } from '@/components/layout/screen-header'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { QueryBoundary } from '@/components/query-boundary'
import { useRewardLedger, useRewardPrograms } from '@/hooks/use-finance'

export function FinanceRewardsScreen() {
  const programs = useRewardPrograms()
  const [selectedProgramId, setSelectedProgramId] = useState<number | null>(null)
  const activeProgramId = selectedProgramId ?? programs.data?.[0]?.id ?? null
  const ledger = useRewardLedger(activeProgramId)

  return (
    <section>
      <ScreenHeader title="Rewards" description="Programs, balances, and ledger from reward projections." />
      <QueryBoundary query={programs} loadingMessage="Loading reward programs…" emptyMessage="No reward programs yet.">
        {(programList) => (
          <>
            <div className="mb-4 flex flex-wrap gap-2">
              {programList.map((program) => (
                <button
                  key={program.id}
                  type="button"
                  className={`rounded-lg border px-3 py-2 text-sm transition ${
                    activeProgramId === program.id
                      ? 'border-primary bg-accent text-accent-foreground'
                      : 'border-border text-muted-foreground hover:bg-accent/50'
                  }`}
                  onClick={() => setSelectedProgramId(program.id)}
                >
                  {program.name}
                </button>
              ))}
            </div>
            <div className="mb-4 grid gap-4 sm:grid-cols-3">
              {programList
                .filter((p) => p.id === activeProgramId)
                .map((program) => (
                  <Card key={program.id} className="sm:col-span-3">
                    <CardContent className="flex flex-wrap items-center justify-between gap-4 p-4">
                      <div>
                        <p className="font-medium">{program.name}</p>
                        <p className="text-xs text-muted-foreground">{program.unit}</p>
                      </div>
                      <div className="flex gap-6 text-sm">
                        <div>
                          <p className="text-muted-foreground">Balance</p>
                          <p className="text-xl font-semibold">{program.balance?.balance ?? 0}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Earned</p>
                          <p className="text-xl font-semibold">{program.balance?.totalEarned ?? 0}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Redeemed</p>
                          <p className="text-xl font-semibold">{program.balance?.totalRedeemed ?? 0}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
            </div>
            <QueryBoundary query={ledger} loadingMessage="Loading ledger…" emptyMessage="No reward events yet.">
              {(data) => (
                <Card>
                  <CardHeader>
                    <CardTitle>Reward ledger</CardTitle>
                    <p className="text-sm text-muted-foreground">Yearly earned: {data.yearlyEarned}</p>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {data.events.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No events in this ledger.</p>
                    ) : (
                      data.events.map((event) => (
                        <div
                          key={event.id}
                          className="flex items-center justify-between rounded-md border border-border bg-muted/30 p-3"
                        >
                          <div>
                            <p className="text-sm font-medium">{event.note || event.kind}</p>
                            <p className="text-xs text-muted-foreground">{event.occurredOn}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">{event.direction}</Badge>
                            <span className="font-semibold">{event.amount}</span>
                          </div>
                        </div>
                      ))
                    )}
                  </CardContent>
                </Card>
              )}
            </QueryBoundary>
          </>
        )}
      </QueryBoundary>
    </section>
  )
}
