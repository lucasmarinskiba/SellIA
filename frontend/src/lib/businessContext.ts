import { api } from './api'

export interface BusinessContext {
  id: string
  user_id: string
  business_id?: string
  business_type: string
  sales_model: string
  geographic_reach: string
  presence_type: string
  industry?: string
  target_audience?: string
  value_proposition?: string
  price_range?: string
  average_ticket?: number
  city?: string
  state_province?: string
  country: string
  address?: string
  has_physical_location: boolean
  serves_home_office: boolean
  does_delivery: boolean
  does_pickup: boolean
  shipping_radius_km?: number
  channels_configured: Record<string, boolean>
  ads_configured: Record<string, boolean>
  shipping_configured: Record<string, boolean>
  website_configured: boolean
  seo_configured: boolean
  email_marketing_configured: boolean
  primary_goal?: string
  monthly_revenue_goal?: number
  monthly_leads_goal?: number
  target_countries: string[]
  ai_recommended_playbooks: string[]
  ai_priority_actions: Record<string, unknown>[]
  ai_brand_voice?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ReachAnalysis {
  current_reach: string
  recommended_reach: string
  local_seo_priority: boolean
  cross_border_opportunity: boolean
  shipping_recommendations: string[]
  platform_recommendations: string[]
  estimated_addressable_market: string
}

export interface ChannelGap {
  channel: string
  is_configured: boolean
  priority: string
  impact_estimate: string
  setup_difficulty: string
  recommended_playbook?: string
}

export interface WizardStep {
  step: number
  title: string
  description: string
  fields: Record<string, unknown>[]
  is_completed: boolean
}

export interface WizardState {
  current_step: number
  total_steps: number
  steps: WizardStep[]
  context: BusinessContext
}

export const businessContextApi = {
  getContext: (businessId?: string) =>
    api.get<BusinessContext>('/business-context', { params: businessId ? { business_id: businessId } : undefined }).then(r => r.data),

  updateContext: (data: Partial<BusinessContext>, businessId?: string) =>
    api.post<BusinessContext>('/business-context', data, { params: businessId ? { business_id: businessId } : undefined }).then(r => r.data),

  detectContext: (businessId: string) =>
    api.get<BusinessContext>('/business-context/detect', { params: { business_id: businessId } }).then(r => r.data),

  getReachAnalysis: (contextId: string) =>
    api.get<ReachAnalysis>('/business-context/reach-analysis', { params: { context_id: contextId } }).then(r => r.data),

  getChannelGaps: (contextId: string) =>
    api.get<ChannelGap[]>('/business-context/channel-gaps', { params: { context_id: contextId } }).then(r => r.data),

  getRecommendedPlaybooks: (contextId: string) =>
    api.get<string[]>('/business-context/recommended-playbooks', { params: { context_id: contextId } }).then(r => r.data),

  getWizardState: (contextId: string) =>
    api.get<WizardState>('/business-context/wizard', { params: { context_id: contextId } }).then(r => r.data),

  saveWizardStep: (step: number, data: Partial<BusinessContext>, contextId: string) =>
    api.post<WizardState>(`/business-context/wizard/step/${step}`, data, { params: { context_id: contextId } }).then(r => r.data),
}
