export const queryKeys = {
  all: ['nova'] as const,
  home: () => [...queryKeys.all, 'home'] as const,
  tasks: (params?: { limit?: number }) => [...queryKeys.all, 'tasks', params ?? {}] as const,
  reminders: (params?: { limit?: number }) => [...queryKeys.all, 'reminders', params ?? {}] as const,
  calendar: (params?: { day?: string }) => [...queryKeys.all, 'calendar', params ?? {}] as const,
  products: () => [...queryKeys.all, 'products'] as const,
  spending: (params?: { limit?: number }) => [...queryKeys.all, 'spending', params ?? {}] as const,
  memories: (params?: {
    limit?: number
    offset?: number
    tier?: string
    sourceType?: string
    search?: string
    sort?: string
    order?: string
  }) => [...queryKeys.all, 'memories', params ?? {}] as const,
  graph: (params?: { entityLimit?: number; edgeLimit?: number }) =>
    [...queryKeys.all, 'graph', params ?? {}] as const,
  settings: () => [...queryKeys.all, 'settings'] as const,
  system: {
    status: () => [...queryKeys.all, 'system', 'status'] as const,
  },
} as const
