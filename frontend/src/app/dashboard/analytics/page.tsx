'use client'

import { TrendingUp, Users, Clock, Zap } from 'lucide-react'

export default function AnalyticsPage() {
  const metrics = [
    { label: 'Ingresos (30d)', value: '$47,300', trend: '+12%', icon: TrendingUp },
    { label: 'Clientes únicos', value: '234', trend: '+8%', icon: Users },
    { label: 'Tiempo promedio', value: '2.3h', trend: '-5%', icon: Clock },
    { label: 'Performance', value: '94%', trend: '+3%', icon: Zap },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-black text-slate-900">Analytics</h1>
        <p className="text-slate-600 mt-2">Métricas detalladas de tu negocio</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric) => {
          const Icon = metric.icon
          return (
            <div key={metric.label} className="bg-white rounded-lg border border-slate-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <Icon className="text-blue-500" size={24} />
                <span className="text-sm font-medium text-green-600">{metric.trend}</span>
              </div>
              <p className="text-slate-600 text-sm mb-1">{metric.label}</p>
              <p className="text-2xl font-black text-slate-900">{metric.value}</p>
            </div>
          )
        })}
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <h2 className="text-lg font-bold text-slate-900 mb-4">Tendencias (últimos 30 días)</h2>
        <div className="h-64 bg-slate-50 rounded-lg flex items-center justify-center text-slate-400">
          Gráfico de línea simulado
        </div>
      </div>
    </div>
  )
}
