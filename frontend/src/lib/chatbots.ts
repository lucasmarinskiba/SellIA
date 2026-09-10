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

export interface PlatformBot {
  platform: string
  enabled: boolean
  personality_slug: string | null
  focus: BotFocus
  focus_label: string
  custom_instructions: string | null
  handoff_keywords: string[]
  max_ai_replies: number | null
  updated_at: string | null
  configured: boolean
  stats: BotStats
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
}

export const chatbotsApi = {
  list: (): Promise<BotsOverview> =>
    api.get<BotsOverview>('/chatbots').then(r => r.data),

  personalities: (): Promise<Personality[]> =>
    api.get<{ personalities: Personality[] }>('/chatbots/personalities')
      .then(r => r.data.personalities),

  update: (platform: string, body: Partial<{
    enabled: boolean
    personality_slug: string | null
    focus: BotFocus
    custom_instructions: string | null
    handoff_keywords: string[]
    max_ai_replies: number | null
  }>): Promise<PlatformBot> =>
    api.put<PlatformBot>(`/chatbots/${platform}`, body).then(r => r.data),

  test: (platform: string, question: string): Promise<TestResult> =>
    api.post<TestResult>(`/chatbots/${platform}/test`, { question }).then(r => r.data),
}
