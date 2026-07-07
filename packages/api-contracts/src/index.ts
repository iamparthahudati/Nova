/**
 * Canonical HTTP API contracts for Nova backend ↔ clients.
 * Keep in sync with apps/backend/services/api/schemas/.
 */

export interface MutationMeta {
  message: string
}

export interface EntityMutationResponse<T> {
  item: T
  meta: MutationMeta
}

export interface CreateTaskRequest {
  text: string
  due?: string | null
}

export interface TaskMutationResponse {
  item: TaskResponse
  meta: MutationMeta
}

export interface ErrorDetail {
  code: string
  message: string
  details?: Record<string, unknown>
}

export interface ErrorResponse {
  error: ErrorDetail
}

export interface HealthResponse {
  status: string
  service: string
  version: string
}

export interface ChatRequest {
  message: string
  conversation_id?: string
}

export interface ToolCallRecord {
  name: string
  args: Record<string, unknown>
  result: string
}

export interface ChatResponse {
  reply: string
  conversation_id: string
  tools_called: ToolCallRecord[]
  error?: string | null
}

export interface TaskResponse {
  id: number
  text: string
  status: string
  created_at: string
  due?: string | null
}

export interface TasksResponse {
  tasks: TaskResponse[]
}

export interface ReminderResponse {
  id: number
  text: string
  remind_date: string
  remind_time?: string | null
  created_at: string
}

export interface RemindersResponse {
  reminders: ReminderResponse[]
}

export interface CreateReminderRequest {
  text: string
  remind_date: string
  remind_time?: string | null
}

export interface ReminderMutationResponse {
  item: ReminderResponse
  meta: MutationMeta
}

export interface MemoryResponse {
  id: string
  text: string
  source_type: string
  source_id?: string | null
  metadata: Record<string, unknown>
  tier: string
  importance: number
  access_count: number
  created_at: string
  similarity?: number | null
  score?: number | null
}

export interface MemoryRecallResponse {
  query: string
  memories: MemoryResponse[]
}

export interface CalendarEventResponse {
  title: string
  time: string
}

export interface CalendarResponse {
  date: string
  events: CalendarEventResponse[]
  unavailable: boolean
}

export interface GraphEntityResponse {
  id: string
  type: string
  canonical_name: string
  attributes: Record<string, unknown>
  created_at?: string | null
}

export interface GraphEdgeResponse {
  id: string
  from_entity_id: string
  to_entity_id: string
  relation_type: string
  weight: number
  source_memory_id?: string | null
  created_at?: string | null
}

export interface GraphRelatedResponse {
  entity: GraphEntityResponse
  related: GraphEntityResponse[]
  edges: GraphEdgeResponse[]
}

export interface GraphSnapshotResponse {
  entities: GraphEntityResponse[]
  edges: GraphEdgeResponse[]
}

export interface GraphStatsResponse {
  entity_count: number
  edge_count: number
  entities_by_type: Record<string, number>
  edges_by_relation: Record<string, number>
}

export interface MemoriesListResponse {
  memories: MemoryResponse[]
  total: number
  limit: number
  offset: number
}

export interface MemoriesStatsResponse {
  count: number
  by_tier: Record<string, number>
}

export interface HomeCard {
  id: string
  label: string
  value: string
  icon?: string | null
}

export interface HomePanelItem {
  id: string
  primary: string
  secondary?: string | null
  meta?: Record<string, unknown>
}

export interface HomePanel {
  id: string
  title: string
  items: HomePanelItem[]
}

export interface HomeResponse {
  cards: HomeCard[]
  panels: HomePanel[]
}

export type SubsystemStatus = 'ok' | 'degraded' | 'unavailable'

export interface SubsystemDiagnostic {
  name: string
  status: SubsystemStatus
  message?: string | null
}

export interface SystemStatusResponse {
  status: SubsystemStatus
  version: string
  subsystems: SubsystemDiagnostic[]
}

export interface SpendingTransactionResponse {
  id: number
  type: string
  amount: number
  note?: string | null
  created_at: string
}

export interface SpendingSummaryResponse {
  period: string
  earned: number
  spent: number
  summary: string
}

export interface SpendingResponse {
  earned_month: number
  spent_month: number
  transactions: SpendingTransactionResponse[]
}

export interface LogSpendingRequest {
  type: 'earned' | 'spent'
  amount: number
  note?: string | null
}

export interface SpendingMutationResponse {
  item: SpendingTransactionResponse
  meta: MutationMeta
}

export interface ProductResponse {
  id: number
  name: string
  store?: string | null
  status: string
  price?: number | null
  sold_count: number
  created_at: string
}

export interface ProductsResponse {
  products: ProductResponse[]
}

export interface ProfileObservationResponse {
  observation: string
  category: string
  confidence: number
}

export interface SettingsResponse {
  assistant_name: string
  voice_name: string
  briefing_time: string
  evening_wrapup_time?: string | null
  claude_model: string
  semantic_memory_enabled: boolean
  entity_extraction_enabled: boolean
  graph_context_enabled: boolean
  observations: ProfileObservationResponse[]
}

export interface FinanceDashboardResponse {
  total_balance_minor: number
  total_balance: number
  total_assets_minor: number
  total_assets: number
  total_liabilities_minor: number
  total_liabilities: number
  cash_available_minor: number
  cash_available: number
  credit_utilization_ratio: number
  credit_utilization_percent: number
  total_outstanding_minor: number
  total_outstanding: number
  total_available_credit_minor: number
  total_available_credit: number
  cards_near_due_count: number
  income_month: number
  spent_month: number
  savings_month: number
  reward_balance: number
  rewards_earned_month: number
  cashback_earned_month_minor: number
  cashback_earned_month: number
  account_count: number
  credit_card_count: number
  upcoming_due_dates: Array<Record<string, unknown>>
  recent_transactions: Array<Record<string, unknown>>
  latest_rewards: Array<Record<string, unknown>>
}

export interface AccountResponse {
  id: number
  name: string
  type: string
  classification: string
  currency: string
  opening_balance_minor: number
  opening_balance_on: string
  archived_at?: string | null
  created_at: string
  updated_at: string
  balance_minor?: number | null
  balance?: number | null
}

export interface AccountsResponse {
  accounts: AccountResponse[]
}

export interface CreateAccountRequest {
  name: string
  account_type: string
  opening_balance?: number
  opening_balance_on?: string | null
}

export interface UpdateAccountRequest {
  name?: string | null
  opening_balance?: number | null
  opening_balance_on?: string | null
}

export interface AccountMutationResponse {
  item: AccountResponse
  meta: MutationMeta
}

export interface CreditCardResponse {
  account_id: number
  name: string
  type: string
  network?: string | null
  last4?: string | null
  credit_limit_minor: number
  credit_limit: number
  statement_day: number
  due_day_offset: number
  autopay: boolean
  opening_balance_minor: number
  opening_balance_on: string
  archived_at?: string | null
  created_at: string
  updated_at: string
  balance_minor?: number | null
  balance?: number | null
  outstanding_minor?: number | null
  outstanding?: number | null
  utilization_ratio?: number | null
  utilization_percent?: number | null
  available_limit_minor?: number | null
  available_limit?: number | null
  current_statement?: Record<string, unknown> | null
  previous_statement?: Record<string, unknown> | null
}

export interface CreditCardsResponse {
  cards: CreditCardResponse[]
}

export interface CreateCreditCardRequest {
  name: string
  credit_limit: number
  statement_day: number
  due_day_offset: number
  opening_balance?: number
  opening_balance_on?: string | null
  network?: string | null
  last4?: string | null
  autopay?: boolean
}

export interface UpdateCreditCardRequest {
  name?: string | null
  credit_limit?: number | null
  statement_day?: number | null
  due_day_offset?: number | null
  network?: string | null
  last4?: string | null
  autopay?: boolean | null
}

export interface CreditCardMutationResponse {
  item: CreditCardResponse
  meta: MutationMeta
}

export interface StatementResponse {
  id: number
  account_id: number
  period_start: string
  period_end: string
  statement_date: string
  due_date: string
  total_due_minor?: number | null
  min_due_minor?: number | null
  created_at: string
  updated_at: string
  spend_minor?: number | null
  spend?: number | null
  paid_minor?: number | null
  paid?: number | null
  remaining_due_minor?: number | null
  remaining_due?: number | null
  status?: string | null
  transactions?: Array<Record<string, unknown>> | null
}

export interface StatementsResponse {
  statements: StatementResponse[]
}

export interface TransactionResponse {
  id: number
  account_id: number
  direction: string
  kind: string
  amount_minor: number
  amount: number
  category_id?: number | null
  merchant_id?: number | null
  note?: string | null
  occurred_on: string
  transfer_group_id?: string | null
  statement_id?: number | null
  source: string
  created_at: string
  updated_at: string
  account_name?: string | null
  category_name?: string | null
  merchant_name?: string | null
}

export interface TransactionsResponse {
  transactions: TransactionResponse[]
  total: number
  limit: number
  offset: number
}

export interface CreateTransactionRequest {
  account_id: number
  kind: string
  amount: number
  occurred_on: string
  category_id?: number | null
  merchant_id?: number | null
  note?: string | null
  direction?: string | null
}

export interface UpdateTransactionRequest {
  amount?: number | null
  category_id?: number | null
  merchant_id?: number | null
  note?: string | null
  occurred_on?: string | null
}

export interface TransactionMutationResponse {
  item: TransactionResponse
  meta: MutationMeta
}

export interface CategoryResponse {
  id: number
  name: string
  created_at: string
  updated_at: string
}

export interface CategoriesResponse {
  categories: CategoryResponse[]
}

export interface CreateCategoryRequest {
  name: string
}

export interface UpdateCategoryRequest {
  name: string
}

export interface CategoryMutationResponse {
  item: CategoryResponse
  meta: MutationMeta
}

export interface MerchantResponse {
  id: number
  name: string
  created_at: string
  updated_at: string
}

export interface MerchantsResponse {
  merchants: MerchantResponse[]
}

export interface CreateMerchantRequest {
  name: string
}

export interface UpdateMerchantRequest {
  name: string
}

export interface MerchantMutationResponse {
  item: MerchantResponse
  meta: MutationMeta
}

export interface TransferLegResponse {
  id: number
  account_id: number
  direction: string
  kind: string
  amount_minor: number
  amount: number
  note?: string | null
  occurred_on: string
  transfer_group_id?: string | null
  statement_id?: number | null
  source: string
  created_at: string
  updated_at: string
}

export interface TransferGroupResponse {
  legs: TransferLegResponse[]
  transfer_group_id: string
  statement_id?: number | null
}

export interface TransferMutationResponse {
  item: TransferGroupResponse
  meta: MutationMeta
}

export interface CreateTransferRequest {
  from_account_id: number
  to_account_id: number
  amount: number
  occurred_on: string
  note?: string | null
}

export interface CreateCardPaymentRequest {
  from_account_id: number
  card_account_id: number
  amount: number
  occurred_on: string
  statement_id?: number | null
  note?: string | null
  confirm_overpayment?: boolean
}

export interface PayStatementRequest {
  from_account_id: number
  payment_mode?: string
  amount?: number | null
  note?: string | null
  confirm_overpayment?: boolean
}

export interface UpdateStatementRequest {
  total_due?: number | null
  min_due?: number | null
}

export interface StatementMutationResponse {
  item: StatementResponse
  meta: MutationMeta
}

export interface RewardProgramResponse {
  id: number
  account_id: number
  name: string
  unit: string
  earn_rate_note?: string | null
  expiry_note?: string | null
  created_at: string
  updated_at: string
  balance?: Record<string, unknown> | null
  account_name?: string | null
  bank_name?: string | null
  status?: string | null
}

export interface RewardProgramsResponse {
  programs: RewardProgramResponse[]
}

export interface RewardsOverviewResponse {
  total_balance: number
  total_balance_cashback_minor: number
  total_balance_cashback: number
  earned_month: number
  earned_year: number
  earned_lifetime: number
  earned_month_cashback_minor: number
  earned_year_cashback_minor: number
  earned_lifetime_cashback_minor: number
  earned_month_cashback: number
  earned_year_cashback: number
  earned_lifetime_cashback: number
}

export interface RewardLedgerResponse {
  program: RewardProgramResponse
  balance: Record<string, unknown>
  events: Array<Record<string, unknown>>
  yearly_earned: number
  monthly_earned: number
  lifetime_earned: number
}

export interface RewardProgramDetailResponse {
  program: RewardProgramResponse
  balance: Record<string, unknown>
  status: string
  account_name: string
  bank_name: string
  earned_month: number
  earned_year: number
  earned_lifetime: number
  monthly_history: Array<Record<string, unknown>>
  recent_events: Array<Record<string, unknown>>
  related_transactions: Array<Record<string, unknown>>
}

export interface CashbackRuleResponse {
  id: number
  program_id: number
  account_id?: number | null
  name: string
  flat_rate_bps: number
  flat_rate_percent: number
  category_multipliers: Record<number, number>
  merchant_multipliers: Record<number, number>
  excluded_category_ids: number[]
  excluded_merchant_ids: number[]
  excluded_mcc_codes: string[]
  excluded_transaction_kinds: string[]
  monthly_cap_minor?: number | null
  monthly_cap?: number | null
  minimum_spend_minor: number
  minimum_spend: number
  created_at: string
  updated_at: string
  program_name?: string | null
}

export interface CashbackSummaryResponse {
  monthly_earned_minor: number
  monthly_earned: number
  rules: CashbackRuleResponse[]
}

/** WebSocket envelope: { event: string, data: Record<string, unknown> } */
export interface WebSocketEvent {
  event: string
  data: Record<string, unknown>
}

export type ChatWebSocketEvent =
  | 'chat.started'
  | 'chat.routing'
  | 'chat.tool_called'
  | 'chat.reply'
  | 'chat.finished'
  | 'chat.error'

export type EventsWebSocketEvent =
  | 'api.started'
  | 'task.created'
  | 'task.updated'
  | 'spending.logged'
  | 'finance.account.created'
  | 'finance.account.updated'
  | 'finance.account.archived'
  | 'finance.account.restored'
  | 'finance.credit_card.created'
  | 'finance.credit_card.updated'
  | 'finance.transaction.created'
  | 'finance.transaction.updated'
  | 'finance.transaction.deleted'
  | 'finance.transfer.created'
  | 'finance.card_payment.created'
  | 'finance.statement.created'
  | 'finance.statement.updated'
  | 'finance.statement.paid'
  | 'finance.category.created'
  | 'finance.category.updated'
  | 'finance.category.deleted'
  | 'finance.merchant.created'
  | 'finance.merchant.updated'
  | 'finance.merchant.deleted'
  | 'finance.cashback.earned'
  | 'progress.logged'
  | 'product.created'
  | 'product.updated'
  | 'calendar.updated'
  | 'reminder.created'
  | 'memory.created'
  | 'habit.logged'
  | 'graph.updated'
  | 'reminder.triggered'
  | 'pomodoro.completed'
  | 'reflection.completed'
  | 'entity_extraction.completed'
