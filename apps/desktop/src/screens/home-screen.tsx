import {
  Activity,
  Bell,
  Brain,
  ListTodo,
  Package,
  Wallet,
  type LucideIcon,
} from 'lucide-react'
import { ScreenHeader } from '@/components/layout/screen-header'
import { QueryBoundary } from '@/components/query-boundary'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useHome } from '@/hooks/use-home'
import { formatINR } from '@/lib/utils'
import type { HomeCard } from '@/view-models'

const CARD_ICONS: Record<string, LucideIcon> = {
  'list-todo': ListTodo,
  wallet: Wallet,
  activity: Activity,
  brain: Brain,
  bell: Bell,
  package: Package,
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

export function HomeScreen() {
  const home = useHome()

  return (
    <section>
      <ScreenHeader
        title="Home"
        description="Dashboard overview from the backend home projection."
      />
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
                return (
                  <Card key={card.id}>
                    <CardHeader className="flex-row items-center justify-between space-y-0">
                      <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">{card.label}</CardTitle>
                      {Icon ? <Icon className="size-4 text-primary" /> : null}
                    </CardHeader>
                    <CardContent>
                      <p className="text-2xl font-semibold">{formatCardValue(card)}</p>
                    </CardContent>
                  </Card>
                )
              })}
            </div>

            <div className="mt-4 grid gap-4 xl:grid-cols-3">
              {data.panels.map((panel) => (
                <Card key={panel.id} className="xl:col-span-1">
                  <CardHeader>
                    <CardTitle>{panel.title}</CardTitle>
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
