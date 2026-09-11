/**
 * Rendimiento real del equipo.
 *
 * Mirrors backend/app/domains/team_performance/. This is what replaced the XP
 * ranking: those counters are written for the business owner on every order,
 * whoever actually closed it, so an employee could never leave zero. These
 * numbers come from the replies each person really sent and the deals they own.
 */

import { api } from './api'

export interface TeamMember {
  user_id: string
  name: string
  email: string
  role: string
  replies: number
  conversations: number
  median_first_reply_minutes: number | null
  first_reply_sample: number
  /** False when the median rests on too few replies to mean anything. */
  speed_is_readable: boolean
  deals_assigned: number
  deals_won: number
}

export interface TeamBoard {
  has_data: boolean
  headline: string
  members: TeamMember[]
  ai_replies?: number
  human_replies?: number
  unattributed_replies?: number
  conversations_waiting?: number
  /** What cannot be measured, stated instead of estimated. */
  gaps: string[]
  attribution_since?: string
  period_days: number
  generated_at?: string
}

export const teamPerformanceApi = {
  get: (days = 30, businessId?: string): Promise<TeamBoard> =>
    api.get<TeamBoard>('/team-performance', {
      params: { days, ...(businessId ? { business_id: businessId } : {}) },
    }).then(r => r.data),
}
