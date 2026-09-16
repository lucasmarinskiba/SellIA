'use client'

import React, { useEffect, useState } from 'react'
import { Loader2, Brain, AlertCircle, CheckCircle2 } from 'lucide-react'
import { api } from '@/lib/api'

interface PredictiveScoresPanelProps {
  businessId: string
}

export function PredictiveScoresPanel({ businessId }: PredictiveScoresPanelProps): React.JSX.Element {
  const [accuracy, setAccuracy] = useState<any>(null)
  const [velocity, setVelocity] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadPredictiveData = async () => {
      try {
        const [accRes, velRes] = await Promise.all([
          api.get(`/businesses/${businessId}/seo-config/fomo-learning/prediction-accuracy`),
          api.get(`/businesses/${businessId}/seo-config/fomo-learning/velocity`),
        ])
        setAccuracy(accRes.data)
        setVelocity(velRes.data)
      } catch (error) {
        console.error('Error loading predictive data:', error)
      } finally {
        setLoading(false)
      }
    }

    void loadPredictiveData()
  }, [businessId])

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-3 py-12">
        <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
        <span className="text-slate-600">Calculando modelos…</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Prediction Accuracy */}
      <div className="rounded-lg border border-slate-200 bg-white p-6">
        <div className="flex items-center gap-3 mb-4">
          <Brain className="w-5 h-5 text-blue-600" />
          <h3 className="font-semibold text-slate-900">Prediction Accuracy</h3>
        </div>

        {accuracy && (
          <div className="space-y-4">
            {/* Score */}
            <div className="text-center py-4">
              <p className="text-5xl font-bold text-blue-600">
                {accuracy.prediction_accuracy.toFixed(0)}%
              </p>
              <p className="text-sm text-slate-600 mt-2">
                {accuracy.status === 'improving'
                  ? '📈 Mejorando'
                  : '📊 Estable'}
              </p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg bg-slate-50 p-3">
                <p className="text-xs text-slate-600">Total Conversiones</p>
                <p className="text-lg font-bold text-slate-900 mt-1">
                  {accuracy.total_conversions}
                </p>
              </div>
              <div className="rounded-lg bg-slate-50 p-3">
                <p className="text-xs text-slate-600">FOMO Copies Testeadas</p>
                <p className="text-lg font-bold text-slate-900 mt-1">
                  {accuracy.fomo_copies_tested}
                </p>
              </div>
            </div>

            {/* Recommendation */}
            <div
              className={`rounded-lg p-3 border ${
                accuracy.prediction_accuracy > 70
                  ? 'border-green-200 bg-green-50'
                  : 'border-orange-200 bg-orange-50'
              }`}
            >
              <p className="text-sm font-medium text-slate-900">
                {accuracy.recommendation}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Learning Velocity */}
      <div className="rounded-lg border border-slate-200 bg-white p-6">
        <div className="flex items-center gap-3 mb-4">
          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          <h3 className="font-semibold text-slate-900">Learning Velocity</h3>
        </div>

        {velocity && (
          <div className="space-y-4">
            {/* Trend */}
            <div className="grid grid-cols-3 gap-3">
              <div>
                <p className="text-xs text-slate-600">This Week</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">
                  {velocity.week_accuracy.toFixed(0)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-600">This Month</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">
                  {velocity.month_accuracy.toFixed(0)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-600">Velocity</p>
                <p
                  className={`text-2xl font-bold mt-1 ${
                    velocity.learning_velocity > 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {velocity.learning_velocity > 0 ? '+' : ''}
                  {velocity.learning_velocity.toFixed(1)}%
                </p>
              </div>
            </div>

            {/* Conversion Data */}
            <div className="rounded-lg bg-slate-50 p-3">
              <p className="text-sm text-slate-600">
                <span className="font-medium">{velocity.conversions_this_week}</span> conversiones esta semana vs{' '}
                <span className="font-medium">{velocity.conversions_this_month}</span> este mes
              </p>
            </div>

            {/* Status */}
            <div
              className={`rounded-lg p-3 border ${
                velocity.trend === 'positive'
                  ? 'border-green-200 bg-green-50'
                  : velocity.trend === 'stable'
                    ? 'border-blue-200 bg-blue-50'
                    : 'border-red-200 bg-red-50'
              }`}
            >
              <p className="text-sm font-medium text-slate-900">
                Trend:{' '}
                {velocity.trend === 'positive'
                  ? '📈 Positivo - Modelo mejorando'
                  : velocity.trend === 'stable'
                    ? '📊 Estable - Sin cambios significativos'
                    : '📉 Negativo - Revisar estrategia'}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
