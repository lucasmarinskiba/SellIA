'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { AlertCircle, CheckCircle2, Clock, Plug, Plus, Search, X } from 'lucide-react'
import { businessApi, type Business } from '@/lib/business'
import { channelsApi, type ChannelConnection } from '@/lib/channels'
import type { ChannelPlatform } from '@/types/channels'
import { ChannelCard } from './ChannelCard'
import { ConnectModal, type ConnectDraft } from './ConnectModal'
import {
  CATEGORIES, channelTitle, isIncomplete, needsReconnect, ONE_CLICK_PLATFORMS, PLATFORMS, platformMeta, type CategoryKey,
} from './catalog'

type Notice = { kind: 'ok' | 'error' | 'warn'; text: string } | null

const NOTICE_STYLE: Record<'ok' | 'error' | 'warn', string> = {
  ok: 'border-emerald-200 bg-emerald-50 text-emerald-900',
  error: 'border-red-200 bg-red-50 text-red-900',
  warn: 'border-amber-200 bg-amber-50 text-amber-900',
}

const emptyDraft = (platform: ChannelPlatform = 'email'): ConnectDraft => ({
  platform,
  name: platformMeta(platform).label,
  credentials: platform === 'email' ? { smtp_host: 'smtp.gmail.com', smtp_port: '587' } : {},
})

/** The backend's reason when it gave one, so a failed save says why instead of failing silently. */
const reason = (e: unknown, fallback: string): string => {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  return typeof detail === 'string' ? detail : fallback
}

function Stat({ label, hint, value, tone, icon: Icon }: {
  label: string; hint: string; value: number; tone: string; icon: typeof Plug
}) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${tone}`} aria-hidden="true">
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <p className="text-2xl font-bold tabular-nums leading-none text-slate-900">{value}</p>
        <p className="mt-1 text-xs font-medium text-slate-700">{label}</p>
        <p className="text-xs text-slate-500">{hint}</p>
      </div>
    </div>
  )
}

export default function CanalesPage() {
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [businessId, setBusinessId] = useState('')
  const [channels, setChannels] = useState<ChannelConnection[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [draft, setDraft] = useState<ConnectDraft>(emptyDraft())
  const [saving, setSaving] = useState(false)
  const [modalError, setModalError] = useState<string | null>(null)
  const [testingId, setTestingId] = useState<string | null>(null)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [connecting, setConnecting] = useState(false)
  const [notice, setNotice] = useState<Notice>(null)
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState<CategoryKey | 'all'>('all')

  const loadChannels = useCallback(async (id: string) => {
    setLoading(true)
    try {
      setChannels(await channelsApi.list(id))
    } catch {
      setNotice({ kind: 'error', text: 'No se pudieron cargar tus canales. Probá recargar la página.' })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    businessApi
      .list()
      .then((data) => {
        setBusinesses(data)
        if (data.length) setBusinessId(data[0].id)
        else setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (businessId) void loadChannels(businessId)
  }, [businessId, loadChannels])

  const openModal = useCallback((platform: ChannelPlatform = 'email') => {
    setDraft(emptyDraft(platform))
    setModalError(null)
    setModalOpen(true)
  }, [])

  // Return trip from an OAuth authorization, or a deep link like ?connect=email.
  useEffect(() => {
    if (!businessId) return
    const params = new URLSearchParams(window.location.search)
    if (params.get('connected')) {
      window.history.replaceState({}, '', window.location.pathname)
      void loadChannels(businessId)
      setNotice({ kind: 'ok', text: 'Canal conectado.' })
    }
    if (params.get('connect_error') === 'cancelled') {
      window.history.replaceState({}, '', window.location.pathname)
      setNotice({ kind: 'warn', text: 'No se conectó nada: cancelaste (o no completaste) la autorización.' })
    }
    if (params.get('connect_error') === 'state') {
      window.history.replaceState({}, '', window.location.pathname)
      setNotice({ kind: 'error', text: 'El enlace de autorización venció o no es válido. Empezá la conexión de nuevo desde acá.' })
    }
    const connect = params.get('connect')
    if (connect) {
      window.history.replaceState({}, '', window.location.pathname)
      openModal(connect as ChannelPlatform)
    }
  }, [businessId, loadChannels, openModal])

  const closeModal = useCallback(() => setModalOpen(false), [])

  const handleCreate = async () => {
    setSaving(true)
    setModalError(null)
    try {
      await channelsApi.create(businessId, { platform: draft.platform, name: draft.name, credentials: draft.credentials })
      setModalOpen(false)
      setNotice({
        kind: 'ok',
        text: `${platformMeta(draft.platform).label} guardado. Usá "Probar" para verificar que la conexión funcione.`,
      })
      await loadChannels(businessId)
    } catch (e) {
      setModalError(reason(e, 'No se pudo guardar el canal. Revisá los datos e intentá de nuevo.'))
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (channel: ChannelConnection) => {
    const name = channelTitle(channel)
    const prompt = isIncomplete(channel)
      ? `¿Quitar "${name}"? Era una conexión sin terminar; podés iniciarla de nuevo cuando quieras.`
      : `¿Desconectar "${name}"? Vas a tener que volver a conectarlo si lo querés usar de nuevo.`
    if (!confirm(prompt)) return
    try {
      await channelsApi.delete(businessId, channel.id)
      setNotice({ kind: 'ok', text: `"${name}" ${isIncomplete(channel) ? 'quitado' : 'desconectado'}.` })
      await loadChannels(businessId)
    } catch (e) {
      setNotice({ kind: 'error', text: reason(e, 'No se pudo desconectar el canal.') })
    }
  }

  const handleTest = async (channel: ChannelConnection) => {
    setTestingId(channel.id)
    setNotice(null)
    try {
      await channelsApi.test(businessId, channel.id)
      const fresh = await channelsApi.list(businessId)
      setChannels(fresh)
      const updated = fresh.find((c) => c.id === channel.id)
      if (updated?.status === 'error') {
        setNotice({ kind: 'error', text: updated.status_message || `La conexión de ${channelTitle(channel)} falló.` })
      } else {
        setNotice({ kind: 'ok', text: `${channelTitle(channel)}: conexión verificada.` })
      }
    } catch (e) {
      setNotice({ kind: 'error', text: reason(e, 'No se pudo probar la conexión.') })
    } finally {
      setTestingId(null)
    }
  }

  const completeConnection = (channel: ChannelConnection) => {
    if (ONE_CLICK_PLATFORMS.includes(channel.platform)) void handleOAuth(channel.platform as ChannelPlatform)
    else openModal(channel.platform as ChannelPlatform)
  }

  const switchAccount = (channel: ChannelConnection) => {
    const meta = platformMeta(channel.platform)
    const current = channel.account?.name ? ` (hoy: ${channel.account.name})` : ''
    const ok = confirm(
      `Vas a conectar otra cuenta de ${meta.label}${current}.\n\n` +
        `${meta.label} usa la cuenta que tengas abierta en este navegador. Si querés usar otra, antes cerrá sesión en ` +
        `${meta.label} o abrí esta página en una ventana privada. La conexión actual se reemplaza cuando termines.`,
    )
    if (ok) void handleOAuth(channel.platform as ChannelPlatform)
  }

  const handleOAuth = async (platform: ChannelPlatform) => {
    setConnecting(true)
    try {
      const { auth_url } = await channelsApi.authUrl(businessId, platform)
      window.location.href = auth_url
    } catch {
      setModalError(`No se pudo iniciar la conexión con ${platformMeta(platform).label}. Probá de nuevo en un momento.`)
      setConnecting(false)
    }
  }

  // WhatsApp can't use the plain redirect flow: a phone_number_id only comes back through Meta's own
  // Embedded Signup popup (Facebook JS SDK), which delivers it via postMessage rather than a query param.
  const loadFacebookSdk = (appId: string): Promise<any> =>
    new Promise((resolve) => {
      const w = window as any
      if (w.FB) {
        resolve(w.FB)
        return
      }
      w.fbAsyncInit = () => {
        w.FB.init({ appId, version: 'v18.0', xfbml: false })
        resolve(w.FB)
      }
      if (!document.getElementById('facebook-jssdk')) {
        const script = document.createElement('script')
        script.id = 'facebook-jssdk'
        script.src = 'https://connect.facebook.net/es_LA/sdk.js'
        script.async = true
        document.body.appendChild(script)
      }
    })

  const handleWhatsApp = async () => {
    setConnecting(true)
    setModalError(null)
    try {
      const { app_id } = await channelsApi.whatsappEmbeddedSignupConfig(businessId)
      const FB = await loadFacebookSdk(app_id)
      let wabaData: { waba_id?: string; phone_number_id?: string } = {}
      const onMessage = (event: MessageEvent) => {
        if (event.origin !== 'https://www.facebook.com') return
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'WA_EMBEDDED_SIGNUP' && data.event === 'FINISH') {
            wabaData = { waba_id: data.data?.waba_id, phone_number_id: data.data?.phone_number_id }
          }
        } catch {
          /* not a WA Embedded Signup message */
        }
      }
      window.addEventListener('message', onMessage)
      FB.login(
        (response: any) => {
          window.removeEventListener('message', onMessage)
          const code = response?.authResponse?.code
          if (!code || !wabaData.waba_id || !wabaData.phone_number_id) {
            setModalError('No se completó la conexión con WhatsApp. Probá de nuevo y no cierres el popup hasta el final.')
            setConnecting(false)
            return
          }
          channelsApi
            .whatsappEmbeddedSignup(businessId, { code, waba_id: wabaData.waba_id, phone_number_id: wabaData.phone_number_id })
            .then(() => {
              setModalOpen(false)
              setNotice({ kind: 'ok', text: 'WhatsApp conectado.' })
              void loadChannels(businessId)
            })
            .catch(() => setModalError('WhatsApp autorizó pero no se pudo guardar la conexión. Probá de nuevo en un momento.'))
            .finally(() => setConnecting(false))
        },
        {
          scope: 'whatsapp_business_management,whatsapp_business_messaging',
          extras: { feature: 'whatsapp_embedded_signup', sessionInfoVersion: '3' },
        },
      )
    } catch {
      setModalError('No se pudo iniciar la conexión con WhatsApp. Probá de nuevo en un momento.')
      setConnecting(false)
    }
  }

  const copyWebhook = (url: string, id: string) => {
    void navigator.clipboard.writeText(url)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const counts = useMemo(
    () => ({
      connected: channels.filter((c) => c.status === 'connected' && !needsReconnect(c)).length,
      toVerify: channels.filter((c) => c.status === 'pending' && !isIncomplete(c)).length,
      incomplete: channels.filter(isIncomplete).length,
      error: channels.filter((c) => c.status === 'error' || needsReconnect(c)).length,
    }),
    [channels],
  )

  const q = query.trim().toLowerCase()
  const matchesFilters = (platform: string, text: string): boolean => {
    const meta = platformMeta(platform)
    return (category === 'all' || meta.category === category) && (!q || `${text} ${meta.label}`.toLowerCase().includes(q))
  }

  const visibleChannels = channels.filter((c) => matchesFilters(c.platform, c.account?.name ?? ''))
  const connectedPlatforms = new Set(channels.map((c) => c.platform as string))
  const available = Object.keys(PLATFORMS).filter((p) => !connectedPlatforms.has(p) && matchesFilters(p, PLATFORMS[p].description))

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-brand-orange/10 text-brand-orange" aria-hidden="true">
            <Plug className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">Canales</h1>
            <p className="text-sm text-slate-500">Conectá tus plataformas de venta y comunicación en un solo lugar.</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {businesses.length > 1 && (
            <>
              <label htmlFor="canales-business" className="sr-only">Negocio</label>
              <select
                id="canales-business"
                value={businessId}
                onChange={(e) => setBusinessId(e.target.value)}
                className="h-11 rounded-xl border border-slate-300 bg-white px-3 text-sm text-slate-900 focus:border-brand-orange focus:outline-none focus:ring-2 focus:ring-brand-orange/30"
              >
                {businesses.map((b) => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>
            </>
          )}
          <button
            type="button"
            onClick={() => openModal()}
            disabled={!businessId}
            className="inline-flex h-11 items-center gap-2 rounded-xl bg-brand-orange px-5 text-sm font-semibold text-white shadow-sm hover:bg-brand-orange-dark focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange focus-visible:ring-offset-2 disabled:opacity-50"
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            Conectar canal
          </button>
        </div>
      </header>

      {notice && (
        <div role="status" className={`flex items-start justify-between gap-3 rounded-xl border px-4 py-3 text-sm ${NOTICE_STYLE[notice.kind]}`}>
          <span>{notice.text}</span>
          <button type="button" onClick={() => setNotice(null)} aria-label="Cerrar aviso" className="-mr-1 shrink-0 rounded p-1 opacity-60 hover:opacity-100">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <section aria-label="Resumen" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="Conectados" hint="Autorizados y listos" value={counts.connected} icon={CheckCircle2} tone="bg-emerald-50 text-emerald-700" />
        <Stat label="Por verificar" hint="Guardados: falta probarlos" value={counts.toVerify} icon={Clock} tone="bg-amber-50 text-amber-700" />
        <Stat label="Sin completar" hint="Autorización sin terminar" value={counts.incomplete} icon={Plug} tone="bg-slate-100 text-slate-700" />
        <Stat label="Con error" hint="Fallaron al probar" value={counts.error} icon={AlertCircle} tone="bg-red-50 text-red-700" />
      </section>

      <section aria-label="Filtros" className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="relative w-full lg:max-w-xs">
          <label htmlFor="canales-search" className="sr-only">Buscar canal</label>
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
          <input
            id="canales-search"
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Buscar canal…"
            className="h-11 w-full rounded-xl border border-slate-300 bg-white pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-orange focus:outline-none focus:ring-2 focus:ring-brand-orange/30"
          />
        </div>
        <div className="flex flex-wrap gap-2" role="group" aria-label="Categoría">
          {[{ key: 'all' as const, label: 'Todos' }, ...CATEGORIES].map((c) => (
            <button
              key={c.key}
              type="button"
              aria-pressed={category === c.key}
              onClick={() => setCategory(c.key)}
              className={`h-10 rounded-full px-4 text-sm font-medium ring-1 ring-inset focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange ${
                category === c.key ? 'bg-slate-900 text-white ring-slate-900' : 'bg-white text-slate-700 ring-slate-300 hover:bg-slate-50'
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>
      </section>

      <section aria-labelledby="mis-canales" className="space-y-4">
        <div className="flex items-baseline justify-between">
          <h2 id="mis-canales" className="text-lg font-semibold text-slate-900">Tus canales</h2>
          {!loading && channels.length > 0 && (
            <span className="text-sm text-slate-500">{visibleChannels.length} de {channels.length}</span>
          )}
        </div>

        {loading ? (
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3" aria-busy="true">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-44 animate-pulse rounded-2xl border border-slate-200 bg-white" />
            ))}
          </div>
        ) : channels.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-500" aria-hidden="true">
              <Plug className="h-7 w-7" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900">Todavía no conectaste ningún canal</h3>
            <p className="mx-auto mt-1 max-w-md text-sm text-slate-500">
              Empezá por tu email para enviar y recibir mensajes con tus clientes, o elegí cualquier plataforma de la lista de abajo.
            </p>
            <button
              type="button"
              onClick={() => openModal('email')}
              className="mt-5 inline-flex h-11 items-center gap-2 rounded-xl bg-brand-orange px-5 text-sm font-semibold text-white hover:bg-brand-orange-dark focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange focus-visible:ring-offset-2"
            >
              <Plus className="h-4 w-4" aria-hidden="true" />
              Conectar mi email
            </button>
          </div>
        ) : visibleChannels.length === 0 ? (
          <p className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500">Ningún canal conectado coincide con el filtro.</p>
        ) : (
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
            {visibleChannels.map((channel) => (
              <ChannelCard
                key={channel.id}
                channel={channel}
                testing={testingId === channel.id}
                copied={copiedId === channel.id}
                onTest={() => void handleTest(channel)}
                onComplete={() => completeConnection(channel)}
                onSwitchAccount={() => switchAccount(channel)}
                onDelete={() => void handleDelete(channel)}
                onCopyWebhook={(url) => copyWebhook(url, channel.id)}
              />
            ))}
          </div>
        )}
      </section>

      <section aria-labelledby="disponibles" className="space-y-4">
        <h2 id="disponibles" className="text-lg font-semibold text-slate-900">Disponibles para conectar</h2>
        {available.length === 0 ? (
          <p className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500">No hay más plataformas que coincidan con el filtro.</p>
        ) : (
          CATEGORIES.map((cat) => {
            const items = available.filter((p) => PLATFORMS[p].category === cat.key)
            if (!items.length) return null
            return (
              <div key={cat.key}>
                <h3 className="mb-2 text-sm font-semibold text-slate-700">
                  {cat.label} <span className="font-normal text-slate-400">· {cat.hint}</span>
                </h3>
                <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {items.map((platform) => {
                    const meta = PLATFORMS[platform]
                    const Icon = meta.icon
                    return (
                      <li key={platform}>
                        <button
                          type="button"
                          onClick={() => openModal(platform as ChannelPlatform)}
                          disabled={!businessId}
                          className="flex min-h-[64px] w-full items-center gap-3 rounded-xl border border-slate-200 bg-white p-3 text-left shadow-sm transition-colors hover:border-brand-orange/50 hover:bg-orange-50/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange disabled:opacity-50"
                        >
                          <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${meta.tile}`} aria-hidden="true">
                            <Icon className="h-5 w-5" />
                          </span>
                          <span className="min-w-0 flex-1">
                            <span className="block truncate text-sm font-semibold text-slate-900">{meta.label}</span>
                            <span className="block truncate text-xs text-slate-500">{meta.description}</span>
                          </span>
                          <Plus className="h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
                        </button>
                      </li>
                    )
                  })}
                </ul>
              </div>
            )
          })
        )}
      </section>

      {modalOpen && (
        <ConnectModal
          draft={draft}
          onChange={setDraft}
          onClose={closeModal}
          onSubmit={() => void handleCreate()}
          onOAuth={(p) => void handleOAuth(p)}
          onWhatsApp={() => void handleWhatsApp()}
          saving={saving}
          connecting={connecting}
          error={modalError}
        />
      )}

    </div>
  )
}
