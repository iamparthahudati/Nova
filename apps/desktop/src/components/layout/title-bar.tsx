import { Maximize2, Minimize2, MoonStar, SunMedium, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAppStore } from '@/store/app-store'

export function TitleBar() {
  const { theme, setTheme } = useAppStore()

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark')
  }

  return (
    <header className="drag-region flex h-12 items-center justify-between border-b border-border bg-card/85 px-3 backdrop-blur-md">
      <div className="no-drag flex items-center gap-2 text-sm text-muted-foreground">
        <span className="rounded-md bg-primary/20 px-2 py-1 font-medium text-primary">Nova</span>
        <span className="text-xs uppercase tracking-wider">Desktop Shell</span>
      </div>
      <div className="no-drag flex items-center gap-1">
        <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Toggle theme">
          {theme === 'dark' ? <SunMedium className="size-4" /> : <MoonStar className="size-4" />}
        </Button>
        <Button variant="ghost" size="icon" onClick={() => window.desktopWindow?.minimize()} aria-label="Minimize window">
          <Minimize2 className="size-4" />
        </Button>
        <Button variant="ghost" size="icon" onClick={() => window.desktopWindow?.maximize()} aria-label="Maximize window">
          <Maximize2 className="size-4" />
        </Button>
        <Button variant="ghost" size="icon" onClick={() => window.desktopWindow?.close()} aria-label="Close window">
          <X className="size-4" />
        </Button>
      </div>
    </header>
  )
}
