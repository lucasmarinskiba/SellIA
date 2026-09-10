/**
 * Authority builder client.
 *
 * Mirrors backend/app/domains/authority/. Every score here is computed from the
 * account's own rows, and the trend is stored history — not the current value
 * redrawn as a curve.
 */

import { api } from './api'

export type ActionMode = 'automatic' | 'assisted' | 'manual'
export type ActionStatus = 'suggested' | 'in_progress' | 'done' | 'dismissed'

export interface Pillar {
  key: string
  label: string
  weight: number
  score: number
  inputs: Record<string, unknown>
  missing: string[]
}

export interface TrendPoint {
  captured_at: string
  date: string
  total_score: number
  pillars: Record<string, number>
}

export interface TrendAnalysis {
  direction: 'up' | 'down' | 'flat' | 'unknown'
  points: number
  delta?: number
  headline: string
  detail?: string
  next_focus?: string
  strongest_pillar: string | null
  weakest_pillar: string | null
  movements: { pillar: string; label: string; change: number }[]
}

export interface AuthorityAction {
  id: string
  action_key: string
  pillar: string
  agent: string | null
  principle: string | null
  title: string
  rationale: string | null
  script: string | null
  channel: string | null
  mode: ActionMode
  status: ActionStatus
  /** Points this would add to the total score, projected from the pillar's
   *  own formula — not an estimate of business impact. */
  impact_score: number | null
  executable: boolean
  needs_confirmation: boolean
  completed_at: string | null
}

export interface PsychologyAgent {
  key: string
  name: string
  principle: string
  source: string
  pillar: string
  focus: string
}

export interface AuthorityDashboard {
  total_score: number
  captured_at: string
  pillars: Pillar[]
  trend: TrendPoint[]
  analysis: TrendAnalysis
  actions: AuthorityAction[]
  agents: PsychologyAgent[]
}

export const authorityApi = {
  dashboard: (): Promise<AuthorityDashboard> =>
    api.get<AuthorityDashboard>('/authority-builder/dashboard').then(r => r.data),

  measure: (): Promise<{ total_score: number; captured_at: string }> =>
    api.post('/authority-builder/measure').then(r => r.data),

  setStatus: (id: string, status: ActionStatus): Promise<AuthorityAction> =>
    api.patch<AuthorityAction>(`/authority-builder/actions/${id}`, { status }).then(r => r.data),

  personalize: (id: string): Promise<{ script: string; source: 'ia' | 'plantilla' }> =>
    api.post(`/authority-builder/actions/${id}/personalize`).then(r => r.data),

  preview: (id: string): Promise<ActionPreview> =>
    api.get<ActionPreview>(`/authority-builder/actions/${id}/preview`).then(r => r.data),

  run: (id: string, body: { confirm?: boolean; conversation_ids?: string[] } = {}):
    Promise<{ executed: boolean; detail: string; sent?: number; failed?: number }> =>
    api.post(`/authority-builder/actions/${id}/run`, body).then(r => r.data),
}

export interface CampaignRecipient {
  conversation_id: string
  channel_connection_id: string
  name: string
  contact: string | null
  platform: string
  last_message_at: string | null
}

export interface ActionPreview {
  executable: boolean
  reason?: string
  needs_confirmation?: boolean
  recipients?: CampaignRecipient[]
  script?: string | null
  warning?: string
  detail?: string
}

/** The label comes from the backend's executable registry, so "La hace SellIA"
 *  is only ever shown where there is a real automation behind the button. */
export const MODE_LABEL: Record<ActionMode, { label: string; className: string }> = {
  automatic: { label: 'La ejecuta SellIA', className: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  assisted: { label: 'SellIA lo prepara y vos confirmás', className: 'bg-blue-50 text-blue-700 border-blue-200' },
  manual: { label: 'Lo hacés vos', className: 'bg-slate-50 text-slate-600 border-slate-200' },
}

export const pillarColor = (score: number): string =>
  score >= 70 ? 'bg-emerald-500' : score >= 40 ? 'bg-amber-500' : 'bg-red-500'

export const scoreTone = (score: number): string =>
  score >= 70 ? 'text-emerald-600' : score >= 40 ? 'text-amber-600' : 'text-red-600'
