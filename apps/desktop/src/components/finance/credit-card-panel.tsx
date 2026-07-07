import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Pencil, Archive } from 'lucide-react'
import { ConfirmActionBar } from '@/components/finance/confirm-action-bar'
import { UtilizationBar } from '@/components/finance/metric-card'
import { Badge } from '@/components/ui/badge'
import { Button, buttonVariants } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useArchiveAccount, useUpdateCreditCard } from '@/hooks/use-finance-mutations'
import { ApiError } from '@/lib/api-client'
import { cn, formatINR } from '@/lib/utils'
import type { FinanceCreditCard } from '@/view-models/finance'

interface CreditCardPanelProps {
  card: FinanceCreditCard
  onFeedback: (message: string) => void
}

export function CreditCardPanel({ card, onFeedback }: CreditCardPanelProps) {
  const updateCreditCard = useUpdateCreditCard()
  const archiveAccount = useArchiveAccount()
  const [editing, setEditing] = useState(false)
  const [pendingArchive, setPendingArchive] = useState(false)
  const [name, setName] = useState(card.name)
  const [creditLimit, setCreditLimit] = useState(String(card.creditLimit))
  const [statementDay, setStatementDay] = useState(String(card.statementDay))
  const [dueDayOffset, setDueDayOffset] = useState(String(card.dueDayOffset))
  const [network, setNetwork] = useState(card.network ?? '')
  const [last4, setLast4] = useState(card.last4 ?? '')
  const [autopay, setAutopay] = useState(card.autopay)

  async function handleUpdate(event: React.FormEvent) {
    event.preventDefault()
    try {
      const result = await updateCreditCard.mutateAsync({
        accountId: card.accountId,
        input: {
          name,
          credit_limit: Number(creditLimit),
          statement_day: Number(statementDay),
          due_day_offset: Number(dueDayOffset),
          network: network || null,
          last4: last4 || null,
          autopay,
        },
      })
      onFeedback(result.meta.message)
      setEditing(false)
    } catch (error) {
      onFeedback(error instanceof ApiError ? error.message : 'Could not update credit card.')
    }
  }

  async function handleArchive() {
    try {
      const result = await archiveAccount.mutateAsync(card.accountId)
      onFeedback(result.meta.message)
      setPendingArchive(false)
    } catch (error) {
      onFeedback(error instanceof ApiError ? error.message : 'Could not archive credit card.')
    }
  }

  if (card.archivedAt) {
    return (
      <Card className="opacity-60">
        <CardContent className="flex items-center justify-between p-4">
          <div>
            <p className="font-medium">{card.name}</p>
            <Badge className="mt-1">Archived</Badge>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div>
            <CardTitle>{card.name}</CardTitle>
            {card.network ? <p className="text-xs text-muted-foreground">{card.network}</p> : null}
          </div>
          <div className="flex items-center gap-2">
            {card.last4 ? <Badge variant="outline">•••• {card.last4}</Badge> : null}
            <Button variant="ghost" size="icon" className="size-8" onClick={() => setEditing((v) => !v)}>
              <Pencil className="size-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="size-8 text-muted-foreground hover:text-destructive"
              disabled={archiveAccount.isPending}
              onClick={() => setPendingArchive(true)}
            >
              <Archive className="size-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {pendingArchive ? (
          <ConfirmActionBar
            message={`Archive ${card.name}? This card will no longer appear in active lists.`}
            confirmLabel="Archive"
            destructive
            busy={archiveAccount.isPending}
            onCancel={() => setPendingArchive(false)}
            onConfirm={() => void handleArchive()}
          />
        ) : null}
        {editing ? (
          <form className="grid gap-3 sm:grid-cols-2" onSubmit={handleUpdate}>
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
              <span className="text-xs text-muted-foreground">Statement day</span>
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
              <span className="text-xs text-muted-foreground">Due day offset</span>
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
            <label className="flex items-center gap-2 sm:col-span-2">
              <input type="checkbox" checked={autopay} onChange={(e) => setAutopay(e.target.checked)} />
              <span className="text-sm">Autopay enabled</span>
            </label>
            <div className="flex gap-2 sm:col-span-2">
              <Button type="submit" size="sm" disabled={updateCreditCard.isPending}>
                Save changes
              </Button>
              <Button type="button" variant="ghost" size="sm" onClick={() => setEditing(false)}>
                Cancel
              </Button>
            </div>
          </form>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-muted-foreground">Credit limit</p>
                <p className="font-semibold">{formatINR(card.creditLimit)}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Available limit</p>
                <p className="font-semibold">{formatINR(card.availableLimit ?? 0)}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Current utilization</p>
                <p className="font-semibold text-rose-400">{formatINR(card.outstanding ?? 0)}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Billing cycle</p>
                <p className="font-semibold">
                  Day {card.statementDay} · due +{card.dueDayOffset}d
                </p>
              </div>
            </div>
            {card.autopay ? <Badge variant="secondary">Autopay on</Badge> : null}
            <UtilizationBar percent={card.utilizationPercent ?? 0} />
            {card.currentStatement ? (
              <div className="rounded-md border border-border bg-muted/20 p-3 text-sm">
                <p className="font-medium">Current statement</p>
                <p className="text-muted-foreground">
                  {card.currentStatement.periodStart} → {card.currentStatement.periodEnd}
                </p>
                <p className="text-xs text-muted-foreground">Due {card.currentStatement.dueDate}</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <Badge variant="outline">{card.currentStatement.status}</Badge>
                  {card.currentStatement.remainingDue != null ? (
                    <span>Remaining {formatINR(card.currentStatement.remainingDue)}</span>
                  ) : null}
                </div>
              </div>
            ) : null}
            {card.previousStatement ? (
              <div className="rounded-md border border-dashed border-border p-3 text-sm text-muted-foreground">
                <p className="font-medium text-foreground">Previous statement</p>
                <p>
                  {card.previousStatement.periodStart} → {card.previousStatement.periodEnd} ·{' '}
                  {card.previousStatement.status}
                </p>
              </div>
            ) : null}
            <div className="flex flex-wrap gap-2 pt-1">
              <Link
                to={`/finance/statements?accountId=${card.accountId}`}
                className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}
              >
                Statement history
              </Link>
              <Link
                to={`/finance/transactions?accountId=${card.accountId}`}
                className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}
              >
                Transactions
              </Link>
              <Link to="/finance/rewards" className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}>
                Rewards
              </Link>
              <Link to="/finance/cashback" className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}>
                Cashback
              </Link>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
