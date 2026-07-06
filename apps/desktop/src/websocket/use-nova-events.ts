import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { WebSocketEvent } from '@nova/api-contracts'
import { getWebSocketUrl, isMockMode } from '@/config/env'
import { eventInvalidationMap } from '@/websocket/invalidation-map'

const MAX_RECONNECT_DELAY_MS = 8000

export function useNovaEvents() {
  const queryClient = useQueryClient()
  const reconnectAttempt = useRef(0)
  const socketRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<number | null>(null)

  useEffect(() => {
    if (isMockMode()) {
      return
    }

    let cancelled = false

    const scheduleReconnect = () => {
      if (cancelled) {
        return
      }
      const delay = Math.min(1000 * 2 ** reconnectAttempt.current, MAX_RECONNECT_DELAY_MS)
      reconnectAttempt.current += 1
      reconnectTimer.current = window.setTimeout(() => {
        connect()
      }, delay)
    }

    const connect = () => {
      if (cancelled) {
        return
      }

      const socket = new WebSocket(getWebSocketUrl('/ws/events'))
      socketRef.current = socket

      socket.onopen = () => {
        reconnectAttempt.current = 0
      }

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(String(event.data)) as WebSocketEvent
          const keys = eventInvalidationMap[payload.event as keyof typeof eventInvalidationMap]
          if (!keys) {
            return
          }
          for (const queryKey of keys) {
            void queryClient.invalidateQueries({ queryKey })
          }
        } catch {
          // ignore malformed events
        }
      }

      socket.onclose = () => {
        if (!cancelled) {
          scheduleReconnect()
        }
      }

      socket.onerror = () => {
        socket.close()
      }
    }

    connect()

    return () => {
      cancelled = true
      if (reconnectTimer.current !== null) {
        window.clearTimeout(reconnectTimer.current)
      }
      socketRef.current?.close()
      socketRef.current = null
    }
  }, [queryClient])
}
