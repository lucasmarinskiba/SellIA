'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { channelsApi, ChannelConnection } from '@/lib/channels'
import { ChannelPlatform } from '@/types/channels'
import { businessApi, Business } from '@/lib/business'
import {
  MessageSquare, Mail, Camera as Instagram, ShoppingCart, Briefcase as Linkedin, Link2,
  Plus, Trash2, CheckCircle2, AlertCircle, Clock, ExternalLink,
  Phone, Plug, Zap, X, Loader2, Copy, Check,
  Megaphone, Globe, Search, ShoppingBag, Music
} from 'lucide-react'

const platformConfig: Record<string, { label: string; icon: typeof MessageSquare; color: string; description: string }> = {
  whatsapp: { label: 'WhatsApp', icon: Phone, color: 'text-green-400', description: 'WhatsApp Business API' },
  email: { label: 'Email', icon: Mail, color: 'text-blue-400', description: 'SMTP / Email' },
  instagram: { label: 'Instagram', icon: Instagram, color: 'text-pink-400', description: 'Instagram DMs' },
  mercadolibre: { label: 'MercadoLibre', icon: ShoppingCart, color: 'text-yellow-400', description: 'Preguntas y ventas' },
  amazon: { label: 'Amazon', icon: ShoppingCart, color: 'text-orange-400', description: 'Amazon Seller' },
  beacons: { label: 'Beacons', icon: Link2, color: 'text-purple-400', description: 'Beacons / Linktree' },
  linkedin: { label: 'LinkedIn', icon: Linkedin, color: 'text-sky-400', description: 'LinkedIn Messages' },
  messenger: { label: 'Messenger', icon: MessageSquare, color: 'text-blue-300', description: 'Facebook Messenger' },
  telegram: { label: 'Telegram', icon: MessageSquare, color: 'text-cyan-400', description: 'Telegram Bot' },
  webchat: { label: 'WebChat', icon: MessageSquare, color: 'text-white', description: 'Chat en tu sitio web' },
  facebook_ads: { label: 'Facebook Ads', icon: Megaphone, color: 'text-blue-600', description: 'Facebook Ads' },
  meta_ads: { label: 'Meta Ads', icon: Globe, color: 'text-indigo-600', description: 'Meta Ads' },
  google_ads: { label: 'Google Ads', icon: Search, color: 'text-red-500', description: 'Google Ads' },
  shopify: { label: 'Shopify', icon: ShoppingBag, color: 'text-green-600', description: 'Shopify' },
  tiktok_ads: { label: 'TikTok Ads', icon: Music, color: 'text-black', description: 'TikTok Ads' },
  tiktok: { label: 'TikTok', icon: Music, color: 'text-black', description: 'TikTok' },
}

const statusConfig: Record<string, { icon: typeof CheckCircle2; color: string; label: string }> = {
  connected: { icon: CheckCircle2, color: 'text-green-400', label: 'Conectado' },
  pending: { icon: Clock, color: 'text-yellow-400', label: 'Pendiente' },
  error: { icon: AlertCircle, color: 'text-red-400', label: 'Error' },
  disabled: { icon: AlertCircle, color: 'text-white/30', label: 'Deshabilitado' },
}

export default function CanalesPage() {
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [selectedBusiness, setSelectedBusiness] = useState<string>('')
  const [channels, setChannels] = useState<ChannelConnection[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [testingId, setTestingId] = useState<string | null>(null)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [newChannel, setNewChannel] = useState({
    platform: 'whatsapp' as ChannelPlatform,
    name: '',
    credentials: {} as Record<string, any>,
  })

  useEffect(() => {
    loadBusinesses()
  }, [])

  useEffect(() => {
    if (selectedBusiness) {
      loadChannels()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBusiness])

  const loadBusinesses = async () => {
    try {
      const data = await businessApi.list()
      setBusinesses(data)
      if (data.length > 0 && !selectedBusiness) {
        setSelectedBusiness(data[0].id)
      }
    } catch {
      setLoading(false)
    }
  }

  const loadChannels = async () => {
    setLoading(true)
    try {
      const data = await channelsApi.list(selectedBusiness)
      setChannels(data)
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false)
    }
  }

  const handleCreateChannel = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await channelsApi.create(selectedBusiness, {
        platform: newChannel.platform,
        name: newChannel.name,
        credentials: newChannel.credentials,
      })
      setShowAddModal(false)
      setNewChannel({ platform: 'whatsapp', name: '', credentials: {} })
      await loadChannels()
    } catch {
      // handled by interceptor
    }
  }

  const handleDelete = async (channelId: string) => {
    if (!confirm('¿Eliminar este canal?')) return
    try {
      await channelsApi.delete(selectedBusiness, channelId)
      await loadChannels()
    } catch {
      // handled by interceptor
    }
  }

  const handleTest = async (channelId: string) => {
    setTestingId(channelId)
    try {
      await channelsApi.test(selectedBusiness, channelId)
      await loadChannels()
    } catch {
      alert('Error al probar conexión')
    } finally {
      setTestingId(null)
    }
  }

  const copyWebhook = (url: string, id: string) => {
    navigator.clipboard.writeText(url)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const renderCredentialFields = () => {
    switch (newChannel.platform) {
      case 'whatsapp':
        return (
          <>
            <Field label="API Token" type="password" placeholder="EAAB..." value={newChannel.credentials.api_token || ''} onChange={v => setNewChannel({ ...newChannel, credentials: { ...newChannel.credentials, api_token: v } })} />
            <Field label="Phone Number ID" value={newChannel.credentials.phone_number_id || ''} onChange={v => setNewChannel({ ...newChannel, credentials: { ...newChannel.credentials, phone_number_id: v } })} />
            <Field label="Business Account ID" value={newChannel.credentials.business_account_id || ''} onChange={v => setNewChannel({ ...newChannel, credentials: { ...newChannel.credentials, business_account_id: v } })} />
          </>
        )
      case 'email':
        return (
          <>
            <Field label="SMTP Host" value={newChannel.credentials.smtp_host || ''} onChange={v => setNewChannel({ ...newChannel, credentials: { ...newChannel.credentials, smtp_host: v } })} placeholder="smtp.gmail.com" />
            <Field label="SMTP Port" value={newChannel.credentials.smtp_port || ''} onChange={v => setNewChannel({ ...newChannel, credentials: { ...newChannel.credentials, smtp_port: v } })} placeholder="587" />
            <Field label="SMTP User" value={newChannel.credentials.smtp_user || ''} onChange={v => setNewChannel({ ...newChannel, credentials: { ...newChannel.credentials, smtp_user: v } })} />
            <Field label="SMTP Password" type="password" value={newChannel.credentials.smtp_password || ''} onChange={v => setNewChannel({ ...newChannel, credentials: { ...newChannel.credentials, smtp_password: v } })} />
            <Field label="From Address" value={newChannel.credentials.from_address || ''} onChange={v => setNewChannel({ ...newChannel, credentials: { ...newChannel.credentials, from_address: v } })} />
          </>
        )
      case 'instagram':
        return (
          <>
            <Field label="API Token" type="password" value={newChannel.credentials.api_token || ''} onChange={v => setNewChannel({ ...newChannel, credentials: { ...newChannel.credentials, api_token: v } })} />
            <Field label="Instagram Account ID" value={newChannel.credentials.instagram_account_id || ''} onChange={v => setNewChannel({ ...newChannel, credentials: { ...newChannel.credentials, instagram_account_id: v } })} />
            <Field label="Page ID" value={newChannel.credentials.page_id || ''} onChange={v => setNewChannel({ ...newChannel, credentials: { ...newChannel.credentials, page_id: v } })} />
          </>
        )
      case 'mercadolibre':
        return (
          <>
            <Field label="Client ID" value={newChannel.credentials.client_id || ''} onChange={v => setNewChannel({ ...newChannel, credentials: { ...newChannel.credentials, client_id: v } })} />
            <Field label="Client Secret" type="password" value={newChannel.credentials.client_secret || ''} onChange={v => setNewChannel({ ...newChannel, credentials: { ...newChannel.credentials, client_secret: v } })} />
            <Field label="Redirect URI" value={newChannel.credentials.redirect_uri || ''} onChange={v => setNewChannel({ ...newChannel, credentials: { ...newChannel.credentials, redirect_uri: v } })} placeholder="https://tudominio.com/callback" />
            <p className="text-xs text-white/30">Después de guardar, usá el botón de OAuth para conectar.</p>
          </>
        )
      case 'telegram':
        return (
          <>
            <Field label="Bot Token" type="password" value={newChannel.credentials.bot_token || ''} onChange={v => setNewChannel({ ...newChannel, credentials: { ...newChannel.credentials, bot_token: v } })} placeholder="123456:ABC-DEF..." />
          </>
        )
      case 'webchat':
        return (
          <>
            <Field label="Site Domain" value={newChannel.credentials.site_domain || ''} onChange={v => setNewChannel({ ...newChannel, credentials: { ...newChannel.credentials, site_domain: v } })} placeholder="tudominio.com" />
          </>
        )
      default:
        return (
          <div className="p-3 bg-white/5 rounded-lg text-sm text-white/30">
            Configuración manual disponible próximamente para este canal.
          </div>
        )
    }
  }

  return (
    <div className="space-y-8 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">🔌 Canales</h1>
          <p className="text-sm text-white/40">Conecta tus plataformas de venta y comunicación.</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={selectedBusiness}
            onChange={(e) => setSelectedBusiness(e.target.value)}
            className="px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
          >
            {businesses.map((b) => (
              <option key={b.id} value={b.id} className="bg-[#0A0E1A]">{b.name}</option>
            ))}
          </select>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-orange text-white text-sm font-medium hover:bg-brand-orange/90 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Conectar canal
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
        </div>
      ) : channels.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <Plug className="w-12 h-12 text-white/20 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white/60">No tienes canales conectados</h3>
          <p className="text-white/30 mt-1 mb-6">Conecta WhatsApp, Email u otras plataformas para recibir leads</p>
          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-orange text-white text-sm font-medium hover:bg-brand-orange/90 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Conectar primer canal
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {channels.map((channel) => {
            const pConfig = platformConfig[channel.platform] || platformConfig.whatsapp
            const sConfig = statusConfig[channel.status] || statusConfig.pending
            const PlatformIcon = pConfig.icon
            const StatusIcon = sConfig.icon
            const isTesting = testingId === channel.id
            return (
              <motion.div
                key={channel.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-card p-5"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center ${pConfig.color}`}>
                    <PlatformIcon className="w-6 h-6" />
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`flex items-center gap-1 text-xs font-medium ${sConfig.color}`}>
                      <StatusIcon className="w-3.5 h-3.5" />
                      {sConfig.label}
                    </span>
                    <button
                      onClick={() => handleDelete(channel.id)}
                      className="p-1.5 rounded-lg hover:bg-red-500/10 text-white/20 hover:text-red-400 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <h3 className="font-semibold text-white">{channel.name}</h3>
                <p className="text-sm text-white/30">{pConfig.description}</p>

                {channel.webhook_url && (
                  <div className="mt-3 p-2.5 rounded-lg bg-white/5 flex items-center gap-2">
                    <p className="text-xs text-white/30 truncate flex-1">{channel.webhook_url}</p>
                    <button
                      onClick={() => copyWebhook(channel.webhook_url!, channel.id)}
                      className="shrink-0 p-1 rounded hover:bg-white/10 text-white/30 hover:text-white transition-colors"
                      title="Copiar webhook URL"
                    >
                      {copiedId === channel.id ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                )}

                <div className="flex items-center gap-2 mt-4 pt-3 border-t border-white/5">
                  <button
                    onClick={() => handleTest(channel.id)}
                    disabled={isTesting}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs text-white/60 hover:text-white transition-colors disabled:opacity-50"
                  >
                    {isTesting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Zap className="w-3 h-3" />}
                    Probar
                  </button>
                  {channel.status === 'error' && channel.status_message && (
                    <span className="text-xs text-red-400 truncate">{channel.status_message}</span>
                  )}
                </div>
              </motion.div>
            )
          })}
        </div>
      )}

      {/* Add Modal */}
      <AnimatePresence>
        {showAddModal && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
              className="bg-[#0F1629] border border-white/10 rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto p-6"
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-white">Conectar nuevo canal</h2>
                <button onClick={() => setShowAddModal(false)} className="p-2 rounded-lg hover:bg-white/5"><X className="w-5 h-5 text-white/40" /></button>
              </div>
              <form onSubmit={handleCreateChannel} className="space-y-4">
                <div>
                  <label className="text-xs text-white/40 mb-1 block">Plataforma</label>
                  <select
                    value={newChannel.platform}
                    onChange={(e) => setNewChannel({ ...newChannel, platform: e.target.value as ChannelPlatform, credentials: {} })}
                    className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                  >
                    {Object.entries(platformConfig).map(([key, config]) => (
                      <option key={key} value={key} className="bg-[#0A0E1A]">{config.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-white/40 mb-1 block">Nombre</label>
                  <input
                    type="text"
                    value={newChannel.name}
                    onChange={(e) => setNewChannel({ ...newChannel, name: e.target.value })}
                    required
                    className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                    placeholder="Ej: WhatsApp Principal"
                  />
                </div>
                <div className="space-y-3">
                  <p className="text-sm font-medium text-white/60">Credenciales</p>
                  {renderCredentialFields()}
                </div>
                <div className="flex items-center justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="px-4 py-2 rounded-xl text-sm text-white/60 hover:text-white transition-colors"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-xl bg-brand-orange text-white text-sm font-medium hover:bg-brand-orange/90 transition-colors"
                  >
                    Guardar
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function Field({ label, type = 'text', placeholder, value, onChange }: {
  label: string; type?: string; placeholder?: string; value: string; onChange: (v: string) => void
}) {
  return (
    <div>
      <label className="text-xs text-white/40 mb-1 block">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
      />
    </div>
  )
}
