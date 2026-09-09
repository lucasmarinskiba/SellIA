'use client'

/**
 * AuthContext · provides current user + tenant + role globally.
 *
 * Wraps app in <QueryProvider> → <AuthProvider>.
 * Children read state via useAuth().
 */
import { createContext, useContext, useEffect, useMemo, type ReactNode } from 'react'

import { getToken, setSessionCookie, type MeResponse } from './client'
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

  // Covers sessions that started before the middleware-visible session
  // cookie existed, or a token set by another tab -- setToken() keeps it in
  // sync going forward, this just corrects it once on mount so a stale
  // "no cookie yet" state doesn't bounce an otherwise-valid session to
  // /login the next time middleware.ts checks a /dashboard/* navigation.
  useEffect(() => {
    setSessionCookie(hasToken)
  }, [hasToken])

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

