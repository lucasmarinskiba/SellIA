/**
 * Brain capability ON/OFF toggles.
 *
 * State lives in the visitor's own browser (localStorage) so an anonymous
 * demo visitor works exactly as before, and is sent with every real Computer
 * Use dispatch (POST /api/v1/brain/cua/dispatch's `disabled` field) so a
 * capability someone turned off is genuinely excluded from the plan the
 * backend builds, not just dimmed in the UI. See app/api/v1/brain.py's
 * brain_cua_dispatch.
 *
 * For a logged-in user with a real business, the toggle is ALSO persisted
 * server-side (GET/POST /api/v1/brain/toggles), backed by the same
 * AutomationToggle rows the FOMO middleware and the orchestrator's
 * capability gate check before letting a real automation/agent run (see
 * backend/app/core/brain/toggle_mapping.py) — so turning something off here
 * actually stops it, not just hides it locally. localStorage stays the
 * source of truth for rendering (instant, no network wait); the server call
 * is best-effort and reconciled on next load via syncDisabledFromServer().
 */

import { getToken, api } from '@/lib/sellia-api'

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
  const nowDisabled = !current.has(id)
  if (current.has(id)) current.delete(id)
  else current.add(id)
  setDisabledCapabilities(current)

  // Best-effort real persistence for logged-in users -- fire and forget so
  // the UI (already updated above, optimistically) never waits on the
  // network. If it fails (no business yet, offline, etc.) the toggle still
  // works exactly as before: local-only for this browser.
  if (getToken()) {
    void api.post('/brain/toggles', { brain_id: id, enabled: !nowDisabled }).catch(() => {})
  }

  return current
}

/** Re-enables every currently-disabled capability, both locally and (best
 * effort) on the server -- used by the Brain Map's "reactivar todas"
 * button, which used to only clear localStorage and leave any server-side
 * AutomationToggle rows disabled. */
export const reactivateAllCapabilities = (): void => {
  const current = getDisabledCapabilities()
  setDisabledCapabilities(new Set())
  if (getToken()) {
    for (const id of current) {
      void api.post('/brain/toggles', { brain_id: id, enabled: true }).catch(() => {})
    }
  }
}

/** Sets every id in `ids` to the same enabled/disabled state at once, both
 * locally and (best effort) on the server -- backs the Brain Map's "Activar
 * todo {categoría}" / "Desactivar todo {categoría}" buttons, so a whole
 * category can be flipped in one click instead of one node at a time. */
export const setCapabilitiesForIds = (ids: string[], enabled: boolean): void => {
  const current = getDisabledCapabilities()
  for (const id of ids) {
    if (enabled) current.delete(id)
    else current.add(id)
  }
  setDisabledCapabilities(current)
  if (getToken()) {
    for (const id of ids) {
      void api.post('/brain/toggles', { brain_id: id, enabled }).catch(() => {})
    }
  }
}

/** Pulls the server's real disabled set (per the logged-in user's business)
 * and makes it the local truth -- call this once when the Brain Map mounts
 * so a toggle made on another device/session shows up here too. No-ops
 * (returns null) for anonymous visitors or a user with no business yet;
 * callers should just keep using the localStorage-only state in that case. */
export const syncDisabledFromServer = async (): Promise<Set<string> | null> => {
  if (!getToken()) return null
  try {
    const { data } = await api.get<{ ok: boolean; disabled_brain_ids: string[] }>('/brain/toggles')
    if (!data.ok) return null
    const ids = new Set(data.disabled_brain_ids)
    setDisabledCapabilities(ids)
    return ids
  } catch {
    return null
  }
}
