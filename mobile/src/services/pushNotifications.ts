import * as Notifications from 'expo-notifications'
import * as Device from 'expo-device'
import Constants from 'expo-constants'

interface PushToken {
  type: string
  data: string
}

class PushNotificationService {
  async initializePushNotifications(): Promise<string | null> {
    if (!Device.isDevice) {
      console.log('Push notifications are not available on emulator')
      return null
    }

    try {
      const status = await Notifications.requestPermissionsAsync()
      if (status.granted) {
        return await this.getPushToken()
      }
      return null
    } catch (error) {
      console.error('Push notification init error:', error)
      return null
    }
  }

  private async getPushToken(): Promise<string | null> {
    try {
      const projectId = Constants.expoConfig?.extra?.eas?.projectId
      if (!projectId) {
        console.error('Project ID not found')
        return null
      }

      const token = await Notifications.getExpoPushTokenAsync({ projectId })
      return token.data
    } catch (error) {
      console.error('Get push token error:', error)
      return null
    }
  }

  setupNotificationHandlers(): void {
    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
      }),
    })

    const subscription = Notifications.addNotificationResponseReceivedListener((response) => {
      const data = response.notification.request.content.data
      this.handleNotificationPress(data)
    })

    return () => subscription.remove()
  }

  private handleNotificationPress(data: Record<string, unknown>): void {
    if (data.type === 'approval') {
      // Navigate to approvals screen
      console.log('Navigate to approvals:', data.action_id)
    } else if (data.type === 'deal_update') {
      // Navigate to deal detail
      console.log('Navigate to deal:', data.deal_id)
    } else if (data.type === 'comment') {
      // Navigate to collaboration
      console.log('Navigate to deal comments:', data.deal_id)
    }
  }

  async scheduleLocalNotification(
    title: string,
    body: string,
    delay: number = 5000,
    data?: Record<string, unknown>
  ): Promise<void> {
    await Notifications.scheduleNotificationAsync({
      content: {
        title,
        body,
        data: data || {},
      },
      trigger: { seconds: delay / 1000 },
    })
  }

  async sendPushToServer(token: string, userId: string): Promise<void> {
    // Store push token on server for FCM/APNs delivery
    try {
      await fetch('http://localhost:8000/api/v1/notifications/register-device', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          push_token: token,
          device_type: Device.osName,
        }),
      })
    } catch (error) {
      console.error('Register push token error:', error)
    }
  }
}

export const pushNotifications = new PushNotificationService()
