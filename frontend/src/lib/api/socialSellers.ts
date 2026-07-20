/** Social Sellers / Dream Team — REST API Client */

import { api } from '../api'

export interface SocialSeller {
  id: string
  business_id: string
  platform: string
  name: string
  avatar_url?: string
  personality_slug?: string
  voice_config: {
    tone?: string
    emojis?: string[]
    catch_phrases?: string[]
    response_speed?: string
  }
  stats: {
    total_sales?: number
    revenue?: number
    conversion_rate?: number
    loyal_customers?: number
  }
  status: 'active' | 'paused' | 'training'
  ai_auto_reply: boolean
  greeting_message?: string
  closing_message?: string
  created_at: string
  updated_at: string
}

export interface SellerCustomer {
  id: string
  seller_id: string
  customer_id: string
  customer_name: string
  customer_avatar?: string
  first_contact_at?: string
  last_contact_at?: string
  total_interactions: number
  deals_closed: number
  total_revenue: number
  relationship_stage: string
  loyalty_score: number
  next_best_action?: string
  unified_customer_id?: string
  unified_display_name?: string
  unified_identity_map?: Record<string, string>
  unified_total_lifetime_value?: number
}

export interface SellerPipeline {
  stage: string
  count: number
  revenue: number
}

export interface SellerPerformance {
  period: string
  leads_acquired: number
  messages_sent: number
  conversations_active: number
  deals_won: number
  revenue: number
  conversion_rate: number
}

export interface TeamReport {
  total_sellers: number
  total_revenue: number
  total_deals: number
  avg_conversion_rate: number
  top_performer?: SocialSeller
  sellers: SocialSeller[]
}

export interface CreateSellerRequest {
  business_id: string
  platform: string
  name: string
  personality_slug?: string
  voice_config?: Record<string, any>
}

export interface UpdateSellerRequest {
  name?: string
  personality_slug?: string
  voice_config?: Record<string, any>
  status?: 'active' | 'paused' | 'training'
  ai_auto_reply?: boolean
  greeting_message?: string
  closing_message?: string
}

export interface RecordSaleRequest {
  seller_id: string
  customer_id: string
  amount: number
  product_name?: string
}

export interface ExecuteActionRequest {
  seller_id: string
  action_type: string
  customer_id?: string
  payload?: Record<string, any>
}

export interface UnifiedCustomer {
  id: string
  business_id: string
  display_name: string
  master_email?: string
  master_phone?: string
  identity_map: Record<string, string>
  first_seen_at?: string
  last_seen_at?: string
  total_lifetime_value: number
  buying_frequency_days?: number
  preferred_platforms: string[]
  rfm_segment?: string
  last_purchase_at?: string
  total_purchases: number
}

export interface MergeSuggestion {
  customer_a_id: string
  customer_b_id: string
  score: number
  reasons: string[]
}

export interface WallOfFameCustomer {
  customer_id: string
  name: string
  ltv: number
  total_purchases: number
  last_purchase_at?: string
  first_contact_at?: string
  platform: string
  badges: { badge_type: string; name: string; icon_url?: string }[]
}

export interface CustomerBadge {
  id: string
  badge_type: string
  name: string
  description?: string
  icon_url?: string
  earned_at?: string
}

export interface LoyaltySegment {
  count: number
  avg_revenue: number
}

export interface LoyaltySegmentsResponse {
  business_id: string
  total_customers: number
  segments: Record<string, LoyaltySegment>
}

export interface LoyaltyActionRequest {
  action_type: 'send_gift' | 'offer_vip' | 'request_testimonial' | 'invite_referral'
  business_id: string
}

export interface LoyaltyActionResponse {
  status: string
  action: string
  business_id: string
  customer_id: string
  message: string
  created_at: string
}

export interface RadarOpportunity {
  conversation_id: string
  customer_name: string
  platform: string
  score: number
  heat_level: 'hot' | 'warm' | 'nurture' | 'at_risk'
  signals: string[]
  seller_id?: string
  seller_name?: string
  seller_avatar?: string
  last_contact_at?: string
  predicted_next_purchase?: {
    predicted_date?: string
    confidence_score: number
    days_until?: number
    reason?: string
    avg_interval_days?: number
  }
  purchase_history?: {
    total_orders: number
    total_spent: number
    avg_order_value: number
    last_order_at?: string
  }
  recent_messages_count: number
}

export interface RadarSummary {
  total_opportunities: number
  hot_count: number
  warm_count: number
  nurture_count: number
  at_risk_count: number
  total_potential_revenue: number
}

export interface RadarData {
  business_id: string
  generated_at: string
  summary: RadarSummary
  opportunities: Record<string, RadarOpportunity[]>
  top_actions: {
    priority: string
    target: string
    action: string
    reason: string
  }[]
}

export interface OpportunityScore {
  conversation_id: string
  score: number
  heat_level: string
  signals: string[]
  components: Record<string, number>
}

export interface RadarActPayload {
  action: string
  payload?: Record<string, any>
}

export interface IdealCustomerProfile {
  avg_lifetime_value: number
  avg_purchase_frequency_days: number
  preferred_platforms: string[]
  common_keywords_in_messages: string[]
  avg_deal_value: number
  best_performing_seller?: string
}

export interface LookalikeLead {
  lead_id: string
  name: string
  platform: string
  similarity_score: number
  why: string[]
  recommended_seller?: string
}

export interface LookalikeReport {
  summary: string
  ideal_profile: IdealCustomerProfile
  top_opportunities: LookalikeLead[]
  total_leads_scored: number
}

export const socialSellersApi = {
  listSellers: (businessId: string) =>
    api.get<SocialSeller[]>('/social-sellers', { params: { business_id: businessId } }).then(r => r.data),

  getSeller: (sellerId: string) =>
    api.get<SocialSeller>(`/social-sellers/${sellerId}`).then(r => r.data),

  createSeller: (data: CreateSellerRequest) =>
    api.post<SocialSeller>('/social-sellers', data).then(r => r.data),

  updateSeller: (sellerId: string, data: UpdateSellerRequest) =>
    api.patch<SocialSeller>(`/social-sellers/${sellerId}`, data).then(r => r.data),

  deleteSeller: (sellerId: string) =>
    api.delete(`/social-sellers/${sellerId}`).then(r => r.data),

  getSellerCustomers: (sellerId: string) =>
    api.get<SellerCustomer[]>(`/social-sellers/${sellerId}/customers`).then(r => r.data),

  getSellerPipeline: (sellerId: string) =>
    api.get<SellerPipeline[]>(`/social-sellers/${sellerId}/pipeline`).then(r => r.data),

  getSellerPerformance: (sellerId: string, period?: string) =>
    api.get<SellerPerformance[]>(`/social-sellers/${sellerId}/performance`, { params: period ? { period } : undefined }).then(r => r.data),

  getTeamReport: (businessId: string) =>
    api.get<TeamReport>('/social-sellers/team-report', { params: { business_id: businessId } }).then(r => r.data),

  recordSale: (data: RecordSaleRequest) =>
    api.post<{ success: boolean; sale_id: string }>('/social-sellers/record-sale', data).then(r => r.data),

  executeAction: (data: ExecuteActionRequest) =>
    api.post<{ success: boolean; result: any }>('/social-sellers/execute-action', data).then(r => r.data),

  listUnifiedCustomers: (businessId: string, params?: { limit?: number; offset?: number }) =>
    api.get<UnifiedCustomer[]>('/social-sellers/customers/unified', { params: { business_id: businessId, ...params } }).then(r => r.data),

  getUnifiedCustomer: (id: string) =>
    api.get<UnifiedCustomer>(`/social-sellers/customers/unified/${id}`).then(r => r.data),

  mergeCustomers: (targetId: string, sourceId: string) =>
    api.post<MergeSuggestion>('/social-sellers/customers/merge', { target_id: targetId, source_id: sourceId }).then(r => r.data),

  getMergeSuggestions: (businessId: string, customerAId: string, customerBId: string) =>
    api.get<MergeSuggestion[]>('/social-sellers/customers/suggest-merge', { params: { business_id: businessId, customer_a_id: customerAId, customer_b_id: customerBId } }).then(r => r.data),

  getWallOfFame: (businessId: string, limit?: number) =>
    api.get<WallOfFameCustomer[]>('/social-sellers/wall-of-fame', { params: { business_id: businessId, limit } }).then(r => r.data),

  getCustomerBadges: (customerId: string) =>
    api.get<CustomerBadge[]>(`/social-sellers/customers/${customerId}/badges`).then(r => r.data),

  checkBadges: (customerId: string, businessId: string) =>
    api.post<CustomerBadge[]>(`/social-sellers/customers/${customerId}/badges/check`, null, { params: { business_id: businessId } }).then(r => r.data),

  getLoyaltySegments: (businessId: string) =>
    api.get<LoyaltySegmentsResponse>('/social-sellers/loyalty/segments', { params: { business_id: businessId } }).then(r => r.data),

  createLoyaltyAction: (customerId: string, data: LoyaltyActionRequest) =>
    api.post<LoyaltyActionResponse>(`/social-sellers/customers/${customerId}/actions`, data).then(r => r.data),

  // Radar de Oportunidades
  getRadar: (businessId: string) =>
    api.get<RadarData>('/social-sellers/radar', { params: { business_id: businessId } }).then(r => r.data),

  getRadarOpportunities: (businessId: string, heatLevel?: string) =>
    api.get<RadarOpportunity[]>('/social-sellers/radar/opportunities', { params: { business_id: businessId, heat_level: heatLevel } }).then(r => r.data),

  getOpportunityScore: (conversationId: string) =>
    api.get<OpportunityScore>(`/social-sellers/radar/${conversationId}/score`).then(r => r.data),

  executeRadarAction: (conversationId: string, businessId: string, data: RadarActPayload) =>
    api.post<any>(`/social-sellers/radar/${conversationId}/act`, data, { params: { business_id: businessId } }).then(r => r.data),

  // Lookalike Audience Engine
  getIdealCustomerProfile: (businessId: string) =>
    api.get<IdealCustomerProfile>('/social-sellers/lookalike/profile', { params: { business_id: businessId } }).then(r => r.data),

  getLookalikeLeads: (businessId: string) =>
    api.get<LookalikeLead[]>('/social-sellers/lookalike/leads', { params: { business_id: businessId } }).then(r => r.data),

  getSimilarToCustomer: (customerId: string, businessId: string, limit?: number) =>
    api.get<LookalikeLead[]>(`/social-sellers/lookalike/similar-to/${customerId}`, { params: { business_id: businessId, limit } }).then(r => r.data),

  getLookalikeReport: (businessId: string) =>
    api.get<LookalikeReport>('/social-sellers/lookalike/report', { params: { business_id: businessId } }).then(r => r.data),
}
