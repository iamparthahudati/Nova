import { useState } from 'react'
import { Button } from '@/components/ui/button'
import type { FinanceAccount } from '@/view-models/finance'

const fieldClass = 'w-full rounded-md border border-border bg-background px-3 py-2 text-sm'

interface CreditCardPayFormProps {
  cardAccountId: number
  assetAccounts: FinanceAccount[]
  defaultAmount?: number | null
  statementId?: number | null
  busy?: boolean
  onSubmit: (values: {
    fromAccountId: number
    amount: number
    occurredOn: string
    statementId?: number | null
  }) => Promise<void>
  onCancel: () => void
}

export function CreditCardPayForm({
  cardAccountId,
  assetAccounts,
  defaultAmount,
  statementId,
  busy = false,
  onSubmit,
  onCancel,
}: CreditCardPayFormProps) {
  const [fromAccountId, setFromAccountId] = useState<number | ''>(assetAccounts[0]?.id ?? '')
  const [amount, setAmount] = useState(defaultAmount != null ? String(defaultAmount) : '')
  const [occurredOn, setOccurredOn] = useState(new Date().toISOString().slice(0, 10))

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!fromAccountId) return
    await onSubmit({
      fromAccountId: Number(fromAccountId),
      amount: Number(amount),
      occurredOn,
      statementId,
    })
  }

  return (
    <form className="grid gap-3 rounded-md border border-border bg-muted/20 p-3 sm:grid-cols-2" onSubmit={handleSubmit}>
      <input type="hidden" value={cardAccountId} readOnly />
      <label className="space-y-1 sm:col-span-2">
        <span className="text-xs text-muted-foreground">Pay from</span>
        <select
          className={fieldClass}
          value={fromAccountId}
          onChange={(e) => setFromAccountId(Number(e.target.value))}
          required
        >
          <option value="">Select account</option>
          {assetAccounts.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name} · {account.balance != null ? `₹${account.balance}` : '—'}
            </option>
          ))}
        </select>
      </label>
      <label className="space-y-1">
        <span className="text-xs text-muted-foreground">Amount</span>
        <input
          type="number"
          min="0.01"
          step="0.01"
          className={fieldClass}
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          required
        />
      </label>
      <label className="space-y-1">
        <span className="text-xs text-muted-foreground">Payment date</span>
        <input
          type="date"
          className={fieldClass}
          value={occurredOn}
          onChange={(e) => setOccurredOn(e.target.value)}
          required
        />
      </label>
      <div className="flex gap-2 sm:col-span-2">
        <Button type="submit" size="sm" disabled={busy || assetAccounts.length === 0}>
          Pay card
        </Button>
        <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
          Cancel
        </Button>
      </div>
      {assetAccounts.length === 0 ? (
        <p className="text-xs text-amber-400 sm:col-span-2">Add a bank or cash account to pay this card.</p>
      ) : null}
    </form>
  )
}
