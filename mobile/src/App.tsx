import { useEffect } from 'react'
import { Stack } from 'expo-router'
import { useAuth } from '@/hooks/useAuth'
import { offlineSync } from '@/services/offlineSync'
import { pushNotifications } from '@/services/pushNotifications'
import { pushNotificationHandler } from '@/services/pushNotificationHandler'
import { useDeepLinking } from '@/services/deepLinking'
import * as Device from 'expo-device'

export default function App() {
  const { isLoading, isSignedIn, restoreToken, user } = useAuth()

  useDeepLinking()

  useEffect(() => {
    const bootstrap = async () => {
      await offlineSync.init()
      await restoreToken()

      if (Device.isDevice) {
        const pushToken = await pushNotifications.initializePushNotifications()
        if (pushToken && user) {
          await pushNotificationHandler.registerDeviceToken({
            user_id: user.id,
            push_token: pushToken,
            device_type: Device.osName === 'iOS' ? 'ios' : 'android',
            device_id: Device.deviceId || 'unknown',
          })
        }
      }

      pushNotifications.setupNotificationHandlers()
      pushNotificationHandler.setupHandlers()
    }

    bootstrap()
  }, [restoreToken, user])

  if (isLoading) {
    return null
  }

  return (
    <Stack screenOptions={{ headerShown: false }}>
      {isSignedIn ? (
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      ) : (
        <Stack.Screen name="(auth)" options={{ headerShown: false }} />
      )}
    </Stack>
  )
}
