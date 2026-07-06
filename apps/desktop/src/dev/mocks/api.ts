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
  CashbackSummary,
  FinanceAccount,
  FinanceCreditCard,
  FinanceDashboard,
  FinanceStatement,
  RewardLedger,
  RewardProgram,
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

export async function getHome(): Promise<HomeViewModel> {
  await latency()
  const earned = mockSpending.filter((entry) => entry.type === 'earned').reduce((total, entry) => total + entry.amount, 0)
  const spent = mockSpending.filter((entry) => entry.type === 'spent').reduce((total, entry) => total + entry.amount, 0)
  const openTasks = mockTasks.filter((task) => task.status === 'open')

  return {
    cards: [
      { id: 'open_tasks', label: 'Open tasks', value: String(openTasks.length), icon: 'list-todo' },
      { id: 'earned_month', label: 'Monthly earned', value: String(earned), icon: 'wallet' },
      { id: 'spent_month', label: 'Monthly spent', value: String(spent), icon: 'activity' },
      { id: 'memory_count', label: 'Memories indexed', value: String(mockMemories.length), icon: 'brain' },
      { id: 'reminder_count', label: 'Upcoming reminders', value: String(mockReminders.length), icon: 'bell' },
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
        title: "Today's tasks",
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
  return {
    totalBalance: 12500,
    totalAssets: 12500,
    totalLiabilities: 0,
    creditUtilizationPercent: 0,
    spentMonth: 4200,
    rewardBalance: 0,
    cashbackEarnedMonth: 0,
    upcomingDueDates: [],
    recentTransactions: [],
  }
}

export async function getAccounts(): Promise<FinanceAccount[]> {
  await latency()
  return [
    {
      id: 1,
      name: 'Cash',
      type: 'cash',
      classification: 'asset',
      currency: 'INR',
      openingBalanceMinor: 0,
      openingBalanceOn: '2026-01-01',
      balance: 12500,
    },
  ]
}

export async function getCreditCards(): Promise<FinanceCreditCard[]> {
  await latency()
  return []
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

export async function getStatements(_accountId: number): Promise<FinanceStatement[]> {
  await latency()
  return []
}

export async function getFinanceTransactions(): Promise<TransactionsPage> {
  await latency()
  return { transactions: [], total: 0, limit: 50, offset: 0 }
}

export async function getRewardPrograms(): Promise<RewardProgram[]> {
  await latency()
  return []
}

export async function getRewardLedger(_programId: number): Promise<RewardLedger> {
  await latency()
  return {
    program: { id: 1, accountId: 1, name: 'Mock', unit: 'points' },
    balance: { programId: 1, unit: 'points', balance: 0, totalEarned: 0, totalRedeemed: 0, totalExpired: 0 },
    events: [],
    yearlyEarned: 0,
  }
}

export async function getCashbackSummary(): Promise<CashbackSummary> {
  await latency()
  return { monthlyEarned: 0, rules: [] }
}

export async function createAccount(input: { name: string; account_type: string; opening_balance?: number }) {
  await latency()
  return {
    item: { ...mockFinanceAccount, name: input.name, type: input.account_type },
    meta: { message: 'Account created (mock).' },
  }
}

export async function archiveAccount(_accountId: number) {
  await latency()
  return { item: mockFinanceAccount, meta: { message: 'Account archived (mock).' } }
}

export async function createTransaction(_input: unknown) {
  await latency()
  return { meta: { message: 'Transaction created (mock).' } }
}

export async function getCategories() {
  await latency()
  return [{ id: 1, name: 'Food' }]
}

export async function createCategory(input: { name: string }) {
  await latency()
  return { item: { id: 2, name: input.name, created_at: '', updated_at: '' }, meta: { message: 'Category created (mock).' } }
}

export async function getMerchants() {
  await latency()
  return [{ id: 1, name: 'Amazon' }]
}

export async function createMerchant(input: { name: string }) {
  await latency()
  return { item: { id: 2, name: input.name, created_at: '', updated_at: '' }, meta: { message: 'Merchant created (mock).' } }
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
