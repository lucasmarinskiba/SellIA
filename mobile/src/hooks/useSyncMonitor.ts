import { useEffect, useState, useCallback } from 'react'
import NetInfo from '@react-native-community/netinfo'
import { offlineSync } from '@/services/offlineSync'

interface SyncStatus {
  isOnline: boolean
  isSyncing: boolean
  pendingCount: number
  lastSyncTime: string | null
  lastSyncResult: { success: number; failed: number } | null
  error: string | null
}

export const useSyncMonitor = () => {
  const [status, setStatus] = useState<SyncStatus>({
    isOnline: true,
    isSyncing: false,
    pendingCount: 0,
    lastSyncTime: null,
    lastSyncResult: null,
    error: null,
  })

  const performSync = useCallback(async () => {
    if (status.isSyncing) return

    setStatus((prev) => ({ ...prev, isSyncing: true, error: null }))

    try {
      const result = await offlineSync.syncQueue()
      setStatus((prev) => ({
        ...prev,
        isSyncing: false,
        lastSyncTime: new Date().toISOString(),
        lastSyncResult: result,
        pendingCount: Math.max(0, prev.pendingCount - (result.success + result.failed)),
      }))
    } catch (error) {
      setStatus((prev) => ({
        ...prev,
        isSyncing: false,
        error: error instanceof Error ? error.message : 'Sync failed',
      }))
    }
  }, [status.isSyncing])

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state) => {
      setStatus((prev) => ({
        ...prev,
        isOnline: state.isConnected ?? false,
      }))

      if (state.isConnected) {
        performSync()
      }
    })

    // Initial check
    NetInfo.fetch().then((state) => {
      setStatus((prev) => ({
        ...prev,
        isOnline: state.isConnected ?? false,
      }))
    })

    return () => unsubscribe()
  }, [performSync])

  // Periodic sync every 30 seconds if online
  useEffect(() => {
    if (!status.isOnline) return

    const interval = setInterval(() => {
      performSync()
    }, 30000)

    return () => clearInterval(interval)
  }, [status.isOnline, performSync])

  return {
    ...status,
    sync: performSync,
  }
}
