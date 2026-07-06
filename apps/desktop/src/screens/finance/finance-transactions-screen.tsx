import { useState } from 'react'
import { Plus } from 'lucide-react'
import { ScreenHeader } from '@/components/layout/screen-header'
import { Amount } from '@/components/finance/metric-card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { QueryBoundary } from '@/components/query-boundary'
import { useAccounts, useCategories, useFinanceTransactions, useMerchants } from '@/hooks/use-finance'
import { useCreateCategory, useCreateMerchant, useCreateTransaction } from '@/hooks/use-finance-mutations'
import { ApiError } from '@/lib/api-client'

export function FinanceTransactionsScreen() {
  const [accountId, setAccountId] = useState<number | undefined>()
  const [direction, setDirection] = useState<string>('')
  const [search, setSearch] = useState('')
  const [offset, setOffset] = useState(0)
  const limit = 25
  const accountsQuery = useAccounts(false)
  const categoriesQuery = useCategories()
  const merchantsQuery = useMerchants()
  const transactions = useFinanceTransactions({
    accountId,
    direction: direction || undefined,
    search: search || undefined,
    limit,
    offset,
  })
  const createTransaction = useCreateTransaction()
  const createCategory = useCreateCategory()
  const createMerchant = useCreateMerchant()
  const [showForm, setShowForm] = useState(false)
  const [formAccountId, setFormAccountId] = useState<number | ''>('')
  const [categoryId, setCategoryId] = useState<number | ''>('')
  const [merchantId, setMerchantId] = useState<number | ''>('')
  const [kind, setKind] = useState('expense')
  const [amount, setAmount] = useState('')
  const [occurredOn, setOccurredOn] = useState(new Date().toISOString().slice(0, 10))
  const [note, setNote] = useState('')
  const [feedback, setFeedback] = useState<string | null>(null)

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault()
    if (!formAccountId) return
    setFeedback(null)
    try {
      const result = await createTransaction.mutateAsync({
        account_id: Number(formAccountId),
        kind,
        amount: Number(amount),
        occurred_on: occurredOn,
        note: note || undefined,
        category_id: categoryId ? Number(categoryId) : undefined,
        merchant_id: merchantId ? Number(merchantId) : undefined,
      })
      setAmount('')
      setNote('')
      setShowForm(false)
      setFeedback(result.meta.message)
    } catch (error) {
      setFeedback(error instanceof ApiError ? error.message : 'Could not create transaction.')
    }
  }

  return (
    <section>
      <ScreenHeader
        title="Transactions"
        description="Search and filter ledger entries from the backend."
        actions={
          <Button size="sm" onClick={() => setShowForm((open) => !open)}>
            <Plus className="h-4 w-4" />
            Add transaction
          </Button>
        }
      />
      <div className="mb-4 flex flex-wrap gap-2">
        <select
          className="rounded-md border border-border bg-background px-3 py-2 text-sm"
          value={accountId ?? ''}
          onChange={(e) => {
            setOffset(0)
            setAccountId(e.target.value ? Number(e.target.value) : undefined)
          }}
        >
          <option value="">All accounts</option>
          {(accountsQuery.data ?? []).map((account) => (
            <option key={account.id} value={account.id}>
              {account.name}
            </option>
          ))}
        </select>
        <select
          className="rounded-md border border-border bg-background px-3 py-2 text-sm"
          value={direction}
          onChange={(e) => {
            setOffset(0)
            setDirection(e.target.value)
          }}
        >
          <option value="">All directions</option>
          <option value="debit">Debit</option>
          <option value="credit">Credit</option>
        </select>
        <input
          className="min-w-[12rem] flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
          placeholder="Search notes…"
          value={search}
          onChange={(e) => {
            setOffset(0)
            setSearch(e.target.value)
          }}
        />
      </div>
      {feedback ? <p className="mb-4 text-sm text-emerald-400">{feedback}</p> : null}
      {showForm ? (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>New transaction</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="grid gap-3 sm:grid-cols-2" onSubmit={handleCreate}>
              <select
                className="rounded-md border border-border bg-background px-3 py-2 text-sm"
                value={formAccountId}
                onChange={(e) => setFormAccountId(Number(e.target.value))}
                required
              >
                <option value="">Select account</option>
                {(accountsQuery.data ?? []).map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name}
                  </option>
                ))}
              </select>
              <select
                className="rounded-md border border-border bg-background px-3 py-2 text-sm"
                value={kind}
                onChange={(e) => setKind(e.target.value)}
              >
                <option value="expense">Expense</option>
                <option value="income">Income</option>
                <option value="adjustment">Adjustment</option>
              </select>
              <select
                className="rounded-md border border-border bg-background px-3 py-2 text-sm"
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value ? Number(e.target.value) : '')}
              >
                <option value="">No category</option>
                {(categoriesQuery.data ?? []).map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
              <select
                className="rounded-md border border-border bg-background px-3 py-2 text-sm"
                value={merchantId}
                onChange={(e) => setMerchantId(e.target.value ? Number(e.target.value) : '')}
              >
                <option value="">No merchant</option>
                {(merchantsQuery.data ?? []).map((merchant) => (
                  <option key={merchant.id} value={merchant.id}>
                    {merchant.name}
                  </option>
                ))}
              </select>
              <input
                type="number"
                min="0.01"
                step="0.01"
                className="rounded-md border border-border bg-background px-3 py-2 text-sm"
                placeholder="Amount"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
              />
              <input
                type="date"
                className="rounded-md border border-border bg-background px-3 py-2 text-sm"
                value={occurredOn}
                onChange={(e) => setOccurredOn(e.target.value)}
                required
              />
              <input
                className="rounded-md border border-border bg-background px-3 py-2 text-sm sm:col-span-2"
                placeholder="Note"
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />
              <Button type="submit" size="sm" disabled={createTransaction.isPending}>
                Save
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={async () => {
                  const name = window.prompt('Category name')
                  if (!name) return
                  await createCategory.mutateAsync({ name })
                }}
              >
                Add category
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={async () => {
                  const name = window.prompt('Merchant name')
                  if (!name) return
                  await createMerchant.mutateAsync({ name })
                }}
              >
                Add merchant
              </Button>
            </form>
          </CardContent>
        </Card>
      ) : null}
      <QueryBoundary query={transactions} loadingMessage="Loading transactions…" emptyMessage="No transactions found.">
        {(data) => (
          <>
            <div className="space-y-2">
              {data.transactions.map((txn) => (
                <div
                  key={txn.id}
                  className="flex items-center justify-between rounded-md border border-border bg-muted/30 p-3"
                >
                  <div>
                    <p className="text-sm font-medium">{txn.note || txn.merchantName || txn.kind}</p>
                    <p className="text-xs text-muted-foreground">
                      {txn.accountName} · {txn.occurredOn}
                      {txn.categoryName ? ` · ${txn.categoryName}` : ''}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{txn.direction}</Badge>
                    <Amount value={txn.amount} direction={txn.kind} />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 flex items-center justify-between">
              <p className="text-xs text-muted-foreground">
                Showing {data.offset + 1}–{Math.min(data.offset + data.limit, data.total)} of {data.total}
              </p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - limit))}>
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={offset + limit >= data.total}
                  onClick={() => setOffset(offset + limit)}
                >
                  Next
                </Button>
              </div>
            </div>
          </>
        )}
      </QueryBoundary>
    </section>
  )
}
