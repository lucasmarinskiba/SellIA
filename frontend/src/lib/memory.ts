import { api } from './api'

/**
 * User Memory API — persistent per-user profile, interests, challenges,
 * preferences and event log. Backend: backend/app/api/v1/memory.py.
 *
 * Uses the same cookie-authenticated `api` client as the rest of the
 * dashboard (httpOnly access_token cookie + CSRF header) — the backend's
 * auth dependency accepts both that cookie and an Authorization: Bearer
 * header, so this works without any token handling here.
 */

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

export interface MemoryUpdate {
  preferred_language?: string
  preferred_tone?: string
  industry_focus?: string
  business_stage?: string
  primary_business_type?: string
  target_audience_summary?: string
  key_challenges?: string[]
  key_interests?: string[]
  technologies_used?: string[]
  favorite_agents?: string[]
  frequently_asked_topics?: string[]
}

export const memoryApi = {
  // Get (and lazily create) the current user's memory profile
  getMemory: (): Promise<UserMemoryResponse> =>
    api.get('/memory/me').then((r) => r.data),

  // Update fields on the memory profile. Returns only a status ack —
  // re-fetch getMemory() if you need the updated record.
  updateMemory: (updates: MemoryUpdate): Promise<{ status: string; user_id: string }> =>
    api.patch('/memory/me', updates).then((r) => r.data),

  // Log a memory event. `data` becomes the event's event_data JSONB payload.
  logEvent: (
    eventType: string,
    data: Record<string, any> = {}
  ): Promise<{ status: string; total_messages: number }> =>
    api.post('/memory/events', { event_type: eventType, data }).then((r) => r.data),

  // Add an interest (idempotent — no-ops if already present)
  addInterest: (interest: string): Promise<{ status: string; interests: string[] }> =>
    api.post(`/memory/interests/${encodeURIComponent(interest)}`).then((r) => r.data),

  // Add a challenge (idempotent — no-ops if already present)
  addChallenge: (challenge: string): Promise<{ status: string; challenges: string[] }> =>
    api.post(`/memory/challenges/${encodeURIComponent(challenge)}`).then((r) => r.data),

  // Remove an interest client-side by re-writing the full list (no dedicated
  // backend endpoint for removal — PATCH /me replaces the whole array)
  setInterests: (interests: string[]): Promise<{ status: string; user_id: string }> =>
    api.patch('/memory/me', { key_interests: interests }).then((r) => r.data),

  setChallenges: (challenges: string[]): Promise<{ status: string; user_id: string }> =>
    api.patch('/memory/me', { key_challenges: challenges }).then((r) => r.data),

  // Set a preference. Value can be any JSON-serializable type.
  setPreference: (key: string, value: unknown): Promise<{ status: string; key: string }> =>
    api.post('/memory/preferences', { key, value }).then((r) => r.data),

  // Get a single preference's value (null if unset)
  getPreference: (key: string): Promise<unknown> =>
    api.get(`/memory/preferences/${encodeURIComponent(key)}`).then((r) => r.data.value),

  // Get recent events, most recent first
  getRecentEvents: (limit = 50): Promise<UserMemoryEvent[]> =>
    api
      .get('/memory/events', { params: { limit } })
      .then((r) => r.data.events as UserMemoryEvent[]),
}
