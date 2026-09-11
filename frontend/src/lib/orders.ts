import { api } from './api'

export interface OrderItem {
  name: string
  sku?: string
  quantity: number
  unit_price: number
  total_price: number
}

export interface Order {
  id: string
  business_id: string
  conversation_id: string | null
  deal_id: string | null
  order_number: string | null
  items: OrderItem[]
  total_amount: number
  subtotal: number | null
  tax_amount: number | null
  discount_amount: number | null
  shipping_cost: number | null
  currency: string
  status: string
  payment_method: string | null
  payment_status: string
  paid_at: string | null
  shipped_at: string | null
  delivered_at: string | null
  tracking_number: string | null
  shipping_provider: string | null
  customer_name: string | null
  customer_email: string | null
  customer_phone: string | null
  external_platform: string | null
  source_channel: string | null
  source_workflow_id: string | null
  source_agent_id: string | null
  first_touch_channel: string | null
  last_touch_channel: string | null
  attribution_model: string
  notes: string | null
  created_at: string
  updated_at: string
}

export interface RevenueSummary {
  period_days: number
  total_revenue: number
  total_orders: number
  avg_order_value: number
  paid_orders: number
  pending_orders: number
  refunded_amount: number
  revenue_by_channel: Record<string, number>
  revenue_by_platform: Record<string, number>
  orders_by_status: Record<string, number>
  revenue_trend: { date: string; revenue: number; orders: number }[]
}

export interface AttributionSummary {
  total_revenue: number
  total_orders: number
  by_channel: { channel: string; revenue: number; orders: number }[]
  by_workflow: { workflow_id: string | null; revenue: number; orders: number }[]
  by_agent: { agent_id: string | null; revenue: number; orders: number }[]
  first_touch_revenue: Record<string, number>
  last_touch_revenue: Record<string, number>
}

/** One row of the spreadsheet. Customer fields arrive masked, as everywhere else. */
export interface OrderRow {
  id: string
  order_number: string
  created_at: string | null
  customer_name: string | null
  customer_email: string | null
  customer_phone: string | null
  items_count: number
  units: number
  items_label: string
  total_amount: number
  currency: string
  status: string | null
  payment_status: string | null
  payment_method: string | null
  external_platform: string
  source_channel: string
  source_campaign: string | null
  tracking_number: string | null
  shipping_provider: string | null
  paid_at: string | null
  shipped_at: string | null
  delivered_at: string | null
  age_days: number | null
  hours_to_payment: number | null
  notes: string | null
}

export interface CurrencyTotal {
  currency: string
  orders: number
  revenue: number
  paid_revenue: number
  avg_order: number
}

export interface Facet {
  value: string
  count: number
}

export interface OrdersTable {
  rows: OrderRow[]
  total: number
  page: number
  page_size: number
  pages: number
  sort_by: string
  sort_dir: 'asc' | 'desc'
  /** Per currency — never summed across them. */
  totals: CurrencyTotal[]
  facets: Record<string, Facet[]>
  /** What the backend could not do, said out loud (e.g. a capped search). */
  notes: string[]
  columns: { key: string; label: string; sortable: boolean }[]
  transitions: Record<string, string[]>
  generated_at: string
}

export interface OrdersTableParams {
  search?: string
  status_in?: string
  payment_status?: string
  platform?: string
  channel?: string
  currency?: string
  date_from?: string
  date_to?: string
  amount_min?: number
  amount_max?: number
  has_tracking?: boolean
  sort_by?: string
  sort_dir?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

export interface BulkStatusResult {
  requested: number
  updated: number
  skipped: number
  status: string
  results: { order_id: string; changed: boolean; reason: string | null }[]
}

export const ordersApi = {
  getTable: (businessId: string, params: OrdersTableParams): Promise<OrdersTable> =>
    api.get<OrdersTable>('/orders/table', { params: { business_id: businessId, ...params } })
      .then(r => r.data),

  bulkStatus: (orderIds: string[], status: string): Promise<BulkStatusResult> =>
    api.post<BulkStatusResult>('/orders/bulk-status', { order_ids: orderIds, status })
      .then(r => r.data),

  /**
   * Downloads the filtered sheet as CSV.
   *
   * Goes through the axios client rather than a plain <a href>: accounts that
   * log in via /sellia-login hold a Bearer token in localStorage and no cookie,
   * so a top-level navigation to the endpoint would arrive unauthenticated.
   */
  downloadCsv: async (businessId: string, params: OrdersTableParams): Promise<void> => {
    const response = await api.get('/orders/export.csv', {
      params: { business_id: businessId, ...params },
      responseType: 'blob',
    })
    const url = window.URL.createObjectURL(new Blob([response.data], { type: 'text/csv;charset=utf-8;' }))
    const link = document.createElement('a')
    link.href = url
    link.download = `ordenes-${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },

  getOrders: (businessId: string, params?: { status?: string; search?: string }) =>
    api.get<Order[]>('/orders', { params: { business_id: businessId, ...params } }).then(r => r.data),

  createOrder: (data: Omit<Order, 'id' | 'created_at' | 'updated_at' | 'paid_at' | 'shipped_at' | 'delivered_at' | 'source_channel' | 'source_campaign' | 'source_workflow_id' | 'source_agent_id' | 'first_touch_channel' | 'last_touch_channel' | 'attribution_model'>) =>
    api.post<Order>('/orders', data).then(r => r.data),

  updateOrder: (id: string, data: Partial<Order>) =>
    api.patch<Order>(`/orders/${id}`, data).then(r => r.data),

  deleteOrder: (id: string) =>
    api.delete(`/orders/${id}`).then(r => r.data),

  getRevenueSummary: (businessId: string, days = 30) =>
    api.get<RevenueSummary>('/orders/revenue/summary', { params: { business_id: businessId, days } }).then(r => r.data),

  getAttribution: (businessId: string, days = 30) =>
    api.get<AttributionSummary>('/orders/revenue/attribution', { params: { business_id: businessId, days } }).then(r => r.data),
}
