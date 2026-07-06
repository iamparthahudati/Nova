import { useQuery } from '@tanstack/react-query'
import { queryKeys } from '@/query/keys'
import { dataSource } from '@/services/data-source'

export function useSettings() {
  return useQuery({
    queryKey: queryKeys.settings(),
    queryFn: () => dataSource.getSettings(),
  })
}
