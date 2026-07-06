import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScreenHeader } from '@/components/layout/screen-header'
import { QueryBoundary } from '@/components/query-boundary'
import { useGraph } from '@/hooks/use-graph'

export function KnowledgeGraphScreen() {
  const graph = useGraph()

  return (
    <section>
      <ScreenHeader
        title="Knowledge Graph"
        description="Entity and relation browser from the backend graph endpoint."
      />
      <QueryBoundary
        query={graph}
        isEmpty={(data) => data.entities.length === 0 && data.edges.length === 0}
        loadingMessage="Loading knowledge graph…"
        emptyMessage="The knowledge graph is empty."
      >
        {(data) => (
          <div className="grid gap-4 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Entities</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {data.entities.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No entities yet.</p>
                ) : (
                  data.entities.map((entity) => (
                    <div key={entity.id} className="rounded-md border border-border bg-muted/40 p-3 text-sm">
                      <p className="font-medium">{entity.canonicalName}</p>
                      <p className="text-xs uppercase text-muted-foreground">{entity.type}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {Object.entries(entity.attributes)
                          .map(([key, value]) => `${key}: ${String(value)}`)
                          .join(', ')}
                      </p>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Edges</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {data.edges.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No edges yet.</p>
                ) : (
                  data.edges.map((edge) => (
                    <div key={edge.id} className="rounded-md border border-border bg-muted/40 p-3 text-sm">
                      <p className="font-medium">{edge.relationType}</p>
                      <p className="text-xs text-muted-foreground">
                        {edge.fromEntityId} → {edge.toEntityId}
                      </p>
                      <p className="text-xs text-muted-foreground">weight {edge.weight.toFixed(1)}</p>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </QueryBoundary>
    </section>
  )
}
