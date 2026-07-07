import { Link } from 'react-router-dom'
import {
  Activity,
  ArrowRight,
  Bell,
  Brain,
  ListTodo,
  Package,
  Wallet,
  type LucideIcon,
} from 'lucide-react'
import { Amount, MetricCard } from '@/components/finance/metric-card'
import { ScreenHeader } from '@/components/layout/screen-header'
import { QueryBoundary } from '@/components/query-boundary'
import { buttonVariants } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useFinanceDashboard } from '@/hooks/use-finance'
import { useHome } from '@/hooks/use-home'
import { cn, formatINR } from '@/lib/utils'
import type { HomeCard } from '@/view-models'

const CARD_ICONS: Record<string, LucideIcon> = {
  'list-todo': ListTodo,
  wallet: Wallet,
  activity: Activity,
  brain: Brain,
  bell: Bell,
  package: Package,
}

const CARD_LINKS: Record<string, string> = {
  open_tasks: '/tasks',
  earned_month: '/finance/transactions',
  spent_month: '/finance/transactions',
  memory_count: '/memory',
  reminder_count: '/',
  products_building: '/products',
}

const PANEL_LINKS: Record<string, string> = {
  reminders: '/',
  open_tasks: '/tasks',
  calendar: '/calendar',
}

function formatCardValue(card: HomeCard): string {
  if (card.id === 'earned_month' || card.id === 'spent_month') {
    const amount = Number(card.value)
    if (!Number.isNaN(amount)) {
      return formatINR(amount)
    }
  }
  return card.value
}

function FinanceSnapshot() {
  const finance = useFinanceDashboard()

  if (finance.isLoading) {
    return <p className="mb-6 text-sm text-muted-foreground">Loading finance snapshot…</p>
  }

  if (finance.isError || !finance.data) {
    return null
  }

  const data = finance.data
  return (
    <div className="mb-6 space-y-3">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-sm font-medium text-muted-foreground">Finance</h2>
        <Link to="/finance" className={cn(buttonVariants({ variant: 'ghost', size: 'sm' }), 'gap-1')}>
          Open finance
          <ArrowRight className="size-3.5" />
        </Link>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Net worth" value={formatINR(data.totalBalance)} />
        <MetricCard title="Spent this month" value={formatINR(data.spentMonth)} />
        <MetricCard title="Reward balance" value={String(data.rewardBalance)} subtitle="Points / units" />
        <MetricCard title="Cashback this month" value={formatINR(data.cashbackEarnedMonth)} tone="positive" />
      </div>
      {data.recentTransactions.length > 0 ? (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Recent transactions</CardTitle>
            <Link to="/finance/transactions" className={cn(buttonVariants({ variant: 'ghost', size: 'sm' }), 'gap-1')}>
              View all
              <ArrowRight className="size-3.5" />
            </Link>
          </CardHeader>
          <CardContent className="space-y-2">
            {data.recentTransactions.slice(0, 3).map((txn) => (
              <div
                key={txn.id}
                className="flex items-center justify-between rounded-md border border-border bg-muted/30 p-3"
              >
                <div>
                  <p className="text-sm font-medium">{txn.note || txn.merchantName || txn.kind}</p>
                  <p className="text-xs text-muted-foreground">
                    {txn.accountName} · {txn.occurredOn}
                  </p>
                </div>
                <Amount value={txn.amount} direction={txn.kind} />
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}
    </div>
  )
}

export function HomeScreen() {
  const home = useHome()

  return (
    <section>
      <ScreenHeader
        title="Home"
        description="Dashboard overview from backend projections."
      />
      <FinanceSnapshot />
      <QueryBoundary
        query={home}
        isEmpty={(data) => data.cards.length === 0 && data.panels.length === 0}
        loadingMessage="Loading home dashboard…"
        emptyMessage="No dashboard data available."
      >
        {(data) => (
          <>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {data.cards.map((card) => {
                const Icon = card.icon ? CARD_ICONS[card.icon] : undefined
                const href = CARD_LINKS[card.id]
                const content = (
                  <>
                    <CardHeader className="flex-row items-center justify-between space-y-0">
                      <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">{card.label}</CardTitle>
                      {Icon ? <Icon className="size-4 text-primary" /> : null}
                    </CardHeader>
                    <CardContent>
                      <p className="text-2xl font-semibold">{formatCardValue(card)}</p>
                    </CardContent>
                  </>
                )
                return href ? (
                  <Link key={card.id} to={href} className="block transition hover:opacity-90">
                    <Card>{content}</Card>
                  </Link>
                ) : (
                  <Card key={card.id}>{content}</Card>
                )
              })}
            </div>

            <div className="mt-4 grid gap-4 xl:grid-cols-3">
              {data.panels.map((panel) => (
                <Card key={panel.id} className="xl:col-span-1">
                  <CardHeader className="flex-row items-center justify-between space-y-0">
                    <CardTitle>{panel.title}</CardTitle>
                    {PANEL_LINKS[panel.id] ? (
                      <Link
                        to={PANEL_LINKS[panel.id]}
                        className="text-xs text-muted-foreground hover:text-foreground"
                      >
                        View all
                      </Link>
                    ) : null}
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    {panel.items.length === 0 ? (
                      <p className="text-muted-foreground">Nothing here yet.</p>
                    ) : (
                      panel.items.map((item) => (
                        <div key={item.id} className="rounded-md bg-muted/60 p-2">
                          <p>{item.primary}</p>
                          {item.secondary ? <p className="text-xs text-muted-foreground">{item.secondary}</p> : null}
                        </div>
                      ))
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </>
        )}
      </QueryBoundary>
    </section>
  )
}
