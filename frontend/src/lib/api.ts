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

api.interceptors.request.use((config) => {
  const csrfToken = getCookie('csrf_token')
  if (csrfToken && config.method && config.method !== 'get') {
    config.headers['X-CSRF-Token'] = csrfToken
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
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
