/**
 * Computer Use — WebSocket Client
 * Cliente WebSocket para la comunicación bidireccional con el backend
 * de Computer Use Agents (Caja de Cristal).
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export interface ComputerUseSession {
  id: string
  user_id: string
  business_id?: string
  task_description: string
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'stopped'
  current_url?: string
  total_steps: number
  created_at: string
}

export interface ComputerUseStep {
  id: string
  session_id: string
  step_number: number
  action_type: string
  action_params: Record<string, any>
  reason?: string
  execution_result?: string
  created_at: string
}

export type WSMessageType =
  | { type: 'screenshot'; data: { image_base64: string; step: number; url: string } }
  | { type: 'action'; data: { action_type: string; params: Record<string, any>; reason: string; step: number } }
  | { type: 'status'; data: { status: string; message: string; step: number; total_steps: number } }
  | { type: 'chat'; data: { role: string; content: string } }
  | { type: 'error'; data: { message: string } }
  | { type: 'completed'; data: { result: string; total_steps: number } }

export type WSControlAction = 'pause' | 'resume' | 'stop'

export class ComputerUseClient {
  private ws: WebSocket | null = null
  private sessionId: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 3
  private reconnectDelay = 2000

  // Event handlers
  onScreenshot: ((imageBase64: string, step: number, url: string) => void) | null = null
  onAction: ((action: WSMessageType & { type: 'action' }) => void) | null = null
  onStatus: ((status: string, message: string, step: number, totalSteps: number) => void) | null = null
  onChat: ((role: string, content: string) => void) | null = null
  onError: ((message: string) => void) | null = null
  onCompleted: ((result: string, totalSteps: number) => void) | null = null
  onConnect: (() => void) | null = null
  onDisconnect: (() => void) | null = null

  constructor(sessionId: string) {
    this.sessionId = sessionId
  }

  connect(): void {
    const token = typeof window !== 'undefined' ? (localStorage.getItem('token') || localStorage.getItem('access_token')) : null
    const wsUrl = API_URL.replace(/^http/, 'ws')
    const url = token
      ? `${wsUrl}/api/v1/ws/computer-use/${this.sessionId}?token=${encodeURIComponent(token)}`
      : `${wsUrl}/api/v1/ws/computer-use/${this.sessionId}`

    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      this.reconnectAttempts = 0
      this.onConnect?.()
    }

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as WSMessageType
        this._handleMessage(msg)
      } catch {
        // Ignore malformed messages
      }
    }

    this.ws.onerror = (err) => {
      console.error('Computer Use WS error:', err)
      this.onError?.('Error de conexión WebSocket')
    }

    this.ws.onclose = () => {
      this.onDisconnect?.()
      this._attemptReconnect()
    }
  }

  private _handleMessage(msg: WSMessageType): void {
    switch (msg.type) {
      case 'screenshot':
        this.onScreenshot?.(msg.data.image_base64, msg.data.step, msg.data.url)
        break
      case 'action':
        this.onAction?.(msg)
        break
      case 'status':
        this.onStatus?.(msg.data.status, msg.data.message, msg.data.step, msg.data.total_steps)
        break
      case 'chat':
        this.onChat?.(msg.data.role, msg.data.content)
        break
      case 'error':
        this.onError?.(msg.data.message)
        break
      case 'completed':
        this.onCompleted?.(msg.data.result, msg.data.total_steps)
        break
    }
  }

  private _attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      setTimeout(() => {
        this.connect()
      }, this.reconnectDelay * this.reconnectAttempts)
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.onclose = null
      this.ws.close()
      this.ws = null
    }
  }

  pause(): void {
    this._sendControl('pause')
  }

  resume(): void {
    this._sendControl('resume')
  }

  stop(): void {
    this._sendControl('stop')
  }

  sendMessage(message: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'chat', message }))
    }
  }

  private _sendControl(action: WSControlAction): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'control', action }))
    }
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}
