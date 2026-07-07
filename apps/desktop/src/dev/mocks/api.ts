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
  FinanceCreditCard,
  FinanceDashboard,
  FinanceStatement,
  FinanceTransaction,
  RewardLedger,
  RewardProgram,
  RewardProgramDetail,
  RewardsOverview,
  TransactionsPage,
} from '@/view-models/finance'
import {
  mockCalendar,
  mockEdges,
  mockEntities,
  mockMemories,
  mockProducts,
  mockProfile,
  mockReminders,
  mockSpending,
  mockTasks,
} from '@/dev/mocks/data'

const latency = async (ms = 140) => new Promise((resolve) => setTimeout(resolve, ms))

const mockCategories = [
  { id: 1, name: 'Food', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' },
  { id: 2, name: 'Transport', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' },
  { id: 3, name: 'Salary', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' },
]
const mockMerchants = [
  { id: 1, name: 'Amazon', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' },
  { id: 2, name: 'Swiggy', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' },
]
let nextCategoryId = 4
let nextMerchantId = 3
let nextTransactionId = 5
const mockTransactions: FinanceTransaction[] = [
  {
    id: 1,
    accountId: 1,
    direction: 'debit',
    kind: 'expense',
    amount: 450,
    amountMinor: 45_000,
    categoryId: 1,
    merchantId: 1,
    note: 'Weekly groceries',
    occurredOn: '2026-07-01',
    accountName: 'Cash',
    categoryName: 'Groceries',
    merchantName: 'BigBasket',
  },
  {
    id: 2,
    accountId: 1,
    direction: 'credit',
    kind: 'income',
    amount: 2500,
    amountMinor: 250_000,
    categoryId: 2,
    merchantId: null,
    note: 'Freelance payout',
    occurredOn: '2026-07-03',
    accountName: 'Cash',
    categoryName: 'Salary',
    merchantName: null,
  },
  {
    id: 3,
    accountId: 2,
    direction: 'debit',
    kind: 'expense',
    amount: 12000,
    amountMinor: 1_200_000,
    categoryId: 1,
    merchantId: 2,
    note: 'Food delivery',
    occurredOn: '2026-06-02',
    accountName: 'HDFC Millennia',
    categoryName: 'Food',
    merchantName: 'Swiggy',
  },
  {
    id: 4,
    accountId: 2,
    direction: 'debit',
    kind: 'expense',
    amount: 30000,
    amountMinor: 3_000_000,
    categoryId: 2,
    merchantId: 1,
    note: 'Electronics',
    occurredOn: '2026-06-10',
    accountName: 'HDFC Millennia',
    categoryName: 'Transport',
    merchantName: 'Amazon',
  },
]
const mockAccounts: FinanceAccount[] = [
  {
    id: 1,
    name: 'Cash',
    type: 'cash',
    classification: 'asset',
    currency: 'INR',
    openingBalanceMinor: 1_250_000,
    openingBalanceOn: '2026-01-01',
    balance: 12500,
  },
]

const mockCreditCards: FinanceCreditCard[] = [
  {
    accountId: 2,
    name: 'HDFC Millennia',
    type: 'credit_card',
    network: 'Visa',
    last4: '4821',
    creditLimit: 200000,
    statementDay: 15,
    dueDayOffset: 20,
    autopay: true,
    outstanding: 42000,
    availableLimit: 158000,
    utilizationPercent: 21,
    currentStatement: {
      id: 101,
      accountId: 2,
      periodStart: '2026-05-16',
      periodEnd: '2026-06-15',
      statementDate: '2026-06-15',
      dueDate: '2026-07-05',
      totalDue: 42000,
      minDue: 4200,
      spend: 42000,
      paid: 0,
      remainingDue: 42000,
      status: 'due',
    },
    previousStatement: {
      id: 100,
      accountId: 2,
      periodStart: '2026-04-16',
      periodEnd: '2026-05-15',
      statementDate: '2026-05-15',
      dueDate: '2026-06-04',
      totalDue: 38500,
      minDue: 3850,
      spend: 38500,
      paid: 38500,
      remainingDue: 0,
      status: 'paid',
    },
  },
  {
    accountId: 3,
    name: 'ICICI Amazon Pay',
    type: 'credit_card',
    network: 'RuPay',
    last4: '9034',
    creditLimit: 150000,
    statementDay: 10,
    dueDayOffset: 18,
    autopay: false,
    outstanding: 112000,
    availableLimit: 38000,
    utilizationPercent: 74.7,
    currentStatement: {
      id: 201,
      accountId: 3,
      periodStart: '2026-05-11',
      periodEnd: '2026-06-10',
      statementDate: '2026-06-10',
      dueDate: '2026-06-28',
      totalDue: 112000,
      minDue: 11200,
      spend: 112000,
      paid: 20000,
      remainingDue: 92000,
      status: 'partial',
    },
    previousStatement: {
      id: 200,
      accountId: 3,
      periodStart: '2026-04-11',
      periodEnd: '2026-05-10',
      statementDate: '2026-05-10',
      dueDate: '2026-05-28',
      totalDue: 98000,
      minDue: 9800,
      spend: 98000,
      paid: 98000,
      remainingDue: 0,
      status: 'paid',
    },
  },
]

const mockStatements: FinanceStatement[] = [
  ...(mockCreditCards[0].previousStatement ? [mockCreditCards[0].previousStatement] : []),
  ...(mockCreditCards[0].currentStatement ? [mockCreditCards[0].currentStatement] : []),
  ...(mockCreditCards[1].previousStatement ? [mockCreditCards[1].previousStatement] : []),
  ...(mockCreditCards[1].currentStatement ? [mockCreditCards[1].currentStatement] : []),
]

function monthBounds() {
  const today = new Date()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  return {
    start: `${today.getFullYear()}-${month}-01`,
    end: today.toISOString().slice(0, 10),
  }
}

function computeMockFinanceDashboard(): FinanceDashboard {
  const { start, end } = monthBounds()
  const spentMonth = mockTransactions
    .filter((txn) => txn.kind === 'expense' && txn.occurredOn >= start && txn.occurredOn <= end)
    .reduce((sum, txn) => sum + txn.amount, 0)

  const totalAssets = mockAccounts.reduce((sum, account) => {
    const openingMinor =
      account.openingBalanceMinor > 0
        ? account.openingBalanceMinor
        : Math.round((account.balance ?? 0) * 100)
    const deltaMinor = mockTransactions
      .filter((txn) => txn.accountId === account.id)
      .reduce(
        (delta, txn) => delta + (txn.direction === 'credit' ? txn.amountMinor : -txn.amountMinor),
        0,
      )
    return sum + (openingMinor + deltaMinor) / 100
  }, 0)

  const totalLiabilities = mockCreditCards.reduce((sum, card) => sum + (card.outstanding ?? 0), 0)

  return {
    totalBalance: totalAssets - totalLiabilities,
    totalAssets,
    totalLiabilities,
    cashAvailable: totalAssets,
    creditUtilizationPercent: 74.7,
    totalOutstanding: 224000,
    totalAvailableCredit: 76000,
    cardsNearDueCount: 2,
    incomeMonth: 85000,
    spentMonth,
    savingsMonth: 85000 - spentMonth,
    rewardBalance: 12450,
    rewardsEarnedMonth: 3200,
    cashbackEarnedMonth: 1250,
    accountCount: mockAccounts.length,
    creditCardCount: mockCreditCards.length,
    upcomingDueDates: mockCreditCards
      .filter((card) => card.currentStatement && card.currentStatement.status !== 'paid')
      .map((card) => ({
        accountId: card.accountId,
        cardName: card.name,
        statementId: card.currentStatement!.id,
        dueDate: card.currentStatement!.dueDate,
        remainingDue: card.currentStatement!.remainingDue,
        status: card.currentStatement!.status ?? 'due',
      })),
    recentTransactions: mockTransactions.slice(0, 10),
    latestRewards: [
      {
        id: 1,
        programId: 1,
        programName: 'Reward Points',
        accountId: 2,
        kind: 'earned',
        direction: 'credit',
        amount: 450,
        unit: 'points',
        amountDisplay: 450,
        note: 'Dining spend',
        occurredOn: '2026-06-28',
      },
      {
        id: 2,
        programId: 2,
        programName: 'CashPoints',
        accountId: 3,
        kind: 'earned',
        direction: 'credit',
        amount: 12500,
        unit: 'cashback_minor',
        amountDisplay: 125,
        note: 'June cashback',
        occurredOn: '2026-06-25',
      },
    ],
  }
}

export async function getHome(): Promise<HomeViewModel> {
  await latency()
  const earned = mockSpending.filter((entry) => entry.type === 'earned').reduce((total, entry) => total + entry.amount, 0)
  const spent = mockSpending.filter((entry) => entry.type === 'spent').reduce((total, entry) => total + entry.amount, 0)
  const openTasks = mockTasks.filter((task) => task.status === 'open')
  const today = new Date().toISOString().slice(0, 10)
  const upcomingReminders = mockReminders.filter((reminder) => reminder.remindDate >= today)

  return {
    cards: [
      { id: 'open_tasks', label: 'Open tasks', value: String(openTasks.length), icon: 'list-todo' },
      { id: 'earned_month', label: 'Monthly earned', value: String(earned), icon: 'wallet' },
      { id: 'spent_month', label: 'Monthly spent', value: String(spent), icon: 'activity' },
      { id: 'memory_count', label: 'Memories indexed', value: String(mockMemories.length), icon: 'brain' },
      { id: 'reminder_count', label: 'Upcoming reminders', value: String(upcomingReminders.length), icon: 'bell' },
      {
        id: 'products_building',
        label: 'Products in progress',
        value: String(mockProducts.filter((product) => product.status === 'building').length),
        icon: 'package',
      },
    ],
    panels: [
      {
        id: 'reminders',
        title: 'Upcoming reminders',
        items: mockReminders.map((reminder) => ({
          id: String(reminder.id),
          primary: reminder.text,
          secondary: [reminder.remindDate, reminder.remindTime ? `at ${reminder.remindTime}` : ''].filter(Boolean).join(' '),
          meta: {
            remindDate: reminder.remindDate,
            remindTime: reminder.remindTime,
          },
        })),
      },
      {
        id: 'open_tasks',
        title: 'Open tasks',
        items: openTasks.map((task) => ({
          id: String(task.id),
          primary: task.text,
          secondary: task.due ? `Due ${task.due}` : 'No due date',
          meta: { status: task.status, due: task.due },
        })),
      },
      {
        id: 'calendar',
        title: 'Calendar events',
        items: mockCalendar.map((event) => ({
          id: event.id,
          primary: event.title,
          secondary: new Date(event.start).toLocaleString(),
          meta: { date: event.date, unavailable: false },
        })),
      },
    ],
  }
}

export async function listTasks(): Promise<Task[]> {
  await latency()
  return mockTasks
}

export async function listReminders(): Promise<Reminder[]> {
  await latency()
  return mockReminders
}

export async function getSpending(): Promise<SpendingViewModel> {
  await latency()
  const earnedMonth = mockSpending.filter((entry) => entry.type === 'earned').reduce((total, entry) => total + entry.amount, 0)
  const spentMonth = mockSpending.filter((entry) => entry.type === 'spent').reduce((total, entry) => total + entry.amount, 0)
  return {
    earnedMonth,
    spentMonth,
    transactions: mockSpending,
  }
}

export async function listProducts(): Promise<Product[]> {
  await latency()
  return mockProducts
}

export async function listMemories(): Promise<MemoriesViewModel> {
  await latency()
  return {
    memories: mockMemories,
    total: mockMemories.length,
    limit: 50,
    offset: 0,
  }
}

export async function listGraph(): Promise<GraphViewModel> {
  await latency()
  return { entities: mockEntities, edges: mockEdges }
}

export async function getCalendar(): Promise<CalendarViewModel> {
  await latency()
  return {
    date: '2026-07-06',
    unavailable: false,
    events: mockCalendar.map((event) => ({
      id: event.id,
      title: event.title,
      timeLabel: `${new Date(event.start).toLocaleString()} - ${new Date(event.end).toLocaleTimeString()}`,
      date: event.date,
      unavailable: false,
    })),
  }
}

export async function getSettings(): Promise<SettingsViewModel> {
  await latency()
  return {
    assistantName: 'Nova',
    voiceName: 'default',
    briefingTime: '08:00',
    eveningWrapupTime: '21:00',
    claudeModel: 'claude-haiku-4-5-20251001',
    semanticMemoryEnabled: true,
    entityExtractionEnabled: true,
    graphContextEnabled: true,
    observations: mockProfile,
  }
}

export async function getSystemStatus(): Promise<SystemStatusViewModel> {
  await latency()
  return {
    status: 'ok',
    version: '0.1.0',
    subsystems: [],
  }
}

const mockFinanceAccount = {
  id: 1,
  name: 'Cash',
  type: 'cash',
  classification: 'asset',
  currency: 'INR',
  opening_balance_minor: 0,
  opening_balance_on: '2026-01-01',
  archived_at: null,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  balance_minor: 1250000,
  balance: 12500,
}

export async function getFinanceDashboard(): Promise<FinanceDashboard> {
  await latency()
  return computeMockFinanceDashboard()
}

export async function getAccounts(): Promise<FinanceAccount[]> {
  await latency()
  return mockAccounts.map((account) => ({ ...account }))
}

export async function getCreditCards(): Promise<FinanceCreditCard[]> {
  await latency()
  return mockCreditCards.map((card) => ({ ...card }))
}

export async function getCreditCard(accountId: number): Promise<FinanceCreditCard> {
  await latency()
  const card = mockCreditCards.find((row) => row.accountId === accountId)
  if (!card) throw new Error(`Credit card ${accountId} not found (mock).`)
  return { ...card }
}

export async function createCardPayment(input: {
  from_account_id: number
  card_account_id: number
  amount: number
  occurred_on: string
  statement_id?: number | null
}) {
  await latency()
  return { meta: { message: `Paid ₹${input.amount} toward card ${input.card_account_id} (mock).` } }
}

export async function createCreditCard(input: {
  name: string
  credit_limit: number
  statement_day: number
  due_day_offset: number
  opening_balance?: number
  network?: string | null
  last4?: string | null
  autopay?: boolean
}) {
  await latency()
  return {
    item: {
      account_id: 2,
      name: input.name,
      type: 'credit_card',
      network: input.network ?? null,
      last4: input.last4 ?? null,
      credit_limit_minor: Math.round(input.credit_limit * 100),
      credit_limit: input.credit_limit,
      statement_day: input.statement_day,
      due_day_offset: input.due_day_offset,
      autopay: input.autopay ?? false,
      opening_balance_minor: Math.round((input.opening_balance ?? 0) * 100),
      opening_balance_on: '2026-01-01',
      archived_at: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      balance_minor: 0,
      balance: 0,
      outstanding_minor: 0,
      outstanding: 0,
      utilization_ratio: 0,
      utilization_percent: 0,
      available_limit_minor: Math.round(input.credit_limit * 100),
      available_limit: input.credit_limit,
    },
    meta: { message: 'Credit card created (mock).' },
  }
}

export async function updateCreditCard(
  accountId: number,
  input: {
    name?: string | null
    credit_limit?: number | null
    statement_day?: number | null
    due_day_offset?: number | null
    network?: string | null
    last4?: string | null
    autopay?: boolean | null
  },
) {
  await latency()
  return {
    item: {
      account_id: accountId,
      name: input.name ?? 'Mock Card',
      type: 'credit_card',
      network: input.network ?? null,
      last4: input.last4 ?? null,
      credit_limit_minor: Math.round((input.credit_limit ?? 100000) * 100),
      credit_limit: input.credit_limit ?? 100000,
      statement_day: input.statement_day ?? 15,
      due_day_offset: input.due_day_offset ?? 20,
      autopay: input.autopay ?? false,
      opening_balance_minor: 0,
      opening_balance_on: '2026-01-01',
      archived_at: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      balance_minor: 0,
      balance: 0,
      outstanding_minor: 0,
      outstanding: 0,
      utilization_ratio: 0,
      utilization_percent: 0,
      available_limit_minor: Math.round((input.credit_limit ?? 100000) * 100),
      available_limit: input.credit_limit ?? 100000,
    },
    meta: { message: 'Credit card updated (mock).' },
  }
}

export async function getStatements(accountId: number): Promise<FinanceStatement[]> {
  await latency()
  return mockStatements
    .filter((statement) => statement.accountId === accountId)
    .map((statement) => ({ ...statement }))
}

export async function getStatement(statementId: number): Promise<FinanceStatement> {
  await latency()
  const statement = mockStatements.find((row) => row.id === statementId)
  if (!statement) {
    throw new Error('Statement not found')
  }
  const transactions = mockTransactions.filter(
    (txn) =>
      txn.accountId === statement.accountId &&
      txn.occurredOn >= statement.periodStart &&
      txn.occurredOn <= statement.periodEnd,
  )
  return { ...statement, transactions }
}

export async function getFinanceTransactions(params?: {
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
  await latency()
  let rows = [...mockTransactions]
  if (params?.accountId) {
    rows = rows.filter((txn) => txn.accountId === params.accountId)
  }
  if (params?.categoryId) {
    rows = rows.filter((txn) => txn.categoryId === params.categoryId)
  }
  if (params?.merchantId) {
    rows = rows.filter((txn) => txn.merchantId === params.merchantId)
  }
  if (params?.direction) {
    rows = rows.filter((txn) => txn.direction === params.direction)
  }
  if (params?.kind) {
    rows = rows.filter((txn) => txn.kind === params.kind)
  }
  if (params?.startDate) {
    rows = rows.filter((txn) => txn.occurredOn >= params.startDate!)
  }
  if (params?.endDate) {
    rows = rows.filter((txn) => txn.occurredOn <= params.endDate!)
  }
  if (params?.search) {
    const query = params.search.toLowerCase()
    rows = rows.filter(
      (txn) =>
        txn.note?.toLowerCase().includes(query) ||
        txn.merchantName?.toLowerCase().includes(query) ||
        txn.categoryName?.toLowerCase().includes(query),
    )
  }
  const limit = params?.limit ?? 50
  const offset = params?.offset ?? 0
  const total = rows.length
  return {
    transactions: rows.slice(offset, offset + limit),
    total,
    limit,
    offset,
  }
}

const mockRewardPrograms: RewardProgram[] = [
  {
    id: 1,
    accountId: 101,
    name: 'Reward Points',
    unit: 'points',
    earnRateNote: '5x on dining, 2x on travel',
    expiryNote: 'Points expire after 24 months',
    accountName: 'HDFC Millennia',
    bankName: 'HDFC Millennia',
    status: 'expiring',
    balance: {
      programId: 1,
      unit: 'points',
      balance: 12450,
      totalEarned: 18200,
      totalRedeemed: 4200,
      totalExpired: 1550,
    },
  },
  {
    id: 2,
    accountId: 102,
    name: 'CashPoints',
    unit: 'cashback_minor',
    earnRateNote: '1% on all spends',
    expiryNote: null,
    accountName: 'ICICI Amazon Pay',
    bankName: 'ICICI Amazon Pay',
    status: 'active',
    balance: {
      programId: 2,
      unit: 'cashback_minor',
      balance: 245000,
      totalEarned: 310000,
      totalRedeemed: 65000,
      totalExpired: 0,
    },
  },
]

const mockRewardEvents = [
  {
    id: 1,
    programId: 1,
    kind: 'earned',
    direction: 'credit',
    amount: 1200,
    note: 'Dining spend',
    occurredOn: '2026-07-05',
    transactionId: 501,
  },
  {
    id: 2,
    programId: 1,
    kind: 'redeemed',
    direction: 'debit',
    amount: 800,
    note: 'Amazon voucher',
    occurredOn: '2026-07-03',
    transactionId: null,
  },
  {
    id: 3,
    programId: 1,
    kind: 'earned',
    direction: 'credit',
    amount: 2400,
    note: 'Travel booking',
    occurredOn: '2026-06-28',
    transactionId: 502,
  },
  {
    id: 4,
    programId: 1,
    kind: 'expired',
    direction: 'debit',
    amount: 500,
    note: 'Annual expiry sweep',
    occurredOn: '2026-06-15',
    transactionId: null,
  },
]

export async function getRewardsOverview(): Promise<RewardsOverview> {
  await latency()
  return {
    totalBalance: 12450,
    totalBalanceCashbackMinor: 245000,
    totalBalanceCashback: 2450,
    earnedMonth: 3200,
    earnedYear: 12450,
    earnedLifetime: 18200,
    earnedMonthCashbackMinor: 18500,
    earnedYearCashbackMinor: 245000,
    earnedLifetimeCashbackMinor: 310000,
    earnedMonthCashback: 185,
    earnedYearCashback: 2450,
    earnedLifetimeCashback: 3100,
  }
}

export async function getRewardPrograms(): Promise<RewardProgram[]> {
  await latency()
  return mockRewardPrograms
}

export async function getRewardProgramDetail(programId: number): Promise<RewardProgramDetail> {
  await latency()
  const program = mockRewardPrograms.find((row) => row.id === programId) ?? mockRewardPrograms[0]
  return {
    program,
    balance: program.balance!,
    status: program.status ?? 'active',
    accountName: program.accountName ?? 'Credit card',
    bankName: program.bankName ?? 'Credit card',
    earnedMonth: 3200,
    earnedYear: 12450,
    earnedLifetime: program.balance?.totalEarned ?? 0,
    monthlyHistory: [
      { month: '2026-07', earned: 1200, redeemed: 800, expired: 0, adjusted: 0 },
      { month: '2026-06', earned: 2400, redeemed: 0, expired: 500, adjusted: 0 },
      { month: '2026-05', earned: 1800, redeemed: 1200, expired: 0, adjusted: 0 },
      { month: '2026-04', earned: 900, redeemed: 0, expired: 0, adjusted: 0 },
      { month: '2026-03', earned: 1500, redeemed: 400, expired: 0, adjusted: 0 },
      { month: '2026-02', earned: 600, redeemed: 0, expired: 1050, adjusted: 0 },
    ],
    recentEvents: mockRewardEvents,
    relatedTransactions: [
      {
        id: 501,
        accountId: 101,
        direction: 'debit',
        kind: 'expense',
        amount: 2400,
        amountMinor: 240000,
        note: 'Dining spend',
        occurredOn: '2026-07-05',
        accountName: 'HDFC Millennia',
        categoryName: 'Dining',
        merchantName: 'Truffles',
      },
    ],
  }
}

export async function getRewardLedger(programId: number): Promise<RewardLedger> {
  await latency()
  const program = mockRewardPrograms.find((row) => row.id === programId) ?? mockRewardPrograms[0]
  return {
    program,
    balance: program.balance!,
    events: mockRewardEvents.filter((event) => event.programId === program.id),
    yearlyEarned: 12450,
    monthlyEarned: 3200,
    lifetimeEarned: program.balance?.totalEarned ?? 0,
  }
}

const mockCashbackRules: CashbackSummary['rules'] = [
  {
    id: 1,
    programId: 2,
    accountId: 102,
    name: 'Flat 1% on all spends',
    flatRatePercent: 1,
    flatRateBps: 100,
    categoryMultipliers: { 3: 500 },
    merchantMultipliers: {},
    excludedCategoryIds: [],
    excludedMerchantIds: [],
    excludedMccCodes: [],
    excludedTransactionKinds: [],
    monthlyCap: 500,
    minimumSpend: 100,
    programName: 'CashPoints',
    accountName: 'ICICI Amazon Pay',
    cardName: 'ICICI Amazon Pay',
    earnedMonth: 185,
    remainingCap: 315,
    status: 'active',
    excludedCategoryNames: [],
    excludedMerchantNames: [],
  },
  {
    id: 2,
    programId: 2,
    accountId: 102,
    name: '5% on dining',
    flatRatePercent: 5,
    flatRateBps: 500,
    categoryMultipliers: {},
    merchantMultipliers: {},
    excludedCategoryIds: [9],
    excludedMerchantIds: [],
    excludedMccCodes: [],
    excludedTransactionKinds: ['fee'],
    monthlyCap: 250,
    minimumSpend: 0,
    programName: 'CashPoints',
    accountName: 'ICICI Amazon Pay',
    cardName: 'ICICI Amazon Pay',
    earnedMonth: 250,
    remainingCap: 0,
    status: 'capped',
    excludedCategoryNames: ['Rent'],
    excludedMerchantNames: [],
  },
]

const mockCashbackActivity: CashbackActivityEvent[] = [
  {
    id: 901,
    programId: 2,
    programName: 'CashPoints',
    ruleId: 1,
    ruleName: 'Flat 1% on all spends',
    transactionId: 501,
    transactionNote: 'Amazon order',
    amount: 45,
    occurredOn: '2026-07-06',
    note: 'cashback rule 1',
  },
  {
    id: 902,
    programId: 2,
    programName: 'CashPoints',
    ruleId: 2,
    ruleName: '5% on dining',
    transactionId: 502,
    transactionNote: 'Dinner at Social',
    amount: 120,
    occurredOn: '2026-07-05',
    note: 'cashback rule 2',
  },
]

export async function getCashbackSummary(): Promise<CashbackSummary> {
  await latency()
  return {
    totalBalance: 2450,
    monthlyEarned: 435,
    earnedYear: 2450,
    earnedLifetime: 3100,
    remainingMonthlyCap: 315,
    activeRulesCount: mockCashbackRules.length,
    rules: mockCashbackRules,
  }
}

export async function getCashbackActivity(): Promise<CashbackActivityEvent[]> {
  await latency()
  return mockCashbackActivity
}

export async function getCashbackRuleDetail(ruleId: number): Promise<CashbackRuleDetail> {
  await latency()
  const rule = mockCashbackRules.find((row) => row.id === ruleId) ?? mockCashbackRules[0]
  return {
    rule,
    programName: rule.programName ?? 'CashPoints',
    accountName: rule.accountName ?? 'ICICI Amazon Pay',
    cardName: rule.cardName ?? 'ICICI Amazon Pay',
    earnedMonth: rule.earnedMonth ?? 0,
    earnedYear: 2450,
    earnedLifetime: 3100,
    remainingCap: rule.remainingCap,
    monthlyHistory: [
      { month: '2026-07', earned: rule.earnedMonth ?? 0, redeemed: 0, expired: 0, adjusted: 0 },
      { month: '2026-06', earned: 380, redeemed: 0, expired: 0, adjusted: 0 },
      { month: '2026-05', earned: 290, redeemed: 0, expired: 0, adjusted: 0 },
      { month: '2026-04', earned: 410, redeemed: 0, expired: 0, adjusted: 0 },
      { month: '2026-03', earned: 320, redeemed: 0, expired: 0, adjusted: 0 },
      { month: '2026-02', earned: 275, redeemed: 0, expired: 0, adjusted: 0 },
    ],
    recentEvents: mockRewardEvents.filter((event) => event.programId === rule.programId),
    relatedTransactions: mockTransactions.slice(0, 2),
  }
}

export async function createAccount(input: { name: string; account_type: string; opening_balance?: number }) {
  await latency()
  const classification = input.account_type === 'loan' || input.account_type === 'credit_card' ? 'liability' : 'asset'
  const account: FinanceAccount = {
    id: mockAccounts.length + 1,
    name: input.name,
    type: input.account_type,
    classification,
    currency: 'INR',
    openingBalanceMinor: Math.round((input.opening_balance ?? 0) * 100),
    openingBalanceOn: '2026-01-01',
    createdAt: '2026-01-01T00:00:00Z',
    updatedAt: '2026-01-01T00:00:00Z',
    balance: input.opening_balance ?? 0,
  }
  mockAccounts.push(account)
  return {
    item: {
      ...mockFinanceAccount,
      id: account.id,
      name: input.name,
      type: input.account_type,
      classification,
      opening_balance_minor: account.openingBalanceMinor,
      balance: account.balance,
      balance_minor: account.openingBalanceMinor,
    },
    meta: { message: 'Account created (mock).' },
  }
}

export async function updateAccount(
  accountId: number,
  input: { name?: string | null; opening_balance?: number | null; opening_balance_on?: string | null },
) {
  await latency()
  const account = mockAccounts.find((row) => row.id === accountId)
  if (!account) throw new Error('Account not found')
  if (input.name) account.name = input.name
  if (input.opening_balance != null) {
    account.openingBalanceMinor = Math.round(input.opening_balance * 100)
    account.balance = input.opening_balance
  }
  if (input.opening_balance_on) account.openingBalanceOn = input.opening_balance_on
  return {
    item: {
      ...mockFinanceAccount,
      id: account.id,
      name: account.name,
      type: account.type,
      classification: account.classification,
      opening_balance_minor: account.openingBalanceMinor,
      opening_balance_on: account.openingBalanceOn,
      archived_at: account.archivedAt ?? null,
      balance: account.balance,
      balance_minor: account.openingBalanceMinor,
    },
    meta: { message: 'Account updated (mock).' },
  }
}

export async function archiveAccount(accountId: number) {
  await latency()
  const account = mockAccounts.find((row) => row.id === accountId)
  if (account) account.archivedAt = '2026-07-01T00:00:00Z'
  return {
    item: {
      ...mockFinanceAccount,
      id: accountId,
      archived_at: '2026-07-01T00:00:00Z',
    },
    meta: { message: 'Account archived (mock).' },
  }
}

export async function restoreAccount(accountId: number) {
  await latency()
  const account = mockAccounts.find((row) => row.id === accountId)
  if (account) account.archivedAt = null
  return {
    item: {
      ...mockFinanceAccount,
      id: accountId,
      archived_at: null,
    },
    meta: { message: 'Account restored (mock).' },
  }
}

export async function createTransaction(input: {
  account_id: number
  kind: string
  amount: number
  occurred_on: string
  category_id?: number | null
  merchant_id?: number | null
  note?: string | null
}) {
  await latency()
  const account = mockAccounts.find((row) => row.id === input.account_id)
  const category = mockCategories.find((row) => row.id === input.category_id)
  const merchant = mockMerchants.find((row) => row.id === input.merchant_id)
  const direction = input.kind === 'income' ? 'credit' : 'debit'
  const txn: FinanceTransaction = {
    id: nextTransactionId++,
    accountId: input.account_id,
    direction,
    kind: input.kind,
    amount: input.amount,
    amountMinor: Math.round(input.amount * 100),
    categoryId: input.category_id ?? null,
    merchantId: input.merchant_id ?? null,
    note: input.note ?? null,
    occurredOn: input.occurred_on,
    accountName: account?.name ?? `Account ${input.account_id}`,
    categoryName: category?.name ?? null,
    merchantName: merchant?.name ?? null,
  }
  mockTransactions.unshift(txn)
  return {
    item: txn,
    meta: { message: `Transaction logged on ${txn.accountName}.` },
  }
}

export async function updateTransaction(
  transactionId: number,
  input: {
    amount?: number | null
    category_id?: number | null
    merchant_id?: number | null
    note?: string | null
    occurred_on?: string | null
  },
) {
  await latency()
  const index = mockTransactions.findIndex((row) => row.id === transactionId)
  if (index === -1) throw new Error('Transaction not found.')
  const current = mockTransactions[index]
  const category = mockCategories.find((row) => row.id === (input.category_id ?? current.categoryId))
  const merchant = mockMerchants.find((row) => row.id === (input.merchant_id ?? current.merchantId))
  const amount = input.amount ?? current.amount
  const updated: FinanceTransaction = {
    ...current,
    amount,
    amountMinor: Math.round(amount * 100),
    categoryId: input.category_id ?? current.categoryId ?? null,
    merchantId: input.merchant_id ?? current.merchantId ?? null,
    note: input.note ?? current.note ?? null,
    occurredOn: input.occurred_on ?? current.occurredOn,
    categoryName: category?.name ?? null,
    merchantName: merchant?.name ?? null,
  }
  mockTransactions[index] = updated
  return {
    item: updated,
    meta: { message: 'Transaction updated (mock).' },
  }
}

export async function deleteTransaction(transactionId: number) {
  await latency()
  const index = mockTransactions.findIndex((row) => row.id === transactionId)
  if (index === -1) throw new Error('Transaction not found.')
  const [removed] = mockTransactions.splice(index, 1)
  return {
    item: removed,
    meta: { message: 'Transaction deleted (mock).' },
  }
}

export async function getCategories() {
  await latency()
  return mockCategories.map((row) => ({ ...row }))
}

export async function createCategory(input: { name: string }) {
  await latency()
  const item = {
    id: nextCategoryId++,
    name: input.name,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
  mockCategories.push(item)
  return { item, meta: { message: 'Category created (mock).' } }
}

export async function updateCategory(categoryId: number, input: { name: string }) {
  await latency()
  const index = mockCategories.findIndex((row) => row.id === categoryId)
  if (index === -1) throw new Error('Category not found.')
  mockCategories[index] = {
    ...mockCategories[index],
    name: input.name,
    updated_at: new Date().toISOString(),
  }
  return { item: mockCategories[index], meta: { message: 'Category updated (mock).' } }
}

export async function deleteCategory(categoryId: number) {
  await latency()
  const index = mockCategories.findIndex((row) => row.id === categoryId)
  if (index === -1) throw new Error('Category not found.')
  const [item] = mockCategories.splice(index, 1)
  return { item, meta: { message: 'Category deleted (mock).' } }
}

export async function getMerchants() {
  await latency()
  return mockMerchants.map((row) => ({ ...row }))
}

export async function createMerchant(input: { name: string }) {
  await latency()
  const item = {
    id: nextMerchantId++,
    name: input.name,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
  mockMerchants.push(item)
  return { item, meta: { message: 'Merchant created (mock).' } }
}

export async function updateMerchant(merchantId: number, input: { name: string }) {
  await latency()
  const index = mockMerchants.findIndex((row) => row.id === merchantId)
  if (index === -1) throw new Error('Merchant not found.')
  mockMerchants[index] = {
    ...mockMerchants[index],
    name: input.name,
    updated_at: new Date().toISOString(),
  }
  return { item: mockMerchants[index], meta: { message: 'Merchant updated (mock).' } }
}

export async function deleteMerchant(merchantId: number) {
  await latency()
  const index = mockMerchants.findIndex((row) => row.id === merchantId)
  if (index === -1) throw new Error('Merchant not found.')
  const [item] = mockMerchants.splice(index, 1)
  return { item, meta: { message: 'Merchant deleted (mock).' } }
}

export async function createTransfer(_input: unknown) {
  await latency()
  return { item: { legs: [], transfer_group_id: 'mock' }, meta: { message: 'Transfer created (mock).' } }
}

export async function payStatement(_statementId: number, _input: unknown) {
  await latency()
  return { item: { legs: [], transfer_group_id: 'mock' }, meta: { message: 'Statement paid (mock).' } }
}

export async function updateStatement(_statementId: number, _input: unknown) {
  await latency()
  return { item: {}, meta: { message: 'Statement updated (mock).' } }
}
