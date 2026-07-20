'use client'

/**
 * Hook · resolve current tenant from subdomain (via middleware cookie · client-side).
 */
import { useEffect, useState } from 'react'

import { api } from './client'

export interface TenantPublic {
  id: string
  name: string
  plan: string
}

function readCookie(name: string): string | null {
  if (typeof document === 'undefined') return null
  const match = document.cookie.match(new RegExp(`(?:^|;\\s*)${name}=([^;]+)`))
  return match ? decodeURIComponent(match[1]) : null
}

export function useTenantSubdomain() {
  const [subdomain, setSubdomain] = useState<string | null>(null)
  const [tenant, setTenant] = useState<TenantPublic | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const sub = readCookie('sellia.tenant')
    if (!sub) return
    setSubdomain(sub)
    setLoading(true)
    api
      .get<TenantPublic>(`/onboarding/by-subdomain/${sub}`)
      .then((r) => setTenant(r.data))
      .catch((e) => setError(e?.response?.data?.detail || 'Tenant lookup failed'))
      .finally(() => setLoading(false))
  }, [])

  return { subdomain, tenant, loading, error }
}
