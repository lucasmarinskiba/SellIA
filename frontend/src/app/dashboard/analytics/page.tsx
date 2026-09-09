'use client'

/**
 * Analytics — métricas reales de la cuenta.
 *
 * Antes mostraba "$47,300 (+12%) · 234 clientes únicos (+8%) · 2.3h (-5%) ·
 * Performance 94% (+3%)": cuatro constantes con tendencias inventadas, sin
 * ninguna fuente detrás. Ahora todo sale del snapshot real del negocio, y lo
 * que no se puede medir hoy se dice en vez de rellenarse.
 */

import { TrendingUp, MessageSquare, Bot, Plug, Loader2 } from 'lucide-react'
import { useBusinessSnapshot, formatMoney } from '@/lib/businessSnapshot'
import AnalystReadout from '@/components/analytics/AnalystReadout'

export default function AnalyticsPage() {
  const { snapshot, loading, unavailable } = useBusinessSnapshot()

  const rev = snapshot?.revenue
  const conv = snapshot?.conversations
  const channels = snapshot?.channels ?? []

  const metrics = [
    {
      label: 'Cobrado',
      value: rev ? formatMoney(rev.paid_amount, rev.currency) : '—',
      hint: rev ? `${rev.orders_paid} órdenes pagadas de ${rev.orders_total}` : '',
      icon: TrendingUp,
    },
    {
      label: 'Conversaciones',
      value: conv ? String(conv.total) : '—',
      hint: conv ? `${conv.inbound} con consultas entrantes` : '',
      icon: MessageSquare,
    },
    {
      label: 'Tasa de respuesta',
      value: conv && conv.inbound > 0 ? `${conv.response_rate}%` : '—',
      hint: conv && conv.inbound > 0
        ? `${conv.answered} de ${conv.inbound} respondidas`
        : 'todavía no entraron consultas',
      icon: Bot,
    },
    {
      label: 'Canales conectados',
      value: String(channels.length),
      hint: channels.length > 0
        ? channels.map(c => c.platform).join(', ')
        : 'ninguno conectado todavía',
      icon: Plug,
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-black text-slate-900">Analytics</h1>
        <p className="text-slate-600 mt-2">
          {snapshot?.business.name
            ? `Métricas reales de ${snapshot.business.name}`
            : 'Métricas reales de tu cuenta'}
        </p>
      </div>

      {loading && (
        <div className="flex items-center gap-3 text-slate-500 py-10">
          <Loader2 className="w-5 h-5 animate-spin" /> Leyendo tus métricas…
        </div>
      )}

      {!loading && unavailable && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-6">
          <p className="font-semibold text-slate-900">No se pudo leer tu cuenta.</p>
          <p className="text-sm text-slate-600 mt-1">No se muestran métricas de ejemplo mientras tanto.</p>
        </div>
      )}

      {!loading && !unavailable && (
        <>
          {/* Lectura del analista: cada número con su evidencia (n, intervalo,
              confianza) en vez de un porcentaje suelto sin denominador. */}
          <AnalystReadout />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {metrics.map((metric) => {
              const Icon = metric.icon
              return (
                <div key={metric.label} className="bg-white rounded-lg border border-slate-200 p-6">
                  <Icon className="text-slate-400 mb-4" size={24} />
                  <p className="text-slate-600 text-sm mb-1">{metric.label}</p>
                  <p className="text-2xl font-black text-slate-900">{metric.value}</p>
                  {metric.hint && <p className="text-xs text-slate-500 mt-1">{metric.hint}</p>}
                </div>
              )
            })}
          </div>

          {channels.length > 0 && (
            <div className="bg-white rounded-lg border border-slate-200 p-6">
              <h2 className="text-lg font-bold text-slate-900 mb-4">Actividad por canal</h2>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Canal</th>
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Conversaciones</th>
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Respuestas de la IA</th>
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Último mensaje</th>
                  </tr>
                </thead>
                <tbody>
                  {channels.map(ch => (
                    <tr key={`${ch.platform}-${ch.name}`} className="border-b border-slate-100">
                      <td className="py-3 px-2 text-slate-900 font-medium">{ch.name}</td>
                      <td className="py-3 px-2 text-slate-700">{ch.conversations}</td>
                      <td className="py-3 px-2 text-slate-700">{ch.ai_replies}</td>
                      <td className="py-3 px-2 text-slate-600">
                        {ch.last_message_at ? new Date(ch.last_message_at).toLocaleString('es-AR') : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <p className="text-xs text-slate-500">
            La serie diaria y las comparaciones semanales de arriba se cuentan sobre las fechas reales
            de tus conversaciones. Un período sin actividad se dibuja vacío, nunca se rellena.
          </p>
        </>
      )}
    </div>
  )
}
