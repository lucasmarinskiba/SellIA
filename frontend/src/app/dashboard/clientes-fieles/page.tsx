'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { businessApi } from '@/lib/business'
import {
  socialSellersApi,
  WallOfFameCustomer,
  LoyaltySegmentsResponse,
} from '@/lib/api/socialSellers'
import {
  Heart, Loader2, AlertCircle, X, Gift, Crown, Star,
  RefreshCw, Trophy, Diamond, Zap, AlertTriangle,
  MessageCircle, TrendingUp, User, Camera as Instagram, ShoppingBag,
} from 'lucide-react'

const TIER_DATA = [
  {
    key: 'champions',
    label: 'Campeones',
    icon: Trophy,
    color: 'text-yellow-400',
    bg: 'bg-yellow-400/10',
    border: 'border-yellow-400/20',
    description: 'El 10% de tus clientes que generan el 50% de tu revenue',
    criteria: '5+ compras',
  },
  {
    key: 'ambassador',
    label: 'Embajadores',
    icon: Diamond,
    color: 'text-cyan-400',
    bg: 'bg-cyan-400/10',
    border: 'border-cyan-400/20',
    description: 'Tu mejor marketing',
    criteria: 'Refirieron a alguien',
  },
  {
    key: 'fan_1',
    label: 'Fans #1',
    icon: Star,
    color: 'text-pink-400',
    bg: 'bg-pink-400/10',
    border: 'border-pink-400/20',
    description: 'Incondicionales',
    criteria: 'Mayor LTV',
  },
  {
    key: 'regular',
    label: 'Regulares',
    icon: RefreshCw,
    color: 'text-emerald-400',
    bg: 'bg-emerald-400/10',
    border: 'border-emerald-400/20',
    description: 'Tu base sólida',
    criteria: 'Compran mensualmente',
  },
  {
    key: 'at_risk',
    label: 'En Riesgo',
    icon: AlertTriangle,
    color: 'text-red-400',
    bg: 'bg-red-400/10',
    border: 'border-red-400/20',
    description: '¡A reconquistar!',
    criteria: 'No compran hace 60+ días',
  },
]

const BADGE_COLORS: Record<string, string> = {
  champion: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  ambassador: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  fan_1: 'bg-pink-500/20 text-pink-300 border-pink-500/30',
  comeback_kid: 'bg-violet-500/20 text-violet-300 border-violet-500/30',
  big_spender: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  regular: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map(n => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

function formatCurrency(val: number): string {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    maximumFractionDigits: 0,
  }).format(val)
}

function formatDate(iso?: string): string {
  if (!iso) return '-'
  return new Date(iso).toLocaleDateString('es-AR')
}

export default function ClientesFielesPage() {
  const [businesses, setBusinesses] = useState<any[]>([])
  const [selectedBusinessId, setSelectedBusinessId] = useState('')
  const [customers, setCustomers] = useState<WallOfFameCustomer[]>([])
  const [segments, setSegments] = useState<LoyaltySegmentsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({})

  useEffect(() => {
    businessApi.list().then(data => {
      setBusinesses(data)
      if (data.length > 0) setSelectedBusinessId(data[0].id)
    }).catch(() => setError('No se pudieron cargar los negocios'))
  }, [])

  useEffect(() => {
    if (!selectedBusinessId) return
    loadAll()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBusinessId])

  const loadAll = async () => {
    setLoading(true)
    setError(null)
    try {
      const [wall, segs] = await Promise.all([
        socialSellersApi.getWallOfFame(selectedBusinessId, 50),
        socialSellersApi.getLoyaltySegments(selectedBusinessId).catch(() => null),
      ])
      setCustomers(wall)
      setSegments(segs)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al cargar clientes fieles')
    } finally {
      setLoading(false)
    }
  }

  const handleAction = async (customerId: string, actionType: 'send_gift' | 'offer_vip' | 'request_testimonial') => {
    const key = `${customerId}-${actionType}`
    setActionLoading(prev => ({ ...prev, [key]: true }))
    try {
      await socialSellersApi.createLoyaltyAction(customerId, {
        action_type: actionType,
        business_id: selectedBusinessId,
      })
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al ejecutar acción')
    } finally {
      setActionLoading(prev => ({ ...prev, [key]: false }))
    }
  }

  const avgLtv = customers.length
    ? customers.reduce((s, c) => s + c.ltv, 0) / customers.length
    : 0

  const retentionRate = segments && segments.total_customers > 0
    ? Math.round(
        ((segments.segments.champions?.count || 0) +
          (segments.segments.loyal?.count || 0) +
          (segments.segments.potential?.count || 0)) /
          segments.total_customers * 100
      )
    : 0

  return (
    <div className="space-y-8 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-2">
            <Heart className="w-8 h-8 text-red-400" />
            Clientes Fieles
          </h1>
          <p className="text-sm text-white/40">Tu ejército de fans</p>
        </div>
        <div className="flex items-center gap-3">
          {businesses.length > 0 && (
            <select
              value={selectedBusinessId}
              onChange={e => setSelectedBusinessId(e.target.value)}
              className="px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
            >
              {businesses.map(b => (
                <option key={b.id} value={b.id} className="bg-[#0A0E1A]">{b.name}</option>
              ))}
            </select>
          )}
          <button
            onClick={loadAll}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-2 rounded-xl bg-brand-orange/10 border border-brand-orange/20 text-sm text-brand-orange hover:bg-brand-orange/20 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Actualizar
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="glass-card p-4 text-center">
          <p className="text-2xl font-bold text-white">{customers.length}</p>
          <p className="text-xs text-white/30 mt-1">Total fans</p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-2xl font-bold text-white">{formatCurrency(avgLtv)}</p>
          <p className="text-xs text-white/30 mt-1">LTV promedio</p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-2xl font-bold text-white">{retentionRate}%</p>
          <p className="text-xs text-white/30 mt-1">Tasa de retención</p>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <AlertCircle className="w-4 h-4" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
        </div>
      ) : (
        <>
          {/* VIP Tiers */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-white/80 flex items-center gap-2">
              <Crown className="w-5 h-5 text-brand-orange" />
              VIP Tiers
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
              {TIER_DATA.map((tier, idx) => {
                const Icon = tier.icon
                const count = tier.key === 'champions'
                  ? (segments?.segments.champions?.count || 0)
                  : tier.key === 'regular'
                  ? (segments?.segments.loyal?.count || 0)
                  : tier.key === 'at_risk'
                  ? (segments?.segments.at_risk?.count || 0)
                  : undefined
                return (
                  <motion.div
                    key={tier.key}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className={`glass-card p-4 border ${tier.border}`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <div className={`p-1.5 rounded-lg ${tier.bg}`}>
                        <Icon className={`w-4 h-4 ${tier.color}`} />
                      </div>
                      <h3 className="text-sm font-semibold text-white">{tier.label}</h3>
                    </div>
                    <p className="text-xs text-white/30 mb-1">{tier.description}</p>
                    <p className="text-[10px] text-white/20">{tier.criteria}</p>
                    {count !== undefined && (
                      <p className={`text-lg font-bold ${tier.color} mt-2`}>{count}</p>
                    )}
                  </motion.div>
                )
              })}
            </div>
          </div>

          {/* Wall of Fame Grid */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-white/80 flex items-center gap-2">
              <Star className="w-5 h-5 text-yellow-400" />
              Wall of Fame
              <span className="text-xs text-white/30 font-normal ml-2">({customers.length} clientes)</span>
            </h2>

            {customers.length === 0 ? (
              <div className="glass-card p-10 text-center">
                <Heart className="w-12 h-12 text-white/10 mx-auto mb-4" />
                <p className="text-white/30 text-sm">
                  Todavía no tenés clientes fieles. ¡Zoe y el equipo están trabajando en eso!
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {customers.map((customer, idx) => (
                  <motion.div
                    key={customer.customer_id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.04 }}
                    className="glass-card p-5"
                  >
                    <div className="flex items-start gap-3 mb-3">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-brand-orange/20 to-brand-violet/20 flex items-center justify-center text-sm font-bold text-white border border-white/10 shrink-0">
                        {getInitials(customer.name)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-semibold text-white truncate">{customer.name}</h3>
                        <p className="text-xs text-white/30">
                          LTV: <span className="text-white/60 font-medium">{formatCurrency(customer.ltv)}</span>
                        </p>
                      </div>
                      <div className="shrink-0">
                        {customer.platform === 'instagram' && <Instagram className="w-4 h-4 text-pink-400" />}
                        {customer.platform === 'whatsapp' && <MessageCircle className="w-4 h-4 text-green-400" />}
                        {customer.platform === 'webchat' && <ShoppingBag className="w-4 h-4 text-blue-400" />}
                        {!['instagram', 'whatsapp', 'webchat'].includes(customer.platform) && (
                          <User className="w-4 h-4 text-white/20" />
                        )}
                      </div>
                    </div>

                    {/* Badges */}
                    {customer.badges.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mb-3">
                        {customer.badges.map((badge, bidx) => (
                          <span
                            key={bidx}
                            className={`text-[10px] px-2 py-0.5 rounded-full border ${BADGE_COLORS[badge.badge_type] || 'bg-white/5 text-white/40 border-white/10'}`}
                          >
                            {badge.name}
                          </span>
                        ))}
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                      <div className="p-2 rounded-lg bg-white/5">
                        <p className="text-white/20">Compras</p>
                        <p className="text-white font-medium">{customer.total_purchases}</p>
                      </div>
                      <div className="p-2 rounded-lg bg-white/5">
                        <p className="text-white/20">Última</p>
                        <p className="text-white font-medium">{formatDate(customer.last_purchase_at)}</p>
                      </div>
                    </div>

                    {/* Quick Actions */}
                    <div className="flex gap-2">
                      <ActionButton
                        icon={<Gift className="w-3 h-3" />}
                        label="Regalo"
                        onClick={() => handleAction(customer.customer_id, 'send_gift')}
                        loading={actionLoading[`${customer.customer_id}-send_gift`]}
                      />
                      <ActionButton
                        icon={<Crown className="w-3 h-3" />}
                        label="VIP"
                        onClick={() => handleAction(customer.customer_id, 'offer_vip')}
                        loading={actionLoading[`${customer.customer_id}-offer_vip`]}
                      />
                      <ActionButton
                        icon={<MessageCircle className="w-3 h-3" />}
                        label="Testimonio"
                        onClick={() => handleAction(customer.customer_id, 'request_testimonial')}
                        loading={actionLoading[`${customer.customer_id}-request_testimonial`]}
                      />
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

function ActionButton({
  icon,
  label,
  onClick,
  loading,
}: {
  icon: React.ReactNode
  label: string
  onClick: () => void
  loading?: boolean
}) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className="flex items-center gap-1 px-2 py-1.5 rounded-lg bg-white/5 border border-white/10 text-[10px] text-white/50 hover:bg-white/10 hover:text-white transition-colors disabled:opacity-50"
    >
      {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : icon}
      {label}
    </button>
  )
}
