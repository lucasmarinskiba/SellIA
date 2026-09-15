'use client'

import { useState, useEffect, useCallback } from 'react'
import { auth, User } from '@/lib/auth'
import { setToken } from '@/lib/sellia-api/client'

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchUser = useCallback(async () => {
    try {
      const userData = await auth.me()
      setUser(userData)
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  const logout = useCallback(async () => {
    try {
      await auth.logout()
    } catch {
      // Silencioso: incluso si falla el backend, limpiamos local
    }
    // Was clearing localStorage key 'token', but login (now on the Bearer
    // system) stores it under 'sellia.token' via setToken() -- logout
    // never actually cleared the real session, so the very next request
    // (or a reload) would silently log the user back in with the stale
    // token still attached by lib/api.ts's interceptor.
    setToken(null)
    setUser(null)
    window.location.href = '/login'
  }, [])

  return { user, loading, logout, refetch: fetchUser }
}
