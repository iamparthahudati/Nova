export interface FinanceDashboard {
  totalBalance: number
  totalAssets: number
  totalLiabilities: number
  creditUtilizationPercent: number
  spentMonth: number
  rewardBalance: number
  cashbackEarnedMonth: number
  upcomingDueDates: UpcomingDueDate[]
  recentTransactions: FinanceTransaction[]
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
}

export interface RewardEvent {
  id: number
  programId: number
  kind: string
  direction: string
  amount: number
  note?: string | null
  occurredOn: string
}

export interface CashbackRule {
  id: number
  programId: number
  name: string
  flatRatePercent: number
  categoryMultipliers: Record<number, number>
  merchantMultipliers: Record<number, number>
  monthlyCap?: number | null
  minimumSpend: number
  programName?: string | null
}

export interface CashbackSummary {
  monthlyEarned: number
  rules: CashbackRule[]
}

export interface TransactionsPage {
  transactions: FinanceTransaction[]
  total: number
  limit: number
  offset: number
}
