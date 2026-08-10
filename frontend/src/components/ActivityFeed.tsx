'use client'

import { useNotifications } from '@/hooks/useNotifications'
import { Clock, CheckCircle, AlertCircle, Loader } from 'lucide-react'
import { Card } from './ui/Card'

export default function ActivityFeed() {
  const { activities, isLoading } = useNotifications()

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-700'
      case 'in_progress':
        return 'bg-blue-100 text-blue-700'
      case 'pending':
        return 'bg-yellow-100 text-yellow-700'
      case 'failed':
        return 'bg-red-100 text-red-700'
      default:
        return 'bg-slate-100 text-slate-700'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'in_progress':
        return <Loader className="w-5 h-5 text-blue-600 animate-spin" />
      case 'pending':
        return <Clock className="w-5 h-5 text-yellow-600" />
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-600" />
      default:
        return <Clock className="w-5 h-5" />
    }
  }

  const formatTime = (date: Date) => {
    const now = new Date()
    const diff = now.getTime() - new Date(date).getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)

    if (minutes < 1) return 'Ahora'
    if (minutes < 60) return `hace ${minutes}m`
    return `hace ${hours}h`
  }

  const agentEmojis: Record<string, string> = {
    'Lead Scout': '🔍',
    'Closer Bot': '💼',
    'Coach Agent': '🎯',
    'Analytics Engine': '📊',
    'Strategy Bot': '💡',
    'Automation Bot': '⚙️',
  }

  return (
    <Card className="p-6 bg-gradient-to-br from-slate-50 to-blue-50/50">
      <div className="mb-6">
        <h2 className="text-lg font-bold text-brand-night flex items-center gap-2">
          <span>🤖</span>
          Tu equipo de agentes trabajando
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Aquí puedes ver en tiempo real qué están haciendo los agentes por tu negocio
        </p>
      </div>

      {isLoading && activities.length === 0 ? (
        <div className="text-center py-8">
          <Loader className="w-8 h-8 mx-auto text-blue-600 animate-spin mb-2" />
          <p className="text-slate-500 text-sm">Cargando actividad de agentes...</p>
        </div>
      ) : activities.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-slate-500 text-sm">Los agentes están en espera de nuevas tareas</p>
        </div>
      ) : (
        <div className="space-y-3">
          {activities.map((activity, idx) => (
            <div
              key={activity.id}
              className="bg-white rounded-lg p-4 border border-slate-200 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-start gap-4">
                {/* Agent Avatar */}
                <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-gradient-to-br from-brand-orange to-orange-500 flex items-center justify-center text-lg">
                  {agentEmojis[activity.agent] || '🤖'}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <h3 className="font-semibold text-sm text-brand-night">
                        {activity.agent}
                      </h3>
                      <p className="text-sm text-slate-600 mt-0.5">
                        {activity.action}
                      </p>
                    </div>

                    {/* Status */}
                    <div
                      className={`flex-shrink-0 px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(activity.status)}`}
                    >
                      {activity.status === 'completed' && 'Completado'}
                      {activity.status === 'in_progress' && 'En progreso'}
                      {activity.status === 'pending' && 'Pendiente'}
                      {activity.status === 'failed' && 'Falló'}
                    </div>
                  </div>

                  {activity.result && (
                    <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded text-xs text-green-700">
                      ✓ {activity.result}
                    </div>
                  )}

                  <p className="text-xs text-slate-400 mt-2">
                    {formatTime(activity.timestamp)}
                  </p>
                </div>

                {/* Status Icon */}
                <div className="flex-shrink-0">
                  {getStatusIcon(activity.status)}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Live Indicator */}
      <div className="mt-6 pt-4 border-t border-slate-200 flex items-center justify-center gap-2">
        <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
        <p className="text-xs text-slate-500">
          Actualizándose en tiempo real cada 30 segundos
        </p>
      </div>
    </Card>
  )
}
