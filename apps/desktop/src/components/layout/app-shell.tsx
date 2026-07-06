import { Outlet } from 'react-router-dom'
import { ConnectionBanner } from '@/components/connection-banner'
import { Sidebar } from '@/components/layout/sidebar'
import { TitleBar } from '@/components/layout/title-bar'
import { useAppStore } from '@/store/app-store'

export function AppShell() {
  const theme = useAppStore((state) => state.theme)
  const resolvedTheme = theme === 'system' ? 'dark' : theme

  return (
    <div className={resolvedTheme}>
      <div className="flex h-screen w-screen flex-col bg-background text-foreground">
        <TitleBar />
        <div className="flex min-h-0 flex-1">
          <Sidebar />
          <main className="min-w-0 flex-1 overflow-auto p-5">
            <ConnectionBanner />
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}
