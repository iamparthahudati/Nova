import { useQuery } from '@tanstack/react-query'
import { queryKeys } from '@/query/keys'
import { dataSource } from '@/services/data-source'

export function useSpending(limit = 30) {
  return useQuery({
    queryKey: queryKeys.spending({ limit }),
    queryFn: () => dataSource.getSpending(limit),
  })
}
