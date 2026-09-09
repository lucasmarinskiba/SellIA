'use client'

/**
 * Conectar plataformas — de verdad.
 *
 * The page used to list platforms the account could supposedly sell on without
 * any way to actually connect one: the connectors read specific credential keys
 * (mercadolibre needs client_id/client_secret, whatsapp needs
 * api_token/phone_number_id…) that no form ever asked for.
 *
 * This renders the real per-platform form from GET /channel-setup/catalog,
 * saves a real ChannelConnection, and then lets the user run the real
 * validate_credentials() check against the platform. Nothing here reports a
 * connection as working on the strength of a saved form: "Funcionando" only
 * appears once messages have actually flowed.
 */

import React, { useCallback, useEffect, useState } from 'react'
import {
  AlertCircle, CheckCircle2, ExternalLink, Loader2, Lock, Plug, RefreshCw, X,
} from 'lucide-react'
import { api } from '@/lib/api'

type State = 'live' | 'configured' | 'incomplete' | 'not_connected'

interface Field {
  key: string
  label: string
  secret: boolean
}

interface Connection {
  id: string
  business_id: string
  name: string
  status: string
  status_message: string | null
  webhook_url: string | null
  last_sync_at: string | null
  credentials: Record<string, unknown>
  missing_required: string[]
  traffic: { conversations: number; inbound_messages: number; outbound_messages: number }
}

interface PlatformEntry {
  platform: string
  label: string
  group: string
  oauth: boolean
  required: Field[]
  optional: Field[]
  help: string
  docs_url: string
  connection: Connection | null
  state: State
}

interface Catalog {
  business_id: string | null
  business_name: string | null
  platforms: PlatformEntry[]
  connected_count: number
}

const GROUP_LABEL: Record<string, string> = {
  mensajeria: 'Mensajería',
  redes: 'Redes sociales',
  marketplace: 'Marketplaces',
  ecommerce: 'Tu e-commerce',
}

const STATE_BADGE: Record<State, { label: string; className: string }> = {
  live: { label: 'Funcionando', className: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  configured: { label: 'Configurado, sin tráfico', className: 'bg-blue-50 text-blue-700 border-blue-200' },
  incomplete: { label: 'Faltan datos', className: 'bg-amber-50 text-amber-700 border-amber-200' },
  not_connected: { label: 'Sin conectar', className: 'bg-slate-50 text-slate-500 border-slate-200' },
}

export default function ChannelConnectPanel(): React.JSX.Element {
  const [catalog, setCatalog] = useState<Catalog | null>(null)
  const [loading, setLoading] = useState(true)
  const [openPlatform, setOpenPlatform] = useState<PlatformEntry | null>(null)
  const [values, setValues] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async (): Promise<void> => {
    try {
      const res = await api.get<Catalog>('/channel-setup/catalog')
      setCatalog(res.data)
    } catch {
      setCatalog(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void reload() }, [reload])

  const openForm = (entry: PlatformEntry): void => {
    setOpenPlatform(entry)
    setValues({})
    setError(null)
  }

  const save = async (): Promise<void> => {
    if (!openPlatform || !catalog?.business_id) return
    setSaving(true)
    setError(null)
    const filled = Object.fromEntries(
      Object.entries(values).filter(([, v]) => v.trim() !== ''),
    )
    try {
      if (openPlatform.connection) {
        await api.put(
          `/businesses/${catalog.business_id}/channels/${openPlatform.connection.id}`,
          { credentials: { ...openPlatform.connection.credentials, ...filled } },
        )
      } else {
        await api.post(`/businesses/${catalog.business_id}/channels`, {
          platform: openPlatform.platform,
          name: openPlatform.label,
          credentials: filled,
        })
      }
      setOpenPlatform(null)
      await reload()
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(detail || 'No se pudo guardar la conexión.')
    } finally {
      setSaving(false)
    }
  }

  const testConnection = async (entry: PlatformEntry): Promise<void> => {
    if (!entry.connection || !catalog?.business_id) return
    setTesting(entry.platform)
    try {
      const res = await api.post<{ valid: boolean; detail?: string }>(
        `/businesses/${catalog.business_id}/channels/${entry.connection.id}/test`,
      )
      setTestResult(prev => ({
        ...prev,
        [entry.platform]: res.data.valid
          ? 'La plataforma aceptó tus credenciales.'
          : `La plataforma las rechazó: ${res.data.detail ?? 'credenciales inválidas'}`,
      }))
      await reload()
    } catch {
      setTestResult(prev => ({ ...prev, [entry.platform]: 'No se pudo probar la conexión.' }))
    } finally {
      setTesting(null)
    }
  }

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6 flex items-center gap-3 text-slate-500 text-sm">
        <Loader2 className="w-4 h-4 animate-spin" /> Leyendo tus plataformas…
      </div>
    )
  }

  if (!catalog) return <></>

  if (!catalog.business_id) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6">
        <p className="font-semibold text-slate-900">Creá tu negocio para conectar plataformas</p>
        <p className="text-sm text-slate-600 mt-1">
          Las conexiones se guardan contra un negocio tuyo. Sin negocio no hay dónde guardarlas.
        </p>
      </div>
    )
  }

  const groups = ['mensajeria', 'redes', 'marketplace', 'ecommerce']

  return (
    <div className="space-y-5">
      <div className="rounded-xl border border-slate-200 bg-white p-5 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="font-semibold text-slate-900 flex items-center gap-2">
            <Plug className="w-4 h-4 text-blue-600" /> Conectar plataformas
          </h2>
          <p className="text-sm text-slate-600 mt-0.5">
            {catalog.connected_count > 0
              ? `${catalog.connected_count} plataforma(s) con mensajes reales pasando por SellIA.`
              : 'Todavía ninguna plataforma tuvo tráfico real. Conectá la primera para que la IA empiece a responder.'}
          </p>
        </div>
        <button
          type="button"
          onClick={reload}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 text-sm text-slate-600 hover:bg-slate-50"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Actualizar
        </button>
      </div>

      {groups.map(group => {
        const entries = catalog.platforms.filter(p => p.group === group)
        if (entries.length === 0) return null
        return (
          <div key={group}>
            <h3 className="text-sm font-semibold text-slate-700 mb-2">{GROUP_LABEL[group] ?? group}</h3>
            <div className="grid sm:grid-cols-2 gap-3">
              {entries.map(entry => {
                const badge = STATE_BADGE[entry.state]
                const conn = entry.connection
                return (
                  <div key={entry.platform} className="rounded-xl border border-slate-200 bg-white p-4">
                    <div className="flex items-start justify-between gap-2">
                      <p className="font-medium text-slate-900">{entry.label}</p>
                      <span className={`text-[11px] px-2 py-0.5 rounded-full border shrink-0 ${badge.className}`}>
                        {badge.label}
                      </span>
                    </div>

                    {conn && conn.missing_required.length > 0 && (
                      <p className="text-xs text-amber-700 mt-2">
                        Falta cargar: {conn.missing_required.join(', ')}
                      </p>
                    )}

                    {conn && entry.state === 'live' && (
                      <p className="text-xs text-slate-600 mt-2">
                        {conn.traffic.conversations} conversaciones · {conn.traffic.inbound_messages} mensajes
                        recibidos · {conn.traffic.outbound_messages} enviados
                      </p>
                    )}

                    {conn && entry.state === 'configured' && (
                      <p className="text-xs text-slate-600 mt-2">
                        Credenciales completas, pero todavía no pasó ningún mensaje. Configurá el webhook
                        en la plataforma para que las consultas lleguen acá.
                      </p>
                    )}

                    {conn?.status_message && (
                      <p className="text-xs text-red-600 mt-2">{conn.status_message}</p>
                    )}

                    {testResult[entry.platform] && (
                      <p className="text-xs text-slate-700 mt-2 flex gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                        {testResult[entry.platform]}
                      </p>
                    )}

                    {conn?.webhook_url && (
                      <p className="text-[11px] text-slate-500 mt-2 break-all">
                        Webhook: <span className="font-mono">{conn.webhook_url}</span>
                      </p>
                    )}

                    <div className="flex items-center gap-2 mt-3">
                      <button
                        type="button"
                        onClick={() => openForm(entry)}
                        className="px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700"
                      >
                        {conn ? 'Editar credenciales' : 'Conectar'}
                      </button>
                      {conn && (
                        <button
                          type="button"
                          onClick={() => testConnection(entry)}
                          disabled={testing === entry.platform}
                          className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 inline-flex items-center gap-1.5"
                        >
                          {testing === entry.platform && <Loader2 className="w-3 h-3 animate-spin" />}
                          Probar conexión
                        </button>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )
      })}

      {/* Formulario real con los campos que el conector realmente lee */}
      {openPlatform && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="p-5 border-b border-slate-100 flex items-start justify-between gap-3">
              <div>
                <h3 className="font-semibold text-slate-900">Conectar {openPlatform.label}</h3>
                <p className="text-sm text-slate-600 mt-1">{openPlatform.help}</p>
                {openPlatform.docs_url && (
                  <a
                    href={openPlatform.docs_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:underline inline-flex items-center gap-1 mt-1"
                  >
                    Dónde se sacan estos datos <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
              <button
                type="button"
                onClick={() => setOpenPlatform(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 space-y-4">
              {[...openPlatform.required, ...openPlatform.optional].map(field => {
                const isRequired = openPlatform.required.some(f => f.key === field.key)
                const alreadySet = openPlatform.connection?.credentials?.[field.key]
                return (
                  <div key={field.key}>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      {field.label}
                      {!isRequired && <span className="text-slate-400 font-normal"> (opcional)</span>}
                      {field.secret && <Lock className="w-3 h-3 inline ml-1 text-slate-400" />}
                    </label>
                    <input
                      type={field.secret ? 'password' : 'text'}
                      value={values[field.key] ?? ''}
                      onChange={e => setValues(prev => ({ ...prev, [field.key]: e.target.value }))}
                      placeholder={alreadySet ? 'Ya configurado — dejalo vacío para no cambiarlo' : ''}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-900 placeholder:text-slate-400"
                    />
                  </div>
                )
              })}

              {error && (
                <p className="text-sm text-red-600 flex gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" /> {error}
                </p>
              )}

              <p className="text-xs text-slate-500">
                Las credenciales se guardan en tu cuenta y nunca se devuelven al navegador: al volver
                a abrir este formulario vas a ver &quot;ya configurado&quot;, no el valor.
              </p>
            </div>

            <div className="p-5 border-t border-slate-100 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setOpenPlatform(null)}
                className="px-4 py-2 rounded-lg border border-slate-200 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={save}
                disabled={saving}
                className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 inline-flex items-center gap-2"
              >
                {saving && <Loader2 className="w-4 h-4 animate-spin" />} Guardar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
