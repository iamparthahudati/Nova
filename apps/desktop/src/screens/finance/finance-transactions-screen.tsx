import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Plus, Receipt } from 'lucide-react'
import { ScreenHeader } from '@/components/layout/screen-header'
import { TransactionCard } from '@/components/finance/transaction-card'
import { TransactionFilters, type TransactionFilterState } from '@/components/finance/transaction-filters'
import { TransactionForm, type TransactionFormValues } from '@/components/finance/transaction-form'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { QueryBoundary } from '@/components/query-boundary'
import { useAccounts, useCategories, useFinanceTransactions, useMerchants } from '@/hooks/use-finance'
import {
  useCreateCategory,
  useCreateMerchant,
  useCreateTransaction,
  useDeleteTransaction,
  useUpdateTransaction,
} from '@/hooks/use-finance-mutations'
import { ApiError } from '@/lib/api-client'

const EMPTY_FILTERS: TransactionFilterState = {
  kind: '',
  startDate: '',
  endDate: '',
  search: '',
}

const EMPTY_FORM: TransactionFormValues = {
  accountId: '',
  kind: 'expense',
  amount: '',
  occurredOn: new Date().toISOString().slice(0, 10),
  note: '',
  categoryId: '',
  merchantId: '',
}

export function FinanceTransactionsScreen() {
  const [searchParams] = useSearchParams()
  const paramAccountId = searchParams.get('accountId')
  const [filters, setFilters] = useState<TransactionFilterState>({
    ...EMPTY_FILTERS,
    accountId: paramAccountId ? Number(paramAccountId) : undefined,
  })
  const [offset, setOffset] = useState(0)
  const limit = 25
  const accountsQuery = useAccounts(false)
  const categoriesQuery = useCategories()
  const merchantsQuery = useMerchants()
  const transactions = useFinanceTransactions({
    accountId: filters.accountId,
    categoryId: filters.categoryId,
    merchantId: filters.merchantId,
    kind: filters.kind || undefined,
    startDate: filters.startDate || undefined,
    endDate: filters.endDate || undefined,
    search: filters.search || undefined,
    limit,
    offset,
  })
  const createTransaction = useCreateTransaction()
  const updateTransaction = useUpdateTransaction()
  const deleteTransaction = useDeleteTransaction()
  const createCategory = useCreateCategory()
  const createMerchant = useCreateMerchant()
  const [showForm, setShowForm] = useState(false)
  const [formValues, setFormValues] = useState<TransactionFormValues>(EMPTY_FORM)
  const [feedback, setFeedback] = useState<string | null>(null)
  const mutationBusy =
    createTransaction.isPending || updateTransaction.isPending || deleteTransaction.isPending

  useEffect(() => {
    if (paramAccountId) {
      setFilters((current) => ({ ...current, accountId: Number(paramAccountId) }))
    }
  }, [paramAccountId])

  function resetFilters() {
    setOffset(0)
    setFilters({ ...EMPTY_FILTERS, accountId: paramAccountId ? Number(paramAccountId) : undefined })
  }

  function handleFilterChange(next: TransactionFilterState) {
    setOffset(0)
    setFilters(next)
  }

  async function handleCreate(values: TransactionFormValues) {
    if (!values.accountId) return
    setFeedback(null)
    const savedAccountId = Number(values.accountId)
    const accountName =
      (accountsQuery.data ?? []).find((account) => account.id === savedAccountId)?.name ?? 'account'
    try {
      const result = await createTransaction.mutateAsync({
        account_id: savedAccountId,
        kind: values.kind,
        amount: Number(values.amount),
        occurred_on: values.occurredOn,
        note: values.note || undefined,
        category_id: values.categoryId ? Number(values.categoryId) : undefined,
        merchant_id: values.merchantId ? Number(values.merchantId) : undefined,
      })
      setFormValues({ ...EMPTY_FORM, accountId: savedAccountId })
      setShowForm(false)
      setOffset(0)
      setFilters((current) => ({ ...current, accountId: savedAccountId, kind: '', search: '' }))
      setFeedback(`${result.meta.message} Showing ${accountName} below.`)
    } catch (error) {
      setFeedback(error instanceof ApiError ? error.message : 'Could not create transaction.')
    }
  }

  async function handleUpdate(transactionId: number, values: TransactionFormValues) {
    const result = await updateTransaction.mutateAsync({
      transactionId,
      input: {
        amount: Number(values.amount),
        occurred_on: values.occurredOn,
        note: values.note || null,
        category_id: values.categoryId ? Number(values.categoryId) : null,
        merchant_id: values.merchantId ? Number(values.merchantId) : null,
      },
    })
    setFeedback(result.meta.message)
  }

  async function handleDelete(transactionId: number) {
    const result = await deleteTransaction.mutateAsync(transactionId)
    setFeedback(result.meta.message)
  }

  return (
    <section>
      <ScreenHeader
        title="Transactions"
        description="Search, filter, and manage ledger entries from the backend."
        actions={
          <Button size="sm" onClick={() => setShowForm((open) => !open)}>
            <Plus className="h-4 w-4" />
            Add transaction
          </Button>
        }
      />
      <TransactionFilters
        filters={filters}
        accounts={accountsQuery.data ?? []}
        categories={categoriesQuery.data ?? []}
        merchants={merchantsQuery.data ?? []}
        onChange={handleFilterChange}
        onReset={resetFilters}
      />
      {feedback ? <p className="mb-4 mt-4 text-sm text-emerald-400">{feedback}</p> : null}
      {showForm ? (
        <Card className="mb-4 mt-4">
          <CardHeader>
            <CardTitle>New transaction</CardTitle>
          </CardHeader>
          <CardContent>
            <TransactionForm
              mode="create"
              values={formValues}
              accounts={accountsQuery.data ?? []}
              categories={categoriesQuery.data ?? []}
              merchants={merchantsQuery.data ?? []}
              busy={mutationBusy}
              onChange={setFormValues}
              onSubmit={handleCreate}
              onCancel={() => setShowForm(false)}
              onCreateCategory={async (name) => {
                const result = await createCategory.mutateAsync({ name })
                return result.category
              }}
              onCreateMerchant={async (name) => {
                const result = await createMerchant.mutateAsync({ name })
                return result.merchant
              }}
            />
          </CardContent>
        </Card>
      ) : null}
      <QueryBoundary
        query={transactions}
        isEmpty={(data) => data.transactions.length === 0}
        loadingMessage="Loading transactions…"
        emptyMessage="No transactions match these filters."
      >
        {(data) => {
          if (data.transactions.length === 0) {
            return (
              <div className="mt-4 rounded-md border border-dashed border-border p-8 text-center">
                <Receipt className="mx-auto size-8 text-muted-foreground" />
                <p className="mt-3 text-sm font-medium">No transactions yet</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Add a transaction or clear filters to see ledger entries.
                </p>
                <Button className="mt-4" size="sm" onClick={() => setShowForm(true)}>
                  <Plus className="h-4 w-4" />
                  Add transaction
                </Button>
              </div>
            )
          }
          return (
            <>
              <div className="mt-4 space-y-3">
                {data.transactions.map((txn) => (
                  <TransactionCard
                    key={txn.id}
                    transaction={txn}
                    categories={categoriesQuery.data ?? []}
                    merchants={merchantsQuery.data ?? []}
                    busy={mutationBusy}
                    onFeedback={setFeedback}
                    onUpdate={handleUpdate}
                    onDelete={handleDelete}
                    onCreateCategory={async (name) => {
                      const result = await createCategory.mutateAsync({ name })
                      return result.category
                    }}
                    onCreateMerchant={async (name) => {
                      const result = await createMerchant.mutateAsync({ name })
                      return result.merchant
                    }}
                  />
                ))}
              </div>
              <div className="mt-4 flex items-center justify-between">
                <p className="text-xs text-muted-foreground">
                  Showing {data.offset + 1}–{Math.min(data.offset + data.limit, data.total)} of {data.total}
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={offset === 0}
                    onClick={() => setOffset(Math.max(0, offset - limit))}
                  >
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
          )
        }}
      </QueryBoundary>
    </section>
  )
}
