import { useState } from 'react'
import { Plus } from 'lucide-react'
import { CreditCardCreateForm } from '@/components/finance/credit-card-create-form'
import { CreditCardEmptyState, CreditCardLoadingGrid, CreditCardTile } from '@/components/finance/credit-card-tile'
import { FeedbackBanner } from '@/components/finance/feedback'
import { useFinanceFeedback } from '@/hooks/use-finance-feedback'
import { ScreenHeader } from '@/components/layout/screen-header'
import { Button } from '@/components/ui/button'
import { useCreditCards } from '@/hooks/use-finance'
import { useCreateCreditCard } from '@/hooks/use-finance-mutations'
import { ApiError } from '@/lib/api-client'

export function FinanceCreditCardsScreen() {
  const cards = useCreditCards()
  const createCreditCard = useCreateCreditCard()
  const [showForm, setShowForm] = useState(false)
  const { feedback, notify, reset } = useFinanceFeedback()

  async function handleCreate(values: {
    name: string
    creditLimit: string
    statementDay: string
    dueDayOffset: string
    network: string
    last4: string
    openingBalance: string
  }) {
    reset()
    try {
      const result = await createCreditCard.mutateAsync({
        name: values.name,
        credit_limit: Number(values.creditLimit),
        statement_day: Number(values.statementDay),
        due_day_offset: Number(values.dueDayOffset),
        opening_balance: Number(values.openingBalance) || 0,
        network: values.network || undefined,
        last4: values.last4 || undefined,
      })
      setShowForm(false)
      notify(result.meta.message)
    } catch (error) {
      notify(error instanceof ApiError ? error.message : 'Could not create credit card.', 'error')
    }
  }

  return (
    <section>
      <ScreenHeader
        title="Credit Cards"
        description="Track limits, utilization, statements, and payments for every card."
        actions={
          <Button size="sm" onClick={() => setShowForm((open) => !open)}>
            <Plus className="h-4 w-4" />
            Add credit card
          </Button>
        }
      />
      <FeedbackBanner feedback={feedback} />
      {showForm ? (
        <CreditCardCreateForm
          busy={createCreditCard.isPending}
          onSubmit={handleCreate}
          onCancel={() => setShowForm(false)}
        />
      ) : null}

      {cards.isLoading ? <CreditCardLoadingGrid /> : null}

      {cards.isError ? (
        <div className="rounded-md border border-destructive/40 bg-destructive/10 p-4 text-sm">
          <p className="font-medium text-destructive">Failed to load credit cards</p>
          <p className="mt-1 text-muted-foreground">{cards.error.message}</p>
          <Button className="mt-3" size="sm" variant="secondary" onClick={() => void cards.refetch()}>
            Retry
          </Button>
        </div>
      ) : null}

      {!cards.isLoading && !cards.isError && cards.data && cards.data.length > 0 ? (
        <div className="grid gap-4 xl:grid-cols-2">
          {cards.data.map((card) => (
            <CreditCardTile key={card.accountId} card={card} onFeedback={notify} />
          ))}
        </div>
      ) : null}

      {!cards.isLoading && !cards.isError && cards.data?.length === 0 && !showForm ? (
        <CreditCardEmptyState onAdd={() => setShowForm(true)} />
      ) : null}
    </section>
  )
}
