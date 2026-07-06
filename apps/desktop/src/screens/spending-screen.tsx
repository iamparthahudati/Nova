import { useState } from 'react'
import { Plus } from 'lucide-react'
import { ScreenHeader } from '@/components/layout/screen-header'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { QueryBoundary } from '@/components/query-boundary'
import { useLogSpending } from '@/hooks/use-spending-mutations'
import { useSpending } from '@/hooks/use-spending'
import { ApiError } from '@/lib/api-client'
import { formatINR } from '@/lib/utils'

export function SpendingScreen() {
  const spending = useSpending()
  const logSpending = useLogSpending()
  const [showAddForm, setShowAddForm] = useState(false)
  const [type, setType] = useState<'earned' | 'spent'>('spent')
  const [amount, setAmount] = useState('')
  const [note, setNote] = useState('')
  const [feedback, setFeedback] = useState<{ tone: 'success' | 'error'; message: string } | null>(null)

  const pending = logSpending.isPending

  async function handleLog(event: React.FormEvent) {
    event.preventDefault()
    setFeedback(null)
    const parsedAmount = Number(amount)
    if (!Number.isFinite(parsedAmount) || parsedAmount <= 0) {
      return
    }
    try {
      const result = await logSpending.mutateAsync({
        type,
        amount: parsedAmount,
        note: note.trim() || undefined,
      })
      setAmount('')
      setNote('')
      setShowAddForm(false)
      setFeedback({ tone: 'success', message: result.meta?.message ?? 'Transaction logged.' })
    } catch (error) {
      setFeedback({
        tone: 'error',
        message: error instanceof ApiError ? error.message : 'Could not log transaction.',
      })
    }
  }

  return (
    <section>
      <ScreenHeader
        title="Spending"
        description="Income and expenses from the backend spending endpoint."
        actions={
          <Button
            type="button"
            variant={showAddForm ? 'secondary' : 'default'}
            size="sm"
            disabled={pending}
            onClick={() => setShowAddForm((open) => !open)}
          >
            <Plus className="h-4 w-4" />
            Log transaction
          </Button>
        }
      />

      {feedback ? (
        <p
          className={`mb-4 text-sm ${feedback.tone === 'success' ? 'text-emerald-400' : 'text-rose-400'}`}
          role="status"
        >
          {feedback.message}
        </p>
      ) : null}

      {showAddForm ? (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>New transaction</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="space-y-3" onSubmit={handleLog}>
              <label className="block space-y-1">
                <span className="text-xs text-muted-foreground">Type</span>
                <select
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  value={type}
                  onChange={(event) => setType(event.target.value as 'earned' | 'spent')}
                  disabled={pending}
                >
                  <option value="spent">Expense</option>
                  <option value="earned">Income</option>
                </select>
              </label>
              <label className="block space-y-1">
                <span className="text-xs text-muted-foreground">Amount</span>
                <input
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  type="number"
                  min="0"
                  step="0.01"
                  value={amount}
                  onChange={(event) => setAmount(event.target.value)}
                  placeholder="0.00"
                  disabled={pending}
                  autoFocus
                />
              </label>
              <label className="block space-y-1">
                <span className="text-xs text-muted-foreground">Note (optional)</span>
                <input
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  value={note}
                  onChange={(event) => setNote(event.target.value)}
                  placeholder="What was this for?"
                  disabled={pending}
                />
              </label>
              <div className="flex gap-2">
                <Button
                  type="submit"
                  size="sm"
                  disabled={pending || !amount || Number(amount) <= 0}
                >
                  {logSpending.isPending ? 'Saving…' : 'Save transaction'}
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  disabled={pending}
                  onClick={() => setShowAddForm(false)}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      ) : null}

      <QueryBoundary
        query={spending}
        isEmpty={(data) => data.transactions.length === 0 && data.earnedMonth === 0 && data.spentMonth === 0}
        loadingMessage="Loading spending data…"
        emptyMessage="No spending data available."
      >
        {(data) => (
          <>
            <div className="mb-4 grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Total earned</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-semibold text-emerald-400">{formatINR(data.earnedMonth)}</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Total spent</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-semibold text-rose-400">{formatINR(data.spentMonth)}</p>
                </CardContent>
              </Card>
            </div>
            <Card>
              <CardHeader>
                <CardTitle>Transactions</CardTitle>
              </CardHeader>
              <CardContent>
                {data.transactions.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No transactions this month.</p>
                ) : (
                  <div className="space-y-2">
                    {data.transactions.map((entry) => (
                      <div
                        key={entry.id}
                        className="flex items-center justify-between rounded-md border border-border bg-muted/30 p-3"
                      >
                        <div>
                          <p className="text-sm font-medium">{entry.note || 'Untitled transaction'}</p>
                          <p className="text-xs text-muted-foreground">{new Date(entry.createdAt).toLocaleString()}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant={entry.type === 'earned' ? 'default' : 'secondary'}>{entry.type}</Badge>
                          <p className="text-sm font-semibold">{formatINR(entry.amount)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </QueryBoundary>
    </section>
  )
}
