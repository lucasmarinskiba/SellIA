/**
 * Harvey (prospección saliente) API client.
 * Backend: /api/v1/businesses/{businessId}/harvey
 */
import { api } from '@/lib/api'

const base = (bid: string) => `/businesses/${bid}/harvey`

export interface HarveyProfile {
  id: string
  business_id: string
  is_enabled: boolean
  persona_name: string
  persona_role: string
  tone: string
  language: string
  offer: string
  benefits: string[]
  icp: { keywords?: string[]; locations?: string[]; [k: string]: unknown }
  postal_address: string
  opt_out_line: string
  do_not_contact: string[]
  max_daily_drafts: number
  max_daily_sends: number
  auto_draft: boolean
  auto_discover: boolean
  max_daily_discoveries: number
  send_window_start: number
  send_window_end: number
  send_timezone: string
  send_weekdays_only: boolean
  warmup_started_at: string | null
  inbox_synced_at: string | null
  last_cycle_at: string | null
  last_cycle: Record<string, unknown>
  last_discovery_at: string | null
}

export type HarveyProfileUpdate = Partial<
  Omit<
    HarveyProfile,
    'id' | 'business_id' | 'warmup_started_at' | 'inbox_synced_at' | 'last_cycle_at' | 'last_cycle' | 'last_discovery_at'
  >
>

export interface HarveyStatus {
  email_connected: boolean
  model_available: boolean
  search_available: boolean
  search_provider: 'brave' | 'google' | null
  has_brave_key: boolean
  has_google_key: boolean
  in_send_window: boolean
  sent_today: number
  send_cap_today: number
  drafts_today: number
  discovered_today: number
  prospects: Record<string, number>
  outbox: Record<string, number>
  replies: number
}

export interface HarveyProspect {
  id: string
  email: string
  first_name: string
  last_name: string
  title: string
  company: string
  website: string
  notes: string
  email_status: string
  is_company_inbox: boolean
  source: string
  source_url: string
  status: string
  created_at: string
}

export interface ProspectIn {
  email: string
  first_name?: string
  last_name?: string
  company?: string
}

export interface OutboxItem {
  id: string
  prospect_id: string
  step: number
  kind: 'sequence' | 'reply'
  reply_id: string | null
  to_email: string
  subject: string
  body: string
  status: string
  gate_reasons: string[]
  sent_at: string | null
  send_attempts: number
  send_error: string
  created_at: string
}

export interface HarveyReply {
  id: string
  prospect_id: string
  body: string
  classification: string
  needs_human: boolean
  draft_answer: string
  created_at: string
}

export interface DiscoverSite {
  url: string
  outcome: 'added' | 'skipped' | 'exists' | 'no_email' | 'error'
  detail: string
}

export interface DiscoverResult {
  counts: Record<string, number>
  sites: DiscoverSite[]
}

type Counts = { counts: Record<string, number> }

/** The backend's human-readable reason (Spanish) when there is one. */
export const errMsg = (e: unknown): string => {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (typeof detail === 'string') return detail
  return e instanceof Error ? e.message : 'Algo salió mal'
}

export interface ImportCsvResult {
  rows: number
  created: number
  skipped: { email: string; reason: string }[]
  rejected: { row: string; reason: string }[]
}

export type CompetitorKind = 'direct' | 'indirect' | 'own'

export interface Competitor {
  id: string
  name: string
  url: string
  kind: CompetitorKind
  snapshot: { prices?: string[]; offers?: string[]; headlines?: string[]; title?: string }
  last_scanned_at: string | null
  last_error: string
}

export interface CompetitiveBrief {
  brief: { summary?: string; gaps?: string[]; opportunities?: string[]; angles?: string[]; icp_hints?: string[]; source?: string }
  generated_at: string | null
}

export interface WeeklySummary {
  since: string
  sent: number
  prospects_added: number
  prospects_total: number
  prospects_new: number
  replies: { total: number; interested: number }
  pending_review: number
  needs_you: number
  deals: { created: number; won: number; won_value: number }
  next_steps: string[]
}

export const harvey = {
  weeklySummary: (bid: string) => api.get<WeeklySummary>(`${base(bid)}/weekly-summary`).then((r) => r.data),
  competitors: (bid: string) => api.get<Competitor[]>(`${base(bid)}/competitors`).then((r) => r.data),
  addCompetitor: (bid: string, body: { url: string; kind: CompetitorKind; name?: string }) =>
    api.post<Competitor>(`${base(bid)}/competitors`, body).then((r) => r.data),
  scanCompetitor: (bid: string, id: string) =>
    api.post<Competitor>(`${base(bid)}/competitors/${id}/scan`).then((r) => r.data),
  deleteCompetitor: (bid: string, id: string) => api.delete(`${base(bid)}/competitors/${id}`).then(() => undefined),
  competitiveBrief: (bid: string) => api.get<CompetitiveBrief>(`${base(bid)}/competitors/brief`).then((r) => r.data),
  analyzeCompetitors: (bid: string) => api.post<CompetitiveBrief>(`${base(bid)}/competitors/analyze`).then((r) => r.data),
  setDiscoveryKeys: (
    bid: string,
    body: { brave_api_key?: string; google_places_api_key?: string; search_provider?: 'brave' | 'google' },
  ) => api.put<HarveyStatus>(`${base(bid)}/discovery-keys`, body).then((r) => r.data),
  importCsv: (bid: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api
      .post<ImportCsvResult>(`${base(bid)}/prospects/import-csv`, form, { headers: { 'Content-Type': 'multipart/form-data' } })
      .then((r) => r.data)
  },
  status: (bid: string) => api.get<HarveyStatus>(`${base(bid)}/status`).then((r) => r.data),
  profile: (bid: string) => api.get<HarveyProfile>(`${base(bid)}/profile`).then((r) => r.data),
  updateProfile: (bid: string, body: HarveyProfileUpdate) =>
    api.patch<HarveyProfile>(`${base(bid)}/profile`, body).then((r) => r.data),

  prospects: (bid: string) =>
    api.get<HarveyProspect[]>(`${base(bid)}/prospects`, { params: { limit: 500 } }).then((r) => r.data),
  addProspects: (bid: string, prospects: ProspectIn[]) =>
    api
      .post<{ created: HarveyProspect[]; skipped: { email: string; reason: string }[] }>(`${base(bid)}/prospects`, {
        prospects,
      })
      .then((r) => r.data),
  verify: (bid: string, ids: string[], verified: boolean) =>
    api.post<Counts>(`${base(bid)}/prospects/verify`, { prospect_ids: ids, verified }).then((r) => r.data),
  discover: (bid: string, body: { urls: string[]; queries: string[] }) =>
    api.post<DiscoverResult>(`${base(bid)}/prospects/discover`, body).then((r) => r.data),
  draft: (bid: string, prospectId: string, step = 1) =>
    api.post<OutboxItem>(`${base(bid)}/prospects/${prospectId}/draft`, null, { params: { step } }).then((r) => r.data),

  outbox: (bid: string) =>
    api.get<OutboxItem[]>(`${base(bid)}/outbox`, { params: { limit: 200 } }).then((r) => r.data),
  edit: (bid: string, id: string, subject: string, body: string) =>
    api.patch<OutboxItem>(`${base(bid)}/outbox/${id}`, { subject, body }).then((r) => r.data),
  approve: (bid: string, id: string) => api.post<OutboxItem>(`${base(bid)}/outbox/${id}/approve`).then((r) => r.data),
  reject: (bid: string, id: string) => api.post<OutboxItem>(`${base(bid)}/outbox/${id}/reject`).then((r) => r.data),
  send: (bid: string, id: string) => api.post<OutboxItem>(`${base(bid)}/outbox/${id}/send`).then((r) => r.data),
  sendApproved: (bid: string) => api.post<Counts>(`${base(bid)}/outbox/send-approved`).then((r) => r.data),
  runSequences: (bid: string) => api.post<Counts>(`${base(bid)}/sequences/run`).then((r) => r.data),
  syncInbox: (bid: string) => api.post<Counts>(`${base(bid)}/inbox/sync`).then((r) => r.data),

  replies: (bid: string) => api.get<HarveyReply[]>(`${base(bid)}/replies`).then((r) => r.data),
  answerReply: (bid: string, replyId: string) =>
    api.post<OutboxItem>(`${base(bid)}/replies/${replyId}/answer`).then((r) => r.data),
}
