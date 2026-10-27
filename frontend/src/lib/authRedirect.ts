/**
 * Where a rejected request sends the person, shared by both API clients.
 *
 * Two bugs lived in the copies of this logic:
 * - A 401 from the login request itself (wrong email or password) was treated as "your session expired", so the
 *   page jumped to another login screen and the real error ("credenciales inválidas") was never shown.
 * - Sessions that did expire were sent to a different login screen depending on which client noticed first.
 * There is one login (`/login`); a rejected credential check stays on it.
 */

const AUTH_PAGES = ['/login', '/register', '/sellia-login', '/sellia-signup', '/reset-password', '/verify-email', '/forgot-password']

const CREDENTIAL_ENDPOINTS = /\/auth\/(signin|signup|login|forgot-password|reset-password|resend-verification|verify-email|2fa)/

/** A 401 on these means "those credentials are wrong", not "your session expired". */
export const isCredentialRequest = (url?: string): boolean => CREDENTIAL_ENDPOINTS.test(url ?? '')

export const isOnAuthPage = (): boolean =>
  typeof window !== 'undefined' &&
  AUTH_PAGES.some((p) => window.location.pathname === p || window.location.pathname.startsWith(`${p}/`))

/** Send an expired session to the login, remembering where the person was. */
export const redirectToLogin = (): void => {
  if (typeof window === 'undefined' || isOnAuthPage()) return
  const from = `${window.location.pathname}${window.location.search}`
  window.location.href = `/login?from=${encodeURIComponent(from)}`
}

/** The page to open after logging in: the one that asked for it, only if it is a path on this site. */
export const safeFrom = (raw: string | null | undefined): string =>
  raw && /^\/(?![/\\])/.test(raw) ? raw : '/dashboard'
