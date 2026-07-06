import { useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/query/keys'
import { dataSource } from '@/services/data-source'

export function useCreateReminder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (input: { text: string; remindDate: string; remindTime?: string }) =>
      dataSource.createReminder({
        text: input.text,
        remind_date: input.remindDate,
        remind_time: input.remindTime ?? null,
      }),
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.reminders() })
      void queryClient.invalidateQueries({ queryKey: queryKeys.home() })
    },
  })
}
