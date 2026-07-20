'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { motion } from 'framer-motion'
import { useAuth } from '@/hooks/useAuth'
import {
  socialSellersApi,
  SocialSeller,
  SellerCustomer,
  SellerPipeline,
  SellerPerformance,
} from '@/lib/api/socialSellers'
import {
  Users, TrendingUp, MessageCircle, Camera as Instagram, Smartphone, Globe,
  Trophy, Flame, Zap, Loader2, ArrowLeft, Edit3, Pause, Play, Trash2,
  AlertCircle, CheckCircle2, Clock, Send, Gift, AlertTriangle,
  ChevronRight, Target, DollarSign, BarChart3, UserCheck, Mail,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/Dialog'

// ─── Platform Config ─────────────────────────────────────────────────────────

const PLATFORM_CONFIG: Record<string, {
  label: string
  icon: any
  gradient: string
  bg: string
  border: string
  text: string
}> = {
  instagram: {
    label: 'Instagram',
    icon: Instagram,
    gradient: 'from-purple-500 to-pink-500',
    bg: 'bg-purple-500/10',
    border: 'border-purple-500/20',
    text: 'text-purple-400',
  },
  tiktok: {
    label: 'TikTok',
    icon: Zap,
    gradient: 'from-cyan-400 to-red-500',
    bg: 'bg-cyan-400/10',
    border: 'border-cyan-400/20',
    text: 'text-cyan-400',
  },
  whatsapp: {
    label: 'WhatsApp',
    icon: MessageCircle,
    gradient: 'from-green-500 to-emerald-600',
    bg: 'bg-green-500/10',
    border: 'border-green-500/20',
    text: 'text-green-400',
  },
  facebook: {
    label: 'Facebook',
    icon: Globe,
    gradient: 'from-blue-500 to-blue-700',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/20',
    text: 'text-blue-400',
  },
  twitter: {
    label: 'X / Twitter',
    icon: Smartphone,
    gradient: 'from-gray-800 to-black',
    bg: 'bg-gray-500/10',
    border: 'border-gray-500/20',
    text: 'text-gray-400',
  },
  threads: {
    label: 'Threads',
    icon: MessageCircle,
    gradient: 'from-gray-700 to-gray-900',
    bg: 'bg-gray-500/10',
    border: 'border-gray-500/20',
    text: 'text-gray-400',
  },
  linkedin: {
    label: 'LinkedIn',
    icon: Globe,
    gradient: 'from-blue-700 to-blue-900',
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

const PIPELINE_STAGES = [
  { id: 'lead', label: 'Leads', emoji: '👋' },
  { id: 'nurturing', label: 'Nutrición', emoji: '🌱' },
  { id: 'proposal', label: 'Propuesta', emoji: '📦' },
  { id: 'closed', label: 'Cerrado', emoji: '🤝' },
  { id: 'loyal', label: 'Cliente Fiel', emoji: '💎' },
]

const STAGE_COLORS: Record<string, string> = {
  lead: 'bg-blue-500',
  nurturing: 'bg-teal-500',
  proposal: 'bg-amber-500',
  closed: 'bg-emerald-500',
  loyal: 'bg-purple-500',
}

// ─── Mock Data Helpers ───────────────────────────────────────────────────────

function generateMockActivity(seller: SocialSeller): any[] {
  return [
    { id: '1', time: 'Hace 2h', action: `envió mensaje a`, target: 'María', type: 'message' },
    { id: '2', time: 'Hace 5h', action: `cerró venta de`, target: '$150 con Juan', type: 'sale' },
    { id: '3', time: 'Hace 8h', action: `recibió lead de`, target: 'Instagram', type: 'lead' },
    { id: '4', time: 'Ayer', action: `envió propuesta a`, target: 'Carlos', type: 'proposal' },
    { id: '5', time: 'Ayer', action: `cerró venta de`, target: '$320 con Ana', type: 'sale' },
  ]
}

function generateMockSuggestions(customers: SellerCustomer[]): any[] {
  const top = customers.slice(0, 3)
  return top.map((c, i) => ({
    id: i,
    customer: c.customer_name,
    action: i === 0 ? 'Enviar oferta de cumpleaños' : i === 1 ? 'Seguir up (no responde hace 3 días)' : 'Ofrecer upsell premium',
    icon: i === 0 ? Gift : i === 1 ? AlertTriangle : TrendingUp,
    color: i === 0 ? 'text-purple-400' : i === 1 ? 'text-amber-400' : 'text-emerald-400',
    bg: i === 0 ? 'bg-purple-500/10' : i === 1 ? 'bg-amber-500/10' : 'bg-emerald-500/10',
    border: i === 0 ? 'border-purple-500/20' : i === 1 ? 'border-amber-500/20' : 'border-emerald-500/20',
  }))
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function SellerDetailPage() {
  const router = useRouter()
  const params = useParams()
  const sellerId = params?.seller_id as string

  const [seller, setSeller] = useState<SocialSeller | null>(null)
  const [customers, setCustomers] = useState<SellerCustomer[]>([])
  const [pipeline, setPipeline] = useState<SellerPipeline[]>([])
  const [performance, setPerformance] = useState<SellerPerformance[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [updating, setUpdating] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [editForm, setEditForm] = useState({ name: '', greeting_message: '', closing_message: '' })

  const loadData = useCallback(async () => {
    if (!sellerId) return
    setLoading(true)
    setError(null)
    try {
      const [sellerData, customersData, pipelineData, perfData] = await Promise.all([
        socialSellersApi.getSeller(sellerId).catch(() => null),
        socialSellersApi.getSellerCustomers(sellerId).catch(() => []),
        socialSellersApi.getSellerPipeline(sellerId).catch(() => []),
        socialSellersApi.getSellerPerformance(sellerId, '7d').catch(() => []),
      ])
      setSeller(sellerData)
      setCustomers(customersData)
      setPipeline(pipelineData)
      setPerformance(perfData)
      if (sellerData) {
        setEditForm({
          name: sellerData.name,
          greeting_message: sellerData.greeting_message || '',
          closing_message: sellerData.closing_message || '',
        })
      }
    } catch (e: any) {
      setError(e?.message || 'Error cargando vendedor')
    } finally {
      setLoading(false)
    }
  }, [sellerId])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleToggleStatus = async () => {
    if (!seller) return
    setUpdating(true)
    try {
      const newStatus = seller.status === 'active' ? 'paused' : 'active'
      await socialSellersApi.updateSeller(seller.id, { status: newStatus })
      await loadData()
    } catch (e: any) {
      setError(e?.message || 'Error actualizando estado')
    } finally {
      setUpdating(false)
    }
  }

  const handleDelete = async () => {
    if (!seller) return
    if (!confirm('¿Estás seguro de eliminar este vendedor?')) return
    setUpdating(true)
    try {
      await socialSellersApi.deleteSeller(seller.id)
      router.push('/dashboard/equipo')
    } catch (e: any) {
      setError(e?.message || 'Error eliminando vendedor')
      setUpdating(false)
    }
  }

  const handleUpdate = async () => {
    if (!seller) return
    setUpdating(true)
    try {
      await socialSellersApi.updateSeller(seller.id, {
        name: editForm.name,
        greeting_message: editForm.greeting_message || undefined,
        closing_message: editForm.closing_message || undefined,
      })
      setEditOpen(false)
      await loadData()
    } catch (e: any) {
      setError(e?.message || 'Error actualizando vendedor')
    } finally {
      setUpdating(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <div className="text-center space-y-3">
          <Loader2 className="w-10 h-10 text-brand-orange animate-spin mx-auto" />
          <p className="text-white/40 text-sm">Cargando vendedor...</p>
        </div>
      </div>
    )
  }

  if (!seller) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <div className="text-center space-y-3">
          <AlertCircle className="w-10 h-10 text-red-400 mx-auto" />
          <p className="text-white/40 text-sm">Vendedor no encontrado</p>
          <Button onClick={() => router.push('/dashboard/equipo')}>
            Volver al equipo
          </Button>
        </div>
      </div>
    )
  }

  const platform = getPlatformConfig(seller.platform)
  const status = STATUS_CONFIG[seller.status] || STATUS_CONFIG.training
  const revenue = seller.stats?.revenue || 0
  const deals = seller.stats?.total_sales || 0
  const conversion = seller.stats?.conversion_rate || 0
  const loyalCustomers = seller.stats?.loyal_customers || 0

  const activity = generateMockActivity(seller)
  const suggestions = generateMockSuggestions(customers)

  return (
    <div className="min-h-screen bg-[#060812]">
      <div className="max-w-7xl mx-auto p-6 space-y-8">

        {/* ── Back + Header ────────────────────────────────────── */}
        <div className="space-y-6">
          <button
            onClick={() => router.push('/dashboard/equipo')}
            className="flex items-center gap-1 text-white/40 hover:text-white text-sm transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Volver al equipo
          </button>

          <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6">
            {/* Avatar + Info */}
            <div className="flex items-start gap-5">
              <div className="relative">
                <div className={`w-20 h-20 rounded-full bg-gradient-to-br ${platform.gradient} p-[2px]`}>
                  <div className="w-full h-full rounded-full bg-[#060812] flex items-center justify-center overflow-hidden">
                    {seller.avatar_url ? (
                      <img src={seller.avatar_url} alt={seller.name} className="w-full h-full object-cover" />
                    ) : (
                      <span className="text-3xl font-bold text-white">{seller.name.charAt(0)}</span>
                    )}
                  </div>
                </div>
                <div className={`absolute -bottom-1 -right-1 w-7 h-7 rounded-full bg-gradient-to-br ${platform.gradient} flex items-center justify-center border-2 border-[#060812]`}>
                  <platform.icon className="w-3.5 h-3.5 text-white" />
                </div>
              </div>

              <div>
                <div className="flex items-center gap-3 mb-1">
                  <h1 className="text-2xl font-bold text-white">{seller.name}</h1>
                  <span className={`text-xs px-2.5 py-0.5 rounded-full border ${platform.bg} ${platform.border} ${platform.text}`}>
                    {platform.label}
                  </span>
                  <span className="flex items-center gap-1.5 text-xs">
                    <span className={`w-2 h-2 rounded-full ${status.dot}`} />
                    <span className={status.text}>{status.label}</span>
                  </span>
                </div>
                <p className="text-white/40 text-sm max-w-xl">
                  {seller.name} es tu vendedora de {platform.label}. Es {seller.voice_config?.tone || 'visual'}, usa {seller.voice_config?.emojis?.join('') || 'muchos emojis'}, y cierra ventas en el primer DM {conversion || 40}% de las veces.
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                leftIcon={<Edit3 className="w-4 h-4" />}
                onClick={() => setEditOpen(true)}
              >
                Editar
              </Button>
              <Button
                variant="outline"
                size="sm"
                leftIcon={seller.status === 'active' ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                onClick={handleToggleStatus}
                isLoading={updating}
              >
                {seller.status === 'active' ? 'Pausar' : 'Reanudar'}
              </Button>
              <Button
                variant="destructive"
                size="sm"
                leftIcon={<Trash2 className="w-4 h-4" />}
                onClick={handleDelete}
              >
                Eliminar
              </Button>
            </div>
          </div>
        </div>

        {/* ── Error ────────────────────────────────────────────── */}
        {error && (
          <div className="flex items-center gap-2 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        {/* ── Stats Row ────────────────────────────────────────── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Ventas este mes', value: deals, icon: Trophy, color: 'text-amber-400', bg: 'bg-amber-500/8', border: 'border-amber-500/15' },
            { label: 'Revenue', value: `$${revenue.toLocaleString('es-AR')}`, icon: DollarSign, color: 'text-emerald-400', bg: 'bg-emerald-500/8', border: 'border-emerald-500/15' },
            { label: 'Tasa de conversión', value: `${conversion}%`, icon: BarChart3, color: 'text-blue-400', bg: 'bg-blue-500/8', border: 'border-blue-500/15' },
            { label: 'Clientes activos', value: loyalCustomers, icon: UserCheck, color: 'text-purple-400', bg: 'bg-purple-500/8', border: 'border-purple-500/15' },
          ].map(stat => (
            <div key={stat.label} className={`${stat.bg} ${stat.border} border rounded-2xl p-5`}>
              <div className="flex items-center gap-2 mb-3">
                <stat.icon className={`w-4 h-4 ${stat.color}`} />
                <span className="text-xs text-white/40">{stat.label}</span>
              </div>
              <p className="text-2xl font-bold text-white">{stat.value}</p>
            </div>
          ))}
        </div>

        {/* ── Pipeline + Customers + Activity ──────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Pipeline */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl p-5">
              <h2 className="text-sm font-semibold text-white mb-5">Pipeline de Ventas</h2>
              <div className="flex items-center justify-between gap-2">
                {PIPELINE_STAGES.map((stage, idx) => {
                  const pipeData = pipeline.find(p => p.stage.toLowerCase() === stage.id) || { count: 0, revenue: 0 }
                  const color = STAGE_COLORS[stage.id] || 'bg-gray-500'
                  const isLast = idx === PIPELINE_STAGES.length - 1

                  return (
                    <div key={stage.id} className="flex-1 flex items-center">
                      <div className="flex-1 text-center">
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          transition={{ delay: idx * 0.1 + 0.3 }}
                          className={`w-10 h-10 rounded-full ${color} bg-opacity-20 border border-${color.replace('bg-', '')}/30 flex items-center justify-center mx-auto mb-2`}
                          style={{ borderColor: 'rgba(255,255,255,0.1)' }}
                        >
                          <span className="text-lg">{stage.emoji}</span>
                        </motion.div>
                        <p className="text-[10px] text-white/40 mb-1">{stage.label}</p>
                        <p className="text-sm font-bold text-white">{pipeData.count}</p>
                        {pipeData.revenue > 0 && (
                          <p className="text-[10px] text-emerald-400">${pipeData.revenue.toLocaleString('es-AR')}</p>
                        )}
                      </div>
                      {!isLast && (
                        <div className="w-6 h-px bg-white/10 mx-1" />
                      )}
                    </div>
                  )
                })}
              </div>
              {/* Animated progress bar */}
              <div className="mt-6 h-2 bg-white/5 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(100, (deals / Math.max(deals + 5, 10)) * 100)}%` }}
                  transition={{ duration: 1.5, ease: 'easeOut' }}
                  className={`h-full rounded-full bg-gradient-to-r ${platform.gradient}`}
                />
              </div>
            </div>

            {/* Customer List */}
            <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-semibold text-white">Clientes Asignados</h2>
                <span className="text-xs text-white/30">{customers.length} total</span>
              </div>
              {customers.length === 0 ? (
                <div className="text-center py-10 text-white/20 text-sm">
                  <Users className="w-8 h-8 mx-auto mb-2 opacity-30" />
                  Sin clientes asignados aún
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-[10px] text-white/30 uppercase tracking-wider">
                        <th className="pb-3 pl-2">Nombre</th>
                        <th className="pb-3">Etapa</th>
                        <th className="pb-3 text-center">Interacciones</th>
                        <th className="pb-3 text-center">Ventas</th>
                        <th className="pb-3 text-right">Revenue</th>
                        <th className="pb-3 text-right">Último contacto</th>
                        <th className="pb-3 text-right pr-2">Próxima acción</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/[0.04]">
                      {customers.map((c, i) => {
                        const stageColor = STAGE_COLORS[c.relationship_stage?.toLowerCase()] || 'bg-gray-500'
                        const platforms = c.unified_identity_map ? Object.keys(c.unified_identity_map) : [seller?.platform]
                        const platformLabels = platforms.map(p => {
                          const cfg = getPlatformConfig(p)
                          return cfg.label.slice(0, 2).toUpperCase()
                        })
                        const displayName = c.unified_display_name || c.customer_name
                        const nameWithPlatforms = platformLabels.length > 1
                          ? `${displayName} (${platformLabels.join(' + ')})`
                          : displayName
                        const totalLTV = (c.unified_total_lifetime_value || 0) > (c.total_revenue || 0)
                          ? c.unified_total_lifetime_value
                          : c.total_revenue
                        return (
                          <motion.tr
                            key={c.id}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.05 }}
                            className="hover:bg-white/[0.02] transition-colors"
                          >
                            <td className="py-3 pl-2">
                              <div className="flex items-center gap-2">
                                <div className="w-7 h-7 rounded-full bg-white/5 flex items-center justify-center text-[10px] text-white/60">
                                  {c.customer_avatar ? (
                                    <img src={c.customer_avatar} alt="" className="w-full h-full rounded-full object-cover" />
                                  ) : (
                                    displayName.charAt(0)
                                  )}
                                </div>
                                <div className="flex flex-col">
                                  <span className="text-white text-xs">{nameWithPlatforms}</span>
                                  <div className="flex items-center gap-1 mt-0.5">
                                    {platforms.map(p => {
                                      const cfg = getPlatformConfig(p)
                                      const Icon = cfg.icon
                                      return (
                                        <span key={p} className={`inline-flex items-center justify-center w-3.5 h-3.5 rounded-full ${cfg.bg}`} title={cfg.label}>
                                          <Icon className={`w-2 h-2 ${cfg.text}`} />
                                        </span>
                                      )
                                    })}
                                  </div>
                                </div>
                              </div>
                            </td>
                            <td>
                              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] ${stageColor.replace('bg-', 'bg-')}/15 ${stageColor.replace('bg-', 'text-')}/80 border ${stageColor.replace('bg-', 'border-')}/20`}>
                                <span className={`w-1.5 h-1.5 rounded-full ${stageColor}`} />
                                {c.relationship_stage || 'Lead'}
                              </span>
                            </td>
                            <td className="text-center text-white/50 text-xs">{c.total_interactions}</td>
                            <td className="text-center text-white/50 text-xs">{c.deals_closed}</td>
                            <td className="text-right text-emerald-400 text-xs font-medium">${Number(totalLTV).toLocaleString('es-AR')}</td>
                            <td className="text-right text-white/30 text-xs">{c.last_contact_at ? new Date(c.last_contact_at).toLocaleDateString('es-AR') : '—'}</td>
                            <td className="text-right text-white/50 text-xs pr-2">{c.next_best_action || '—'}</td>
                          </motion.tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar: Activity + Suggestions */}
          <div className="space-y-6">
            {/* Recent Activity */}
            <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl p-5">
              <h2 className="text-sm font-semibold text-white mb-4">Actividad Reciente</h2>
              <div className="space-y-4">
                {activity.map((item, i) => (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="flex items-start gap-3"
                  >
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${
                      item.type === 'sale' ? 'bg-emerald-500/15' : item.type === 'message' ? 'bg-blue-500/15' : 'bg-purple-500/15'
                    }`}>
                      {item.type === 'sale' ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> :
                       item.type === 'message' ? <Send className="w-3.5 h-3.5 text-blue-400" /> :
                       <Target className="w-3.5 h-3.5 text-purple-400" />}
                    </div>
                    <div>
                      <p className="text-xs text-white/70">
                        <span className="text-white/40">{item.time}:</span> {seller.name} {item.action} <span className="text-white font-medium">{item.target}</span>
                      </p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* AI Suggested Actions */}
            <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <Zap className="w-4 h-4 text-brand-orange" />
                <h2 className="text-sm font-semibold text-white">Acciones sugeridas por IA</h2>
              </div>
              <div className="space-y-3">
                {suggestions.length === 0 ? (
                  <p className="text-white/20 text-xs text-center py-4">Sin sugerencias por ahora</p>
                ) : suggestions.map((s, i) => (
                  <motion.div
                    key={s.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1 + 0.3 }}
                    className={`p-3 rounded-xl border ${s.bg} ${s.border} cursor-pointer hover:bg-white/5 transition-colors`}
                  >
                    <div className="flex items-start gap-2">
                      <s.icon className={`w-4 h-4 ${s.color} shrink-0 mt-0.5`} />
                      <div>
                        <p className="text-xs text-white/80 font-medium">{s.action}</p>
                        <p className="text-[10px] text-white/40">para {s.customer}</p>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ── Edit Modal ───────────────────────────────────────── */}
        <Dialog open={editOpen} onOpenChange={setEditOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Editar vendedor</DialogTitle>
              <DialogDescription>
                Actualizá los datos de {seller.name}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <label className="text-xs text-white/40 mb-1.5 block">Nombre</label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={e => setEditForm(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                />
              </div>
              <div>
                <label className="text-xs text-white/40 mb-1.5 block">Mensaje de bienvenida</label>
                <textarea
                  value={editForm.greeting_message}
                  onChange={e => setEditForm(prev => ({ ...prev, greeting_message: e.target.value }))}
                  rows={3}
                  className="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                />
              </div>
              <div>
                <label className="text-xs text-white/40 mb-1.5 block">Mensaje de cierre</label>
                <textarea
                  value={editForm.closing_message}
                  onChange={e => setEditForm(prev => ({ ...prev, closing_message: e.target.value }))}
                  rows={3}
                  className="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <Button variant="ghost" onClick={() => setEditOpen(false)} className="flex-1">
                  Cancelar
                </Button>
                <Button onClick={handleUpdate} isLoading={updating} className="flex-1">
                  Guardar cambios
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}
