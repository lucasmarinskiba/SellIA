/**
 * Website API client — Tier 1 onboarding + website builder
 */

export interface Website {
  id: string
  business_id: string
  template: 'MINIMAL' | 'CLASSIC' | 'MODERN' | 'ECOMMERCE' | 'PORTFOLIO'
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'
  title?: string
  description?: string
  hero_image_url?: string
  meta_title?: string
  meta_description?: string
  meta_keywords?: string
  og_image_url?: string
  config: Record<string, any>
  pages: Record<string, any>
  domain?: Domain
  created_at: string
  updated_at: string
  published_at?: string
}

export interface Domain {
  id: string
  website_id: string
  subdomain: string
  custom_domain?: string
  is_primary: boolean
  is_verified: boolean
  dns_records: Record<string, any>
  created_at: string
  updated_at: string
}

export interface OnboardingRequest {
  business_name: string
  business_description: string
  website_template: string
  subdomain: string
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const websites = {
  /**
   * Complete onboarding flow (create business + website + domain)
   */
  completeOnboarding: async (data: OnboardingRequest): Promise<Website> => {
    const res = await fetch(`${API_BASE}/api/v1/websites/onboarding/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data),
    })

    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Error en onboarding')
    }

    return res.json()
  },

  /**
   * Get website for a business
   */
  getWebsite: async (businessId: string): Promise<Website> => {
    const res = await fetch(`${API_BASE}/api/v1/websites/businesses/${businessId}/website`, {
      credentials: 'include',
    })

    if (!res.ok) {
      throw new Error('Error obteniendo website')
    }

    return res.json()
  },

  /**
   * Create website for a business
   */
  createWebsite: async (
    businessId: string,
    data: {
      template: string
      title?: string
      description?: string
      subdomain: string
    }
  ): Promise<Website> => {
    const res = await fetch(`${API_BASE}/api/v1/websites/businesses/${businessId}/website`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data),
    })

    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Error creando website')
    }

    return res.json()
  },

  /**
   * Update website
   */
  updateWebsite: async (
    businessId: string,
    data: Partial<Website>
  ): Promise<Website> => {
    const res = await fetch(`${API_BASE}/api/v1/websites/businesses/${businessId}/website`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data),
    })

    if (!res.ok) {
      throw new Error('Error actualizando website')
    }

    return res.json()
  },

  /**
   * Publish website
   */
  publishWebsite: async (businessId: string): Promise<Website> => {
    const res = await fetch(`${API_BASE}/api/v1/websites/businesses/${businessId}/website/publish`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
    })

    if (!res.ok) {
      throw new Error('Error publicando website')
    }

    return res.json()
  },

  /**
   * Get domain info
   */
  getDomain: async (businessId: string): Promise<Domain> => {
    const res = await fetch(`${API_BASE}/api/v1/websites/businesses/${businessId}/domain`, {
      credentials: 'include',
    })

    if (!res.ok) {
      throw new Error('Error obteniendo dominio')
    }

    return res.json()
  },

  /**
   * Update domain
   */
  updateDomain: async (
    businessId: string,
    data: { custom_domain?: string; is_verified?: boolean }
  ): Promise<Domain> => {
    const res = await fetch(`${API_BASE}/api/v1/websites/businesses/${businessId}/domain`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data),
    })

    if (!res.ok) {
      throw new Error('Error actualizando dominio')
    }

    return res.json()
  },
}
