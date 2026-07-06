import { ScreenHeader } from '@/components/layout/screen-header'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { QueryBoundary } from '@/components/query-boundary'
import { useProducts } from '@/hooks/use-products'
import { formatINR } from '@/lib/utils'

export function ProductsScreen() {
  const products = useProducts()

  return (
    <section>
      <ScreenHeader title="Products" description="Product pipeline from the backend products endpoint." />
      <Card>
        <CardHeader>
          <CardTitle>Product pipeline</CardTitle>
        </CardHeader>
        <CardContent>
          <QueryBoundary
            query={products}
            isEmpty={(data) => data.length === 0}
            loadingMessage="Loading products…"
            emptyMessage="No products in the pipeline."
          >
            {(data) => (
              <div className="space-y-2">
                {data.map((product) => (
                  <div key={product.id} className="flex items-center justify-between rounded-md border border-border bg-muted/30 p-3">
                    <div>
                      <p className="text-sm font-medium">{product.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {product.store || 'No channel'} · created {new Date(product.createdAt).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <Badge variant={product.status === 'shipped' ? 'default' : 'secondary'}>{product.status}</Badge>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {product.price ? formatINR(product.price) : 'No price'} · sold {product.soldCount}
                      </p>
                    </div>
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
