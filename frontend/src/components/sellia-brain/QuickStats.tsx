'use client'

import { AutomationToggleResponse } from '@/lib/api/toggles'

interface QuickStatsProps {
  toggles: AutomationToggleResponse[]
}

export const QuickStats = ({ toggles }: QuickStatsProps) => {
  const totalToggles = toggles.length
  const enabledCount = toggles.filter((t) => t.is_enabled).length
  const disabledCount = totalToggles - enabledCount
  const avgUsage = toggles.filter((t) => t.monthly_limit).length > 0
    ? Math.round(
        toggles
          .filter((t) => t.monthly_limit)
          .reduce((sum, t) => sum + ((t.current_month_usage / t.monthly_limit!) * 100), 0) /
          toggles.filter((t) => t.monthly_limit).length
      )
    : 0

  const statCards = [
    {
      label: 'Total Activos',
      value: enabledCount,
      color: 'bg-green-50 dark:bg-green-900/20 text-green-900 dark:text-green-100',
      icon: '✅',
    },
    {
      label: 'Deshabilitados',
      value: disabledCount,
      color: 'bg-red-50 dark:bg-red-900/20 text-red-900 dark:text-red-100',
      icon: '🚫',
    },
    {
      label: 'Uso Promedio',
      value: `${avgUsage}%`,
      color: 'bg-blue-50 dark:bg-blue-900/20 text-blue-900 dark:text-blue-100',
      icon: '📊',
    },
    {
      label: 'Total Features',
      value: totalToggles,
      color: 'bg-purple-50 dark:bg-purple-900/20 text-purple-900 dark:text-purple-100',
      icon: '⚙️',
    },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      {statCards.map((stat) => (
        <div key={stat.label} className={`${stat.color} rounded-lg p-4 border border-current border-opacity-20`}>
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium opacity-75">{stat.label}</p>
            <span className="text-xl">{stat.icon}</span>
          </div>
          <p className="text-2xl font-bold">{stat.value}</p>
        </div>
      ))}
    </div>
  )
}
