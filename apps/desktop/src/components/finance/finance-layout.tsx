import { NavLink, Outlet } from 'react-router-dom'
import {
  Banknote,
  CreditCard,
  FileText,
  Gift,
  LayoutDashboard,
  Percent,
  Receipt,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const financeNav = [
  { label: 'Dashboard', path: '/finance', icon: LayoutDashboard, end: true },
  { label: 'Accounts', path: '/finance/accounts', icon: Banknote },
  { label: 'Credit Cards', path: '/finance/credit-cards', icon: CreditCard },
  { label: 'Statements', path: '/finance/statements', icon: FileText },
  { label: 'Transactions', path: '/finance/transactions', icon: Receipt },
  { label: 'Rewards', path: '/finance/rewards', icon: Gift },
  { label: 'Cashback', path: '/finance/cashback', icon: Percent },
]

export function FinanceLayout() {
  return (
    <div className="flex min-h-full flex-col gap-6 lg:flex-row">
      <nav className="flex shrink-0 flex-row gap-1 overflow-x-auto lg:w-52 lg:flex-col lg:overflow-visible">
        {financeNav.map(({ label, path, icon: Icon, end }) => (
          <NavLink
            key={path}
            to={path}
            end={end}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-muted-foreground transition whitespace-nowrap',
                isActive && 'bg-accent text-accent-foreground',
                'hover:bg-accent/80 hover:text-accent-foreground',
              )
            }
          >
            <Icon className="size-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="min-w-0 flex-1">
        <Outlet />
      </div>
    </div>
  )
}
