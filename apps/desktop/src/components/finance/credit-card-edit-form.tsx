import { useState } from 'react'
import { Button } from '@/components/ui/button'
import type { FinanceCreditCard } from '@/view-models/finance'

const fieldClass = 'w-full rounded-md border border-border bg-background px-3 py-2 text-sm'

interface CreditCardEditFormProps {
  card: FinanceCreditCard
  busy?: boolean
  onSubmit: (input: {
    name: string
    credit_limit: number
    statement_day: number
    due_day_offset: number
    network: string | null
    last4: string | null
    autopay: boolean
  }) => Promise<void>
  onCancel: () => void
}

export function CreditCardEditForm({ card, busy = false, onSubmit, onCancel }: CreditCardEditFormProps) {
  const [name, setName] = useState(card.name)
  const [creditLimit, setCreditLimit] = useState(String(card.creditLimit))
  const [statementDay, setStatementDay] = useState(String(card.statementDay))
  const [dueDayOffset, setDueDayOffset] = useState(String(card.dueDayOffset))
  const [network, setNetwork] = useState(card.network ?? '')
  const [last4, setLast4] = useState(card.last4 ?? '')
  const [autopay, setAutopay] = useState(card.autopay)

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    await onSubmit({
      name,
      credit_limit: Number(creditLimit),
      statement_day: Number(statementDay),
      due_day_offset: Number(dueDayOffset),
      network: network || null,
      last4: last4 || null,
      autopay,
    })
  }

  return (
    <form className="grid gap-3 border-t border-border pt-4 sm:grid-cols-2" onSubmit={handleSubmit}>
      <label className="space-y-1 sm:col-span-2">
        <span className="text-xs text-muted-foreground">Card name</span>
        <input className={fieldClass} value={name} onChange={(e) => setName(e.target.value)} required />
      </label>
      <label className="space-y-1">
        <span className="text-xs text-muted-foreground">Credit limit</span>
        <input
          type="number"
          min="1"
          step="0.01"
          className={fieldClass}
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
          className={fieldClass}
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
          className={fieldClass}
          value={dueDayOffset}
          onChange={(e) => setDueDayOffset(e.target.value)}
          required
        />
      </label>
      <label className="space-y-1">
        <span className="text-xs text-muted-foreground">Network</span>
        <input className={fieldClass} value={network} onChange={(e) => setNetwork(e.target.value)} />
      </label>
      <label className="space-y-1">
        <span className="text-xs text-muted-foreground">Last 4 digits</span>
        <input className={fieldClass} maxLength={4} value={last4} onChange={(e) => setLast4(e.target.value)} />
      </label>
      <label className="flex items-center gap-2 sm:col-span-2">
        <input type="checkbox" checked={autopay} onChange={(e) => setAutopay(e.target.checked)} />
        <span className="text-sm">Autopay enabled</span>
      </label>
      <div className="flex gap-2 sm:col-span-2">
        <Button type="submit" size="sm" disabled={busy}>
          Save changes
        </Button>
        <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  )
}
