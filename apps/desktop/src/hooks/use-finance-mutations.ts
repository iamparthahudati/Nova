import { useMutation, useQueryClient } from '@tanstack/react-query'
import type {
  CreateAccountRequest,
  CreateCategoryRequest,
  CreateCreditCardRequest,
  CreateMerchantRequest,
  CreateTransactionRequest,
  CreateTransferRequest,
  PayStatementRequest,
  UpdateStatementRequest,
} from '@nova/api-contracts'
import { queryKeys } from '@/query/keys'
import { dataSource } from '@/services/data-source'

function invalidateFinance(queryClient: ReturnType<typeof useQueryClient>) {
  void queryClient.invalidateQueries({ queryKey: [...queryKeys.all, 'finance'] })
  void queryClient.invalidateQueries({ queryKey: queryKeys.home() })
  void queryClient.invalidateQueries({ queryKey: queryKeys.spending() })
}

export function useCreateAccount() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: CreateAccountRequest) => dataSource.createAccount(input),
    onSuccess: () => invalidateFinance(queryClient),
  })
}

export function useArchiveAccount() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (accountId: number) => dataSource.archiveAccount(accountId),
    onSuccess: () => invalidateFinance(queryClient),
  })
}

export function useCreateCreditCard() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: CreateCreditCardRequest) => dataSource.createCreditCard(input),
    onSuccess: () => invalidateFinance(queryClient),
  })
}

export function useCreateTransaction() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: CreateTransactionRequest) => dataSource.createTransaction(input),
    onSuccess: () => invalidateFinance(queryClient),
  })
}

export function useCreateCategory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: CreateCategoryRequest) => dataSource.createCategory(input),
    onSuccess: () => invalidateFinance(queryClient),
  })
}

export function useCreateMerchant() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: CreateMerchantRequest) => dataSource.createMerchant(input),
    onSuccess: () => invalidateFinance(queryClient),
  })
}

export function useCreateTransfer() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: CreateTransferRequest) => dataSource.createTransfer(input),
    onSuccess: () => invalidateFinance(queryClient),
  })
}

export function usePayStatement() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ statementId, input }: { statementId: number; input: PayStatementRequest }) =>
      dataSource.payStatement(statementId, input),
    onSuccess: () => invalidateFinance(queryClient),
  })
}

export function useUpdateStatement() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ statementId, input }: { statementId: number; input: UpdateStatementRequest }) =>
      dataSource.updateStatement(statementId, input),
    onSuccess: () => invalidateFinance(queryClient),
  })
}
