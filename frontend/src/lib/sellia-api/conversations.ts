/**
 * SellIA Assistant Conversations API
 */

import { api } from './client'

export interface AssistantConversation {
  id: string
  title: string
  message_count: number
  created_at: string | null
  updated_at: string | null
}

export interface AssistantMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  action?: string
  created_at?: string
}

export interface AssistantConversationDetail {
  id: string
  title: string
  messages: AssistantMessage[]
  created_at: string | null
  updated_at: string | null
}

export interface AssistantChatResponse {
  response: string
  action?: string
  agent_id?: string
  conversation_id?: string
  suggested_next_steps?: string[]
  [key: string]: any
}

export const assistantApi = {
  // List all conversations for current user
  listConversations: () =>
    api.get<AssistantConversation[]>('/assistant/conversations').then((r) => r.data),

  // Get a specific conversation with all messages
  getConversation: (conversationId: string) =>
    api.get<AssistantConversationDetail>(`/assistant/conversations/${conversationId}`).then((r) => r.data),

  // Create a new conversation
  createConversation: (title?: string) =>
    api.post<AssistantConversationDetail>('/assistant/conversations', null, {
      params: title ? { title } : undefined,
    }).then((r) => r.data),

  // Delete (soft-delete) a conversation
  deleteConversation: (conversationId: string) =>
    api.delete(`/assistant/conversations/${conversationId}`).then((r) => r.data),

  // Chat with SellIA Assistant
  chat: (options: {
    message: string
    business_id?: string
    context?: Record<string, any>
    conversation_history?: AssistantMessage[]
    conversation_id?: string
  }) =>
    api.post<AssistantChatResponse>('/assistant/chat', null, {
      params: {
        message: options.message,
        business_id: options.business_id,
        context: options.context ? JSON.stringify(options.context) : undefined,
        conversation_id: options.conversation_id,
      },
      data: options.conversation_history ? { conversation_history: options.conversation_history } : undefined,
    }).then((r) => r.data),

  // Stream chat (if backend supports it via GET with streaming)
  streamChat: async (options: {
    message: string
    business_id?: string
    conversation_id?: string
    onChunk?: (chunk: string) => void
  }) => {
    const response = await api.get('/assistant/chat/stream', {
      params: {
        message: options.message,
        business_id: options.business_id,
        conversation_id: options.conversation_id,
      },
      responseType: 'stream',
    })
    return response.data
  },
}
