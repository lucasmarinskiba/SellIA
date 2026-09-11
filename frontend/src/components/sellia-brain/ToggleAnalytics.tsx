'use client'

import { useEffect, useState } from 'react'
import { UUID } from 'crypto'
import { ToggleDashboardResponse, ToggleDashboardStats } from '@/lib/api/toggles'

interface ToggleAnalyticsProps {
  businessId: UUID
}

export default function ToggleAnalytics({ businessId }: ToggleAnalyticsProps) {
  const [dashboard, setDashboard] = useState<ToggleDashboardResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboard()
  }, [businessId])

  const loadDashboard = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/v1/automations/toggles/dashboard/${businessId}`)
      if (res.ok) {
        const data = await res.json()
        setDashboard(data)
      }
    } catch (err) {
      console.error('Error loading dashboard:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  if (!dashboard || !dashboard.by_category.length) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-600 dark:text-slate-400">Sin datos de toggles</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
          Analytics de Toggles
        </h2>
        <p className="text-slate-600 dark:text-slate-400">
          Estado y uso de automaciones, agentes y features
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total de Toggles"
          value={dashboard.by_category.reduce((sum, c) => sum + c.total, 0)}
          color="blue"
        />
        <StatCard
          label="Habilitados"
          value={dashboard.by_category.reduce((sum, c) => sum + c.enabled, 0)}
          color="green"
        />
        <StatCard
          label="Deshabilitados"
          value={
            dashboard.by_category.reduce((sum, c) => sum + c.total - c.enabled, 0)
          }
          color="red"
        />
        <StatCard
          label="Uso Total (mes)"
          value={dashboard.by_category.reduce((sum, c) => sum + c.usage, 0)}
          color="purple"
        />
      </div>

      {/* Categories Table */}
      <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900">
              <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900 dark:text-white">
                Categoría
              </th>
              <th className="px-6 py-3 text-center text-sm font-semibold text-slate-900 dark:text-white">
                Total
              </th>
              <th className="px-6 py-3 text-center text-sm font-semibold text-slate-900 dark:text-white">
                Habilitados
              </th>
              <th className="px-6 py-3 text-center text-sm font-semibold text-slate-900 dark:text-white">
                % Activos
              </th>
              <th className="px-6 py-3 text-center text-sm font-semibold text-slate-900 dark:text-white">
                Uso (mes)
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {dashboard.by_category.map((cat) => {
              const activePercent = cat.total > 0 ? Math.round((cat.enabled / cat.total) * 100) : 0
              return (
                <tr key={cat.category} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                  <td className="px-6 py-4 text-sm font-medium text-slate-900 dark:text-white capitalize">
                    {cat.category}
                  </td>
                  <td className="px-6 py-4 text-center text-sm text-slate-600 dark:text-slate-400">
                    {cat.total}
                  </td>
                  <td className="px-6 py-4 text-center text-sm">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100">
                      {cat.enabled}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center text-sm text-slate-600 dark:text-slate-400">
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-32 h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500 transition-all"
                          style={{ width: `${activePercent}%` }}
                        />
                      </div>
                      <span className="font-mono text-xs">{activePercent}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-center text-sm text-slate-600 dark:text-slate-400">
                    <span className="font-mono font-semibold">{cat.usage}</span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Info Card */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <p className="text-sm text-blue-900 dark:text-blue-100">
          <strong>💡 Tip:</strong> Los toggles deshabilitados devolverán un error 403 cuando se
          intente usar. Revisa el Control Center para habilitar features según sea necesario.
        </p>
      </div>
    </div>
  )
}

interface StatCardProps {
  label: string
  value: number
  color: 'blue' | 'green' | 'red' | 'purple'
}

const StatCard = ({ label, value, color }: StatCardProps) => {
  const colorClasses = {
    blue: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-900 dark:text-blue-100',
    green:
      'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-900 dark:text-green-100',
    red: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-900 dark:text-red-100',
    purple:
      'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800 text-purple-900 dark:text-purple-100',
  }

  return (
    <div className={`border rounded-lg p-4 ${colorClasses[color]}`}>
      <p className="text-sm font-medium opacity-75">{label}</p>
      <p className="text-3xl font-bold">{value}</p>
    </div>
  )
}
