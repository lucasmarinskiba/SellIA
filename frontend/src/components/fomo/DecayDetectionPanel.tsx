'use client'

import React, { useEffect, useState } from 'react'
import { Loader2, AlertTriangle, TrendingDown, Zap } from 'lucide-react'
import { api } from '@/lib/api'

interface DecayDetectionPanelProps {
  businessId: string
}

export function DecayDetectionPanel({ businessId }: DecayDetectionPanelProps): React.JSX.Element {
  const [decayed, setDecayed] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadDecay = async () => {
      try {
        const res = await api.get(
          `/businesses/${businessId}/seo-config/fomo-decay/detect?decay_threshold=30`
        )
        setDecayed(res.data || [])
      } catch (error) {
        console.error('Error loading decay data:', error)
      } finally {
        setLoading(false)
      }
    }

    void loadDecay()
    const interval = setInterval(() => void loadDecay(), 3600000) // 1h
    return () => clearInterval(interval)
  }, [businessId])

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-3 py-12">
        <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
        <span className="text-slate-600">Analizando decay…</span>
      </div>
    )
  }

  if (decayed.length === 0) {
    return (
      <div className="text-center py-12">
        <TrendingDown className="w-12 h-12 text-green-300 mx-auto mb-3" />
        <p className="text-slate-600">Sin decay detectado</p>
        <p className="text-sm text-slate-500 mt-1">Tu FOMO copy sigue fuerte</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-5 h-5 text-red-600" />
        <h3 className="font-semibold text-slate-900">{decayed.length} Link(s) con Decay</h3>
      </div>

      {decayed.map((item, idx) => (
        <div key={idx} className="rounded-lg border border-red-200 bg-red-50 p-4">
          {/* Link Info */}
          <div className="mb-3">
            <p className="font-medium text-slate-900 truncate">{item.link.title}</p>
            <a
              href={item.link.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-600 hover:text-blue-700 truncate block"
            >
              {item.link.url}
            </a>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-3 gap-2 mb-3">
            <div>
              <p className="text-xs text-slate-600">Baseline CTR</p>
              <p className="font-bold text-slate-900">{item.baseline_ctr.toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-xs text-slate-600">Current CTR</p>
              <p className="font-bold text-red-600">{item.current_ctr.toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-xs text-slate-600">Decay</p>
              <p className="font-bold text-red-600">-{item.decay_percentage.toFixed(1)}%</p>
            </div>
          </div>

          {/* Action */}
          <button className="w-full px-3 py-2 rounded-lg bg-blue-100 text-blue-700 text-sm font-medium hover:bg-blue-200 flex items-center justify-center gap-2">
            <Zap className="w-4 h-4" />
            Regenerar FOMO Copy
          </button>
        </div>
      ))}
    </div>
  )
}
