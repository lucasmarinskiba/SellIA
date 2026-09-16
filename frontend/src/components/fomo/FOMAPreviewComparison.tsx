'use client'

import React, { useEffect, useState } from 'react'
import { AlertCircle, Loader2, Copy, Check } from 'lucide-react'
import { fomaPhase1Api, type FOMAPreview } from '@/lib/fomoPhase1'

interface FOMAPreviewComparisonProps {
  businessId: string
  linkId: string
}

export function FOMAPreviewComparison({
  businessId,
  linkId,
}: FOMAPreviewComparisonProps): React.JSX.Element {
  const [preview, setPreview] = useState<FOMAPreview | null>(null)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState<string | null>(null)

  useEffect(() => {
    const loadPreview = async () => {
      try {
        const data = await fomaPhase1Api.getFOMAPreview(businessId, linkId)
        setPreview(data)
      } catch (error) {
        console.error('Error loading preview:', error)
      } finally {
        setLoading(false)
      }
    }

    void loadPreview()
  }, [businessId, linkId])

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopied(id)
    setTimeout(() => setCopied(null), 2000)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-3 py-12">
        <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
        <span className="text-slate-600">Cargando preview…</span>
      </div>
    )
  }

  if (!preview) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 flex gap-3">
        <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
        <div>
          <p className="font-medium text-red-900">No se encontró preview</p>
          <p className="text-sm text-red-700 mt-1">Genera primero el FOMO copy</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Link Info */}
      <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
        <a
          href={preview.link.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-blue-600 hover:text-blue-700 truncate block"
        >
          {preview.link.url}
        </a>
        <p className="text-xs text-slate-500 mt-2">
          {preview.link.platform === 'mercado-libre' ? 'Mercado Libre' : preview.link.platform}
        </p>
      </div>

      {/* Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Original */}
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="mb-3">
            <p className="text-xs font-semibold text-slate-600 uppercase tracking-wide">
              Original (Sin FOMO)
            </p>
          </div>
          <div className="space-y-3">
            <div>
              <p className="text-sm font-medium text-slate-900">{preview.original.title}</p>
            </div>
            <div className="text-sm text-slate-600 bg-slate-50 p-3 rounded">
              {preview.original.description}
            </div>
            <button
              type="button"
              onClick={() => handleCopy(preview.original.title, 'original')}
              className="text-xs text-slate-600 hover:text-slate-900 flex items-center gap-1"
            >
              {copied === 'original' ? (
                <>
                  <Check className="w-3 h-3 text-green-600" /> Copiado
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" /> Copiar
                </>
              )}
            </button>
          </div>
        </div>

        {/* With FOMO */}
        <div className="rounded-lg border border-green-300 bg-gradient-to-br from-green-50 to-green-50/50 p-4">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-xs font-semibold text-green-700 uppercase tracking-wide">
              Con FOMO (+{Math.round(preview.with_fomo.fomo_score)}%)
            </p>
            <span className="text-xs px-2 py-1 rounded-full bg-green-100 text-green-700 font-medium">
              Optimizado
            </span>
          </div>
          <div className="space-y-3">
            <div>
              <p className="text-sm font-medium text-slate-900">{preview.with_fomo.title}</p>
            </div>

            {/* FOMO Elements */}
            {preview.with_fomo.urgency_trigger && (
              <div className="text-xs p-2 rounded bg-orange-100 text-orange-800">
                <span className="font-medium">Urgencia:</span> {preview.with_fomo.urgency_trigger}
              </div>
            )}

            {preview.with_fomo.scarcity_message && (
              <div className="text-xs p-2 rounded bg-red-100 text-red-800">
                <span className="font-medium">Escasez:</span> {preview.with_fomo.scarcity_message}
              </div>
            )}

            <div className="text-sm font-medium text-green-700">
              CTA: {preview.with_fomo.call_to_action}
            </div>

            <div className="text-sm text-slate-700 bg-white p-3 rounded border border-green-200">
              <p className="font-medium mb-2 text-slate-900">Copy Completo:</p>
              <p>{preview.with_fomo.full_copy}</p>
            </div>

            <button
              type="button"
              onClick={() => handleCopy(preview.with_fomo.full_copy, 'fomo')}
              className="text-xs text-green-700 hover:text-green-900 font-medium flex items-center gap-1"
            >
              {copied === 'fomo' ? (
                <>
                  <Check className="w-3 h-3 text-green-600" /> Copiado
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" /> Copiar para testear
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
