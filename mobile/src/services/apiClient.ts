import axios, { AxiosInstance } from 'axios'
import * as SecureStore from 'expo-secure-store'

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000'

interface ApiClientConfig {
  baseURL: string
  timeout: number
}

class ApiClient {
  private client: AxiosInstance
  private token: string | null = null

  constructor(config: ApiClientConfig = { baseURL: API_URL, timeout: 10000 }) {
    this.client = axios.create(config)

    this.client.interceptors.request.use(async (config) => {
      if (!this.token) {
        this.token = await SecureStore.getItemAsync('auth_token')
      }
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`
      }
      return config
    })

    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          await this.clearAuth()
        }
        return Promise.reject(error)
      }
    )
  }

  async setToken(token: string): Promise<void> {
    this.token = token
    await SecureStore.setItemAsync('auth_token', token)
  }

  async getToken(): Promise<string | null> {
    if (!this.token) {
      this.token = await SecureStore.getItemAsync('auth_token')
    }
    return this.token
  }

  async clearAuth(): Promise<void> {
    this.token = null
    await SecureStore.deleteItemAsync('auth_token')
  }

  // Analytics endpoints
  async getDashboard(userId: string) {
    return this.client.get(`/api/v1/analytics/dashboard/${userId}`)
  }

  // Pipeline endpoints
  async getDeals(userId: string, limit: number = 50) {
    return this.client.get(`/api/v1/teams/performance/${userId}`, { params: { limit } })
  }

  async getDealDetail(dealId: string) {
    return this.client.get(`/api/v1/pipeline/deal/${dealId}`)
  }

  async updateDealStage(dealId: string, stage: string) {
    return this.client.post(`/api/v1/pipeline/deal/${dealId}/stage`, { stage })
  }

  // Approvals endpoints
  async getPendingApprovals(userId: string) {
    return this.client.get(`/api/v1/collaboration/pending/${userId}`)
  }

  async approveAction(actionId: string, userId: string, decision: 'approved' | 'rejected') {
    return this.client.post(`/api/v1/collaboration/approve`, {
      action_id: actionId,
      user_id: userId,
      decision,
    })
  }

  // Comments/Collaboration endpoints
  async getDealComments(dealId: string, limit: number = 50) {
    return this.client.get(`/api/v1/collaboration/comments/${dealId}`, { params: { limit } })
  }

  async addComment(dealId: string, userId: string, content: string, mentions: string[] = []) {
    return this.client.post(`/api/v1/collaboration/comment`, {
      deal_id: dealId,
      user_id: userId,
      content,
      mentions,
    })
  }

  // Notifications endpoints
  async getNotifications(userId: string, limit: number = 20) {
    return this.client.get(`/api/v1/analytics/notifications/${userId}`, { params: { limit } })
  }

  async markNotificationRead(notificationId: string) {
    return this.client.post(`/api/v1/analytics/notifications/${notificationId}/read`)
  }

  // User endpoints
  async getCurrentUser() {
    return this.client.get('/api/v1/users/me')
  }

  async updateUserProfile(userId: string, data: Record<string, unknown>) {
    return this.client.put(`/api/v1/users/${userId}/profile`, data)
  }
}

export const apiClient = new ApiClient()
