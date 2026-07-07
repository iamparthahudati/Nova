export interface FinanceDashboard {
  totalBalance: number
  totalAssets: number
  totalLiabilities: number
  cashAvailable: number
  creditUtilizationPercent: number
  totalOutstanding: number
  totalAvailableCredit: number
  cardsNearDueCount: number
  incomeMonth: number
  spentMonth: number
  savingsMonth: number
  rewardBalance: number
  rewardsEarnedMonth: number
  cashbackEarnedMonth: number
  accountCount: number
  creditCardCount: number
  upcomingDueDates: UpcomingDueDate[]
  recentTransactions: FinanceTransaction[]
  latestRewards: LatestReward[]
}

export interface LatestReward {
  id: number
  programId: number
  programName: string
  accountId: number
  kind: string
  direction: string
  amount: number
  unit: string
  amountDisplay: number
  note?: string | null
  occurredOn: string
}

export interface UpcomingDueDate {
  accountId: number
  cardName: string
  statementId: number
  dueDate: string
  remainingDue?: number | null
  status: string
}

export interface FinanceAccount {
  id: number
  name: string
  type: string
  classification: string
  currency: string
  openingBalanceMinor: number
  openingBalanceOn: string
  archivedAt?: string | null
  createdAt?: string | null
  updatedAt?: string | null
  balance?: number | null
  balanceMinor?: number | null
}

export interface FinanceCreditCard {
  accountId: number
  name: string
  type: string
  network?: string | null
  last4?: string | null
  creditLimit: number
  statementDay: number
  dueDayOffset: number
  autopay: boolean
  archivedAt?: string | null
  balance?: number | null
  outstanding?: number | null
  utilizationPercent?: number | null
  availableLimit?: number | null
  currentStatement?: FinanceStatement | null
  previousStatement?: FinanceStatement | null
}

export interface FinanceStatement {
  id: number
  accountId: number
  periodStart: string
  periodEnd: string
  statementDate: string
  dueDate: string
  totalDue?: number | null
  minDue?: number | null
  spend?: number | null
  paid?: number | null
  remainingDue?: number | null
  status?: string | null
  transactions?: FinanceTransaction[]
}

export interface FinanceTransaction {
  id: number
  accountId: number
  direction: string
  kind: string
  amount: number
  amountMinor: number
  categoryId?: number | null
  merchantId?: number | null
  note?: string | null
  occurredOn: string
  accountName?: string | null
  categoryName?: string | null
  merchantName?: string | null
}

export interface FinanceCategory {
  id: number
  name: string
}

export interface FinanceMerchant {
  id: number
  name: string
}

export interface RewardProgram {
  id: number
  accountId: number
  name: string
  unit: string
  earnRateNote?: string | null
  expiryNote?: string | null
  accountName?: string | null
  bankName?: string | null
  status?: string | null
  balance?: RewardBalance | null
}

export interface RewardBalance {
  programId: number
  unit: string
  balance: number
  totalEarned: number
  totalRedeemed: number
  totalExpired: number
}

export interface RewardLedger {
  program: RewardProgram
  balance: RewardBalance
  events: RewardEvent[]
  yearlyEarned: number
  monthlyEarned: number
  lifetimeEarned: number
}

export interface RewardEvent {
  id: number
  programId: number
  kind: string
  direction: string
  amount: number
  note?: string | null
  occurredOn: string
  transactionId?: number | null
}

export interface RewardsOverview {
  totalBalance: number
  totalBalanceCashbackMinor: number
  totalBalanceCashback: number
  earnedMonth: number
  earnedYear: number
  earnedLifetime: number
  earnedMonthCashbackMinor: number
  earnedYearCashbackMinor: number
  earnedLifetimeCashbackMinor: number
  earnedMonthCashback: number
  earnedYearCashback: number
  earnedLifetimeCashback: number
}

export interface RewardMonthlyHistory {
  month: string
  earned: number
  redeemed: number
  expired: number
  adjusted: number
}

export interface RewardProgramDetail {
  program: RewardProgram
  balance: RewardBalance
  status: string
  accountName: string
  bankName: string
  earnedMonth: number
  earnedYear: number
  earnedLifetime: number
  monthlyHistory: RewardMonthlyHistory[]
  recentEvents: RewardEvent[]
  relatedTransactions: FinanceTransaction[]
}

export interface CashbackRule {
  id: number
  programId: number
  accountId?: number | null
  name: string
  flatRatePercent: number
  flatRateBps: number
  categoryMultipliers: Record<number, number>
  merchantMultipliers: Record<number, number>
  excludedCategoryIds: number[]
  excludedMerchantIds: number[]
  excludedMccCodes: string[]
  excludedTransactionKinds: string[]
  monthlyCap?: number | null
  minimumSpend: number
  programName?: string | null
  accountName?: string | null
  cardName?: string | null
  earnedMonth?: number | null
  remainingCap?: number | null
  status?: string | null
  excludedCategoryNames: string[]
  excludedMerchantNames: string[]
}

export interface CashbackSummary {
  totalBalance: number
  monthlyEarned: number
  earnedYear: number
  earnedLifetime: number
  remainingMonthlyCap?: number | null
  activeRulesCount: number
  rules: CashbackRule[]
}

export interface CashbackActivityEvent {
  id: number
  programId: number
  programName: string
  ruleId?: number | null
  ruleName?: string | null
  transactionId?: number | null
  transactionNote?: string | null
  amount: number
  occurredOn: string
  note?: string | null
}

export interface CashbackMonthlyHistory {
  month: string
  earned: number
  redeemed: number
  expired: number
  adjusted: number
}

export interface CashbackRuleDetail {
  rule: CashbackRule
  programName: string
  accountName: string
  cardName: string
  earnedMonth: number
  earnedYear: number
  earnedLifetime: number
  monthlyHistory: CashbackMonthlyHistory[]
  recentEvents: RewardEvent[]
  relatedTransactions: FinanceTransaction[]
  remainingCap?: number | null
}

export interface TransactionsPage {
  transactions: FinanceTransaction[]
  total: number
  limit: number
  offset: number
}
