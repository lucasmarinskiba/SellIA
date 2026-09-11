/**
 * Sales analysis over the account's real orders.
 *
 * Mirrors backend/app/domains/data_science/sales.py. Amounts are per currency —
 * the API never sums across currencies, and neither does the UI.
 */

import { api } from './api'

export type Confidence = 'solid' | 'preliminary' | 'insufficient'

export interface Reading {
  key: string
  title: string
  value: number | string | null
  unit: string
  confidence: Confidence
  /** The number with its denominator and interval, in words. */
  reading: string
  why_it_matters?: string
  direction?: string
}

export interface CurrencyBreakdown {
  currency: string
  orders: number
  revenue: number
  collected: number
  median_ticket: number | null
  q1_ticket: number | null
  q3_ticket: number | null
  is_main: boolean
}

export interface SalesAnalysis {
  period_days: number
  has_data: boolean
  headline: string
  main_currency?: string
  currencies: CurrencyBreakdown[]
  revenue_series: { date: string; revenue: number; orders: number }[]
  ticket_distribution: { from: number; to: number; orders: number }[]
  by_platform: {
    platform: string
    orders: number
    revenue: number
    median_ticket: number | null
    paid_rate: number | null
    confidence: Confidence
    reading: string
  }[]
  by_weekday: { weekday: string; orders: number }[]
  by_hour: { hour: number; orders: number }[]
  status_funnel: { step: string; count: number; of_created: number | null }[]
  lost?: { cancelled: number; refunded: number }
  repeat_customers: {
    identified_customers: number
    returning_customers: number
    orders_without_identity: number
    repeat_rate: number | null
    confidence: Confidence
    reading: string
  } | null
  concentration: {
    customers: number
    top_customers?: number
    top_share: number | null
    currency?: string
    reading: string
  } | null
  readings: Reading[]
  generated_at: string
}

export const salesAnalyticsApi = {
  get: (days = 90): Promise<SalesAnalysis> =>
    api.get<SalesAnalysis>('/data-science/sales', { params: { days } }).then(r => r.data),
}
