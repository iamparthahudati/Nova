import { useState } from 'react'
import { TaxonomySelectField } from '@/components/finance/taxonomy-select-field'
import { Button } from '@/components/ui/button'
import type { FinanceCategory, FinanceMerchant } from '@/view-models/finance'

const fieldClass = 'w-full rounded-md border border-border bg-background px-3 py-2 text-sm'

interface CreditCardExpenseFormProps {
  accountId: number
  categories: FinanceCategory[]
  merchants: FinanceMerchant[]
  busy?: boolean
  onSubmit: (values: {
    amount: number
    occurredOn: string
    note: string
    categoryId?: number
    merchantId?: number
  }) => Promise<void>
  onCancel: () => void
  onCreateCategory: (name: string) => Promise<{ id: number }>
  onCreateMerchant: (name: string) => Promise<{ id: number }>
}

export function CreditCardExpenseForm({
  accountId,
  categories,
  merchants,
  busy = false,
  onSubmit,
  onCancel,
  onCreateCategory,
  onCreateMerchant,
}: CreditCardExpenseFormProps) {
  const [amount, setAmount] = useState('')
  const [occurredOn, setOccurredOn] = useState(new Date().toISOString().slice(0, 10))
  const [note, setNote] = useState('')
  const [categoryId, setCategoryId] = useState<number | ''>('')
  const [merchantId, setMerchantId] = useState<number | ''>('')

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    await onSubmit({
      amount: Number(amount),
      occurredOn,
      note,
      categoryId: categoryId ? Number(categoryId) : undefined,
      merchantId: merchantId ? Number(merchantId) : undefined,
    })
    setAmount('')
    setNote('')
  }

  return (
    <form className="grid gap-3 rounded-md border border-border bg-muted/20 p-3 sm:grid-cols-2" onSubmit={handleSubmit}>
      <input type="hidden" value={accountId} readOnly />
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
        <span className="text-xs text-muted-foreground">Date</span>
        <input
          type="date"
          className={fieldClass}
          value={occurredOn}
          onChange={(e) => setOccurredOn(e.target.value)}
          required
        />
      </label>
      <div className="sm:col-span-2">
        <TaxonomySelectField
          label="Category"
          placeholder="Select category"
          emptyLabel="No categories yet"
          addLabel="Add category"
          value={categoryId}
          options={categories}
          onChange={setCategoryId}
          onCreate={onCreateCategory}
        />
      </div>
      <div className="sm:col-span-2">
        <TaxonomySelectField
          label="Merchant"
          placeholder="Select merchant"
          emptyLabel="No merchants yet"
          addLabel="Add merchant"
          value={merchantId}
          options={merchants}
          onChange={setMerchantId}
          onCreate={onCreateMerchant}
        />
      </div>
      <label className="space-y-1 sm:col-span-2">
        <span className="text-xs text-muted-foreground">Note</span>
        <input className={fieldClass} value={note} onChange={(e) => setNote(e.target.value)} />
      </label>
      <div className="flex gap-2 sm:col-span-2">
        <Button type="submit" size="sm" disabled={busy}>
          Add expense
        </Button>
        <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  )
}
