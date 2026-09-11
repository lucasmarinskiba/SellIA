import { UUID } from 'crypto'

export interface AutomationToggleResponse {
  id: UUID
  business_id: UUID
  toggle_key: string
  category: string
  display_name: string
  description?: string
  icon?: string
  is_enabled: boolean
  monthly_limit?: number
  current_month_usage: number
  enabled_at?: string
  disabled_at?: string
  created_at: string
  updated_at: string
}

export interface ToggleAuditLogResponse {
  id: UUID
  toggle_id: UUID
  action: string
  old_value?: Record<string, any>
  new_value?: Record<string, any>
  changed_by_email?: string
  reason?: string
  leads_affected?: number
  estimated_impact_pct?: number
  created_at: string
}

export interface ToggleDashboardStats {
  category: string
  total: number
  enabled: number
  usage: number
}

export interface ToggleDashboardResponse {
  by_category: ToggleDashboardStats[]
  timestamp: string
}

export const togglesApi = {
  async listToggles(businessId: UUID, category?: string): Promise<AutomationToggleResponse[]> {
    const params = new URLSearchParams()
    if (category) params.append('category', category)
    const res = await fetch(
      `/api/v1/automations/toggles/business/${businessId}?${params.toString()}`
    )
    if (!res.ok) throw new Error('Failed to fetch toggles')
    return res.json()
  },

  async getToggle(toggleId: UUID): Promise<AutomationToggleResponse> {
    const res = await fetch(`/api/v1/automations/toggles/${toggleId}`)
    if (!res.ok) throw new Error('Failed to fetch toggle')
    return res.json()
  },

  async updateToggle(
    toggleId: UUID,
    data: { is_enabled?: boolean; monthly_limit?: number }
  ): Promise<AutomationToggleResponse> {
    const res = await fetch(`/api/v1/automations/toggles/${toggleId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('Failed to update toggle')
    return res.json()
  },

  async getAuditHistory(toggleId: UUID): Promise<ToggleAuditLogResponse[]> {
    const res = await fetch(`/api/v1/automations/toggles/${toggleId}/audit`)
    if (!res.ok) throw new Error('Failed to fetch audit history')
    return res.json()
  },

  async resetUsage(toggleId: UUID): Promise<{ ok: boolean; message: string }> {
    const res = await fetch(`/api/v1/automations/toggles/${toggleId}/reset-usage`, {
      method: 'POST',
    })
    if (!res.ok) throw new Error('Failed to reset usage')
    return res.json()
  },

  async getDashboard(businessId: UUID): Promise<ToggleDashboardResponse> {
    const res = await fetch(`/api/v1/automations/toggles/dashboard/${businessId}`)
    if (!res.ok) throw new Error('Failed to fetch dashboard')
    return res.json()
  },
}
