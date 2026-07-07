import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Building2, Receipt } from 'lucide-react'
import { CashbackActivityTimeline } from '@/components/finance/cashback-activity-timeline'
import { CashbackStatusChip } from '@/components/finance/cashback-status-chip'
import { TransactionCard } from '@/components/finance/transaction-card'
import { MetricCard, UtilizationBar } from '@/components/finance/metric-card'
import { ScreenHeader } from '@/components/layout/screen-header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { QueryBoundary } from '@/components/query-boundary'
import { useCashbackRuleDetail } from '@/hooks/use-finance'
import { formatMultiplierMap } from '@/lib/finance/cashback-display'
import { formatINR } from '@/lib/utils'
import type { CashbackMonthlyHistory, CashbackRuleDetail } from '@/view-models/finance'

function monthLabel(monthKey: string): string {
  const [year, month] = monthKey.split('-')
  const date = new Date(Number(year), Number(month) - 1, 1)
  return date.toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })
}

function MonthlyHistoryChart({ history }: { history: CashbackMonthlyHistory[] }) {
  const maxEarned = Math.max(...history.map((row) => row.earned), 1)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Monthly history</CardTitle>
        <p className="text-sm text-muted-foreground">Cashback earned through this rule over the last six months.</p>
      </CardHeader>
      <CardContent className="space-y-3">
        {history.map((row) => {
          const width = row.earned > 0 ? Math.max(8, (row.earned / maxEarned) * 100) : 0
          return (
            <div key={row.month} className="space-y-1">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>{monthLabel(row.month)}</span>
                <span className="font-medium text-foreground">{row.earned > 0 ? formatINR(row.earned) : '—'}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-muted">
                <div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${width}%` }} />
              </div>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}

function RuleSummary({ detail }: { detail: CashbackRuleDetail }) {
  const { rule } = detail

  return (
    <Card className="border-emerald-500/20 bg-gradient-to-br from-emerald-500/10 via-background to-background">
      <CardContent className="space-y-5 p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold">{rule.name}</h1>
            <p className="mt-1 flex items-center gap-1.5 text-sm text-muted-foreground">
              <Building2 className="size-4" />
              {detail.cardName}
            </p>
          </div>
          <CashbackStatusChip status={rule.status ?? 'active'} />
        </div>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard title="This month" value={formatINR(detail.earnedMonth)} tone="positive" />
          <MetricCard title="This year" value={formatINR(detail.earnedYear)} />
          <MetricCard title="Lifetime" value={formatINR(detail.earnedLifetime)} tone="positive" />
          <MetricCard
            title="Base rate"
            value={`${rule.flatRatePercent}%`}
            subtitle={rule.monthlyCap != null ? `Cap ${formatINR(rule.monthlyCap)}` : 'No monthly cap'}
          />
        </div>

        <div className="grid gap-3 text-sm sm:grid-cols-2">
          <div className="rounded-lg border border-border bg-muted/20 p-3">
            <p className="text-xs text-muted-foreground">Eligible card</p>
            <p className="mt-1 font-medium">{detail.programName}</p>
          </div>
          <div className="rounded-lg border border-border bg-muted/20 p-3">
            <p className="text-xs text-muted-foreground">Minimum spend</p>
            <p className="mt-1 font-medium">{formatINR(rule.minimumSpend)}</p>
          </div>
          {Object.keys(rule.categoryMultipliers).length > 0 ? (
            <div className="rounded-lg border border-border bg-muted/20 p-3 sm:col-span-2">
              <p className="text-xs text-muted-foreground">Category multipliers</p>
              <p className="mt-1 font-medium">{formatMultiplierMap(rule.categoryMultipliers)}</p>
            </div>
          ) : null}
          {rule.excludedCategoryNames.length > 0 ? (
            <div className="rounded-lg border border-border bg-muted/20 p-3">
              <p className="text-xs text-muted-foreground">Excluded categories</p>
              <p className="mt-1 font-medium">{rule.excludedCategoryNames.join(', ')}</p>
            </div>
          ) : null}
          {rule.excludedMerchantNames.length > 0 ? (
            <div className="rounded-lg border border-border bg-muted/20 p-3">
              <p className="text-xs text-muted-foreground">Excluded merchants</p>
              <p className="mt-1 font-medium">{rule.excludedMerchantNames.join(', ')}</p>
            </div>
          ) : null}
        </div>

        {rule.monthlyCap != null && detail.remainingCap != null ? (
          <>
            <UtilizationBar
              percent={Math.min(100, ((rule.monthlyCap - detail.remainingCap) / rule.monthlyCap) * 100)}
            />
            <p className="text-xs text-muted-foreground">
              {formatINR(detail.remainingCap)} of {formatINR(rule.monthlyCap)} monthly cap remaining
            </p>
          </>
        ) : null}
      </CardContent>
    </Card>
  )
}

export function FinanceCashbackDetailScreen() {
  const { ruleId } = useParams()
  const navigate = useNavigate()
  const parsedId = Number(ruleId)
  const detailQuery = useCashbackRuleDetail(Number.isFinite(parsedId) ? parsedId : null)

  if (!Number.isFinite(parsedId)) {
    return (
      <section>
        <ScreenHeader title="Cashback rule" description="Invalid rule id." />
        <Button variant="outline" size="sm" onClick={() => navigate('/finance/cashback')}>
          <ArrowLeft className="size-4" />
          Back to cashback
        </Button>
      </section>
    )
  }

  return (
    <section className="space-y-6">
      <div className="mb-2">
        <Button variant="ghost" size="sm" onClick={() => navigate('/finance/cashback')}>
          <ArrowLeft className="size-4" />
          Cashback
        </Button>
      </div>

      <QueryBoundary query={detailQuery} loadingMessage="Loading cashback rule…" emptyMessage="Rule not found.">
        {(detail) => (
          <>
            <RuleSummary detail={detail} />

            <div className="grid gap-4 xl:grid-cols-2">
              <MonthlyHistoryChart history={detail.monthlyHistory} />
              <CashbackActivityTimeline
                title="Recent earned events"
                events={detail.recentEvents.map((event) => ({
                  id: event.id,
                  programId: event.programId,
                  programName: detail.programName,
                  ruleId: detail.rule.id,
                  ruleName: detail.rule.name,
                  transactionId: event.transactionId,
                  transactionNote: event.note,
                  amount: event.amount / 100,
                  occurredOn: event.occurredOn,
                  note: event.note,
                }))}
                emptyMessage="No earned events for this rule yet."
              />
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Receipt className="size-4 text-emerald-400" />
                  Related transactions
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {detail.relatedTransactions.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No linked transactions for this rule yet.</p>
                ) : (
                  detail.relatedTransactions.map((txn) => (
                    <TransactionCard key={txn.id} transaction={txn} categories={[]} merchants={[]} readOnly />
                  ))
                )}
              </CardContent>
            </Card>

            {detail.rule.accountId ? (
              <div className="flex justify-end">
                <Link to={`/finance/credit-cards/${detail.rule.accountId}`}>
                  <Button variant="outline" size="sm">
                    View credit card
                  </Button>
                </Link>
              </div>
            ) : null}
          </>
        )}
      </QueryBoundary>
    </section>
  )
}
