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

export const ordersApi = {
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
