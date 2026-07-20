import { api } from './api'

export interface Pipeline {
  id: string
  business_id: string
  name: string
  description: string | null
  stages: PipelineStage[]
  is_default: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface PipelineStage {
  id: string
  name: string
  order: number
  color?: string
}

export interface Deal {
  id: string
  business_id: string
  pipeline_id: string | null
  conversation_id: string | null
  title: string
  description: string | null
  contact_name: string | null
  contact_email: string | null
  contact_phone: string | null
  value: number | null
  currency: string
  stage: string
  probability: number
  priority: number
  expected_close_date: string | null
  actual_close_date: string | null
  close_reason: string | null
  source_channel: string | null
  extra_data: Record<string, any>
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LeadScore {
  id: string
  conversation_id: string
  total_score: number
  classification: string
  engagement_score: number
  intent_score: number
  demographic_score: number
  behavioral_score: number
  recency_score: number
  last_calculated_at: string
}

export interface CRMSummary {
  total_deals: number
  total_value: number
  deals_by_stage: Record<string, number>
  value_by_stage: Record<string, number>
  avg_deal_value: number
  win_rate: number
  hot_leads: number
  warm_leads: number
  cold_leads: number
}

export const crmApi = {
  getPipelines: (businessId: string) =>
    api.get<Pipeline[]>('/crm/pipelines', { params: { business_id: businessId } }).then(r => r.data),

  createPipeline: (data: Omit<Pipeline, 'id' | 'created_at' | 'updated_at' | 'is_default' | 'is_active'>) =>
    api.post<Pipeline>('/crm/pipelines', data).then(r => r.data),

  getDeals: (businessId: string, params?: { stage?: string; pipeline_id?: string; search?: string }) =>
    api.get<Deal[]>('/crm/deals', { params: { business_id: businessId, ...params } }).then(r => r.data),

  createDeal: (data: Omit<Deal, 'id' | 'created_at' | 'updated_at' | 'actual_close_date' | 'close_reason' | 'source_channel' | 'is_active'>) =>
    api.post<Deal>('/crm/deals', data).then(r => r.data),

  updateDeal: (id: string, data: Partial<Deal>) =>
    api.patch<Deal>(`/crm/deals/${id}`, data).then(r => r.data),

  moveDeal: (id: string, stage: string, order?: number) =>
    api.post<Deal>(`/crm/deals/${id}/move`, { stage, order }).then(r => r.data),

  deleteDeal: (id: string) =>
    api.delete(`/crm/deals/${id}`).then(r => r.data),

  getLeadScores: (businessId: string, params?: { classification?: string; min_score?: number }) =>
    api.get<LeadScore[]>('/crm/lead-scores', { params: { business_id: businessId, ...params } }).then(r => r.data),

  getSummary: (businessId: string) =>
    api.get<CRMSummary>('/crm/summary', { params: { business_id: businessId } }).then(r => r.data),
}
