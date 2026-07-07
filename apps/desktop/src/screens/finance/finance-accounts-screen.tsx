import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus } from 'lucide-react'
import { AccountCard, AccountTypeSelect } from '@/components/finance/account-card'
import { FeedbackBanner } from '@/components/finance/feedback'
import { useFinanceFeedback } from '@/hooks/use-finance-feedback'
import { ScreenHeader } from '@/components/layout/screen-header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { QueryBoundary } from '@/components/query-boundary'
import { useCreateAccount, useCreateTransfer } from '@/hooks/use-finance-mutations'
import { useAccounts } from '@/hooks/use-finance'
import { ApiError } from '@/lib/api-client'
import { CREATABLE_ACCOUNT_TYPES, isTransferEligible } from '@/lib/finance/account-types'
import { formatINR } from '@/lib/utils'

export function FinanceAccountsScreen() {
  const [includeArchived, setIncludeArchived] = useState(false)
  const accounts = useAccounts(includeArchived)
  const createAccount = useCreateAccount()
  const createTransfer = useCreateTransfer()
  const [showForm, setShowForm] = useState(false)
  const [showTransfer, setShowTransfer] = useState(false)
  const [name, setName] = useState('')
  const [accountType, setAccountType] = useState('bank')
  const [openingBalance, setOpeningBalance] = useState('0')
  const { feedback, notify, reset } = useFinanceFeedback()
  const [fromAccountId, setFromAccountId] = useState<number | ''>('')
  const [toAccountId, setToAccountId] = useState<number | ''>('')
  const [transferAmount, setTransferAmount] = useState('')
  const [transferDate, setTransferDate] = useState(new Date().toISOString().slice(0, 10))

  const transferAccounts = useMemo(
    () => (accounts.data ?? []).filter((account) => isTransferEligible(account)),
    [accounts.data],
  )

  async function handleTransfer(event: React.FormEvent) {
    event.preventDefault()
    if (!fromAccountId || !toAccountId) return
    reset()
    try {
      const result = await createTransfer.mutateAsync({
        from_account_id: Number(fromAccountId),
        to_account_id: Number(toAccountId),
        amount: Number(transferAmount),
        occurred_on: transferDate,
      })
      notify(result.meta.message)
      setShowTransfer(false)
    } catch (error) {
      notify(error instanceof ApiError ? error.message : 'Could not create transfer.', 'error')
    }
  }

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault()
    reset()
    try {
      const result = await createAccount.mutateAsync({
        name,
        account_type: accountType,
        opening_balance: Number(openingBalance) || 0,
      })
      setName('')
      setOpeningBalance('0')
      setAccountType('bank')
      setShowForm(false)
      notify(result.meta.message)
    } catch (error) {
      notify(error instanceof ApiError ? error.message : 'Could not create account.', 'error')
    }
  }

  return (
    <section>
      <ScreenHeader
        title="Accounts"
        description="Master registry for every financial account. Credit cards keep their specialized screen for billing and rewards."
        actions={
          <div className="flex flex-wrap gap-2">
            <Button
              size="sm"
              variant={includeArchived ? 'secondary' : 'outline'}
              onClick={() => setIncludeArchived((value) => !value)}
            >
              {includeArchived ? 'Hide archived' : 'Show archived'}
            </Button>
            <Button size="sm" variant="outline" onClick={() => setShowTransfer((open) => !open)}>
              Transfer
            </Button>
            <Button size="sm" onClick={() => setShowForm((open) => !open)}>
              <Plus className="h-4 w-4" />
              New account
            </Button>
          </div>
        }
      />
      <FeedbackBanner feedback={feedback} />
      {showTransfer ? (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>Transfer funds</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="grid gap-3 sm:grid-cols-2" onSubmit={handleTransfer}>
              <select
                className="rounded-md border border-border bg-background px-3 py-2 text-sm"
                value={fromAccountId}
                onChange={(e) => setFromAccountId(Number(e.target.value))}
                required
              >
                <option value="">From account</option>
                {transferAccounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name}
                  </option>
                ))}
              </select>
              <select
                className="rounded-md border border-border bg-background px-3 py-2 text-sm"
                value={toAccountId}
                onChange={(e) => setToAccountId(Number(e.target.value))}
                required
              >
                <option value="">To account</option>
                {transferAccounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name}
                  </option>
                ))}
              </select>
              <input
                type="number"
                min="0.01"
                step="0.01"
                placeholder="Amount"
                aria-label="Transfer amount"
                className="rounded-md border border-border bg-background px-3 py-2 text-sm"
                value={transferAmount}
                onChange={(e) => setTransferAmount(e.target.value)}
                required
              />
              <input
                type="date"
                className="rounded-md border border-border bg-background px-3 py-2 text-sm"
                value={transferDate}
                onChange={(e) => setTransferDate(e.target.value)}
                required
              />
              <Button type="submit" size="sm" disabled={createTransfer.isPending}>
                Transfer
              </Button>
            </form>
          </CardContent>
        </Card>
      ) : null}
      {showForm ? (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>Create account</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={handleCreate}>
              <label className="block space-y-1">
                <span className="text-xs text-muted-foreground">Name</span>
                <input
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  placeholder="e.g. HDFC Savings, PhonePe UPI, Home Loan"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </label>
              <div className="space-y-2">
                <span className="text-xs text-muted-foreground">Type</span>
                <AccountTypeSelect value={accountType} onChange={setAccountType} options={CREATABLE_ACCOUNT_TYPES} />
                <p className="text-xs text-muted-foreground">
                  Credit cards need billing settings.{' '}
                  <Link to="/finance/credit-cards" className="text-emerald-400 hover:underline">
                    Create on the Credit Cards screen
                  </Link>
                  .
                </p>
              </div>
              <label className="block space-y-1">
                <span className="text-xs text-muted-foreground">Opening balance</span>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  value={openingBalance}
                  onChange={(e) => setOpeningBalance(e.target.value)}
                />
              </label>
              <div className="flex items-center gap-2">
                <Button type="submit" size="sm" disabled={createAccount.isPending}>
                  Save
                </Button>
                <Button type="button" variant="ghost" size="sm" onClick={() => setShowForm(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      ) : null}
      <QueryBoundary query={accounts} loadingMessage="Loading accounts…" emptyMessage="No accounts yet.">
        {(data) => {
          if (data.length === 0) {
            return (
              <div className="rounded-md border border-dashed border-border p-8 text-center">
                <p className="text-sm font-medium">No Accounts Yet</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Create cash, bank, wallet, loan, investment, and other accounts here.
                </p>
                <Button className="mt-4" size="sm" onClick={() => setShowForm(true)}>
                  <Plus className="h-4 w-4" />
                  New account
                </Button>
              </div>
            )
          }

          const assets = data.filter((account) => account.classification === 'asset')
          const liabilities = data.filter((account) => account.classification === 'liability')

          return (
            <div className="space-y-6">
              {assets.length > 0 ? (
                <section className="space-y-3">
                  <div className="flex items-baseline justify-between gap-2">
                    <h2 className="text-sm font-medium text-muted-foreground">Assets</h2>
                    <p className="text-sm font-semibold">
                      {formatINR(assets.reduce((sum, account) => sum + (account.balance ?? 0), 0))}
                    </p>
                  </div>
                  <div className="grid gap-3">
                    {assets.map((account) => (
                      <AccountCard key={account.id} account={account} onFeedback={notify} />
                    ))}
                  </div>
                </section>
              ) : null}
              {liabilities.length > 0 ? (
                <section className="space-y-3">
                  <div className="flex items-baseline justify-between gap-2">
                    <h2 className="text-sm font-medium text-muted-foreground">Liabilities</h2>
                    <p className="text-sm font-semibold">
                      {formatINR(liabilities.reduce((sum, account) => sum + (account.balance ?? 0), 0))}
                    </p>
                  </div>
                  <div className="grid gap-3">
                    {liabilities.map((account) => (
                      <AccountCard key={account.id} account={account} onFeedback={notify} />
                    ))}
                  </div>
                </section>
              ) : null}
            </div>
          )
        }}
      </QueryBoundary>
    </section>
  )
}
