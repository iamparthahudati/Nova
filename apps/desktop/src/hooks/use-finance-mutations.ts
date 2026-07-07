import { useMutation, useQueryClient } from '@tanstack/react-query'
import type {
  CreateAccountRequest,
  CreateCategoryRequest,
  CreateCreditCardRequest,
  CreateMerchantRequest,
  CreateCardPaymentRequest,
  CreateTransactionRequest,
  CreateTransferRequest,
  PayStatementRequest,
  UpdateAccountRequest,
  UpdateCategoryRequest,
  UpdateCreditCardRequest,
  UpdateMerchantRequest,
  UpdateStatementRequest,
  UpdateTransactionRequest,
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

export function useRestoreAccount() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (accountId: number) => dataSource.restoreAccount(accountId),
    onSuccess: () => invalidateFinance(queryClient),
  })
}

export function useUpdateAccount() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ accountId, input }: { accountId: number; input: UpdateAccountRequest }) =>
      dataSource.updateAccount(accountId, input),
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

export function useUpdateCreditCard() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ accountId, input }: { accountId: number; input: UpdateCreditCardRequest }) =>
      dataSource.updateCreditCard(accountId, input),
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

export function useUpdateTransaction() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ transactionId, input }: { transactionId: number; input: UpdateTransactionRequest }) =>
      dataSource.updateTransaction(transactionId, input),
    onSuccess: () => invalidateFinance(queryClient),
  })
}

export function useDeleteTransaction() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (transactionId: number) => dataSource.deleteTransaction(transactionId),
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

export function useUpdateCategory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ categoryId, input }: { categoryId: number; input: UpdateCategoryRequest }) =>
      dataSource.updateCategory(categoryId, input),
    onSuccess: () => invalidateFinance(queryClient),
  })
}

export function useDeleteCategory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (categoryId: number) => dataSource.deleteCategory(categoryId),
    onSuccess: () => invalidateFinance(queryClient),
  })
}

export function useUpdateMerchant() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ merchantId, input }: { merchantId: number; input: UpdateMerchantRequest }) =>
      dataSource.updateMerchant(merchantId, input),
    onSuccess: () => invalidateFinance(queryClient),
  })
}

export function useDeleteMerchant() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (merchantId: number) => dataSource.deleteMerchant(merchantId),
    onSuccess: () => invalidateFinance(queryClient),
  })
}

export function useCreateCardPayment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: CreateCardPaymentRequest) => dataSource.createCardPayment(input),
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
