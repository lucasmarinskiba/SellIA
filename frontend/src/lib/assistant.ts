import { api } from './api'

export type AssistantActionType =
  | 'ASK_CLARIFICATION'
  | 'SUGGEST_AGENTS'
  | 'CREATE_CONVERSATION'
  | 'GENERATE_CONTENT'
  | 'NAVIGATE'
  | 'CREATE_SEQUENCE'
  | 'SETUP_AUTOMATION'
  | 'GENERATE_PLAYBOOK'
  | 'ANALYZE_BUSINESS'
  | 'CREATE_CONTENT_CALENDAR'
  | 'MULTI_AGENT_PANEL'
  | 'COMPUTER_USE'
  | 'ACTIVATE_PIPELINE_AGENT'
  | 'NEGOTIATE'
  | 'BUILD_OFFER'
  | 'SYSTEM_HEALTH'

export interface AssistantAction {
  action: AssistantActionType
  response: string
  options?: string[]
  suggested_agents?: string[]
  agent_slug?: string
  context_hint?: string
  content_request?: string
  target?: string
  conversation_id?: string
  sellia_conversation_id?: string
  personality?: {
    id: string
    slug: string
    name: string
    emoji: string
    color: string
  }
  // Complex action fields
  sequence_type?: string
  sequence_name?: string
  steps?: Array<{ step: number; delay: string; subject?: string; content: string }>
  automation_name?: string
  trigger?: string
  actions?: string[]
  playbook_type?: string
  topic?: string
  analysis_type?: string
  period?: string
  platforms?: string[]
  topics?: string[]
  agent_slugs?: string[]
  question?: string
  // Execution results
  execution_result?: any
  execution_error?: string
  // Computer Use
  session_id?: string
  ws_url?: string
  task?: string
  // Pipeline Agent
  stage?: string
  deal_id?: string
  context?: Record<string, any>
  // Negotiate
  expert?: string
  situation?: string
  // Build Offer
  product_name?: string
  target_audience?: string
  price_point?: number
  pain_points?: string[]
  // System Health
  include_recommendations?: boolean
}

export interface AssistantChatRequest {
  message: string
  business_id?: string
  context?: Record<string, any>
  conversation_history?: Array<{ role: 'user' | 'assistant'; content: string }>
  conversation_id?: string
}

export interface SellIAConversation {
  id: string
  title: string
  message_count: number
  created_at: string
  updated_at: string
}

export interface StreamEvent {
  type: 'token' | 'action' | 'error'
  content?: string
  data?: AssistantAction
  message?: string
}

export const assistantApi = {
  chat: (data: AssistantChatRequest) =>
    api.post<AssistantAction>('/assistant/chat', data).then(r => r.data),

  chatStream: (
    data: AssistantChatRequest,
    onEvent: (event: StreamEvent) => void,
    onComplete: () => void,
    onError: (error: Error) => void
  ) => {
    const params = new URLSearchParams()
    params.append('message', data.message)
    if (data.business_id) params.append('business_id', data.business_id)
    if (data.conversation_id) params.append('conversation_id', data.conversation_id)
    if (data.conversation_history) {
      params.append('conversation_history', JSON.stringify(data.conversation_history))
    }

    const eventSource = new EventSource(
      `${api.defaults.baseURL}/assistant/chat/stream?${params.toString()}`
    )

    eventSource.addEventListener('token', (e: MessageEvent) => {
      try {
        const parsed = JSON.parse(e.data)
        onEvent({ type: 'token', content: parsed.content })
      } catch {
        onEvent({ type: 'token', content: e.data })
      }
    })

    eventSource.addEventListener('action', (e: MessageEvent) => {
      try {
        const parsed = JSON.parse(e.data)
        onEvent({ type: 'action', data: parsed.data })
      } catch {
        onEvent({ type: 'error', message: 'Failed to parse action' })
      }
      eventSource.close()
      onComplete()
    })

    eventSource.addEventListener('error', (e: MessageEvent) => {
      try {
        const parsed = JSON.parse(e.data)
        onEvent({ type: 'error', message: parsed.message })
      } catch {
        onEvent({ type: 'error', message: 'Stream error' })
      }
      eventSource.close()
      onError(new Error('Stream error'))
      onComplete()
    })

    eventSource.onerror = () => {
      eventSource.close()
      onError(new Error('Connection error'))
      onComplete()
    }

    return () => eventSource.close()
  },

  getConversations: () =>
    api.get<SellIAConversation[]>('/assistant/conversations').then(r => r.data),

  getConversation: (id: string) =>
    api.get<{ id: string; title: string; messages: any[]; created_at: string; updated_at: string }>(
      `/assistant/conversations/${id}`
    ).then(r => r.data),

  createConversation: (title?: string) =>
    api
      .post<{ id: string; title: string; messages: any[]; created_at: string; updated_at: string }>(
        '/assistant/conversations',
        null,
        { params: { title } }
      )
      .then(r => r.data),

  deleteConversation: (id: string) =>
    api.delete<{ success: boolean; message: string }>(`/assistant/conversations/${id}`).then(r => r.data),

  getAgentsSummary: () =>
    api.get('/assistant/agents-summary').then(r => r.data),
}
