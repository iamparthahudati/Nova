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
  finance: {
    dashboard: () => [...queryKeys.all, 'finance', 'dashboard'] as const,
    accounts: (params?: { includeArchived?: boolean }) =>
      [...queryKeys.all, 'finance', 'accounts', params ?? {}] as const,
    creditCards: () => [...queryKeys.all, 'finance', 'credit-cards'] as const,
    creditCard: (accountId: number) => [...queryKeys.all, 'finance', 'credit-cards', accountId] as const,
    statements: (params: { accountId: number; limit?: number }) =>
      [...queryKeys.all, 'finance', 'statements', params] as const,
    statementsAll: () => [...queryKeys.all, 'finance', 'statements'] as const,
    statement: (statementId: number) => [...queryKeys.all, 'finance', 'statement', statementId] as const,
    transactions: (params?: Record<string, unknown>) =>
      [...queryKeys.all, 'finance', 'transactions', params ?? {}] as const,
    rewardsOverview: () => [...queryKeys.all, 'finance', 'rewards', 'overview'] as const,
    rewards: (params?: { accountId?: number }) =>
      [...queryKeys.all, 'finance', 'rewards', params ?? {}] as const,
    rewardDetail: (programId: number) => [...queryKeys.all, 'finance', 'rewards', programId, 'detail'] as const,
    rewardLedger: (programId: number) => [...queryKeys.all, 'finance', 'rewards', programId, 'ledger'] as const,
    cashback: () => [...queryKeys.all, 'finance', 'cashback'] as const,
    categories: () => [...queryKeys.all, 'finance', 'categories'] as const,
    merchants: () => [...queryKeys.all, 'finance', 'merchants'] as const,
  },
  system: {
    status: () => [...queryKeys.all, 'system', 'status'] as const,
  },
} as const
