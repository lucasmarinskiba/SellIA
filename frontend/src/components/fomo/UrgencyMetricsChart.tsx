'use client'

import React, { useEffect, useState } from 'react'
import { Loader2, TrendingUp } from 'lucide-react'
import { fomaPhase1Api, type UrgencyMetric } from '@/lib/fomoPhase1'

interface UrgencyMetricsChartProps {
  businessId: string
}

export function UrgencyMetricsChart({ businessId }: UrgencyMetricsChartProps): React.JSX.Element {
  const [metrics, setMetrics] = useState<UrgencyMetric[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadMetrics = async () => {
      try {
        const data = await fomaPhase1Api.getUrgencyMetrics(businessId)
        setMetrics(data.triggers)
      } catch (error) {
        console.error('Error loading urgency metrics:', error)
      } finally {
        setLoading(false)
      }
    }

    void loadMetrics()
  }, [businessId])

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-3 py-12">
        <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
        <span className="text-slate-600">Analizando triggers…</span>
      </div>
    )
  }

  if (metrics.length === 0) {
    return (
      <div className="rounded-lg border border-slate-200 bg-slate-50 p-6 text-center">
        <TrendingUp className="w-10 h-10 text-slate-300 mx-auto mb-3" />
        <p className="text-sm text-slate-600">
          Sin datos de urgencia aún. Genera FOMO copy para comenzar a medir.
        </p>
      </div>
    )
  }

  const maxCtr = Math.max(...metrics.map(m => m.avg_ctr))

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="w-5 h-5 text-blue-600" />
        <h3 className="font-semibold text-slate-900">CTR por Tipo de Urgencia</h3>
      </div>

      {metrics.map((metric, idx) => (
        <div key={idx} className="space-y-1">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium text-slate-900 capitalize">
              {metric.trigger === 'limited_stock'
                ? 'Stock Limitado'
                : metric.trigger === 'ending_soon'
                  ? 'Termina Pronto'
                  : metric.trigger === 'best_seller'
                    ? 'Bestseller'
                    : metric.trigger}
            </span>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-600">{metric.conversions} conversiones</span>
              <span className="font-bold text-slate-900">{metric.avg_ctr.toFixed(1)}%</span>
            </div>
          </div>

          {/* Bar */}
          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-500"
              style={{
                width: `${(metric.avg_ctr / maxCtr) * 100}%`,
              }}
            />
          </div>
        </div>
      ))}

      {/* Recommendation */}
      {metrics.length > 0 && (
        <div className="mt-6 p-4 rounded-lg bg-blue-50 border border-blue-200">
          <p className="text-sm text-blue-900">
            <span className="font-semibold">Recomendación:</span> El trigger{' '}
            <span className="font-bold capitalize">
              {metrics[0].trigger === 'limited_stock'
                ? 'Stock Limitado'
                : metrics[0].trigger === 'ending_soon'
                  ? 'Termina Pronto'
                  : 'Bestseller'}
            </span>{' '}
            tiene mayor impacto. Úsalo más en nuevos listings.
          </p>
        </div>
      )}
    </div>
  )
}
