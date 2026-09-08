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
      if (!window.location.pathname.startsWith('/sellia-login')) {
        window.location.href = '/sellia-login'
      }
    }
    return Promise.reject(error)
  }
)

// ─── Type-safe helpers ────────────────────────────────────────────────────────

// Matches what backend/app/api/v1/signup.py's /auth/signup and /auth/signin
// actually return -- there is no tenant/role concept in the real backend
// (User -> Business is a plain one-to-many, no roles table), so the earlier
// `tenant_id`/`role` fields here were never populated by anything real and
// every call through authApi.signup/login/me 422'd in production (wrong
// field names entirely for signup/login, and a nonexistent shape for me).
export interface AuthResponse {
  access_token: string
  token_type?: string
  user_id: string
  email: string
  full_name: string
  requires_2fa_setup?: boolean
  requires_2fa?: boolean
}

export interface MeResponse {
  user_id: string
  email: string
  full_name: string
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
  // full_name is the real backend field (SignupRequest.full_name) -- payload
  // keeps `name` at the call sites for UI-label continuity and maps it here.
  signup: (payload: { email: string; password: string; name: string }) =>
    api.post<AuthResponse>('/auth/signup', { email: payload.email, password: payload.password, full_name: payload.name }).then((r) => r.data),

  // /auth/signin (not /auth/login -- that other endpoint takes an
  // OAuth2 form-encoded body and 403s until email verification, neither of
  // which this JSON/instant-access flow expects). Real accounts with 2FA
  // enabled get {requires_2fa: true, user_id} back with no access_token;
  // this client only handles the no-2FA path today, matching every new
  // signup's default (is_2fa_enabled=false) -- a 2FA account gets a clear
  // "código 2FA requerido" error here rather than silently failing.
  login: async (payload: { email: string; password: string; totp_code?: string }) => {
    const { data } = await api.post<AuthResponse & { requires_2fa?: boolean }>('/auth/signin', payload)
    if (data.requires_2fa) {
      throw new Error('Esta cuenta tiene 2FA activado. Ingresá el código de tu app autenticadora.')
    }
    return data
  },

  me: () => api.get<MeResponse>('/auth/me').then((r) => r.data),
}

/**
 * FastAPI's 422 validation errors send `detail` as an ARRAY of
 * {msg, loc, ...} objects, not a plain string -- pages that did
 * `typeof detail === 'string' ? detail : 'generic fallback'` silently
 * swallowed every Pydantic validation message (e.g. the real password
 * complexity rule) and showed a useless generic error instead. This
 * handles both shapes (a plain-string `detail`, from most other handlers
 * in this app, and the Pydantic array shape).
 */
export const extractErrorMessage = (err: unknown, fallback = 'Ocurrió un error'): string => {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((d) => (typeof d === 'string' ? d : d?.msg))
      .filter(Boolean)
      .join('; ') || fallback
  }
  return fallback
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
