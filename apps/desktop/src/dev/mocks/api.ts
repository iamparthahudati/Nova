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
