'use client'

/**
 * Vendedor Multiplataforma.
 *
 * One card per platform the account actually sells on, plus the consolidated
 * position. Three rules hold this screen together:
 *
 * 1. Capabilities are real. A platform whose connector cannot import orders
 *    says exactly that, instead of rendering a zero that reads as "no sales".
 * 2. Costs are declared, never assumed. A commission rate guessed from a public
 *    rate card would be wrong for most sellers and would quietly produce a
 *    wrong margin, so the margin stays null until the seller declares what they
 *    are really charged.
 * 3. Actions only appear where the connector can perform them, from the same
 *    introspection that produced the capability matrix.
 */

import React, { useCallback, useEffect, useState } from 'react'
import {
  AlertTriangle, Check, ChevronDown, Loader2, Package, PlayCircle, Plug, RefreshCw,
  MessageSquare, Settings2, TrendingUp, XCircle,
} from 'lucide-react'
import {
  commerceApi, COST_LABEL, formatMoney,
  type CommerceOverview, type PendingQuestion, type PlatformCosts, type PlatformRow,
  type SyncResult,
} from '@/lib/platformCommerce'
import { platformMeta } from '@/lib/platformMeta'

const SettingsForm = ({
  platform, current, onSaved,
}: {
  platform: PlatformRow
  current: PlatformRow['settings']
  onSaved: () => void
}): React.JSX.Element => {
  const [values, setValues] = useState({
    commission_percent: current?.commission_percent ?? '',
    fixed_fee_per_order: current?.fixed_fee_per_order ?? '',
    cogs_percent: current?.cogs_percent ?? '',
    monthly_fixed_cost: current?.monthly_fixed_cost ?? '',
    monthly_ad_spend: current?.monthly_ad_spend ?? '',
  })
  const [saving, setSaving] = useState(false)

  const fields: { key: keyof typeof values; label: string; hint: string }[] = [
    { key: 'commission_percent', label: 'Comisión (%)', hint: 'Lo que te cobra la plataforma por venta' },
    { key: 'fixed_fee_per_order', label: 'Cargo fijo por venta', hint: 'Monto fijo por operación, si lo hay' },
    { key: 'cogs_percent', label: 'Costo de producto (%)', hint: 'Cuánto del precio es costo tuyo' },
    { key: 'monthly_fixed_cost', label: 'Costo fijo mensual', hint: 'Suscripción, alquiler de tienda…' },
    { key: 'monthly_ad_spend', label: 'Publicidad mensual', hint: 'Lo que invertís en anuncios acá' },
  ]

  const save = async (): Promise<void> => {
    setSaving(true)
    try {
      const body = Object.fromEntries(
        Object.entries(values)
          .filter(([, v]) => v !== '' && v !== null)
          .map(([k, v]) => [k, Number(v)]),
      )
      await commerceApi.saveSettings(platform.platform, body)
      onSaved()
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
      <p className="text-sm font-medium text-slate-900">Tus números en esta plataforma</p>
      <p className="text-xs text-slate-600 mt-0.5 mb-3">
        Sólo vos sabés estos valores. No los estimamos: sin ellos el margen no se calcula, en vez
        de mostrarte una ganancia que no es.
      </p>
      <div className="grid sm:grid-cols-2 gap-3">
        {fields.map(field => (
          <div key={field.key}>
            <label className="block text-xs font-medium text-slate-700 mb-1">{field.label}</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={values[field.key]}
              onChange={e => setValues(prev => ({ ...prev, [field.key]: e.target.value }))}
              className="w-full px-3 py-1.5 rounded-lg border border-slate-200 text-sm text-slate-900"
            />
            <p className="text-[11px] text-slate-500 mt-0.5">{field.hint}</p>
          </div>
        ))}
      </div>
      <button
        type="button"
        onClick={save}
        disabled={saving}
        className="mt-3 px-4 py-1.5 rounded-lg bg-slate-900 text-white text-xs font-semibold hover:bg-slate-800 disabled:opacity-50 inline-flex items-center gap-2"
      >
        {saving && <Loader2 className="w-3.5 h-3.5 animate-spin" />} Guardar
      </button>
    </div>
  )
}

export default function MultiPlatformSeller(): React.JSX.Element {
  const [data, setData] = useState<CommerceOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [syncResults, setSyncResults] = useState<SyncResult[] | null>(null)
  const [busy, setBusy] = useState<string | null>(null)
  const [results, setResults] = useState<Record<string, string>>({})
  const [openSettings, setOpenSettings] = useState<string | null>(null)
  const [openDetail, setOpenDetail] = useState<string | null>(null)
  const [pending, setPending] = useState<{ platform: string; items: PendingQuestion[] } | null>(null)

  const load = useCallback(async (): Promise<void> => {
    try {
      setData(await commerceApi.overview())
    } catch {
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void load() }, [load])

  const runSync = async (): Promise<void> => {
    setSyncing(true)
    try {
      const res = await commerceApi.sync()
      setSyncResults(res.results)
      await load()
    } finally {
      setSyncing(false)
    }
  }

  /** Answering buyers reaches real customers, so the open questions are shown
   *  first and the AI only writes after the seller confirms. */
  const previewPending = async (platform: string): Promise<void> => {
    setBusy(`${platform}:answer_pending`)
    try {
      const res = await commerceApi.pendingQuestions(platform)
      setPending({ platform, items: res.pending })
    } finally {
      setBusy(null)
    }
  }

  const runAction = async (platform: string, action: string): Promise<void> => {
    const id = `${platform}:${action}`
    setBusy(id)
    try {
      const res = await commerceApi.runAction(platform, action)
      setResults(prev => ({ ...prev, [id]: res.detail || 'Listo.' }))
      await load()
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setResults(prev => ({ ...prev, [id]: detail || 'No se pudo ejecutar.' }))
    } finally {
      setBusy(null)
    }
  }

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 flex items-center justify-center gap-3 text-slate-500 text-sm">
        <Loader2 className="w-4 h-4 animate-spin" /> Leyendo tus plataformas…
      </div>
    )
  }

  if (!data) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-6">
        <p className="font-semibold text-slate-900">No se pudo leer tu operación.</p>
        <p className="text-sm text-slate-600 mt-1">No se muestran cifras estimadas mientras tanto.</p>
      </div>
    )
  }

  const c = data.consolidated

  return (
    <div className="space-y-5">
      {/* ── Balance englobante ── */}
      <div className="rounded-xl border border-slate-200 bg-white p-6">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <p className="text-sm font-medium text-slate-600">
              Balance de todas tus plataformas · últimos {data.period_days} días
            </p>
            <p className="text-4xl font-bold text-slate-900 mt-1">
              {formatMoney(c.revenue, c.currency)}
            </p>
            <p className="text-sm text-slate-600 mt-1">
              facturado en {c.orders} venta(s) cobradas
            </p>
          </div>
          <button
            type="button"
            onClick={runSync}
            disabled={syncing}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-200 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            {syncing ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            Traer mis ventas
          </button>
        </div>

        <div className="grid sm:grid-cols-3 gap-4 mt-5">
          <div>
            <p className="text-xs text-slate-500">Costos conocidos</p>
            <p className="text-xl font-bold text-slate-900">{formatMoney(c.known_costs, c.currency)}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Ganancia</p>
            {c.margin !== null ? (
              <p className={`text-xl font-bold ${c.margin >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                {formatMoney(c.margin, c.currency)}
              </p>
            ) : (
              <p className="text-sm text-amber-700 mt-1">
                No calculable todavía: falta declarar costos en al menos una plataforma.
              </p>
            )}
          </div>
          <div>
            <p className="text-xs text-slate-500">Plataformas</p>
            <p className="text-xl font-bold text-slate-900">{data.platforms.length}</p>
          </div>
        </div>

        {c.mixed_currencies && (
          <p className="text-xs text-amber-700 mt-3 flex gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            Tenés ventas en más de una moneda. El total no las convierte: sumar pesos con dólares
            daría un número que no significa nada.
          </p>
        )}
        {c.note && <p className="text-sm text-slate-600 mt-3">{c.note}</p>}
      </div>

      {syncResults && (
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <p className="text-sm font-medium text-slate-900 mb-2">Resultado de la importación</p>
          <ul className="space-y-1">
            {syncResults.map(r => (
              <li key={r.platform} className="text-sm text-slate-700 flex gap-2">
                {r.supported && r.ok
                  ? <Check className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                  : <XCircle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />}
                <span>
                  <strong>{platformMeta(r.platform).label}:</strong>{' '}
                  {r.supported && r.ok
                    ? `${r.imported} nuevas, ${r.updated} actualizadas (de ${r.fetched ?? 0} traídas)`
                    : r.reason}
                </span>
              </li>
            ))}
            {syncResults.length === 0 && (
              <li className="text-sm text-slate-600">
                Ninguna de tus plataformas conectadas puede importar ventas todavía.
              </li>
            )}
          </ul>
        </div>
      )}

      {/* ── Una tarjeta por plataforma ── */}
      {data.platforms.length === 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-8 text-center">
          <Package className="w-8 h-8 text-slate-300 mx-auto mb-3" />
          <p className="font-semibold text-slate-900">Todavía no conectaste ninguna plataforma</p>
          <p className="text-sm text-slate-600 mt-1">
            Conectá donde ya vendés y acá vas a ver, por cada una, sus ventas reales y su margen.
          </p>
        </div>
      )}

      {data.platforms.map(row => {
        const meta = platformMeta(row.platform)
        const detailOpen = openDetail === row.platform
        return (
          <div key={row.platform} className="rounded-xl border border-slate-200 bg-white">
            <div className="p-5 flex items-start justify-between gap-4 flex-wrap">
              <div className="flex items-start gap-3">
                <span
                  className="w-9 h-9 rounded-lg grid place-items-center text-white text-xs font-bold shrink-0"
                  style={{ background: meta.color }}
                >
                  {meta.label.slice(0, 2).toUpperCase()}
                </span>
                <div>
                  <p className="font-semibold text-slate-900">{meta.label}</p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {row.connection
                      ? row.connection.connected
                        ? `Conectado · ${row.connection.status}`
                        : 'Desconectado'
                      : 'Sin conexión configurada'}
                    {row.connection?.status_message && ` · ${row.connection.status_message}`}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-6">
                <div className="text-right">
                  <p className="text-xs text-slate-500">Facturado</p>
                  <p className="text-lg font-bold text-slate-900">
                    {formatMoney(row.revenue, row.currency)}
                  </p>
                  <p className="text-[11px] text-slate-500">{row.orders} venta(s)</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500">Ganancia</p>
                  {row.margin !== null ? (
                    <>
                      <p className={`text-lg font-bold ${row.margin >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                        {formatMoney(row.margin, row.currency)}
                      </p>
                      {row.margin_percent !== null && (
                        <p className="text-[11px] text-slate-500">{row.margin_percent}% del precio</p>
                      )}
                    </>
                  ) : (
                    <p className="text-xs text-amber-700 max-w-[160px]">Falta declarar costos</p>
                  )}
                </div>
              </div>
            </div>

            {row.missing.length > 0 && (
              <div className="px-5 pb-4">
                <p className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-lg p-3">
                  Para saber si ganás plata acá falta: {row.missing.join(', ')}.
                </p>
              </div>
            )}

            <div className="px-5 pb-4 flex items-center gap-2 flex-wrap">
              {row.actions.filter(a => a.available).map(action => {
                const id = `${row.platform}:${action.key}`
                return (
                  <button
                    key={action.key}
                    type="button"
                    onClick={() => (
                      action.key === 'answer_pending'
                        ? previewPending(row.platform)
                        : runAction(row.platform, action.key)
                    )}
                    disabled={busy === id}
                    title={action.detail}
                    className="px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 disabled:opacity-50 inline-flex items-center gap-1.5"
                  >
                    {busy === id
                      ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      : <PlayCircle className="w-3.5 h-3.5" />}
                    {action.label}
                  </button>
                )
              })}
              <button
                type="button"
                onClick={() => setOpenSettings(openSettings === row.platform ? null : row.platform)}
                className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-700 hover:bg-slate-50 inline-flex items-center gap-1.5"
              >
                <Settings2 className="w-3.5 h-3.5" /> Mis costos acá
              </button>
              <button
                type="button"
                onClick={() => setOpenDetail(detailOpen ? null : row.platform)}
                className="px-3 py-1.5 rounded-lg text-xs font-medium text-blue-600 hover:underline inline-flex items-center gap-1"
              >
                Detalle
                <ChevronDown className={`w-3.5 h-3.5 transition-transform ${detailOpen ? 'rotate-180' : ''}`} />
              </button>
            </div>

            {Object.entries(results)
              .filter(([id]) => id.startsWith(`${row.platform}:`))
              .map(([id, text]) => (
                <p key={id} className="px-5 pb-3 text-sm text-slate-700 flex gap-2">
                  <Check className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />{text}
                </p>
              ))}

            {openSettings === row.platform && (
              <div className="px-5 pb-5">
                <SettingsForm platform={row} current={row.settings} onSaved={load} />
              </div>
            )}

            {detailOpen && (
              <div className="px-5 pb-5 grid md:grid-cols-2 gap-5 border-t border-slate-100 pt-4">
                <div>
                  <p className="text-sm font-medium text-slate-900 mb-2 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-slate-400" /> Desglose
                  </p>
                  <ul className="space-y-1">
                    <li className="text-sm flex justify-between">
                      <span className="text-slate-700">Facturado</span>
                      <span className="font-medium text-slate-900">
                        {formatMoney(row.revenue, row.currency)}
                      </span>
                    </li>
                    {(Object.keys(row.costs) as (keyof PlatformCosts)[]).map(key => (
                      <li key={key} className="text-sm flex justify-between">
                        <span className="text-slate-600">{COST_LABEL[key]}</span>
                        {row.costs[key] === null ? (
                          <span className="text-amber-700 text-xs">sin declarar</span>
                        ) : (
                          <span className="text-slate-700">
                            −{formatMoney(row.costs[key] as number, row.currency)}
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <p className="text-sm font-medium text-slate-900 mb-2 flex items-center gap-2">
                    <Plug className="w-4 h-4 text-slate-400" /> Qué puede hacer SellIA acá
                  </p>
                  <ul className="space-y-1.5">
                    {row.capabilities.map(cap => (
                      <li key={cap.key} className="text-sm flex gap-2">
                        {cap.available
                          ? <Check className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                          : <XCircle className="w-4 h-4 text-slate-300 shrink-0 mt-0.5" />}
                        <span>
                          <span className={cap.available ? 'text-slate-900' : 'text-slate-500'}>
                            {cap.label}
                          </span>
                          <span className="block text-xs text-slate-500">{cap.detail}</span>
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        )
      })}

      <p className="text-xs text-slate-500">
        Lo facturado sale de tus órdenes reales. Los costos salen de lo que declaraste por
        plataforma: no se estiman comisiones ni costos de producto, porque una tasa supuesta
        produciría una ganancia equivocada con aspecto de dato.
      </p>

      {/* Consultas reales sin responder: se muestran antes de que la IA
          escriba, porque el mensaje sale con el nombre del vendedor. */}
      {pending && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-5 border-b border-slate-100">
              <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-blue-600" />
                {pending.items.length} consulta(s) sin responder en {platformMeta(pending.platform).label}
              </h3>
              <p className="text-sm text-slate-600 mt-1">
                La IA va a redactar y enviar una respuesta a cada uno de estos compradores reales,
                por tu canal y con tu nombre.
              </p>
            </div>

            <div className="p-5">
              {pending.items.length === 0 ? (
                <p className="text-sm text-slate-600">
                  No hay consultas colgadas ahora mismo. Nada que responder.
                </p>
              ) : (
                <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200">
                  {pending.items.map(item => (
                    <li key={item.conversation_id} className="p-3">
                      <p className="text-sm font-medium text-slate-900">{item.name}</p>
                      <p className="text-sm text-slate-600 mt-0.5">{item.question}</p>
                      {item.asked_at && (
                        <p className="text-[11px] text-slate-500 mt-1">
                          preguntó el {new Date(item.asked_at).toLocaleString('es-AR')}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="p-5 border-t border-slate-100 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setPending(null)}
                className="px-4 py-2 rounded-lg border border-slate-200 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Cancelar
              </button>
              <button
                type="button"
                disabled={pending.items.length === 0 || busy !== null}
                onClick={async () => {
                  const platform = pending.platform
                  setPending(null)
                  await runAction(platform, 'answer_pending')
                }}
                className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-50"
              >
                Que la IA responda a {pending.items.length}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
