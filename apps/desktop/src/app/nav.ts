import type { LucideIcon } from 'lucide-react'
import {
  Banknote,
  CalendarDays,
  CircuitBoard,
  ClipboardList,
  Home,
  MessageSquareText,
  Settings,
  ShoppingBag,
  Waypoints,
} from 'lucide-react'

export interface NavItem {
  label: string
  path: string
  icon: LucideIcon
}

export const navItems: NavItem[] = [
  { label: 'Home', path: '/', icon: Home },
  { label: 'Chat', path: '/chat', icon: MessageSquareText },
  { label: 'Memory', path: '/memory', icon: CircuitBoard },
  { label: 'Knowledge Graph', path: '/knowledge-graph', icon: Waypoints },
  { label: 'Calendar', path: '/calendar', icon: CalendarDays },
  { label: 'Tasks', path: '/tasks', icon: ClipboardList },
  { label: 'Finance', path: '/finance', icon: Banknote },
  { label: 'Products', path: '/products', icon: ShoppingBag },
  { label: 'Settings', path: '/settings', icon: Settings },
]
