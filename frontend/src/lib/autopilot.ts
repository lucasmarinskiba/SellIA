import { api } from './api'

export interface AutopilotConfig {
  id: string
  business_id: string
  auto_qualify_leads: boolean
  auto_move_deals: boolean
  auto_send_followups: boolean
  auto_close_deals: boolean
  auto_create_orders: boolean
  auto_request_reviews: boolean
  auto_activate_recovery_workflows: boolean
  auto_escalate_to_human: boolean
  approval_threshold_amount: number
  max_daily_auto_messages: number
  max_daily_auto_closes: number
  max_daily_auto_orders: number
  human_escalation_channels: string[]
  escalation_email: string | null
  escalation_whatsapp: string | null
  is_active: boolean
  is_paused: boolean
  paused_reason: string | null
  paused_at: string | null
  require_ai_explanation: boolean
  explanation_language: string
  created_at: string
  updated_at: string
}

export interface AutopilotActionLog {
  id: string
  business_id: string
  action_type: string
  entity_type: string
  entity_id: string
  reason: string
  ai_explanation: string | null
  confidence_score: number
  context_data: Record<string, any>
  status: string
  error_message: string | null
  requires_approval: boolean
  approved_at: string | null
  approved_by_user_id: string | null
  rejected_at: string | null
  rejected_reason: string | null
  revenue_impact: number | null
  created_at: string
  executed_at: string | null
}

export interface AutopilotDailyReport {
  id: string
  business_id: string
  report_date: string
  leads_contacted: number
  deals_moved: number
  deals_closed: number
  orders_created: number
  messages_sent: number
  sequences_started: number
  workflows_activated: number
  revenue_generated: number
  deals_value_closed: number
  actions_escalated: number
  actions_pending_approval: number
  actions_rejected: number
  ai_summary: string | null
  highlights: any[]
  created_at: string
}

export interface AutopilotStatus {
  business_id: string
  is_active: boolean
  is_paused: boolean
  paused_reason: string | null
  today_executed: number
  today_pending: number
  today_escalated: number
  today_revenue: number
  last_action_at: string | null
}

export interface AutopilotOverview {
  business_id: string
  message: string
  period: string
  summary: Record<string, any>
  pending_actions: AutopilotActionLog[]
  escalations: AutopilotActionLog[]
}

export interface OvernightSaleItem {
  seller_name: string
  seller_avatar?: string
  platform: string
  customer_name: string
  amount: number
  time: string
}

export interface OvernightSection {
  emoji: string
  title: string
  count: number
  items: Record<string, any>[]
  highlight?: string
}

export interface OvernightReport {
  greeting: string
  night_period: string
  summary_stats: Record<string, any>
  sections: OvernightSection[]
  top_seller: Record<string, any> | null
  prediction: string
  trust_score: number
  recommendation: string
}

export const autopilotApi = {
  getConfig: (businessId: string) =>
    api.get<AutopilotConfig>(`/autopilot/config/${businessId}`).then(r => r.data),

  updateConfig: (businessId: string, data: Partial<AutopilotConfig>) =>
    api.patch<AutopilotConfig>(`/autopilot/config/${businessId}`, data).then(r => r.data),

  getStatus: (businessId: string) =>
    api.get<AutopilotStatus>(`/autopilot/status/${businessId}`).then(r => r.data),

  getOverview: (businessId: string, period?: string) =>
    api.get<AutopilotOverview>(`/autopilot/overview/${businessId}`, { params: { period } }).then(r => r.data),

  getAuditLog: (businessId: string, params?: { status?: string; action_type?: string; limit?: number; offset?: number }) =>
    api.get<AutopilotActionLog[]>(`/autopilot/audit-log/${businessId}`, { params }).then(r => r.data),

  approveAction: (actionId: string, reason?: string) =>
    api.post<AutopilotActionLog>(`/autopilot/approve/${actionId}`, { reason }).then(r => r.data),

  rejectAction: (actionId: string, reason: string) =>
    api.post<AutopilotActionLog>(`/autopilot/reject/${actionId}`, { reason }).then(r => r.data),

  pause: (businessId: string, reason?: string) =>
    api.post<AutopilotConfig>(`/autopilot/pause/${businessId}`, null, { params: { reason } }).then(r => r.data),

  resume: (businessId: string) =>
    api.post<AutopilotConfig>(`/autopilot/resume/${businessId}`).then(r => r.data),

  getDailyReports: (businessId: string, limit?: number) =>
    api.get<AutopilotDailyReport[]>(`/autopilot/daily-reports/${businessId}`, { params: { limit } }).then(r => r.data),

  getOvernightReport: (businessId: string) =>
    api.get<OvernightReport>(`/autopilot/overnight-report/${businessId}`).then(r => r.data),
}
