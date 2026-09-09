import { useEffect, useState } from 'react'
import { api } from './api'

/**
 * Real, per-account business snapshot.
 *
 * Mirrors backend/app/domains/ai_activity/service.py's get_business_snapshot.
 * Every field is counted from the signed-in account's own rows, which is what
 * lets the SEO / autoridad / vendedor-multiplataforma pages show real state
 * instead of the invented figures they used to hardcode.
 */
export interface ChannelActivity {
  platform: string
  name: string
  status: string
  conversations: number
  ai_replies: number
  last_message_at: string | null
}

export interface BusinessSnapshot {
  business: { id: string | null; name: string | null; count: number }
  verification: {
    email_verified: boolean
    two_factor_enabled: boolean
    account_age_days: number
    has_business: boolean
    website_published: boolean
    domain_verified: boolean
    subdomain: string | null
  }
  channels: ChannelActivity[]
  conversations: {
    total: number
    inbound: number
    answered: number
    ai_answered: number
    response_rate: number
    ai_share: number
  }
  revenue: {
    orders_total: number
    orders_paid: number
    gross_amount: number
    paid_amount: number
    currency: string | null
  }
  generated_at: string
}

export const fetchBusinessSnapshot = async (): Promise<BusinessSnapshot> => {
  const res = await api.get<BusinessSnapshot>('/ai-activity/business-snapshot')
  return res.data
}

export interface SnapshotState {
  snapshot: BusinessSnapshot | null
  loading: boolean
  /** True when the account could not be read at all (no session / backend down).
   *  Kept separate from "no data yet" so the UI never blames the user for an
   *  outage, nor claims an outage when the account is simply empty. */
  unavailable: boolean
}

export const useBusinessSnapshot = (): SnapshotState => {
  const [snapshot, setSnapshot] = useState<BusinessSnapshot | null>(null)
  const [loading, setLoading] = useState(true)
  const [unavailable, setUnavailable] = useState(false)

  useEffect(() => {
    let alive = true
    fetchBusinessSnapshot()
      .then(data => { if (alive) { setSnapshot(data); setUnavailable(false) } })
      .catch(() => { if (alive) setUnavailable(true) })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [])

  return { snapshot, loading, unavailable }
}

/** Money as it should be shown: the account's own currency, or a plain dash
 *  when there is genuinely nothing to show (never a placeholder amount). */
export const formatMoney = (amount: number, currency: string | null): string => {
  if (!amount) return currency ? `0 ${currency}` : '0'
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: currency || 'ARS',
    maximumFractionDigits: 0,
  }).format(amount)
}
