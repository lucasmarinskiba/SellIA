'use client'

import { useState, useEffect, useCallback } from 'react'
import { auth, User } from '@/lib/auth'

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
    localStorage.removeItem('token')
    setUser(null)
    window.location.href = '/login'
  }, [])

  return { user, loading, logout, refetch: fetchUser }
}
