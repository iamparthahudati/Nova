import { useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/query/keys'
import { dataSource } from '@/services/data-source'
import type { Task } from '@/view-models'

const TASKS_QUERY = queryKeys.tasks({ limit: 200 })

export function useCreateTask() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (input: { text: string; due?: string }) => dataSource.createTask(input),
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.tasks() })
      void queryClient.invalidateQueries({ queryKey: queryKeys.home() })
    },
  })
}

export function useCompleteTask() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (taskId: number) => dataSource.completeTask(taskId),
    onMutate: async (taskId) => {
      await queryClient.cancelQueries({ queryKey: TASKS_QUERY })
      const previous = queryClient.getQueryData<Task[]>(TASKS_QUERY)
      queryClient.setQueryData<Task[]>(TASKS_QUERY, (current) =>
        current?.map((task) => (task.id === taskId ? { ...task, status: 'done' } : task)),
      )
      return { previous }
    },
    onError: (_error, _taskId, context) => {
      if (context?.previous) {
        queryClient.setQueryData(TASKS_QUERY, context.previous)
      }
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.tasks() })
      void queryClient.invalidateQueries({ queryKey: queryKeys.home() })
    },
    retry: 1,
  })
}
