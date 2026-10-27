/**
 * What state a channel connection is in: ONE definition for every screen.
 *
 * Canales, Plataformas and Vendedor Multiplataforma all show the same `channel_connections` rows. They used to
 * each decide for themselves what "Conectado" means (one said so for any row that existed), so the same
 * connection read "Conectado" in one place and "Por verificar" in another. Everything now goes through here.
 */

type Conn = { platform: string; status: string; credentials?: Record<string, unknown> | null }

/** Platforms with their own SellIA app: the user only authorizes, never pastes credentials. */
export const ONE_CLICK_PLATFORMS = ['mercadolibre', 'instagram', 'messenger', 'facebook_ads', 'facebook_marketplace']

/** Keys that mean "an authorization actually finished" (the API returns key names, never values). */
const AUTH_KEYS = ['access_token', 'api_token', 'page_access_token', 'refresh_token']

const hasAuthorization = (c: Conn): boolean => AUTH_KEYS.some((k) => k in (c.credentials ?? {}))

/**
 * A row exists as soon as someone STARTS an authorization (the backend creates it with no token and
 * status "pending"). If they close the Meta/Mercado Libre window, that row stays behind: it is not a
 * connection, so it must not be counted or shown as one.
 */
export const isIncomplete = (c: Conn): boolean => {
  if (c.status !== 'pending') return false
  return ONE_CLICK_PLATFORMS.includes(c.platform)
    ? !hasAuthorization(c)
    : Object.keys(c.credentials ?? {}).length === 0
}

/** Marked connected but nothing was stored, so it cannot send or receive: it has to be authorized again. */
export const needsReconnect = (c: Conn): boolean =>
  c.status === 'connected' && ONE_CLICK_PLATFORMS.includes(c.platform) && !hasAuthorization(c)

export type ChannelState = 'connected' | 'toVerify' | 'incomplete' | 'error' | 'other'

/** The single place that decides which bucket a channel belongs to (counts, filters and badges share it). */
export const channelState = (c: Conn): ChannelState => {
  if (isIncomplete(c)) return 'incomplete'
  if (c.status === 'error' || needsReconnect(c)) return 'error'
  if (c.status === 'connected') return 'connected'
  if (c.status === 'pending') return 'toVerify'
  return 'other'
}

export const STATE_LABEL: Record<Exclude<ChannelState, 'other'>, string> = {
  connected: 'Conectados',
  toVerify: 'Por verificar',
  incomplete: 'Sin completar',
  error: 'Con error',
}

const PILL = {
  connected: 'bg-emerald-50 text-emerald-800 ring-emerald-200',
  toVerify: 'bg-amber-50 text-amber-800 ring-amber-200',
  incomplete: 'bg-slate-100 text-slate-700 ring-slate-300',
  error: 'bg-red-50 text-red-800 ring-red-200',
  other: 'bg-slate-100 text-slate-700 ring-slate-200',
} as const

/** The badge a single connection shows, identical on every screen. */
export const stateBadge = (c: Conn): { state: ChannelState; label: string; pill: string } => {
  const state = channelState(c)
  const labels: Record<ChannelState, string> = {
    connected: 'Conectado',
    toVerify: 'Por verificar',
    incomplete: 'Sin completar',
    error: needsReconnect(c) ? 'Hay que reconectar' : 'Con error',
    other: 'Deshabilitado',
  }
  return { state, label: labels[state], pill: PILL[state] }
}

/** One-click platforms use the account that is logged in at the provider, so switching means authorizing again. */
export const canSwitchAccount = (platform: string): boolean => ONE_CLICK_PLATFORMS.includes(platform)
