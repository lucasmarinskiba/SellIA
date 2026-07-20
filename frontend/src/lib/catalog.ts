import { api } from './api'

export interface CatalogItem {
  id: string
  business_id: string
  type: 'service' | 'good' | 'digital'
  name: string
  description: string | null
  price: string
  currency: string
  stock: number | null
  is_available: boolean
  extra_data: Record<string, any>
  images: string[]
  tags: string[]
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CreateCatalogItemData {
  type: 'service' | 'good' | 'digital'
  name: string
  description?: string
  price: number
  currency?: string
  stock?: number
  is_available?: boolean
  extra_data?: Record<string, any>
  images?: string[]
  tags?: string[]
}

export interface UpdateCatalogItemData {
  name?: string
  description?: string | null
  price?: number
  currency?: string
  stock?: number | null
  is_available?: boolean
  extra_data?: Record<string, any>
  images?: string[]
  tags?: string[]
  is_active?: boolean
}

export const catalogApi = {
  list: async (businessId: string): Promise<CatalogItem[]> => {
    const res = await api.get(`/catalog/${businessId}/items`)
    return res.data
  },
  get: async (businessId: string, itemId: string): Promise<CatalogItem> => {
    const res = await api.get(`/catalog/${businessId}/items/${itemId}`)
    return res.data
  },
  create: async (businessId: string, data: CreateCatalogItemData): Promise<CatalogItem> => {
    const res = await api.post(`/catalog/${businessId}/items`, data)
    return res.data
  },
  update: async (businessId: string, itemId: string, data: UpdateCatalogItemData): Promise<CatalogItem> => {
    const res = await api.put(`/catalog/${businessId}/items/${itemId}`, data)
    return res.data
  },
  delete: async (businessId: string, itemId: string): Promise<void> => {
    await api.delete(`/catalog/${businessId}/items/${itemId}`)
  },
}
