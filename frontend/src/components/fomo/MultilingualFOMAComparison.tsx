'use client'

import React, { useEffect, useState } from 'react'
import { Loader2, Globe, Copy, Check } from 'lucide-react'
import { api } from '@/lib/api'

interface MultilingualFOMAComparisonProps {
  businessId: string
  linkId: string
  platform: string
}

interface LanguageCopy {
  copy: string
  urgency_trigger: string
  language_name: string
}

const LANGUAGES = ['es', 'en', 'pt'] as const

interface ComparisonData {
  es?: LanguageCopy
  en?: LanguageCopy
  pt?: LanguageCopy
}

export function MultilingualFOMAComparison({
  businessId,
  linkId,
  platform,
}: MultilingualFOMAComparisonProps): React.JSX.Element {
  const [comparison, setComparison] = useState<ComparisonData | null>(null)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState<string | null>(null)
  const [selectedLang, setSelectedLang] = useState<'es' | 'en' | 'pt'>('es')

  useEffect(() => {
    const loadComparison = async () => {
      try {
        const res = await api.get(
          `/businesses/${businessId}/seo-config/fomo-multilingual/comparison?link_id=${linkId}&platform=${platform}`
        )
        setComparison(res.data?.languages || {})
      } catch (error) {
        console.error('Error loading comparison:', error)
      } finally {
        setLoading(false)
      }
    }

    void loadComparison()
  }, [businessId, linkId, platform])

  const copyToClipboard = async (text: string, lang: string) => {
    await navigator.clipboard.writeText(text)
    setCopied(lang)
    setTimeout(() => setCopied(null), 2000)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-3 py-12">
        <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
        <span className="text-slate-600">Generating multilingual FOMO…</span>
      </div>
    )
  }

  if (!comparison || Object.keys(comparison).length === 0) {
    return (
      <div className="text-center py-8">
        <Globe className="w-12 h-12 text-slate-300 mx-auto mb-3" />
        <p className="text-slate-600">No multilingual FOMO generated yet</p>
      </div>
    )
  }

  const current = comparison[selectedLang]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-slate-900 flex items-center gap-2">
          <Globe className="w-5 h-5 text-blue-600" />
          FOMO Multilingüe
        </h3>
      </div>

      {/* Language Tabs */}
      <div className="flex gap-2 border-b border-slate-200 overflow-x-auto">
        {LANGUAGES.map(lang => (
          <button
            key={lang}
            onClick={() => setSelectedLang(lang)}
            className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
              selectedLang === lang
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            {comparison[lang]?.language_name || lang.toUpperCase()}
          </button>
        ))}
      </div>

      {/* Content */}
      {current && (
        <div className="rounded-lg border border-slate-200 bg-white p-6 space-y-4">
          {/* Urgency Trigger */}
          <div>
            <p className="text-xs text-slate-600 font-medium uppercase mb-1">Urgency Trigger</p>
            <p className="text-sm font-medium text-slate-900">
              {current.urgency_trigger}
            </p>
          </div>

          {/* FOMO Copy */}
          <div>
            <p className="text-xs text-slate-600 font-medium uppercase mb-2">FOMO Copy</p>
            <p className="text-sm text-slate-800 whitespace-pre-wrap leading-relaxed">
              {current.copy}
            </p>
          </div>

          {/* Copy Button */}
          <button
            onClick={() => copyToClipboard(current.copy, selectedLang)}
            className="w-full px-3 py-2 rounded-lg border border-blue-200 text-blue-700 text-sm font-medium hover:bg-blue-50 flex items-center justify-center gap-2"
          >
            {copied === selectedLang ? (
              <>
                <Check className="w-4 h-4" />
                Copiado
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                Copiar
              </>
            )}
          </button>
        </div>
      )}

      {/* All Languages Grid */}
      <div className="mt-8 pt-8 border-t border-slate-200">
        <p className="text-xs text-slate-600 font-medium uppercase mb-4">Vista General</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {LANGUAGES.map(lang => {
            const entry = comparison[lang]
            if (!entry) return null
            return (
              <div key={lang} className="rounded-lg border border-slate-100 bg-slate-50 p-3">
                <p className="font-medium text-slate-900 mb-2">{entry.language_name}</p>
                <p className="text-xs text-slate-600 line-clamp-3">{entry.copy}</p>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
