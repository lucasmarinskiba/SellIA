import { api } from './api'

export interface SequenceStep {
  id: string
  sequence_id: string
  step_order: number
  delay_hours: number
  delay_minutes: number
  template_id: string | null
  subject_override: string | null
  body_override: string | null
  condition: string | null
  extra_data: Record<string, any>
  is_active: boolean
  created_at: string
}

export interface EmailSequence {
  id: string
  business_id: string
  name: string
  description: string | null
  category: string | null
  status: string
  trigger_type: string | null
  is_active: boolean
  sent_count: number
  opens_count: number
  clicks_count: number
  created_at: string
  updated_at: string
  steps: SequenceStep[]
}

export interface SequenceAnalytics {
  sequence_id: string
  total_subscribers: number
  total_sent: number
  total_opens: number
  total_clicks: number
  open_rate: number
  click_rate: number
  sent_trend: { date: string; count: number }[]
}

export interface CreateSequenceData {
  business_id: string
  name: string
  description?: string
  category?: string
  status?: string
  trigger_type?: string
  steps: {
    step_order: number
    delay_hours?: number
    delay_minutes?: number
    template_id?: string
    subject_override?: string
    body_override?: string
    condition?: string
    extra_data?: Record<string, any>
  }[]
}

export const sequencesApi = {
  list: (businessId: string) =>
    api.get<EmailSequence[]>('/automations/email-sequences', { params: { business_id: businessId } }).then(r => r.data),

  get: (id: string) =>
    api.get<EmailSequence>(`/automations/email-sequences/${id}`).then(r => r.data),

  create: (data: CreateSequenceData) =>
    api.post<EmailSequence>('/automations/email-sequences', data).then(r => r.data),

  update: (id: string, data: Partial<EmailSequence>) =>
    api.patch<EmailSequence>(`/automations/email-sequences/${id}`, data).then(r => r.data),

  delete: (id: string) =>
    api.delete(`/automations/email-sequences/${id}`).then(r => r.data),

  analytics: (id: string) =>
    api.get<SequenceAnalytics>(`/automations/email-sequences/${id}/analytics`).then(r => r.data),
}
