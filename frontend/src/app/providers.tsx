'use client'

import { createContext, useContext, useState, ReactNode, useCallback } from 'react'
import { Toast } from '@/components/Toast'

export type NotificationType = 'success' | 'error' | 'warning' | 'info'

export interface Notification {
  id: string
  message: string
  type: NotificationType
  duration?: number
}

interface NotificationContextType {
  notifications: Notification[]
  notify: (message: string, type?: NotificationType, duration?: number) => void
  dismiss: (id: string) => void
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([])

  const notify = useCallback((message: string, type: NotificationType = 'info', duration = 3000) => {
    const id = Math.random().toString(36).substr(2, 9)
    const notification: Notification = { id, message, type, duration }

    setNotifications((prev) => [...prev, notification])

    if (duration > 0) {
      setTimeout(() => dismiss(id), duration)
    }
  }, [])

  const dismiss = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))
  }, [])

  return (
    <NotificationContext.Provider value={{ notifications, notify, dismiss }}>
      {children}
      <div className="fixed bottom-4 right-4 space-y-2 z-50">
        {notifications.map((notif) => (
          <Toast key={notif.id} notification={notif} onDismiss={dismiss} />
        ))}
      </div>
    </NotificationContext.Provider>
  )
}

export function useNotification() {
  const context = useContext(NotificationContext)
  if (!context) {
    throw new Error('useNotification must be used within NotificationProvider')
  }
  return context
}
