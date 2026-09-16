'use client'

import React, { useEffect, useState } from 'react'
import { Loader2, TrendingUp, Zap, Target, Brain, Repeat2 } from 'lucide-react'
import { ConversionTicker } from './ConversionTicker'
import { FOMAPreviewComparison } from './FOMAPreviewComparison'
import { UrgencyMetricsChart } from './UrgencyMetricsChart'
import { ABTestStatus } from './ABTestStatus'
import { DecayDetectionPanel } from './DecayDetectionPanel'
import { PredictiveScoresPanel } from './PredictiveScoresPanel'
import { AutoRotationPanel } from './AutoRotationPanel'
import { fomaPhase1Api } from '@/lib/fomoPhase1'

interface FOMADashboardProps {
  businessId: string
  linkId?: string
}

type TabType = 'overview' | 'ticker' | 'ab-tests' | 'decay' | 'predictions' | 'rotation'

export function FOMADashboard({ businessId, linkId }: FOMADashboardProps): React.JSX.Element {
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(false)
  }, [businessId])

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-3 py-20">
        <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
        <span className="text-slate-600">Cargando dashboard FOMO…</span>
      </div>
    )
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Zap },
    { id: 'ticker', label: 'Ticker', icon: TrendingUp },
    { id: 'ab-tests', label: 'A/B Tests', icon: Target },
    { id: 'decay', label: 'Decay', icon: Repeat2 },
    { id: 'predictions', label: 'Predictive', icon: Brain },
    { id: 'rotation', label: 'Auto-Rotation', icon: Repeat2 },
  ] as const

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-xl border border-slate-200 bg-white p-6">
        <div className="flex items-center gap-3 mb-2">
          <Zap className="w-6 h-6 text-blue-600" />
          <h1 className="text-2xl font-bold text-slate-900">FOMO Inteligente</h1>
        </div>
        <p className="text-sm text-slate-600">
          Sistema cerrado de learning: cada conversión refina el siguiente FOMO
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-slate-200 overflow-x-auto">
        {tabs.map(tab => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabType)}
              className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors whitespace-nowrap flex items-center gap-2 ${
                isActive
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Content */}
      <div>
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <p className="text-xs text-slate-600 font-medium uppercase">Conversiones Hoy</p>
                <p className="text-2xl font-bold text-slate-900 mt-2">—</p>
                <p className="text-xs text-slate-500 mt-1">Sincronizando…</p>
              </div>
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <p className="text-xs text-slate-600 font-medium uppercase">CTR Promedio</p>
                <p className="text-2xl font-bold text-slate-900 mt-2">—</p>
                <p className="text-xs text-slate-500 mt-1">Datos en vivo</p>
              </div>
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <p className="text-xs text-slate-600 font-medium uppercase">Accuracy</p>
                <p className="text-2xl font-bold text-slate-900 mt-2">—</p>
                <p className="text-xs text-slate-500 mt-1">Modelo predictivo</p>
              </div>
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <p className="text-xs text-slate-600 font-medium uppercase">Learning Velocity</p>
                <p className="text-2xl font-bold text-slate-900 mt-2">—</p>
                <p className="text-xs text-slate-500 mt-1">7d vs 30d</p>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="rounded-lg border border-slate-200 bg-white p-6">
              <h2 className="font-semibold text-slate-900 mb-4">Próximos Pasos</h2>
              <div className="space-y-2">
                <button className="w-full px-4 py-2 rounded-lg border border-blue-600 text-blue-600 text-sm font-medium hover:bg-blue-50">
                  Generar FOMO Copy Nueva
                </button>
                <button className="w-full px-4 py-2 rounded-lg border border-slate-200 text-slate-600 text-sm font-medium hover:bg-slate-50">
                  Crear A/B Test
                </button>
                <button className="w-full px-4 py-2 rounded-lg border border-slate-200 text-slate-600 text-sm font-medium hover:bg-slate-50">
                  Ver Recomendaciones Cross-Platform
                </button>
              </div>
            </div>

            {/* Urgency Metrics */}
            <div className="rounded-lg border border-slate-200 bg-white p-6">
              <UrgencyMetricsChart businessId={businessId} />
            </div>
          </div>
        )}

        {/* Ticker Tab */}
        {activeTab === 'ticker' && (
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <ConversionTicker businessId={businessId} refreshInterval={5000} />
          </div>
        )}

        {/* A/B Tests Tab */}
        {activeTab === 'ab-tests' && (
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <ABTestStatus businessId={businessId} />
          </div>
        )}

        {/* Decay Tab */}
        {activeTab === 'decay' && (
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <DecayDetectionPanel businessId={businessId} />
          </div>
        )}

        {/* Predictions Tab */}
        {activeTab === 'predictions' && (
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <PredictiveScoresPanel businessId={businessId} />
          </div>
        )}

        {/* Auto-Rotation Tab */}
        {activeTab === 'rotation' && (
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <AutoRotationPanel businessId={businessId} />
          </div>
        )}
      </div>
    </div>
  )
}
