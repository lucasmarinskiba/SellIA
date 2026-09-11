'use client'

/**
 * Próximos pasos — qué hacer ahora, con el número que lo justifica.
 *
 * Esta página era "Misiones": pedía /missions, /missions/diagnostics/list y
 * /business-context/recommended-playbooks, y las tres rutas no existen en este
 * backend. Devolvían 404, así que la pantalla cargaba, preguntaba y mostraba
 * nada. Ahora lee /next-steps, que se calcula sobre las filas reales de la
 * cuenta: consultas sin responder, órdenes sin cobrar, órdenes cobradas sin
 * despachar, clientes sin contacto, clientes que no vuelven, bots apagados
 * donde hay tráfico y configuración que le falta a la IA.
 *
 * Ninguna acción promete un porcentaje de mejora: dice el hecho y por qué
 * importa, y la decisión queda en quien conoce su negocio.
 */

import React, { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import {
  AlertCircle, ArrowRight, CheckCircle2, Info, Loader2, RotateCw,
} from 'lucide-react'
import { logger } from '@/lib/logger'
import { nextStepsApi, type NextAction, type NextStepsResponse, type Urgency } from '@/lib/nextSteps'

const URGENCY_STYLE: Record<Urgency, { label: string; dot: string; ring: string }> = {
  alta: { label: 'Urgente', dot: 'bg-red-500', ring: 'border-red-200 bg-red-50/60' },
  media: { label: 'Importante', dot: 'bg-amber-500', ring: 'border-amber-200 bg-amber-50/50' },
  baja: { label: 'Cuando puedas', dot: 'bg-slate-400', ring: 'border-slate-200 bg-white' },
}

const CHECK_LABELS: Record<string, string> = {
  waiting_conversations: 'consultas sin responder',
  bot_off_where_traffic_is: 'bots apagados con tráfico',
  unpaid_orders: 'órdenes sin cobrar',
  unshipped_orders: 'órdenes sin despachar',
  customers_without_contact: 'órdenes sin contacto del cliente',
  dormant_customers: 'clientes que no vuelven',
  incomplete_profile: 'configuración del negocio',
  ai_not_configured: 'clave de IA',
}

const ActionCard = ({ action }: { action: NextAction }): React.JSX.Element => {
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

export default function ProximosPasosPage(): React.JSX.Element {
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

  const urgent = (data?.actions ?? []).filter(a => a.urgency === 'alta').length

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-black text-slate-900">Próximos pasos</h1>
          <p className="text-slate-600 mt-2">
            Calculado sobre tus propias conversaciones, órdenes y clientes. Si no hay nada acá, no hay
            nada pendiente que se pueda medir.
          </p>
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
            No se muestran tareas de ejemplo mientras tanto: serían indistinguibles de las reales.
          </p>
        </div>
      )}

      {data && data.actions.length === 0 && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-6">
          <CheckCircle2 className="w-7 h-7 text-emerald-600 mb-2" />
          <p className="font-semibold text-slate-900">No hay nada pendiente de lo que se puede medir.</p>
          <p className="text-sm text-slate-700 mt-1">
            Ninguna consulta sin responder, ninguna orden trabada, ningún cliente sin contacto.
          </p>
        </div>
      )}

      {data && data.actions.length > 0 && (
        <>
          {urgent > 0 && (
            <p className="text-sm text-slate-700 inline-flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-500" />
              {urgent} {urgent === 1 ? 'cosa urgente' : 'cosas urgentes'}: hay plata o un cliente en
              juego ahora mismo.
            </p>
          )}
          <div className="space-y-3">
            {data.actions.map(action => (
              <ActionCard key={action.key} action={action} />
            ))}
          </div>
        </>
      )}

      {/* Lo que no se pudo revisar: una lista vacía no es prueba de que todo esté bien. */}
      {data && data.not_checked.length > 0 && (
        <div className="flex items-start gap-2 px-4 py-3 rounded-xl border border-amber-200 bg-amber-50 text-xs text-amber-900">
          <Info className="w-4 h-4 mt-0.5 shrink-0" />
          <span>
            No se pudo revisar: {data.not_checked.map(c => CHECK_LABELS[c] || c).join(' · ')}. Puede
            haber pendientes ahí que esta lista no está viendo.
          </span>
        </div>
      )}

      {data && (
        <p className="text-[11px] text-slate-400">
          Revisado: {data.checked.map(c => CHECK_LABELS[c] || c).join(' · ')} ·{' '}
          {new Date(data.generated_at).toLocaleString('es-AR')}
        </p>
      )}
    </div>
  )
}
