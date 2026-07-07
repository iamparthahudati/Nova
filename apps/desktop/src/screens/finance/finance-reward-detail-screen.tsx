import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Building2, Receipt } from 'lucide-react'
import { RewardLedgerTimeline } from '@/components/finance/reward-ledger-timeline'
import { RewardStatusChip } from '@/components/finance/reward-status-chip'
import { TransactionCard } from '@/components/finance/transaction-card'
import { MetricCard, UtilizationBar } from '@/components/finance/metric-card'
import { ScreenHeader } from '@/components/layout/screen-header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { QueryBoundary } from '@/components/query-boundary'
import { useRewardProgramDetail } from '@/hooks/use-finance'
import {
  formatRewardAmount,
  formatRewardUnit,
  programBalanceDisplay,
} from '@/lib/finance/reward-display'
import { formatINR } from '@/lib/utils'
import type { RewardMonthlyHistory, RewardProgramDetail } from '@/view-models/finance'

function monthLabel(monthKey: string): string {
  const [year, month] = monthKey.split('-')
  const date = new Date(Number(year), Number(month) - 1, 1)
  return date.toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })
}

function BalanceHistoryChart({ history, unit }: { history: RewardMonthlyHistory[]; unit: string }) {
  const maxEarned = Math.max(...history.map((row) => row.earned), 1)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Balance history</CardTitle>
        <p className="text-sm text-muted-foreground">Monthly earned activity over the last six months.</p>
      </CardHeader>
      <CardContent className="space-y-3">
        {history.map((row) => {
          const width = row.earned > 0 ? Math.max(8, (row.earned / maxEarned) * 100) : 0
          return (
            <div key={row.month} className="space-y-1">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>{monthLabel(row.month)}</span>
                <span className="font-medium text-foreground">
                  {row.earned > 0 ? formatRewardAmount(row.earned, unit) : '—'}
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-emerald-500 transition-all"
                  style={{ width: `${width}%` }}
                />
              </div>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}

function ProgramSummary({ detail }: { detail: RewardProgramDetail }) {
  const { program } = detail

  return (
    <Card className="border-emerald-500/20 bg-gradient-to-br from-emerald-500/10 via-background to-background">
      <CardContent className="space-y-5 p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold">{program.name}</h1>
            <p className="mt-1 flex items-center gap-1.5 text-sm text-muted-foreground">
              <Building2 className="size-4" />
              {detail.bankName}
            </p>
          </div>
          <RewardStatusChip status={detail.status} />
        </div>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard title="Current balance" value={programBalanceDisplay(program)} tone="positive" />
          <MetricCard
            title="This month"
            value={formatRewardAmount(detail.earnedMonth, program.unit)}
          />
          <MetricCard title="This year" value={formatRewardAmount(detail.earnedYear, program.unit)} />
          <MetricCard
            title="Lifetime earned"
            value={formatRewardAmount(detail.earnedLifetime, program.unit)}
            tone="positive"
          />
        </div>

        <div className="grid gap-3 text-sm sm:grid-cols-2">
          <div className="rounded-lg border border-border bg-muted/20 p-3">
            <p className="text-xs text-muted-foreground">Reward unit</p>
            <p className="mt-1 font-medium">{formatRewardUnit(program.unit)}</p>
          </div>
          <div className="rounded-lg border border-border bg-muted/20 p-3">
            <p className="text-xs text-muted-foreground">Expiry policy</p>
            <p className="mt-1 font-medium">{program.expiryNote ?? 'Not specified'}</p>
          </div>
          {program.earnRateNote ? (
            <div className="rounded-lg border border-border bg-muted/20 p-3 sm:col-span-2">
              <p className="text-xs text-muted-foreground">Earn rate</p>
              <p className="mt-1 font-medium">{program.earnRateNote}</p>
            </div>
          ) : null}
        </div>

        <UtilizationBar
          percent={
            detail.balance.totalEarned > 0
              ? Math.min(100, (detail.balance.balance / detail.balance.totalEarned) * 100)
              : 0
          }
        />
        <p className="text-xs text-muted-foreground">
          {detail.balance.balance.toLocaleString('en-IN')} of{' '}
          {detail.balance.totalEarned.toLocaleString('en-IN')}{' '}
          {program.unit === 'cashback_minor' ? formatINR(detail.balance.totalEarned / 100) : 'pts'} still available
        </p>
      </CardContent>
    </Card>
  )
}

export function FinanceRewardDetailScreen() {
  const { programId } = useParams()
  const navigate = useNavigate()
  const parsedId = Number(programId)
  const detailQuery = useRewardProgramDetail(Number.isFinite(parsedId) ? parsedId : null)

  if (!Number.isFinite(parsedId)) {
    return (
      <section>
        <ScreenHeader title="Reward program" description="Invalid program id." />
        <Button variant="outline" size="sm" onClick={() => navigate('/finance/rewards')}>
          <ArrowLeft className="size-4" />
          Back to rewards
        </Button>
      </section>
    )
  }

  return (
    <section className="space-y-6">
      <div className="mb-2">
        <Button variant="ghost" size="sm" onClick={() => navigate('/finance/rewards')}>
          <ArrowLeft className="size-4" />
          Rewards
        </Button>
      </div>

      <QueryBoundary query={detailQuery} loadingMessage="Loading reward program…" emptyMessage="Program not found.">
        {(detail) => (
          <>
            <ProgramSummary detail={detail} />

            <div className="grid gap-4 xl:grid-cols-2">
              <BalanceHistoryChart history={detail.monthlyHistory} unit={detail.program.unit} />
              <RewardLedgerTimeline
                title="Recent activity"
                unit={detail.program.unit}
                events={detail.recentEvents.slice(0, 8)}
                emptyMessage="No recent reward events."
              />
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Receipt className="size-4 text-emerald-400" />
                  Related transactions
                </CardTitle>
                <p className="text-sm text-muted-foreground">
                  Spend transactions linked to reward events, when available.
                </p>
              </CardHeader>
              <CardContent className="space-y-2">
                {detail.relatedTransactions.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No linked transactions for this program yet.</p>
                ) : (
                  detail.relatedTransactions.map((txn) => (
                    <TransactionCard
                      key={txn.id}
                      transaction={txn}
                      categories={[]}
                      merchants={[]}
                      readOnly
                    />
                  ))
                )}
              </CardContent>
            </Card>

            <RewardLedgerTimeline
              title="Full ledger"
              unit={detail.program.unit}
              events={detail.recentEvents}
            />

            <div className="flex justify-end">
              <Link to={`/finance/credit-cards/${detail.program.accountId}`}>
                <Button variant="outline" size="sm">
                  View credit card
                </Button>
              </Link>
            </div>
          </>
        )}
      </QueryBoundary>
    </section>
  )
}
