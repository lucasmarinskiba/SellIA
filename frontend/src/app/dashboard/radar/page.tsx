'use client'

import { useEffect, useState, useCallback, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '@/hooks/useAuth'
import { isSafeRedirectUrl } from '@/lib/security'
import { businessApi } from '@/lib/business'
import { socialSellersApi, RadarOpportunity, RadarData } from '@/lib/api/socialSellers'
import {
  Radar,
  Flame,
  Thermometer,
  Droplets,
  Snowflake,
  MessageCircle,
  Percent,
  User,
  Loader2,
  AlertCircle,
  Camera as Instagram,
  Smartphone,
  Globe,
  Zap,
  Send,
  Eye,
  ChevronRight,
  Calendar,
  Clock,
  ShoppingBag,
  RefreshCw,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'

// ─── Platform Config ─────────────────────────────────────────────────────────

const PLATFORM_CONFIG: Record<string, { label: string; icon: any; color: string }> = {
  instagram: { label: 'Instagram', icon: Instagram, color: 'text-pink-400' },
  tiktok: { label: 'TikTok', icon: Zap, color: 'text-cyan-400' },
  whatsapp: { label: 'WhatsApp', icon: Smartphone, color: 'text-green-400' },
  facebook: { label: 'Facebook', icon: Globe, color: 'text-blue-400' },
  messenger: { label: 'Messenger', icon: MessageCircle, color: 'text-blue-400' },
  twitter: { label: 'X / Twitter', icon: Smartphone, color: 'text-gray-400' },
  webchat: { label: 'Web', icon: Globe, color: 'text-purple-400' },
}

function getPlatformConfig(platform: string) {
  const key = platform.toLowerCase()
  return PLATFORM_CONFIG[key] || { label: platform, icon: Globe, color: 'text-brand-orange' }
}

// ─── Heat Level Config ───────────────────────────────────────────────────────

const HEAT_CONFIG: Record<string, {
  label: string
  subtitle: string
  icon: any
  gradient: string
  border: string
  glow: string
  text: string
  bg: string
  pulse: string
}> = {
  hot: {
    label: 'HOT',
    subtitle: 'Listos para comprar HOY',
    icon: Flame,
    gradient: 'from-red-500 to-orange-500',
    border: 'border-red-500/30',
    glow: 'shadow-red-500/20',
    text: 'text-red-400',
    bg: 'bg-red-500/10',
    pulse: 'animate-pulse',
  },
  warm: {
    label: 'WARM',
    subtitle: 'Probables esta semana',
    icon: Thermometer,
    gradient: 'from-orange-400 to-amber-500',
    border: 'border-orange-500/30',
    glow: 'shadow-orange-500/20',
    text: 'text-orange-400',
    bg: 'bg-orange-500/10',
    pulse: '',
  },
  nurture: {
    label: 'NURTURE',
    subtitle: 'Necesitan más valor',
    icon: Droplets,
    gradient: 'from-blue-400 to-cyan-500',
    border: 'border-blue-500/30',
    glow: 'shadow-blue-500/20',
    text: 'text-blue-400',
    bg: 'bg-blue-500/10',
    pulse: '',
  },
  at_risk: {
    label: 'AT RISK',
    subtitle: 'En riesgo de irse',
    icon: Snowflake,
    gradient: 'from-gray-400 to-slate-500',
    border: 'border-gray-500/30',
    glow: 'shadow-gray-500/20',
    text: 'text-gray-400',
    bg: 'bg-gray-500/10',
    pulse: '',
  },
}

// ─── Time Filter ─────────────────────────────────────────────────────────────

type TimeFilter = 'today' | 'week' | 'month' | 'all'

const TIME_FILTERS: { key: TimeFilter; label: string }[] = [
  { key: 'today', label: 'Hoy' },
  { key: 'week', label: 'Esta semana' },
  { key: 'month', label: 'Este mes' },
  { key: 'all', label: 'Todos' },
]

function matchesTimeFilter(opp: RadarOpportunity, filter: TimeFilter): boolean {
  if (filter === 'all') return true
  const lastContact = opp.last_contact_at ? new Date(opp.last_contact_at) : null
  if (!lastContact) return true
  const now = new Date()
  const diffHours = (now.getTime() - lastContact.getTime()) / (1000 * 60 * 60)
  if (filter === 'today') return diffHours <= 24
  if (filter === 'week') return diffHours <= 168
  if (filter === 'month') return diffHours <= 720
  return true
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function RadarPage() {
  const router = useRouter()
  const { user } = useAuth()

  const [radarData, setRadarData] = useState<RadarData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [timeFilter, setTimeFilter] = useState<TimeFilter>('all')
  const [actingId, setActingId] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const businesses = await businessApi.list().catch(() => [])
      const businessId = businesses?.[0]?.id
      if (businessId) {
        const data = await socialSellersApi.getRadar(businessId)
        setRadarData(data)
      } else {
        setRadarData(null)
      }
    } catch (e: any) {
      setError(e?.message || 'Error cargando radar')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleRefresh = () => {
    setRefreshing(true)
    loadData()
  }

  const handleAction = async (opp: RadarOpportunity, action: string) => {
    const businesses = await businessApi.list().catch(() => [])
    const businessId = businesses?.[0]?.id
    if (!businessId) return

    setActingId(`${opp.conversation_id}-${action}`)
    try {
      const result = await socialSellersApi.executeRadarAction(
        opp.conversation_id,
        businessId,
        { action, payload: { seller_id: opp.seller_id } }
      )
      if (result.redirect_url && action === 'view_profile' && isSafeRedirectUrl(result.redirect_url)) {
        router.push(result.redirect_url)
      }
    } catch (e: any) {
      setError(e?.message || 'Error ejecutando acción')
    } finally {
      setActingId(null)
    }
  }

  const filteredOpportunities = useMemo(() => {
    if (!radarData?.opportunities) return {}
    const result: Record<string, RadarOpportunity[]> = {}
    for (const [key, opps] of Object.entries(radarData.opportunities)) {
      result[key] = opps.filter((o) => matchesTimeFilter(o, timeFilter))
    }
    return result
  }, [radarData, timeFilter])

  const totalFiltered = useMemo(() => {
    return Object.values(filteredOpportunities).reduce((sum, arr) => sum + arr.length, 0)
  }, [filteredOpportunities])

  if (loading && !refreshing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <div className="text-center space-y-3">
          <Radar className="w-10 h-10 text-brand-orange animate-pulse mx-auto" />
          <p className="text-white/40 text-sm">Escaneando oportunidades...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#060812]">
      <div className="max-w-7xl mx-auto p-6 space-y-8">
        {/* ── Header ────────────────────────────────────────────── */}
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="relative">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-brand-orange/20 to-red-500/20 border border-brand-orange/20 flex items-center justify-center">
                <Radar className="w-6 h-6 text-brand-orange" />
              </div>
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-ping" />
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Radar de Oportunidades</h1>
              <p className="text-white/40 text-sm">Clientes listos para comprar ahora</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              isLoading={refreshing}
              leftIcon={<RefreshCw className="w-4 h-4" />}
              className="text-white/40 hover:text-white"
            >
              Actualizar
            </Button>
            <div className="flex bg-white/5 border border-white/10 rounded-xl p-1">
              {TIME_FILTERS.map((f) => (
                <button
                  key={f.key}
                  onClick={() => setTimeFilter(f.key)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                    timeFilter === f.key
                      ? 'bg-brand-orange/20 text-brand-orange'
                      : 'text-white/40 hover:text-white/60'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* ── Stats Bar ─────────────────────────────────────────── */}
        {radarData?.summary && (
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
            {[
              {
                label: 'Oportunidades',
                value: radarData.summary.total_opportunities,
                icon: Radar,
                color: 'text-brand-orange',
              },
              {
                label: 'Hot',
                value: radarData.summary.hot_count,
                icon: Flame,
                color: 'text-red-400',
              },
              {
                label: 'Warm',
                value: radarData.summary.warm_count,
                icon: Thermometer,
                color: 'text-orange-400',
              },
              {
                label: 'Nurture',
                value: radarData.summary.nurture_count,
                icon: Droplets,
                color: 'text-blue-400',
              },
              {
                label: 'At Risk',
                value: radarData.summary.at_risk_count,
                icon: Snowflake,
                color: 'text-gray-400',
              },
            ].map((stat) => (
              <div
                key={stat.label}
                className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-4"
              >
                <div className="flex items-center gap-2 mb-2">
                  <stat.icon className={`w-4 h-4 ${stat.color}`} />
                  <span className="text-xs text-white/40">{stat.label}</span>
                </div>
                <p className="text-xl font-bold text-white">{stat.value}</p>
              </div>
            ))}
          </div>
        )}

        {/* ── Error ────────────────────────────────────────────── */}
        {error && (
          <div className="flex items-center gap-2 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        {/* ── Empty State ──────────────────────────────────────── */}
        {totalFiltered === 0 && !loading && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-24 h-24 rounded-full bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mb-6 relative">
              <Radar className="w-10 h-10 text-white/10" />
              <span className="absolute inset-0 rounded-full border border-white/5 animate-ping" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">
              No hay oportunidades activas
            </h3>
            <p className="text-white/40 text-sm max-w-md mb-6">
              El radar escanea automáticamente tus conversaciones. Cuando detecte clientes con alta intención de compra, aparecerán acá.
            </p>
            <Button onClick={handleRefresh} leftIcon={<RefreshCw className="w-4 h-4" />}>
              Escanear de nuevo
            </Button>
          </div>
        )}

        {/* ── Opportunity Grid ─────────────────────────────────── */}
        <div className="space-y-8">
          {(['hot', 'warm', 'nurture', 'at_risk'] as const).map((heatLevel) => {
            const opps = filteredOpportunities[heatLevel] || []
            if (opps.length === 0) return null
            const config = HEAT_CONFIG[heatLevel]

            return (
              <section key={heatLevel}>
                <div className="flex items-center gap-3 mb-4">
                  <config.icon className={`w-5 h-5 ${config.text}`} />
                  <div>
                    <h2 className="text-lg font-bold text-white">{config.label}</h2>
                    <p className="text-xs text-white/40">{config.subtitle}</p>
                  </div>
                  <span className={`ml-auto text-xs px-2.5 py-1 rounded-full border ${config.bg} ${config.border} ${config.text}`}>
                    {opps.length}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
                  <AnimatePresence>
                    {opps.map((opp, index) => (
                      <OpportunityCard
                        key={opp.conversation_id}
                        opportunity={opp}
                        index={index}
                        heatConfig={config}
                        actingId={actingId}
                        onAction={handleAction}
                        onViewProfile={() =>
                          router.push(`/dashboard/conversaciones/${opp.conversation_id}`)
                        }
                      />
                    ))}
                  </AnimatePresence>
                </div>
              </section>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ─── Opportunity Card ────────────────────────────────────────────────────────

function OpportunityCard({
  opportunity,
  index,
  heatConfig,
  actingId,
  onAction,
  onViewProfile,
}: {
  opportunity: RadarOpportunity
  index: number
  heatConfig: (typeof HEAT_CONFIG)['hot']
  actingId: string | null
  onAction: (opp: RadarOpportunity, action: string) => void
  onViewProfile: () => void
}) {
  const platform = getPlatformConfig(opportunity.platform)
  const isHot = opportunity.heat_level === 'hot'
  const scorePulse = isHot ? 'animate-pulse' : ''

  const lastContact = opportunity.last_contact_at
    ? formatTimeAgo(opportunity.last_contact_at)
    : 'Sin contacto reciente'

  const mainSignal = opportunity.signals[0] || ''

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3, delay: index * 0.08 }}
      className={`group relative bg-white/[0.03] hover:bg-white/[0.05] border ${heatConfig.border} hover:border-white/[0.15] rounded-2xl p-5 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl ${heatConfig.glow}`}
    >
      {/* Fire glow for hot cards */}
      {isHot && (
        <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-red-500/5 to-orange-500/5 pointer-events-none" />
      )}

      {/* Header: Name + Platform + Score */}
      <div className="flex items-start justify-between mb-4 relative">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${heatConfig.gradient} p-[2px]`}>
            <div className="w-full h-full rounded-full bg-[#060812] flex items-center justify-center">
              <span className="text-sm font-bold text-white">
                {opportunity.customer_name.charAt(0)}
              </span>
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-white font-semibold text-sm">{opportunity.customer_name}</h3>
              <platform.icon className={`w-3.5 h-3.5 ${platform.color}`} />
            </div>
            <p className="text-[11px] text-white/30">{platform.label}</p>
          </div>
        </div>

        <div className={`text-right ${scorePulse}`}>
          <p className={`text-2xl font-bold ${heatConfig.text}`}>{opportunity.score}%</p>
          <p className="text-[10px] text-white/30">oportunidad</p>
        </div>
      </div>

      {/* Why they're here */}
      <div className="mb-4 relative">
        <p className="text-xs text-white/50 leading-relaxed">
          {mainSignal}
          {opportunity.purchase_history && opportunity.purchase_history.total_orders > 0 && (
            <span className="block mt-1 text-white/30">
              {opportunity.purchase_history.total_orders} compra(s) · ${opportunity.purchase_history.total_spent.toLocaleString('es-AR')}
            </span>
          )}
          {opportunity.predicted_next_purchase?.days_until !== undefined && (
            <span className="block mt-1 text-white/30">
              Próxima compra estimada: en {opportunity.predicted_next_purchase.days_until} días
            </span>
          )}
        </p>
      </div>

      {/* Seller + Last Contact */}
      <div className="flex items-center justify-between mb-4 relative">
        <div className="flex items-center gap-2">
          {opportunity.seller_avatar ? (
            <img
              src={opportunity.seller_avatar}
              alt={opportunity.seller_name}
              className="w-5 h-5 rounded-full object-cover"
            />
          ) : (
            <div className="w-5 h-5 rounded-full bg-white/10 flex items-center justify-center">
              <User className="w-3 h-3 text-white/40" />
            </div>
          )}
          <span className="text-xs text-white/40">
            {opportunity.seller_name || 'Sin vendedor'}
          </span>
        </div>
        <div className="flex items-center gap-1 text-[11px] text-white/30">
          <Clock className="w-3 h-3" />
          {lastContact}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="flex gap-2 relative">
        <button
          onClick={() => onAction(opportunity, 'send_message')}
          disabled={actingId === `${opportunity.conversation_id}-send_message`}
          className={`flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-medium rounded-xl border transition-colors ${heatConfig.bg} ${heatConfig.border} ${heatConfig.text} hover:bg-white/5 disabled:opacity-50`}
        >
          {actingId === `${opportunity.conversation_id}-send_message` ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            <Send className="w-3 h-3" />
          )}
          Enviar mensaje
        </button>
        <button
          onClick={() => onAction(opportunity, 'offer_discount')}
          disabled={actingId === `${opportunity.conversation_id}-offer_discount`}
          className="flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-medium rounded-xl border border-white/10 text-white/60 hover:bg-white/5 transition-colors disabled:opacity-50"
        >
          {actingId === `${opportunity.conversation_id}-offer_discount` ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            <Percent className="w-3 h-3" />
          )}
          Ofrecer 10%
        </button>
        <button
          onClick={onViewProfile}
          className="px-3 py-2 text-xs font-medium rounded-xl border border-white/10 text-white/60 hover:bg-white/5 transition-colors"
          title="Ver perfil"
        >
          <Eye className="w-3 h-3" />
        </button>
      </div>
    </motion.div>
  )
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatTimeAgo(isoDate: string): string {
  const date = new Date(isoDate)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 1) return 'Ahora'
  if (diffMins < 60) return `Hace ${diffMins} min`
  if (diffHours < 24) return `Hace ${diffHours} h`
  if (diffDays < 7) return `Hace ${diffDays} días`
  return date.toLocaleDateString('es-AR', { day: 'numeric', month: 'short' })
}
