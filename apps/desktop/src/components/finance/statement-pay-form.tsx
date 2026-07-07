import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { formatINR } from '@/lib/utils'
import type { FinanceAccount, FinanceStatement } from '@/view-models/finance'

const fieldClass = 'w-full rounded-md border border-border bg-background px-3 py-2 text-sm'

type PaymentMode = 'full' | 'minimum' | 'custom'

interface StatementPayFormProps {
  statement: FinanceStatement
  assetAccounts: FinanceAccount[]
  busy?: boolean
  onSubmit: (values: {
    fromAccountId: number
    paymentMode: 'full' | 'minimum' | 'partial'
    amount?: number
  }) => Promise<void>
  onCancel: () => void
}

export function StatementPayForm({
  statement,
  assetAccounts,
  busy = false,
  onSubmit,
  onCancel,
}: StatementPayFormProps) {
  const [fromAccountId, setFromAccountId] = useState<number | ''>(assetAccounts[0]?.id ?? '')
  const [mode, setMode] = useState<PaymentMode>('custom')
  const [amount, setAmount] = useState('')

  const remaining = statement.remainingDue ?? 0
  const minimum = statement.minDue ?? 0
  const canPayFull = remaining > 0 && statement.totalDue != null
  const canPayMinimum = minimum > 0 && (statement.paid ?? 0) < minimum

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!fromAccountId) return
    if (mode === 'full') {
      await onSubmit({ fromAccountId: Number(fromAccountId), paymentMode: 'full' })
      return
    }
    if (mode === 'minimum') {
      await onSubmit({ fromAccountId: Number(fromAccountId), paymentMode: 'minimum' })
      return
    }
    await onSubmit({
      fromAccountId: Number(fromAccountId),
      paymentMode: 'partial',
      amount: Number(amount),
    })
  }

  return (
    <form className="grid gap-3 rounded-md border border-border bg-muted/20 p-4" onSubmit={handleSubmit}>
      <p className="text-sm font-medium">Pay statement</p>
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          size="sm"
          variant={mode === 'full' ? 'default' : 'outline'}
          disabled={!canPayFull}
          onClick={() => setMode('full')}
        >
          Pay full · {formatINR(remaining)}
        </Button>
        <Button
          type="button"
          size="sm"
          variant={mode === 'minimum' ? 'default' : 'outline'}
          disabled={!canPayMinimum}
          onClick={() => setMode('minimum')}
        >
          Pay minimum · {formatINR(Math.max(minimum - (statement.paid ?? 0), 0))}
        </Button>
        <Button
          type="button"
          size="sm"
          variant={mode === 'custom' ? 'default' : 'outline'}
          onClick={() => setMode('custom')}
        >
          Custom amount
        </Button>
      </div>
      <label className="space-y-1">
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
              {account.name} · {account.balance != null ? formatINR(account.balance) : '—'}
            </option>
          ))}
        </select>
      </label>
      {mode === 'custom' ? (
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
      ) : null}
      <div className="flex gap-2">
        <Button type="submit" size="sm" disabled={busy || assetAccounts.length === 0}>
          Confirm payment
        </Button>
        <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
          Cancel
        </Button>
      </div>
      {assetAccounts.length === 0 ? (
        <p className="text-xs text-amber-400">Add a bank or cash account to pay this statement.</p>
      ) : null}
    </form>
  )
}
