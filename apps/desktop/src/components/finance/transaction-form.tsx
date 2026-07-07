import { useMemo, useState } from 'react'
import { TaxonomySelectField } from '@/components/finance/taxonomy-select-field'
import { Button } from '@/components/ui/button'
import { TRANSACTION_KINDS } from '@/lib/finance/transaction-kinds'
import type { FinanceAccount, FinanceCategory, FinanceMerchant } from '@/view-models/finance'

export interface TransactionFormValues {
  accountId: number | ''
  kind: string
  amount: string
  occurredOn: string
  note: string
  categoryId: number | ''
  merchantId: number | ''
}

interface TransactionFormProps {
  mode: 'create' | 'edit'
  values: TransactionFormValues
  accounts: FinanceAccount[]
  categories: FinanceCategory[]
  merchants: FinanceMerchant[]
  busy?: boolean
  onChange: (values: TransactionFormValues) => void
  onSubmit: (values: TransactionFormValues) => Promise<void>
  onCancel: () => void
  onCreateCategory: (name: string) => Promise<{ id: number }>
  onCreateMerchant: (name: string) => Promise<{ id: number }>
}

function validate(values: TransactionFormValues, mode: 'create' | 'edit'): Record<string, string> {
  const errors: Record<string, string> = {}
  if (mode === 'create' && !values.accountId) {
    errors.accountId = 'Select an account.'
  }
  const amount = Number(values.amount)
  if (!values.amount.trim()) {
    errors.amount = 'Amount is required.'
  } else if (!Number.isFinite(amount) || amount <= 0) {
    errors.amount = 'Amount must be greater than zero.'
  }
  if (!values.occurredOn) {
    errors.occurredOn = 'Date is required.'
  }
  return errors
}

const fieldClass = 'w-full rounded-md border border-border bg-background px-3 py-2 text-sm'
const errorClass = 'border-destructive/60 focus-visible:ring-destructive/40'

export function TransactionForm({
  mode,
  values,
  accounts,
  categories,
  merchants,
  busy = false,
  onChange,
  onSubmit,
  onCancel,
  onCreateCategory,
  onCreateMerchant,
}: TransactionFormProps) {
  const [touched, setTouched] = useState<Record<string, boolean>>({})
  const errors = useMemo(() => validate(values, mode), [values, mode])

  function patch(partial: Partial<TransactionFormValues>) {
    onChange({ ...values, ...partial })
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setTouched({
      accountId: true,
      amount: true,
      occurredOn: true,
    })
    if (Object.keys(errors).length > 0) return
    await onSubmit(values)
  }

  function showError(field: keyof TransactionFormValues) {
    return touched[field] && errors[field] ? (
      <p className="text-xs text-destructive">{errors[field]}</p>
    ) : null
  }

  return (
    <form className="grid gap-3 sm:grid-cols-2" onSubmit={handleSubmit}>
      {mode === 'create' ? (
        <label className="space-y-1">
          <span className="text-xs text-muted-foreground">Account</span>
          <select
            className={`${fieldClass} ${touched.accountId && errors.accountId ? errorClass : ''}`}
            value={values.accountId}
            onChange={(e) => patch({ accountId: e.target.value ? Number(e.target.value) : '' })}
            onBlur={() => setTouched((prev) => ({ ...prev, accountId: true }))}
            required
          >
            <option value="">Select account</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name}
              </option>
            ))}
          </select>
          {showError('accountId')}
        </label>
      ) : null}
      {mode === 'create' ? (
        <label className="space-y-1">
          <span className="text-xs text-muted-foreground">Type</span>
          <select
            className={fieldClass}
            value={values.kind}
            onChange={(e) => patch({ kind: e.target.value })}
          >
            {TRANSACTION_KINDS.map((kind) => (
              <option key={kind.value} value={kind.value}>
                {kind.label}
              </option>
            ))}
          </select>
        </label>
      ) : null}
      <TaxonomySelectField
        label="Category"
        placeholder="Select category"
        emptyLabel="No Categories Yet"
        addLabel="Add category"
        value={values.categoryId}
        options={categories}
        onChange={(categoryId) => patch({ categoryId })}
        onCreate={onCreateCategory}
      />
      <TaxonomySelectField
        label="Merchant"
        placeholder="Select merchant"
        emptyLabel="No Merchants Yet"
        addLabel="Add merchant"
        value={values.merchantId}
        options={merchants}
        onChange={(merchantId) => patch({ merchantId })}
        onCreate={onCreateMerchant}
      />
      <label className="space-y-1">
        <span className="text-xs text-muted-foreground">Amount</span>
        <input
          type="number"
          min="0.01"
          step="0.01"
          className={`${fieldClass} ${touched.amount && errors.amount ? errorClass : ''}`}
          placeholder="0.00"
          value={values.amount}
          onChange={(e) => patch({ amount: e.target.value })}
          onBlur={() => setTouched((prev) => ({ ...prev, amount: true }))}
          required
        />
        {showError('amount')}
      </label>
      <label className="space-y-1">
        <span className="text-xs text-muted-foreground">Date</span>
        <input
          type="date"
          className={`${fieldClass} ${touched.occurredOn && errors.occurredOn ? errorClass : ''}`}
          value={values.occurredOn}
          onChange={(e) => patch({ occurredOn: e.target.value })}
          onBlur={() => setTouched((prev) => ({ ...prev, occurredOn: true }))}
          required
        />
        {showError('occurredOn')}
      </label>
      <label className="space-y-1 sm:col-span-2">
        <span className="text-xs text-muted-foreground">Note</span>
        <input
          className={fieldClass}
          placeholder="Optional description"
          value={values.note}
          onChange={(e) => patch({ note: e.target.value })}
        />
      </label>
      <div className="flex flex-wrap items-center gap-2 sm:col-span-2">
        <Button type="submit" size="sm" disabled={busy}>
          {mode === 'create' ? 'Save transaction' : 'Save changes'}
        </Button>
        <Button type="button" variant="ghost" size="sm" disabled={busy} onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  )
}
