import { api } from './api'

export interface AlertRule {
  id: string
  business_id: string
  name: string
  description: string | null
  is_active: boolean
  rule_type: string
  config: Record<string, any>
  severity: string
  channels: string[]
  cooldown_minutes: number
  max_alerts_per_day: number
  created_at: string
  updated_at: string
}

export interface Alert {
  id: string
  business_id: string
  rule_id: string | null
  conversation_id: string | null
  deal_id: string | null
  order_id: string | null
  title: string
  description: string | null
  severity: string
  status: string
  entity_type: string | null
  entity_id: string | null
  recommended_action: string | null
  metadata: Record<string, any>
  created_at: string
  read_at: string | null
  dismissed_at: string | null
}

export interface AlertStats {
  total_unread: number
  total_read: number
  total_dismissed: number
  by_severity: Record<string, number>
}

export interface Recommendation {
  id: string
  business_id: string
  type: string
  title: string
  description: string | null
  priority: number
  context_data: Record<string, any>
  action_type: string
  action_payload: Record<string, any>
  status: string
  applied_at: string | null
  applied_by_user_id: string | null
  created_at: string
}

export const alertsApi = {
  // Rules
  getRules: (businessId: string) =>
    api.get<AlertRule[]>('/alerts/rules', { params: { business_id: businessId } }).then(r => r.data),

  createRule: (data: Omit<AlertRule, 'id' | 'created_at' | 'updated_at'>) =>
    api.post<AlertRule>('/alerts/rules', data).then(r => r.data),

  updateRule: (id: string, data: Partial<AlertRule>) =>
    api.patch<AlertRule>(`/alerts/rules/${id}`, data).then(r => r.data),

  deleteRule: (id: string) =>
    api.delete(`/alerts/rules/${id}`).then(r => r.data),

  // Alerts
  getAlerts: (businessId: string, params?: { status?: string; severity?: string; limit?: number; offset?: number }) =>
    api.get<Alert[]>('/alerts', { params: { business_id: businessId, ...params } }).then(r => r.data),

  getAlertStats: (businessId: string) =>
    api.get<AlertStats>('/alerts/stats', { params: { business_id: businessId } }).then(r => r.data),

  markRead: (id: string) =>
    api.patch<Alert>(`/alerts/${id}/read`).then(r => r.data),

  dismissAlert: (id: string) =>
    api.patch<Alert>(`/alerts/${id}/dismiss`).then(r => r.data),

  deleteAlert: (id: string) =>
    api.delete(`/alerts/${id}`).then(r => r.data),

  // Recommendations
  getRecommendations: (businessId: string, status = 'pending') =>
    api.get<Recommendation[]>('/alerts/recommendations', { params: { business_id: businessId, status } }).then(r => r.data),

  applyRecommendation: (id: string) =>
    api.post<Recommendation>(`/alerts/recommendations/${id}/apply`, {}).then(r => r.data),

  dismissRecommendation: (id: string) =>
    api.post<Recommendation>(`/alerts/recommendations/${id}/dismiss`).then(r => r.data),
}
