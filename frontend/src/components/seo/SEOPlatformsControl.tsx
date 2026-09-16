'use client'

import React, { useEffect, useState } from 'react'
import { AlertCircle, Loader2, Power, Zap } from 'lucide-react'
import { seoConfigApi, type PlatformSEOStatus } from '@/lib/seoConfig'

interface SEOPlatformsControlProps {
  businessId: string
  onChanged?: () => void
}

export function SEOPlatformsControl({ businessId, onChanged }: SEOPlatformsControlProps): React.JSX.Element {
  const [platforms, setPlatforms] = useState<PlatformSEOStatus[]>([])
  const [globalEnabled, setGlobalEnabled] = useState(true)
  const [loading, setLoading] = useState(true)
  const [toggling, setToggling] = useState<string | null>(null)

  const loadPlatforms = async () => {
    try {
      const data = await seoConfigApi.getPlatformsSEOStatus(businessId)
      setPlatforms(data.platforms)
      setGlobalEnabled(data.global_seo_enabled)
    } catch (error) {
      console.error('Error loading platforms:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadPlatforms()
  }, [businessId])

  const handleGlobalToggle = async () => {
    try {
      setToggling('global')
      await seoConfigApi.toggleGlobalSEO(businessId, !globalEnabled)
      setGlobalEnabled(!globalEnabled)
      onChanged?.()
    } catch (error) {
      console.error('Error toggling global SEO:', error)
    } finally {
      setToggling(null)
    }
  }

  const handlePlatformToggle = async (connectionId: string) => {
    try {
      setToggling(connectionId)
      const platform = platforms.find(p => p.connection_id === connectionId)
      if (!platform) return
      await seoConfigApi.togglePlatformSEO(businessId, connectionId, !platform.seo_enabled)
      setPlatforms(platforms.map(p =>
        p.connection_id === connectionId
          ? { ...p, seo_enabled: !p.seo_enabled }
          : p,
      ))
      onChanged?.()
    } catch (error) {
      console.error('Error toggling platform SEO:', error)
    } finally {
      setToggling(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-3 text-slate-500 py-10 justify-center">
        <Loader2 className="w-5 h-5 animate-spin" /> Cargando plataformas anexadas…
      </div>
    )
  }

  if (platforms.length === 0) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6 text-center">
        <AlertCircle className="w-12 h-12 mx-auto text-slate-300 mb-4" />
        <p className="text-sm text-slate-600">No tenés plataformas anexadas todavía.</p>
        <p className="text-xs text-slate-500 mt-1">
          Conecta plataformas como Mercado Libre, Amazon o Shopify para posicionar automáticamente tus productos.
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white">
      {/* Global Toggle */}
      <div className="p-5 border-b border-slate-100">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Zap className="w-5 h-5 text-blue-600" />
            <div>
              <p className="font-semibold text-slate-900">Posicionamiento SEO Automático</p>
              <p className="text-xs text-slate-500 mt-0.5">
                Activá para que la IA posicione automáticamente en todas tus plataformas
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleGlobalToggle}
            disabled={toggling === 'global'}
            className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors ${
              globalEnabled ? 'bg-blue-600' : 'bg-slate-200'
            } ${toggling === 'global' ? 'opacity-50' : ''}`}
          >
            {toggling === 'global' && (
              <Loader2 className="absolute left-1 w-4 h-4 animate-spin text-white" />
            )}
            <span
              className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${
                globalEnabled ? 'translate-x-7' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Platform List */}
      <div className="divide-y divide-slate-100">
        {platforms.map(platform => (
          <div key={platform.connection_id} className="p-4 flex items-center justify-between gap-4">
            <div>
              <p className="font-medium text-slate-900 capitalize">{platform.platform_name}</p>
              <p className="text-xs text-slate-500 mt-0.5">
                {platform.status === 'active' ? '✓ Conectada' : `⚠️ ${platform.status}`}
                {platform.last_sync && ` • Sincronizado ${new Date(platform.last_sync).toLocaleDateString()}`}
              </p>
            </div>
            <button
              type="button"
              onClick={() => void handlePlatformToggle(platform.connection_id)}
              disabled={toggling === platform.connection_id}
              className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors ${
                platform.seo_enabled ? 'bg-green-600' : 'bg-slate-200'
              } ${toggling === platform.connection_id ? 'opacity-50' : ''}`}
            >
              {toggling === platform.connection_id && (
                <Loader2 className="absolute left-0.5 w-3 h-3 animate-spin text-white" />
              )}
              <span
                className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${
                  platform.seo_enabled ? 'translate-x-6' : 'translate-x-0.5'
                }`}
              />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
