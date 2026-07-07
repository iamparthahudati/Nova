import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Archive,
  ArrowRight,
  CreditCard,
  FileText,
  Pencil,
  PlusCircle,
  Wallet,
} from 'lucide-react'
import { ConfirmActionBar } from '@/components/finance/confirm-action-bar'
import type { FeedbackTone } from '@/hooks/use-finance-feedback'
import { CreditCardEditForm } from '@/components/finance/credit-card-edit-form'
import { CreditCardExpenseForm } from '@/components/finance/credit-card-expense-form'
import { CreditCardPayForm } from '@/components/finance/credit-card-pay-form'
import {
  CreditCardFace,
  CreditCardMetricsGrid,
} from '@/components/finance/credit-card-visuals'
import { UtilizationBar } from '@/components/finance/metric-card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  useArchiveAccount,
  useCreateCardPayment,
  useCreateCategory,
  useCreateMerchant,
  useCreateTransaction,
  useUpdateCreditCard,
} from '@/hooks/use-finance-mutations'
import { useAccounts, useCategories, useMerchants } from '@/hooks/use-finance'
import { ApiError } from '@/lib/api-client'
import {
  statementStatusClass,
  statementStatusTone,
} from '@/lib/finance/credit-card-display'
import { cn, formatINR } from '@/lib/utils'
import type { FinanceCreditCard } from '@/view-models/finance'

type ActivePanel = 'none' | 'pay' | 'expense' | 'edit' | 'archive'

interface CreditCardTileProps {
  card: FinanceCreditCard
  onFeedback: (message: string, tone?: FeedbackTone) => void
}

export function CreditCardTile({ card, onFeedback }: CreditCardTileProps) {
  const navigate = useNavigate()
  const accountsQuery = useAccounts(false)
  const categoriesQuery = useCategories()
  const merchantsQuery = useMerchants()
  const updateCreditCard = useUpdateCreditCard()
  const archiveAccount = useArchiveAccount()
  const createTransaction = useCreateTransaction()
  const createCardPayment = useCreateCardPayment()
  const createCategory = useCreateCategory()
  const createMerchant = useCreateMerchant()
  const [activePanel, setActivePanel] = useState<ActivePanel>('none')

  const assetAccounts = (accountsQuery.data ?? []).filter((account) => account.classification === 'asset')
  const busy =
    updateCreditCard.isPending ||
    archiveAccount.isPending ||
    createTransaction.isPending ||
    createCardPayment.isPending

  async function handleUpdate(input: Parameters<typeof updateCreditCard.mutateAsync>[0]['input']) {
    try {
      const result = await updateCreditCard.mutateAsync({ accountId: card.accountId, input })
      onFeedback(result.meta.message)
      setActivePanel('none')
    } catch (error) {
      onFeedback(error instanceof ApiError ? error.message : 'Could not update credit card.', 'error')
    }
  }

  async function handleArchive() {
    try {
      const result = await archiveAccount.mutateAsync(card.accountId)
      onFeedback(result.meta.message)
      setActivePanel('none')
    } catch (error) {
      onFeedback(error instanceof ApiError ? error.message : 'Could not archive credit card.', 'error')
    }
  }

  async function handlePay(values: {
    fromAccountId: number
    amount: number
    occurredOn: string
    statementId?: number | null
  }) {
    try {
      const result = await createCardPayment.mutateAsync({
        from_account_id: values.fromAccountId,
        card_account_id: card.accountId,
        amount: values.amount,
        occurred_on: values.occurredOn,
        statement_id: values.statementId ?? card.currentStatement?.id ?? null,
      })
      onFeedback(result.meta.message)
      setActivePanel('none')
    } catch (error) {
      onFeedback(error instanceof ApiError ? error.message : 'Could not pay card.', 'error')
    }
  }

  async function handleExpense(values: {
    amount: number
    occurredOn: string
    note: string
    categoryId?: number
    merchantId?: number
  }) {
    try {
      const result = await createTransaction.mutateAsync({
        account_id: card.accountId,
        direction: 'debit',
        kind: 'expense',
        amount: values.amount,
        occurred_on: values.occurredOn,
        note: values.note || null,
        category_id: values.categoryId ?? null,
        merchant_id: values.merchantId ?? null,
      })
      onFeedback(result.meta.message)
      setActivePanel('none')
    } catch (error) {
      onFeedback(error instanceof ApiError ? error.message : 'Could not add expense.', 'error')
    }
  }

  const statementTone = statementStatusTone(card.currentStatement?.status)
  const statementClass = statementStatusClass(statementTone)

  return (
    <Card className="overflow-hidden transition hover:border-border/80 hover:shadow-md">
      <CardContent className="space-y-4 p-0">
        <button
          type="button"
          className="block w-full text-left"
          onClick={() => navigate(`/finance/credit-cards/${card.accountId}`)}
        >
          <CreditCardFace name={card.name} network={card.network} last4={card.last4} className="rounded-none" />
        </button>

        <div className="space-y-4 px-4 pb-4">
          <div className="flex flex-wrap items-center gap-2">
            {card.autopay ? <Badge variant="secondary">Autopay</Badge> : null}
            {card.currentStatement ? (
              <span className={cn('rounded-full border px-2 py-0.5 text-xs font-medium capitalize', statementClass)}>
                {card.currentStatement.status ?? 'open'}
              </span>
            ) : (
              <Badge variant="outline">No statement</Badge>
            )}
            {card.currentStatement?.remainingDue != null && card.currentStatement.remainingDue > 0 ? (
              <Badge variant="outline" className="border-rose-500/40 text-rose-400">
                Due {formatINR(card.currentStatement.remainingDue)}
              </Badge>
            ) : null}
          </div>

          <CreditCardMetricsGrid
            creditLimit={card.creditLimit}
            availableLimit={card.availableLimit}
            outstanding={card.outstanding}
            utilizationPercent={card.utilizationPercent}
            statementDay={card.statementDay}
            dueDayOffset={card.dueDayOffset}
          />

          <UtilizationBar percent={card.utilizationPercent ?? 0} />

          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/finance/statements?accountId=${card.accountId}`)}
            >
              <FileText className="size-4" />
              View statements
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setActivePanel((panel) => (panel === 'expense' ? 'none' : 'expense'))}
            >
              <PlusCircle className="size-4" />
              Add expense
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setActivePanel((panel) => (panel === 'pay' ? 'none' : 'pay'))}
            >
              <Wallet className="size-4" />
              Pay card
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setActivePanel((panel) => (panel === 'edit' ? 'none' : 'edit'))}
            >
              <Pencil className="size-4" />
              Edit
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-muted-foreground hover:text-destructive"
              onClick={() => setActivePanel('archive')}
            >
              <Archive className="size-4" />
              Archive
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="ml-auto"
              onClick={() => navigate(`/finance/credit-cards/${card.accountId}`)}
            >
              Details
              <ArrowRight className="size-4" />
            </Button>
          </div>

          {activePanel === 'archive' ? (
            <ConfirmActionBar
              message={`Archive ${card.name}? This card will no longer appear in active lists.`}
              confirmLabel="Archive"
              destructive
              busy={busy}
              onCancel={() => setActivePanel('none')}
              onConfirm={() => void handleArchive()}
            />
          ) : null}

          {activePanel === 'edit' ? (
            <CreditCardEditForm
              card={card}
              busy={busy}
              onSubmit={handleUpdate}
              onCancel={() => setActivePanel('none')}
            />
          ) : null}

          {activePanel === 'pay' ? (
            <CreditCardPayForm
              cardAccountId={card.accountId}
              assetAccounts={assetAccounts}
              defaultAmount={card.currentStatement?.remainingDue}
              statementId={card.currentStatement?.id}
              busy={busy}
              onSubmit={handlePay}
              onCancel={() => setActivePanel('none')}
            />
          ) : null}

          {activePanel === 'expense' ? (
            <CreditCardExpenseForm
              accountId={card.accountId}
              categories={categoriesQuery.data ?? []}
              merchants={merchantsQuery.data ?? []}
              busy={busy}
              onSubmit={handleExpense}
              onCancel={() => setActivePanel('none')}
              onCreateCategory={async (name) => {
                const result = await createCategory.mutateAsync({ name })
                return { id: result.category.id }
              }}
              onCreateMerchant={async (name) => {
                const result = await createMerchant.mutateAsync({ name })
                return { id: result.merchant.id }
              }}
            />
          ) : null}
        </div>
      </CardContent>
    </Card>
  )
}

export function CreditCardEmptyState({ onAdd }: { onAdd: () => void }) {
  return (
    <div className="rounded-xl border border-dashed border-border bg-muted/10 p-10 text-center">
      <div className="mx-auto flex size-14 items-center justify-center rounded-full border border-border bg-muted/30">
        <CreditCard className="size-7 text-muted-foreground" />
      </div>
      <p className="mt-4 text-base font-medium">No credit cards yet</p>
      <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
        Add your cards to track utilization, statement cycles, payments, and rewards in one place.
      </p>
      <Button className="mt-5" size="sm" onClick={onAdd}>
        <PlusCircle className="size-4" />
        Add your first card
      </Button>
      <p className="mt-4 text-xs text-muted-foreground">
        Cards also appear in{' '}
        <Link to="/finance/accounts" className="text-emerald-400 hover:underline">
          Accounts
        </Link>{' '}
        as liability entries.
      </p>
    </div>
  )
}

export function CreditCardLoadingGrid() {
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      {[0, 1].map((key) => (
        <Card key={key} className="overflow-hidden">
          <div className="h-36 animate-pulse bg-muted/40" />
          <CardContent className="space-y-3 p-4">
            <div className="h-4 w-1/3 animate-pulse rounded bg-muted" />
            <div className="grid grid-cols-2 gap-2">
              {[0, 1, 2, 3].map((cell) => (
                <div key={cell} className="h-12 animate-pulse rounded bg-muted/60" />
              ))}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
