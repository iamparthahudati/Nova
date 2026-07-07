import { Card, CardContent, CardHeader } from '@/components/ui/card'

function MetricSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="h-4 w-24 animate-pulse rounded bg-muted" />
      </CardHeader>
      <CardContent>
        <div className="h-8 w-32 animate-pulse rounded bg-muted/80" />
      </CardContent>
    </Card>
  )
}

function PanelSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <Card>
      <CardHeader>
        <div className="h-5 w-40 animate-pulse rounded bg-muted" />
      </CardHeader>
      <CardContent className="space-y-2">
        {Array.from({ length: rows }).map((_, index) => (
          <div key={index} className="h-14 animate-pulse rounded-md bg-muted/50" />
        ))}
      </CardContent>
    </Card>
  )
}

export function FinanceDashboardSkeleton() {
  return (
    <div className="space-y-8">
      <Card className="overflow-hidden border-emerald-500/20 bg-gradient-to-br from-emerald-500/10 via-background to-background">
        <CardContent className="space-y-4 p-6">
          <div className="h-4 w-28 animate-pulse rounded bg-muted" />
          <div className="h-10 w-48 animate-pulse rounded bg-muted/80" />
          <div className="grid gap-3 sm:grid-cols-3">
            {[0, 1, 2].map((key) => (
              <div key={key} className="h-16 animate-pulse rounded-lg bg-muted/40" />
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[0, 1, 2, 3].map((key) => (
          <MetricSkeleton key={key} />
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <PanelSkeleton rows={4} />
        <PanelSkeleton rows={4} />
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <PanelSkeleton rows={3} />
        <PanelSkeleton rows={3} />
        <PanelSkeleton rows={3} />
      </div>
    </div>
  )
}
