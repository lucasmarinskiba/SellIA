/**
 * Security helpers for the frontend.
 */

const ALLOWED_REDIRECT_DOMAINS = [
  'mercadolibre.com',
  'mercadolibre.com.ar',
  'mercadopago.com',
  'stripe.com',
  'paypal.com',
  'instagram.com',
  'facebook.com',
  'whatsapp.com',
  'tiktok.com',
]

export function isSafeRedirectUrl(url: string): boolean {
  if (!url) return false
  try {
    const parsed = new URL(url)
    // Reject javascript:, data:, etc.
    if (parsed.protocol !== 'https:' && parsed.protocol !== 'http:') {
      return false
    }
    // Allow relative URLs (should not happen with URL constructor but be safe)
    if (!parsed.hostname) return true
    return ALLOWED_REDIRECT_DOMAINS.some((domain) =>
      parsed.hostname === domain || parsed.hostname.endsWith('.' + domain)
    )
  } catch {
    // If URL constructor fails, it might be a relative URL
    return !url.startsWith('javascript:') && !url.startsWith('data:') && !url.startsWith('vbscript:')
  }
}

/**
 * Get client-side token fallback for legacy code paths
 * (e.g., direct file downloads that need a query param).
 * The primary auth mechanism is httpOnly cookie via withCredentials.
 */
export function getClientToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('token') || localStorage.getItem('access_token') || null
}
