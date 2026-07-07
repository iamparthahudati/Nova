import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  Banknote,
  CalendarClock,
  CreditCard,
  Gift,
  PlusCircle,
  Receipt,
  Sparkles,
  TrendingUp,
  Wallet,
} from 'lucide-react'
import { FinanceDashboardEmpty } from '@/components/finance/finance-dashboard-empty'
import { FinanceDashboardSkeleton } from '@/components/finance/finance-dashboard-skeleton'
import { Amount, MetricCard, UtilizationBar } from '@/components/finance/metric-card'
import { ScreenHeader } from '@/components/layout/screen-header'
import { Badge } from '@/components/ui/badge'
import { Button, buttonVariants } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useFinanceDashboard } from '@/hooks/use-finance'
import { statementStatusClass, statementStatusTone } from '@/lib/finance/credit-card-display'
import { daysUntilDue } from '@/lib/finance/statement-display'
import { cn, formatINR, formatShortDate } from '@/lib/utils'
import type { FinanceDashboard, FinanceTransaction, LatestReward, UpcomingDueDate } from '@/view-models/finance'

function isDashboardEmpty(data: FinanceDashboard): boolean {
  return (
    data.recentTransactions.length === 0 &&
    data.incomeMonth === 0 &&
    data.spentMonth === 0 &&
    data.creditCardCount === 0 &&
    data.totalAssets === 0 &&
    data.totalLiabilities === 0
  )
}

function savingsRate(data: FinanceDashboard): number {
  if (data.incomeMonth <= 0) return 0
  return Math.max(0, Math.min(100, (data.savingsMonth / data.incomeMonth) * 100))
}

function formatRewardAmount(reward: LatestReward): string {
  if (reward.unit === 'cashback_minor') return formatINR(reward.amountDisplay)
  return `${reward.amountDisplay.toLocaleString('en-IN')} pts`
}

function SectionHeader({
  title,
  description,
  action,
}: {
  title: string
  description?: string
  action?: ReactNode
}) {
  return (
    <div className="mb-4 flex items-start justify-between gap-3">
      <div>
        <h2 className="text-base font-semibold">{title}</h2>
        {description ? <p className="mt-0.5 text-sm text-muted-foreground">{description}</p> : null}
      </div>
      {action}
    </div>
  )
}

function QuickActions() {
  const actions = [
    { label: 'Add transaction', to: '/finance/transactions', icon: Receipt },
    { label: 'Add account', to: '/finance/accounts', icon: Banknote },
    { label: 'Add credit card', to: '/finance/credit-cards', icon: CreditCard },
    { label: 'Pay card', to: '/finance/credit-cards', icon: Wallet },
  ]

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {actions.map(({ label, to, icon: Icon }) => (
        <Link
          key={label}
          to={to}
          className={cn(
            buttonVariants({ variant: 'outline' }),
            'h-auto justify-start gap-3 px-4 py-3 text-left hover:border-emerald-500/40 hover:bg-emerald-500/5',
          )}
        >
          <span className="flex size-9 items-center justify-center rounded-lg bg-muted/60">
            <Icon className="size-4 text-emerald-400" />
          </span>
          <span className="text-sm font-medium">{label}</span>
        </Link>
      ))}
    </div>
  )
}

function HeroSummary({ data }: { data: FinanceDashboard }) {
  return (
    <Card className="overflow-hidden border-emerald-500/20 bg-gradient-to-br from-emerald-500/10 via-background to-background">
      <CardContent className="space-y-5 p-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Net worth</p>
            <p className="mt-1 text-4xl font-semibold tracking-tight text-foreground">{formatINR(data.totalBalance)}</p>
          </div>
          <Badge variant="outline" className="border-emerald-500/30 text-emerald-400">
            <Sparkles className="mr-1 size-3" />
            Live projection
          </Badge>
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          <SummaryPill label="Assets" value={formatINR(data.totalAssets)} tone="positive" />
          <SummaryPill label="Liabilities" value={formatINR(data.totalLiabilities)} tone="negative" />
          <SummaryPill label="Cash available" value={formatINR(data.cashAvailable)} />
        </div>
      </CardContent>
    </Card>
  )
}

function SummaryPill({
  label,
  value,
  tone = 'default',
}: {
  label: string
  value: string
  tone?: 'default' | 'positive' | 'negative'
}) {
  const toneClass =
    tone === 'positive' ? 'text-emerald-400' : tone === 'negative' ? 'text-rose-400' : 'text-foreground'
  return (
    <div className="rounded-xl border border-border/70 bg-background/50 px-4 py-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={cn('mt-1 text-lg font-semibold', toneClass)}>{value}</p>
    </div>
  )
}

function CreditSection({ data }: { data: FinanceDashboard }) {
  return (
    <section>
      <SectionHeader
        title="Credit cards"
        description="Outstanding balances, available credit, and cards approaching due dates."
        action={
          <Link to="/finance/credit-cards" className={cn(buttonVariants({ variant: 'ghost', size: 'sm' }), 'gap-1')}>
            Manage cards
            <ArrowRight className="size-3.5" />
          </Link>
        }
      />
      {data.creditCardCount === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center gap-3 p-8 text-center">
            <CreditCard className="size-8 text-muted-foreground" />
            <p className="text-sm font-medium">No credit cards yet</p>
            <p className="max-w-sm text-sm text-muted-foreground">
              Add a card to track utilization, statement cycles, and payment due dates.
            </p>
            <Link to="/finance/credit-cards" className={cn(buttonVariants({ size: 'sm' }), 'inline-flex')}>
              <PlusCircle className="size-4" />
              Add credit card
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="grid gap-4 sm:grid-cols-2">
            <MetricCard title="Outstanding" value={formatINR(data.totalOutstanding)} tone="negative" />
            <MetricCard title="Available credit" value={formatINR(data.totalAvailableCredit)} tone="positive" />
            <MetricCard
              title="Cards near due"
              value={String(data.cardsNearDueCount)}
              subtitle="Due within 7 days"
              tone={data.cardsNearDueCount > 0 ? 'warning' : 'default'}
            />
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Portfolio utilization</CardTitle>
              </CardHeader>
              <CardContent>
                <UtilizationBar percent={data.creditUtilizationPercent} />
              </CardContent>
            </Card>
          </div>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Utilization snapshot</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Used</span>
                <span className="font-medium">{formatINR(data.totalOutstanding)}</span>
              </div>
              <UtilizationBar percent={data.creditUtilizationPercent} />
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Available</span>
                <span className="font-medium text-emerald-400">{formatINR(data.totalAvailableCredit)}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </section>
  )
}

function MonthSection({ data }: { data: FinanceDashboard }) {
  const rate = savingsRate(data)
  const expenseShare = data.incomeMonth > 0 ? Math.min(100, (data.spentMonth / data.incomeMonth) * 100) : 0

  return (
    <section>
      <SectionHeader
        title="This month"
        description="Income, spending, savings, and rewards earned in the current period."
        action={
          <Link to="/finance/transactions" className={cn(buttonVariants({ variant: 'ghost', size: 'sm' }), 'gap-1')}>
            View transactions
            <ArrowRight className="size-3.5" />
          </Link>
        }
      />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <MetricCard title="Income" value={formatINR(data.incomeMonth)} tone="positive" />
        <MetricCard title="Expense" value={formatINR(data.spentMonth)} tone="negative" />
        <MetricCard
          title="Savings"
          value={formatINR(data.savingsMonth)}
          subtitle={`${rate.toFixed(0)}% of income`}
          tone={data.savingsMonth >= 0 ? 'positive' : 'negative'}
        />
        <MetricCard title="Cashback earned" value={formatINR(data.cashbackEarnedMonth)} tone="positive" />
        <MetricCard
          title="Rewards earned"
          value={data.rewardsEarnedMonth.toLocaleString('en-IN')}
          subtitle="Points this month"
        />
      </div>
      <Card className="mt-4">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">Cash flow mix</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <FlowBar label="Income retained" percent={rate} tone="bg-emerald-500" />
          <FlowBar label="Expenses" percent={expenseShare} tone="bg-rose-500" />
        </CardContent>
      </Card>
    </section>
  )
}

function FlowBar({ label, percent, tone }: { label: string; percent: number; tone: string }) {
  const clamped = Math.min(Math.max(percent, 0), 100)
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{label}</span>
        <span>{clamped.toFixed(0)}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div className={cn('h-full rounded-full transition-all', tone)} style={{ width: `${clamped}%` }} />
      </div>
    </div>
  )
}

function UpcomingSection({ data }: { data: FinanceDashboard }) {
  return (
    <section>
      <SectionHeader title="Upcoming" description="Statements due, recent activity, and latest rewards." />
      <div className="grid gap-4 xl:grid-cols-3">
        <DueDatesPanel items={data.upcomingDueDates} />
        <RecentTransactionsPanel transactions={data.recentTransactions} />
        <LatestRewardsPanel rewards={data.latestRewards} />
      </div>
    </section>
  )
}

function DueDatesPanel({ items }: { items: UpcomingDueDate[] }) {
  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0">
        <CardTitle className="text-sm font-medium">Statements due</CardTitle>
        <Link to="/finance/statements" className={cn(buttonVariants({ variant: 'ghost', size: 'sm' }))}>
          View all
        </Link>
      </CardHeader>
      <CardContent className="space-y-2">
        {items.length === 0 ? (
          <p className="rounded-md border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
            No upcoming statement due dates.
          </p>
        ) : (
          items.slice(0, 5).map((item) => <DueDateRow key={item.statementId} item={item} />)
        )}
      </CardContent>
    </Card>
  )
}

function DueDateRow({ item }: { item: UpcomingDueDate }) {
  const daysLeft = daysUntilDue(item.dueDate)
  const tone = statementStatusTone(item.status)

  return (
    <Link
      to={`/finance/statements/${item.statementId}`}
      className="flex items-center justify-between rounded-lg border border-border bg-muted/20 p-3 transition-colors hover:border-emerald-500/30 hover:bg-muted/40"
    >
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">{item.cardName}</p>
        <p className="mt-0.5 flex items-center gap-1 text-xs text-muted-foreground">
          <CalendarClock className="size-3.5" />
          Due {formatShortDate(item.dueDate) ?? item.dueDate}
          {daysLeft >= 0 && item.status !== 'paid' ? (
            <span className="text-amber-400">
              · {daysLeft === 0 ? 'today' : `${daysLeft}d left`}
            </span>
          ) : null}
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <span
          className={cn(
            'inline-flex rounded-full border px-2 py-0.5 text-xs font-medium capitalize',
            statementStatusClass(tone),
          )}
        >
          {item.status}
        </span>
        {item.remainingDue != null ? (
          <span className="text-sm font-semibold">{formatINR(item.remainingDue)}</span>
        ) : null}
      </div>
    </Link>
  )
}

function RecentTransactionsPanel({ transactions }: { transactions: FinanceTransaction[] }) {
  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0">
        <CardTitle className="text-sm font-medium">Recent transactions</CardTitle>
        <Link to="/finance/transactions" className={cn(buttonVariants({ variant: 'ghost', size: 'sm' }))}>
          View all
        </Link>
      </CardHeader>
      <CardContent className="space-y-2">
        {transactions.length === 0 ? (
          <div className="rounded-md border border-dashed border-border p-6 text-center">
            <p className="text-sm font-medium">No recent transactions</p>
            <p className="mt-1 text-sm text-muted-foreground">Log income and expenses to populate activity.</p>
            <Link to="/finance/transactions" className={cn(buttonVariants({ size: 'sm' }), 'mt-4 inline-flex')}>
              Add transaction
            </Link>
          </div>
        ) : (
          transactions.slice(0, 5).map((txn) => <TransactionRow key={txn.id} txn={txn} />)
        )}
      </CardContent>
    </Card>
  )
}

function TransactionRow({ txn }: { txn: FinanceTransaction }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border bg-muted/20 p-3">
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">{txn.note || txn.merchantName || txn.kind}</p>
        <p className="mt-0.5 truncate text-xs text-muted-foreground">
          {txn.accountName} · {formatShortDate(txn.occurredOn) ?? txn.occurredOn}
        </p>
      </div>
      <Amount value={txn.amount} direction={txn.kind} />
    </div>
  )
}

function LatestRewardsPanel({ rewards }: { rewards: LatestReward[] }) {
  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0">
        <CardTitle className="text-sm font-medium">Latest rewards</CardTitle>
        <Link to="/finance/rewards" className={cn(buttonVariants({ variant: 'ghost', size: 'sm' }))}>
          View all
        </Link>
      </CardHeader>
      <CardContent className="space-y-2">
        {rewards.length === 0 ? (
          <div className="rounded-md border border-dashed border-border p-6 text-center">
            <Gift className="mx-auto size-6 text-muted-foreground" />
            <p className="mt-2 text-sm font-medium">No reward activity yet</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Configure reward programs on your credit cards to track earnings.
            </p>
            <Link to="/finance/rewards" className={cn(buttonVariants({ size: 'sm' }), 'mt-4 inline-flex')}>
              Go to rewards
            </Link>
          </div>
        ) : (
          rewards.map((reward) => <RewardRow key={reward.id} reward={reward} />)
        )}
      </CardContent>
    </Card>
  )
}

function RewardRow({ reward }: { reward: LatestReward }) {
  const earned = reward.kind === 'earned'
  return (
    <div className="flex items-center justify-between rounded-lg border border-border bg-muted/20 p-3">
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">{reward.programName}</p>
        <p className="mt-0.5 truncate text-xs text-muted-foreground">
          {reward.note || reward.kind} · {formatShortDate(reward.occurredOn) ?? reward.occurredOn}
        </p>
      </div>
      <span className={cn('text-sm font-semibold', earned ? 'text-emerald-400' : 'text-rose-400')}>
        {earned ? '+' : '-'}
        {formatRewardAmount(reward)}
      </span>
    </div>
  )
}

function DashboardContent({ data }: { data: FinanceDashboard }) {
  if (isDashboardEmpty(data)) {
    return <FinanceDashboardEmpty />
  }

  return (
    <div className="space-y-8">
      <HeroSummary data={data} />
      <section>
        <SectionHeader title="Quick actions" description="Jump straight into the flows you use most." />
        <QuickActions />
      </section>
      <CreditSection data={data} />
      <MonthSection data={data} />
      <UpcomingSection data={data} />
      <Card className="border-border/60 bg-muted/10">
        <CardContent className="flex flex-wrap items-center justify-between gap-3 p-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <TrendingUp className="size-4 text-emerald-400" />
            <span>
              Tracking {data.accountCount} account{data.accountCount === 1 ? '' : 's'} and {data.creditCardCount}{' '}
              credit card{data.creditCardCount === 1 ? '' : 's'}
            </span>
          </div>
          <span>Reward balance: {data.rewardBalance.toLocaleString('en-IN')} pts</span>
        </CardContent>
      </Card>
    </div>
  )
}

export function FinanceDashboardScreen() {
  const dashboard = useFinanceDashboard()

  return (
    <section>
      <ScreenHeader
        title="Finance"
        description="Your command center — net worth, cards, monthly cash flow, and what's due next."
      />

      {dashboard.isLoading ? <FinanceDashboardSkeleton /> : null}

      {dashboard.isError ? (
        <div className="rounded-md border border-destructive/40 bg-destructive/10 p-4 text-sm">
          <p className="font-medium text-destructive">Failed to load finance dashboard</p>
          <p className="mt-1 text-muted-foreground">{dashboard.error.message}</p>
          <Button className="mt-3" size="sm" variant="secondary" onClick={() => void dashboard.refetch()}>
            Retry
          </Button>
        </div>
      ) : null}

      {!dashboard.isLoading && !dashboard.isError && dashboard.data ? (
        <DashboardContent data={dashboard.data} />
      ) : null}
    </section>
  )
}
