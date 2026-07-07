import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { CreditCard } from 'lucide-react'
import {
  StatementCard,
  StatementEmptyState,
  StatementLoadingGrid,
} from '@/components/finance/statement-card'
import { ScreenHeader } from '@/components/layout/screen-header'
import { Button, buttonVariants } from '@/components/ui/button'
import { useAccounts, useCreditCards, useStatements } from '@/hooks/use-finance'
import { cn } from '@/lib/utils'

export function FinanceStatementsScreen() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const cardsQuery = useCreditCards()
  const accountsQuery = useAccounts(false)
  const cardAccounts = cardsQuery.data ?? []
  const paramAccountId = searchParams.get('accountId')
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(
    paramAccountId ? Number(paramAccountId) : null,
  )

  useEffect(() => {
    if (paramAccountId) setSelectedAccountId(Number(paramAccountId))
  }, [paramAccountId])

  const activeAccountId = selectedAccountId ?? cardAccounts[0]?.accountId ?? null
  const statementsQuery = useStatements(activeAccountId)
  const activeCard = cardAccounts.find((card) => card.accountId === activeAccountId)
  const loading = cardsQuery.isLoading || accountsQuery.isLoading || statementsQuery.isLoading
  const error = cardsQuery.error ?? statementsQuery.error

  return (
    <section>
      <ScreenHeader
        title="Statements"
        description="Billing cycles, payment status, and spend summaries for every card."
      />

      {cardAccounts.length > 0 ? (
        <div className="mb-4">
          <label className="space-y-1">
            <span className="text-xs text-muted-foreground">Credit card</span>
            <select
              className="w-full max-w-sm rounded-md border border-border bg-background px-3 py-2 text-sm"
              value={activeAccountId ?? ''}
              onChange={(e) => setSelectedAccountId(Number(e.target.value))}
            >
              {cardAccounts.map((card) => (
                <option key={card.accountId} value={card.accountId}>
                  {card.name}
                </option>
              ))}
            </select>
          </label>
        </div>
      ) : null}

      {loading ? <StatementLoadingGrid /> : null}

      {error ? (
        <div className="rounded-md border border-destructive/40 bg-destructive/10 p-4 text-sm">
          <p className="font-medium text-destructive">Failed to load statements</p>
          <p className="mt-1 text-muted-foreground">{error.message}</p>
          <Button
            className="mt-3"
            size="sm"
            variant="secondary"
            onClick={() => {
              void cardsQuery.refetch()
              void statementsQuery.refetch()
            }}
          >
            Retry
          </Button>
        </div>
      ) : null}

      {!loading && !error && statementsQuery.data && statementsQuery.data.length > 0 ? (
        <div className="space-y-4">
          {statementsQuery.data.map((statement) => (
            <StatementCard key={statement.id} statement={statement} cardName={activeCard?.name} />
          ))}
        </div>
      ) : null}

      {!loading && !error && cardAccounts.length === 0 ? (
        <StatementEmptyState onBrowseCards={() => navigate('/finance/credit-cards')} />
      ) : null}

      {!loading && !error && cardAccounts.length > 0 && statementsQuery.data?.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border bg-muted/10 p-10 text-center">
          <div className="mx-auto flex size-14 items-center justify-center rounded-full border border-border bg-muted/30">
            <CreditCard className="size-7 text-muted-foreground" />
          </div>
          <p className="mt-4 text-base font-medium">No statements for {activeCard?.name ?? 'this card'}</p>
          <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
            Statements generate automatically from your card&apos;s billing cycle once transactions are logged.
          </p>
          {activeCard ? (
            <Link
              to={`/finance/credit-cards/${activeCard.accountId}`}
              className={cn(buttonVariants({ variant: 'outline', size: 'sm' }), 'mt-5 inline-flex')}
            >
              View card details
            </Link>
          ) : null}
        </div>
      ) : null}
    </section>
  )
}
