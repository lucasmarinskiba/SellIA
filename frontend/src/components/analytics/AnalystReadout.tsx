'use client'

/**
 * "Lectura del analista" — the account's real numbers, explained.
 *
 * A percentage with no denominator and no sample size is how dashboards get
 * people to change their business over noise. Everything rendered here arrives
 * from GET /data-science/insights already carrying its evidence: the counts
 * behind it, a 95% Wilson interval, and an explicit confidence band. When the
 * sample is too small, the component says so instead of drawing a big number.
 */

import React, { useEffect, useState } from 'react'
import {
  AlertCircle, BarChart3, ChevronDown, Clock, Info, Loader2, TrendingDown, TrendingUp,
} from 'lucide-react'
import { api } from '@/lib/api'

type Confidence = 'insufficient' | 'preliminary' | 'solid'

interface Reading {
  key: string
  title: string
  value: number
  unit: string
  confidence: Confidence
  reading: string
  why_it_matters: string
  direction?: 'up' | 'down' | 'flat'
}

interface PlatformRow {
  platform: string
  conversations: number
  answered: number
  response_rate: number
  confidence: Confidence
  reading: string
}

interface Insights {
  period_days: number
  has_data: boolean
  headline: string
  totals?: {
    conversations: number
    with_customer_message: number
    answered: number
    ai_answered: number
    inbound_messages: number
  }
  readings: Reading[]
  series: { date: string; conversations: number }[]
  by_platform: PlatformRow[]
  peak_hours: { hour: number; inbound: number }[]
  methodology: string[]
}

const CONFIDENCE_BADGE: Record<Confidence, { label: string; className: string }> = {
  insufficient: { label: 'muestra insuficiente', className: 'bg-slate-100 text-slate-600' },
  preliminary: { label: 'lectura preliminar', className: 'bg-amber-50 text-amber-700' },
  solid: { label: 'muestra suficiente', className: 'bg-emerald-50 text-emerald-700' },
}

export default function AnalystReadout(): React.JSX.Element | null {
  const [data, setData] = useState<Insights | null>(null)
  const [loading, setLoading] = useState(true)
  const [showMethod, setShowMethod] = useState(false)

  useEffect(() => {
    let alive = true
    api.get<Insights>('/data-science/insights?days=30')
      .then(res => { if (alive) setData(res.data) })
      .catch(() => { if (alive) setData(null) })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [])

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6 flex items-center gap-3 text-slate-500 text-sm">
        <Loader2 className="w-4 h-4 animate-spin" /> Analizando tus números…
      </div>
    )
  }

  if (!data) return null

  const maxDay = Math.max(1, ...data.series.map(s => s.conversations))
  const peakMax = Math.max(1, ...data.peak_hours.map(h => h.inbound))
  const bestHour = data.peak_hours.reduce<{ hour: number; inbound: number } | null>(
    (best, h) => (best === null || h.inbound > best.inbound ? h : best), null,
  )

  return (
    <div className="space-y-4">
      {/* Titular: la frase que realmente importa hoy */}
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-6">
        <div className="flex items-start gap-3">
          <BarChart3 className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-blue-700 mb-1">
              Lectura del analista · últimos {data.period_days} días
            </p>
            <p className="text-slate-900 font-medium leading-relaxed">{data.headline}</p>
          </div>
        </div>
      </div>

      {!data.has_data && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-600">
          No se dibuja ningún gráfico todavía: sin datos propios, cualquier curva sería inventada.
        </div>
      )}

      {data.has_data && (
        <>
          {data.totals && (
            <div className="grid sm:grid-cols-4 gap-3">
              {[
                { label: 'Conversaciones', value: data.totals.conversations },
                { label: 'Con consulta del cliente', value: data.totals.with_customer_message },
                { label: 'Respondidas', value: data.totals.answered },
                { label: 'Respondidas por la IA', value: data.totals.ai_answered },
              ].map(t => (
                <div key={t.label} className="rounded-xl border border-slate-200 bg-white p-4">
                  <p className="text-2xl font-bold text-slate-900">{t.value}</p>
                  <p className="text-xs text-slate-600 mt-0.5">{t.label}</p>
                </div>
              ))}
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-4">
            {data.readings.map(r => {
              const badge = CONFIDENCE_BADGE[r.confidence]
              return (
                <div key={r.key} className="rounded-xl border border-slate-200 bg-white p-5">
                  <div className="flex items-start justify-between gap-3">
                    <p className="font-medium text-slate-900">{r.title}</p>
                    <span className={`text-[11px] px-2 py-0.5 rounded-full shrink-0 ${badge.className}`}>
                      {badge.label}
                    </span>
                  </div>
                  <p className="text-3xl font-bold text-slate-900 mt-2 flex items-center gap-2">
                    {r.value}<span className="text-base text-slate-400 font-semibold">{r.unit}</span>
                    {r.direction === 'up' && <TrendingUp className="w-5 h-5 text-emerald-500" />}
                    {r.direction === 'down' && <TrendingDown className="w-5 h-5 text-red-500" />}
                  </p>
                  <p className="text-sm text-slate-700 mt-2 leading-relaxed">{r.reading}</p>
                  <p className="text-xs text-slate-500 mt-2 flex gap-1.5">
                    <Info className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                    {r.why_it_matters}
                  </p>
                </div>
              )
            })}
          </div>

          {/* Serie diaria: conteos reales, con los días vacíos visibles como vacíos */}
          <div className="rounded-xl border border-slate-200 bg-white p-5">
            <p className="font-medium text-slate-900 mb-3">Conversaciones por día</p>
            <div className="flex items-end gap-[3px] h-28">
              {data.series.map(s => (
                <div
                  key={s.date}
                  title={`${s.date}: ${s.conversations}`}
                  className="flex-1 bg-blue-500/80 rounded-t hover:bg-blue-600 transition-colors"
                  style={{ height: `${(s.conversations / maxDay) * 100}%`, minHeight: s.conversations ? 2 : 1 }}
                />
              ))}
            </div>
            <div className="flex justify-between text-[11px] text-slate-500 mt-2">
              <span>{data.series[0]?.date}</span>
              <span>máximo en un día: {maxDay}</span>
              <span>{data.series[data.series.length - 1]?.date}</span>
            </div>
          </div>

          {bestHour && bestHour.inbound > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <p className="font-medium text-slate-900 flex items-center gap-2 mb-1">
                <Clock className="w-4 h-4 text-blue-600" /> Cuándo te escriben
              </p>
              <p className="text-sm text-slate-600 mb-3">
                La hora más activa es las {bestHour.hour}:00 ({bestHour.inbound} mensajes).
                Es la franja donde una respuesta lenta cuesta más caro.
              </p>
              <div className="flex items-end gap-[3px] h-16">
                {Array.from({ length: 24 }, (_, hour) => {
                  const found = data.peak_hours.find(h => h.hour === hour)
                  const count = found?.inbound ?? 0
                  return (
                    <div
                      key={hour}
                      title={`${hour}:00 — ${count} mensajes`}
                      className="flex-1 bg-slate-300 rounded-t"
                      style={{ height: `${(count / peakMax) * 100}%`, minHeight: 1 }}
                    />
                  )
                })}
              </div>
              <div className="flex justify-between text-[11px] text-slate-500 mt-1">
                <span>00h</span><span>12h</span><span>23h</span>
              </div>
            </div>
          )}

          {data.by_platform.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white overflow-x-auto">
              <p className="font-medium text-slate-900 p-5 pb-3">Por canal</p>
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-slate-600">
                  <tr>
                    <th className="text-left font-medium px-5 py-2.5">Canal</th>
                    <th className="text-right font-medium px-3 py-2.5">Consultas</th>
                    <th className="text-right font-medium px-3 py-2.5">Respondidas</th>
                    <th className="text-left font-medium px-5 py-2.5">Lectura</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.by_platform.map(p => (
                    <tr key={p.platform}>
                      <td className="px-5 py-3 font-medium text-slate-900">{p.platform}</td>
                      <td className="px-3 py-3 text-right text-slate-700">{p.conversations}</td>
                      <td className="px-3 py-3 text-right text-slate-700">{p.answered}</td>
                      <td className="px-5 py-3 text-slate-600">{p.reading}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {/* Cómo se calculó: auditable, no una caja negra */}
      <div className="rounded-xl border border-slate-200 bg-white">
        <button
          type="button"
          onClick={() => setShowMethod(v => !v)}
          className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-slate-50"
        >
          <span className="font-medium text-slate-900 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-slate-400" /> Cómo se calculó cada número
          </span>
          <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${showMethod ? 'rotate-180' : ''}`} />
        </button>
        {showMethod && (
          <ul className="px-5 pb-5 space-y-2">
            {data.methodology.map((m, i) => (
              <li key={i} className="text-sm text-slate-600 flex gap-2">
                <span className="text-slate-300 shrink-0">·</span>{m}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
