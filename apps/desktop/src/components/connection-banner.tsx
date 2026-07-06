import { isMockMode } from '@/config/env'
import { useSystemStatus } from '@/hooks/use-system-status'

export function ConnectionBanner() {
  const systemStatus = useSystemStatus()

  if (isMockMode()) {
    return (
      <div className="mb-4 rounded-md border border-border bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
        Mock mode enabled — backend requests and WebSocket connections are disabled.
      </div>
    )
  }

  if (systemStatus.isLoading) {
    return null
  }

  if (systemStatus.isError) {
    return (
      <div className="mb-4 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-xs text-destructive">
        Cannot reach Nova backend. Showing cached data when available.
      </div>
    )
  }

  if (systemStatus.data?.status !== 'ok') {
    return (
      <div className="mb-4 rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-200">
        Nova backend is degraded. Some features may be unavailable.
      </div>
    )
  }

  return null
}
