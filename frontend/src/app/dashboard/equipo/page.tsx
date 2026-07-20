'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '@/hooks/useAuth'
import { businessApi } from '@/lib/business'
import { socialSellersApi, SocialSeller, TeamReport, LookalikeReport } from '@/lib/api/socialSellers'
import {
  Users, Plus, TrendingUp, MessageCircle, Camera as Instagram, Smartphone, Globe,
  Trophy, Flame, Zap, Loader2, X, AlertCircle, Pause, Play, Trash2,
  Target, UserPlus,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/Dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select'

// ─── Platform Config ─────────────────────────────────────────────────────────

const PLATFORM_CONFIG: Record<string, {
  label: string
  icon: any
  gradient: string
  glow: string
  bg: string
  border: string
  text: string
}> = {
  instagram: {
    label: 'Instagram',
    icon: Instagram,
    gradient: 'from-purple-500 to-pink-500',
    glow: 'group-hover:shadow-purple-500/20',
    bg: 'bg-purple-500/10',
    border: 'border-purple-500/20',
    text: 'text-purple-400',
  },
  tiktok: {
    label: 'TikTok',
    icon: Zap,
    gradient: 'from-cyan-400 to-red-500',
    glow: 'group-hover:shadow-cyan-400/20',
    bg: 'bg-cyan-400/10',
    border: 'border-cyan-400/20',
    text: 'text-cyan-400',
  },
  whatsapp: {
    label: 'WhatsApp',
    icon: MessageCircle,
    gradient: 'from-green-500 to-emerald-600',
    glow: 'group-hover:shadow-green-500/20',
    bg: 'bg-green-500/10',
    border: 'border-green-500/20',
    text: 'text-green-400',
  },
  facebook: {
    label: 'Facebook',
    icon: Globe,
    gradient: 'from-blue-500 to-blue-700',
    glow: 'group-hover:shadow-blue-500/20',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/20',
    text: 'text-blue-400',
  },
  twitter: {
    label: 'X / Twitter',
    icon: Smartphone,
    gradient: 'from-gray-800 to-black',
    glow: 'group-hover:shadow-gray-500/20',
    bg: 'bg-gray-500/10',
    border: 'border-gray-500/20',
    text: 'text-gray-400',
  },
  threads: {
    label: 'Threads',
    icon: MessageCircle,
    gradient: 'from-gray-700 to-gray-900',
    glow: 'group-hover:shadow-gray-500/20',
    bg: 'bg-gray-500/10',
    border: 'border-gray-500/20',
    text: 'text-gray-400',
  },
  linkedin: {
    label: 'LinkedIn',
    icon: Globe,
    gradient: 'from-blue-700 to-blue-900',
    glow: 'group-hover:shadow-blue-700/20',
    bg: 'bg-blue-700/10',
    border: 'border-blue-700/20',
    text: 'text-blue-400',
  },
}

function getPlatformConfig(platform: string) {
  const key = platform.toLowerCase()
  return PLATFORM_CONFIG[key] || {
    label: platform,
    icon: Globe,
    gradient: 'from-brand-orange to-brand-orange-dark',
    glow: 'group-hover:shadow-brand-orange/20',
    bg: 'bg-brand-orange/10',
    border: 'border-brand-orange/20',
    text: 'text-brand-orange',
  }
}

const STATUS_CONFIG: Record<string, { label: string; dot: string; text: string }> = {
  active: { label: 'Vendiendo', dot: 'bg-emerald-500', text: 'text-emerald-400' },
  paused: { label: 'En pausa', dot: 'bg-amber-500', text: 'text-amber-400' },
  training: { label: 'En entrenamiento', dot: 'bg-red-500', text: 'text-red-400' },
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function EquipoPage() {
  const router = useRouter()
  const { user } = useAuth()

  const [sellers, setSellers] = useState<SocialSeller[]>([])
  const [teamReport, setTeamReport] = useState<TeamReport | null>(null)
  const [lookalike, setLookalike] = useState<LookalikeReport | null>(null)
  const [businessId, setBusinessId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [creating, setCreating] = useState(false)

  const [newSeller, setNewSeller] = useState({
    platform: 'instagram',
    name: '',
    personality_slug: '',
    voice_config: '{}',
  })

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const businesses = await businessApi.list().catch(() => [])
      const bid = businesses?.[0]?.id
      setBusinessId(bid || null)
      if (bid) {
        const [sellersData, report, lookalikeData] = await Promise.all([
          socialSellersApi.listSellers(bid).catch(() => []),
          socialSellersApi.getTeamReport(bid).catch(() => null),
          socialSellersApi.getLookalikeReport(bid).catch(() => null),
        ])
        setSellers(sellersData)
        setTeamReport(report)
        setLookalike(lookalikeData)
      } else {
        setSellers([])
        setTeamReport(null)
        setLookalike(null)
      }
    } catch (e: any) {
      setError(e?.message || 'Error cargando vendedores')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleCreate = async () => {
    const businesses = await businessApi.list().catch(() => [])
    const businessId = businesses?.[0]?.id
    if (!businessId) return

    setCreating(true)
    try {
      let voiceConfig: Record<string, any> = {}
      try {
        voiceConfig = JSON.parse(newSeller.voice_config || '{}')
      } catch {
        voiceConfig = {}
      }

      await socialSellersApi.createSeller({
        business_id: businessId,
        platform: newSeller.platform,
        name: newSeller.name,
        personality_slug: newSeller.personality_slug || undefined,
        voice_config: voiceConfig,
      })

      setModalOpen(false)
      setNewSeller({ platform: 'instagram', name: '', personality_slug: '', voice_config: '{}' })
      await loadData()
    } catch (e: any) {
      setError(e?.message || 'Error creando vendedor')
    } finally {
      setCreating(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <div className="text-center space-y-3">
          <Users className="w-10 h-10 text-brand-orange animate-pulse mx-auto" />
          <p className="text-white/40 text-sm">Cargando tu equipo...</p>
        </div>
      </div>
    )
  }

  const activeSellers = sellers.filter(s => s.status === 'active')
  const topSeller = teamReport?.top_performer || sellers[0]
  const totalRevenue = teamReport?.total_revenue || sellers.reduce((sum, s) => sum + (s.stats?.revenue || 0), 0)
  const totalDeals = teamReport?.total_deals || sellers.reduce((sum, s) => sum + (s.stats?.total_sales || 0), 0)

  return (
    <div className="min-h-screen bg-[#060812]">
      <div className="max-w-7xl mx-auto p-6 space-y-8">

        {/* ── Header ────────────────────────────────────────────── */}
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-orange/20 to-purple-500/20 border border-brand-orange/20 flex items-center justify-center">
                <Users className="w-5 h-5 text-brand-orange" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Mi Equipo de Vendedores</h1>
                <p className="text-white/40 text-sm">Tu dream team vende 24/7</p>
              </div>
            </div>
          </div>
          <Button
            onClick={() => setModalOpen(true)}
            leftIcon={<Plus className="w-4 h-4" />}
            className="bg-brand-orange/20 hover:bg-brand-orange/30 border border-brand-orange/30 text-brand-orange"
          >
            Agregar vendedor
          </Button>
        </div>

        {/* ── Team Stats Bar ───────────────────────────────────── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Revenue esta semana', value: `$${totalRevenue.toLocaleString('es-AR')}`, icon: TrendingUp, color: 'text-emerald-400' },
            { label: 'Total ventas', value: totalDeals, icon: Trophy, color: 'text-amber-400' },
            { label: 'Sellers activos', value: activeSellers.length, icon: Users, color: 'text-blue-400' },
            { label: 'Top seller', value: topSeller?.name || '—', icon: Flame, color: 'text-orange-400' },
          ].map(stat => (
            <div key={stat.label} className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <stat.icon className={`w-4 h-4 ${stat.color}`} />
                <span className="text-xs text-white/40">{stat.label}</span>
              </div>
              <p className="text-xl font-bold text-white truncate">{stat.value}</p>
            </div>
          ))}
        </div>

        {/* ── Error ────────────────────────────────────────────── */}
        {error && (
          <div className="flex items-center gap-2 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        {/* ── Seller Grid ──────────────────────────────────────── */}
        {sellers.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-24 h-24 rounded-full bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mb-6">
              <Users className="w-10 h-10 text-white/10" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Todavía no tenés vendedores</h3>
            <p className="text-white/40 text-sm max-w-md mb-6">
              Conectá un canal y te armamos tu primer seller.
            </p>
            <Button onClick={() => setModalOpen(true)} leftIcon={<Plus className="w-4 h-4" />}>
              Crear primer vendedor
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            <AnimatePresence>
              {sellers.map((seller, index) => (
                <SellerCard
                  key={seller.id}
                  seller={seller}
                  index={index}
                  isTop={seller.id === topSeller?.id && index === 0}
                  onClick={() => router.push(`/dashboard/equipo/${seller.id}`)}
                />
              ))}
            </AnimatePresence>
          </div>
        )}

        {/* ── Add Seller Modal ─────────────────────────────────── */}
        <Dialog open={modalOpen} onOpenChange={setModalOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Agregar vendedor</DialogTitle>
              <DialogDescription>
                Creá un nuevo seller para tu equipo de ventas
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <label className="text-xs text-white/40 mb-1.5 block">Plataforma</label>
                <Select
                  value={newSeller.platform}
                  onValueChange={(v) => setNewSeller(prev => ({ ...prev, platform: v }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar plataforma" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(PLATFORM_CONFIG).map(([key, cfg]) => (
                      <SelectItem key={key} value={key}>
                        <span className="flex items-center gap-2">
                          <cfg.icon className="w-3.5 h-3.5" />
                          {cfg.label}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-xs text-white/40 mb-1.5 block">Nombre del seller</label>
                <input
                  type="text"
                  value={newSeller.name}
                  onChange={e => setNewSeller(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Ej: Zoe, Max, Luna..."
                  className="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                />
              </div>

              <div>
                <label className="text-xs text-white/40 mb-1.5 block">Personalidad (opcional)</label>
                <input
                  type="text"
                  value={newSeller.personality_slug}
                  onChange={e => setNewSeller(prev => ({ ...prev, personality_slug: e.target.value }))}
                  placeholder="Ej: friendly-closer, visual-creator..."
                  className="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                />
              </div>

              <div>
                <label className="text-xs text-white/40 mb-1.5 block">Voice config JSON (opcional)</label>
                <textarea
                  value={newSeller.voice_config}
                  onChange={e => setNewSeller(prev => ({ ...prev, voice_config: e.target.value }))}
                  rows={4}
                  placeholder='{"tone":"amigable","emojis":["✨","🔥"]}'
                  className="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-brand-orange/20 font-mono"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  variant="ghost"
                  onClick={() => setModalOpen(false)}
                  className="flex-1"
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handleCreate}
                  isLoading={creating}
                  disabled={!newSeller.name.trim()}
                  className="flex-1"
                >
                  Crear vendedor
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* ── Lookalike Opportunities ──────────────────────────── */}
        {lookalike && (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border border-emerald-500/20 flex items-center justify-center">
                <Target className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">Lookalike Opportunities</h2>
                <p className="text-white/40 text-sm">Encontrá clientes como tu Fan #1</p>
              </div>
            </div>

            <div className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-5 space-y-4">
              {/* Ideal profile summary */}
              <div className="flex items-center gap-2 text-sm text-white/70">
                <Flame className="w-4 h-4 text-orange-400" />
                <span>Tus mejores clientes:</span>
                <span className="text-white font-medium">
                  {lookalike.ideal_profile.preferred_platforms[0]
                    ? `Compran por ${lookalike.ideal_profile.preferred_platforms[0].toUpperCase()}`
                    : 'Compran frecuentemente'}
                  {' · '}
                  Cada {Math.round(lookalike.ideal_profile.avg_purchase_frequency_days)} días
                  {' · '}
                  Responden en &lt; 5 min
                </span>
              </div>

              {/* Top 5 lookalike leads */}
              <div className="space-y-3">
                {lookalike.top_opportunities.slice(0, 5).map((lead, idx) => {
                  const platform = getPlatformConfig(lead.platform)
                  const sellerName = lead.recommended_seller || 'Zoe'
                  return (
                    <motion.div
                      key={lead.lead_id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.1 }}
                      className="flex items-center gap-3 p-3 bg-white/[0.02] border border-white/[0.06] rounded-xl"
                    >
                      <div className={`w-8 h-8 rounded-full bg-gradient-to-br ${platform.gradient} flex items-center justify-center text-[10px] font-bold text-white`}>
                        {lead.name.charAt(0)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-white truncate">
                          {lead.name}{' '}
                          <span className="text-white/40">({lead.platform.toUpperCase()})</span>
                          {' · '}
                          <span className="text-emerald-400 font-medium">{lead.similarity_score}% parecido a tu cliente ideal</span>
                          {' · '}
                          <span className="text-white/50">{sellerName} debería contactarlo</span>
                        </p>
                      </div>
                      <Button
                        size="sm"
                        className="shrink-0 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/30 text-emerald-400"
                        leftIcon={<UserPlus className="w-3 h-3" />}
                        onClick={() => {
                          // TODO: assign lead to recommended seller
                          alert(`Asignar ${lead.name} a ${sellerName}`)
                        }}
                      >
                        Asignar a {sellerName}
                      </Button>
                    </motion.div>
                  )
                })}
                {lookalike.top_opportunities.length === 0 && (
                  <p className="text-sm text-white/30 text-center py-4">
                    No hay leads lookalike por el momento. Seguí interactuando para entrenar el modelo.
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Seller Card ─────────────────────────────────────────────────────────────

function SellerCard({ seller, index, isTop, onClick }: {
  seller: SocialSeller
  index: number
  isTop: boolean
  onClick: () => void
}) {
  const platform = getPlatformConfig(seller.platform)
  const status = STATUS_CONFIG[seller.status] || STATUS_CONFIG.training
  const revenue = seller.stats?.revenue || 0
  const deals = seller.stats?.total_sales || 0
  const conversion = seller.stats?.conversion_rate || 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3, delay: index * 0.08 }}
      onClick={onClick}
      className={`group relative bg-white/[0.03] hover:bg-white/[0.05] border border-white/[0.06] hover:border-white/[0.12] rounded-2xl p-5 cursor-pointer transition-all duration-300 hover:-translate-y-1 hover:shadow-xl ${platform.glow}`}
    >
      {/* Top performer badge */}
      {isTop && (
        <div className="absolute -top-2 -right-2 flex items-center gap-1 px-2.5 py-1 bg-gradient-to-r from-orange-500 to-red-500 rounded-full text-[10px] font-bold text-white shadow-lg">
          <Flame className="w-3 h-3" />
          #1 del equipo
        </div>
      )}

      {/* Avatar + Platform */}
      <div className="flex items-start gap-4 mb-4">
        <div className="relative">
          <div className={`w-16 h-16 rounded-full bg-gradient-to-br ${platform.gradient} p-[2px]`}>
            <div className="w-full h-full rounded-full bg-[#060812] flex items-center justify-center overflow-hidden">
              {seller.avatar_url ? (
                <img src={seller.avatar_url} alt={seller.name} className="w-full h-full object-cover" />
              ) : (
                <span className="text-xl font-bold text-white">{seller.name.charAt(0)}</span>
              )}
            </div>
          </div>
          <div className={`absolute -bottom-0.5 -right-0.5 w-6 h-6 rounded-full bg-gradient-to-br ${platform.gradient} flex items-center justify-center border-2 border-[#060812]`}>
            <platform.icon className="w-3 h-3 text-white" />
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-white font-semibold truncate">{seller.name}</h3>
            <span className={`text-[10px] px-2 py-0.5 rounded-full border ${platform.bg} ${platform.border} ${platform.text}`}>
              {platform.label}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${status.dot}`} />
            <span className={`text-xs ${status.text}`}>{status.label}</span>
          </div>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="text-center">
          <p className="text-lg font-bold text-white">${revenue.toLocaleString('es-AR')}</p>
          <p className="text-[10px] text-white/30">Revenue</p>
        </div>
        <div className="text-center">
          <p className="text-lg font-bold text-white">{deals}</p>
          <p className="text-[10px] text-white/30">Ventas</p>
        </div>
        <div className="text-center">
          <p className="text-lg font-bold text-white">{conversion}%</p>
          <p className="text-[10px] text-white/30">Conv.</p>
        </div>
      </div>

      {/* Confianza Progress */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[10px] text-white/30">Confianza</span>
          <span className="text-[10px] text-white/50">{Math.min(100, Math.round((deals || 0) * 5 + (conversion || 0)))}%</span>
        </div>
        <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(100, Math.round((deals || 0) * 5 + (conversion || 0)))}%` }}
            transition={{ duration: 1, delay: index * 0.1 + 0.3 }}
            className={`h-full rounded-full bg-gradient-to-r ${platform.gradient}`}
          />
        </div>
      </div>

      {/* CTA */}
      <button
        onClick={(e) => { e.stopPropagation(); onClick() }}
        className={`w-full py-2 text-xs font-medium rounded-xl border transition-colors ${platform.bg} ${platform.border} ${platform.text} hover:bg-white/5`}
      >
        Ver pipeline
      </button>
    </motion.div>
  )
}
