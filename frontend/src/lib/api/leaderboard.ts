/** Leaderboard API Client */

import { api } from '../api'

export interface LeaderboardEntry {
  rank: number
  user_id: string
  full_name: string
  email: string
  level: number
  total_xp: number
  total_sales_closed: number
  total_revenue_generated: number
  total_referrals_generated: number
  current_login_streak: number
  total_achievements: number
}

export interface UserRank {
  rank: number | null
  total_members: number
  user_id: string
  full_name: string
  email: string
  level: number
  total_xp: number
  total_sales_closed: number
  total_revenue_generated: number
  total_referrals_generated: number
  current_login_streak: number
  total_achievements: number
}

export interface NearbyUsers {
  user_rank: number | null
  metric: string
  nearby: LeaderboardEntry[]
}

export interface TeamStats {
  total_members: number
  total_sales: number
  total_revenue: number
  avg_streak: number
  top_performer_name: string | null
  top_performer_xp: number
}

export type LeaderboardMetric =
  | 'total_xp'
  | 'total_sales_closed'
  | 'total_revenue_generated'
  | 'total_referrals_generated'
  | 'current_login_streak'
  | 'total_achievements'

export const METRIC_LABELS: Record<LeaderboardMetric, string> = {
  total_xp: 'XP',
  total_sales_closed: 'Ventas',
  total_revenue_generated: 'Revenue',
  total_referrals_generated: 'Referidos',
  current_login_streak: 'Racha',
  total_achievements: 'Logros',
}

export const leaderboardApi = {
  getLeaderboard: (
    businessId: string,
    metric: LeaderboardMetric = 'total_xp',
    period: string = 'all_time',
    limit: number = 50
  ) =>
    api
      .get<LeaderboardEntry[]>('/gamification/leaderboard', {
        params: { business_id: businessId, metric, period, limit },
      })
      .then((r) => r.data),

  getMyRank: (businessId: string, metric: LeaderboardMetric = 'total_xp') =>
    api
      .get<UserRank>('/gamification/leaderboard/me', {
        params: { business_id: businessId, metric },
      })
      .then((r) => r.data),

  getNearby: (businessId: string, metric: LeaderboardMetric = 'total_xp') =>
    api
      .get<NearbyUsers>('/gamification/leaderboard/nearby', {
        params: { business_id: businessId, metric },
      })
      .then((r) => r.data),

  getTeamStats: (businessId: string) =>
    api
      .get<TeamStats>('/gamification/leaderboard/team-stats', {
        params: { business_id: businessId },
      })
      .then((r) => r.data),
}
