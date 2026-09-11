/**
 * Qué hacer ahora, qué funciona, y a quién responder primero.
 *
 * Mirrors backend/app/domains/next_steps/. Replaces the three pages whose
 * backends did not exist (Misiones, Leaderboard, Radar). Amounts come grouped by
 * currency and are never summed across them.
 */

import { api } from './api'

export type Urgency = 'alta' | 'media' | 'baja'

export interface NextAction {
  key: string
  title: string
  /** The fact with its numbers. Never a prediction. */
  evidence: string
  why: string
  urgency: Urgency
  /** Dashboard route where the action is carried out. */
  where: string
  size: number
  extra: Record<string, unknown>
}

export interface NextStepsResponse {
  actions: NextAction[]
  /** Checks that ran. */
  checked: string[]
  /** Checks that could not run — an empty action list is not proof of health. */
  not_checked: string[]
  generated_at: string
}

export interface RankedProduct {
  name: string
  units: number
  orders: number
  revenue: Record<string, number>
}

export interface RankedCustomer {
  label: string
  orders: number
  revenue: Record<string, number>
  last_purchase: string | null
  days_since: number | null
}

export interface RankedPlatform {
  platform: string
  orders: number
  paid: number
  revenue: Record<string, number>
}

export interface RankingResponse {
  period_days: number
  has_data: boolean
  enough_data: boolean
  orders_counted: number
  note: string | null
  orders_without_named_items?: number
  products: RankedProduct[]
  customers: RankedCustomer[]
  platforms: RankedPlatform[]
  generated_at: string
}

export interface QueueItem {
  conversation_id: string
  platform: string
  who: string
  last_message: string
  waiting_hours: number
  asked_to_buy: boolean
  is_customer: boolean
  spent: Record<string, number>
  awaiting_human: boolean
  /** Why this conversation sits where it sits. */
  reasons: string[]
}

export interface QueueResponse {
  items: QueueItem[]
  waiting: number
  criteria?: string
  generated_at: string
}

export const nextStepsApi = {
  actions: (): Promise<NextStepsResponse> =>
    api.get<NextStepsResponse>('/next-steps').then(r => r.data),

  ranking: (days = 90): Promise<RankingResponse> =>
    api.get<RankingResponse>('/next-steps/ranking', { params: { days } }).then(r => r.data),

  queue: (limit = 25): Promise<QueueResponse> =>
    api.get<QueueResponse>('/next-steps/queue', { params: { limit } }).then(r => r.data),
}

/** Per-currency amounts, written out without ever adding them together. */
export const formatAmounts = (amounts: Record<string, number>): string =>
  Object.entries(amounts)
    .map(([currency, value]) => `${value.toLocaleString('es-AR', { maximumFractionDigits: 0 })} ${currency}`)
    .join(' · ') || '—'
