import { api } from './api'

export interface PlatformSEOStatus {
  connection_id: string
  platform_name: string
  status: string
  last_sync: string | null
  seo_enabled: boolean
}

export interface PlatformSEOListResponse {
  platforms: PlatformSEOStatus[]
  global_seo_enabled: boolean
}

export interface PublicationLink {
  id: string
  url: string
  title: string
  platform_source: string
  product_id: string | null
  seo_enabled: boolean
}

export interface CreatePublicationLinkRequest {
  url: string
  title: string
  platform_source: string
  product_id?: string | null
}

export type AlgorithmCoverage = 'measured' | 'web_audit' | 'guidance_only'
export type FactorEvidence = 'official' | 'community'

export interface AlgorithmFactor {
  name: string
  evidence: FactorEvidence
  note: string
  measured_by: string[]
}

export interface AlgorithmGuide {
  platform: string
  label: string
  kind: string
  coverage: AlgorithmCoverage
  researched: boolean
  summary: string
  disclosure: string
  factors: AlgorithmFactor[]
  not_measurable: string[]
  playbook: string[]
  in_use?: boolean
}

export interface PositioningAction {
  id: string
  signal_key: string
  severity: 'critical' | 'warning' | 'info'
  message: string
  current_value: number | null
  target_value: number | null
  why: { factor: string; evidence: FactorEvidence; note: string } | null
  platform: string
  affected: number
}

export interface PlatformOverview {
  platform: string
  label: string
  coverage: AlgorithmCoverage
  note: string
  links: number
  scored_links: number
}

export interface UnscoredLink {
  link_id: string
  title: string
  platform: string
  coverage: AlgorithmCoverage
  reason: string
}

export interface PositioningSummary {
  platform_overview: PlatformOverview[]
  unscored_links: UnscoredLink[]
  top_actions: PositioningAction[]
}

export const seoConfigApi = {
  async getGlobalConfig(businessId: string) {
    const res = await api.get<{ id: string; business_id: string; global_seo_enabled: boolean }>(
      `/businesses/${businessId}/seo-config`,
    )
    return res.data
  },

  async toggleGlobalSEO(businessId: string, enabled: boolean) {
    const res = await api.patch(`/businesses/${businessId}/seo-config/global-toggle`, null, {
      params: { enabled },
    })
    return res.data
  },

  async getPlatformsSEOStatus(businessId: string): Promise<PlatformSEOListResponse> {
    const res = await api.get(`/businesses/${businessId}/seo-config/platforms`)
    return res.data
  },

  async togglePlatformSEO(businessId: string, connectionId: string, enabled: boolean) {
    const res = await api.patch(
      `/businesses/${businessId}/seo-config/platforms/${connectionId}/toggle`,
      null,
      { params: { enabled } },
    )
    return res.data
  },

  async listPublicationLinks(businessId: string): Promise<PublicationLink[]> {
    const res = await api.get(`/businesses/${businessId}/seo-config/publication-links`)
    return res.data
  },

  async createPublicationLink(businessId: string, data: CreatePublicationLinkRequest): Promise<PublicationLink> {
    const res = await api.post(`/businesses/${businessId}/seo-config/publication-links`, data)
    return res.data
  },

  async togglePublicationLinkSEO(businessId: string, linkId: string, enabled: boolean) {
    const res = await api.patch(
      `/businesses/${businessId}/seo-config/publication-links/${linkId}/toggle`,
      null,
      { params: { enabled } },
    )
    return res.data
  },

  async deletePublicationLink(businessId: string, linkId: string) {
    const res = await api.delete(`/businesses/${businessId}/seo-config/publication-links/${linkId}`)
    return res.data
  },

  async getPositioningSummary(businessId: string): Promise<PositioningSummary> {
    const res = await api.get(`/businesses/${businessId}/seo-config/positioning/summary`)
    return res.data
  },

  async getAlgorithmGuide(businessId: string): Promise<{ platforms: AlgorithmGuide[] }> {
    const res = await api.get(`/businesses/${businessId}/seo-config/positioning/algorithm-guide`)
    return res.data
  },
}
