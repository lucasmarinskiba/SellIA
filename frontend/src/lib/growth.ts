import { api } from './api'

export interface GrowthDashboardMetrics {
  leads_this_week: number
  total_organic_leads: number
  total_conversions: number
  conversion_rate: number
  active_campaigns: number
  sources_breakdown: Record<string, number>
  period: string
}

export interface GrowthCampaign {
  id: string
  business_id: string
  name: string
  description: string | null
  campaign_type: string
  status: string
  config: Record<string, any>
  target_audience: string | null
  content_pillars: string[]
  tone_of_voice: string
  leads_generated: number
  conversions: number
  revenue_attributed: number
  content_published: number
  engagement_score: number
  metrics_snapshot: Record<string, any>
  started_at: string | null
  ended_at: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LeadMagnet {
  id: string
  business_id: string
  campaign_id: string | null
  title: string
  description: string | null
  format: string
  topic: string
  content: Record<string, any>
  landing_page_copy: string | null
  delivery_message: string | null
  call_to_action: string | null
  times_delivered: number
  times_downloaded: number
  times_converted: number
  conversion_rate: number
  engagement_score: number
  auto_deliver: boolean
  delivery_channel: string
  delivery_trigger: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface InboundLead {
  id: string
  business_id: string
  conversation_id: string | null
  campaign_id: string | null
  lead_magnet_id: string | null
  source_type: string
  source_detail: string | null
  contact_info: Record<string, any>
  nurturing_stage: string
  engagement_score: number
  value_touches_received: number
  sales_touches_received: number
  first_touch_at: string
  last_touch_at: string
  converted_at: string | null
  is_active: boolean
}

export interface SocialProofItem {
  id: string
  business_id: string
  conversation_id: string | null
  order_id: string | null
  item_type: string
  status: string
  content: string
  rating: number | null
  headline: string | null
  customer_name: string | null
  media_urls: string[]
  sentiment_score: number
  ai_summary: string | null
  key_quotes: string[]
  usage_count: number
  is_active: boolean
  created_at: string
}

export interface ReferralMetrics {
  business_id: string
  unique_referrers: number
  total_signups: number
  total_conversions: number
  signups_per_referrer: number
  conversion_rate: number
  k_factor: number
  k_interpretation: string
  total_revenue: number
  exponential_growth: boolean
}

export interface ValueSequence {
  id: string
  business_id: string
  name: string
  topic: string
  message_count: number
  total_duration_days: number
  target_segment: string
  times_started: number
  times_completed: number
  conversion_rate: number
  avg_engagement_score: number
  is_active: boolean
  created_at: string
}

export const growthApi = {
  // Dashboard
  getDashboard: (): Promise<GrowthDashboardMetrics> =>
    api.get('/growth/dashboard').then(r => r.data),

  // Campaigns
  listCampaigns: (params?: { campaign_type?: string; status?: string }): Promise<GrowthCampaign[]> =>
    api.get('/growth/campaigns', { params }).then(r => r.data),

  createCampaign: (data: Partial<GrowthCampaign>): Promise<GrowthCampaign> =>
    api.post('/growth/campaigns', data).then(r => r.data),

  activateCampaign: (id: string): Promise<GrowthCampaign> =>
    api.post(`/growth/campaigns/${id}/activate`).then(r => r.data),

  pauseCampaign: (id: string): Promise<GrowthCampaign> =>
    api.post(`/growth/campaigns/${id}/pause`).then(r => r.data),

  evaluateCampaign: (id: string): Promise<any> =>
    api.get(`/growth/campaigns/${id}/evaluate`).then(r => r.data),

  // Lead Magnets
  createLeadMagnet: (data: { topic: string; magnet_format?: string; target_audience?: string; campaign_id?: string }): Promise<LeadMagnet> =>
    api.post('/growth/lead-magnets', data).then(r => r.data),

  listLeadMagnets: (): Promise<LeadMagnet[]> =>
    api.get('/growth/lead-magnets').then(r => r.data),

  getLeadMagnetPerformance: (id: string): Promise<any> =>
    api.get(`/growth/lead-magnets/${id}/performance`).then(r => r.data),

  getTopLeadMagnets: (limit?: number): Promise<any[]> =>
    api.get('/growth/lead-magnets/top', { params: { limit } }).then(r => r.data),

  // Inbound Leads
  listInboundLeads: (params?: { stage?: string; source_type?: string; limit?: number }): Promise<InboundLead[]> =>
    api.get('/growth/leads', { params }).then(r => r.data),

  // Social Proof
  getSocialProofWall: (params?: { item_type?: string; count?: number; min_rating?: number }): Promise<SocialProofItem[]> =>
    api.get('/growth/social-proof', { params }).then(r => r.data),

  getSocialProofStats: (): Promise<any> =>
    api.get('/growth/social-proof/stats').then(r => r.data),

  getModerationQueue: (): Promise<SocialProofItem[]> =>
    api.get('/growth/social-proof/moderation-queue').then(r => r.data),

  approveSocialProof: (id: string): Promise<SocialProofItem> =>
    api.post(`/growth/social-proof/${id}/approve`).then(r => r.data),

  rejectSocialProof: (id: string, reason?: string): Promise<SocialProofItem> =>
    api.post(`/growth/social-proof/${id}/reject`, null, { params: { reason } }).then(r => r.data),

  // Referrals
  getReferralMetrics: (): Promise<ReferralMetrics> =>
    api.get('/growth/referrals/metrics').then(r => r.data),

  getReferralReport: (): Promise<any> =>
    api.get('/growth/referrals/report').then(r => r.data),

  createReferralCampaign: (data: { name: string; incentive_type?: string; reward_value?: number; max_referrals_per_user?: number }): Promise<any> =>
    api.post('/growth/referrals/campaign', data).then(r => r.data),

  // Value Sequences
  listValueSequences: (): Promise<ValueSequence[]> =>
    api.get('/growth/value-sequences').then(r => r.data),

  createValueSequence: (data: { name: string; topic: string; message_count?: number; total_duration_days?: number; target_segment?: string }): Promise<ValueSequence> =>
    api.post('/growth/value-sequences', data).then(r => r.data),

  getValueSequencePerformance: (id: string): Promise<any> =>
    api.get(`/growth/value-sequences/${id}/performance`).then(r => r.data),

  // UGC
  getUgcGallery: (params?: { content_type?: string; limit?: number }): Promise<any[]> =>
    api.get('/growth/ugc/gallery', { params }).then(r => r.data),
}
