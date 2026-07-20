'use client'

/**
 * WebSocket hook · connect to brain · auto-reconnect · typed events.
 */
import { useEffect, useRef, useState, useCallback } from 'react'

import { getToken } from './client'

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'

export type WSStatus = 'connecting' | 'open' | 'closing' | 'closed' | 'error'

export interface BrainEvent {
  type: string
  [key: string]: any
}

interface UseWSOptions {
  enabled?: boolean
  onEvent?: (event: BrainEvent) => void
  reconnectDelayMs?: number
}

export function useSellIAWebSocket({
  enabled = true,
  onEvent,
  reconnectDelayMs = 3000,
}: UseWSOptions = {}) {
  const [status, setStatus] = useState<WSStatus>('closed')
  const [lastEvent, setLastEvent] = useState<BrainEvent | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const shouldReconnectRef = useRef(true)
  const onEventRef = useRef(onEvent)
  onEventRef.current = onEvent

  const connect = useCallback(() => {
    const token = getToken()
    if (!token || !enabled) return

    setStatus('connecting')
    const ws = new WebSocket(`${WS_BASE}?token=${encodeURIComponent(token)}`)
    wsRef.current = ws

    ws.onopen = () => setStatus('open')

    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data) as BrainEvent
        setLastEvent(data)
        onEventRef.current?.(data)
      } catch {
        // swallow
      }
    }

    ws.onerror = () => setStatus('error')

    ws.onclose = () => {
      setStatus('closed')
      wsRef.current = null
      if (shouldReconnectRef.current && enabled) {
        reconnectTimerRef.current = setTimeout(connect, reconnectDelayMs)
      }
    }
  }, [enabled, reconnectDelayMs])

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false
    if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current)
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  const send = useCallback((payload: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload))
      return true
    }
    return false
  }, [])

  useEffect(() => {
    shouldReconnectRef.current = true
    if (enabled) connect()
    return () => {
      shouldReconnectRef.current = false
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current)
      if (wsRef.current) wsRef.current.close()
    }
  }, [connect, enabled])

  return { status, lastEvent, send, connect, disconnect }
}
