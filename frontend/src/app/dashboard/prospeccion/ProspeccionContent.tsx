'use client'

import Link from 'next/link'
import { useCallback, useEffect, useState } from 'react'
import { AlertTriangle, CheckCircle2, Loader2, XCircle } from 'lucide-react'
import { businessApi } from '@/lib/business'
import { errMsg, harvey, type HarveyProfile, type HarveyStatus } from '@/lib/api/harvey'
import { ApprovalTab } from './ApprovalTab'
import { ProspectsTab } from './ProspectsTab'
import { RepliesTab } from './RepliesTab'
import { SettingsTab } from './SettingsTab'
import { card } from './ui'

type TabKey = 'prospects' | 'approval' | 'replies' | 'settings'

const Check = ({ ok, children }: { ok: boolean; children: React.ReactNode }) => (
  <span className="inline-flex items-center gap-1.5 text-sm text-slate-700">
    {ok ? <CheckCircle2 className="h-4 w-4 text-emerald-600" /> : <XCircle className="h-4 w-4 text-red-600" />}
    {children}
  </span>
)

export function ProspeccionContent() {
  const [bid, setBid] = useState<string | null>(null)
  const [status, setStatus] = useState<HarveyStatus | null>(null)
  const [profile, setProfile] = useState<HarveyProfile | null>(null)
  const [tab, setTab] = useState<TabKey>('approval')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async (id: string) => {
    try {
      const [s, p] = await Promise.all([harvey.status(id), harvey.profile(id)])
      setStatus(s)
      setProfile(p)
      setError(null)
    } catch (e) {
      setError(errMsg(e))
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const list = await businessApi.list()
        if (cancelled) return
        if (!list.length) {
          setError('Primero creá un negocio.')
        } else {
          setBid(list[0].id)
          await refresh(list[0].id)
        }
      } catch (e) {
        if (!cancelled) setError(errMsg(e))
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [refresh])

  const reload = useCallback(() => (bid ? refresh(bid) : Promise.resolve()), [bid, refresh])

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }
  if (!bid || !status || !profile) {
    return <p className="p-6 text-sm text-red-700">{error ?? 'No se pudo cargar Prospección.'}</p>
  }

  const toggleEnabled = async () => {
    try {
      setProfile(await harvey.updateProfile(bid, { is_enabled: !profile.is_enabled }))
      await reload()
    } catch (e) {
      setError(errMsg(e))
    }
  }

  const missing: string[] = []
  if (!status.email_connected) missing.push('conectar un canal de email')
  if (!status.model_available) missing.push('la API key del modelo (no se pueden redactar borradores)')
  if (!profile.postal_address.trim()) missing.push('la dirección postal del negocio (se agrega al pie de cada email)')

  const tabs: { key: TabKey; label: string; badge?: number }[] = [
    { key: 'approval', label: 'Aprobación', badge: (status.outbox.pending_review ?? 0) + (status.outbox.blocked ?? 0) },
    { key: 'prospects', label: 'Prospectos', badge: status.prospects.new ?? 0 },
    { key: 'replies', label: 'Respuestas', badge: status.replies },
    { key: 'settings', label: 'Configuración' },
  ]

  return (
    <div className="mx-auto max-w-5xl space-y-5 p-4 sm:p-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Prospección</h1>
          <p className="text-sm text-slate-500">
            Encuentra clientes, redacta los emails y los envía desde tu casilla. Vos aprobás cada uno.
          </p>
        </div>
        <button
          onClick={toggleEnabled}
          className={`rounded-xl px-4 py-2 text-sm font-semibold ${
            profile.is_enabled ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'
          }`}
          aria-pressed={profile.is_enabled}
        >
          {profile.is_enabled ? 'Activo' : 'Desactivado'}
        </button>
      </header>

      {error && <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">{error}</p>}

      <section className={`${card} space-y-3`}>
        <div className="flex flex-wrap gap-x-6 gap-y-2">
          <Check ok={status.email_connected}>
            Email {status.email_connected ? 'conectado' : <Link href="/dashboard/canales" className="underline">sin conectar</Link>}
          </Check>
          <Check ok={status.model_available}>Redactor IA</Check>
          <Check ok={status.in_send_window}>{status.in_send_window ? 'En horario de envío' : 'Fuera del horario de envío'}</Check>
          <span className="text-sm text-slate-600">
            Enviados hoy: {status.sent_today}/{status.send_cap_today} · Borradores: {status.drafts_today}/{profile.max_daily_drafts}
          </span>
        </div>
        {missing.length > 0 && (
          <p className="flex items-start gap-2 text-sm text-amber-700">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            Falta: {missing.join('; ')}.
          </p>
        )}
      </section>

      <nav className="flex flex-wrap gap-2" role="tablist">
        {tabs.map((t) => (
          <button
            key={t.key}
            role="tab"
            aria-selected={tab === t.key}
            onClick={() => setTab(t.key)}
            className={`rounded-lg px-4 py-2 text-sm font-medium ${
              tab === t.key ? 'bg-primary text-primary-foreground' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            {t.label}
            {t.badge ? (
              <span className={`ml-2 rounded-full px-1.5 text-xs ${tab === t.key ? 'bg-white/30 text-white' : 'bg-slate-300 text-slate-800'}`}>
                {t.badge}
              </span>
            ) : null}
          </button>
        ))}
      </nav>

      {tab === 'approval' && <ApprovalTab bid={bid} onChange={reload} />}
      {tab === 'prospects' && <ProspectsTab bid={bid} status={status} onChange={reload} />}
      {tab === 'replies' && <RepliesTab bid={bid} onChange={reload} goToApproval={() => setTab('approval')} />}
      {tab === 'settings' && (
        <SettingsTab
          bid={bid}
          profile={profile}
          onSaved={async (p) => {
            setProfile(p)
            await reload()
          }}
        />
      )}
    </div>
  )
}
