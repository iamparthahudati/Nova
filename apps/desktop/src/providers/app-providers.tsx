import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/query/client'
import { useNovaEvents } from '@/websocket/use-nova-events'

function NovaEventsBridge() {
  useNovaEvents()
  return null
}

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <NovaEventsBridge />
      {children}
    </QueryClientProvider>
  )
}
