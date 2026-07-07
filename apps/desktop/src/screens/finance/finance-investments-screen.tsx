import { TrendingUp } from 'lucide-react'
import { ScreenHeader } from '@/components/layout/screen-header'
import { Card, CardContent } from '@/components/ui/card'

const PLANNED_TYPES = [
  'Mutual Funds',
  'Stocks',
  'ETFs',
  'Bonds',
  'PPF',
  'NPS',
  'EPF',
  'Crypto',
  'Gold',
]

export function FinanceInvestmentsScreen() {
  return (
    <section>
      <ScreenHeader
        title="Investments"
        description="Portfolio tracking and investment accounts — coming soon."
      />
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center gap-4 py-12 text-center">
          <div className="rounded-full bg-muted p-4">
            <TrendingUp className="size-8 text-muted-foreground" />
          </div>
          <div className="max-w-md space-y-2">
            <p className="font-medium">Investment tracking is not yet available</p>
            <p className="text-sm text-muted-foreground">
              Nova will support investment accounts as a separate bounded context. Navigation is
              in place so holdings, allocation, and performance can be added without restructuring
              the finance module.
            </p>
          </div>
          <div className="flex flex-wrap justify-center gap-2 pt-2">
            {PLANNED_TYPES.map((type) => (
              <span
                key={type}
                className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground"
              >
                {type}
              </span>
            ))}
          </div>
        </CardContent>
      </Card>
    </section>
  )
}
