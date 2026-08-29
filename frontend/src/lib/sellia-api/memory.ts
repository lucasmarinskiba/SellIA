/**
 * User Memory API — Persistent user profile & preferences
 *
 * Field names and response shapes here are matched against the live
 * backend (backend/app/api/v1/memory.py), verified by hand against
 * production on 2026-08-29 — not against the original design docs,
 * which had drifted from what the endpoints actually accept/return.
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
  favorite_agents: string[]
  frequently_asked_topics: string[]
  engagement_score: number
  satisfaction_score: number
  churn_risk_score: number
  lifetime_value_estimate: string
  created_at: string | null
  updated_at: string | null
}

export interface UserMemoryEvent {
  id: string
  event_type: string
  event_data: Record<string, any>
  created_at: string | null
}

export const userMemoryApi = {
  // Get (and lazily create) the current user's memory profile
  getMemory: () =>
    api.get<UserMemoryResponse>('/memory/me').then((r) => r.data),

  // Update fields on the memory profile. Returns only a status ack —
  // re-fetch getMemory() if you need the updated record.
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
    total_conversations?: number
    favorite_agents?: string[]
    frequently_asked_topics?: string[]
  }) =>
    api
      .patch<{ status: string; user_id: string }>('/memory/me', updates)
      .then((r) => r.data),

  // Log a memory event. `data` becomes the event's event_data JSONB payload.
  logEvent: (eventType: string, data: Record<string, any> = {}) =>
    api
      .post<{ status: string; total_messages: number }>('/memory/events', {
        event_type: eventType,
        data,
      })
      .then((r) => r.data),

  // Add an interest (idempotent — no-ops if already present)
  addInterest: (interest: string) =>
    api
      .post<{ status: string; interests: string[] }>(
        `/memory/interests/${encodeURIComponent(interest)}`
      )
      .then((r) => r.data),

  // Add a challenge (idempotent — no-ops if already present)
  addChallenge: (challenge: string) =>
    api
      .post<{ status: string; challenges: string[] }>(
        `/memory/challenges/${encodeURIComponent(challenge)}`
      )
      .then((r) => r.data),

  // Set a preference. Value can be any JSON-serializable type.
  setPreference: (key: string, value: unknown) =>
    api
      .post<{ status: string; key: string }>('/memory/preferences', {
        key,
        value,
      })
      .then((r) => r.data),

  // Get a single preference's value (null if unset)
  getPreference: (key: string) =>
    api
      .get<{ key: string; value: unknown }>(
        `/memory/preferences/${encodeURIComponent(key)}`
      )
      .then((r) => r.data.value),

  // Get recent events, most recent first
  getRecentEvents: (limit = 50) =>
    api
      .get<{ events: UserMemoryEvent[]; count: number }>('/memory/events', {
        params: { limit },
      })
      .then((r) => r.data.events),
}
