import { useQuery } from '@tanstack/react-query'
import { queryKeys } from '@/query/keys'
import { dataSource } from '@/services/data-source'

export function useGraph() {
  return useQuery({
    queryKey: queryKeys.graph(),
    queryFn: () => dataSource.getGraph(),
  })
}
