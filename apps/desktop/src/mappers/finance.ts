import type {
  AccountResponse,
  CashbackRuleResponse,
  CashbackSummaryResponse,
  CreditCardResponse,
  FinanceDashboardResponse,
  RewardLedgerResponse,
  RewardProgramResponse,
  StatementResponse,
  TransactionResponse,
  TransactionsResponse,
} from '@nova/api-contracts'
import type {
  CashbackRule,
  CashbackSummary,
  FinanceAccount,
  FinanceCreditCard,
  FinanceDashboard,
  FinanceStatement,
  FinanceTransaction,
  RewardEvent,
  RewardLedger,
  RewardProgram,
  TransactionsPage,
  UpcomingDueDate,
} from '@/view-models/finance'

function mapTransaction(row: TransactionResponse | Record<string, unknown>): FinanceTransaction {
  const txn = row as TransactionResponse
  return {
    id: txn.id,
    accountId: txn.account_id,
    direction: txn.direction,
    kind: txn.kind,
    amount: txn.amount,
    amountMinor: txn.amount_minor,
    categoryId: txn.category_id,
    merchantId: txn.merchant_id,
    note: txn.note,
    occurredOn: txn.occurred_on,
    accountName: txn.account_name,
    categoryName: txn.category_name,
    merchantName: txn.merchant_name,
  }
}

function mapStatement(row: StatementResponse | Record<string, unknown>): FinanceStatement {
  const stmt = row as StatementResponse
  return {
    id: stmt.id,
    accountId: stmt.account_id,
    periodStart: stmt.period_start,
    periodEnd: stmt.period_end,
    statementDate: stmt.statement_date,
    dueDate: stmt.due_date,
    spend: stmt.spend,
    paid: stmt.paid,
    remainingDue: stmt.remaining_due,
    status: stmt.status,
    transactions: stmt.transactions?.map((txn) => mapTransaction(txn as unknown as TransactionResponse)),
  }
}

export function mapFinanceDashboard(response: FinanceDashboardResponse): FinanceDashboard {
  return {
    totalBalance: response.total_balance,
    totalAssets: response.total_assets,
    totalLiabilities: response.total_liabilities,
    creditUtilizationPercent: response.credit_utilization_percent,
    spentMonth: response.spent_month,
    rewardBalance: response.reward_balance,
    cashbackEarnedMonth: response.cashback_earned_month,
    upcomingDueDates: response.upcoming_due_dates.map(
      (row): UpcomingDueDate => ({
        accountId: row.account_id as number,
        cardName: row.card_name as string,
        statementId: row.statement_id as number,
        dueDate: row.due_date as string,
        remainingDue: row.remaining_due as number | null,
        status: row.status as string,
      }),
    ),
    recentTransactions: response.recent_transactions.map((txn) =>
      mapTransaction(txn as unknown as TransactionResponse),
    ),
  }
}

export function mapAccount(row: AccountResponse): FinanceAccount {
  return {
    id: row.id,
    name: row.name,
    type: row.type,
    classification: row.classification,
    currency: row.currency,
    openingBalanceMinor: row.opening_balance_minor,
    openingBalanceOn: row.opening_balance_on,
    archivedAt: row.archived_at,
    balance: row.balance,
    balanceMinor: row.balance_minor,
  }
}

export function mapCreditCard(row: CreditCardResponse): FinanceCreditCard {
  return {
    accountId: row.account_id,
    name: row.name,
    type: row.type,
    network: row.network,
    last4: row.last4,
    creditLimit: row.credit_limit,
    statementDay: row.statement_day,
    dueDayOffset: row.due_day_offset,
    autopay: row.autopay,
    balance: row.balance,
    outstanding: row.outstanding,
    utilizationPercent: row.utilization_percent,
    availableLimit: row.available_limit,
    currentStatement: row.current_statement ? mapStatement(row.current_statement) : null,
    previousStatement: row.previous_statement ? mapStatement(row.previous_statement) : null,
  }
}

export function mapStatementList(rows: StatementResponse[]): FinanceStatement[] {
  return rows.map(mapStatement)
}

export function mapTransactionsPage(response: TransactionsResponse): TransactionsPage {
  return {
    transactions: response.transactions.map(mapTransaction),
    total: response.total,
    limit: response.limit,
    offset: response.offset,
  }
}

export function mapRewardProgram(row: RewardProgramResponse): RewardProgram {
  const balance = row.balance as Record<string, unknown> | null | undefined
  return {
    id: row.id,
    accountId: row.account_id,
    name: row.name,
    unit: row.unit,
    earnRateNote: row.earn_rate_note,
    balance: balance
      ? {
          programId: balance.program_id as number,
          unit: balance.unit as string,
          balance: balance.balance as number,
          totalEarned: balance.total_earned as number,
          totalRedeemed: balance.total_redeemed as number,
          totalExpired: balance.total_expired as number,
        }
      : null,
  }
}

export function mapRewardLedger(response: RewardLedgerResponse): RewardLedger {
  const balance = response.balance as Record<string, unknown>
  return {
    program: mapRewardProgram(response.program),
    balance: {
      programId: balance.program_id as number,
      unit: balance.unit as string,
      balance: balance.balance as number,
      totalEarned: balance.total_earned as number,
      totalRedeemed: balance.total_redeemed as number,
      totalExpired: balance.total_expired as number,
    },
    events: response.events.map(
      (event): RewardEvent => ({
        id: event.id as number,
        programId: event.program_id as number,
        kind: event.kind as string,
        direction: event.direction as string,
        amount: event.amount as number,
        note: event.note as string | null,
        occurredOn: event.occurred_on as string,
      }),
    ),
    yearlyEarned: response.yearly_earned,
  }
}

export function mapCashbackRule(row: CashbackRuleResponse): CashbackRule {
  return {
    id: row.id,
    programId: row.program_id,
    name: row.name,
    flatRatePercent: row.flat_rate_percent,
    categoryMultipliers: row.category_multipliers,
    merchantMultipliers: row.merchant_multipliers,
    monthlyCap: row.monthly_cap,
    minimumSpend: row.minimum_spend,
    programName: row.program_name,
  }
}

export function mapCashbackSummary(response: CashbackSummaryResponse): CashbackSummary {
  return {
    monthlyEarned: response.monthly_earned,
    rules: response.rules.map(mapCashbackRule),
  }
}

export function mapCategory(row: { id: number; name: string }) {
  return { id: row.id, name: row.name }
}

export function mapMerchant(row: { id: number; name: string }) {
  return { id: row.id, name: row.name }
}
