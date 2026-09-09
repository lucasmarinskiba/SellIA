/**
 * SellIA API client · axios + interceptors + token mgmt.
 */
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios'

// NEXT_PUBLIC_API_URL is set (both locally and in Vercel prod) to the bare
// backend origin (e.g. https://sellia-production.up.railway.app), same as
// lib/api.ts expects (which builds `${API_URL}/api/v1` itself) -- this
// client used to use the env var AS the full base with no `/api/v1`
// appended, so every real call (auth/signup, auth/signin, business-context,
// ai-activity, ...) actually hit `<origin>/auth/signup` etc. and 404'd.
// Confirmed live-broken in production this way -- the real backend has
// nothing mounted at that bare path. Normalizes defensively in case some
// deployment ever does set the var WITH the suffix already.
const normalizeApiBase = (raw: string): string => {
  const trimmed = raw.replace(/\/+$/, '')
  return /\/api\/v1$/.test(trimmed) ? trimmed : `${trimmed}/api/v1`
}
const API_BASE = normalizeApiBase(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')

const TOKEN_KEY = 'sellia.token'

// middleware.ts gates /dashboard/* on an `access_token` httpOnly cookie --
// but NEXT_PUBLIC_API_URL points this whole client straight at
// sellia-production.up.railway.app (a different domain from wherever this
// frontend is deployed, e.g. sellia-brain.vercel.app), so any cookie the
// backend sets is scoped to railway.app and can NEVER reach this frontend's
// own middleware, no matter which login flow issued it. That's why a real,
// just-created, just-logged-in account still got bounced back to /login the
// moment it clicked into /dashboard/*: the middleware's cookie was
// structurally unreachable, not missing due to a login bug.
//
// SELLIA_SESSION_COOKIE is a plain (non-httpOnly), same-origin marker this
// JS sets itself whenever it has a real token -- readable by middleware.ts
// server-side. It carries no secret (never the JWT itself, just "1"/absent)
// so it changes nothing about the real security boundary: every actual API
// call is still authorized by the real Bearer token in localStorage,
// attached by the interceptor below and (for the legacy cookie-based
// lib/api.ts client) by its own Bearer-fallback interceptor. This cookie's
// only job is letting middleware answer "should this render at all".
const SELLIA_SESSION_COOKIE = 'sellia_session'

export const setSessionCookie = (present: boolean): void => {
  if (typeof document === 'undefined') return
  if (present) {
    document.cookie = `${SELLIA_SESSION_COOKIE}=1; path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Lax`
  } else {
    document.cookie = `${SELLIA_SESSION_COOKIE}=; path=/; max-age=0; SameSite=Lax`
  }
}

export const getToken = (): string | null => {
  if (typeof window === 'undefined') return null
  return window.localStorage.getItem(TOKEN_KEY)
}

export const setToken = (token: string | null): void => {
  if (typeof window === 'undefined') return
  if (token) window.localStorage.setItem(TOKEN_KEY, token)
  else window.localStorage.removeItem(TOKEN_KEY)
  setSessionCookie(!!token)
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
