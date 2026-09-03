/**
 * Brand Transformation API client.
 * Backend: /api/v1/businesses/{businessId}/brand-transformation
 */
import { api } from '@/lib/api'

const base = (bid: string) => `/businesses/${bid}/brand-transformation`

export interface StageInfo {
  key: string
  order: number
  name: string
  goal: string
  agent: string
  deliverable: string
}

export interface DomainHealth {
  llm_available: boolean
  model: string
  agents_mode: 'ai' | 'fallback'
  note: string | null
}

export interface BusinessProfileIn {
  industry: string
  what_they_sell: string
  current_positioning?: string
  known_competitors?: string[]
  revenue_model?: string
  target_customer?: string
  price_point?: string
  notes?: string
  // diagnosis-only evidence (all optional)
  time_in_market?: string
  monthly_revenue?: string
  gross_margin_pct?: number
  repeat_purchase_rate?: string
  pricing?: string[]
  channels?: string[]
  differentiation_claims?: string[]
  customer_quotes?: string[]
  recent_marketing?: string[]
}

export interface Diagnosis {
  id: string
  industry: string
  referent_potential_score: number
  commoditization_level: string
  symptoms: string[] | null
  root_causes: string[] | null
  highest_leverage_moves: string[] | null
  scorecard: Record<string, number> | null
  summary: string | null
  commoditization_analysis: Record<string, any> | null
  referent_gap: Record<string, any> | null
  closest_precedent: Record<string, any> | null
  moat_assessment: Record<string, any> | null
  quick_wins: string[] | null
  structural_moves: string[] | null
  kill_criteria: string[] | null
  second_order_risk: string | null
  evidence_quality: string | null
  confidence: number
  frameworks_applied: string[] | null
  generated_by: string
  score_delta: number | null
  created_at: string
}

export interface Program {
  id: string
  name: string
  status: string
  current_stage: string
  completed_stages: string[] | null
  stage_artifacts: Record<string, string> | null
  roadmap: Record<string, any> | null
  execution_plan: Record<string, any> | null
  coherence_audit: Record<string, any> | null
  metrics_board: Record<string, any> | null
  created_at: string
  updated_at: string
}

export interface StageResult {
  program_id: string
  stage_key: string
  stage_name: string
  artifact_id: string | null
  artifact: Record<string, any>
  next_stage: string | null
  completed_stages: string[]
}

export interface FomoCampaignPlan {
  playbook_id: string
  cadence: string | null
  campaign_specs: Array<Record<string, any>>
  skipped_levers: Array<{ lever: string; reason: string }>
  deployed?: Array<Record<string, any>>
  created_count?: number
}

export const brandTransformation = {
  stages: (bid: string) => api.get<StageInfo[]>(`${base(bid)}/stages`).then((r) => r.data),
  health: (bid: string) => api.get<DomainHealth>(`${base(bid)}/health`).then((r) => r.data),

  // Etapa 0
  latestDiagnosis: (bid: string) =>
    api.get<Diagnosis | null>(`${base(bid)}/agents/diagnosis/latest`).then((r) => r.data),
  diagnosisHistory: (bid: string) =>
    api.get<Diagnosis[]>(`${base(bid)}/agents/diagnosis/history`).then((r) => r.data),
  runDiagnosis: (bid: string, body: BusinessProfileIn) =>
    api.post<Diagnosis>(`${base(bid)}/agents/diagnosis`, body).then((r) => r.data),

  // Programs
  listPrograms: (bid: string) => api.get<Program[]>(`${base(bid)}/programs`).then((r) => r.data),
  getProgram: (bid: string, pid: string) =>
    api.get<Program>(`${base(bid)}/programs/${pid}`).then((r) => r.data),
  createProgram: (bid: string, name: string, profile: BusinessProfileIn) =>
    api.post<Program>(`${base(bid)}/programs`, { name, profile }).then((r) => r.data),
  runStage: (bid: string, pid: string, stageKey: string, body?: { profile?: BusinessProfileIn; extra_instructions?: string }) =>
    api.post<StageResult>(`${base(bid)}/programs/${pid}/stages/${stageKey}/run`, body ?? {}).then((r) => r.data),
  runAll: (bid: string, pid: string) =>
    api.post<StageResult[]>(`${base(bid)}/programs/${pid}/run-all`, {}).then((r) => r.data),
  coherenceAudit: (bid: string, pid: string) =>
    api.post<Record<string, any>>(`${base(bid)}/programs/${pid}/coherence-audit`, {}).then((r) => r.data),

  // FOMO bridge
  fomoCampaignPreview: (bid: string) =>
    api.get<FomoCampaignPlan>(`${base(bid)}/agents/fomo-engine/campaign-preview`).then((r) => r.data),
  deployFomoCampaigns: (bid: string, body: { activate?: boolean; levers?: string[]; dry_run?: boolean }) =>
    api.post<FomoCampaignPlan>(`${base(bid)}/agents/fomo-engine/deploy-campaigns`, body).then((r) => r.data),

  // Automations
  listAutomations: (bid: string) => api.get<any[]>(`${base(bid)}/automations`).then((r) => r.data),
  automationAlerts: (bid: string) =>
    api.get<Array<{ automation_id: string; type: string; severity: string; at: string | null; headline: string | null; recommended_action: string | null }>>(
      `${base(bid)}/automations/alerts`,
    ).then((r) => r.data),
  automationHistory: (bid: string, aid: string) =>
    api.get<{ automation_id: string; type: string; runs: any[] }>(`${base(bid)}/automations/${aid}/history`).then((r) => r.data),
  createAutomation: (bid: string, body: { automation_type: string; schedule?: string; config?: any }) =>
    api.post<any>(`${base(bid)}/automations`, body).then((r) => r.data),
  runAutomation: (bid: string, aid: string) =>
    api.post<any>(`${base(bid)}/automations/${aid}/run`, {}).then((r) => r.data),
}
