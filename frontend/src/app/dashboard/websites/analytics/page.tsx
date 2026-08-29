'use client'

import { Suspense, useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import {
  ArrowLeft,
  TrendingUp,
  Eye,
  Users,
  ShoppingCart,
  BarChart3,
  Loader,
} from 'lucide-react'

/* ============================================================
   ANALYTICS DASHBOARD — Tier 3 Events, Conversions, Metrics
   ============================================================ */

interface AnalyticsSummary {
  period_days: number
  total_views: number
  unique_sessions: number
  total_conversions: number
  conversion_rate: number
  total_conversion_value: number
  avg_views_per_session: number
}

interface PageAnalytics {
  page_url: string
  page_title: string
  views: number
  sessions: number
}

interface ConversionAnalytics {
  type: string
  count: number
  total_value: number
  avg_value: number
}

function AnalyticsDashboardContent() {
  const searchParams = useSearchParams()
  const businessId = searchParams?.get('businessId') || ''

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [mounted, setMounted] = useState(false)
  const [days, setDays] = useState(30)

  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)
  const [pages, setPages] = useState<PageAnalytics[]>([])
  const [conversions, setConversions] = useState<ConversionAnalytics[]>([])

  useEffect(() => {
    setMounted(true)
    if (businessId) {
      fetchData()
    }
  }, [businessId, days])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError('')

      const [summaryRes, pagesRes, conversionsRes] = await Promise.all([
        fetch(`/api/v1/businesses/${businessId}/analytics/summary?days=${days}`),
        fetch(`/api/v1/businesses/${businessId}/analytics/pages?days=${days}`),
        fetch(`/api/v1/businesses/${businessId}/analytics/conversions?days=${days}`),
      ])

      if (!summaryRes.ok || !pagesRes.ok || !conversionsRes.ok) {
        throw new Error('Error cargando datos de analytics')
      }

      const summaryData = await summaryRes.json()
      const pagesData = await pagesRes.json()
      const conversionsData = await conversionsRes.json()

      setSummary(summaryData)
      setPages(pagesData.pages || [])
      setConversions(conversionsData.conversions || [])
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (!mounted) return null

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center gap-4">
          <Link
            href="/dashboard/websites"
            className="p-2 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 transition-all"
          >
            <ArrowLeft className="w-5 h-5 text-slate-900" />
          </Link>
          <div>
            <h1 className="text-4xl font-bold text-slate-900">Analytics</h1>
            <p className="text-lg text-slate-600">Monitorea el rendimiento de tu website</p>
          </div>
        </div>

        {error && (
          <div className="mb-6 flex items-start gap-3 p-4 rounded-lg bg-red-50 border border-red-200">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Date filter */}
        <div className="mb-6 flex gap-2">
          {[7, 30, 90].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                days === d
                  ? 'bg-cyan-500 text-white'
                  : 'bg-white border border-slate-200 text-slate-900 hover:bg-slate-50'
              }`}
            >
              {d} días
            </button>
          ))}
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader className="w-8 h-8 text-cyan-500 animate-spin" />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Summary cards */}
            {summary && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="rounded-lg bg-white border border-slate-200 p-6">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-semibold text-slate-600 uppercase">Vistas</p>
                    <Eye className="w-5 h-5 text-cyan-500" />
                  </div>
                  <p className="text-3xl font-bold text-slate-900">{summary.total_views.toLocaleString()}</p>
                  <p className="text-xs text-slate-500 mt-2">En {summary.period_days} días</p>
                </div>

                <div className="rounded-lg bg-white border border-slate-200 p-6">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-semibold text-slate-600 uppercase">Sesiones</p>
                    <Users className="w-5 h-5 text-indigo-500" />
                  </div>
                  <p className="text-3xl font-bold text-slate-900">{summary.unique_sessions.toLocaleString()}</p>
                  <p className="text-xs text-slate-500 mt-2">
                    {(summary.avg_views_per_session).toFixed(1)} vistas/sesión
                  </p>
                </div>

                <div className="rounded-lg bg-white border border-slate-200 p-6">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-semibold text-slate-600 uppercase">Conversiones</p>
                    <ShoppingCart className="w-5 h-5 text-emerald-500" />
                  </div>
                  <p className="text-3xl font-bold text-slate-900">{summary.total_conversions.toLocaleString()}</p>
                  <p className="text-xs text-slate-500 mt-2">
                    Tasa: {summary.conversion_rate.toFixed(2)}%
                  </p>
                </div>

                <div className="rounded-lg bg-white border border-slate-200 p-6">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-semibold text-slate-600 uppercase">Valor</p>
                    <TrendingUp className="w-5 h-5 text-pink-500" />
                  </div>
                  <p className="text-3xl font-bold text-slate-900">
                    ${summary.total_conversion_value.toFixed(2)}
                  </p>
                  <p className="text-xs text-slate-500 mt-2">Valor total de conversiones</p>
                </div>
              </div>
            )}

            {/* Top pages */}
            {pages.length > 0 && (
              <div className="rounded-lg bg-white border border-slate-200 p-8">
                <div className="flex items-center gap-2 mb-6">
                  <BarChart3 className="w-5 h-5 text-slate-900" />
                  <h2 className="text-2xl font-bold text-slate-900">Páginas más visitadas</h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-200">
                        <th className="text-left py-3 px-4 font-semibold text-slate-600">Página</th>
                        <th className="text-right py-3 px-4 font-semibold text-slate-600">Vistas</th>
                        <th className="text-right py-3 px-4 font-semibold text-slate-600">Sesiones</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pages.map((page, idx) => (
                        <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                          <td className="py-3 px-4">
                            <div>
                              <p className="font-semibold text-slate-900">
                                {page.page_title || 'Sin título'}
                              </p>
                              <p className="text-xs text-slate-500">{page.page_url}</p>
                            </div>
                          </td>
                          <td className="text-right py-3 px-4 text-slate-900">
                            {page.views.toLocaleString()}
                          </td>
                          <td className="text-right py-3 px-4 text-slate-900">
                            {page.sessions.toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Conversions */}
            {conversions.length > 0 && (
              <div className="rounded-lg bg-white border border-slate-200 p-8">
                <div className="flex items-center gap-2 mb-6">
                  <ShoppingCart className="w-5 h-5 text-slate-900" />
                  <h2 className="text-2xl font-bold text-slate-900">Conversiones por tipo</h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-200">
                        <th className="text-left py-3 px-4 font-semibold text-slate-600">Tipo</th>
                        <th className="text-right py-3 px-4 font-semibold text-slate-600">Cantidad</th>
                        <th className="text-right py-3 px-4 font-semibold text-slate-600">Valor total</th>
                        <th className="text-right py-3 px-4 font-semibold text-slate-600">Valor promedio</th>
                      </tr>
                    </thead>
                    <tbody>
                      {conversions.map((conv, idx) => (
                        <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                          <td className="py-3 px-4 font-semibold text-slate-900">{conv.type}</td>
                          <td className="text-right py-3 px-4 text-slate-900">
                            {conv.count.toLocaleString()}
                          </td>
                          <td className="text-right py-3 px-4 text-slate-900">
                            ${conv.total_value.toFixed(2)}
                          </td>
                          <td className="text-right py-3 px-4 text-slate-900">
                            ${conv.avg_value.toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Empty state */}
            {pages.length === 0 && conversions.length === 0 && (
              <div className="rounded-lg bg-white border border-slate-200 p-12 text-center">
                <Eye className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-slate-900 mb-2">Sin datos de analytics</h3>
                <p className="text-slate-600">
                  Aún no hay eventos registrados. Integra el script de tracking en tu website para empezar a recopilar datos.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default function AnalyticsDashboardPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><div className="animate-spin">Loading...</div></div>}>
      <AnalyticsDashboardContent />
    </Suspense>
  )
}
