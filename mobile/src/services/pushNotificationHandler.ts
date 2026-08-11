import * as Notifications from 'expo-notifications'
import { createDeepLink } from './deepLinking'
import { offlineSync } from './offlineSync'

interface NotificationPayload {
  type: 'approval' | 'deal_update' | 'comment' | 'mention'
  title: string
  body: string
  data: {
    id: string
    action_id?: string
    deal_id?: string
    user_id?: string
    [key: string]: unknown
  }
}

interface PushTokenRegistration {
  user_id: string
  push_token: string
  device_type: 'ios' | 'android'
  device_id: string
}

class PushNotificationHandler {
  private notificationListeners: Array<(notification: NotificationPayload) => void> = []

  subscribe(callback: (notification: NotificationPayload) => void): () => void {
    this.notificationListeners.push(callback)
    return () => {
      this.notificationListeners = this.notificationListeners.filter((cb) => cb !== callback)
    }
  }

  setupHandlers(): void {
    Notifications.setNotificationHandler({
      handleNotification: async (notification) => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
      }),
    })

    this.setupResponseHandler()
    this.setupReceivedHandler()
  }

  private setupResponseHandler(): void {
    Notifications.addNotificationResponseReceivedListener((response) => {
      const { notification } = response
      const payload = this.parseNotificationData(notification.request.content.data)

      if (payload) {
        this.handleNotificationPress(payload)
        this.notificationListeners.forEach((cb) => cb(payload))
      }
    })
  }

  private setupReceivedHandler(): void {
    Notifications.addNotificationReceivedListener((notification) => {
      const payload = this.parseNotificationData(notification.request.content.data)
      if (payload) {
        this.cacheNotification(payload)
      }
    })
  }

  private parseNotificationData(data: Record<string, unknown>): NotificationPayload | null {
    try {
      if (
        !data.type ||
        !data.title ||
        !data.body ||
        !data.data
      ) {
        return null
      }

      return {
        type: data.type as NotificationPayload['type'],
        title: data.title as string,
        body: data.body as string,
        data: typeof data.data === 'string' ? JSON.parse(data.data) : (data.data as NotificationPayload['data']),
      }
    } catch (error) {
      console.error('Parse notification error:', error)
      return null
    }
  }

  private handleNotificationPress(payload: NotificationPayload): void {
    const deepLink = createDeepLink({
      type: payload.type,
      id: payload.data.id,
      data: payload.data,
    })

    console.log('Deep link:', deepLink)
  }

  private cacheNotification(payload: NotificationPayload): void {
    if (payload.type === 'approval' && payload.data.action_id) {
      offlineSync.queueAction('create', 'notification_approval', payload.data.id, {
        action_id: payload.data.action_id,
        title: payload.title,
        body: payload.body,
      })
    } else if (payload.type === 'deal_update' && payload.data.deal_id) {
      offlineSync.queueAction('create', 'notification_deal', payload.data.id, {
        deal_id: payload.data.deal_id,
        title: payload.title,
        body: payload.body,
      })
    }
  }

  async registerDeviceToken(registration: PushTokenRegistration): Promise<void> {
    try {
      await offlineSync.queueAction('create', 'push_token_registration', registration.user_id, {
        push_token: registration.push_token,
        device_type: registration.device_type,
        device_id: registration.device_id,
      })

      // Try immediate sync
      await fetch('http://localhost:8000/api/v1/notifications/register-device', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(registration),
      })
    } catch (error) {
      console.error('Register device token error:', error)
    }
  }

  async scheduleTestNotification(
    title: string,
    body: string,
    delay: number = 5
  ): Promise<void> {
    await Notifications.scheduleNotificationAsync({
      content: {
        title,
        body,
        badge: 1,
        priority: 'high',
        data: {
          type: 'approval',
          title,
          body,
          data: JSON.stringify({ id: 'test_notification', action_id: 'test_action' }),
        },
      },
      trigger: { seconds: delay },
    })
  }
}

export const pushNotificationHandler = new PushNotificationHandler()
