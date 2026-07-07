import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, CheckCircle2 } from 'lucide-react'
import { StatementPayForm } from '@/components/finance/statement-pay-form'
import { StatementSpendBreakdown } from '@/components/finance/statement-spend-breakdown'
import { StatementStatusChip } from '@/components/finance/statement-status-chip'
import { StatementTimeline } from '@/components/finance/statement-timeline'
import { TransactionCard } from '@/components/finance/transaction-card'
import { MetricCard, UtilizationBar } from '@/components/finance/metric-card'
import { ScreenHeader } from '@/components/layout/screen-header'
import { Button, buttonVariants } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { QueryBoundary } from '@/components/query-boundary'
import {
  useAccounts,
  useCategories,
  useCreditCards,
  useMerchants,
  useStatement,
} from '@/hooks/use-finance'
import { usePayStatement, useUpdateStatement } from '@/hooks/use-finance-mutations'
import { ApiError } from '@/lib/api-client'
import {
  aggregateSpendByCategory,
  aggregateSpendByMerchant,
  daysUntilDue,
  formatBillingPeriod,
  paymentProgressPercent,
  resolveDisplayStatus,
  statementMonthLabel,
} from '@/lib/finance/statement-display'
import { formatINR, formatShortDate, cn } from '@/lib/utils'

export function FinanceStatementDetailScreen() {
  const { statementId } = useParams()
  const navigate = useNavigate()
  const parsedId = Number(statementId)
  const statementQuery = useStatement(Number.isFinite(parsedId) ? parsedId : null)
  const cardsQuery = useCreditCards()
  const accountsQuery = useAccounts(false)
  const categoriesQuery = useCategories()
  const merchantsQuery = useMerchants()
  const payStatement = usePayStatement()
  const updateStatement = useUpdateStatement()
  const [showPayForm, setShowPayForm] = useState(false)
  const [showDuesForm, setShowDuesForm] = useState(false)
  const [totalDueInput, setTotalDueInput] = useState('')
  const [minDueInput, setMinDueInput] = useState('')
  const [feedback, setFeedback] = useState<string | null>(null)

  const assetAccounts = (accountsQuery.data ?? []).filter((account) => account.classification === 'asset')
  const busy = payStatement.isPending || updateStatement.isPending

  if (!Number.isFinite(parsedId)) {
    return (
      <section>
        <ScreenHeader title="Statement" description="Invalid statement id." />
        <Button variant="outline" size="sm" onClick={() => navigate('/finance/statements')}>
          <ArrowLeft className="size-4" />
          Back to statements
        </Button>
      </section>
    )
  }

  return (
    <section>
      <div className="mb-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/finance/statements')}>
          <ArrowLeft className="size-4" />
          Statements
        </Button>
      </div>

      <QueryBoundary
        query={statementQuery}
        loadingMessage="Loading statement…"
        emptyMessage="Statement not found."
      >
        {(statement) => {
          const card = cardsQuery.data?.find((item) => item.accountId === statement.accountId)
          const displayStatus = resolveDisplayStatus(statement)
          const transactions = statement.transactions ?? []
          const categoryRows = aggregateSpendByCategory(transactions)
          const merchantRows = aggregateSpendByMerchant(transactions)
          const daysLeft = daysUntilDue(statement.dueDate)
          const progress = paymentProgressPercent(statement)

          return (
            <>
              <ScreenHeader
                title={statementMonthLabel(statement.periodEnd)}
                description={
                  card
                    ? `${card.name} · ${formatBillingPeriod(statement.periodStart, statement.periodEnd)}`
                    : formatBillingPeriod(statement.periodStart, statement.periodEnd)
                }
                actions={
                  <div className="flex flex-wrap items-center gap-2">
                    <StatementStatusChip statement={statement} status={displayStatus} />
                    {displayStatus !== 'paid' ? (
                      <Button size="sm" onClick={() => setShowPayForm((open) => !open)}>
                        Pay statement
                      </Button>
                    ) : null}
                    <Button variant="ghost" size="sm" onClick={() => setShowDuesForm((open) => !open)}>
                      Set dues
                    </Button>
                  </div>
                }
              />

              {feedback ? (
                <div className="mb-4 flex items-start gap-2 rounded-md border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-300">
                  <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
                  <p>{feedback}</p>
                </div>
              ) : null}

              {showPayForm && displayStatus !== 'paid' ? (
                <div className="mb-4">
                  <StatementPayForm
                    statement={statement}
                    assetAccounts={assetAccounts}
                    busy={busy}
                    onCancel={() => setShowPayForm(false)}
                    onSubmit={async (values) => {
                      setFeedback(null)
                      try {
                        const result = await payStatement.mutateAsync({
                          statementId: statement.id,
                          input: {
                            from_account_id: values.fromAccountId,
                            payment_mode: values.paymentMode,
                            amount: values.amount,
                          },
                        })
                        setShowPayForm(false)
                        setFeedback(result.meta.message)
                      } catch (error) {
                        setFeedback(error instanceof ApiError ? error.message : 'Could not pay statement.')
                      }
                    }}
                  />
                </div>
              ) : null}

              {showDuesForm ? (
                <Card className="mb-4">
                  <CardHeader>
                    <CardTitle className="text-base">Statement dues</CardTitle>
                  </CardHeader>
                  <CardContent className="grid gap-3 sm:grid-cols-2">
                    <label className="space-y-1 text-sm">
                      <span className="text-xs text-muted-foreground">Total due</span>
                      <input
                        className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                        placeholder={statement.totalDue != null ? String(statement.totalDue) : 'Total due'}
                        value={totalDueInput}
                        onChange={(e) => setTotalDueInput(e.target.value)}
                      />
                    </label>
                    <label className="space-y-1 text-sm">
                      <span className="text-xs text-muted-foreground">Minimum due</span>
                      <input
                        className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                        placeholder={statement.minDue != null ? String(statement.minDue) : 'Min due'}
                        value={minDueInput}
                        onChange={(e) => setMinDueInput(e.target.value)}
                      />
                    </label>
                    <div className="flex gap-2 sm:col-span-2">
                      <Button
                        size="sm"
                        disabled={busy}
                        onClick={() =>
                          void (async () => {
                            setFeedback(null)
                            try {
                              const result = await updateStatement.mutateAsync({
                                statementId: statement.id,
                                input: {
                                  total_due: totalDueInput ? Number(totalDueInput) : undefined,
                                  min_due: minDueInput ? Number(minDueInput) : undefined,
                                },
                              })
                              setShowDuesForm(false)
                              setTotalDueInput('')
                              setMinDueInput('')
                              setFeedback(result.meta.message)
                            } catch (error) {
                              setFeedback(
                                error instanceof ApiError ? error.message : 'Could not update statement.',
                              )
                            }
                          })()
                        }
                      >
                        Save dues
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => setShowDuesForm(false)}>
                        Cancel
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ) : null}

              <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
                <div className="space-y-4">
                  <StatementTimeline statement={statement} />
                  <div className="grid gap-3 sm:grid-cols-2">
                    <MetricCard title="Total spend" value={formatINR(statement.spend ?? 0)} />
                    <MetricCard title="Total paid" value={formatINR(statement.paid ?? 0)} tone="positive" />
                    <MetricCard title="Remaining due" value={formatINR(statement.remainingDue ?? 0)} tone="negative" />
                    <MetricCard
                      title="Minimum due"
                      value={formatINR(statement.minDue ?? 0)}
                      subtitle={
                        daysLeft >= 0 && displayStatus !== 'paid'
                          ? daysLeft === 0
                            ? 'Due today'
                            : `${daysLeft} days remaining`
                          : undefined
                      }
                      tone={daysLeft <= 3 && displayStatus !== 'paid' ? 'warning' : 'default'}
                    />
                  </div>
                  {(statement.totalDue ?? 0) > 0 ? (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Payment progress</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <UtilizationBar percent={progress} />
                      </CardContent>
                    </Card>
                  ) : null}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Transactions</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {transactions.length === 0 ? (
                        <p className="text-sm text-muted-foreground">No transactions in this billing period.</p>
                      ) : (
                        transactions.map((transaction) => (
                          <TransactionCard
                            key={transaction.id}
                            transaction={transaction}
                            categories={categoriesQuery.data ?? []}
                            merchants={merchantsQuery.data ?? []}
                            readOnly
                          />
                        ))
                      )}
                    </CardContent>
                  </Card>
                </div>
                <div className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Statement summary</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2 text-sm">
                      <SummaryRow label="Statement date" value={formatShortDate(statement.statementDate)} />
                      <SummaryRow label="Due date" value={formatShortDate(statement.dueDate)} />
                      <SummaryRow label="Billing period" value={formatBillingPeriod(statement.periodStart, statement.periodEnd)} />
                      <SummaryRow label="Total due" value={formatINR(statement.totalDue ?? statement.spend ?? 0)} />
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Spend breakdown</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      <StatementSpendBreakdown
                        title="By category"
                        rows={categoryRows}
                        emptyMessage="No categorized spend on this statement."
                      />
                      <StatementSpendBreakdown
                        title="By merchant"
                        rows={merchantRows}
                        emptyMessage="No merchant-tagged spend on this statement."
                      />
                    </CardContent>
                  </Card>
                  {card ? (
                    <Link
                      to={`/finance/credit-cards/${card.accountId}`}
                      className={cn(buttonVariants({ variant: 'outline', size: 'sm' }), 'inline-flex')}
                    >
                      View credit card
                    </Link>
                  ) : null}
                </div>
              </div>
            </>
          )
        }}
      </QueryBoundary>
    </section>
  )
}

function SummaryRow({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-border/50 py-2 last:border-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value ?? '—'}</span>
    </div>
  )
}
