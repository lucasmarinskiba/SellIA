'use client'

import { useState, useCallback, useRef, useEffect } from 'react'

export interface CUStep {
  step_number: number
  screenshot_url?: string
  action_type: string
  action_params?: any
  llm_response?: string
  timestamp?: string
}

export interface CUMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: string
}

export type CUSessionStatus = 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'stopped'

interface UseComputerUseWebSocketOptions {
  sessionId: string | null
  onStep?: (step: CUStep) => void
  onMessage?: (msg: CUMessage) => void
  onStatusChange?: (status: CUSessionStatus) => void
  onError?: (error: string) => void
}

export function useComputerUseWebSocket(options: UseComputerUseWebSocketOptions) {
  const { sessionId, onStep, onMessage, onStatusChange, onError } = options
  const [isConnected, setIsConnected] = useState(false)
  const [status, setStatus] = useState<CUSessionStatus>('pending')
  const [lastScreenshot, setLastScreenshot] = useState<string | null>(null)
  const [steps, setSteps] = useState<CUStep[]>([])
  const [messages, setMessages] = useState<CUMessage[]>([])
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const getWsUrl = useCallback((sid: string) => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const wsBase = baseUrl.replace(/^http/, 'ws')
    return `${wsBase}/ws/computer-use/${sid}`
  }, [])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setIsConnected(false)
  }, [])

  const connect = useCallback((sid: string) => {
    disconnect()

    try {
      const ws = new WebSocket(getWsUrl(sid))
      wsRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          if (data.type === 'step' && data.step) {
            setSteps(prev => [...prev, data.step])
            if (data.step.screenshot_url) {
              setLastScreenshot(data.step.screenshot_url)
            }
            onStep?.(data.step)
          }

          if (data.type === 'message' && data.message) {
            setMessages(prev => [...prev, data.message])
            onMessage?.(data.message)
          }

          if (data.type === 'status' && data.status) {
            setStatus(data.status)
            onStatusChange?.(data.status)
          }

          if (data.type === 'screenshot' && data.url) {
            setLastScreenshot(data.url)
          }
        } catch {
          // ignore non-JSON messages
        }
      }

      ws.onerror = () => {
        onError?.('Error de conexión WebSocket')
        setIsConnected(false)
      }

      ws.onclose = () => {
        setIsConnected(false)
        // Auto-reconnect si el sessionId sigue activo
        if (sessionId === sid) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect(sid)
          }, 3000)
        }
      }
    } catch (err) {
      onError?.('No se pudo conectar al WebSocket')
    }
  }, [disconnect, getWsUrl, onStep, onMessage, onStatusChange, onError, sessionId])

  const sendCommand = useCallback((command: 'pause' | 'resume' | 'stop' | 'chat', payload?: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: command, ...payload }))
    }
  }, [])

  useEffect(() => {
    if (sessionId) {
      connect(sessionId)
    } else {
      disconnect()
      setSteps([])
      setMessages([])
      setLastScreenshot(null)
      setStatus('pending')
    }
    return () => disconnect()
  }, [sessionId, connect, disconnect])

  return {
    isConnected,
    status,
    lastScreenshot,
    steps,
    messages,
    connect,
    disconnect,
    sendCommand,
  }
}
