import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Gift, Percent, Sparkles } from 'lucide-react'
import { ConfirmActionBar } from '@/components/finance/confirm-action-bar'
import { CreditCardEditForm } from '@/components/finance/credit-card-edit-form'
import { CreditCardExpenseForm } from '@/components/finance/credit-card-expense-form'
import { CreditCardPayForm } from '@/components/finance/credit-card-pay-form'
import { CreditCardUtilizationHistory } from '@/components/finance/credit-card-utilization-history'
import { FeedbackBanner } from '@/components/finance/feedback'
import { useFinanceFeedback } from '@/hooks/use-finance-feedback'
import {
  CreditCardFace,
  CreditCardMetricsGrid,
  CreditCardStatementBlock,
} from '@/components/finance/credit-card-visuals'
import { MetricCard, UtilizationBar } from '@/components/finance/metric-card'
import { ScreenHeader } from '@/components/layout/screen-header'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { QueryBoundary } from '@/components/query-boundary'
import {
  useAccounts,
  useCashbackSummary,
  useCategories,
  useCreditCard,
  useMerchants,
  useRewardPrograms,
  useStatements,
} from '@/hooks/use-finance'
import {
  useArchiveAccount,
  useCreateCardPayment,
  useCreateCategory,
  useCreateMerchant,
  useCreateTransaction,
  useUpdateCreditCard,
} from '@/hooks/use-finance-mutations'
import { ApiError } from '@/lib/api-client'
import { formatINR, formatShortDate } from '@/lib/utils'

type DetailPanel = 'none' | 'pay' | 'expense' | 'edit' | 'archive'

export function FinanceCreditCardDetailScreen() {
  const { accountId } = useParams()
  const navigate = useNavigate()
  const parsedId = Number(accountId)
  const cardQuery = useCreditCard(Number.isFinite(parsedId) ? parsedId : null)
  const statementsQuery = useStatements(Number.isFinite(parsedId) ? parsedId : null, 12)
  const rewardPrograms = useRewardPrograms(Number.isFinite(parsedId) ? parsedId : undefined)
  const cashback = useCashbackSummary()
  const accountsQuery = useAccounts(false)
  const categoriesQuery = useCategories()
  const merchantsQuery = useMerchants()
  const updateCreditCard = useUpdateCreditCard()
  const archiveAccount = useArchiveAccount()
  const createTransaction = useCreateTransaction()
  const createCardPayment = useCreateCardPayment()
  const createCategory = useCreateCategory()
  const createMerchant = useCreateMerchant()
  const [panel, setPanel] = useState<DetailPanel>('none')
  const { feedback, notify } = useFinanceFeedback()

  const assetAccounts = (accountsQuery.data ?? []).filter((account) => account.classification === 'asset')
  const busy =
    updateCreditCard.isPending ||
    archiveAccount.isPending ||
    createTransaction.isPending ||
    createCardPayment.isPending

  if (!Number.isFinite(parsedId)) {
    return (
      <section>
        <ScreenHeader title="Credit card" description="Invalid card id." />
        <Button variant="outline" size="sm" onClick={() => navigate('/finance/credit-cards')}>
          <ArrowLeft className="size-4" />
          Back to cards
        </Button>
      </section>
    )
  }

  return (
    <section>
      <div className="mb-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/finance/credit-cards')}>
          <ArrowLeft className="size-4" />
          Credit cards
        </Button>
      </div>

      <QueryBoundary
        query={cardQuery}
        loadingMessage="Loading card details…"
        emptyMessage="Credit card not found."
      >
        {(card) => {
          const cardRewards = rewardPrograms.data ?? []
          const cardCashbackRules = (cashback.data?.rules ?? []).filter((rule) =>
            cardRewards.some((program) => program.id === rule.programId),
          )

          return (
            <>
              <ScreenHeader
                title={card.name}
                description="Statement cycles, utilization, payments, and rewards for this card."
                actions={
                  <div className="flex flex-wrap gap-2">
                    <Button variant="outline" size="sm" onClick={() => setPanel(panel === 'pay' ? 'none' : 'pay')}>
                      Pay card
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => setPanel(panel === 'expense' ? 'none' : 'expense')}>
                      Add expense
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => setPanel(panel === 'edit' ? 'none' : 'edit')}>
                      Edit
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => setPanel('archive')}>
                      Archive
                    </Button>
                  </div>
                }
              />

              <FeedbackBanner feedback={feedback} />

              <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
                <div className="space-y-4">
                  <CreditCardFace name={card.name} network={card.network} last4={card.last4} />
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Card overview</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <CreditCardMetricsGrid
                        creditLimit={card.creditLimit}
                        availableLimit={card.availableLimit}
                        outstanding={card.outstanding}
                        utilizationPercent={card.utilizationPercent}
                        statementDay={card.statementDay}
                        dueDayOffset={card.dueDayOffset}
                      />
                      <UtilizationBar percent={card.utilizationPercent ?? 0} />
                    </CardContent>
                  </Card>

                  {panel === 'archive' ? (
                    <ConfirmActionBar
                      message={`Archive ${card.name}?`}
                      confirmLabel="Archive"
                      destructive
                      busy={busy}
                      onCancel={() => setPanel('none')}
                      onConfirm={() =>
                        void archiveAccount.mutateAsync(card.accountId).then((result) => {
                          notify(result.meta.message)
                          navigate('/finance/credit-cards')
                        }).catch((error) => {
                          notify(error instanceof ApiError ? error.message : 'Could not archive card.', 'error')
                        })
                      }
                    />
                  ) : null}

                  {panel === 'edit' ? (
                    <Card>
                      <CardContent className="p-4">
                        <CreditCardEditForm
                          card={card}
                          busy={busy}
                          onSubmit={async (input) => {
                            const result = await updateCreditCard.mutateAsync({ accountId: card.accountId, input })
                            notify(result.meta.message)
                            setPanel('none')
                          }}
                          onCancel={() => setPanel('none')}
                        />
                      </CardContent>
                    </Card>
                  ) : null}

                  {panel === 'pay' ? (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Pay card</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <CreditCardPayForm
                          cardAccountId={card.accountId}
                          assetAccounts={assetAccounts}
                          defaultAmount={card.currentStatement?.remainingDue}
                          statementId={card.currentStatement?.id}
                          busy={busy}
                          onSubmit={async (values) => {
                            const result = await createCardPayment.mutateAsync({
                              from_account_id: values.fromAccountId,
                              card_account_id: card.accountId,
                              amount: values.amount,
                              occurred_on: values.occurredOn,
                              statement_id: values.statementId ?? null,
                            })
                            notify(result.meta.message)
                            setPanel('none')
                          }}
                          onCancel={() => setPanel('none')}
                        />
                      </CardContent>
                    </Card>
                  ) : null}

                  {panel === 'expense' ? (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Add expense</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <CreditCardExpenseForm
                          accountId={card.accountId}
                          categories={categoriesQuery.data ?? []}
                          merchants={merchantsQuery.data ?? []}
                          busy={busy}
                          onSubmit={async (values) => {
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
                            notify(result.meta.message)
                            setPanel('none')
                          }}
                          onCancel={() => setPanel('none')}
                          onCreateCategory={async (name) => {
                            const result = await createCategory.mutateAsync({ name })
                            return { id: result.category.id }
                          }}
                          onCreateMerchant={async (name) => {
                            const result = await createMerchant.mutateAsync({ name })
                            return { id: result.merchant.id }
                          }}
                        />
                      </CardContent>
                    </Card>
                  ) : null}
                </div>

                <div className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Upcoming payment</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {card.currentStatement ? (
                        <div className="space-y-2 text-sm">
                          <div className="flex items-center justify-between">
                            <span className="text-muted-foreground">Due date</span>
                            <span className="font-medium">
                              {formatShortDate(card.currentStatement.dueDate) ?? card.currentStatement.dueDate}
                            </span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-muted-foreground">Amount due</span>
                            <span className="font-semibold text-rose-400">
                              {formatINR(card.currentStatement.remainingDue ?? 0)}
                            </span>
                          </div>
                          {card.autopay ? <Badge variant="secondary">Autopay enabled</Badge> : null}
                        </div>
                      ) : (
                        <p className="text-sm text-muted-foreground">No open statement cycle yet.</p>
                      )}
                    </CardContent>
                  </Card>

                  {card.currentStatement ? (
                    <CreditCardStatementBlock
                      title="Current statement"
                      statement={card.currentStatement}
                      creditLimit={card.creditLimit}
                      variant="current"
                    />
                  ) : null}

                  {card.previousStatement ? (
                    <CreditCardStatementBlock
                      title="Previous statement"
                      statement={card.previousStatement}
                      creditLimit={card.creditLimit}
                      variant="previous"
                    />
                  ) : null}

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Utilization history</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <QueryBoundary query={statementsQuery} loadingMessage="Loading history…">
                        {(statements) => (
                          <CreditCardUtilizationHistory
                            statements={statements}
                            creditLimit={card.creditLimit}
                            currentUtilization={card.utilizationPercent}
                          />
                        )}
                      </QueryBoundary>
                    </CardContent>
                  </Card>

                  <div className="grid gap-4 sm:grid-cols-2">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="flex items-center gap-2 text-base">
                          <Gift className="size-4 text-amber-400" />
                          Rewards
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3 text-sm">
                        {cardRewards.length === 0 ? (
                          <p className="text-muted-foreground">No reward programs linked to this card.</p>
                        ) : (
                          cardRewards.map((program) => (
                            <div key={program.id} className="rounded-md border border-border/60 p-3">
                              <p className="font-medium">{program.name}</p>
                              <p className="text-xs text-muted-foreground">{program.unit}</p>
                              <p className="mt-2 text-lg font-semibold">{program.balance?.balance ?? 0}</p>
                            </div>
                          ))
                        )}
                        <Link to="/finance/rewards" className="text-xs text-emerald-400 hover:underline">
                          Open rewards
                        </Link>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="flex items-center gap-2 text-base">
                          <Percent className="size-4 text-emerald-400" />
                          Cashback
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3 text-sm">
                        {cardCashbackRules.length === 0 ? (
                          <p className="text-muted-foreground">No cashback rules for this card yet.</p>
                        ) : (
                          cardCashbackRules.map((rule) => (
                            <div key={rule.id} className="rounded-md border border-border/60 p-3">
                              <p className="font-medium">{rule.name}</p>
                              <Badge className="mt-1">{rule.flatRatePercent}% base</Badge>
                            </div>
                          ))
                        )}
                        <p className="text-xs text-muted-foreground">
                          Monthly earned (all cards): {formatINR(cashback.data?.monthlyEarned ?? 0)}
                        </p>
                        <Link to="/finance/cashback" className="text-xs text-emerald-400 hover:underline">
                          Open cashback
                        </Link>
                      </CardContent>
                    </Card>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-3">
                    <MetricCard
                      title="Outstanding"
                      value={formatINR(card.outstanding ?? 0)}
                      tone="negative"
                    />
                    <MetricCard
                      title="Available"
                      value={formatINR(card.availableLimit ?? 0)}
                      tone="positive"
                    />
                    <MetricCard
                      title="Limit"
                      value={formatINR(card.creditLimit)}
                      subtitle={card.autopay ? 'Autopay on' : undefined}
                    />
                  </div>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate(`/finance/statements?accountId=${card.accountId}`)}
                  >
                    <Sparkles className="size-4" />
                    View full statement history
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
