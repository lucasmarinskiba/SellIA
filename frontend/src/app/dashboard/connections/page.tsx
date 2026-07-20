'use client'

import { useState, useEffect, useCallback } from 'react'
import { api } from '@/lib/api'
import { isSafeRedirectUrl } from '@/lib/security'
import { ChannelConnection, ChannelStatus, SyncResult } from '@/types/channels'

type ChannelPlatform = ChannelConnection['platform']

const PLATFORM_CONFIG: Record<ChannelPlatform, { label: string; color: string; oauth: boolean }> = {
  whatsapp: { label: 'WhatsApp', color: 'bg-green-500', oauth: false },
  email: { label: 'Email', color: 'bg-blue-500', oauth: false },
  instagram: { label: 'Instagram', color: 'bg-pink-500', oauth: true },
  messenger: { label: 'Messenger', color: 'bg-blue-600', oauth: true },
  telegram: { label: 'Telegram', color: 'bg-sky-500', oauth: false },
  linkedin: { label: 'LinkedIn', color: 'bg-blue-700', oauth: false },
  webchat: { label: 'WebChat', color: 'bg-purple-500', oauth: false },
  mercadolibre: { label: 'MercadoLibre', color: 'bg-yellow-500', oauth: true },
  facebook_ads: { label: 'Facebook Ads', color: 'bg-blue-700', oauth: true },
  meta_ads: { label: 'Meta Ads', color: 'bg-indigo-600', oauth: true },
  google_ads: { label: 'Google Ads', color: 'bg-red-500', oauth: true },
  shopify: { label: 'Shopify', color: 'bg-green-600', oauth: false },
  tiktok_ads: { label: 'TikTok Ads', color: 'bg-black', oauth: true },
  amazon: { label: 'Amazon', color: 'bg-orange-500', oauth: false },
  beacons: { label: 'Beacons', color: 'bg-violet-500', oauth: false },
  tiktok: { label: 'TikTok', color: 'bg-black', oauth: true },
}

const STATUS_STYLES: Record<ChannelStatus, string> = {
  pending: 'text-yellow-400',
  connected: 'text-green-400',
  error: 'text-red-400',
  disabled: 'text-gray-400',
}

export default function ConnectionsPage() {
  const [channels, setChannels] = useState<ChannelConnection[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [syncResults, setSyncResults] = useState<SyncResult[]>([])
  const [error, setError] = useState('')

  const businessId = typeof window !== 'undefined'
    ? localStorage.getItem('business_id') || ''
    : ''

  const fetchChannels = useCallback(async () => {
    if (!businessId) return
    try {
      setLoading(true)
      const { data } = await api.get(`/businesses/${businessId}/channels`)
      setChannels(data || [])
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error cargando conexiones')
    } finally {
      setLoading(false)
    }
  }, [businessId])

  useEffect(() => {
    fetchChannels()
  }, [fetchChannels])

  const handleConnect = async (platform: ChannelPlatform) => {
    if (!businessId) return
    try {
      const { data } = await api.get(`/businesses/${businessId}/channels/${platform}/auth-url`)
      if (data.auth_url && isSafeRedirectUrl(data.auth_url)) {
        window.location.href = data.auth_url
      } else {
        alert('URL de autorización no válida')
      }
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Error generando URL de OAuth')
    }
  }

  const handleDisconnect = async (channelId: string) => {
    if (!businessId) return
    if (!confirm('¿Seguro que querés desconectar este canal?')) return
    try {
      await api.delete(`/businesses/${businessId}/channels/${channelId}`)
      fetchChannels()
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Error desconectando canal')
    }
  }

  const handleSyncCatalog = async () => {
    if (!businessId) return
    setSyncing(true)
    setSyncResults([])
    try {
      const { data } = await api.post(`/businesses/${businessId}/catalog/sync-push`)
      setSyncResults(data.results || [])
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Error sincronizando catálogo')
    } finally {
      setSyncing(false)
    }
  }

  const connectedPlatforms = new Set(channels.map((c) => c.platform))

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold">Conexiones</h1>
            <p className="text-gray-400 mt-1">
              {channels.length} canal{channels.length !== 1 ? 'es' : ''} conectado{channels.length !== 1 ? 's' : ''}
            </p>
          </div>
          <button
            onClick={handleSyncCatalog}
            disabled={syncing || channels.length === 0}
            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            {syncing ? (
              <>
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Sincronizando...
              </>
            ) : (
              <>🔄 Sincronizar Catálogo</>
            )}
          </button>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-900/50 border border-red-500 rounded-lg text-red-200">
            {error}
          </div>
        )}

        {syncResults.length > 0 && (
          <div className="mb-6 grid gap-2">
            {syncResults.map((r) => (
              <div
                key={r.platform}
                className={`p-3 rounded-lg border ${
                  r.success ? 'bg-green-900/30 border-green-500/50' : 'bg-red-900/30 border-red-500/50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{PLATFORM_CONFIG[r.platform as ChannelPlatform]?.label || r.platform}</span>
                  <span className={r.success ? 'text-green-400' : 'text-red-400'}>
                    {r.success ? '✓' : '✗'} {r.message}
                  </span>
                </div>
                {r.items_synced > 0 && (
                  <span className="text-sm text-gray-400">{r.items_synced} items sincronizados</span>
                )}
              </div>
            ))}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <span className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {Object.entries(PLATFORM_CONFIG).map(([platform, config]) => {
              const channel = channels.find((c) => c.platform === platform)
              const isConnected = !!channel

              return (
                <div
                  key={platform}
                  className={`p-5 rounded-xl border transition-all ${
                    isConnected
                      ? 'bg-gray-800 border-green-500/30 hover:border-green-500/50'
                      : 'bg-gray-800/50 border-gray-700 hover:border-gray-600'
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-lg ${config.color} flex items-center justify-center text-white font-bold text-lg`}>
                        {config.label[0]}
                      </div>
                      <div>
                        <h3 className="font-semibold">{config.label}</h3>
                        {isConnected && (
                          <span className={`text-sm ${STATUS_STYLES[channel.status]}`}>
                            {channel.status === 'connected' ? 'Conectado' : channel.status}
                          </span>
                        )}
                      </div>
                    </div>
                    {isConnected && (
                      <button
                        onClick={() => handleDisconnect(channel.id)}
                        className="text-gray-500 hover:text-red-400 transition-colors text-sm"
                        title="Desconectar"
                      >
                        ✕
                      </button>
                    )}
                  </div>

                  {isConnected && (
                    <div className="space-y-2 mb-4">
                      <div className="text-xs text-gray-400">
                        Token: <code className="bg-gray-900 px-2 py-0.5 rounded">{(channel.webhook_token || '').slice(0, 8)}...</code>
                      </div>
                      {channel.last_sync_at && (
                        <div className="text-xs text-gray-400">
                          Último sync: {new Date(channel.last_sync_at).toLocaleString()}
                        </div>
                      )}
                    </div>
                  )}

                  {!isConnected ? (
                    config.oauth ? (
                      <button
                        onClick={() => handleConnect(platform as ChannelPlatform)}
                        className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-sm font-medium transition-colors"
                      >
                        Conectar con OAuth
                      </button>
                    ) : (
                      <button
                        onClick={() => alert(`Configurá manualmente el canal de ${config.label}`)}
                        className="w-full py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors"
                      >
                        Configurar manualmente
                      </button>
                    )
                  ) : (
                    <div className="w-full py-2 bg-green-900/30 border border-green-500/30 rounded-lg text-sm text-center text-green-400">
                      Activo
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
