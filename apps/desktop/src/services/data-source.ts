import type {
  CreateAccountRequest,
  CreateCategoryRequest,
  CreateCreditCardRequest,
  CreateMerchantRequest,
  CreateReminderRequest,
  CreateTaskRequest,
  CreateTransactionRequest,
  CreateCardPaymentRequest,
  CreateTransferRequest,
  LogSpendingRequest,
  PayStatementRequest,
  ReminderMutationResponse,
  SpendingMutationResponse,
  TaskMutationResponse,
  UpdateCategoryRequest,
  UpdateCreditCardRequest,
  UpdateMerchantRequest,
  UpdateStatementRequest,
  UpdateAccountRequest,
  UpdateTransactionRequest,
} from '@nova/api-contracts'
import { isMockMode } from '@/config/env'
import * as mockMutations from '@/dev/mocks/mutations'
import * as mockApi from '@/dev/mocks/api'
import * as novaApi from '@/services/nova-api'
import { mapAccount, mapCategory, mapCreditCard, mapMerchant } from '@/mappers/finance'
import { mapReminder } from '@/mappers/reminders'
import { mapSpendingTransaction } from '@/mappers/spending'
import { mapTask } from '@/mappers/tasks'
import type { Reminder, SpendingEntry, Task } from '@/view-models'

export interface TaskMutationResult {
  task: Task
  meta: { message: string }
}

export interface ReminderMutationResult {
  reminder: Reminder
  meta: { message: string }
}

export interface SpendingMutationResult {
  transaction: SpendingEntry
  meta: { message: string }
}

async function normalizeTaskMutation(response: TaskMutationResponse): Promise<TaskMutationResult> {
  return {
    task: mapTask(response.item),
    meta: response.meta,
  }
}

async function normalizeReminderMutation(response: ReminderMutationResponse): Promise<ReminderMutationResult> {
  return {
    reminder: mapReminder(response.item),
    meta: response.meta,
  }
}

async function normalizeSpendingMutation(response: SpendingMutationResponse): Promise<SpendingMutationResult> {
  return {
    transaction: mapSpendingTransaction(response.item),
    meta: response.meta,
  }
}

export const dataSource = {
  getProducts: () => (isMockMode() ? mockApi.listProducts() : novaApi.fetchProducts()),
  getTasks: (limit?: number) => (isMockMode() ? mockApi.listTasks() : novaApi.fetchTasks(limit)),
  getSpending: (limit?: number) => (isMockMode() ? mockApi.getSpending() : novaApi.fetchSpending(limit)),
  getReminders: (limit?: number) => (isMockMode() ? mockApi.listReminders() : novaApi.fetchReminders(limit)),
  getHome: () => (isMockMode() ? mockApi.getHome() : novaApi.fetchHome()),
  getMemories: (params?: Parameters<typeof novaApi.fetchMemories>[0]) =>
    isMockMode() ? mockApi.listMemories() : novaApi.fetchMemories(params),
  getGraph: () => (isMockMode() ? mockApi.listGraph() : novaApi.fetchGraph()),
  getCalendar: (day?: string) => (isMockMode() ? mockApi.getCalendar() : novaApi.fetchCalendar(day)),
  getSettings: () => (isMockMode() ? mockApi.getSettings() : novaApi.fetchSettings()),
  getSystemStatus: () => (isMockMode() ? mockApi.getSystemStatus() : novaApi.fetchSystemStatus()),
  getFinanceDashboard: () => (isMockMode() ? mockApi.getFinanceDashboard() : novaApi.fetchFinanceDashboard()),
  getAccounts: (includeArchived?: boolean) =>
    isMockMode() ? mockApi.getAccounts() : novaApi.fetchAccounts(includeArchived),
  getCreditCards: () => (isMockMode() ? mockApi.getCreditCards() : novaApi.fetchCreditCards()),
  getCreditCard: (accountId: number) =>
    isMockMode() ? mockApi.getCreditCard(accountId) : novaApi.fetchCreditCard(accountId),
  getStatements: (accountId: number, limit?: number) =>
    isMockMode() ? mockApi.getStatements(accountId) : novaApi.fetchStatements(accountId, limit),
  getFinanceTransactions: (params?: Parameters<typeof novaApi.fetchFinanceTransactions>[0]) =>
    isMockMode() ? mockApi.getFinanceTransactions() : novaApi.fetchFinanceTransactions(params),
  getRewardPrograms: (accountId?: number) =>
    isMockMode() ? mockApi.getRewardPrograms() : novaApi.fetchRewardPrograms(accountId),
  getRewardLedger: (programId: number) =>
    isMockMode() ? mockApi.getRewardLedger(programId) : novaApi.fetchRewardLedger(programId),
  getCashbackSummary: () => (isMockMode() ? mockApi.getCashbackSummary() : novaApi.fetchCashbackSummary()),
  getCategories: () => (isMockMode() ? mockApi.getCategories() : novaApi.fetchCategories()),
  getMerchants: () => (isMockMode() ? mockApi.getMerchants() : novaApi.fetchMerchants()),
  createAccount: async (input: CreateAccountRequest) => {
    const response = isMockMode() ? await mockApi.createAccount(input) : await novaApi.createAccountRaw(input)
    return { account: mapAccount(response.item), meta: response.meta }
  },
  updateAccount: async (accountId: number, input: UpdateAccountRequest) => {
    const response = isMockMode()
      ? await mockApi.updateAccount(accountId, input)
      : await novaApi.updateAccountRaw(accountId, input)
    return { account: mapAccount(response.item), meta: response.meta }
  },
  archiveAccount: async (accountId: number) => {
    const response = isMockMode()
      ? await mockApi.archiveAccount(accountId)
      : await novaApi.archiveAccountRaw(accountId)
    return { account: mapAccount(response.item), meta: response.meta }
  },
  restoreAccount: async (accountId: number) => {
    const response = isMockMode()
      ? await mockApi.restoreAccount(accountId)
      : await novaApi.restoreAccountRaw(accountId)
    return { account: mapAccount(response.item), meta: response.meta }
  },
  createCreditCard: async (input: CreateCreditCardRequest) => {
    const response = isMockMode()
      ? await mockApi.createCreditCard(input)
      : await novaApi.createCreditCardRaw(input)
    return { card: mapCreditCard(response.item), meta: response.meta }
  },
  updateCreditCard: async (accountId: number, input: UpdateCreditCardRequest) => {
    const response = isMockMode()
      ? await mockApi.updateCreditCard(accountId, input)
      : await novaApi.updateCreditCardRaw(accountId, input)
    return { card: mapCreditCard(response.item), meta: response.meta }
  },
  createTransaction: async (input: CreateTransactionRequest) => {
    const response = isMockMode()
      ? await mockApi.createTransaction(input)
      : await novaApi.createTransactionRaw(input)
    return { meta: response.meta }
  },
  updateTransaction: async (transactionId: number, input: UpdateTransactionRequest) => {
    const response = isMockMode()
      ? await mockApi.updateTransaction(transactionId, input)
      : await novaApi.updateTransactionRaw(transactionId, input)
    return { meta: response.meta }
  },
  deleteTransaction: async (transactionId: number) => {
    const response = isMockMode()
      ? await mockApi.deleteTransaction(transactionId)
      : await novaApi.deleteTransactionRaw(transactionId)
    return { meta: response.meta }
  },
  createCategory: async (input: CreateCategoryRequest) => {
    const response = isMockMode() ? await mockApi.createCategory(input) : await novaApi.createCategoryRaw(input)
    return { category: mapCategory(response.item), meta: response.meta }
  },
  createMerchant: async (input: CreateMerchantRequest) => {
    const response = isMockMode() ? await mockApi.createMerchant(input) : await novaApi.createMerchantRaw(input)
    return { merchant: mapMerchant(response.item), meta: response.meta }
  },
  updateCategory: async (categoryId: number, input: UpdateCategoryRequest) => {
    const response = isMockMode()
      ? await mockApi.updateCategory(categoryId, input)
      : await novaApi.updateCategoryRaw(categoryId, input)
    return { category: mapCategory(response.item), meta: response.meta }
  },
  deleteCategory: async (categoryId: number) => {
    const response = isMockMode()
      ? await mockApi.deleteCategory(categoryId)
      : await novaApi.deleteCategoryRaw(categoryId)
    return { category: mapCategory(response.item), meta: response.meta }
  },
  updateMerchant: async (merchantId: number, input: UpdateMerchantRequest) => {
    const response = isMockMode()
      ? await mockApi.updateMerchant(merchantId, input)
      : await novaApi.updateMerchantRaw(merchantId, input)
    return { merchant: mapMerchant(response.item), meta: response.meta }
  },
  deleteMerchant: async (merchantId: number) => {
    const response = isMockMode()
      ? await mockApi.deleteMerchant(merchantId)
      : await novaApi.deleteMerchantRaw(merchantId)
    return { merchant: mapMerchant(response.item), meta: response.meta }
  },
  createTransfer: async (input: CreateTransferRequest) => {
    const response = isMockMode() ? await mockApi.createTransfer(input) : await novaApi.createTransferRaw(input)
    return { meta: response.meta }
  },
  createCardPayment: async (input: CreateCardPaymentRequest) => {
    const response = isMockMode()
      ? await mockApi.createCardPayment(input)
      : await novaApi.createCardPaymentRaw(input)
    return { meta: response.meta }
  },
  payStatement: async (statementId: number, input: PayStatementRequest) => {
    const response = isMockMode()
      ? await mockApi.payStatement(statementId, input)
      : await novaApi.payStatementRaw(statementId, input)
    return { meta: response.meta }
  },
  updateStatement: async (statementId: number, input: UpdateStatementRequest) => {
    const response = isMockMode()
      ? await mockApi.updateStatement(statementId, input)
      : await novaApi.updateStatementRaw(statementId, input)
    return { meta: response.meta }
  },
  createTask: async (input: CreateTaskRequest): Promise<TaskMutationResult> =>
    normalizeTaskMutation(
      isMockMode() ? await mockMutations.createTask(input) : await novaApi.createTaskRaw(input),
    ),
  completeTask: async (taskId: number): Promise<TaskMutationResult> =>
    normalizeTaskMutation(
      isMockMode() ? await mockMutations.completeTask(taskId) : await novaApi.completeTaskRaw(taskId),
    ),
  createReminder: async (input: CreateReminderRequest): Promise<ReminderMutationResult> =>
    normalizeReminderMutation(
      isMockMode() ? await mockMutations.createReminder(input) : await novaApi.createReminderRaw(input),
    ),
  logSpending: async (input: LogSpendingRequest): Promise<SpendingMutationResult> =>
    normalizeSpendingMutation(
      isMockMode() ? await mockMutations.logSpending(input) : await novaApi.logSpendingRaw(input),
    ),
}
