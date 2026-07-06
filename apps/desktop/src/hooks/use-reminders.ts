import { useQuery } from '@tanstack/react-query'
import { queryKeys } from '@/query/keys'
import { dataSource } from '@/services/data-source'

export function useReminders(limit = 50) {
  return useQuery({
    queryKey: queryKeys.reminders({ limit }),
    queryFn: () => dataSource.getReminders(limit),
  })
}
