/**
 * SEO API client — Tier 2 meta tags, schema, sitemap, robots.txt
 */

export interface SEOMetadata {
  meta_title: string
  meta_description: string
  meta_keywords: string
  og_image_url: string
}

export interface SEOSchema {
  local_business: any
  organization: any
  breadcrumb_list: any
}

export interface SEOAudit {
  score: number
  passed: number
  total: number
  checks: Record<string, {
    label: string
    passed: boolean
    recommendation: string
  }>
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const seo = {
  /**
   * Get SEO metadata (meta tags)
   */
  getMetadata: async (businessId: string): Promise<SEOMetadata> => {
    const res = await fetch(`${API_BASE}/api/v1/seo/businesses/${businessId}/seo/meta`, {
      credentials: 'include',
    })

    if (!res.ok) {
      throw new Error('Error obteniendo meta tags')
    }

    return res.json()
  },

  /**
   * Update SEO metadata
   */
  updateMetadata: async (businessId: string, data: Partial<SEOMetadata>): Promise<SEOMetadata> => {
    const res = await fetch(`${API_BASE}/api/v1/seo/businesses/${businessId}/seo/meta`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data),
    })

    if (!res.ok) {
      throw new Error('Error actualizando meta tags')
    }

    return res.json()
  },

  /**
   * Get Schema.org markup
   */
  getSchema: async (businessId: string): Promise<SEOSchema> => {
    const res = await fetch(`${API_BASE}/api/v1/seo/businesses/${businessId}/seo/schema`, {
      credentials: 'include',
    })

    if (!res.ok) {
      throw new Error('Error obteniendo schema')
    }

    return res.json()
  },

  /**
   * Get dynamic sitemap.xml
   */
  getSitemap: async (businessId: string): Promise<string> => {
    const res = await fetch(`${API_BASE}/api/v1/seo/businesses/${businessId}/seo/sitemap.xml`, {
      credentials: 'include',
    })

    if (!res.ok) {
      throw new Error('Error obteniendo sitemap')
    }

    return res.text()
  },

  /**
   * Get dynamic robots.txt
   */
  getRobotsTxt: async (businessId: string): Promise<string> => {
    const res = await fetch(`${API_BASE}/api/v1/seo/businesses/${businessId}/seo/robots.txt`, {
      credentials: 'include',
    })

    if (!res.ok) {
      throw new Error('Error obteniendo robots.txt')
    }

    return res.text()
  },

  /**
   * Get SEO audit checklist
   */
  getAudit: async (businessId: string): Promise<SEOAudit> => {
    const res = await fetch(`${API_BASE}/api/v1/seo/businesses/${businessId}/seo/audit`, {
      credentials: 'include',
    })

    if (!res.ok) {
      throw new Error('Error obteniendo auditoría SEO')
    }

    return res.json()
  },
}
