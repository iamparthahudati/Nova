import { useQuery } from '@tanstack/react-query'
import { isMockMode } from '@/config/env'
import { queryKeys } from '@/query/keys'
import { dataSource } from '@/services/data-source'

export function useSystemStatus() {
  return useQuery({
    queryKey: queryKeys.system.status(),
    queryFn: () => dataSource.getSystemStatus(),
    enabled: !isMockMode(),
    staleTime: 10_000,
    retry: 1,
  })
}
