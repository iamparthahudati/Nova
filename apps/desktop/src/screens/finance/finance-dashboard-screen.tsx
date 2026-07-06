import { ScreenHeader } from '@/components/layout/screen-header'
import { Amount, MetricCard, UtilizationBar } from '@/components/finance/metric-card'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { QueryBoundary } from '@/components/query-boundary'
import { useFinanceDashboard } from '@/hooks/use-finance'
import { formatINR } from '@/lib/utils'

export function FinanceDashboardScreen() {
  const dashboard = useFinanceDashboard()

  return (
    <section>
      <ScreenHeader title="Finance" description="Overview from backend projections — no client-side calculations." />
      <QueryBoundary query={dashboard} loadingMessage="Loading finance dashboard…" emptyMessage="No finance data yet.">
        {(data) => (
          <>
            <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <MetricCard title="Net worth" value={formatINR(data.totalBalance)} />
              <MetricCard title="Total assets" value={formatINR(data.totalAssets)} tone="positive" />
              <MetricCard title="Total liabilities" value={formatINR(data.totalLiabilities)} tone="negative" />
              <MetricCard
                title="Spent this month"
                value={formatINR(data.spentMonth)}
                subtitle="From period totals projection"
              />
            </div>
            <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              <MetricCard title="Reward balance" value={String(data.rewardBalance)} subtitle="Points / units" />
              <MetricCard title="Cashback this month" value={formatINR(data.cashbackEarnedMonth)} tone="positive" />
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Credit utilization</CardTitle>
                </CardHeader>
                <CardContent>
                  <UtilizationBar percent={data.creditUtilizationPercent} />
                </CardContent>
              </Card>
            </div>
            <div className="grid gap-4 xl:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Upcoming due dates</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {data.upcomingDueDates.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No upcoming statement due dates.</p>
                  ) : (
                    data.upcomingDueDates.map((item) => (
                      <div
                        key={item.statementId}
                        className="flex items-center justify-between rounded-md border border-border bg-muted/30 p-3"
                      >
                        <div>
                          <p className="text-sm font-medium">{item.cardName}</p>
                          <p className="text-xs text-muted-foreground">Due {item.dueDate}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{item.status}</Badge>
                          {item.remainingDue != null ? (
                            <span className="text-sm font-semibold">{formatINR(item.remainingDue)}</span>
                          ) : null}
                        </div>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Recent transactions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {data.recentTransactions.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No recent transactions.</p>
                  ) : (
                    data.recentTransactions.map((txn) => (
                      <div
                        key={txn.id}
                        className="flex items-center justify-between rounded-md border border-border bg-muted/30 p-3"
                      >
                        <div>
                          <p className="text-sm font-medium">{txn.note || txn.merchantName || txn.kind}</p>
                          <p className="text-xs text-muted-foreground">
                            {txn.accountName} · {txn.occurredOn}
                          </p>
                        </div>
                        <Amount value={txn.amount} direction={txn.kind} />
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </QueryBoundary>
    </section>
  )
}
