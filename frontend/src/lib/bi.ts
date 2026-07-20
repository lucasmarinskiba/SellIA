import { api } from './api'

export interface FunnelMetrics {
  id: string
  business_id: string
  period: string
  period_type: string
  leads_count: number
  qualified_count: number
  deals_count: number
  orders_count: number
  repeat_orders_count: number
  conversion_lead_to_qualified: number
  conversion_qualified_to_deal: number
  conversion_deal_to_order: number
  conversion_order_to_repeat: number
  revenue_total: number
  avg_order_value: number
  created_at: string
}

export interface InsightAlert {
  id: string
  business_id: string
  insight_type: string
  severity: string
  title: string
  description: string | null
  metric_name: string | null
  metric_change_percent: number | null
  recommended_action: string | null
  action_taken: boolean
  action_result: string | null
  is_active: boolean
  created_at: string
}

export const biApi = {
  generateFunnel: (businessId: string, period: string, period_type?: string) =>
    api.post<FunnelMetrics>(`/businesses/${businessId}/bi/funnel`, null, { params: { period, period_type } }).then(r => r.data),

  getLatestFunnel: (businessId: string) =>
    api.get<FunnelMetrics | null>(`/businesses/${businessId}/bi/funnel/latest`).then(r => r.data),

  getInsights: (businessId: string, insight_type?: string) =>
    api.get<InsightAlert[]>(`/businesses/${businessId}/bi/insights`, { params: { insight_type } }).then(r => r.data),
}
