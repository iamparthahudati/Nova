import type {
  CalendarEvent,
  GraphEdge,
  GraphEntity,
  MemoryItem,
  Product,
  ProfileObservation,
  Reminder,
  SpendingEntry,
  Task,
} from '@/view-models'

export const mockTasks: Task[] = [
  { id: 1, text: 'Finalize Nova desktop shell architecture', status: 'open', due: '2026-07-07', createdAt: '2026-07-04T07:10:00Z' },
  { id: 2, text: 'Review semantic memory ranking thresholds', status: 'open', due: '2026-07-08', createdAt: '2026-07-04T09:20:00Z' },
  { id: 3, text: 'Draft milestone 2.11 API contracts', status: 'done', createdAt: '2026-07-03T08:30:00Z' },
  { id: 4, text: 'Validate graph extraction retry strategy', status: 'open', createdAt: '2026-07-02T11:05:00Z' },
]

export const mockReminders: Reminder[] = [
  { id: 1, text: 'Weekly reflection run', remindDate: '2026-07-06', remindTime: '21:00', createdAt: '2026-07-02T07:00:00Z' },
  { id: 2, text: 'Submit investor update', remindDate: '2026-07-07', remindTime: '10:30', createdAt: '2026-07-03T09:10:00Z' },
  { id: 3, text: 'Health checkup follow-up', remindDate: '2026-07-10', createdAt: '2026-07-01T10:00:00Z' },
]

export const mockSpending: SpendingEntry[] = [
  { id: 1, type: 'earned', amount: 120000, note: 'Product consulting retainer', createdAt: '2026-07-01T04:00:00Z' },
  { id: 2, type: 'spent', amount: 12900, note: 'Cloud + tooling subscriptions', createdAt: '2026-07-02T08:15:00Z' },
  { id: 3, type: 'spent', amount: 8400, note: 'Team contractor payout', createdAt: '2026-07-03T13:30:00Z' },
  { id: 4, type: 'earned', amount: 45000, note: 'Workshop revenue', createdAt: '2026-07-04T07:30:00Z' },
]

export const mockProducts: Product[] = [
  { id: 1, name: 'Nova Core Assistant', status: 'shipped', store: 'Direct', price: 2999, soldCount: 84, createdAt: '2026-05-18T06:00:00Z' },
  { id: 2, name: 'Nova Team Workspace', status: 'building', store: 'Private beta', price: 7499, soldCount: 12, createdAt: '2026-06-25T08:00:00Z' },
]

export const mockMemories: MemoryItem[] = [
  {
    id: 'm-001',
    text: 'Partha prefers morning deep-work blocks from 8:30 to 11:30.',
    sourceType: 'insight',
    tier: 'long_term',
    importance: 0.93,
    accessCount: 28,
    createdAt: '2026-06-20T03:10:00Z',
  },
  {
    id: 'm-002',
    text: 'Desktop shell should launch with mock API first, backend integration later.',
    sourceType: 'conversation',
    sourceId: 'conv-2026-07-05',
    tier: 'medium_term',
    importance: 0.89,
    accessCount: 9,
    createdAt: '2026-07-05T07:10:00Z',
  },
  {
    id: 'm-003',
    text: 'Calendar service remains AppleScript backed and should be accessed via services/api facade.',
    sourceType: 'journal',
    tier: 'medium_term',
    importance: 0.76,
    accessCount: 3,
    createdAt: '2026-07-03T05:45:00Z',
  },
]

export const mockEntities: GraphEntity[] = [
  { id: 'e-1', type: 'person', canonicalName: 'Partha Hudati', attributes: { role: 'Founder' } },
  { id: 'e-2', type: 'project', canonicalName: 'Nova Desktop Shell', attributes: { phase: '2.11' } },
  { id: 'e-3', type: 'service', canonicalName: 'Memory Service', attributes: { storage: 'SQLite + LanceDB' } },
  { id: 'e-4', type: 'service', canonicalName: 'API Facade', attributes: { transport: 'HTTP + WebSocket' } },
]

export const mockEdges: GraphEdge[] = [
  { id: 'g-1', fromEntityId: 'e-1', toEntityId: 'e-2', relationType: 'LEADS', weight: 2.2, sourceMemoryId: 'm-002' },
  { id: 'g-2', fromEntityId: 'e-2', toEntityId: 'e-4', relationType: 'DEPENDS_ON', weight: 1.4, sourceMemoryId: 'm-002' },
  { id: 'g-3', fromEntityId: 'e-4', toEntityId: 'e-3', relationType: 'READS', weight: 1.0, sourceMemoryId: 'm-003' },
]

export const mockCalendar: Array<CalendarEvent & { start: string; end: string }> = [
  {
    id: 'c-1',
    title: 'Desktop shell UI review',
    start: '2026-07-05T09:30:00Z',
    end: '2026-07-05T10:00:00Z',
    timeLabel: '2026-07-05T09:30:00Z',
    date: '2026-07-05',
    unavailable: false,
  },
  {
    id: 'c-2',
    title: 'Investor sync',
    start: '2026-07-05T12:30:00Z',
    end: '2026-07-05T13:00:00Z',
    timeLabel: '2026-07-05T12:30:00Z',
    date: '2026-07-05',
    unavailable: false,
  },
  {
    id: 'c-3',
    title: 'Weekly planning',
    start: '2026-07-06T03:30:00Z',
    end: '2026-07-06T04:15:00Z',
    timeLabel: '2026-07-06T03:30:00Z',
    date: '2026-07-06',
    unavailable: false,
  },
]

export const mockProfile: ProfileObservation[] = [
  { id: 'work:Prefers architecture-first sequencing before implementation.', observation: 'Prefers architecture-first sequencing before implementation.', category: 'work', confidence: 0.91 },
  { id: 'productivity:Responds better to concise summaries with explicit next steps.', observation: 'Responds better to concise summaries with explicit next steps.', category: 'productivity', confidence: 0.82 },
]
