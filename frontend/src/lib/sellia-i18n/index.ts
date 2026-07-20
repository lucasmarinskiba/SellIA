/**
 * Lightweight i18n · 12 langs · no next-intl dep · client-side resolution.
 *
 * Usage:
 *   import { t, setLocale, useTranslation } from '@/lib/sellia-i18n'
 *   t('login.title')  → "Iniciar sesión"
 */
import { type Locale, MESSAGES, DEFAULT_LOCALE } from './messages'

export type { Locale }
export { MESSAGES, DEFAULT_LOCALE }

const STORAGE_KEY = 'sellia.locale'

let currentLocale: Locale = DEFAULT_LOCALE
const listeners = new Set<() => void>()

export function getLocale(): Locale {
  if (typeof window !== 'undefined') {
    const stored = window.localStorage.getItem(STORAGE_KEY) as Locale | null
    if (stored && stored in MESSAGES) return stored
    const browserLang = window.navigator.language.toLowerCase().split('-')[0] as Locale
    if (browserLang in MESSAGES) return browserLang
  }
  return currentLocale
}

export function setLocale(locale: Locale): void {
  if (!(locale in MESSAGES)) return
  currentLocale = locale
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(STORAGE_KEY, locale)
    window.document.documentElement.lang = locale
  }
  listeners.forEach((fn) => fn())
}

export function subscribeLocale(fn: () => void): () => void {
  listeners.add(fn)
  return () => listeners.delete(fn)
}

/** Look up translation · falls back to en · then key. Supports {var} interpolation. */
export function t(key: string, vars?: Record<string, string | number>): string {
  const loc = getLocale()
  const dict = MESSAGES[loc] || MESSAGES[DEFAULT_LOCALE]
  let value = dict[key] ?? MESSAGES['en'][key] ?? key
  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      value = value.replaceAll(`{${k}}`, String(v))
    }
  }
  return value
}
