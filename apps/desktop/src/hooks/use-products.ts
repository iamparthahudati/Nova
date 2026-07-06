import { useQuery } from '@tanstack/react-query'
import { queryKeys } from '@/query/keys'
import { dataSource } from '@/services/data-source'

export function useProducts() {
  return useQuery({
    queryKey: queryKeys.products(),
    queryFn: () => dataSource.getProducts(),
  })
}
