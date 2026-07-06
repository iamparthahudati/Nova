import { AnimatePresence, motion } from 'framer-motion'
import { PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { navItems } from '@/app/nav'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useAppStore } from '@/store/app-store'

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useAppStore()

  return (
    <aside className={cn('h-full border-r border-border bg-card/70 transition-all duration-200', sidebarCollapsed ? 'w-20' : 'w-72')}>
      <div className="flex h-12 items-center justify-between border-b border-border px-3">
        <AnimatePresence initial={false}>
          {!sidebarCollapsed && (
            <motion.p
              key="label"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              className="text-xs font-medium uppercase tracking-wider text-muted-foreground"
            >
              Navigation
            </motion.p>
          )}
        </AnimatePresence>
        <Button variant="ghost" size="icon" onClick={toggleSidebar} aria-label="Toggle sidebar">
          {sidebarCollapsed ? <PanelLeftOpen className="size-4" /> : <PanelLeftClose className="size-4" />}
        </Button>
      </div>
      <nav className="space-y-1 p-2">
        {navItems.map(({ icon: Icon, label, path }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              cn(
                'group flex h-10 items-center gap-2 rounded-lg px-3 text-sm text-muted-foreground transition',
                isActive && 'bg-accent text-accent-foreground',
                'hover:bg-accent/80 hover:text-accent-foreground',
              )
            }
          >
            <Icon className="size-4 shrink-0" />
            <AnimatePresence initial={false}>
              {!sidebarCollapsed && (
                <motion.span key={label} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  {label}
                </motion.span>
              )}
            </AnimatePresence>
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
