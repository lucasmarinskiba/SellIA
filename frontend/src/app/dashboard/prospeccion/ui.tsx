'use client'

import { useCallback, useState } from 'react'
import { errMsg } from '@/lib/api/harvey'

export const card = 'rounded-xl border border-slate-200 bg-white p-5'
export const input =
  'w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-primary focus:outline-none'
export const label = 'mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500'

const TONES: Record<string, string> = {
  good: 'bg-emerald-50 text-emerald-800',
  warn: 'bg-amber-50 text-amber-800',
  bad: 'bg-red-50 text-red-800',
  info: 'bg-sky-50 text-sky-800',
  muted: 'bg-slate-100 text-slate-500',
}

const STATUS_TONE: Record<string, string> = {
  pending_review: 'warn',
  approved: 'info',
  sent: 'good',
  blocked: 'bad',
  failed: 'bad',
  rejected: 'muted',
  sending: 'info',
  new: 'muted',
  drafted: 'info',
  contacted: 'info',
  completed: 'good',
  replied: 'good',
  opted_out: 'bad',
  bounced: 'bad',
  scraped: 'warn',
  verified: 'good',
  provided: 'good',
  invalid: 'bad',
}

export const STATUS_LABEL: Record<string, string> = {
  pending_review: 'a revisar',
  approved: 'aprobado',
  sent: 'enviado',
  blocked: 'bloqueado',
  failed: 'falló',
  rejected: 'rechazado',
  sending: 'enviando',
  new: 'nuevo',
  drafted: 'con borrador',
  contacted: 'contactado',
  completed: 'secuencia completa',
  replied: 'respondió',
  opted_out: 'pidió baja',
  bounced: 'rebotó',
  scraped: 'sin verificar',
  verified: 'verificado',
  provided: 'propio',
  invalid: 'inválido',
  interested: 'interesado',
  objection: 'objeción',
  question: 'pregunta',
  not_interested: 'no interesado',
  opt_out: 'baja',
  handoff: 'atiende una persona',
}

export function Badge({ value, tone }: { value: string; tone?: string }) {
  const t = TONES[tone ?? STATUS_TONE[value] ?? 'muted'] ?? TONES.muted
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${t}`}>
      {STATUS_LABEL[value] ?? value}
    </span>
  )
}

/** Runs an async action with a busy flag and a message, so every button reports what happened. */
export function useAction() {
  const [busy, setBusy] = useState<string | null>(null)
  const [notice, setNotice] = useState<{ kind: 'ok' | 'error'; text: string } | null>(null)

  const run = useCallback(async <T,>(key: string, fn: () => Promise<T>, ok: (r: T) => string): Promise<T | undefined> => {
    setBusy(key)
    setNotice(null)
    try {
      const result = await fn()
      setNotice({ kind: 'ok', text: ok(result) })
      return result
    } catch (e) {
      setNotice({ kind: 'error', text: errMsg(e) })
      return undefined
    } finally {
      setBusy(null)
    }
  }, [])

  return { busy, notice, run, clear: () => setNotice(null) }
}

export function Notice({ notice }: { notice: { kind: 'ok' | 'error'; text: string } | null }) {
  if (!notice) return null
  const cls =
    notice.kind === 'ok'
      ? 'border-emerald-200 bg-emerald-50 text-emerald-900'
      : 'border-red-200 bg-red-50 text-red-900'
  return (
    <p role="status" className={`rounded-lg border px-3 py-2 text-sm ${cls}`}>
      {notice.text}
    </p>
  )
}

export const lines = (text: string): string[] =>
  text
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean)

export const fmtDate = (iso: string | null): string => (iso ? new Date(iso).toLocaleString('es-AR') : '—')
