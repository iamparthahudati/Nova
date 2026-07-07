import { useState } from 'react'
import { Pencil, Trash2 } from 'lucide-react'
import { ConfirmActionBar } from '@/components/finance/confirm-action-bar'
import { Amount } from '@/components/finance/metric-card'
import { TransactionForm, type TransactionFormValues } from '@/components/finance/transaction-form'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { transactionKindMeta } from '@/lib/finance/transaction-kinds'
import { cn, formatShortDate } from '@/lib/utils'
import type { FinanceCategory, FinanceMerchant, FinanceTransaction } from '@/view-models/finance'

interface TransactionCardProps {
  transaction: FinanceTransaction
  categories: FinanceCategory[]
  merchants: FinanceMerchant[]
  busy?: boolean
  onFeedback: (message: string) => void
  onUpdate: (transactionId: number, values: TransactionFormValues) => Promise<void>
  onDelete: (transactionId: number) => Promise<void>
  onCreateCategory: (name: string) => Promise<{ id: number }>
  onCreateMerchant: (name: string) => Promise<{ id: number }>
}

function toFormValues(transaction: FinanceTransaction): TransactionFormValues {
  return {
    accountId: transaction.accountId,
    kind: transaction.kind,
    amount: String(transaction.amount),
    occurredOn: transaction.occurredOn,
    note: transaction.note ?? '',
    categoryId: transaction.categoryId ?? '',
    merchantId: transaction.merchantId ?? '',
  }
}

export function TransactionCard({
  transaction,
  categories,
  merchants,
  busy = false,
  onFeedback,
  onUpdate,
  onDelete,
  onCreateCategory,
  onCreateMerchant,
}: TransactionCardProps) {
  const [editing, setEditing] = useState(false)
  const [pendingDelete, setPendingDelete] = useState(false)
  const [values, setValues] = useState(() => toFormValues(transaction))
  const kind = transactionKindMeta(transaction.kind)
  const KindIcon = kind.icon
  const title = transaction.note || transaction.merchantName || kind.label
  const dateLabel = formatShortDate(transaction.occurredOn) ?? transaction.occurredOn

  function resetDraft() {
    setValues(toFormValues(transaction))
  }

  async function handleUpdate(formValues: TransactionFormValues) {
    try {
      await onUpdate(transaction.id, formValues)
      setEditing(false)
    } catch (error) {
      onFeedback(error instanceof Error ? error.message : 'Could not update transaction.')
    }
  }

  async function handleDelete() {
    try {
      await onDelete(transaction.id)
      setPendingDelete(false)
    } catch (error) {
      onFeedback(error instanceof Error ? error.message : 'Could not delete transaction.')
    }
  }

  return (
    <Card>
      <CardContent className="space-y-3 p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-start gap-3">
            <div
              className={cn(
                'flex size-10 shrink-0 items-center justify-center rounded-lg border border-border',
                kind.amountTone === 'positive' && 'bg-emerald-500/10 text-emerald-400',
                kind.amountTone === 'negative' && 'bg-rose-500/10 text-rose-400',
                kind.amountTone === 'neutral' && 'bg-muted/40 text-muted-foreground',
              )}
            >
              <KindIcon className="size-5" />
            </div>
            <div className="min-w-0">
              <p className="truncate font-medium">{title}</p>
              <div className="mt-1 flex flex-wrap gap-2">
                <Badge variant="secondary">{kind.label}</Badge>
                <Badge variant="outline">{transaction.direction}</Badge>
              </div>
              <div className="mt-2 space-y-0.5 text-xs text-muted-foreground">
                <p>
                  {transaction.accountName ?? `Account ${transaction.accountId}`} · {dateLabel}
                </p>
                {transaction.categoryName ? <p>Category: {transaction.categoryName}</p> : null}
                {transaction.merchantName ? <p>Merchant: {transaction.merchantName}</p> : null}
              </div>
            </div>
          </div>
          <Amount value={transaction.amount} direction={transaction.kind} />
        </div>

        {pendingDelete ? (
          <ConfirmActionBar
            message={`Delete this ${kind.label.toLowerCase()} on ${transaction.accountName ?? 'the account'}? This cannot be undone.`}
            confirmLabel="Delete"
            destructive
            busy={busy}
            onCancel={() => setPendingDelete(false)}
            onConfirm={() => void handleDelete()}
          />
        ) : null}

        {editing ? (
          <div className="border-t border-border pt-3">
            <TransactionForm
              mode="edit"
              values={values}
              accounts={[]}
              categories={categories}
              merchants={merchants}
              busy={busy}
              onChange={setValues}
              onSubmit={handleUpdate}
              onCancel={() => {
                resetDraft()
                setEditing(false)
              }}
              onCreateCategory={onCreateCategory}
              onCreateMerchant={onCreateMerchant}
            />
          </div>
        ) : (
          <div className="flex items-center justify-end gap-1 border-t border-border pt-3">
            <Button
              variant="ghost"
              size="sm"
              disabled={busy}
              onClick={() => {
                resetDraft()
                setEditing(true)
              }}
            >
              <Pencil className="size-4" />
              Edit
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={busy}
              onClick={() => setPendingDelete(true)}
            >
              <Trash2 className="size-4" />
              Delete
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
