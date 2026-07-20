import { CUSessionStatus } from '@/hooks/useComputerUseWebSocket'

export interface BrainNode {
  id: string
  name: string
  icon: string
  status: 'active' | 'idle' | 'warning' | 'error'
  color: string
  connections: string[]
  metric?: string
}

export interface PendingAction {
  id: string
  action: string
  reason: string
  confidence: number
  impact: number
  type: 'discount' | 'upgrade' | 'refund' | 'general'
  icon?: string
}

export interface CUSessionMini {
  id: string
  task: string
  browser: string
  steps: number
  status: CUSessionStatus
  url?: string
  color?: string
}
