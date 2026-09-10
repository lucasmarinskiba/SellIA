/**
 * Vendedor Multiplataforma client.
 *
 * Mirrors backend/app/domains/platform_commerce/. Two things to keep in mind
 * when rendering this:
 *
 * - `capabilities` is derived from the real connector classes, so a platform
 *   that cannot import orders says so instead of showing an empty sales figure
 *   that reads as "no vendiste nada".
 * - `margin` is null whenever a cost component was never declared. That is not
 *   a loading state: it means the margin genuinely cannot be computed yet, and
 *   `missing` lists what the seller has to declare for it to exist.
 */

import { api } from './api'

export interface PlatformCapability {
  key: string
  label: string
  detail: string
  available: boolean
}

export interface PlatformAction {
  key: string
  label: string
  detail: string
  available: boolean
  touches_customers: boolean
}

export interface PlatformCosts {
  envios: number | null
  comision: number | null
  cargo_fijo_por_venta: number | null
  costo_de_producto: number | null
  costos_fijos: number | null
  publicidad: number | null
}

export interface PlatformSettings {
  commission_percent: number | null
  fixed_fee_per_order: number | null
  cogs_percent: number | null
  monthly_fixed_cost: number | null
  monthly_ad_spend: number | null
}

export interface PlatformRow {
  platform: string
  orders: number
  orders_total: number
  revenue: number
  costs: PlatformCosts
  known_costs: number
  margin: number | null
  margin_percent: number | null
  margin_complete: boolean
  missing: string[]
  currency: string | null
  connection: {
    connected: boolean
    status: string
    status_message: string | null
    last_sync_at: string | null
  } | null
  capabilities: PlatformCapability[]
  actions: PlatformAction[]
  settings: PlatformSettings | null
}

export interface Consolidated {
  revenue: number
  orders: number
  known_costs: number
  margin: number | null
  margin_complete: boolean
  currency: string | null
  mixed_currencies?: boolean
  note?: string
}

export interface CommerceOverview {
  period_days: number
  platforms: PlatformRow[]
  consolidated: Consolidated
  has_business: boolean
  generated_at: string
}

export interface SyncResult {
  platform: string
  supported: boolean
  ok?: boolean
  reason?: string
  imported: number
  updated: number
  skipped?: number
  fetched?: number
}

export const commerceApi = {
  overview: (days = 30): Promise<CommerceOverview> =>
    api.get<CommerceOverview>(`/platform-commerce/overview?days=${days}`).then(r => r.data),

  saveSettings: (platform: string, body: Partial<PlatformSettings>): Promise<{ saved: boolean }> =>
    api.put(`/platform-commerce/settings/${platform}`, body).then(r => r.data),

  sync: (): Promise<{ results: SyncResult[]; imported: number; updated: number }> =>
    api.post('/platform-commerce/sync').then(r => r.data),

  runAction: (platform: string, action: string): Promise<{ detail?: string }> =>
    api.post(`/platform-commerce/${platform}/actions/${action}`).then(r => r.data),
}

export const formatMoney = (amount: number, currency: string | null): string =>
  new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: currency || 'ARS',
    maximumFractionDigits: 0,
  }).format(amount)

export const COST_LABEL: Record<keyof PlatformCosts, string> = {
  comision: 'Comisión de la plataforma',
  cargo_fijo_por_venta: 'Cargo fijo por venta',
  costo_de_producto: 'Costo de producto',
  envios: 'Envíos',
  costos_fijos: 'Costos fijos',
  publicidad: 'Publicidad',
}
