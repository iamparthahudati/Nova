import { useState } from 'react'
import { ScreenHeader } from '@/components/layout/screen-header'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { QueryBoundary } from '@/components/query-boundary'
import { useAccounts, useCreditCards, useStatements } from '@/hooks/use-finance'
import { usePayStatement, useUpdateStatement } from '@/hooks/use-finance-mutations'
import { ApiError } from '@/lib/api-client'
import { formatINR } from '@/lib/utils'

export function FinanceStatementsScreen() {
  const accountsQuery = useAccounts(false)
  const cardsQuery = useCreditCards()
  const cardAccountIds = new Set((cardsQuery.data ?? []).map((c) => c.accountId))
  const cardAccounts = (accountsQuery.data ?? []).filter((a) => cardAccountIds.has(a.id))
  const assetAccounts = (accountsQuery.data ?? []).filter((a) => a.classification === 'asset')
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null)
  const activeAccountId = selectedAccountId ?? cardAccounts[0]?.id ?? null
  const statements = useStatements(activeAccountId)
  const payStatement = usePayStatement()
  const updateStatement = useUpdateStatement()
  const [feedback, setFeedback] = useState<string | null>(null)

  async function handlePay(statementId: number, amount: string, fromAccountId: number) {
    setFeedback(null)
    try {
      const result = await payStatement.mutateAsync({
        statementId,
        input: {
          from_account_id: fromAccountId,
          payment_mode: 'partial',
          amount: Number(amount),
        },
      })
      setFeedback(result.meta.message)
    } catch (error) {
      setFeedback(error instanceof ApiError ? error.message : 'Could not pay statement.')
    }
  }

  async function handleSetTotals(statementId: number, totalDue: string, minDue: string) {
    setFeedback(null)
    try {
      const result = await updateStatement.mutateAsync({
        statementId,
        input: {
          total_due: totalDue ? Number(totalDue) : undefined,
          min_due: minDue ? Number(minDue) : undefined,
        },
      })
      setFeedback(result.meta.message)
    } catch (error) {
      setFeedback(error instanceof ApiError ? error.message : 'Could not update statement.')
    }
  }

  return (
    <section>
      <ScreenHeader title="Statements" description="Statement summaries with spend, payments, and status." />
      <div className="mb-4">
        <select
          className="rounded-md border border-border bg-background px-3 py-2 text-sm"
          value={activeAccountId ?? ''}
          onChange={(e) => setSelectedAccountId(Number(e.target.value))}
        >
          {cardAccounts.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name}
            </option>
          ))}
        </select>
      </div>
      {feedback ? <p className="mb-4 text-sm text-emerald-400">{feedback}</p> : null}
      <QueryBoundary
        query={statements}
        loadingMessage="Loading statements…"
        emptyMessage="No statements for this card."
      >
        {(data) => (
          <div className="space-y-3">
            {data.map((statement) => (
              <Card key={statement.id}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">
                      {statement.periodStart} → {statement.periodEnd}
                    </CardTitle>
                    <Badge variant="outline">{statement.status}</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">Due {statement.dueDate}</p>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-3 text-sm">
                    <div>
                      <p className="text-muted-foreground">Spend</p>
                      <p className="font-semibold">{formatINR(statement.spend ?? 0)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Paid</p>
                      <p className="font-semibold">{formatINR(statement.paid ?? 0)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Remaining</p>
                      <p className="font-semibold">{formatINR(statement.remainingDue ?? 0)}</p>
                    </div>
                  </div>
                  <div className="mt-4 grid gap-2 sm:grid-cols-4">
                    <input
                      className="rounded-md border border-border bg-background px-2 py-1 text-sm"
                      placeholder="Total due"
                      id={`total-${statement.id}`}
                    />
                    <input
                      className="rounded-md border border-border bg-background px-2 py-1 text-sm"
                      placeholder="Min due"
                      id={`min-${statement.id}`}
                    />
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        const totalDue = (document.getElementById(`total-${statement.id}`) as HTMLInputElement).value
                        const minDue = (document.getElementById(`min-${statement.id}`) as HTMLInputElement).value
                        void handleSetTotals(statement.id, totalDue, minDue)
                      }}
                    >
                      Set dues
                    </Button>
                  </div>
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    <select
                      className="rounded-md border border-border bg-background px-2 py-1 text-sm"
                      id={`from-${statement.id}`}
                    >
                      {assetAccounts.map((account) => (
                        <option key={account.id} value={account.id}>
                          {account.name}
                        </option>
                      ))}
                    </select>
                    <input
                      type="number"
                      min="0.01"
                      step="0.01"
                      className="w-28 rounded-md border border-border bg-background px-2 py-1 text-sm"
                      placeholder="Amount"
                      id={`pay-${statement.id}`}
                    />
                    <Button
                      size="sm"
                      disabled={payStatement.isPending}
                      onClick={() => {
                        const fromAccountId = Number(
                          (document.getElementById(`from-${statement.id}`) as HTMLSelectElement).value,
                        )
                        const amount = (document.getElementById(`pay-${statement.id}`) as HTMLInputElement).value
                        void handlePay(statement.id, amount, fromAccountId)
                      }}
                    >
                      Pay
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </QueryBoundary>
    </section>
  )
}
