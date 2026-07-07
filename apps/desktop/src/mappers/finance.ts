import type {
  AccountResponse,
  CashbackRuleResponse,
  CashbackSummaryResponse,
  CreditCardResponse,
  FinanceDashboardResponse,
  RewardLedgerResponse,
  RewardProgramDetailResponse,
  RewardProgramResponse,
  RewardsOverviewResponse,
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
  RewardMonthlyHistory,
  RewardProgram,
  RewardProgramDetail,
  RewardsOverview,
  TransactionsPage,
  UpcomingDueDate,
  LatestReward,
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

function minorToRupees(minor?: number | null): number | null {
  if (minor == null) return null
  return minor / 100
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
    totalDue: minorToRupees(stmt.total_due_minor),
    minDue: minorToRupees(stmt.min_due_minor),
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
    cashAvailable: response.cash_available,
    creditUtilizationPercent: response.credit_utilization_percent,
    totalOutstanding: response.total_outstanding,
    totalAvailableCredit: response.total_available_credit,
    cardsNearDueCount: response.cards_near_due_count,
    incomeMonth: response.income_month,
    spentMonth: response.spent_month,
    savingsMonth: response.savings_month,
    rewardBalance: response.reward_balance,
    rewardsEarnedMonth: response.rewards_earned_month,
    cashbackEarnedMonth: response.cashback_earned_month,
    accountCount: response.account_count,
    creditCardCount: response.credit_card_count,
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
    latestRewards: response.latest_rewards.map(
      (row): LatestReward => ({
        id: row.id as number,
        programId: row.program_id as number,
        programName: row.program_name as string,
        accountId: row.account_id as number,
        kind: row.kind as string,
        direction: row.direction as string,
        amount: row.amount as number,
        unit: row.unit as string,
        amountDisplay: row.amount_display as number,
        note: row.note as string | null,
        occurredOn: row.occurred_on as string,
      }),
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
    createdAt: row.created_at,
    updatedAt: row.updated_at,
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
    archivedAt: row.archived_at,
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
    expiryNote: row.expiry_note,
    accountName: row.account_name,
    bankName: row.bank_name,
    status: row.status,
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

export function mapRewardsOverview(response: RewardsOverviewResponse): RewardsOverview {
  return {
    totalBalance: response.total_balance,
    totalBalanceCashbackMinor: response.total_balance_cashback_minor,
    totalBalanceCashback: response.total_balance_cashback,
    earnedMonth: response.earned_month,
    earnedYear: response.earned_year,
    earnedLifetime: response.earned_lifetime,
    earnedMonthCashbackMinor: response.earned_month_cashback_minor,
    earnedYearCashbackMinor: response.earned_year_cashback_minor,
    earnedLifetimeCashbackMinor: response.earned_lifetime_cashback_minor,
    earnedMonthCashback: response.earned_month_cashback,
    earnedYearCashback: response.earned_year_cashback,
    earnedLifetimeCashback: response.earned_lifetime_cashback,
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
        transactionId: event.transaction_id as number | null,
      }),
    ),
    yearlyEarned: response.yearly_earned,
    monthlyEarned: response.monthly_earned,
    lifetimeEarned: response.lifetime_earned,
  }
}

export function mapRewardProgramDetail(response: RewardProgramDetailResponse): RewardProgramDetail {
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
    status: response.status,
    accountName: response.account_name,
    bankName: response.bank_name,
    earnedMonth: response.earned_month,
    earnedYear: response.earned_year,
    earnedLifetime: response.earned_lifetime,
    monthlyHistory: response.monthly_history.map(
      (row): RewardMonthlyHistory => ({
        month: row.month as string,
        earned: row.earned as number,
        redeemed: row.redeemed as number,
        expired: row.expired as number,
        adjusted: row.adjusted as number,
      }),
    ),
    recentEvents: response.recent_events.map(
      (event): RewardEvent => ({
        id: event.id as number,
        programId: event.program_id as number,
        kind: event.kind as string,
        direction: event.direction as string,
        amount: event.amount as number,
        note: event.note as string | null,
        occurredOn: event.occurred_on as string,
        transactionId: event.transaction_id as number | null,
      }),
    ),
    relatedTransactions: response.related_transactions.map((txn) =>
      mapTransaction(txn as unknown as TransactionResponse),
    ),
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
