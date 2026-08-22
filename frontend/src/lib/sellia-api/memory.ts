/**
 * User Memory API — Persistent user profile & preferences
 */

import { api } from './client'

export interface UserMemoryResponse {
  id: string
  user_id: string
  preferred_language: string
  preferred_tone: string
  industry_focus: string | null
  business_stage: string | null
  primary_business_type: string | null
  target_audience_summary: string | null
  key_challenges: string[]
  key_interests: string[]
  technologies_used: string[]
  total_conversations: number
  total_messages: number
  favorite_agents: Array<{
    agent_id: string
    agent_name: string
    count: number
    first_used: string
    last_used: string
  }>
  frequently_asked_topics: string[]
  engagement_score: number
  satisfaction_score: number
  churn_risk_score: number
  lifetime_value_estimate: string
  last_active_business_id: string | null
  last_active_conversation_id: string | null
  last_active_agent_id: string | null
  created_at: string | null
  updated_at: string | null
  last_activity_at: string | null
}

export interface UserMemoryEvent {
  id: string
  user_id: string
  event_type: string
  event_data: Record<string, any>
  conversation_id: string | null
  business_id: string | null
  agent_id: string | null
  created_at: string | null
}

export interface UserPreference {
  id: string
  user_id: string
  preference_key: string
  preference_value: Record<string, any>
  created_at: string | null
  updated_at: string | null
}

export const userMemoryApi = {
  // Get current user's memory
  getMemory: () =>
    api.get<UserMemoryResponse>('/memory/me').then((r) => r.data),

  // Update user's memory
  updateMemory: (updates: {
    preferred_language?: string
    preferred_tone?: string
    industry_focus?: string
    business_stage?: string
    primary_business_type?: string
    target_audience_summary?: string
    key_challenges?: string[]
    key_interests?: string[]
    technologies_used?: string[]
    notification_frequency?: string
    email_notifications_enabled?: boolean
    last_active_business_id?: string
    last_active_conversation_id?: string
    last_active_agent_id?: string
  }) =>
    api.patch<UserMemoryResponse>('/memory/me', updates).then((r) => r.data),

  // Log a memory event
  logEvent: (eventType: string, eventData: Record<string, any>, options?: {
    conversation_id?: string
    business_id?: string
    agent_id?: string
  }) =>
    api.post<UserMemoryEvent>('/memory/events', {
      event_type: eventType,
      event_data: eventData,
      ...options,
    }).then((r) => r.data),

  // Add interest to memory
  addInterest: (interest: string) =>
    api.post<UserMemoryResponse>(`/memory/interests/${interest}`).then((r) => r.data),

  // Add challenge to memory
  addChallenge: (challenge: string) =>
    api.post<UserMemoryResponse>(`/memory/challenges/${challenge}`).then((r) => r.data),

  // Set a preference
  setPreference: (preferenceKey: string, preferenceValue: Record<string, any>) =>
    api.post<UserPreference>('/memory/preferences', {
      preference_key: preferenceKey,
      preference_value: preferenceValue,
    }).then((r) => r.data),

  // Get a preference
  getPreference: (preferenceKey: string) =>
    api.get<UserPreference>(`/memory/preferences/${preferenceKey}`).then((r) => r.data),

  // Get recent events
  getRecentEvents: (limit = 50) =>
    api.get<UserMemoryEvent[]>('/memory/events', { params: { limit } }).then((r) => r.data),
}
