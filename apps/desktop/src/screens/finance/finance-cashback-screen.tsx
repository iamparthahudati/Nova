import { Link } from 'react-router-dom'
import { ScreenHeader } from '@/components/layout/screen-header'
import { Badge } from '@/components/ui/badge'
import { buttonVariants } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { QueryBoundary } from '@/components/query-boundary'
import { useCashbackSummary } from '@/hooks/use-finance'
import { cn, formatINR } from '@/lib/utils'

export function FinanceCashbackScreen() {
  const cashback = useCashbackSummary()

  return (
    <section>
      <ScreenHeader
        title="Cashback"
        description="Cashback is earned on credit card spend when cashback rules are linked to a card's reward program. Cash and bank transactions do not earn cashback here."
      />
      <QueryBoundary query={cashback} loadingMessage="Loading cashback…">
        {(data) => {
          if (data.rules.length === 0) {
            return (
              <div className="rounded-md border border-dashed border-border p-8 text-center">
                <p className="text-sm font-medium">No cashback rules configured</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Set up a credit card, attach a cashback reward program, and define earn rules. Monthly earned totals
                  update when matching credit card transactions are logged.
                </p>
                <div className="mt-4 flex flex-wrap justify-center gap-2">
                  <Link to="/finance/credit-cards" className={cn(buttonVariants({ size: 'sm' }))}>
                    Credit cards
                  </Link>
                  <Link to="/finance/rewards" className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}>
                    Rewards
                  </Link>
                </div>
              </div>
            )
          }
          return (
          <>
            <Card className="mb-4">
              <CardHeader>
                <CardTitle>Monthly earned</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-semibold text-emerald-400">{formatINR(data.monthlyEarned)}</p>
              </CardContent>
            </Card>
            <div className="grid gap-3">
              {data.rules.map((rule) => (
                <Card key={rule.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="font-medium">{rule.name}</p>
                        {rule.programName ? (
                          <p className="text-xs text-muted-foreground">{rule.programName}</p>
                        ) : null}
                      </div>
                      <Badge>{rule.flatRatePercent}% base</Badge>
                    </div>
                    <div className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
                      {Object.keys(rule.categoryMultipliers).length > 0 ? (
                        <div>
                          <p className="text-muted-foreground">Category multipliers</p>
                          <p>{Object.entries(rule.categoryMultipliers).map(([id, bps]) => `${id}: ${bps / 100}%`).join(', ')}</p>
                        </div>
                      ) : null}
                      {Object.keys(rule.merchantMultipliers).length > 0 ? (
                        <div>
                          <p className="text-muted-foreground">Merchant multipliers</p>
                          <p>{Object.entries(rule.merchantMultipliers).map(([id, bps]) => `${id}: ${bps / 100}%`).join(', ')}</p>
                        </div>
                      ) : null}
                      {rule.monthlyCap != null ? (
                        <div>
                          <p className="text-muted-foreground">Monthly cap</p>
                          <p>{formatINR(rule.monthlyCap)}</p>
                        </div>
                      ) : null}
                      <div>
                        <p className="text-muted-foreground">Minimum spend</p>
                        <p>{formatINR(rule.minimumSpend)}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </>
          )
        }}
      </QueryBoundary>
    </section>
  )
}
