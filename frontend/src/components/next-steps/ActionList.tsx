'use client'

/**
 * The shared renderer for the actions engine.
 *
 * Three pages show the same computed actions through different lenses — what is
 * losing money now (Alertas), what would grow the business (Recomendaciones),
 * and everything in order (Próximos pasos) — so the card, the evidence and the
 * honesty about failed checks live in one place instead of three.
 */

import React, { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import { ArrowRight, CheckCircle2, Info, Loader2, RotateCw } from 'lucide-react'
import { logger } from '@/lib/logger'
import { nextStepsApi, type NextAction, type NextStepsResponse, type Urgency } from '@/lib/nextSteps'

export const URGENCY_STYLE: Record<Urgency, { label: string; dot: string; ring: string }> = {
  alta: { label: 'Urgente', dot: 'bg-red-500', ring: 'border-red-200 bg-red-50/60' },
  media: { label: 'Importante', dot: 'bg-amber-500', ring: 'border-amber-200 bg-amber-50/50' },
  baja: { label: 'Cuando puedas', dot: 'bg-slate-400', ring: 'border-slate-200 bg-white' },
}

export const CHECK_LABELS: Record<string, string> = {
  waiting_conversations: 'consultas sin responder',
  bot_off_where_traffic_is: 'bots apagados con tráfico',
  unpaid_orders: 'órdenes sin cobrar',
  unshipped_orders: 'órdenes sin despachar',
  customers_without_contact: 'órdenes sin contacto del cliente',
  dormant_customers: 'clientes que no vuelven',
  incomplete_profile: 'configuración del negocio',
  ai_not_configured: 'clave de IA',
  channel_gaps: 'canales que faltan',
  reach_opportunity: 'alcance del negocio',
}

export const ActionCard = ({ action }: { action: NextAction }): React.JSX.Element => {
  const style = URGENCY_STYLE[action.urgency] ?? URGENCY_STYLE.baja
  return (
    <div className={`rounded-xl border p-5 ${style.ring}`}>
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="flex items-start gap-3">
          <span className={`w-2 h-2 rounded-full mt-2 shrink-0 ${style.dot}`} />
          <div>
            <p className="font-semibold text-slate-900">{action.title}</p>
            <p className="text-sm text-slate-700 mt-1">{action.evidence}</p>
            <p className="text-xs text-slate-500 mt-2">{action.why}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[10px] uppercase tracking-wide text-slate-400">{style.label}</span>
          <Link
            href={action.where}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800"
          >
            Resolver <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </div>
  )
}

interface Props {
  title: string
  subtitle: string
  /** Which urgencies this lens shows. */
  urgencies: Urgency[]
  emptyTitle: string
  emptyBody: string
}

const ActionList = ({ title, subtitle, urgencies, emptyTitle, emptyBody }: Props): React.JSX.Element => {
  const [data, setData] = useState<NextStepsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [failed, setFailed] = useState(false)

  const load = useCallback(async (): Promise<void> => {
    setLoading(true)
    setFailed(false)
    try {
      setData(await nextStepsApi.actions())
    } catch (e) {
      logger.error(String(e))
      setFailed(true)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void load() }, [load])

  const shown = (data?.actions ?? []).filter(action => urgencies.includes(action.urgency))
  const hidden = (data?.actions ?? []).length - shown.length

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-black text-slate-900">{title}</h1>
          <p className="text-slate-600 mt-2">{subtitle}</p>
        </div>
        <button
          onClick={() => void load()}
          className="px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-600 hover:bg-slate-50 inline-flex items-center gap-2"
        >
          <RotateCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Actualizar
        </button>
      </div>

      {loading && !data && (
        <div className="flex items-center gap-3 text-slate-500 py-10">
          <Loader2 className="w-5 h-5 animate-spin" /> Revisando tu cuenta…
        </div>
      )}

      {failed && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-5">
          <p className="font-semibold text-slate-900">No se pudo revisar tu cuenta.</p>
          <p className="text-sm text-slate-600 mt-1">
            No se muestran avisos de ejemplo mientras tanto: serían indistinguibles de los reales.
          </p>
        </div>
      )}

      {data && shown.length === 0 && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-6">
          <CheckCircle2 className="w-7 h-7 text-emerald-600 mb-2" />
          <p className="font-semibold text-slate-900">{emptyTitle}</p>
          <p className="text-sm text-slate-700 mt-1">{emptyBody}</p>
        </div>
      )}

      {shown.length > 0 && (
        <div className="space-y-3">
          {shown.map(action => <ActionCard key={action.key} action={action} />)}
        </div>
      )}

      {/* The other lens is one click away, and its count is not hidden. */}
      {data && hidden > 0 && (
        <p className="text-xs text-slate-500">
          Hay {hidden} punto(s) más en{' '}
          <Link href="/dashboard/misiones" className="underline hover:text-slate-800">
            Próximos pasos
          </Link>
          , de otra prioridad.
        </p>
      )}

      {data && data.not_checked.length > 0 && (
        <div className="flex items-start gap-2 px-4 py-3 rounded-xl border border-amber-200 bg-amber-50 text-xs text-amber-900">
          <Info className="w-4 h-4 mt-0.5 shrink-0" />
          <span>
            No se pudo revisar: {data.not_checked.map(c => CHECK_LABELS[c] || c).join(' · ')}. Puede
            haber cosas ahí que esta lista no está viendo.
          </span>
        </div>
      )}

      {data && (
        <p className="text-[11px] text-slate-400">
          Revisado sobre tus datos reales: {data.checked.map(c => CHECK_LABELS[c] || c).join(' · ')} ·{' '}
          {new Date(data.generated_at).toLocaleString('es-AR')}
        </p>
      )}
    </div>
  )
}

export default ActionList
