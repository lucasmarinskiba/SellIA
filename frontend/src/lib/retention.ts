import { api } from './api'

export interface ReferralProgram {
  id: string
  business_id: string
  name: string
  description: string | null
  reward_type: string
  reward_value: number
  max_referrals_per_user: number
  expiry_days: number
  is_active: boolean
  created_at: string
}

export interface NpsCampaign {
  id: string
  business_id: string
  name: string
  trigger_type: string
  trigger_days: number
  status: string
  question_text: string
  thank_you_message: string
  is_active: boolean
  created_at: string
}

export interface NpsScore {
  nps: number
  promoters: number
  passives: number
  detractors: number
  total_responses: number
}

export interface CustomerSegment {
  id: string
  business_id: string
  conversation_id: string
  segment: string
  r_score: number
  f_score: number
  m_score: number
  rfm_score: number
  last_order_at: string | null
  total_orders: number
  total_revenue: number
  avg_order_value: number
  calculated_at: string
}

export const retentionApi = {
  getReferralPrograms: (businessId: string) =>
    api.get<ReferralProgram[]>(`/businesses/${businessId}/retention/referral-programs`).then(r => r.data),

  createReferralProgram: (businessId: string, data: Partial<ReferralProgram>) =>
    api.post<ReferralProgram>(`/businesses/${businessId}/retention/referral-programs`, data).then(r => r.data),

  getNpsCampaigns: (businessId: string) =>
    api.get<NpsCampaign[]>(`/businesses/${businessId}/retention/nps-campaigns`).then(r => r.data),

  createNpsCampaign: (businessId: string, data: Partial<NpsCampaign>) =>
    api.post<NpsCampaign>(`/businesses/${businessId}/retention/nps-campaigns`, data).then(r => r.data),

  getNpsScore: (businessId: string, campaignId?: string) =>
    api.get<NpsScore>(`/businesses/${businessId}/retention/nps-score`, { params: { campaign_id: campaignId } }).then(r => r.data),

  getCustomerSegments: (businessId: string) =>
    api.get<CustomerSegment[]>(`/businesses/${businessId}/retention/segments`).then(r => r.data),

  calculateRFM: (businessId: string) =>
    api.post(`/businesses/${businessId}/retention/calculate-rfm`).then(r => r.data),
}
