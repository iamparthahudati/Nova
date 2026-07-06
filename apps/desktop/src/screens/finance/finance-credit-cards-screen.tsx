import { useState } from 'react'
import { Plus } from 'lucide-react'
import { ScreenHeader } from '@/components/layout/screen-header'
import { UtilizationBar } from '@/components/finance/metric-card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { QueryBoundary } from '@/components/query-boundary'
import { useCreditCards } from '@/hooks/use-finance'
import { useCreateCreditCard } from '@/hooks/use-finance-mutations'
import { ApiError } from '@/lib/api-client'
import { formatINR } from '@/lib/utils'

export function FinanceCreditCardsScreen() {
  const cards = useCreditCards()
  const createCreditCard = useCreateCreditCard()
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [creditLimit, setCreditLimit] = useState('')
  const [statementDay, setStatementDay] = useState('15')
  const [dueDayOffset, setDueDayOffset] = useState('20')
  const [network, setNetwork] = useState('')
  const [last4, setLast4] = useState('')
  const [openingBalance, setOpeningBalance] = useState('0')
  const [feedback, setFeedback] = useState<string | null>(null)

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault()
    setFeedback(null)
    try {
      const result = await createCreditCard.mutateAsync({
        name,
        credit_limit: Number(creditLimit),
        statement_day: Number(statementDay),
        due_day_offset: Number(dueDayOffset),
        opening_balance: Number(openingBalance) || 0,
        network: network || undefined,
        last4: last4 || undefined,
      })
      setName('')
      setCreditLimit('')
      setNetwork('')
      setLast4('')
      setOpeningBalance('0')
      setShowForm(false)
      setFeedback(result.meta.message)
    } catch (error) {
      setFeedback(error instanceof ApiError ? error.message : 'Could not create credit card.')
    }
  }

  return (
    <section>
      <ScreenHeader
        title="Credit Cards"
        description="Limits, utilization, and billing cycles from projections."
        actions={
          <Button size="sm" onClick={() => setShowForm((open) => !open)}>
            <Plus className="h-4 w-4" />
            Add card
          </Button>
        }
      />
      {feedback ? <p className="mb-4 text-sm text-emerald-400">{feedback}</p> : null}
      {showForm ? (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>Add credit card</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="grid gap-3 sm:grid-cols-2" onSubmit={handleCreate}>
              <label className="space-y-1 sm:col-span-2">
                <span className="text-xs text-muted-foreground">Card name</span>
                <input
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </label>
              <label className="space-y-1">
                <span className="text-xs text-muted-foreground">Credit limit</span>
                <input
                  type="number"
                  min="1"
                  step="0.01"
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  value={creditLimit}
                  onChange={(e) => setCreditLimit(e.target.value)}
                  required
                />
              </label>
              <label className="space-y-1">
                <span className="text-xs text-muted-foreground">Opening balance</span>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  value={openingBalance}
                  onChange={(e) => setOpeningBalance(e.target.value)}
                />
              </label>
              <label className="space-y-1">
                <span className="text-xs text-muted-foreground">Statement day (1–28)</span>
                <input
                  type="number"
                  min="1"
                  max="28"
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  value={statementDay}
                  onChange={(e) => setStatementDay(e.target.value)}
                  required
                />
              </label>
              <label className="space-y-1">
                <span className="text-xs text-muted-foreground">Due day offset (1–45)</span>
                <input
                  type="number"
                  min="1"
                  max="45"
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  value={dueDayOffset}
                  onChange={(e) => setDueDayOffset(e.target.value)}
                  required
                />
              </label>
              <label className="space-y-1">
                <span className="text-xs text-muted-foreground">Network</span>
                <input
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  placeholder="Visa, Mastercard…"
                  value={network}
                  onChange={(e) => setNetwork(e.target.value)}
                />
              </label>
              <label className="space-y-1">
                <span className="text-xs text-muted-foreground">Last 4 digits</span>
                <input
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  maxLength={4}
                  value={last4}
                  onChange={(e) => setLast4(e.target.value)}
                />
              </label>
              <div className="flex items-end gap-2 sm:col-span-2">
                <Button type="submit" size="sm" disabled={createCreditCard.isPending}>
                  Save
                </Button>
                <Button type="button" variant="ghost" size="sm" onClick={() => setShowForm(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      ) : null}
      <QueryBoundary query={cards} loadingMessage="Loading credit cards…" emptyMessage="No credit cards yet.">
        {(data) => (
          <div className="grid gap-4 xl:grid-cols-2">
            {data.map((card) => (
              <Card key={card.accountId}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>{card.name}</CardTitle>
                    {card.last4 ? <Badge variant="outline">•••• {card.last4}</Badge> : null}
                  </div>
                  {card.network ? <p className="text-xs text-muted-foreground">{card.network}</p> : null}
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-muted-foreground">Credit limit</p>
                      <p className="font-semibold">{formatINR(card.creditLimit)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Available</p>
                      <p className="font-semibold">{formatINR(card.availableLimit ?? 0)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Outstanding</p>
                      <p className="font-semibold text-rose-400">{formatINR(card.outstanding ?? 0)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Billing cycle</p>
                      <p className="font-semibold">
                        Day {card.statementDay} · due +{card.dueDayOffset}d
                      </p>
                    </div>
                  </div>
                  <UtilizationBar percent={card.utilizationPercent ?? 0} />
                  {card.currentStatement ? (
                    <div className="rounded-md border border-border bg-muted/20 p-3 text-sm">
                      <p className="font-medium">Current statement</p>
                      <p className="text-muted-foreground">
                        {card.currentStatement.periodStart} → {card.currentStatement.periodEnd}
                      </p>
                      <div className="mt-2 flex gap-2">
                        <Badge variant="outline">{card.currentStatement.status}</Badge>
                        {card.currentStatement.remainingDue != null ? (
                          <span>Due {formatINR(card.currentStatement.remainingDue)}</span>
                        ) : null}
                      </div>
                    </div>
                  ) : null}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </QueryBoundary>
    </section>
  )
}
