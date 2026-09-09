import { api } from './api'

export type ConversationStatus = 'active' | 'archived' | 'spam'
export type MessageDirection = 'inbound' | 'outbound'
export type MessageStatus = 'sent' | 'delivered' | 'read' | 'failed' | 'pending'

export interface Conversation {
  id: string
  business_id: string
  channel_connection_id: string | null
  external_id: string | null
  lead_name: string | null
  lead_email: string | null
  lead_phone: string | null
  lead_source: string | null
  status: ConversationStatus
  last_message_at: string | null
  metadata: Record<string, any>
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ConversationWithPreview extends Conversation {
  message_count: number
  last_message_preview: string | null
  // Real platform this conversation is happening on -- WhatsApp, Instagram,
  // MercadoLibre (product questions), Amazon, Hotmart, etc. null only if the
  // conversation has no channel_connection_id set (rare/manual entries).
  platform: string | null
  last_direction: MessageDirection | null
  // true once at least one message in this thread was actually sent by the
  // AI bot (see Message.extra_data.generated_by) -- the concrete proof this
  // isn't just a manually-answered thread.
  ai_responded: boolean
}

export interface Message {
  id: string
  conversation_id: string
  direction: MessageDirection
  content: string
  content_type: string
  status: MessageStatus
  external_message_id: string | null
  extra_data: Record<string, any>
  created_at: string
  updated_at: string
}

export interface SendMessageData {
  direction: MessageDirection
  content: string
  content_type?: string
  extra_data?: Record<string, any>
}

export const conversationsApi = {
  list: async (businessId: string, status?: ConversationStatus, platform?: string): Promise<ConversationWithPreview[]> => {
    const params: Record<string, string> = {}
    if (status) params.status = status
    if (platform) params.platform = platform
    const res = await api.get(`/businesses/${businessId}/conversations`, { params })
    return res.data
  },
  get: async (businessId: string, conversationId: string): Promise<Conversation> => {
    const res = await api.get(`/businesses/${businessId}/conversations/${conversationId}`)
    return res.data
  },
  update: async (businessId: string, conversationId: string, data: Partial<Conversation>): Promise<Conversation> => {
    const res = await api.put(`/businesses/${businessId}/conversations/${conversationId}`, data)
    return res.data
  },
  getMessages: async (businessId: string, conversationId: string): Promise<Message[]> => {
    const res = await api.get(`/businesses/${businessId}/conversations/${conversationId}/messages`)
    return res.data
  },
  sendMessage: async (businessId: string, conversationId: string, data: SendMessageData): Promise<Message> => {
    const res = await api.post(`/businesses/${businessId}/conversations/${conversationId}/messages`, data)
    return res.data
  },
}
