/**
 * Chatbots por plataforma.
 *
 * Mirrors backend/app/domains/chatbots/. The sales intelligence (which funnel
 * stage a conversation is in, and which specialist prompt and expert voice to
 * layer on) already lives in the reply engine; what these types carry is the
 * part the seller controls: where the bot speaks, as whom, aimed at what, and
 * when it hands over to a person.
 */

import { api } from './api'

export type BotFocus = 'auto' | 'acquisition' | 'conversion' | 'retention' | 'expansion'

export interface BotStats {
  conversations: number
  inbound: number
  ai_replies: number
  human_replies: number
  waiting: number
}

/** The rules the platform itself imposes, applied by the backend. */
export interface Playbook {
  platform: string
  label: string
  max_chars: number
  allow_links: boolean
  allow_contact_details: boolean
  formatting: string
  register: string
  rules: string[]
  why: string
  is_default: boolean
}

/** What the bot achieved, not how much it typed. */
export interface BotPerformance {
  answered_by_ai: number
  asked: number
  coverage_percent: number | null
  coverage_confidence: 'solid' | 'preliminary' | 'insufficient'
  coverage_reading: string
  median_first_reply_minutes: number | null
  latency_sample: number
  held_for_human: number
  held_reasons: { reason: string; count: number }[]
  orders_after_ai: number
  revenue_after_ai: Record<string, number>
  attribution_note: string
  orders_without_conversation: number
}

export interface ActiveHours {
  from: number
  to: number
  utc_offset: number
}

export interface PlatformBot {
  platform: string
  enabled: boolean
  personality_slug: string | null
  focus: BotFocus
  focus_label: string
  custom_instructions: string | null
  handoff_keywords: string[]
  max_ai_replies: number | null
  active_hours: ActiveHours | null
  after_hours_message: string | null
  escalate_on_frustration: boolean
  /** Hold the reply for a human when it breaks the platform's own rules. */
  hold_on_policy_violation: boolean
  updated_at: string | null
  configured: boolean
  stats: BotStats
  playbook?: Playbook
  performance?: BotPerformance | null
}

export interface BotsOverview {
  bots: PlatformBot[]
  has_business: boolean
  focus_options?: { value: BotFocus; label: string }[]
  generated_at?: string
}

export interface Personality {
  slug: string
  name: string
  emoji: string
  tagline: string
}

export interface TestResult {
  ok: boolean
  reply?: string
  reason?: string
  focus?: string
  /** The untrimmed text, when the platform's budget forced a cut. */
  raw_reply?: string | null
  /** False when this reply would be held for a human instead of sent. */
  would_send?: boolean
  policy_problems?: string[]
  trimmed?: boolean
  playbook?: Playbook
  /** Which parts of the seller's configuration actually fed this reply. */
  brief_sources?: string[]
  brief_missing?: string[]
  within_hours?: boolean
  hours_note?: string | null
}

export const chatbotsApi = {
  list: (): Promise<BotsOverview> =>
    api.get<BotsOverview>('/chatbots').then(r => r.data),

  personalities: (): Promise<Personality[]> =>
    api.get<{ personalities: Personality[] }>('/chatbots/personalities')
      .then(r => r.data.personalities),

  playbooks: (): Promise<{ playbooks: Playbook[]; default: Playbook }> =>
    api.get<{ playbooks: Playbook[]; default: Playbook }>('/chatbots/playbooks').then(r => r.data),

  update: (platform: string, body: Partial<{
    enabled: boolean
    personality_slug: string | null
    focus: BotFocus
    custom_instructions: string | null
    handoff_keywords: string[]
    max_ai_replies: number | null
    active_hours: ActiveHours | null
    after_hours_message: string | null
    escalate_on_frustration: boolean
    hold_on_policy_violation: boolean
  }>): Promise<PlatformBot> =>
    api.put<PlatformBot>(`/chatbots/${platform}`, body).then(r => r.data),

  test: (platform: string, question: string): Promise<TestResult> =>
    api.post<TestResult>(`/chatbots/${platform}/test`, { question }).then(r => r.data),
}
