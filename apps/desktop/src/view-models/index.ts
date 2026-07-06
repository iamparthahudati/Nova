export interface Task {
  id: number
  text: string
  status: string
  due?: string
  createdAt: string
}

export interface Reminder {
  id: number
  text: string
  remindDate: string
  remindTime?: string
  createdAt: string
}

export interface SpendingEntry {
  id: number
  type: string
  amount: number
  note?: string
  createdAt: string
}

export interface SpendingViewModel {
  earnedMonth: number
  spentMonth: number
  transactions: SpendingEntry[]
}

export interface Product {
  id: number
  name: string
  store?: string
  status: string
  price?: number
  soldCount: number
  createdAt: string
}

export interface MemoryItem {
  id: string
  text: string
  sourceType: string
  sourceId?: string
  tier: string
  importance: number
  accessCount: number
  createdAt: string
}

export interface MemoriesViewModel {
  memories: MemoryItem[]
  total: number
  limit: number
  offset: number
}

export interface GraphEntity {
  id: string
  type: string
  canonicalName: string
  attributes: Record<string, unknown>
}

export interface GraphEdge {
  id: string
  fromEntityId: string
  toEntityId: string
  relationType: string
  weight: number
  sourceMemoryId?: string
}

export interface GraphViewModel {
  entities: GraphEntity[]
  edges: GraphEdge[]
}

export interface CalendarEvent {
  id: string
  title: string
  timeLabel: string
  date: string
  unavailable: boolean
}

export interface CalendarViewModel {
  date: string
  events: CalendarEvent[]
  unavailable: boolean
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
  meta: Record<string, unknown>
}

export interface HomePanel {
  id: string
  title: string
  items: HomePanelItem[]
}

export interface HomeViewModel {
  cards: HomeCard[]
  panels: HomePanel[]
}

export interface ProfileObservation {
  id: string
  observation: string
  category: string
  confidence: number
}

export interface SettingsViewModel {
  assistantName: string
  voiceName: string
  briefingTime: string
  eveningWrapupTime?: string
  claudeModel: string
  semanticMemoryEnabled: boolean
  entityExtractionEnabled: boolean
  graphContextEnabled: boolean
  observations: ProfileObservation[]
}

export interface SystemStatusViewModel {
  status: string
  version: string
  subsystems: Array<{
    name: string
    status: string
    message?: string | null
  }>
}
