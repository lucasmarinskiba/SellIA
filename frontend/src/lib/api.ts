import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'))
  return match ? decodeURIComponent(match[2]) : null
}

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Enviar cookies httpOnly automáticamente
})

// Bridges this cookie-based client with the sellia-api family's Bearer-token
// auth (src/lib/sellia-api/client.ts). Real accounts created through
// /sellia-signup + /sellia-login only ever get a JSON access_token (no
// cookie is set anywhere in backend/app/api/v1/signup.py's /signup or
// /signin), so businessContextApi/business.ts/missions.ts -- all built on
// THIS client -- had zero credentials to send for those users, even after
// a successful login: withCredentials sent an empty cookie jar, silently
// 401ing every call. get_current_user (app/core/deps.py) already accepts
// either a Bearer header or a cookie, so attaching whichever token this
// browser actually has makes both auth systems interoperate without
// touching either one's own storage mechanism.
const SELLIA_API_TOKEN_KEY = 'sellia.token'

api.interceptors.request.use((config) => {
  const csrfToken = getCookie('csrf_token')
  if (csrfToken && config.method && config.method !== 'get') {
    config.headers['X-CSRF-Token'] = csrfToken
  }
  if (!config.headers.Authorization && typeof window !== 'undefined') {
    const bearerToken = window.localStorage.getItem(SELLIA_API_TOKEN_KEY)
    if (bearerToken) config.headers.Authorization = `Bearer ${bearerToken}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        // Send sellia-api users back to their own login, not the legacy one.
        const hasBearerToken = !!window.localStorage.getItem(SELLIA_API_TOKEN_KEY)
        window.location.href = hasBearerToken ? '/sellia-login' : '/login'
      }
    }
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after']
      const msg = retryAfter
        ? `Demasiadas peticiones. Reintentá en ${retryAfter}s.`
        : 'Demasiadas peticiones. Esperá un momento e intentá de nuevo.'
      if (typeof window !== 'undefined') {
        alert(msg)
      }
    }
    return Promise.reject(error)
  }
)
