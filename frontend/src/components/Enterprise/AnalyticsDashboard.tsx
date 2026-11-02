'use client'

import { useCallback, useEffect, useState } from 'react'
import { TrendingUp, TrendingDown, Target, Zap } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { api } from '@/lib/api'

type Direction = 'up' | 'down' | 'neutral'

interface KPICard {
  label: string
  current_value: number
  unit: string
  trend: number | null
  trend_direction: Direction
}

interface PipelineData {
  total_value: number
  stages: Record<string, number>
  projected_revenue_30d: number
}

interface DashboardData {
  currency: string
  other_currency_deals: number
  kpi_cards: KPICard[]
  pipeline: PipelineData
}

const TIME_RANGES = ['today', 'week', 'month', 'quarter'] as const

const formatKpi = (value: number, unit: string): string =>
  unit === '%' ? `${value.toFixed(1)}%` : value.toLocaleString('es-AR', { maximumFractionDigits: 2 })

const getTrendIcon = (direction: Direction) => {
  switch (direction) {
    case 'up':
      return <TrendingUp className="w-4 h-4 text-green-600" />
    case 'down':
      return <TrendingDown className="w-4 h-4 text-red-600" />
    default:
      return <Zap className="w-4 h-4 text-slate-400" />
  }
}

const getTrendColor = (direction: Direction): string => {
  switch (direction) {
    case 'up':
      return 'text-green-600'
    case 'down':
      return 'text-red-600'
    default:
      return 'text-slate-600'
  }
}

// The dashboard only shows numbers the server computed from this account's deals.
// On failure it says so; it never falls back to sample figures.
export default function AnalyticsDashboard({ userId }: { userId: string }) {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [timeRange, setTimeRange] = useState<(typeof TIME_RANGES)[number]>('month')

  const fetchDashboard = useCallback(async () => {
    setLoading(true)
    setError(false)
    try {
      const res = await api.get<DashboardData>(`/analytics/dashboard/${userId}`, {
        params: { time_range: timeRange },
      })
      setData(res.data)
    } catch (err) {
      console.error('Dashboard fetch error:', err)
      setData(null)
      setError(true)
    } finally {
      setLoading(false)
    }
  }, [userId, timeRange])

  useEffect(() => {
    fetchDashboard()
  }, [fetchDashboard])

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-brand-night">Performance Analytics</h2>
          <p className="text-sm text-slate-600 mt-1">Números calculados con tus propias ventas</p>
        </div>
        <div className="flex gap-2">
          {TIME_RANGES.map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                timeRange === range
                  ? 'bg-brand-orange text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {range.charAt(0).toUpperCase() + range.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <Card className="p-6 flex items-center justify-between">
          <p className="text-sm text-slate-700">No pudimos cargar el dashboard.</p>
          <button onClick={fetchDashboard} className="px-4 py-2 rounded-lg text-sm bg-slate-100 hover:bg-slate-200">
            Reintentar
          </button>
        </Card>
      )}

      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="p-6 animate-pulse">
              <div className="h-4 bg-slate-200 rounded w-3/4 mb-4" />
              <div className="h-8 bg-slate-200 rounded w-1/2 mb-2" />
              <div className="h-3 bg-slate-100 rounded w-2/3" />
            </Card>
          ))}
        </div>
      )}

      {!loading && data && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {data.kpi_cards.map((kpi) => (
              <Card key={kpi.label} className="p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <p className="text-sm font-medium text-slate-600">{kpi.label}</p>
                  {getTrendIcon(kpi.trend_direction)}
                </div>

                <p className="text-3xl font-bold text-brand-night">
                  {formatKpi(kpi.current_value, kpi.unit)}
                  {kpi.unit !== '%' && <span className="text-lg text-slate-500 ml-2">{kpi.unit}</span>}
                </p>

                {kpi.trend !== null && (
                  <p className={`mt-3 text-sm font-semibold ${getTrendColor(kpi.trend_direction)}`}>
                    {kpi.trend > 0 ? '+' : ''}
                    {kpi.trend.toFixed(1)}%
                  </p>
                )}
              </Card>
            ))}
          </div>

          {data.other_currency_deals > 0 && (
            <p className="text-sm text-slate-600">
              {data.other_currency_deals} negocio(s) en otra moneda no se suman a los totales de {data.currency}.
            </p>
          )}

          <Card className="p-6">
            <h3 className="text-lg font-bold text-brand-night mb-4 flex items-center gap-2">
              <Target className="w-5 h-5 text-blue-500" />
              Pipeline
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-slate-600">Valor abierto</p>
                <p className="text-2xl font-bold text-brand-night">
                  {data.pipeline.total_value.toLocaleString('es-AR', { maximumFractionDigits: 2 })} {data.currency}
                </p>
              </div>

              <div>
                <p className="text-sm font-semibold text-slate-700 mb-2">Negocios por etapa</p>
                {Object.keys(data.pipeline.stages).length === 0 ? (
                  <p className="text-xs text-slate-500">Todavía no tenés negocios abiertos.</p>
                ) : (
                  <div className="space-y-1">
                    {Object.entries(data.pipeline.stages).map(([stage, count]) => (
                      <div key={stage} className="flex justify-between text-xs">
                        <span className="text-slate-600 capitalize">{stage.replace(/_/g, ' ')}</span>
                        <span className="font-bold text-brand-night">{count}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="p-4 bg-green-50 rounded-lg border-l-4 border-l-green-500">
                <p className="text-xs text-slate-600">Ingreso proyectado (30 días)</p>
                <p className="text-xl font-bold text-green-700">
                  {data.pipeline.projected_revenue_30d.toLocaleString('es-AR', { maximumFractionDigits: 2 })} {data.currency}
                </p>
                <p className="text-xs text-slate-600 mt-1">Según la probabilidad de cada negocio</p>
              </div>
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
