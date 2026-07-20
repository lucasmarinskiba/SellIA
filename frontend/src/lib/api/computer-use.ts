/** Computer Use — REST API Client */

import { api } from '../api'

export interface CreateSessionRequest {
  task_description: string
  start_url?: string
  business_id?: string
  browser_type?: string
}

export interface ComputerUseSession {
  id: string
  user_id: string
  business_id?: string
  task_description: string
  status: string
  current_url?: string
  total_steps: number
  created_at: string
  updated_at: string
}

export const computerUseApi = {
  createSession: (data: CreateSessionRequest) =>
    api.post<ComputerUseSession>('/computer-use/sessions', data).then(r => r.data),

  listSessions: () =>
    api.get<{ items: ComputerUseSession[]; total: number }>('/computer-use/sessions').then(r => r.data),

  getSession: (sessionId: string) =>
    api.get<ComputerUseSession>(`/computer-use/sessions/${sessionId}`).then(r => r.data),

  deleteSession: (sessionId: string) =>
    api.delete(`/computer-use/sessions/${sessionId}`).then(r => r.data),

  startSession: (sessionId: string) =>
    api.post<{ session_id: string; ws_url: string; status: string; message: string }>(
      `/computer-use/sessions/${sessionId}/start`
    ).then(r => r.data),

  getSteps: (sessionId: string) =>
    api.get<any[]>(`/computer-use/sessions/${sessionId}/steps`).then(r => r.data),

  getMessages: (sessionId: string) =>
    api.get<any[]>(`/computer-use/sessions/${sessionId}/messages`).then(r => r.data),
}
