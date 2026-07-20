import { api } from './api'

export type MissionStatus = 'draft' | 'proposed' | 'approved' | 'running' | 'completed' | 'failed' | 'cancelled'
export type MissionCategory = 'launch' | 'seo' | 'ads' | 'recovery' | 'expansion' | 'branding' | 'logistics' | 'automation'
export type MissionCreator = 'ai' | 'user'
export type StepStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'waiting_approval'
export type DiagnosticCategory = 'sales' | 'branding' | 'traffic' | 'seo' | 'logistics' | 'ads' | 'conversion' | 'retention'
export type DiagnosticSeverity = 'info' | 'warning' | 'critical'

export interface MissionStep {
  id: string
  mission_id: string
  step_number: number
  title: string
  description?: string
  platform: string
  action_type: string
  action_params: Record<string, unknown>
  status: StepStatus
  result?: Record<string, unknown>
  error_message?: string
  requires_approval: boolean
  approved_by_user: boolean
  computer_use_session_id?: string
  started_at?: string
  completed_at?: string
  created_at: string
}

export interface Mission {
  id: string
  user_id: string
  business_id?: string
  title: string
  description?: string
  category: MissionCategory
  status: MissionStatus
  playbook_slug?: string
  target_platforms: string[]
  expected_impact: { revenue_estimate?: number; time_estimate?: string; confidence?: number }
  created_by: MissionCreator
  approved_at?: string
  started_at?: string
  completed_at?: string
  created_at: string
  updated_at: string
  steps?: MissionStep[]
}

export interface BusinessDiagnostic {
  id: string
  user_id: string
  business_id?: string
  mission_id?: string
  diagnostic_date: string
  category: DiagnosticCategory
  severity: DiagnosticSeverity
  finding: string
  metric_value?: string
  benchmark_value?: string
  recommended_mission_slug?: string
  context_data: Record<string, unknown>
  is_resolved: boolean
  resolved_at?: string
  created_at: string
}

export interface Playbook {
  slug: string
  name: string
  description: string
  platforms: string[]
  steps: Record<string, unknown>[]
  category: MissionCategory
  estimated_duration_minutes: number
}

export interface MissionCreateInput {
  playbook_slug: string
  business_id?: string
}

export interface DiagnosticRunResult {
  diagnostics: BusinessDiagnostic[]
  recommended_missions: Playbook[]
}

export const missionsApi = {
  getMissions: (businessId?: string) =>
    api.get<Mission[]>('/missions', { params: businessId ? { business_id: businessId } : undefined }).then(r => r.data),

  getMission: (id: string) =>
    api.get<Mission>(`/missions/${id}`).then(r => r.data),

  createMission: (data: MissionCreateInput) =>
    api.post<Mission>(`/missions/from-playbook/${data.playbook_slug}`, { business_id: data.business_id }).then(r => r.data),

  approveMission: (id: string) =>
    api.post<{ status: string; mission_id: string }>(`/missions/${id}/approve`).then(r => r.data),

  runMission: (id: string) =>
    api.post<{ status: string; mission_id: string }>(`/missions/${id}/start`).then(r => r.data),

  cancelMission: (id: string) =>
    api.post<{ status: string; mission_id: string }>(`/missions/${id}/cancel`).then(r => r.data),

  getDiagnostics: (businessId?: string) =>
    api.get<BusinessDiagnostic[]>('/missions/diagnostics/list', { params: businessId ? { business_id: businessId } : undefined }).then(r => r.data),

  runDiagnostics: (businessId?: string) =>
    api.post<DiagnosticRunResult>('/missions/diagnostics/run', { business_id: businessId }).then(r => r.data),

  // createMissionFromDiagnostics: usa createMission con el playbook_slug recomendado
  createMissionFromDiagnostics: (playbookSlug: string, businessId?: string) =>
    api.post<Mission>(`/missions/from-playbook/${playbookSlug}`, { business_id: businessId }).then(r => r.data),

  getPlaybooks: () =>
    api.get<Playbook[]>('/missions/playbooks').then(r => r.data),

  // Shipping Assistant
  getShippingRecommendations: (context: Record<string, unknown>) =>
    api.post('/missions/shipping/recommendations', context).then(r => r.data),
  getShippingSetupSteps: (carrier: string, context: Record<string, unknown>) =>
    api.post(`/missions/shipping/setup-steps?carrier=${carrier}`, context).then(r => r.data),
  estimateShippingCosts: (data: Record<string, unknown>) =>
    api.post('/missions/shipping/estimate-costs', data).then(r => r.data),
  getCrossBorderRequirements: (country: string) =>
    api.get(`/missions/shipping/cross-border/${country}`).then(r => r.data),

  // Ad Spend Assistant
  getAdsPlatformRecommendations: (context: Record<string, unknown>, budget: number) =>
    api.post('/missions/ads/platform-recommendations', { ...context, budget }).then(r => r.data),
  getAdsBudgetAllocation: (monthlyBudget: number, businessType: string, goal: string) =>
    api.post('/missions/ads/budget-allocation', { monthly_budget: monthlyBudget, business_type: businessType, goal }).then(r => r.data),
  getAdsCampaignSteps: (platform: string, objective: string) =>
    api.post('/missions/ads/campaign-steps', { platform, objective }).then(r => r.data),
  estimateAdsCpa: (businessType: string, platform: string, country: string) =>
    api.post('/missions/ads/estimate-cpa', { business_type: businessType, platform, country }).then(r => r.data),
  getAdsCreativeRecommendations: (platform: string, businessType: string) =>
    api.post('/missions/ads/creative-recommendations', { platform, business_type: businessType }).then(r => r.data),
}
