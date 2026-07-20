'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { gamificationApi, GamificationProfile } from '@/lib/gamification'
import { autopilotApi } from '@/lib/autopilot'
import { crmApi } from '@/lib/crm'
import { businessApi } from '@/lib/business'
import {
  Sparkles, Activity, Target, Handshake, Package,
  Zap, TrendingUp, MessageSquare, Bot, ChevronRight,
  Shield, AlertTriangle, CheckCircle2, Clock, Users,
  BarChart3, Flame, Trophy, ArrowRight, Plus, Play,
  TreePine, Flower2, Bird, Home, Volume2, VolumeX, X,
  Coffee, Share2, Award, Moon, Star, RefreshCw, Loader2,
  Banknote
} from 'lucide-react'

// ─── Types ────────────────────────────────────────────────────────────────────

interface KpiCard {
  label: string
  value: string | number
  sub?: string
  color: string
  icon: any
  trend?: 'up' | 'down' | 'neutral'
  href: string
}

interface FeatureModule {
  id: string
  icon: any
  title: string
  description: string
  badge?: string
  color: string
  href: string
  actions: { label: string; href: string }[]
}

// ─── Feature Modules Config ───────────────────────────────────────────────────

const FEATURE_MODULES: FeatureModule[] = [
  {
    id: 'pipeline',
    icon: Target,
    title: 'Pipeline de Ventas',
    description: '9 etapas especializadas con metodologías de Gary Vee, Hormozi, Belfort y más.',
    badge: '9 etapas',
    color: 'emerald',
    href: '/dashboard/pipeline',
    actions: [
      { label: 'Prospección', href: '/dashboard/pipeline?stage=prospecting' },
      { label: 'Cierre', href: '/dashboard/pipeline?stage=closing' },
      { label: 'Retención', href: '/dashboard/pipeline?stage=retention' },
    ],
  },
  {
    id: 'negotiate',
    icon: Handshake,
    title: 'Mesa de Negociación',
    description: 'Activá estrategias de Chris Voss, Roger Fisher, Herb Cohen y los mejores negociadores del mundo.',
    badge: '5 expertos',
    color: 'blue',
    href: '/dashboard/agentes?section=negotiate',
    actions: [
      { label: 'Chris Voss — FBI', href: '/dashboard/agentes?section=negotiate&expert=chris-voss' },
      { label: 'Roger Fisher — Harvard', href: '/dashboard/agentes?section=negotiate&expert=roger-fisher' },
      { label: 'Herb Cohen', href: '/dashboard/agentes?section=negotiate&expert=herb-cohen' },
    ],
  },
  {
    id: 'offer',
    icon: Package,
    title: 'Offer Builder',
    description: 'Construí tu Grand Slam Offer con la Value Equation de Alex Hormozi. Precio irresistible garantizado.',
    badge: 'Hormozi',
    color: 'amber',
    href: '/dashboard/agentes?section=offer',
    actions: [
      { label: 'Nueva oferta', href: '/dashboard/agentes?section=offer' },
      { label: 'Value Stack', href: '/dashboard/agentes?section=offer&tab=stack' },
      { label: 'Garantías', href: '/dashboard/agentes?section=offer&tab=guarantee' },
    ],
  },
  {
    id: 'autonomo',
    icon: Activity,
    title: 'Sistema Autónomo',
    description: '4 pilares de IA autónoma: autoconfigura, autorepara, autooptimiza y autoprotege tu negocio 24/7.',
    badge: '24/7',
    color: 'purple',
    href: '/dashboard/autonomo',
    actions: [
      { label: 'Ver salud', href: '/dashboard/autonomo' },
      { label: 'Autopilot', href: '/dashboard/autopilot' },
      { label: 'Alertas', href: '/dashboard/alertas' },
    ],
  },
]

const COLOR_CLASSES: Record<string, { bg: string; border: string; text: string; badge: string; btn: string }> = {
  emerald: {
    bg: 'bg-emerald-500/5 hover:bg-emerald-500/10',
    border: 'border-emerald-500/20 hover:border-emerald-500/40',
    text: 'text-emerald-400',
    badge: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
    btn: 'bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400',
  },
  blue: {
    bg: 'bg-blue-500/5 hover:bg-blue-500/10',
    border: 'border-blue-500/20 hover:border-blue-500/40',
    text: 'text-blue-400',
    badge: 'bg-blue-500/15 text-blue-400 border-blue-500/20',
    btn: 'bg-blue-500/20 hover:bg-blue-500/30 text-blue-400',
  },
  amber: {
    bg: 'bg-amber-500/5 hover:bg-amber-500/10',
    border: 'border-amber-500/20 hover:border-amber-500/40',
    text: 'text-amber-400',
    badge: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
    btn: 'bg-amber-500/20 hover:bg-amber-500/30 text-amber-400',
  },
  purple: {
    bg: 'bg-purple-500/5 hover:bg-purple-500/10',
    border: 'border-purple-500/20 hover:border-purple-500/40',
    text: 'text-purple-400',
    badge: 'bg-purple-500/15 text-purple-400 border-purple-500/20',
    btn: 'bg-purple-500/20 hover:bg-purple-500/30 text-purple-400',
  },
}

// ─── Main Page ─────────────────────────────────────────────────────────────────

export default function HomePage() {
  const { user } = useAuth()
  const router = useRouter()

  const [profile, setProfile] = useState<GamificationProfile | null>(null)
  const [kpis, setKpis] = useState<{ deals: number; revenue: number; conversations: number; health: number } | null>(null)
  const [dailyReport, setDailyReport] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [gardenOpen, setGardenOpen] = useState(false)
  const [companionMessage, setCompanionMessage] = useState("¡Hola! Soy SellIA. Tu negocio está activo.")
  const [garden, setGarden] = useState<any>(null)

  const loadData = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)
    else setRefreshing(true)
    try {
      const [prof, companion, gardenData, businesses] = await Promise.all([
        gamificationApi.getProfile().catch(() => null),
        gamificationApi.getCompanionMessage('welcome').catch(() => ({ message: "¡Hola! Tu negocio autónomo está activo 24/7." })),
        gamificationApi.getGarden().catch(() => null),
        businessApi.list().catch(() => []),
      ])

      setProfile(prof)
      setGarden(gardenData)
      setCompanionMessage(companion?.message || "¡Hola! Tu negocio está activo.")

      // Load business-specific data if a business exists
      const firstBusiness = businesses?.[0]
      if (firstBusiness?.id) {
        const [autopilotData, dealsData] = await Promise.all([
          autopilotApi.getDailyReports(firstBusiness.id, 1).catch(() => null),
          crmApi.getDeals(firstBusiness.id, {}).catch(() => null),
        ])

        const report = Array.isArray(autopilotData) ? autopilotData[0] : autopilotData
        setDailyReport(report)

        const items: any[] = dealsData || []
        const activeDeals = items.filter((d: any) => d.is_active && d.stage !== 'won' && d.stage !== 'lost')
        const totalRevenue = items
          .filter((d: any) => d.stage === 'won')
          .reduce((sum: number, d: any) => sum + (d.value || 0), 0)

        setKpis({
          deals: activeDeals.length,
          revenue: totalRevenue,
          conversations: report?.leads_contacted || 0,
          health: 85,
        })
      } else {
        setKpis({ deals: 0, revenue: 0, conversations: 0, health: 85 })
      }
    } catch (e) {
      console.error(e)
      setKpis({ deals: 0, revenue: 0, conversations: 0, health: 85 })
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <div className="text-center space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-brand-orange/20 to-purple-500/20 border border-brand-orange/30 flex items-center justify-center mx-auto">
            <Sparkles className="w-6 h-6 text-brand-orange animate-pulse" />
          </div>
          <p className="text-white/40 text-sm">Cargando tu centro de comando...</p>
        </div>
      </div>
    )
  }

  const healthScore = kpis?.health ?? 0
  const healthLabel = healthScore >= 80 ? 'Óptimo' : healthScore >= 60 ? 'Estable' : healthScore >= 40 ? 'Degradado' : 'Crítico'
  const healthColor = healthScore >= 80 ? '#10b981' : healthScore >= 60 ? '#eab308' : healthScore >= 40 ? '#f97316' : '#ef4444'

  const isNewUser = !profile || (profile.total_sales_closed === 0 && profile.total_xp < 100)

  return (
    <div className="min-h-screen bg-[#060812]">
      <div className="max-w-7xl mx-auto p-6 space-y-8">

        {/* ── Header ──────────────────────────────────────────────── */}
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-brand-orange/20 to-purple-500/20 border border-brand-orange/20 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-brand-orange" />
              </div>
              <h1 className="text-2xl font-bold text-white">
                {isNewUser ? '¡Bienvenido a SellIA!' : `Hola, ${user?.email?.split('@')[0] || 'Emprendedor'} 👋`}
              </h1>
            </div>
            <p className="text-white/40 text-sm ml-11">
              {isNewUser
                ? 'Tu negocio autónomo está listo para vender mientras dormís'
                : `Sistema autónomo activo • ${new Date().toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long' })}`}
            </p>
          </div>
          <button
            onClick={() => loadData(true)}
            disabled={refreshing}
            className="p-2.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-white/40 hover:text-white transition-all disabled:opacity-30"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* ── New User Onboarding Banner ─────────────────────────── */}
        {isNewUser && (
          <div className="relative overflow-hidden bg-gradient-to-r from-brand-orange/10 via-purple-500/10 to-blue-500/10 border border-brand-orange/20 rounded-2xl p-6">
            <div className="absolute top-0 right-0 w-64 h-64 bg-brand-orange/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
            <div className="relative">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-2xl bg-brand-orange/20 border border-brand-orange/30 flex items-center justify-center shrink-0">
                  <Play className="w-5 h-5 text-brand-orange" />
                </div>
                <div className="flex-1">
                  <h2 className="text-lg font-semibold text-white mb-1">Empezá a vender en 3 pasos</h2>
                  <p className="text-white/50 text-sm mb-4">Tu sistema autónomo está configurado y listo. Solo necesitás conectar tu negocio.</p>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {[
                      { step: '1', label: 'Conectá tu canal', desc: 'WhatsApp, Instagram o email', href: '/dashboard/canales', color: 'text-emerald-400' },
                      { step: '2', label: 'Cargá tu catálogo', desc: 'Tus productos y servicios', href: '/dashboard/catalogo', color: 'text-amber-400' },
                      { step: '3', label: 'Activá el autopilot', desc: 'El sistema vende solo', href: '/dashboard/autopilot', color: 'text-purple-400' },
                    ].map(s => (
                      <button
                        key={s.step}
                        onClick={() => router.push(s.href)}
                        className="flex items-start gap-3 p-3 bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/15 rounded-xl text-left transition-all group"
                      >
                        <span className={`text-lg font-bold ${s.color} leading-none`}>{s.step}</span>
                        <div>
                          <p className="text-white text-sm font-medium group-hover:text-white">{s.label}</p>
                          <p className="text-white/40 text-xs">{s.desc}</p>
                        </div>
                        <ArrowRight className="w-3 h-3 text-white/20 group-hover:text-white/50 ml-auto mt-1 transition-colors" />
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── KPI Row ───────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* System Health */}
          <button
            onClick={() => router.push('/dashboard/autonomo')}
            className="bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.08] hover:border-purple-500/30 rounded-2xl p-5 text-left transition-all group"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-purple-400" />
                <span className="text-xs text-white/40">Salud del Sistema</span>
              </div>
              <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: healthColor }} />
            </div>
            <div className="flex items-end gap-3">
              <div className="relative w-14 h-14">
                <svg className="w-14 h-14 -rotate-90" viewBox="0 0 36 36">
                  <circle cx="18" cy="18" r="14" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="3" />
                  <circle
                    cx="18" cy="18" r="14" fill="none"
                    stroke={healthColor}
                    strokeWidth="3"
                    strokeDasharray={`${(healthScore / 100) * 88} 88`}
                    strokeLinecap="round"
                    className="transition-all duration-1000"
                  />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-white">{healthScore}</span>
              </div>
              <div>
                <p className="text-xl font-bold text-white">{healthLabel}</p>
                <p className="text-xs text-white/30">4 pilares IA activos</p>
              </div>
            </div>
            <div className="mt-3 flex items-center gap-1 text-purple-400/60 group-hover:text-purple-400 transition-colors">
              <span className="text-xs">Ver panel autónomo</span>
              <ChevronRight className="w-3 h-3" />
            </div>
          </button>

          {/* Active Pipeline Deals */}
          <button
            onClick={() => router.push('/dashboard/pipeline')}
            className="bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.08] hover:border-emerald-500/30 rounded-2xl p-5 text-left transition-all group"
          >
            <div className="flex items-center gap-2 mb-3">
              <Target className="w-4 h-4 text-emerald-400" />
              <span className="text-xs text-white/40">Deals en Pipeline</span>
            </div>
            <p className="text-3xl font-bold text-white mb-1">{kpis?.deals ?? 0}</p>
            <p className="text-xs text-white/30 mb-3">
              {kpis?.deals === 0 ? 'Sin deals activos aún' : 'deals activos en 9 etapas'}
            </p>
            {kpis?.deals === 0 ? (
              <div className="flex items-center gap-1 text-emerald-400/50">
                <Plus className="w-3 h-3" />
                <span className="text-xs">Crear primer deal</span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-emerald-400/60 group-hover:text-emerald-400 transition-colors">
                <span className="text-xs">Ver tablero</span>
                <ChevronRight className="w-3 h-3" />
              </div>
            )}
          </button>

          {/* Revenue Won */}
          <button
            onClick={() => router.push('/dashboard/analytics')}
            className="bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.08] hover:border-amber-500/30 rounded-2xl p-5 text-left transition-all group"
          >
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-4 h-4 text-amber-400" />
              <span className="text-xs text-white/40">Revenue Cerrado</span>
            </div>
            <p className="text-3xl font-bold text-white mb-1">
              ${(kpis?.revenue ?? 0).toLocaleString('es-AR')}
            </p>
            <p className="text-xs text-white/30 mb-3">
              {kpis?.revenue === 0 ? 'Primera venta en camino' : 'total acumulado'}
            </p>
            <div className="flex items-center gap-1 text-amber-400/60 group-hover:text-amber-400 transition-colors">
              <span className="text-xs">Ver analytics</span>
              <ChevronRight className="w-3 h-3" />
            </div>
          </button>

          {/* Autopilot Actions Today */}
          <button
            onClick={() => router.push('/dashboard/autopilot')}
            className="bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.08] hover:border-blue-500/30 rounded-2xl p-5 text-left transition-all group"
          >
            <div className="flex items-center gap-2 mb-3">
              <Zap className="w-4 h-4 text-blue-400" />
              <span className="text-xs text-white/40">Acciones Autopilot Hoy</span>
            </div>
            <p className="text-3xl font-bold text-white mb-1">
              {dailyReport
                ? (dailyReport.leads_contacted || 0) + (dailyReport.deals_moved || 0) + (dailyReport.deals_closed || 0)
                : 0}
            </p>
            <p className="text-xs text-white/30 mb-3">
              {dailyReport ? `${dailyReport.leads_contacted || 0} contactados • ${dailyReport.deals_closed || 0} cerrados` : 'Autopilot en reposo'}
            </p>
            <div className="flex items-center gap-1 text-blue-400/60 group-hover:text-blue-400 transition-colors">
              <span className="text-xs">Ver log de acciones</span>
              <ChevronRight className="w-3 h-3" />
            </div>
          </button>

          {/* Finanzas Autopilot */}
          <button
            onClick={() => router.push('/dashboard/finanzas/autopilot')}
            className="bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.08] hover:border-emerald-500/30 rounded-2xl p-5 text-left transition-all group"
          >
            <div className="flex items-center gap-2 mb-3">
              <Banknote className="w-4 h-4 text-emerald-400" />
              <span className="text-xs text-white/40">Cobranza</span>
            </div>
            <p className="text-xl font-bold text-white mb-1">
              ${(kpis?.revenue ?? 0).toLocaleString('es-AR')} pendiente
            </p>
            <p className="text-xs text-white/30 mb-3">
              3 vencidas • Autopilot activo
            </p>
            <div className="flex items-center gap-1 text-emerald-400/60 group-hover:text-emerald-400 transition-colors">
              <span className="text-xs">Ver finanzas</span>
              <ChevronRight className="w-3 h-3" />
            </div>
          </button>
        </div>

        {/* ── Seller del Día ──────────────────────────────────────── */}
        <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Trophy className="w-4 h-4 text-amber-400" />
              <h2 className="text-sm font-semibold text-white">Seller del día</h2>
            </div>
            <button
              onClick={() => router.push('/dashboard/equipo')}
              className="text-xs text-white/30 hover:text-white/60 transition-colors flex items-center gap-1"
            >
              Ver equipo <ChevronRight className="w-3 h-3" />
            </button>
          </div>
          <div className="flex flex-col sm:flex-row items-start gap-4">
            <div className="flex items-center gap-4 bg-white/[0.03] border border-white/[0.06] rounded-xl p-4 flex-1">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 p-[2px]">
                <div className="w-full h-full rounded-full bg-[#060812] flex items-center justify-center">
                  <span className="text-lg font-bold text-white">Z</span>
                </div>
              </div>
              <div>
                <p className="text-white font-semibold text-sm">Zoe lidera con $2,340 esta semana <span className="text-orange-400">🔥</span></p>
                <p className="text-white/30 text-xs">Instagram • 12 ventas • 38% conversión</p>
              </div>
            </div>
            <div className="flex gap-3 w-full sm:w-auto overflow-x-auto">
              {[
                { name: 'Zoe', revenue: 2340, deals: 12, color: 'from-purple-500 to-pink-500' },
                { name: 'Max', revenue: 1850, deals: 9, color: 'from-blue-500 to-cyan-500' },
                { name: 'Luna', revenue: 1200, deals: 6, color: 'from-emerald-500 to-teal-500' },
                { name: 'Kai', revenue: 890, deals: 4, color: 'from-amber-500 to-orange-500' },
              ].map(seller => (
                <button
                  key={seller.name}
                  onClick={() => router.push('/dashboard/equipo')}
                  className="flex flex-col items-center gap-1.5 p-3 bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.06] hover:border-white/[0.12] rounded-xl transition-all min-w-[80px]"
                >
                  <div className={`w-8 h-8 rounded-full bg-gradient-to-br ${seller.color} flex items-center justify-center`}>
                    <span className="text-[10px] font-bold text-white">{seller.name.charAt(0)}</span>
                  </div>
                  <p className="text-[10px] text-white/60 font-medium">{seller.name}</p>
                  <p className="text-[10px] text-emerald-400 font-semibold">${seller.revenue.toLocaleString('es-AR')}</p>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* ── Feature Modules ───────────────────────────────────────── */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Herramientas IA</h2>
            <span className="text-xs text-white/30">Potenciadas por SellIA</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {FEATURE_MODULES.map(mod => {
              const c = COLOR_CLASSES[mod.color]
              const Icon = mod.icon
              return (
                <div
                  key={mod.id}
                  className={`relative overflow-hidden border rounded-2xl p-5 transition-all cursor-pointer ${c.bg} ${c.border}`}
                  onClick={() => router.push(mod.href)}
                >
                  <div className="flex items-start gap-4 mb-4">
                    <div className={`w-11 h-11 rounded-xl ${c.badge} border flex items-center justify-center shrink-0`}>
                      <Icon className={`w-5 h-5 ${c.text}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <h3 className="text-white font-semibold">{mod.title}</h3>
                        {mod.badge && (
                          <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${c.badge}`}>
                            {mod.badge}
                          </span>
                        )}
                      </div>
                      <p className="text-white/40 text-sm leading-relaxed">{mod.description}</p>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {mod.actions.map(action => (
                      <button
                        key={action.label}
                        onClick={e => { e.stopPropagation(); router.push(action.href) }}
                        className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${c.btn}`}
                      >
                        {action.label}
                      </button>
                    ))}
                    <div className={`ml-auto flex items-center gap-1 text-xs ${c.text} opacity-60 hover:opacity-100 transition-opacity self-center`}>
                      <span>Explorar</span>
                      <ChevronRight className="w-3 h-3" />
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* ── Quick Actions ─────────────────────────────────────────── */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Acceso Rápido</h2>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { icon: Bot, label: 'Agentes IA', href: '/dashboard/agentes', color: 'text-brand-orange' },
              { icon: MessageSquare, label: 'Conversaciones', href: '/dashboard/conversaciones', color: 'text-blue-400' },
              { icon: BarChart3, label: 'Analytics', href: '/dashboard/analytics', color: 'text-emerald-400' },
              { icon: Users, label: 'CRM', href: '/dashboard/crm', color: 'text-purple-400' },
              { icon: Zap, label: 'Automatizaciones', href: '/dashboard/automatizaciones', color: 'text-amber-400' },
              { icon: Shield, label: 'Seguridad', href: '/dashboard/seguridad', color: 'text-red-400' },
            ].map(item => (
              <button
                key={item.href}
                onClick={() => router.push(item.href)}
                className="flex flex-col items-center gap-2 p-4 bg-white/[0.03] hover:bg-white/[0.07] border border-white/[0.06] hover:border-white/[0.15] rounded-xl transition-all group"
              >
                <item.icon className={`w-5 h-5 ${item.color} group-hover:scale-110 transition-transform`} />
                <span className="text-white/60 group-hover:text-white text-xs font-medium transition-colors text-center">{item.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* ── Companion + Gamification (Secondary) ─────────────────── */}
        <div className="border border-white/[0.06] rounded-2xl overflow-hidden">
          <button
            onClick={() => setGardenOpen(prev => !prev)}
            className="w-full flex items-center justify-between px-5 py-4 bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/20 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-purple-400" />
              </div>
              <div className="text-left">
                <p className="text-white text-sm font-medium">Tu Progreso y Jardín</p>
                <p className="text-white/30 text-xs">
                  {profile ? `Nivel ${profile.level} • ${profile.total_xp} XP • ${profile.total_sales_closed} ventas` : 'Sistema de gamificación'}
                </p>
              </div>
            </div>
            <div className={`w-5 h-5 flex items-center justify-center text-white/30 transition-transform ${gardenOpen ? 'rotate-90' : ''}`}>
              <ChevronRight className="w-4 h-4" />
            </div>
          </button>

          {gardenOpen && (
            <div className="px-5 pb-5 bg-white/[0.01] space-y-4">
              {/* Companion message */}
              <div className="flex items-start gap-3 pt-4">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center shrink-0">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1 bg-white/5 border border-white/5 rounded-xl p-3">
                  <p className="text-white/50 text-[10px] mb-1">{profile?.companion_name || 'Selia'}</p>
                  <p className="text-white/70 text-sm leading-relaxed">{companionMessage}</p>
                </div>
              </div>

              {/* Stats row */}
              <div className="grid grid-cols-4 gap-3">
                {[
                  { icon: Flame, value: profile?.current_login_streak || 0, label: 'Racha', color: 'text-orange-400' },
                  { icon: Trophy, value: profile?.total_achievements || 0, label: 'Logros', color: 'text-amber-400' },
                  { icon: Zap, value: profile?.total_sales_closed || 0, label: 'Ventas', color: 'text-emerald-400' },
                  { icon: Star, value: profile?.level || 1, label: 'Nivel', color: 'text-purple-400' },
                ].map(stat => (
                  <div key={stat.label} className="bg-white/5 border border-white/5 rounded-xl p-3 text-center">
                    <stat.icon className={`w-4 h-4 ${stat.color} mx-auto mb-1`} />
                    <p className="text-white font-bold">{stat.value}</p>
                    <p className="text-white/30 text-xs">{stat.label}</p>
                  </div>
                ))}
              </div>

              {/* Mini garden */}
              <GardenMini garden={garden} />

              <div className="flex gap-2">
                <button
                  onClick={() => router.push('/dashboard/gamification')}
                  className="flex-1 py-2.5 text-sm bg-white/5 hover:bg-white/10 border border-white/5 text-white/50 hover:text-white rounded-xl transition-colors"
                >
                  Ver todos los logros
                </button>
                <button
                  onClick={() => router.push('/dashboard/leaderboard')}
                  className="flex-1 py-2.5 text-sm bg-white/5 hover:bg-white/10 border border-white/5 text-white/50 hover:text-white rounded-xl transition-colors"
                >
                  Ranking global
                </button>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}

// ─── Mini Garden Component ─────────────────────────────────────────────────────

function GardenMini({ garden }: { garden: any }) {
  const flowers = garden?.garden?.flowers || 0
  const trees = garden?.garden?.trees || 0
  const butterflies = garden?.garden?.butterflies || 0
  const birds = garden?.garden?.birds || 0
  const isEmpty = flowers === 0 && trees === 0

  return (
    <div className="relative h-36 bg-gradient-to-b from-sky-900/20 to-emerald-900/20 rounded-xl overflow-hidden border border-white/5">
      <div className="absolute bottom-0 left-0 right-0 h-10 bg-gradient-to-t from-emerald-900/30 to-transparent" />

      {Array.from({ length: Math.min(trees, 5) }).map((_, i) => (
        <div key={`t-${i}`} className="absolute bottom-6" style={{ left: `${8 + i * 18}%` }}>
          <TreePine className="w-10 h-10 text-emerald-500" />
        </div>
      ))}
      {Array.from({ length: Math.min(flowers, 15) }).map((_, i) => (
        <div key={`f-${i}`} className="absolute bottom-4" style={{ left: `${4 + (i * 6) % 88}%` }}>
          <Flower2 className="w-3.5 h-3.5 text-pink-400" />
        </div>
      ))}
      {Array.from({ length: Math.min(butterflies, 3) }).map((_, i) => (
        <div key={`b-${i}`} className="absolute animate-bounce" style={{ top: `${25 + i * 15}%`, left: `${30 + i * 20}%`, animationDuration: '3s' }}>
          <span className="text-base">🦋</span>
        </div>
      ))}
      {Array.from({ length: Math.min(birds, 3) }).map((_, i) => (
        <div key={`bi-${i}`} className="absolute" style={{ top: `${10 + i * 10}%`, left: `${40 + i * 20}%` }}>
          <Bird className="w-4 h-4 text-sky-300" />
        </div>
      ))}

      {isEmpty && (
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <Flower2 className="w-7 h-7 text-white/10 mb-1.5" />
          <p className="text-white/20 text-xs text-center">Tu jardín crece con cada venta</p>
          <p className="text-white/10 text-[10px]">Cerrá tu primer deal para plantar una flor</p>
        </div>
      )}

      <div className="absolute top-2 right-2 flex gap-2 text-[10px] text-white/30">
        <span>🌳 {trees}</span>
        <span>🌸 {flowers}</span>
        <span>🦋 {butterflies}</span>
        <span>🐦 {birds}</span>
      </div>
    </div>
  )
}
