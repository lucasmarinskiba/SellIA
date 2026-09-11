'use client'

/**
 * Sales charts, drawn from the account's real orders.
 *
 * Rules this component follows, because a chart lies more easily than a number:
 *
 * - A day with no sales is drawn as zero, never interpolated away.
 * - Amounts are shown per currency. Nothing is summed across currencies, and
 *   the secondary ones are listed beside the main one instead of folded in.
 * - Every chart carries the analyst's reading underneath, with the count it is
 *   based on. When the sample is too small, the reading says so and the chart
 *   is still drawn — hiding it would hide the fact that data exists but is thin.
 */

import React, { useCallback, useEffect, useState } from 'react'
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Line, LineChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { AlertTriangle, BarChart3, Loader2, Repeat, TrendingDown, TrendingUp, Users } from 'lucide-react'
import { logger } from '@/lib/logger'
import { salesAnalyticsApi, type Confidence, type Reading, type SalesAnalysis } from '@/lib/salesAnalytics'

const CONFIDENCE_STYLE: Record<Confidence, { label: string; className: string }> = {
  solid: { label: 'dato firme', className: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  preliminary: { label: 'preliminar', className: 'bg-amber-50 text-amber-700 border-amber-200' },
  insufficient: { label: 'muestra chica', className: 'bg-slate-100 text-slate-600 border-slate-200' },
}

const PALETTE = ['#0F766E', '#B45309', '#4338CA', '#9D174D', '#15803D', '#0E7490']

const money = (value: number, currency: string): string =>
  `${value.toLocaleString('es-AR', { maximumFractionDigits: 0 })} ${currency}`

const round = (value: unknown): string =>
  Number(value ?? 0).toLocaleString('es-AR', { maximumFractionDigits: 0 })

/** Recharts 3 types tooltip callbacks as ReactNode/ValueType, so coerce here. */
const asDate = (label: unknown): string =>
  label ? new Date(String(label)).toLocaleDateString('es-AR') : ''

const Card = ({ title, subtitle, children }: {
  title: string
  subtitle?: string
  children: React.ReactNode
}): React.JSX.Element => (
  <div className="bg-white rounded-lg border border-slate-200 p-5">
    <h3 className="text-base font-bold text-slate-900">{title}</h3>
    {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
    <div className="mt-4">{children}</div>
  </div>
)

const ReadingNote = ({ reading }: { reading: Reading }): React.JSX.Element => {
  const style = CONFIDENCE_STYLE[reading.confidence] ?? CONFIDENCE_STYLE.insufficient
  return (
    <div className="border-t border-slate-100 pt-3 mt-3">
      <div className="flex items-start gap-2">
        <span className={`text-[10px] px-1.5 py-0.5 rounded border shrink-0 ${style.className}`}>
          {style.label}
        </span>
        <p className="text-xs text-slate-600 leading-relaxed">{reading.reading}</p>
      </div>
      {reading.why_it_matters && (
        <p className="text-[11px] text-slate-400 mt-1.5 pl-1">{reading.why_it_matters}</p>
      )}
    </div>
  )
}

const SalesAnalytics = (): React.JSX.Element => {
  const [data, setData] = useState<SalesAnalysis | null>(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(90)
  const [failed, setFailed] = useState(false)

  const load = useCallback(async (): Promise<void> => {
    setLoading(true)
    setFailed(false)
    try {
      setData(await salesAnalyticsApi.get(days))
    } catch (e) {
      logger.error(String(e))
      setFailed(true)
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => { void load() }, [load])

  if (loading && !data) {
    return (
      <div className="flex items-center gap-3 text-slate-500 py-8">
        <Loader2 className="w-5 h-5 animate-spin" /> Analizando tus ventas…
      </div>
    )
  }

  if (failed || !data) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-5">
        <p className="font-semibold text-slate-900">No se pudo leer el análisis de ventas.</p>
        <p className="text-sm text-slate-600 mt-1">No se muestran números de ejemplo mientras tanto.</p>
      </div>
    )
  }

  const currency = data.main_currency ?? ''
  const byKey = (key: string): Reading | undefined => data.readings.find(r => r.key === key)

  const periodPicker = (
    <div className="flex gap-1">
      {[30, 90, 180, 365].map(option => (
        <button
          key={option}
          onClick={() => setDays(option)}
          className={`px-2.5 py-1 rounded-md text-xs border transition-colors ${
            days === option
              ? 'bg-slate-900 text-white border-slate-900'
              : 'bg-white text-slate-600 border-slate-200 hover:border-slate-400'
          }`}
        >
          {option === 365 ? '1 año' : `${option}d`}
        </button>
      ))}
    </div>
  )

  if (!data.has_data) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900">Análisis de ventas</h2>
          {periodPicker}
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-6">
          <BarChart3 className="w-8 h-8 text-slate-300 mb-3" />
          <p className="text-sm text-slate-700">{data.headline}</p>
          <p className="text-xs text-slate-400 mt-1">
            No se dibuja ningún gráfico de muestra: un gráfico de ejemplo es indistinguible de uno real.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Análisis de ventas</h2>
          <p className="text-sm text-slate-600">{data.headline}</p>
        </div>
        {periodPicker}
      </div>

      {/* Per currency, side by side — never added together */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {data.currencies.map(c => (
          <div
            key={c.currency}
            className={`bg-white rounded-lg border p-4 ${c.is_main ? 'border-slate-300' : 'border-slate-200'}`}
          >
            <div className="flex items-center justify-between">
              <p className="text-xs text-slate-500">{c.currency} · {c.orders} órdenes</p>
              {c.is_main && <span className="text-[10px] text-slate-400">principal</span>}
            </div>
            <p className="text-2xl font-black text-slate-900 mt-1">
              {c.revenue.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
            </p>
            <p className="text-xs text-slate-500 mt-0.5">
              Cobrado {c.collected.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
            </p>
            {c.median_ticket !== null && (
              <p className="text-[11px] text-slate-400 mt-1">
                Ticket mediano {c.median_ticket.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
                {c.q1_ticket !== null && c.q3_ticket !== null && (
                  <> · mitad del medio entre {c.q1_ticket.toLocaleString('es-AR', { maximumFractionDigits: 0 })} y {c.q3_ticket.toLocaleString('es-AR', { maximumFractionDigits: 0 })}</>
                )}
              </p>
            )}
          </div>
        ))}
        {data.currencies.length > 1 && (
          <div className="rounded-lg border border-dashed border-slate-300 p-4 flex items-center">
            <p className="text-[11px] text-slate-500">
              Hay ventas en {data.currencies.length} monedas y no se suman entre sí: sin un tipo de cambio
              propio, cualquier total combinado sería inventado.
            </p>
          </div>
        )}
      </div>

      {/* Revenue over time */}
      <Card
        title={`Facturación por día (${currency})`}
        subtitle="Los días sin ventas se dibujan en cero, no se saltean."
      >
        <ResponsiveContainer width="100%" height={240}>
          <AreaChart data={data.revenue_series}>
            <defs>
              <linearGradient id="revFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={PALETTE[0]} stopOpacity={0.35} />
                <stop offset="100%" stopColor={PALETTE[0]} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: '#94A3B8' }}
              tickFormatter={(value) => String(value).slice(5)}
              minTickGap={24}
            />
            <YAxis tick={{ fontSize: 10, fill: '#94A3B8' }} width={56} />
            <Tooltip
              formatter={(value, name) =>
                String(name) === 'revenue'
                  ? [money(Number(value ?? 0), currency), 'Facturado']
                  : [round(value), 'Órdenes']
              }
              labelFormatter={asDate}
            />
            <Area type="monotone" dataKey="revenue" stroke={PALETTE[0]} fill="url(#revFill)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
        {byKey('weekly_orders') && <ReadingNote reading={byKey('weekly_orders')!} />}
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Orders per day, as a separate line: volume and money move apart */}
        <Card title="Órdenes por día" subtitle="El volumen se mira aparte del monto: pueden moverse en sentidos opuestos.">
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={data.revenue_series}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10, fill: '#94A3B8' }}
                tickFormatter={(value) => String(value).slice(5)}
                minTickGap={24}
              />
              <YAxis tick={{ fontSize: 10, fill: '#94A3B8' }} allowDecimals={false} width={32} />
              <Tooltip labelFormatter={asDate} />
              <Line type="monotone" dataKey="orders" stroke={PALETTE[2]} strokeWidth={2} dot={false} name="Órdenes" />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        {/* Ticket histogram */}
        <Card
          title={`Cómo se reparten tus tickets (${currency})`}
          subtitle="Barras reales por rango. Los rangos vacíos se muestran: ahí está la brecha."
        >
          {data.ticket_distribution.length === 0 ? (
            <p className="text-xs text-slate-500">Todavía no hay montos para distribuir.</p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={data.ticket_distribution}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
                <XAxis
                  dataKey="from"
                  tick={{ fontSize: 10, fill: '#94A3B8' }}
                  tickFormatter={(value) => round(value)}
                />
                <YAxis tick={{ fontSize: 10, fill: '#94A3B8' }} allowDecimals={false} width={32} />
                <Tooltip
                  formatter={(value) => [`${round(value)} órdenes`, '']}
                  labelFormatter={(_label, payload) => {
                    const row = payload?.[0]?.payload as { from: number; to: number } | undefined
                    return row ? `Entre ${round(row.from)} y ${round(row.to)} ${currency}` : ''
                  }}
                />
                <Bar dataKey="orders" fill={PALETTE[1]} radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
          {byKey('median_ticket') && <ReadingNote reading={byKey('median_ticket')!} />}
        </Card>
      </div>

      {/* Funnel */}
      <Card title="De la orden a la entrega" subtitle="Cuántas órdenes llegan a cada paso, sobre el total creado.">
        <div className="space-y-2">
          {data.status_funnel.map((step, index) => (
            <div key={step.step}>
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="text-slate-700">{step.step}</span>
                <span className="text-slate-500">
                  {step.count}
                  {step.of_created !== null && <span className="text-slate-400"> · {step.of_created}%</span>}
                </span>
              </div>
              <div className="h-2.5 rounded-full bg-slate-100 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${step.of_created ?? 0}%`,
                    background: PALETTE[index % PALETTE.length],
                  }}
                />
              </div>
            </div>
          ))}
        </div>
        {data.lost && (data.lost.cancelled > 0 || data.lost.refunded > 0) && (
          <p className="text-[11px] text-slate-500 mt-3 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
            {data.lost.cancelled} canceladas y {data.lost.refunded} reembolsadas en el período.
          </p>
        )}
        {byKey('paid_rate') && <ReadingNote reading={byKey('paid_rate')!} />}
        {byKey('hours_to_payment') && <ReadingNote reading={byKey('hours_to_payment')!} />}
      </Card>

      {/* Platform comparison */}
      {data.by_platform.length > 0 && (
        <Card
          title={`Plataformas comparadas (${currency})`}
          subtitle="Facturación y ticket mediano de cada una, con su tasa de cobro."
        >
          <ResponsiveContainer width="100%" height={Math.max(160, data.by_platform.length * 46)}>
            <BarChart data={data.by_platform} layout="vertical" margin={{ left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 10, fill: '#94A3B8' }} />
              <YAxis
                type="category"
                dataKey="platform"
                tick={{ fontSize: 11, fill: '#475569' }}
                width={110}
              />
              <Tooltip formatter={(value) => money(Number(value ?? 0), currency)} />
              <Bar dataKey="revenue" name="Facturado" radius={[0, 3, 3, 0]}>
                {data.by_platform.map((row, index) => (
                  <Cell key={row.platform} fill={PALETTE[index % PALETTE.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <table className="w-full text-xs mt-2">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th className="text-left py-1.5">Plataforma</th>
                <th className="text-right py-1.5">Órdenes</th>
                <th className="text-right py-1.5">Ticket mediano</th>
                <th className="text-right py-1.5">Pagadas</th>
              </tr>
            </thead>
            <tbody>
              {data.by_platform.map(row => (
                <tr key={row.platform} className="border-b border-slate-100">
                  <td className="py-1.5 text-slate-800">{row.platform}</td>
                  <td className="py-1.5 text-right text-slate-600 tabular-nums">{row.orders}</td>
                  <td className="py-1.5 text-right text-slate-600 tabular-nums">
                    {row.median_ticket !== null ? row.median_ticket.toLocaleString('es-AR', { maximumFractionDigits: 0 }) : '—'}
                  </td>
                  <td className="py-1.5 text-right text-slate-600 tabular-nums" title={row.reading}>
                    {row.paid_rate !== null ? `${row.paid_rate}%` : '—'}
                    <span className={`ml-1 text-[9px] ${row.confidence === 'solid' ? 'text-emerald-600' : 'text-slate-400'}`}>
                      {row.confidence === 'solid' ? '' : '(muestra chica)'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* When people buy */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card title="Qué día se vende" subtitle="Órdenes por día de la semana, en todo el período.">
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={data.by_weekday}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
              <XAxis dataKey="weekday" tick={{ fontSize: 10, fill: '#94A3B8' }} tickFormatter={(v) => String(v).slice(0, 3)} />
              <YAxis tick={{ fontSize: 10, fill: '#94A3B8' }} allowDecimals={false} width={28} />
              <Tooltip />
              <Bar dataKey="orders" name="Órdenes" fill={PALETTE[4]} radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          {byKey('best_weekday') && <ReadingNote reading={byKey('best_weekday')!} />}
        </Card>

        <Card title="A qué hora se compra" subtitle="Hora de la orden, en la zona horaria del servidor (UTC).">
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={data.by_hour}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
              <XAxis dataKey="hour" tick={{ fontSize: 9, fill: '#94A3B8' }} interval={2} />
              <YAxis tick={{ fontSize: 10, fill: '#94A3B8' }} allowDecimals={false} width={28} />
              <Tooltip labelFormatter={(label) => `${label}:00 UTC`} />
              <Bar dataKey="orders" name="Órdenes" fill={PALETTE[5]} radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Customers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {data.repeat_customers && (
          <Card title="Clientes que vuelven" subtitle="Identificados por email o teléfono, que la base guarda cifrados.">
            <div className="flex items-baseline gap-3">
              <Repeat className="w-5 h-5 text-slate-400" />
              <p className="text-3xl font-black text-slate-900">
                {data.repeat_customers.repeat_rate !== null ? `${data.repeat_customers.repeat_rate}%` : '—'}
              </p>
              <p className="text-xs text-slate-500">
                {data.repeat_customers.returning_customers} de {data.repeat_customers.identified_customers} clientes
              </p>
            </div>
            <p className="text-xs text-slate-600 mt-3 leading-relaxed">{data.repeat_customers.reading}</p>
            {byKey('repeat_rate')?.why_it_matters && (
              <p className="text-[11px] text-slate-400 mt-1.5">{byKey('repeat_rate')!.why_it_matters}</p>
            )}
          </Card>
        )}

        {data.concentration && (
          <Card title="Concentración de la facturación" subtitle="Cuánto depende el mes de unos pocos compradores.">
            <div className="flex items-baseline gap-3">
              <Users className="w-5 h-5 text-slate-400" />
              <p className="text-3xl font-black text-slate-900">
                {data.concentration.top_share !== null ? `${data.concentration.top_share}%` : '—'}
              </p>
              {data.concentration.top_share !== null && (
                <p className="text-xs text-slate-500 flex items-center gap-1">
                  {data.concentration.top_share >= 60
                    ? <><TrendingDown className="w-3.5 h-3.5 text-amber-500" /> dependencia alta</>
                    : <><TrendingUp className="w-3.5 h-3.5 text-emerald-600" /> bien repartida</>}
                </p>
              )}
            </div>
            <p className="text-xs text-slate-600 mt-3 leading-relaxed">{data.concentration.reading}</p>
          </Card>
        )}
      </div>

      <p className="text-[11px] text-slate-400">
        Calculado sobre {data.period_days} días de órdenes reales de tu cuenta, el{' '}
        {new Date(data.generated_at).toLocaleString('es-AR')}. Las medianas se usan en lugar de promedios
        porque una venta excepcional mueve un promedio y no describe a ningún cliente.
      </p>
    </div>
  )
}

export default SalesAnalytics
