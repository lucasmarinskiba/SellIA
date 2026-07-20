/** Competitive Intelligence — REST API Client */

import { api } from '../api'

export interface Monitor {
  id: string
  business_id: string
  competitor_name: string
  competitor_url: string
  products_to_track: string[]
  last_scraped_at?: string
  last_snapshot: Record<string, any>
  status: string
  created_at: string
  updated_at: string
}

export interface ChangeItem {
  change_type: string
  severity: string
  competitor_name: string
  product_name?: string
  old_value?: string
  new_value?: string
  diff_percent?: number
  detected_at: string
}

export interface StrategySuggestion {
  change: ChangeItem
  suggestion: string
  options: string[]
  risk_note?: string
}

export interface IntelligenceDashboard {
  monitors: Monitor[]
  recent_changes: ChangeItem[]
  alerts_count: number
  unread_alerts: number
  strategies: StrategySuggestion[]
}

export const competitiveApi = {
  listMonitors: (businessId: string) =>
    api.get<Monitor[]>(`/competitive/monitors?business_id=${businessId}`).then(r => r.data),

  createMonitor: (data: {
    business_id: string
    competitor_name: string
    competitor_url: string
    products_to_track?: string[]
  }) =>
    api.post<Monitor>('/competitive/monitors', data).then(r => r.data),

  deleteMonitor: (monitorId: string) =>
    api.delete(`/competitive/monitors/${monitorId}`).then(r => r.data),

  scrapeMonitor: (monitorId: string) =>
    api.post<{ monitor_id: string; prices_found: Record<string, string>; scraped_at: string; status: string }>(
      `/competitive/${monitorId}/scrape`
    ).then(r => r.data),

  getIntelligence: (businessId: string) =>
    api.get<IntelligenceDashboard>(`/competitive/intelligence?business_id=${businessId}`).then(r => r.data),

  getAlerts: (businessId: string) =>
    api.get<any[]>(`/competitive/alerts?business_id=${businessId}`).then(r => r.data),
}
