import { Stack } from 'expo-router'
import { useAuth } from '@/hooks/useAuth'
import { useEffect } from 'react'

export default function RootLayout() {
  const { isLoading, isSignedIn, restoreToken } = useAuth()

  useEffect(() => {
    restoreToken()
  }, [])

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
