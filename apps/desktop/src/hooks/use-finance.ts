import { useQuery } from '@tanstack/react-query'
import { queryKeys } from '@/query/keys'
import { dataSource } from '@/services/data-source'

export function useFinanceDashboard() {
  return useQuery({
    queryKey: queryKeys.finance.dashboard(),
    queryFn: () => dataSource.getFinanceDashboard(),
  })
}

export function useAccounts(includeArchived = false) {
  return useQuery({
    queryKey: queryKeys.finance.accounts({ includeArchived }),
    queryFn: () => dataSource.getAccounts(includeArchived),
  })
}

export function useCreditCards() {
  return useQuery({
    queryKey: queryKeys.finance.creditCards(),
    queryFn: () => dataSource.getCreditCards(),
  })
}

export function useCreditCard(accountId: number | null) {
  return useQuery({
    queryKey: queryKeys.finance.creditCard(accountId ?? 0),
    queryFn: () => dataSource.getCreditCard(accountId!),
    enabled: accountId !== null,
  })
}

export function useStatements(accountId: number | null, limit = 24) {
  return useQuery({
    queryKey: queryKeys.finance.statements({ accountId: accountId ?? 0, limit }),
    queryFn: () => dataSource.getStatements(accountId!, limit),
    enabled: accountId !== null,
  })
}

export function useStatement(statementId: number | null) {
  return useQuery({
    queryKey: queryKeys.finance.statement(statementId ?? 0),
    queryFn: () => dataSource.getStatement(statementId!),
    enabled: statementId !== null,
  })
}

export function useFinanceTransactions(params?: {
  accountId?: number
  categoryId?: number
  merchantId?: number
  direction?: string
  kind?: string
  startDate?: string
  endDate?: string
  search?: string
  limit?: number
  offset?: number
}) {
  return useQuery({
    queryKey: queryKeys.finance.transactions(params),
    queryFn: () => dataSource.getFinanceTransactions(params),
  })
}

export function useRewardPrograms(accountId?: number) {
  return useQuery({
    queryKey: queryKeys.finance.rewards({ accountId }),
    queryFn: () => dataSource.getRewardPrograms(accountId),
  })
}

export function useRewardLedger(programId: number | null) {
  return useQuery({
    queryKey: queryKeys.finance.rewardLedger(programId ?? 0),
    queryFn: () => dataSource.getRewardLedger(programId!),
    enabled: programId !== null,
  })
}

export function useCashbackSummary() {
  return useQuery({
    queryKey: queryKeys.finance.cashback(),
    queryFn: () => dataSource.getCashbackSummary(),
  })
}

export function useCategories() {
  return useQuery({
    queryKey: queryKeys.finance.categories(),
    queryFn: () => dataSource.getCategories(),
  })
}

export function useMerchants() {
  return useQuery({
    queryKey: queryKeys.finance.merchants(),
    queryFn: () => dataSource.getMerchants(),
  })
}
