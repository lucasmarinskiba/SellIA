import { api } from './api'

export interface AgentPersonality {
  id: string
  slug: string
  name: string
  emoji: string
  tagline: string
  description: string
  expertise: string[]
  color: string
  is_active: boolean
  created_at: string
}

export interface AgentConversation {
  id: string
  user_id: string
  business_id: string
  personality_id: string
  title: string | null
  message_count: number
  is_active: boolean
  created_at: string
  updated_at: string
  personality?: AgentPersonality
}

export interface AgentMessage {
  id: string
  conversation_id: string
  role: string
  content: string
  model_used: string | null
  tokens_used: number | null
  extra_data: Record<string, any>
  created_at: string
}

export interface ChatResponse {
  message: AgentMessage
  conversation_id: string
  tokens_used: number
  action_triggered: string | null
}

export interface AutopilotVoiceConfig {
  personality_slug: string
  voice_personality_slug: string | null
  custom_instructions: string | null
}

export interface AgentConfig {
  id: string
  business_id: string
  personality_id: string
  is_enabled: boolean
  custom_instructions: string | null
  tone_override: string | null
  voice_personality_id: string | null
  extra_data: Record<string, any>
  created_at: string
  updated_at: string
  personality?: AgentPersonality
  voice_personality?: AgentPersonality | null
}

export const agentsApi = {
  getPersonalities: () => api.get<AgentPersonality[]>('/agents/personalities').then(r => r.data),

  getConversations: (businessId?: string) =>
    api.get<AgentConversation[]>('/agents/conversations', { params: { business_id: businessId } }).then(r => r.data),

  createConversation: (data: { business_id: string; personality_id: string; title?: string }) =>
    api.post<AgentConversation>('/agents/conversations', data).then(r => r.data),

  getConversation: (id: string) =>
    api.get<{ id: string; messages: AgentMessage[]; personality?: AgentPersonality } & AgentConversation>(`/agents/conversations/${id}`).then(r => r.data),

  deleteConversation: (id: string) =>
    api.delete(`/agents/conversations/${id}`).then(r => r.data),

  sendMessage: (conversationId: string, content: string) =>
    api.post<ChatResponse>(`/agents/conversations/${conversationId}/chat`, { content }).then(r => r.data),

  // Auto-pilot voice configuration
  getAutopilotVoices: (businessId: string) =>
    api.get<{ configs: Record<string, AutopilotVoiceConfig> }>('/agents/autopilot-voices', { params: { business_id: businessId } }).then(r => r.data),

  createOrUpdateConfig: (businessId: string, data: { personality_id: string; voice_personality_id?: string | null; custom_instructions?: string | null; tone_override?: string | null }) =>
    api.post<AgentConfig>('/agents/configs', data, { params: { business_id: businessId } }).then(r => r.data),
}
