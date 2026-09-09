/**
 * Real web presence: the URLs the account actually sells from, and the real
 * audits of those pages.
 *
 * Mirrors backend/app/domains/web_presence/. Every number that arrives here was
 * measured by fetching the page server-side — there is no estimated field in
 * these types, and anything the backend could not verify comes back as an
 * explicit `unverifiable_reason` instead of a silent pass.
 */

import { api } from './api'

export type LinkKind = 'website' | 'social' | 'marketplace' | 'other'
export type IssueSeverity = 'critical' | 'warning' | 'info'

export interface PlatformOption {
  platform: string
  kind: LinkKind
  label: string
}

export interface SeoIssue {
  severity: IssueSeverity
  key: string
  title: string
  detail: string
  fix: string
}

export interface PageAudit {
  title: string | null
  title_length: number
  meta_description: string | null
  meta_description_length: number
  canonical: string | null
  robots: string | null
  lang: string | null
  has_viewport: boolean
  h1: string[]
  h2_count: number
  h3_count: number
  images_total: number
  images_without_alt: number
  internal_links: number
  external_links: number
  external_hosts: string[]
  json_ld_types: string[]
  json_ld_invalid: number
  json_ld_same_as: string[]
  open_graph: Record<string, string>
  twitter_card: Record<string, string>
  word_count: number
  is_https: boolean
  issues: SeoIssue[]
}

export interface BusinessLink {
  id: string
  platform: string
  kind: LinkKind
  url: string
  label: string | null
  is_primary: boolean
  last_checked_at: string | null
  http_status: number | null
  final_url: string | null
  response_ms: number | null
  content_bytes: number | null
  fetch_error: string | null
  seo_score: number | null
  audit: PageAudit | null
}

export interface SeoReportPage {
  id: string
  platform: string
  kind: LinkKind
  url: string
  is_primary: boolean
  checked_at: string | null
  http_status: number | null
  response_ms: number | null
  score: number | null
  unverifiable_reason: string | null
  issues: SeoIssue[]
  title: string | null
  word_count: number | null
  json_ld_types: string[]
}

export interface SeoReport {
  links_total: number
  pages_analyzed: number
  average_score: number | null
  pages: SeoReportPage[]
  priorities: { key: string; title: string; severity: IssueSeverity; fix: string; pages: number }[]
  generated_at: string
}

export interface AuthorityProfile {
  id: string
  platform: string
  kind: LinkKind
  url: string
  linked_from_hub: boolean
  declared_same_as: boolean
  links_back_to_hub: boolean | null
  unverifiable_reason: string | null
}

export interface AuthorityReport {
  hub: BusinessLink | null
  profiles: AuthorityProfile[]
  checks: { key: string; title: string; passed: boolean; detail: string }[]
  score: number
  generated_at: string
}

export const webPresenceApi = {
  platforms: (): Promise<PlatformOption[]> =>
    api.get<{ platforms: PlatformOption[] }>('/web-presence/platforms').then(r => r.data.platforms),

  listLinks: (): Promise<BusinessLink[]> =>
    api.get<{ links: BusinessLink[] }>('/web-presence/links').then(r => r.data.links),

  addLink: (payload: {
    platform: string
    url: string
    label?: string
    is_primary?: boolean
  }): Promise<BusinessLink> =>
    api.post<BusinessLink>('/web-presence/links', payload).then(r => r.data),

  deleteLink: (id: string): Promise<void> =>
    api.delete(`/web-presence/links/${id}`).then(() => undefined),

  auditLink: (id: string): Promise<BusinessLink> =>
    api.post<BusinessLink>(`/web-presence/links/${id}/audit`).then(r => r.data),

  auditAll: (): Promise<BusinessLink[]> =>
    api.post<{ links: BusinessLink[] }>('/web-presence/audit-all').then(r => r.data.links),

  seoReport: (): Promise<SeoReport> =>
    api.get<SeoReport>('/web-presence/seo-report').then(r => r.data),

  authorityReport: (): Promise<AuthorityReport> =>
    api.get<AuthorityReport>('/web-presence/authority-report').then(r => r.data),

  structuredData: (): Promise<{ available: boolean; reason?: string; json_ld?: Record<string, unknown> }> =>
    api.get<{ available: boolean; reason?: string; json_ld?: Record<string, unknown> }>(
      '/web-presence/structured-data',
    ).then(r => r.data),

  analyzeUrl: (url: string): Promise<{
    ok: boolean
    url: string
    final_url?: string
    http_status: number | null
    response_ms: number
    error?: string
    score?: number
    audit?: PageAudit
  }> => api.post('/web-presence/analyze-url', { url }).then(r => r.data),
}

export const SEVERITY_STYLE: Record<IssueSeverity, { label: string; chip: string; dot: string }> = {
  critical: { label: 'Crítico', chip: 'bg-red-50 text-red-700 border-red-200', dot: 'bg-red-500' },
  warning: { label: 'A mejorar', chip: 'bg-amber-50 text-amber-700 border-amber-200', dot: 'bg-amber-500' },
  info: { label: 'Menor', chip: 'bg-slate-50 text-slate-600 border-slate-200', dot: 'bg-slate-400' },
}

export const scoreColor = (score: number | null): string => {
  if (score === null) return 'text-slate-400'
  if (score >= 80) return 'text-emerald-600'
  if (score >= 50) return 'text-amber-600'
  return 'text-red-600'
}
