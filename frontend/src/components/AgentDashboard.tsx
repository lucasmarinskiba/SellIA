'use client'

import { useState } from 'react'
import { useNotifications } from '@/hooks/useNotifications'
import ActivityFeed from './ActivityFeed'
import { TrendingUp, Users, Zap, Target, Brain } from 'lucide-react'
import Card from './ui/Card'
import Button from './ui/Button'
import Link from 'next/link'

export default function AgentDashboard() {
  const { notifications } = useNotifications()
  const [activeTab, setActiveTab] = useState<'overview' | 'coaching' | 'strategies' | 'actions'>('overview')

  // Filter notifications by type
  const agentAlerts = notifications.filter((n) => n.type === 'agent_alert')
  const celebrations = notifications.filter((n) => n.type === 'sale_celebration')
  const strategies = notifications.filter((n) => n.type === 'strategy')
  const actionsRequired = notifications.filter((n) => n.type === 'action_required')
  const milestones = notifications.filter((n) => n.type === 'milestone')
  const emergencySupport = notifications.filter((n) => n.type === 'emergency_support')

  const stats = [
    {
      label: 'Alertas de agentes',
      value: agentAlerts.length,
      icon: Zap,
      color: 'text-blue-600 bg-blue-50',
      trend: 'Monitoreando en tiempo real',
    },
    {
      label: 'Celebraciones',
      value: celebrations.length,
      icon: TrendingUp,
      color: 'text-green-600 bg-green-50',
      trend: 'Últimas ventas',
    },
    {
      label: 'Estrategias',
      value: strategies.length,
      icon: Brain,
      color: 'text-purple-600 bg-purple-50',
      trend: 'Recomendaciones',
    },
    {
      label: 'Aprobaciones pendientes',
      value: actionsRequired.length,
      icon: Target,
      color: 'text-orange-600 bg-orange-50',
      trend: 'Requieren tu decisión',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-brand-night">Centro de Control de Agentes</h1>
        <p className="text-slate-500 mt-2">
          Tu equipo de IA trabajando 24/7 para hacer crecer tu negocio
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.label} className="p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-600">{stat.label}</p>
                  <p className="text-3xl font-bold text-brand-night mt-2">{stat.value}</p>
                  <p className="text-xs text-slate-500 mt-2">{stat.trend}</p>
                </div>
                <div className={`p-3 rounded-lg ${stat.color}`}>
                  <Icon className="w-6 h-6" />
                </div>
              </div>
            </Card>
          )
        })}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-200">
        {[
          { id: 'overview', label: '📊 Resumen', icon: '📊' },
          { id: 'coaching', label: '🎯 Coaching', icon: '🎯' },
          { id: 'strategies', label: '💡 Estrategias', icon: '💡' },
          { id: 'actions', label: '⚠️ Aprobaciones', icon: '⚠️' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-brand-orange text-brand-orange'
                : 'border-transparent text-slate-600 hover:text-brand-night'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <ActivityFeed />
        </div>
      )}

      {activeTab === 'coaching' && (
        <div className="space-y-4">
          {agentAlerts.length === 0 ? (
            <Card className="p-8 text-center">
              <p className="text-slate-500">No hay mensajes de coaching disponibles</p>
            </Card>
          ) : (
            agentAlerts.map((alert) => (
              <Card key={alert.id} className="p-6 border-l-4 border-l-blue-500">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <h3 className="font-bold text-lg text-brand-night flex items-center gap-2">
                      {alert.icon} {alert.title}
                    </h3>
                    <p className="text-slate-600 mt-2">{alert.message}</p>
                    {alert.metadata?.actionItem && (
                      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                        <p className="text-sm font-semibold text-blue-900">
                          Acción recomendada: {alert.metadata.actionItem}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      )}

      {activeTab === 'strategies' && (
        <div className="space-y-4">
          {strategies.length === 0 ? (
            <Card className="p-8 text-center">
              <p className="text-slate-500">No hay estrategias recomendadas en este momento</p>
            </Card>
          ) : (
            strategies.map((strategy) => (
              <Card key={strategy.id} className="p-6 border-l-4 border-l-purple-500">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <h3 className="font-bold text-lg text-brand-night flex items-center gap-2">
                      {strategy.icon} {strategy.title}
                    </h3>
                    <p className="text-slate-600 mt-2">{strategy.message}</p>
                    <div className="mt-4 flex gap-2">
                      {strategy.actionUrl && (
                        <Link href={strategy.actionUrl}>
                          <Button size="sm" variant="secondary">
                            Ver detalles
                          </Button>
                        </Link>
                      )}
                      <Button size="sm" variant="ghost">
                        Guardar para después
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            ))
          )}

          {celebrations.length > 0 && (
            <>
              <div className="pt-4">
                <h3 className="font-bold text-lg text-brand-night mb-4">Últimas Celebraciones 🎉</h3>
                <div className="space-y-3">
                  {celebrations.map((celebration) => (
                    <Card key={celebration.id} className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 border-l-4 border-l-green-500">
                      <div className="flex items-center gap-3">
                        <span className="text-3xl">{celebration.icon}</span>
                        <div>
                          <p className="font-bold text-green-900">{celebration.title}</p>
                          <p className="text-sm text-green-700">{celebration.message}</p>
                          {celebration.platform && (
                            <p className="text-xs text-green-600 mt-1">Plataforma: {celebration.platform}</p>
                          )}
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {activeTab === 'actions' && (
        <div className="space-y-4">
          {actionsRequired.length === 0 ? (
            <Card className="p-8 text-center">
              <p className="text-slate-500">No hay acciones pendientes</p>
              <p className="text-xs text-slate-400 mt-2">Los agentes están funcionando sin problemas</p>
            </Card>
          ) : (
            actionsRequired.map((action) => (
              <Card key={action.id} className="p-6 border-l-4 border-l-orange-500 bg-orange-50/50">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <h3 className="font-bold text-lg text-brand-night flex items-center gap-2">
                      {action.icon} {action.title}
                    </h3>
                    <p className="text-slate-700 mt-2">{action.message}</p>
                    {action.metadata && (
                      <div className="mt-3 text-sm text-slate-600 space-y-1">
                        {Object.entries(action.metadata).map(([key, value]) => (
                          <p key={key}>
                            <span className="font-semibold">{key}:</span> {String(value)}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
                <div className="mt-4 flex gap-2">
                  <Button size="sm" className="bg-green-600 hover:bg-green-700">
                    Aprobar
                  </Button>
                  <Button size="sm" variant="ghost">
                    Rechazar
                  </Button>
                </div>
              </Card>
            ))
          )}

          {emergencySupport.length > 0 && (
            <>
              <div className="pt-4">
                <h3 className="font-bold text-lg text-brand-night mb-4 text-red-600">Soporte de Emergencia 🚨</h3>
                <div className="space-y-3">
                  {emergencySupport.map((emergency) => (
                    <Card key={emergency.id} className="p-4 bg-red-50 border-l-4 border-l-red-500">
                      <p className="font-bold text-red-900">{emergency.title}</p>
                      <p className="text-red-700 mt-1">{emergency.message}</p>
                    </Card>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
