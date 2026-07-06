import { useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/query/keys'
import { dataSource } from '@/services/data-source'

export function useLogSpending() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (input: { type: 'earned' | 'spent'; amount: number; note?: string }) =>
      dataSource.logSpending({
        type: input.type,
        amount: input.amount,
        note: input.note ?? null,
      }),
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.spending() })
      void queryClient.invalidateQueries({ queryKey: queryKeys.home() })
    },
  })
}
