import { useQuery } from '@tanstack/react-query'
import { queryKeys } from '@/query/keys'
import { dataSource } from '@/services/data-source'

export function useMemories(limit = 50) {
  return useQuery({
    queryKey: queryKeys.memories({ limit }),
    queryFn: () => dataSource.getMemories({ limit }),
  })
}
