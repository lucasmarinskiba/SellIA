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

export interface TermProfile {
  top_terms: { term: string; score: number; in_title: boolean; in_body: boolean }[]
  title_terms: string[]
  promised_not_delivered: string[]
  distinct_terms: number
  body_tokens: number
}

export interface SiteFiles {
  origin: string
  robots_found: boolean
  robots_url: string | null
  robots_status: number | null
  blocks_this_page: boolean
  blocking_rule: string | null
  sitemaps_declared: string[]
  sitemap_checked: string | null
  sitemap_found: boolean
  sitemap_is_index: boolean
  sitemap_url_count: number
  contains_this_page: boolean | null
  notes: string[]
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
  terms: TermProfile | null
  site_files: SiteFiles | null
}

export interface SeoDuplicate {
  kind: 'title' | 'description'
  value: string
  urls: string[]
  fix: string
}

export interface SeoHistoryPoint {
  date: string
  average_score: number
  pages: number
  critical_issues: number
}

export interface SeoReport {
  links_total: number
  pages_analyzed: number
  average_score: number | null
  pages: SeoReportPage[]
  priorities: { key: string; title: string; severity: IssueSeverity; fix: string; pages: number }[]
  duplicates: SeoDuplicate[]
  history: SeoHistoryPoint[]
  generated_at: string
}

export interface CompareRow {
  label: string
  mine: number | null
  theirs: number | null
  higher_is_better: boolean
}

export interface CompareResult {
  ok: boolean
  error?: string
  mine?: { url: string; score: number | null; title: string | null }
  theirs?: { url: string; score: number | null; title: string | null }
  rows?: CompareRow[]
  topics_they_cover?: string[]
  their_schema?: string[]
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

  compare: (url: string): Promise<CompareResult> =>
    api.post<CompareResult>('/web-presence/compare', { url }).then(r => r.data),

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
