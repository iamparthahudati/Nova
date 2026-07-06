import { useState } from 'react'
import { Plus } from 'lucide-react'
import { ScreenHeader } from '@/components/layout/screen-header'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { QueryBoundary } from '@/components/query-boundary'
import { useArchiveAccount, useCreateAccount, useCreateTransfer } from '@/hooks/use-finance-mutations'
import { useAccounts } from '@/hooks/use-finance'
import { ApiError } from '@/lib/api-client'
import { formatINR } from '@/lib/utils'

export function FinanceAccountsScreen() {
  const accounts = useAccounts(false)
  const createAccount = useCreateAccount()
  const archiveAccount = useArchiveAccount()
  const createTransfer = useCreateTransfer()
  const [showForm, setShowForm] = useState(false)
  const [showTransfer, setShowTransfer] = useState(false)
  const [name, setName] = useState('')
  const [accountType, setAccountType] = useState('bank')
  const [openingBalance, setOpeningBalance] = useState('0')
  const [feedback, setFeedback] = useState<string | null>(null)
  const [fromAccountId, setFromAccountId] = useState<number | ''>('')
  const [toAccountId, setToAccountId] = useState<number | ''>('')
  const [transferAmount, setTransferAmount] = useState('')
  const [transferDate, setTransferDate] = useState(new Date().toISOString().slice(0, 10))

  async function handleTransfer(event: React.FormEvent) {
    event.preventDefault()
    if (!fromAccountId || !toAccountId) return
    setFeedback(null)
    try {
      const result = await createTransfer.mutateAsync({
        from_account_id: Number(fromAccountId),
        to_account_id: Number(toAccountId),
        amount: Number(transferAmount),
        occurred_on: transferDate,
      })
      setFeedback(result.meta.message)
      setShowTransfer(false)
    } catch (error) {
      setFeedback(error instanceof ApiError ? error.message : 'Could not create transfer.')
    }
  }

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault()
    setFeedback(null)
    try {
      const result = await createAccount.mutateAsync({
        name,
        account_type: accountType,
        opening_balance: Number(openingBalance) || 0,
      })
      setName('')
      setOpeningBalance('0')
      setShowForm(false)
      setFeedback(result.meta.message)
    } catch (error) {
      setFeedback(error instanceof ApiError ? error.message : 'Could not create account.')
    }
  }

  return (
    <section>
      <ScreenHeader
        title="Accounts"
        description="Asset accounts with balances from projection service."
        actions={
          <div className="flex gap-2">
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
      {feedback ? <p className="mb-4 text-sm text-emerald-400">{feedback}</p> : null}
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
                {(accounts.data ?? []).map((account) => (
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
                {(accounts.data ?? []).map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name}
                  </option>
                ))}
              </select>
              <input
                type="number"
                min="0.01"
                step="0.01"
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
            <form className="grid gap-3 sm:grid-cols-2" onSubmit={handleCreate}>
              <label className="space-y-1">
                <span className="text-xs text-muted-foreground">Name</span>
                <input
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </label>
              <label className="space-y-1">
                <span className="text-xs text-muted-foreground">Type</span>
                <select
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  value={accountType}
                  onChange={(e) => setAccountType(e.target.value)}
                >
                  <option value="cash">Cash</option>
                  <option value="bank">Bank</option>
                  <option value="wallet">Wallet</option>
                </select>
              </label>
              <label className="space-y-1">
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
              <div className="flex items-end gap-2">
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
        {(data) => (
          <div className="grid gap-3">
            {data.map((account) => (
              <Card key={account.id}>
                <CardContent className="flex items-center justify-between p-4">
                  <div>
                    <p className="font-medium">{account.name}</p>
                    <div className="mt-1 flex gap-2">
                      <Badge variant="secondary">{account.type}</Badge>
                      <Badge variant="outline">{account.classification}</Badge>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Opening {formatINR(account.openingBalanceMinor / 100)} on {account.openingBalanceOn}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <p className="text-lg font-semibold">{formatINR(account.balance ?? 0)}</p>
                    {!account.archivedAt ? (
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={archiveAccount.isPending}
                        onClick={() => archiveAccount.mutate(account.id)}
                      >
                        Archive
                      </Button>
                    ) : (
                      <Badge>Archived</Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </QueryBoundary>
    </section>
  )
}
