import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Archive, Pencil, RotateCcw } from 'lucide-react'
import { ConfirmActionBar } from '@/components/finance/confirm-action-bar'
import type { FeedbackTone } from '@/hooks/use-finance-feedback'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { useArchiveAccount, useRestoreAccount, useUpdateAccount } from '@/hooks/use-finance-mutations'
import { ApiError } from '@/lib/api-client'
import {
  accountTypeIcon,
  accountTypeLabel,
  REGISTRY_ACCOUNT_TYPES,
} from '@/lib/finance/account-types'
import { cn, formatINR, formatShortDate } from '@/lib/utils'
import type { FinanceAccount } from '@/view-models/finance'

interface AccountCardProps {
  account: FinanceAccount
  onFeedback: (message: string, tone?: FeedbackTone) => void
}

type PendingAction = 'archive' | 'restore' | null

export function AccountCard({ account, onFeedback }: AccountCardProps) {
  const updateAccount = useUpdateAccount()
  const archiveAccount = useArchiveAccount()
  const restoreAccount = useRestoreAccount()
  const [editing, setEditing] = useState(false)
  const [pendingAction, setPendingAction] = useState<PendingAction>(null)
  const [name, setName] = useState(account.name)
  const [openingBalance, setOpeningBalance] = useState(String((account.openingBalanceMinor ?? 0) / 100))
  const [openingBalanceOn, setOpeningBalanceOn] = useState(account.openingBalanceOn)
  const busy = updateAccount.isPending || archiveAccount.isPending || restoreAccount.isPending
  const Icon = accountTypeIcon(account.type)
  const isArchived = Boolean(account.archivedAt)
  const createdLabel = formatShortDate(account.createdAt)

  function resetDraft() {
    setName(account.name)
    setOpeningBalance(String((account.openingBalanceMinor ?? 0) / 100))
    setOpeningBalanceOn(account.openingBalanceOn)
  }

  async function handleUpdate(event: React.FormEvent) {
    event.preventDefault()
    try {
      const result = await updateAccount.mutateAsync({
        accountId: account.id,
        input: {
          name: name.trim(),
          opening_balance: Number(openingBalance) || 0,
          opening_balance_on: openingBalanceOn,
        },
      })
      onFeedback(result.meta.message)
      setEditing(false)
    } catch (error) {
      onFeedback(error instanceof ApiError ? error.message : 'Could not update account.', 'error')
    }
  }

  async function handleArchive() {
    try {
      const result = await archiveAccount.mutateAsync(account.id)
      onFeedback(result.meta.message)
      setPendingAction(null)
      setEditing(false)
    } catch (error) {
      onFeedback(error instanceof ApiError ? error.message : 'Could not archive account.', 'error')
    }
  }

  async function handleRestore() {
    try {
      const result = await restoreAccount.mutateAsync(account.id)
      onFeedback(result.meta.message)
      setPendingAction(null)
      setEditing(false)
    } catch (error) {
      onFeedback(error instanceof ApiError ? error.message : 'Could not restore account.', 'error')
    }
  }

  return (
    <Card className={cn(isArchived && 'opacity-75')}>
      <CardContent className="space-y-4 p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-start gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-lg border border-border bg-muted/40">
              <Icon className="size-5 text-muted-foreground" />
            </div>
            <div className="min-w-0">
              <p className="truncate font-medium">{account.name}</p>
              <div className="mt-1 flex flex-wrap gap-2">
                <Badge variant="secondary">{accountTypeLabel(account.type)}</Badge>
                <Badge variant="outline">{account.classification}</Badge>
                {isArchived ? <Badge className="border-destructive/40 bg-destructive/10 text-destructive">Archived</Badge> : null}
              </div>
              <div className="mt-2 space-y-1 text-xs text-muted-foreground">
                <p>
                  Opening {formatINR(account.openingBalanceMinor / 100)} on {account.openingBalanceOn}
                </p>
                {createdLabel ? <p>Created {createdLabel}</p> : null}
              </div>
              {account.type === 'credit_card' ? (
                <Link to="/finance/credit-cards" className="mt-2 inline-block text-xs text-emerald-400 hover:underline">
                  Manage card settings
                </Link>
              ) : null}
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs text-muted-foreground">Current balance</p>
            <p className="text-lg font-semibold">{formatINR(account.balance ?? 0)}</p>
          </div>
        </div>

        {pendingAction ? (
          <ConfirmActionBar
            message={
              pendingAction === 'archive'
                ? `Archive ${account.name}? It will be hidden from active lists.`
                : `Restore ${account.name}? It will appear in active lists again.`
            }
            confirmLabel={pendingAction === 'archive' ? 'Archive' : 'Restore'}
            destructive={pendingAction === 'archive'}
            busy={busy}
            onCancel={() => setPendingAction(null)}
            onConfirm={() => void (pendingAction === 'archive' ? handleArchive() : handleRestore())}
          />
        ) : null}

        {editing ? (
          <form className="grid gap-3 border-t border-border pt-4 sm:grid-cols-2" onSubmit={handleUpdate}>
            <label className="space-y-1 sm:col-span-2">
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
              <input
                className="w-full rounded-md border border-border bg-muted px-3 py-2 text-sm text-muted-foreground"
                value={accountTypeLabel(account.type)}
                readOnly
              />
              <p className="text-xs text-muted-foreground">Account type is set at creation.</p>
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
            <label className="space-y-1 sm:col-span-2">
              <span className="text-xs text-muted-foreground">Opening balance date</span>
              <input
                type="date"
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                value={openingBalanceOn}
                onChange={(e) => setOpeningBalanceOn(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Opening balance can only change before the first transaction.
              </p>
            </label>
            <div className="flex flex-wrap items-center gap-2 sm:col-span-2">
              <Button type="submit" size="sm" disabled={busy}>
                Save changes
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                disabled={busy}
                onClick={() => {
                  resetDraft()
                  setEditing(false)
                }}
              >
                Cancel
              </Button>
              {isArchived ? (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={busy}
                  onClick={() => setPendingAction('restore')}
                >
                  <RotateCcw className="size-4" />
                  Restore
                </Button>
              ) : (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={busy}
                  onClick={() => setPendingAction('archive')}
                >
                  <Archive className="size-4" />
                  Archive
                </Button>
              )}
            </div>
          </form>
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
            {isArchived ? (
              <Button variant="outline" size="sm" disabled={busy} onClick={() => setPendingAction('restore')}>
                <RotateCcw className="size-4" />
                Restore
              </Button>
            ) : (
              <Button variant="outline" size="sm" disabled={busy} onClick={() => setPendingAction('archive')}>
                <Archive className="size-4" />
                Archive
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export function AccountTypeSelect({
  value,
  onChange,
  options = REGISTRY_ACCOUNT_TYPES,
}: {
  value: string
  onChange: (value: string) => void
  options?: ReadonlyArray<{ value: string; label: string; icon: typeof REGISTRY_ACCOUNT_TYPES[number]['icon'] }>
}) {
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {options.map(({ value: typeValue, label, icon: TypeIcon }) => (
        <button
          key={typeValue}
          type="button"
          className={cn(
            'flex items-center gap-3 rounded-lg border px-3 py-2 text-left text-sm transition',
            value === typeValue
              ? 'border-emerald-500/60 bg-emerald-500/10 text-foreground'
              : 'border-border bg-background text-muted-foreground hover:border-border/80 hover:bg-muted/30',
          )}
          onClick={() => onChange(typeValue)}
        >
          <TypeIcon className="size-4 shrink-0" />
          <span>{label}</span>
        </button>
      ))}
    </div>
  )
}
