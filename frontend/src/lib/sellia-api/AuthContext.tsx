'use client'

/**
 * AuthContext · provides current user + tenant + role globally.
 *
 * Wraps app in <QueryProvider> → <AuthProvider>.
 * Children read state via useAuth().
 */
import { createContext, useContext, useMemo, type ReactNode } from 'react'

import { getToken, type MeResponse } from './client'
import { useMe, useLogout } from './queries'

interface AuthCtx {
  user: MeResponse | null
  isAuthenticated: boolean
  isLoading: boolean
  logout: () => void
}

const Ctx = createContext<AuthCtx | null>(null)

export function SellIAAuthProvider({ children }: { children: ReactNode }) {
  const hasToken = typeof window !== 'undefined' && !!getToken()
  const meQuery = useMe({ enabled: hasToken })
  const logout = useLogout()

  const value = useMemo<AuthCtx>(
    () => ({
      user: meQuery.data || null,
      isAuthenticated: !!meQuery.data,
      isLoading: hasToken && meQuery.isLoading,
      logout,
    }),
    [meQuery.data, meQuery.isLoading, hasToken, logout]
  )

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useSellIAAuth(): AuthCtx {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useSellIAAuth must be used within SellIAAuthProvider')
  return ctx
}
