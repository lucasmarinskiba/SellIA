'use client'

import React, { useEffect, useState } from 'react'
import { Loader2, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react'
import { api } from '@/lib/api'

interface AutoRotationPanelProps {
  businessId: string
}

interface RotationEvent {
  link_id: string
  link_title: string
  baseline_ctr: number
  current_ctr: number
  decay: number
  new_test_id: string
  rotated_at: string
}

export function AutoRotationPanel({ businessId }: AutoRotationPanelProps): React.JSX.Element {
  const [history, setHistory] = useState<RotationEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState(false)

  const loadHistory = async () => {
    try {
      const res = await api.get(
        `/businesses/${businessId}/seo-config/fomo-auto-rotation/history?days=7`
      )
      setHistory(res.data || [])
    } catch (error) {
      console.error('Error loading rotation history:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadHistory()
    const interval = setInterval(() => void loadHistory(), 3600000) // 1h
    return () => clearInterval(interval)
  }, [businessId])

  const handleTrigger = async () => {
    setTriggering(true)
    try {
      const res = await api.post(
        `/businesses/${businessId}/seo-config/fomo-auto-rotation/trigger`,
        {}
      )
      if (res.data?.rotated > 0) {
        await loadHistory()
      }
    } catch (error) {
      console.error('Error triggering rotation:', error)
    } finally {
      setTriggering(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-3 py-12">
        <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
        <span className="text-slate-600">Cargando historial de rotaciones…</span>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-slate-900 flex items-center gap-2">
          <RefreshCw className="w-5 h-5 text-blue-600" />
          Auto-Rotation Inteligente
        </h3>
        <button
          onClick={handleTrigger}
          disabled={triggering}
          className="px-3 py-2 rounded-lg bg-blue-100 text-blue-700 text-sm font-medium hover:bg-blue-200 disabled:opacity-50 flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${triggering ? 'animate-spin' : ''}`} />
          {triggering ? 'Rotando…' : 'Rotar Ahora'}
        </button>
      </div>

      {history.length === 0 ? (
        <div className="text-center py-8">
          <AlertCircle className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-600">Sin rotaciones automáticas en los últimos 7 días</p>
          <p className="text-sm text-slate-500 mt-1">
            El sistema rotará automáticamente cuando detecte decay mayor al 30% en tu FOMO copy
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {history.map((event, idx) => (
            <div key={idx} className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="font-medium text-slate-900">{event.link_title}</p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {new Date(event.rotated_at).toLocaleString('es-AR')}
                  </p>
                </div>
                <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0" />
              </div>

              <div className="grid grid-cols-3 gap-2 mt-3">
                <div>
                  <p className="text-xs text-slate-600">Baseline</p>
                  <p className="font-bold text-slate-900">{event.baseline_ctr.toFixed(1)}%</p>
                </div>
                <div>
                  <p className="text-xs text-slate-600">Actual</p>
                  <p className="font-bold text-red-600">{event.current_ctr.toFixed(1)}%</p>
                </div>
                <div>
                  <p className="text-xs text-slate-600">Decay</p>
                  <p className="font-bold text-red-600">-{event.decay.toFixed(1)}%</p>
                </div>
              </div>

              <p className="text-xs text-slate-500 mt-2">
                Nuevo A/B test iniciado para recuperar CTR
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
