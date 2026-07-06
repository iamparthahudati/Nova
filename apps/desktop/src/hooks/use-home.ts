import { useQuery } from '@tanstack/react-query'
import { queryKeys } from '@/query/keys'
import { dataSource } from '@/services/data-source'

export function useHome() {
  return useQuery({
    queryKey: queryKeys.home(),
    queryFn: () => dataSource.getHome(),
  })
}
