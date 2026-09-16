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
}
