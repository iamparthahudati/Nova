import type { ReactNode } from 'react'
import type { UseQueryResult } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'

interface QueryBoundaryProps<TData> {
  query: UseQueryResult<TData, Error>
  isEmpty?: (data: TData) => boolean
  loadingMessage?: string
  emptyMessage?: string
  children: (data: TData) => ReactNode
}

export function QueryBoundary<TData>({
  query,
  isEmpty,
  loadingMessage = 'Loading…',
  emptyMessage = 'Nothing here yet.',
  children,
}: QueryBoundaryProps<TData>) {
  if (query.isLoading) {
    return <p className="text-sm text-muted-foreground">{loadingMessage}</p>
  }

  if (query.isError) {
    return (
      <div className="rounded-md border border-destructive/40 bg-destructive/10 p-4 text-sm">
        <p className="font-medium text-destructive">Failed to load data</p>
        <p className="mt-1 text-muted-foreground">{query.error.message}</p>
        <Button className="mt-3" size="sm" variant="secondary" onClick={() => void query.refetch()}>
          Retry
        </Button>
      </div>
    )
  }

  if (query.data === undefined) {
    return null
  }

  if (isEmpty?.(query.data)) {
    return <p className="text-sm text-muted-foreground">{emptyMessage}</p>
  }

  return <>{children(query.data)}</>
}
