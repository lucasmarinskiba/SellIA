import { api } from './api'

export interface GamificationProfile {
  id: string
  user_id: string
  level: number
  level_title: string
  total_xp: number
  xp_to_next_level: number
  progress_pct: number
  current_login_streak: number
  max_login_streak: number
  autopilot_trust_streak: number
  total_achievements: number
  total_sales_closed: number
  total_revenue_generated: number
  total_leads_acquired: number
  total_content_published: number
  total_reviews_collected: number
  total_referrals_generated: number
  garden_state: Record<string, any>
  companion_name: string
  companion_mood: string
  user_mood_today: string | null
  created_at: string
  updated_at: string
}

export interface Achievement {
  id: string
  slug: string
  name: string
  description: string
  category: string
  tier: string
  xp_reward: number
  icon: string
  color: string
  animation: string
}

export interface CelebrationEvent {
  id: string
  event_type: string
  event_title: string
  event_description: string | null
  event_value: number | null
  intensity: string
  companion_message: string | null
  companion_emotion: string
  was_shown: boolean
  created_at: string
}

export interface MoodLog {
  id: string
  mood: string
  energy_level: number
  ai_response: string | null
  created_at: string
}

export const gamificationApi = {
  getProfile: (): Promise<GamificationProfile> =>
    api.get('/gamification/profile').then(r => r.data),

  recordLogin: (): Promise<any> =>
    api.post('/gamification/login').then(r => r.data),

  listAchievements: (): Promise<Achievement[]> =>
    api.get('/gamification/achievements').then(r => r.data),

  myAchievements: (): Promise<any[]> =>
    api.get('/gamification/my-achievements').then(r => r.data),

  getPendingCelebrations: (): Promise<CelebrationEvent[]> =>
    api.get('/gamification/celebrations/pending').then(r => r.data),

  markCelebrationShown: (id: string): Promise<any> =>
    api.post(`/gamification/celebrations/${id}/shown`).then(r => r.data),

  getGarden: (): Promise<any> =>
    api.get('/gamification/garden').then(r => r.data),

  gardenAction: (action: string): Promise<any> =>
    api.post('/gamification/garden/action', null, { params: { action } }).then(r => r.data),

  getCompanionMessage: (context?: string): Promise<any> =>
    api.get('/gamification/companion/message', { params: { context } }).then(r => r.data),

  moodCheckin: (data: { mood: string; energy_level?: number; notes?: string }): Promise<MoodLog> =>
    api.post('/gamification/mood', data).then(r => r.data),

  moodHistory: (limit?: number): Promise<MoodLog[]> =>
    api.get('/gamification/mood/history', { params: { limit } }).then(r => r.data),

  seedAchievements: (): Promise<any> =>
    api.post('/gamification/seed-achievements').then(r => r.data),
}
