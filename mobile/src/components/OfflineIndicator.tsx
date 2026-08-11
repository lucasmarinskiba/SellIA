import { View, Text, StyleSheet, Animated, Easing } from 'react-native'
import { useSyncMonitor } from '@/hooks/useSyncMonitor'
import { useEffect, useRef } from 'react'

export default function OfflineIndicator() {
  const { isOnline, isSyncing, pendingCount, error } = useSyncMonitor()
  const slideAnim = useRef(new Animated.Value(0)).current
  const spinAnim = useRef(new Animated.Value(0)).current

  useEffect(() => {
    if (isSyncing) {
      Animated.loop(
        Animated.timing(spinAnim, {
          toValue: 1,
          duration: 1000,
          easing: Easing.linear,
          useNativeDriver: true,
        })
      ).start()
    }
  }, [isSyncing])

  // Show banner if offline or error
  if (isOnline && !error && !isSyncing) {
    return null
  }

  const backgroundColor = error ? '#f44336' : isOnline ? '#FF8C00' : '#2196F3'
  const message = error
    ? `Sync failed: ${error}`
    : isSyncing
      ? `Syncing... (${pendingCount} pending)`
      : `Offline mode (${pendingCount} pending)`

  const rotation = spinAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  })

  return (
    <Animated.View style={[styles.banner, { backgroundColor }]}>
      <View style={styles.content}>
        <Text style={styles.indicator}>●</Text>
        <Text style={styles.message}>{message}</Text>
        {isSyncing && (
          <Animated.Text style={[styles.spinner, { transform: [{ rotate: rotation }] }]}>
            ⟳
          </Animated.Text>
        )}
      </View>
    </Animated.View>
  )
}

const styles = StyleSheet.create({
  banner: {
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  indicator: {
    color: '#fff',
    fontSize: 8,
  },
  message: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '500',
    flex: 1,
  },
  spinner: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
})
