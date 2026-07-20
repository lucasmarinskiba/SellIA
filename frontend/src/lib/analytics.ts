import { api } from './api'

export interface AnalyticsData {
  period_days: number
  conversations_by_channel: Record<string, number>
  messages: Record<string, number>
  workflows: {
    active_count: number
    executions_by_status: Record<string, number>
    executions_trend: { date: string; count: number }[]
  }
  agents: {
    conversations: number
    total_tokens: number
  }
  conversations_trend: { date: string; count: number }[]
  top_chatbot_rules: { name: string; usage: number }[]
  insights: string | null
  kpi: {
    total_revenue: number
    total_orders: number
    total_conversations: number
    total_messages: number
    total_workflow_executions: number
    conversion_rate: number
    avg_order_value: number
    trends: {
      revenue: string
      orders: string
      conversations: string
      messages: string
      executions: string
    }
  }
}

export interface FunnelData {
  period_days: number
  funnel: {
    leads: number
    qualified: number
    proposals: number
    closed_won: number
    orders: number
    revenue: number
  }
  conversion_rates: {
    lead_to_qualified: number
    qualified_to_proposal: number
    proposal_to_closed: number
    lead_to_order: number
    overall_conversion: number
  }
  trend: { date: string; leads: number; orders: number; revenue: number }[]
}

export interface AttributionData {
  period_days: number
  total_revenue: number
  total_orders: number
  by_channel: { channel: string; revenue: number; orders: number }[]
  by_workflow: { workflow_id: string | null; revenue: number; orders: number }[]
  by_agent: { agent_id: string | null; revenue: number; orders: number }[]
  first_touch: { channel: string; revenue: number; orders: number }[]
  last_touch: { channel: string; revenue: number; orders: number }[]
  trend: Record<string, any>[]
}

export const analyticsApi = {
  getAnalytics: (businessId: string, days = 30) =>
    api.get<AnalyticsData>('/automations/analytics', { params: { business_id: businessId, days } }).then(r => r.data),

  getFunnel: (businessId: string, days = 30) =>
    api.get<FunnelData>('/automations/analytics/funnel', { params: { business_id: businessId, days } }).then(r => r.data),

  getAttribution: (businessId: string, days = 30) =>
    api.get<AttributionData>('/automations/analytics/attribution', { params: { business_id: businessId, days } }).then(r => r.data),
}
