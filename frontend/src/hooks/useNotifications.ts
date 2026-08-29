import { useEffect, useState, useCallback } from 'react'
import { useAuth } from './useAuth'

export interface Notification {
  id: string
  type: 'agent_alert' | 'sale_celebration' | 'strategy' | 'action_required' | 'milestone' | 'emergency_support'
  title: string
  message: string
  icon?: string
  timestamp: Date
  read: boolean
  platform?: string
  actionUrl?: string
  requiresApproval?: boolean
  priority: 'low' | 'normal' | 'high' | 'critical'
  metadata?: Record<string, any>
}

export interface ActivityItem {
  id: string
  agent: string
  action: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  timestamp: Date
  details: string
  result?: string
}

const NOTIFICATION_TYPES = {
  agent_alert: { color: 'blue', icon: '🤖' },
  sale_celebration: { color: 'green', icon: '🎉' },
  strategy: { color: 'purple', icon: '💡' },
  action_required: { color: 'orange', icon: '⚠️' },
  milestone: { color: 'gold', icon: '⭐' },
  emergency_support: { color: 'red', icon: '🚨' },
}

export function useNotifications() {
  const { user } = useAuth()
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [activities, setActivities] = useState<ActivityItem[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

  // Fetch coaching daily message
  const fetchCoachingMessage = useCallback(async () => {
    if (!user?.id) return null

    try {
      const response = await fetch(
        `${BACKEND_URL}/api/v1/coach/daily-coaching/${user.id}`
      )
      if (!response.ok) return null

      const data = await response.json()
      if (data.status === 'success') {
        return {
          id: `coach-${Date.now()}`,
          type: 'agent_alert' as const,
          title: data.coaching.title,
          message: data.coaching.message,
          icon: '🎯',
          timestamp: new Date(),
          read: false,
          priority: (data.coaching.urgency === 'high' ? 'high' : 'normal') as Notification['priority'],
          metadata: { topic: data.coaching.topic, actionItem: data.coaching.action_item },
        }
      }
    } catch (err) {
      console.error('Error fetching coaching:', err)
    }
    return null
  }, [user?.id, BACKEND_URL])

  // Fetch user analysis for adaptive response
  const fetchUserAnalysis = useCallback(async () => {
    if (!user?.id) return null

    try {
      const response = await fetch(
        `${BACKEND_URL}/api/v1/adaptive/personalization/${user.id}`
      )
      if (!response.ok) return null

      const data = await response.json()
      if (data.status === 'success' && data.personalization) {
        const { segment, primary_need, urgency } = data.personalization

        // Generate recommendation notification
        if (primary_need === 'lead_generation') {
          return {
            id: `strategy-${Date.now()}`,
            type: 'strategy' as const,
            title: '💡 Estrategia Recomendada',
            message: `Los agentes analizaron tu negocio y recomiendan: Generar más leads.`,
            icon: '💡',
            timestamp: new Date(),
            read: false,
            priority: (urgency === 'critical' ? 'critical' : urgency === 'high' ? 'high' : 'normal') as Notification['priority'],
            actionUrl: '/dashboard/lead-generation',
            requiresApproval: false,
            metadata: { segment, need: primary_need },
          }
        }
      }
    } catch (err) {
      console.error('Error fetching user analysis:', err)
    }
    return null
  }, [user?.id, BACKEND_URL])

  // Simulate agent activity
  const generateMockActivities = useCallback((): ActivityItem[] => {
    const agents = [
      { name: 'Lead Scout', action: 'Buscando clientes potenciales' },
      { name: 'Closer Bot', action: 'Analizando propuestas abiertas' },
      { name: 'Coach Agent', action: 'Preparando recomendaciones personalizadas' },
      { name: 'Analytics Engine', action: 'Procesando métricas de desempeño' },
    ]

    return agents.map((agent, i) => ({
      id: `activity-${i}`,
      agent: agent.name,
      action: agent.action,
      status: ['pending', 'in_progress', 'completed'][Math.floor(Math.random() * 3)] as any,
      timestamp: new Date(Date.now() - Math.random() * 3600000),
      details: `${agent.action}...`,
      result: Math.random() > 0.5 ? `Encontrados ${Math.floor(Math.random() * 20)} resultados relevantes` : undefined,
    }))
  }, [])

  // Fetch all notifications
  const fetchNotifications = useCallback(async () => {
    setIsLoading(true)
    try {
      const coachMsg = await fetchCoachingMessage()
      const strategyMsg = await fetchUserAnalysis()

      // Mock notifications for demo (in production, these would come from backend)
      const mockNotifications: Notification[] = [
        ...(coachMsg ? [coachMsg] : []),
        ...(strategyMsg ? [strategyMsg] : []),
      ]

      // Add mock milestone or sale celebration
      if (Math.random() > 0.7) {
        mockNotifications.push({
          id: `celebration-${Date.now()}`,
          type: 'sale_celebration',
          title: '🎉 ¡Felicidades! Nueva venta confirmada',
          message: 'Has concretado 1 venta en Mercado Libre por $50,000',
          icon: '🎉',
          timestamp: new Date(),
          read: false,
          priority: 'high',
          platform: 'Mercado Libre',
          metadata: { amount: 50000, platform: 'Mercado Libre' },
        })
      }

      // Add action required notification
      if (Math.random() > 0.8) {
        mockNotifications.push({
          id: `action-${Date.now()}`,
          type: 'action_required',
          title: '⚠️ Se requiere tu aprobación',
          message: 'El agente de automatización quiere ejecutar una campaña de email. ¿Aprobar?',
          icon: '⚠️',
          timestamp: new Date(),
          read: false,
          priority: 'high',
          actionUrl: '/dashboard/automatizaciones',
          requiresApproval: true,
          metadata: { campaign: 'email_blast', audience: 150 },
        })
      }

      setNotifications(mockNotifications)
      setUnreadCount(mockNotifications.filter(n => !n.read).length)
      setActivities(generateMockActivities())
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error fetching notifications')
    } finally {
      setIsLoading(false)
    }
  }, [fetchCoachingMessage, fetchUserAnalysis, generateMockActivities])

  // Poll for new notifications
  useEffect(() => {
    if (!user?.id) return

    fetchNotifications()
    const interval = setInterval(fetchNotifications, 30000) // Poll every 30 seconds

    return () => clearInterval(interval)
  }, [user?.id, fetchNotifications])

  const markAsRead = useCallback((notificationId: string) => {
    setNotifications((prev) =>
      prev.map((n) =>
        n.id === notificationId ? { ...n, read: true } : n
      )
    )
    setUnreadCount((prev) => Math.max(0, prev - 1))
  }, [])

  const dismissNotification = useCallback((notificationId: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== notificationId))
  }, [])

  const approveAction = useCallback((notificationId: string) => {
    dismissNotification(notificationId)
    // In production, send approval to backend
    console.log('Action approved:', notificationId)
  }, [dismissNotification])

  return {
    notifications,
    activities,
    unreadCount,
    isLoading,
    error,
    markAsRead,
    dismissNotification,
    approveAction,
    NOTIFICATION_TYPES,
  }
}
