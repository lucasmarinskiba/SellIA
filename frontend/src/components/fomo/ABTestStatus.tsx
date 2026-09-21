'use client'

import React, { useEffect, useState } from 'react'
import { Loader2, CheckCircle2, Clock, BarChart3 } from 'lucide-react'
import { api } from '@/lib/api'

interface ABTestStatusProps {
  businessId: string
}

interface ABVariant {
  id: string
  split: number
  conversions: number
  revenue: number
}

interface ABTest {
  test_id: string
  status: string
  min_conversions: number
  total_conversions: number
  variant_a: ABVariant
  variant_b: ABVariant
  variant_c: ABVariant | null
  winner_id: string | null
  winner_announced_at: string | null
}

export function ABTestStatus({ businessId }: ABTestStatusProps): React.JSX.Element {
  const [tests, setTests] = useState<ABTest[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadTests = async () => {
      try {
        const res = await api.get<ABTest[]>(
          `/businesses/${businessId}/seo-config/fomo-ab-tests/running`
        )
        setTests(res.data || [])
      } catch (error) {
        console.error('Error loading A/B tests:', error)
      } finally {
        setLoading(false)
      }
    }

    void loadTests()
    const interval = setInterval(() => void loadTests(), 10000)
    return () => clearInterval(interval)
  }, [businessId])

  if (loading && tests.length === 0) {
    return (
      <div className="flex items-center justify-center gap-3 py-12">
        <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
        <span className="text-slate-600">Cargando A/B tests…</span>
      </div>
    )
  }

  if (tests.length === 0) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="w-12 h-12 text-slate-300 mx-auto mb-3" />
        <p className="text-slate-600">No hay A/B tests corriendo</p>
        <p className="text-sm text-slate-500 mt-1">Crea uno para optimizar FOMO copy</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 className="w-5 h-5 text-blue-600" />
        <h3 className="font-semibold text-slate-900">{tests.length} Test(s) Activo(s)</h3>
      </div>

      {tests.map((test, idx) => {
        const progress = (test.total_conversions / test.min_conversions) * 100
        const variantA = test.variant_a
        const variantB = test.variant_b
        const variantC = test.variant_c

        return (
          <div key={idx} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            {/* Status Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-orange-600" />
                <span className="font-medium text-slate-900">Test {idx + 1}</span>
              </div>
              <div className="text-sm text-slate-600">
                {test.total_conversions} / {test.min_conversions} conversiones
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-slate-200 rounded-full h-2 mb-4 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-500"
                style={{ width: `${Math.min(100, progress)}%` }}
              />
            </div>

            {/* Variants */}
            <div className="space-y-2">
              {[variantA, variantB, variantC].map((variant, vIdx) => {
                if (!variant || !variant.id) return null
                const isWinner = test.winner_id === variant.id
                const ctr = variant.conversions > 0 ? ((variant.conversions / (variant.conversions + 100)) * 100).toFixed(1) : '0'

                return (
                  <div
                    key={vIdx}
                    className={`rounded-lg p-3 border ${
                      isWinner
                        ? 'border-green-300 bg-green-50'
                        : 'border-slate-200 bg-white'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {isWinner && <CheckCircle2 className="w-4 h-4 text-green-600" />}
                        <span className="text-sm font-medium text-slate-900">
                          Variante {String.fromCharCode(65 + vIdx)}
                        </span>
                        <span className="text-xs text-slate-500">
                          ({(variant.split * 100).toFixed(0)}% traffic)
                        </span>
                      </div>
                      <div className="text-sm font-semibold text-slate-900">
                        {variant.conversions} conversiones
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Action */}
            {test.winner_id && (
              <button className="mt-3 w-full px-3 py-2 rounded-lg bg-green-100 text-green-700 text-sm font-medium hover:bg-green-200">
                Aplicar Ganador
              </button>
            )}
          </div>
        )
      })}
    </div>
  )
}
