import { api } from './api'

export interface Business {
  id: string
  user_id: string
  name: string
  type: 'services' | 'goods' | 'digital' | 'mixed'
  description: string | null
  config: Record<string, any>
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CreateBusinessData {
  name: string
  type: 'services' | 'goods' | 'digital' | 'mixed'
  description?: string
  config?: Record<string, any>
}

export interface UpdateBusinessData {
  name?: string
  type?: 'services' | 'goods' | 'digital' | 'mixed'
  description?: string | null
  config?: Record<string, any>
  is_active?: boolean
}

export const businessApi = {
  list: async (): Promise<Business[]> => {
    const res = await api.get('/businesses/')
    return res.data
  },
  get: async (id: string): Promise<Business> => {
    const res = await api.get(`/businesses/${id}`)
    return res.data
  },
  create: async (data: CreateBusinessData): Promise<Business> => {
    const res = await api.post('/businesses/', data)
    return res.data
  },
  update: async (id: string, data: UpdateBusinessData): Promise<Business> => {
    const res = await api.put(`/businesses/${id}`, data)
    return res.data
  },
  delete: async (id: string): Promise<void> => {
    await api.delete(`/businesses/${id}`)
  },
}
