import { useQuery } from '@tanstack/react-query'
import { queryKeys } from '@/query/keys'
import { dataSource } from '@/services/data-source'

export function useCalendar(day = 'today') {
  return useQuery({
    queryKey: queryKeys.calendar({ day }),
    queryFn: () => dataSource.getCalendar(day),
  })
}
