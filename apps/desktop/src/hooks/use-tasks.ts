import { useQuery } from '@tanstack/react-query'
import { queryKeys } from '@/query/keys'
import { dataSource } from '@/services/data-source'

export function useTasks(limit = 200) {
  return useQuery({
    queryKey: queryKeys.tasks({ limit }),
    queryFn: () => dataSource.getTasks(limit),
  })
}
