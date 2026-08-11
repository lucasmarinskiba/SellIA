import { create } from 'zustand'
import { apiClient } from '@/services/apiClient'

interface Notification {
  id: string
  type: 'approval' | 'deal_update' | 'comment' | 'mention'
  title: string
  message: string
  timestamp: string
  read: boolean
  data: Record<string, unknown>
}

interface NotificationsState {
  notifications: Notification[]
  unreadCount: number
  isLoading: boolean
  fetchNotifications: (userId: string) => Promise<void>
  markAsRead: (notificationId: string) => Promise<void>
  markAllAsRead: (userId: string) => Promise<void>
  clearNotifications: () => void
}

export const useNotificationsStore = create<NotificationsState>((set, get) => ({
  notifications: [],
  unreadCount: 0,
  isLoading: false,

  fetchNotifications: async (userId: string) => {
    set({ isLoading: true })
    try {
      const response = await apiClient.getNotifications(userId, 50)
      const notifications = response.data.notifications || []

      const unreadCount = notifications.filter((n: Notification) => !n.read).length

      set({
        notifications,
        unreadCount,
        isLoading: false,
      })
    } catch (error) {
      console.error('Fetch notifications error:', error)
      set({ isLoading: false })
    }
  },

  markAsRead: async (notificationId: string) => {
    const prevNotifications = get().notifications
    try {
      // Optimistic update
      set({
        notifications: prevNotifications.map((n) =>
          n.id === notificationId ? { ...n, read: true } : n
        ),
        unreadCount: Math.max(0, get().unreadCount - 1),
      })

      await apiClient.markNotificationRead(notificationId)
    } catch (error) {
      // Revert on failure
      set({ notifications: prevNotifications })
      console.error('Mark as read error:', error)
    }
  },

  markAllAsRead: async (userId: string) => {
    const unreadIds = get()
      .notifications.filter((n) => !n.read)
      .map((n) => n.id)

    for (const id of unreadIds) {
      await get().markAsRead(id)
    }
  },

  clearNotifications: () => {
    set({ notifications: [], unreadCount: 0 })
  },
}))

export const useNotifications = () => useNotificationsStore()
