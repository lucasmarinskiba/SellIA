export type ChannelPlatform =
  | 'whatsapp'
  | 'email'
  | 'instagram'
  | 'messenger'
  | 'telegram'
  | 'linkedin'
  | 'webchat'
  | 'mercadolibre'
  | 'facebook_ads'
  | 'meta_ads'
  | 'google_ads'
  | 'shopify'
  | 'tiktok_ads'
  | 'amazon'
  | 'beacons'
  | 'tiktok'

export type ChannelStatus = 'connected' | 'pending' | 'error' | 'disabled'

export interface ChannelConnection {
  id: string
  business_id: string
  platform: ChannelPlatform
  name: string
  status: ChannelStatus
  status_message: string | null
  webhook_url: string | null
  webhook_token: string
  last_sync_at: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface OAuthUrlResponse {
  auth_url: string
}

export interface SyncResult {
  platform: string
  success: boolean
  message: string
  items_synced: number
  synced_at: string
}
