/**
 * SellIA API client · axios + interceptors + token mgmt.
 */
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'

const TOKEN_KEY = 'sellia.token'

export const getToken = (): string | null => {
  if (typeof window === 'undefined') return null
  return window.localStorage.getItem(TOKEN_KEY)
}

export const setToken = (token: string | null): void => {
  if (typeof window === 'undefined') return
  if (token) window.localStorage.setItem(TOKEN_KEY, token)
  else window.localStorage.removeItem(TOKEN_KEY)
}

export const api: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      // Token expired/invalid · clear + redirect to login
      setToken(null)
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// ─── Type-safe helpers ────────────────────────────────────────────────────────

export interface AuthResponse {
  access_token: string
  token_type: string
  user_id: string
  tenant_id: string
  role: 'owner' | 'admin' | 'manager' | 'viewer'
}

export interface MeResponse {
  user_id: string
  tenant_id: string
  role: AuthResponse['role']
}

export interface Deal {
  id: string
  title: string
  value_cents: number
  currency: string
  stage: 'prospect' | 'qualified' | 'negotiation' | 'won' | 'lost'
  probability: number
}

export const authApi = {
  signup: (payload: { email: string; password: string; name: string; tenant_name: string }) =>
    api.post<AuthResponse>('/auth/signup', payload).then((r) => r.data),

  login: (payload: { email: string; password: string }) =>
    api.post<AuthResponse>('/auth/login', payload).then((r) => r.data),

  me: () => api.get<MeResponse>('/auth/me').then((r) => r.data),
}

export const dealsApi = {
  list: () => api.get<Deal[]>('/deals').then((r) => r.data),

  create: (payload: { contact_id: string; title: string; value_cents: number; currency?: string }) =>
    api.post<Deal>('/deals', payload).then((r) => r.data),

  update: (id: string, payload: Partial<Deal>) =>
    api.patch<Deal>(`/deals/${id}`, payload).then((r) => r.data),

  delete: (id: string) => api.delete(`/deals/${id}`).then((r) => r.data),
}

export const billingApi = {
  checkout: (plan: 'starter' | 'pro' | 'scale', success_url: string, cancel_url: string) =>
    api.post<{ checkout_url: string }>('/billing/checkout', { plan, success_url, cancel_url }).then((r) => r.data),
}
