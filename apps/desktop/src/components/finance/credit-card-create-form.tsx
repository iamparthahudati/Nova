import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const fieldClass = 'w-full rounded-md border border-border bg-background px-3 py-2 text-sm'

interface CreditCardCreateFormProps {
  busy?: boolean
  onSubmit: (values: {
    name: string
    creditLimit: string
    statementDay: string
    dueDayOffset: string
    network: string
    last4: string
    openingBalance: string
  }) => Promise<void>
  onCancel: () => void
}

export function CreditCardCreateForm({ busy = false, onSubmit, onCancel }: CreditCardCreateFormProps) {
  const [name, setName] = useState('')
  const [creditLimit, setCreditLimit] = useState('')
  const [statementDay, setStatementDay] = useState('15')
  const [dueDayOffset, setDueDayOffset] = useState('20')
  const [network, setNetwork] = useState('')
  const [last4, setLast4] = useState('')
  const [openingBalance, setOpeningBalance] = useState('0')

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    await onSubmit({
      name,
      creditLimit,
      statementDay,
      dueDayOffset,
      network,
      last4,
      openingBalance,
    })
    setName('')
    setCreditLimit('')
    setNetwork('')
    setLast4('')
    setOpeningBalance('0')
  }

  return (
    <Card className="mb-4">
      <CardHeader>
        <CardTitle>Add credit card</CardTitle>
      </CardHeader>
      <CardContent>
        <form className="grid gap-3 sm:grid-cols-2" onSubmit={handleSubmit}>
          <label className="space-y-1 sm:col-span-2">
            <span className="text-xs text-muted-foreground">Card name</span>
            <input
              className={fieldClass}
              placeholder="HDFC Millennia"
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
              className={fieldClass}
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
              className={fieldClass}
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
              className={fieldClass}
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
              className={fieldClass}
              value={dueDayOffset}
              onChange={(e) => setDueDayOffset(e.target.value)}
              required
            />
          </label>
          <label className="space-y-1">
            <span className="text-xs text-muted-foreground">Network</span>
            <input
              className={fieldClass}
              placeholder="Visa, Mastercard, RuPay…"
              value={network}
              onChange={(e) => setNetwork(e.target.value)}
            />
          </label>
          <label className="space-y-1">
            <span className="text-xs text-muted-foreground">Last 4 digits</span>
            <input
              className={fieldClass}
              maxLength={4}
              value={last4}
              onChange={(e) => setLast4(e.target.value)}
            />
          </label>
          <div className="flex items-end gap-2 sm:col-span-2">
            <Button type="submit" size="sm" disabled={busy}>
              Save card
            </Button>
            <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
