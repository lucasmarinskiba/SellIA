import { useEffect } from 'react'
import { Stack } from 'expo-router'
import { useAuth } from '@/hooks/useAuth'
import { offlineSync } from '@/services/offlineSync'
import { pushNotifications } from '@/services/pushNotifications'

export default function App() {
  const { isLoading, isSignedIn, restoreToken } = useAuth()

  useEffect(() => {
    const bootstrap = async () => {
      await offlineSync.init()
      await restoreToken()

      const pushToken = await pushNotifications.initializePushNotifications()
      if (pushToken) {
        console.log('Push token:', pushToken)
      }

      pushNotifications.setupNotificationHandlers()
    }

    bootstrap()
  }, [restoreToken])

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
