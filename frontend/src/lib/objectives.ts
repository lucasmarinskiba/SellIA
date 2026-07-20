import { api } from './api'

export interface Department {
  id: string
  business_id: string
  name: string
  slug: string
  description: string | null
  head_agent_personality_id: string | null
  color: string
  icon: string
  config: Record<string, any>
  is_active: boolean
  created_at: string
}

export interface BusinessObjective {
  id: string
  business_id: string
  department_id: string | null
  name: string
  description: string | null
  period: string
  status: string
  target_value: number
  current_value: number
  unit: string
  start_date: string
  end_date: string
  linked_workflow_id: string | null
  linked_channel_platform: string | null
  alert_threshold_percent: number
  alert_channels: string[]
  extra_data: Record<string, any>
  is_active: boolean
  created_at: string
}

export interface KPI {
  id: string
  business_id: string
  department_id: string | null
  objective_id: string | null
  name: string
  slug: string
  description: string | null
  metric_type: string
  aggregation: string
  target_value: number | null
  current_value: number
  unit: string
  period: string
  period_start: string | null
  period_end: string | null
  data_source: string
  data_source_filter: Record<string, any>
  is_active: boolean
  created_at: string
}

export const objectivesApi = {
  getDepartments: (businessId: string) =>
    api.get<Department[]>(`/businesses/${businessId}/objectives/departments`).then(r => r.data),

  createDepartment: (businessId: string, data: Partial<Department>) =>
    api.post<Department>(`/businesses/${businessId}/objectives/departments`, data).then(r => r.data),

  getObjectives: (businessId: string, status?: string) =>
    api.get<BusinessObjective[]>(`/businesses/${businessId}/objectives`, { params: { status } }).then(r => r.data),

  createObjective: (businessId: string, data: Partial<BusinessObjective>) =>
    api.post<BusinessObjective>(`/businesses/${businessId}/objectives`, data).then(r => r.data),

  getKPIs: (businessId: string, period?: string) =>
    api.get<KPI[]>(`/businesses/${businessId}/objectives/kpis`, { params: { period } }).then(r => r.data),

  createKPI: (businessId: string, data: Partial<KPI>) =>
    api.post<KPI>(`/businesses/${businessId}/objectives/kpis`, data).then(r => r.data),
}
