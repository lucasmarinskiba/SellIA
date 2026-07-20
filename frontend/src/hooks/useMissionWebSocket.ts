'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useAuth } from './useAuth'

interface MissionProgressMessage {
  type: 'mission_progress' | 'mission_status' | 'step_approval_request' | 'step_approved' | 'pong'
  mission_id: string
  step_id?: string
  status?: string
  message?: string
  step_title?: string
  data?: Record<string, unknown>
  timestamp?: string
}

export function useMissionWebSocket() {
  const { user } = useAuth()
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<MissionProgressMessage | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttempts = useRef(0)
  const MAX_RECONNECT_ATTEMPTS = 5

  const connect = useCallback(() => {
    if (!user || typeof window === 'undefined') return
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    // WebSocket auth via httpOnly cookie (same domain)
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'wss://localhost:8000'}/ws/missions`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      setIsConnected(true)
      reconnectAttempts.current = 0
      console.log('[MissionWS] Connected')
      // Send periodic pings
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }))
        } else {
          clearInterval(pingInterval)
        }
      }, 30000)
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as MissionProgressMessage
        setLastMessage(msg)

        // Dispatch custom event for components to listen
        if (msg.type === 'mission_progress' || msg.type === 'mission_status' || msg.type === 'step_approval_request') {
          window.dispatchEvent(new CustomEvent('mission-ws-update', { detail: msg }))
        }
      } catch (e) {
        console.error('[MissionWS] Parse error:', e)
      }
    }

    ws.onclose = () => {
      setIsConnected(false)
      wsRef.current = null
      // Exponential backoff reconnect
      if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = Math.min(1000 * 2 ** reconnectAttempts.current, 30000)
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttempts.current += 1
          connect()
        }, delay)
      }
    }

    ws.onerror = (err) => {
      console.error('[MissionWS] Error:', err)
      ws.close()
    }

    wsRef.current = ws
  }, [user])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    wsRef.current?.close()
    wsRef.current = null
    setIsConnected(false)
  }, [])

  const approveStep = useCallback((missionId: string, stepId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'approve_step',
        mission_id: missionId,
        step_id: stepId,
      }))
    }
  }, [])

  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  return { isConnected, lastMessage, approveStep, connect, disconnect }
}
