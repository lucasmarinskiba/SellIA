import { api } from './api'

export interface CostAttributionSummary {
  total_calls: number
  total_cost_usd: number
  total_tokens_input: number
  total_tokens_output: number
  avg_latency_ms: number | null
  cache_hit_rate: number
  by_provider: { name: string; cost_usd: number }[]
  by_model: { name: string; cost_usd: number }[]
  by_task_type: { name: string; cost_usd: number }[]
  period_days: number
}

export interface QualityGateConfig {
  enabled: boolean
  min_confidence_threshold: number
  auto_escalate_on_low_confidence: boolean
  max_ai_messages_before_human: number
}

export interface PlanRecommendation {
  current_plan: string
  current_plan_price: number
  current_limit: number
  usage_percent: number
  recommendation: 'keep' | 'upgrade' | 'downgrade'
  suggested_plan: string | null
  suggested_plan_price: number | null
  reason: string
  estimated_savings_or_extra_cost: number | null
}

export interface OnboardingProgress {
  account_created: boolean
  business_created: boolean
  channel_connected: boolean
  agent_configured: boolean
  first_conversation: boolean
  catalog_added: boolean
  automation_created: boolean
  current_step: string
  stuck_minutes: number
  ai_interventions_count: number
  progress_percent: number
}

export interface OnboardingHelpResponse {
  message: string
  suggested_action: string
  resources: string[]
}

export const consumoApi = {
  // Cost Attribution
  getCostAttribution: async (days = 30): Promise<CostAttributionSummary> => {
    const res = await api.get('/consumo/cost-attribution', { params: { days } })
    return res.data
  },

  // Quality Gate
  getQualityGate: async (): Promise<QualityGateConfig> => {
    const res = await api.get('/consumo/quality-gate')
    return res.data
  },
  updateQualityGate: async (data: Partial<QualityGateConfig>): Promise<QualityGateConfig> => {
    const res = await api.patch('/consumo/quality-gate', data)
    return res.data
  },

  // Plan Recommendation
  getPlanRecommendation: async (): Promise<PlanRecommendation> => {
    const res = await api.get('/consumo/plan-recommendation')
    return res.data
  },

  // Onboarding
  getOnboarding: async (): Promise<OnboardingProgress> => {
    const res = await api.get('/consumo/onboarding')
    return res.data
  },
  requestOnboardingHelp: async (current_step: string, context?: string): Promise<OnboardingHelpResponse> => {
    const res = await api.post('/consumo/onboarding/help', { current_step, context })
    return res.data
  },
}
