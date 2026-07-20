import { api } from './api'
import { ChannelPlatform } from '@/types/channels'
export type ChannelStatus = 'pending' | 'connected' | 'error' | 'disabled'

export interface ChannelConnection {
  id: string
  business_id: string
  platform: ChannelPlatform
  name: string
  credentials: Record<string, any>
  settings: Record<string, any>
  status: ChannelStatus
  status_message: string | null
  webhook_url: string | null
  last_sync_at: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CreateChannelData {
  platform: ChannelPlatform
  name: string
  credentials?: Record<string, any>
  settings?: Record<string, any>
}

export interface UpdateChannelData {
  name?: string
  credentials?: Record<string, any>
  settings?: Record<string, any>
  status?: ChannelStatus
  is_active?: boolean
}

export const channelsApi = {
  list: async (businessId: string): Promise<ChannelConnection[]> => {
    const res = await api.get(`/businesses/${businessId}/channels`)
    return res.data
  },
  get: async (businessId: string, channelId: string): Promise<ChannelConnection> => {
    const res = await api.get(`/businesses/${businessId}/channels/${channelId}`)
    return res.data
  },
  create: async (businessId: string, data: CreateChannelData): Promise<ChannelConnection> => {
    const res = await api.post(`/businesses/${businessId}/channels`, data)
    return res.data
  },
  update: async (businessId: string, channelId: string, data: UpdateChannelData): Promise<ChannelConnection> => {
    const res = await api.put(`/businesses/${businessId}/channels/${channelId}`, data)
    return res.data
  },
  delete: async (businessId: string, channelId: string): Promise<void> => {
    await api.delete(`/businesses/${businessId}/channels/${channelId}`)
  },
  test: async (businessId: string, channelId: string): Promise<{ status: string; valid: boolean; detail?: string }> => {
    const res = await api.post(`/businesses/${businessId}/channels/${channelId}/test`)
    return res.data
  },
}
