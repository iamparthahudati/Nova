import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScreenHeader } from '@/components/layout/screen-header'
import { QueryBoundary } from '@/components/query-boundary'
import { useMemories } from '@/hooks/use-memories'

export function MemoryScreen() {
  const memories = useMemories()

  return (
    <section>
      <ScreenHeader
        title="Memory"
        description="Semantic memory ledger from the backend memories endpoint."
      />
      <Card>
        <CardHeader>
          <CardTitle>Memory ledger</CardTitle>
        </CardHeader>
        <CardContent>
          <QueryBoundary
            query={memories}
            isEmpty={(data) => data.memories.length === 0}
            loadingMessage="Loading memories…"
            emptyMessage="No memories indexed yet."
          >
            {(data) => (
              <div className="space-y-3">
                {data.memories.map((memory) => (
                  <div key={memory.id} className="rounded-lg border border-border bg-muted/30 p-3">
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      <Badge variant="secondary">{memory.tier}</Badge>
                      <Badge variant="outline">{memory.sourceType}</Badge>
                      <span className="text-xs text-muted-foreground">importance {memory.importance.toFixed(2)}</span>
                      <span className="text-xs text-muted-foreground">accessed {memory.accessCount}x</span>
                    </div>
                    <p className="text-sm">{memory.text}</p>
                  </div>
                ))}
              </div>
            )}
          </QueryBoundary>
        </CardContent>
      </Card>
    </section>
  )
}
