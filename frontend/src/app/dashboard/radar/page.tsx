'use client'

/**
 * Cola de atención — a quién responder primero, y por qué.
 *
 * Esta página era el "Radar": pedía /social-sellers/{id}, /social-sellers/.../radar
 * y un executeRadarAction, y ninguna de esas rutas existe en este backend (404).
 * Mostraba un tablero de temperaturas sobre datos que nunca llegaban.
 *
 * Ahora muestra las conversaciones realmente abiertas, ordenadas por lo que está
 * en juego: primero las marcadas para una persona, después quienes ya compraron,
 * después quienes preguntaron precio, stock o envío, y dentro de cada grupo quien
 * espera desde más tiempo. El criterio se muestra en pantalla en vez de esconderse
 * en un puntaje, y cada fila dice por qué está donde está.
 */

import React, { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import { ArrowRight, Clock, Inbox, Loader2, RotateCw } from 'lucide-react'
import { logger } from '@/lib/logger'
import { formatAmounts, nextStepsApi, type QueueResponse } from '@/lib/nextSteps'
import { platformMeta } from '@/lib/platformMeta'

const waitLabel = (hours: number): string => {
  if (hours < 1) return `${Math.round(hours * 60)} min`
  if (hours < 48) return `${hours} h`
  return `${Math.round(hours / 24)} días`
}

export default function ColaDeAtencionPage(): React.JSX.Element {
  const [data, setData] = useState<QueueResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [failed, setFailed] = useState(false)

  const load = useCallback(async (): Promise<void> => {
    setLoading(true)
    setFailed(false)
    try {
      setData(await nextStepsApi.queue(30))
    } catch (e) {
      logger.error(String(e))
      setFailed(true)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void load() }, [load])

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-black text-slate-900">Cola de atención</h1>
          <p className="text-slate-600 mt-2">
            Las conversaciones donde el último mensaje es del comprador, en el orden que conviene
            responder.
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
          <Loader2 className="w-5 h-5 animate-spin" /> Revisando tus conversaciones…
        </div>
      )}

      {failed && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-5">
          <p className="font-semibold text-slate-900">No se pudo leer la cola.</p>
          <p className="text-sm text-slate-600 mt-1">No se muestran conversaciones de ejemplo.</p>
        </div>
      )}

      {data && data.items.length === 0 && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-6">
          <Inbox className="w-7 h-7 text-emerald-600 mb-2" />
          <p className="font-semibold text-slate-900">No hay nadie esperando respuesta.</p>
          <p className="text-sm text-slate-700 mt-1">
            Todas las conversaciones abiertas tienen la última palabra de tu lado.
          </p>
        </div>
      )}

      {data && data.items.length > 0 && (
        <>
          <p className="text-sm text-slate-700">
            {data.waiting} esperando. {data.items.length < data.waiting && `Se muestran las primeras ${data.items.length}. `}
          </p>
          {data.criteria && (
            <p className="text-xs text-slate-500 border-l-2 border-slate-200 pl-3">{data.criteria}</p>
          )}

          <div className="space-y-3">
            {data.items.map((item, index) => {
              const meta = platformMeta(item.platform)
              return (
                <div
                  key={item.conversation_id}
                  className={`rounded-xl border p-4 ${
                    item.awaiting_human ? 'border-amber-300 bg-amber-50/50' : 'border-slate-200 bg-white'
                  }`}
                >
                  <div className="flex items-start justify-between gap-4 flex-wrap">
                    <div className="flex items-start gap-3">
                      <span className="text-slate-300 text-sm font-bold w-5 text-right shrink-0">
                        {index + 1}
                      </span>
                      <span
                        className="w-8 h-8 rounded-lg grid place-items-center text-white text-[10px] font-bold shrink-0"
                        style={{ background: meta.color }}
                      >
                        {meta.label.slice(0, 2).toUpperCase()}
                      </span>
                      <div>
                        <p className="font-semibold text-slate-900">
                          {item.who}
                          <span className="ml-2 text-xs font-normal text-slate-500">{meta.label}</span>
                        </p>
                        <p className="text-sm text-slate-700 mt-0.5">“{item.last_message}”</p>
                        <p className="text-[11px] text-slate-500 mt-1.5">{item.reasons.join(' · ')}</p>
                        {Object.keys(item.spent).length > 0 && (
                          <p className="text-[11px] text-slate-500">
                            Compró por {formatAmounts(item.spent)}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-slate-500 inline-flex items-center gap-1 whitespace-nowrap">
                        <Clock className="w-3.5 h-3.5" /> {waitLabel(item.waiting_hours)}
                      </span>
                      <Link
                        href="/dashboard/conversaciones"
                        className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800"
                      >
                        Responder <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}

      {data && (
        <p className="text-[11px] text-slate-400">
          Calculado el {new Date(data.generated_at).toLocaleString('es-AR')} sobre los mensajes reales
          de tus canales conectados.
        </p>
      )}
    </div>
  )
}
