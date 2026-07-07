import { Card, CardContent, CardHeader } from '@/components/ui/card'

function MetricSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="h-4 w-28 animate-pulse rounded bg-muted" />
      </CardHeader>
      <CardContent>
        <div className="h-8 w-32 animate-pulse rounded bg-muted/80" />
      </CardContent>
    </Card>
  )
}

export function RewardsSkeleton() {
  return (
    <div className="space-y-8">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[0, 1, 2, 3].map((key) => (
          <MetricSkeleton key={key} />
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {[0, 1, 2].map((key) => (
          <Card key={key}>
            <CardContent className="space-y-3 p-5">
              <div className="h-5 w-40 animate-pulse rounded bg-muted" />
              <div className="h-4 w-24 animate-pulse rounded bg-muted/70" />
              <div className="h-8 w-28 animate-pulse rounded bg-muted/80" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardHeader>
          <div className="h-5 w-32 animate-pulse rounded bg-muted" />
        </CardHeader>
        <CardContent className="space-y-3">
          {[0, 1, 2, 3].map((key) => (
            <div key={key} className="h-14 animate-pulse rounded-md bg-muted/50" />
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
