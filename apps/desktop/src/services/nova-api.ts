import type {
  AccountMutationResponse,
  AccountsResponse,
  CalendarResponse,
  CashbackActivityResponse,
  CashbackRuleDetailResponse,
  CashbackSummaryResponse,
  CategoriesResponse,
  CategoryMutationResponse,
  CreateCardPaymentRequest,
  CreateCategoryRequest,
  CreateMerchantRequest,
  CreateTransferRequest,
  CreateAccountRequest,
  CreateCreditCardRequest,
  CreateReminderRequest,
  CreateTaskRequest,
  CreateTransactionRequest,
  CreditCardMutationResponse,
  CreditCardResponse,
  CreditCardsResponse,
  FinanceDashboardResponse,
  GraphSnapshotResponse,
  HomeResponse,
  LogSpendingRequest,
  MemoriesListResponse,
  ProductsResponse,
  ReminderMutationResponse,
  RemindersResponse,
  RewardLedgerResponse,
  RewardProgramDetailResponse,
  RewardProgramsResponse,
  RewardsOverviewResponse,
  SettingsResponse,
  SpendingMutationResponse,
  SpendingResponse,
  MerchantsResponse,
  MerchantMutationResponse,
  PayStatementRequest,
  StatementMutationResponse,
  StatementResponse,
  TransferMutationResponse,
  UpdateCategoryRequest,
  UpdateCreditCardRequest,
  UpdateMerchantRequest,
  UpdateStatementRequest,
  StatementsResponse,
  SystemStatusResponse,
  TaskMutationResponse,
  TasksResponse,
  TransactionMutationResponse,
  TransactionsResponse,
  UpdateAccountRequest,
  UpdateTransactionRequest,
} from '@nova/api-contracts'
import { apiDelete, apiGet, apiPatch, apiPost } from '@/lib/api-client'
import { mapCalendar } from '@/mappers/calendar'
import {
  mapAccount,
  mapCashbackActivity,
  mapCashbackRuleDetail,
  mapCashbackSummary,
  mapCategory,
  mapCreditCard,
  mapFinanceDashboard,
  mapMerchant,
  mapRewardLedger,
  mapRewardProgram,
  mapRewardProgramDetail,
  mapRewardsOverview,
  mapStatementList,
  mapTransactionsPage,
} from '@/mappers/finance'
import { mapGraph } from '@/mappers/graph'
import { mapHome } from '@/mappers/home'
import { mapMemories } from '@/mappers/memories'
import { mapProducts } from '@/mappers/products'
import { mapReminders } from '@/mappers/reminders'
import { mapSettings } from '@/mappers/settings'
import { mapSpending } from '@/mappers/spending'
import { mapSystemStatus } from '@/mappers/system'
import { mapTasks } from '@/mappers/tasks'
import type {
  CalendarViewModel,
  GraphViewModel,
  HomeViewModel,
  MemoriesViewModel,
  Product,
  Reminder,
  SettingsViewModel,
  SpendingViewModel,
  SystemStatusViewModel,
  Task,
} from '@/view-models'
import type {
  CashbackActivityEvent,
  CashbackRuleDetail,
  CashbackSummary,
  FinanceAccount,
  FinanceCategory,
  FinanceCreditCard,
  FinanceDashboard,
  FinanceMerchant,
  FinanceStatement,
  RewardLedger,
  RewardProgram,
  RewardProgramDetail,
  RewardsOverview,
  TransactionsPage,
} from '@/view-models/finance'

export async function fetchProducts(): Promise<Product[]> {
  const response = await apiGet<ProductsResponse>('/products')
  return mapProducts(response)
}

export async function fetchTasks(limit = 200): Promise<Task[]> {
  const response = await apiGet<TasksResponse>('/tasks', { limit })
  return mapTasks(response)
}

export async function createTaskRaw(input: CreateTaskRequest): Promise<TaskMutationResponse> {
  return apiPost<CreateTaskRequest, TaskMutationResponse>('/tasks', input)
}

export async function completeTaskRaw(taskId: number): Promise<TaskMutationResponse> {
  return apiPost<Record<string, never>, TaskMutationResponse>(`/tasks/${taskId}/complete`, {})
}

export async function createReminderRaw(input: CreateReminderRequest): Promise<ReminderMutationResponse> {
  return apiPost<CreateReminderRequest, ReminderMutationResponse>('/reminders', input)
}

export async function logSpendingRaw(input: LogSpendingRequest): Promise<SpendingMutationResponse> {
  return apiPost<LogSpendingRequest, SpendingMutationResponse>('/spending', input)
}

export async function fetchSpending(limit = 30): Promise<SpendingViewModel> {
  const response = await apiGet<SpendingResponse>('/spending', { limit })
  return mapSpending(response)
}

export async function fetchReminders(limit = 50): Promise<Reminder[]> {
  const response = await apiGet<RemindersResponse>('/reminders', { limit })
  return mapReminders(response)
}

export async function fetchHome(): Promise<HomeViewModel> {
  const response = await apiGet<HomeResponse>('/home')
  return mapHome(response)
}

export async function fetchMemories(params?: {
  limit?: number
  offset?: number
  tier?: string
  sourceType?: string
  search?: string
  sort?: string
  order?: string
}): Promise<MemoriesViewModel> {
  const response = await apiGet<MemoriesListResponse>('/memories', {
    limit: params?.limit ?? 50,
    offset: params?.offset ?? 0,
    tier: params?.tier,
    source_type: params?.sourceType,
    search: params?.search,
    sort: params?.sort ?? 'created_at',
    order: params?.order ?? 'desc',
  })
  return mapMemories(response)
}

export async function fetchGraph(entityLimit = 500, edgeLimit = 500): Promise<GraphViewModel> {
  const response = await apiGet<GraphSnapshotResponse>('/graph', {
    entity_limit: entityLimit,
    edge_limit: edgeLimit,
  })
  return mapGraph(response)
}

export async function fetchCalendar(day = 'today'): Promise<CalendarViewModel> {
  const response = await apiGet<CalendarResponse>('/calendar', { day })
  return mapCalendar(response)
}

export async function fetchSettings(): Promise<SettingsViewModel> {
  const response = await apiGet<SettingsResponse>('/settings')
  return mapSettings(response)
}

export async function fetchSystemStatus(): Promise<SystemStatusViewModel> {
  const response = await apiGet<SystemStatusResponse>('/system/status')
  return mapSystemStatus(response)
}

export async function fetchFinanceDashboard(): Promise<FinanceDashboard> {
  const response = await apiGet<FinanceDashboardResponse>('/finance/dashboard')
  return mapFinanceDashboard(response)
}

export async function fetchAccounts(includeArchived = false): Promise<FinanceAccount[]> {
  const response = await apiGet<AccountsResponse>('/finance/accounts', {
    include_archived: includeArchived ? 'true' : undefined,
  })
  return response.accounts.map(mapAccount)
}

export async function createAccountRaw(input: CreateAccountRequest): Promise<AccountMutationResponse> {
  return apiPost<CreateAccountRequest, AccountMutationResponse>('/finance/accounts', input)
}

export async function updateAccountRaw(
  accountId: number,
  input: UpdateAccountRequest,
): Promise<AccountMutationResponse> {
  return apiPatch<UpdateAccountRequest, AccountMutationResponse>(`/finance/accounts/${accountId}`, input)
}

export async function archiveAccountRaw(accountId: number): Promise<AccountMutationResponse> {
  return apiPost<Record<string, never>, AccountMutationResponse>(`/finance/accounts/${accountId}/archive`, {})
}

export async function restoreAccountRaw(accountId: number): Promise<AccountMutationResponse> {
  return apiPost<Record<string, never>, AccountMutationResponse>(`/finance/accounts/${accountId}/restore`, {})
}

export async function fetchCreditCards(): Promise<FinanceCreditCard[]> {
  const response = await apiGet<CreditCardsResponse>('/finance/credit-cards')
  return response.cards.map(mapCreditCard)
}

export async function fetchCreditCard(accountId: number): Promise<FinanceCreditCard> {
  const response = await apiGet<CreditCardResponse>(`/finance/credit-cards/${accountId}`)
  return mapCreditCard(response)
}

export async function createCreditCardRaw(input: CreateCreditCardRequest): Promise<CreditCardMutationResponse> {
  return apiPost<CreateCreditCardRequest, CreditCardMutationResponse>('/finance/credit-cards', input)
}

export async function updateCreditCardRaw(
  accountId: number,
  input: UpdateCreditCardRequest,
): Promise<CreditCardMutationResponse> {
  return apiPatch<UpdateCreditCardRequest, CreditCardMutationResponse>(`/finance/credit-cards/${accountId}`, input)
}

export async function fetchStatements(accountId: number, limit = 24): Promise<FinanceStatement[]> {
  const response = await apiGet<StatementsResponse>('/finance/statements', { account_id: accountId, limit })
  return mapStatementList(response.statements)
}

export async function fetchStatement(statementId: number): Promise<FinanceStatement> {
  const response = await apiGet<StatementResponse>(`/finance/statements/${statementId}`)
  return mapStatementList([response])[0]
}

export async function fetchFinanceTransactions(params?: {
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
}): Promise<TransactionsPage> {
  const response = await apiGet<TransactionsResponse>('/finance/transactions', {
    account_id: params?.accountId,
    category_id: params?.categoryId,
    merchant_id: params?.merchantId,
    direction: params?.direction,
    kind: params?.kind,
    start_date: params?.startDate,
    end_date: params?.endDate,
    search: params?.search,
    limit: params?.limit ?? 50,
    offset: params?.offset ?? 0,
  })
  return mapTransactionsPage(response)
}

export async function createTransactionRaw(input: CreateTransactionRequest): Promise<TransactionMutationResponse> {
  return apiPost<CreateTransactionRequest, TransactionMutationResponse>('/finance/transactions', input)
}

export async function updateTransactionRaw(
  transactionId: number,
  input: UpdateTransactionRequest,
): Promise<TransactionMutationResponse> {
  return apiPatch<UpdateTransactionRequest, TransactionMutationResponse>(
    `/finance/transactions/${transactionId}`,
    input,
  )
}

export async function deleteTransactionRaw(transactionId: number): Promise<TransactionMutationResponse> {
  return apiDelete<TransactionMutationResponse>(`/finance/transactions/${transactionId}`)
}

export async function fetchRewardsOverview(): Promise<RewardsOverview> {
  const response = await apiGet<RewardsOverviewResponse>('/finance/rewards/overview')
  return mapRewardsOverview(response)
}

export async function fetchRewardPrograms(accountId?: number): Promise<RewardProgram[]> {
  const response = await apiGet<RewardProgramsResponse>('/finance/rewards/programs', { account_id: accountId })
  return response.programs.map(mapRewardProgram)
}

export async function fetchRewardProgramDetail(programId: number): Promise<RewardProgramDetail> {
  const response = await apiGet<RewardProgramDetailResponse>(`/finance/rewards/programs/${programId}`)
  return mapRewardProgramDetail(response)
}

export async function fetchRewardLedger(programId: number, limit = 50, offset = 0): Promise<RewardLedger> {
  const response = await apiGet<RewardLedgerResponse>(`/finance/rewards/programs/${programId}/ledger`, {
    limit,
    offset,
  })
  return mapRewardLedger(response)
}

export async function fetchCashbackSummary(): Promise<CashbackSummary> {
  const response = await apiGet<CashbackSummaryResponse>('/finance/cashback')
  return mapCashbackSummary(response)
}

export async function fetchCashbackActivity(limit = 50, offset = 0): Promise<CashbackActivityEvent[]> {
  const response = await apiGet<CashbackActivityResponse>('/finance/cashback/activity', { limit, offset })
  return mapCashbackActivity(response)
}

export async function fetchCashbackRuleDetail(ruleId: number): Promise<CashbackRuleDetail> {
  const response = await apiGet<CashbackRuleDetailResponse>(`/finance/cashback/rules/${ruleId}`)
  return mapCashbackRuleDetail(response)
}

export async function fetchCategories(): Promise<FinanceCategory[]> {
  const response = await apiGet<CategoriesResponse>('/finance/categories')
  return response.categories.map(mapCategory)
}

export async function createCategoryRaw(input: CreateCategoryRequest): Promise<CategoryMutationResponse> {
  return apiPost<CreateCategoryRequest, CategoryMutationResponse>('/finance/categories', input)
}

export async function updateCategoryRaw(
  categoryId: number,
  input: UpdateCategoryRequest,
): Promise<CategoryMutationResponse> {
  return apiPatch<UpdateCategoryRequest, CategoryMutationResponse>(`/finance/categories/${categoryId}`, input)
}

export async function deleteCategoryRaw(categoryId: number): Promise<CategoryMutationResponse> {
  return apiDelete<CategoryMutationResponse>(`/finance/categories/${categoryId}`)
}

export async function fetchMerchants(): Promise<FinanceMerchant[]> {
  const response = await apiGet<MerchantsResponse>('/finance/merchants')
  return response.merchants.map(mapMerchant)
}

export async function createMerchantRaw(input: CreateMerchantRequest): Promise<MerchantMutationResponse> {
  return apiPost<CreateMerchantRequest, MerchantMutationResponse>('/finance/merchants', input)
}

export async function updateMerchantRaw(
  merchantId: number,
  input: UpdateMerchantRequest,
): Promise<MerchantMutationResponse> {
  return apiPatch<UpdateMerchantRequest, MerchantMutationResponse>(`/finance/merchants/${merchantId}`, input)
}

export async function deleteMerchantRaw(merchantId: number): Promise<MerchantMutationResponse> {
  return apiDelete<MerchantMutationResponse>(`/finance/merchants/${merchantId}`)
}

export async function createTransferRaw(input: CreateTransferRequest): Promise<TransferMutationResponse> {
  return apiPost<CreateTransferRequest, TransferMutationResponse>('/finance/transfers', input)
}

export async function createCardPaymentRaw(input: CreateCardPaymentRequest): Promise<TransferMutationResponse> {
  return apiPost<CreateCardPaymentRequest, TransferMutationResponse>('/finance/payments/card', input)
}

export async function payStatementRaw(
  statementId: number,
  input: PayStatementRequest,
): Promise<TransferMutationResponse> {
  return apiPost<PayStatementRequest, TransferMutationResponse>(`/finance/statements/${statementId}/pay`, input)
}

export async function updateStatementRaw(
  statementId: number,
  input: UpdateStatementRequest,
): Promise<StatementMutationResponse> {
  return apiPatch<UpdateStatementRequest, StatementMutationResponse>(`/finance/statements/${statementId}`, input)
}
