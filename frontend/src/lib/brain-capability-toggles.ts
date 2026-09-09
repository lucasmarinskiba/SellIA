/**
 * Brain capability ON/OFF toggles.
 *
 * /sellia-brain is a public, unauthenticated command-center demo page (no
 * per-visitor login) -- there is no server-side per-user account to persist
 * a toggle against. State lives in the visitor's own browser (localStorage)
 * and is sent with every real Computer Use dispatch
 * (POST /api/v1/brain/cua/dispatch's `disabled` field) so a capability
 * someone turned off is genuinely excluded from the plan the backend builds,
 * not just dimmed in the UI. See app/api/v1/brain.py's brain_cua_dispatch.
 */

const STORAGE_KEY = 'sellia-brain-disabled-capabilities'
const CHANGE_EVENT = 'sellia-brain-capabilities-changed'

/** Subscribe to toggle changes made anywhere in this tab (BrainInteractionMap
 * writes directly via setDisabledCapabilities/toggleCapability below) --
 * lets a summary widget elsewhere on the page (e.g. the Dashboard's
 * "Automatizaciones activas" card) stay in sync without polling or lifting
 * this into shared React state. Returns an unsubscribe function. */
export const onCapabilitiesChanged = (cb: () => void): (() => void) => {
  if (typeof window === 'undefined') return () => {}
  window.addEventListener(CHANGE_EVENT, cb)
  return () => window.removeEventListener(CHANGE_EVENT, cb)
}

export const getDisabledCapabilities = (): Set<string> => {
  if (typeof window === 'undefined') return new Set()
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return new Set()
    const arr: unknown = JSON.parse(raw)
    return Array.isArray(arr) ? new Set(arr.filter((x): x is string => typeof x === 'string')) : new Set()
  } catch {
    return new Set()
  }
}

export const setDisabledCapabilities = (ids: Set<string>): void => {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify([...ids]))
  } catch {
    /* private mode / storage blocked -- toggle just won't persist across reloads */
  }
  window.dispatchEvent(new Event(CHANGE_EVENT))
}

export const toggleCapability = (id: string): Set<string> => {
  const current = getDisabledCapabilities()
  if (current.has(id)) current.delete(id)
  else current.add(id)
  setDisabledCapabilities(current)
  return current
}
