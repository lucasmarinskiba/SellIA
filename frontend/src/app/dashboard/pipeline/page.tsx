'use client'

export const dynamic = 'force-dynamic'

import { useEffect, useState, useCallback } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { crmApi, Deal } from '@/lib/crm'
import { businessApi } from '@/lib/business'
import {
  Target, ChevronRight, Plus, Loader2, Search, Filter,
  TrendingUp, DollarSign, Users, Zap, Clock, Star,
  ArrowRight, Bot, MoreHorizontal, X, AlertCircle
} from 'lucide-react'

// ─── Pipeline Stage Config ─────────────────────────────────────────────────────

const STAGES = [
  { id: 'prospecting', label: 'Prospección', emoji: '🎯', color: 'blue', methodology: 'Gary Vee', description: 'Captación inicial de prospectos' },
  { id: 'qualifying', label: 'Calificación', emoji: '🔍', color: 'indigo', methodology: 'BANT+MEDDIC', description: 'Filtrar leads de calidad' },
  { id: 'nurturing', label: 'Nutrición', emoji: '🌱', color: 'teal', methodology: 'Email sequences', description: 'Calentar leads fríos' },
  { id: 'discovery', label: 'Diagnóstico', emoji: '💡', color: 'cyan', methodology: 'SPIN Selling', description: 'Entender la necesidad real' },
  { id: 'proposal', label: 'Propuesta', emoji: '📦', color: 'amber', methodology: 'Hormozi Grand Slam', description: 'Oferta irresistible' },
  { id: 'objection', label: 'Objeciones', emoji: '🛡️', color: 'orange', methodology: 'Belfort + Cialdini', description: 'Manejar resistencia' },
  { id: 'closing', label: 'Cierre', emoji: '🤝', color: 'green', methodology: 'Ziglar + Cardone', description: 'Cerrar la venta' },
  { id: 'onboarding', label: 'Bienvenida', emoji: '🚀', color: 'emerald', methodology: 'Bezos CX', description: 'Primera victoria del cliente' },
  { id: 'retention', label: 'Retención', emoji: '💎', color: 'purple', methodology: 'RFM + LTV', description: 'Upsell y lealtad' },
] as const

type StageId = typeof STAGES[number]['id']

const STAGE_COLORS: Record<string, { bg: string; border: string; text: string; dot: string; tag: string }> = {
  blue: { bg: 'bg-blue-500/8', border: 'border-blue-500/25', text: 'text-blue-400', dot: 'bg-blue-500', tag: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
  indigo: { bg: 'bg-indigo-500/8', border: 'border-indigo-500/25', text: 'text-indigo-400', dot: 'bg-indigo-500', tag: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30' },
  teal: { bg: 'bg-teal-500/8', border: 'border-teal-500/25', text: 'text-teal-400', dot: 'bg-teal-500', tag: 'bg-teal-500/20 text-teal-400 border-teal-500/30' },
  cyan: { bg: 'bg-cyan-500/8', border: 'border-cyan-500/25', text: 'text-cyan-400', dot: 'bg-cyan-500', tag: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30' },
  amber: { bg: 'bg-amber-500/8', border: 'border-amber-500/25', text: 'text-amber-400', dot: 'bg-amber-500', tag: 'bg-amber-500/20 text-amber-400 border-amber-500/30' },
  orange: { bg: 'bg-orange-500/8', border: 'border-orange-500/25', text: 'text-orange-400', dot: 'bg-orange-500', tag: 'bg-orange-500/20 text-orange-400 border-orange-500/30' },
  green: { bg: 'bg-green-500/8', border: 'border-green-500/25', text: 'text-green-400', dot: 'bg-green-500', tag: 'bg-green-500/20 text-green-400 border-green-500/30' },
  emerald: { bg: 'bg-emerald-500/8', border: 'border-emerald-500/25', text: 'text-emerald-400', dot: 'bg-emerald-500', tag: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' },
  purple: { bg: 'bg-purple-500/8', border: 'border-purple-500/25', text: 'text-purple-400', dot: 'bg-purple-500', tag: 'bg-purple-500/20 text-purple-400 border-purple-500/30' },
}

// ─── Main Page ─────────────────────────────────────────────────────────────────

export default function PipelinePage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const initialStage = searchParams?.get('stage') as StageId | null

  const [deals, setDeals] = useState<Deal[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [activeStage, setActiveStage] = useState<StageId | null>(initialStage)
  const [selectedDeal, setSelectedDeal] = useState<Deal | null>(null)

  const loadDeals = useCallback(async () => {
    setLoading(true)
    try {
      const businesses = await businessApi.list().catch(() => [])
      const businessId = businesses?.[0]?.id
      if (businessId) {
        const data = await crmApi.getDeals(businessId, {})
        setDeals((data || []).filter((d: Deal) => d.is_active))
      } else {
        setDeals([])
      }
    } catch {
      setDeals([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDeals()
  }, [loadDeals])

  const getDealsForStage = (stageId: string) =>
    deals.filter(d =>
      d.stage === stageId &&
      (search === '' || d.title.toLowerCase().includes(search.toLowerCase()) ||
        (d.contact_name || '').toLowerCase().includes(search.toLowerCase()))
    )

  const totalValue = deals.reduce((sum, d) => sum + (d.value || 0), 0)
  const activeDeals = deals.length

  const activateAgent = (stage: StageId, deal?: Deal) => {
    const params = new URLSearchParams({ section: 'pipeline', stage })
    if (deal?.id) params.set('deal', deal.id)
    if (deal?.contact_name) params.set('contact', deal.contact_name)
    router.push(`/dashboard/agentes?${params.toString()}`)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <div className="text-center space-y-3">
          <Target className="w-10 h-10 text-emerald-400 animate-pulse mx-auto" />
          <p className="text-white/40 text-sm">Cargando pipeline...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#060812]">
      <div className="max-w-[1600px] mx-auto p-6 space-y-6">

        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <Target className="w-6 h-6 text-emerald-400" />
              <h1 className="text-2xl font-bold text-white">Pipeline de Ventas</h1>
            </div>
            <p className="text-white/40 text-sm">9 etapas especializadas con agentes IA para cada fase del proceso</p>
          </div>
          <button
            onClick={() => router.push('/dashboard/crm')}
            className="flex items-center gap-2 px-4 py-2.5 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/30 text-emerald-400 rounded-xl text-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            Nuevo Deal
          </button>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Deals activos', value: activeDeals, icon: Target, color: 'text-emerald-400' },
            { label: 'Valor total pipeline', value: `$${totalValue.toLocaleString('es-AR')}`, icon: DollarSign, color: 'text-amber-400' },
            { label: 'Etapas activas', value: new Set(deals.map(d => d.stage)).size, icon: Zap, color: 'text-blue-400' },
            { label: 'Agentes disponibles', value: 9, icon: Bot, color: 'text-purple-400' },
          ].map(kpi => (
            <div key={kpi.label} className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <kpi.icon className={`w-4 h-4 ${kpi.color}`} />
                <span className="text-xs text-white/40">{kpi.label}</span>
              </div>
              <p className="text-2xl font-bold text-white">{kpi.value}</p>
            </div>
          ))}
        </div>

        {/* Search */}
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Buscar deal o contacto..."
            className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
          />
        </div>

        {/* Pipeline Board */}
        <div className="overflow-x-auto pb-4">
          <div className="flex gap-3 min-w-max">
            {STAGES.map(stage => {
              const stageDeals = getDealsForStage(stage.id)
              const c = STAGE_COLORS[stage.color]
              const stageValue = stageDeals.reduce((sum, d) => sum + (d.value || 0), 0)
              const isActive = activeStage === stage.id

              return (
                <div
                  key={stage.id}
                  className={`w-64 flex flex-col rounded-2xl border transition-all ${
                    isActive ? `${c.bg} ${c.border}` : 'bg-white/[0.02] border-white/[0.06]'
                  }`}
                >
                  {/* Stage Header */}
                  <div
                    className="p-3 cursor-pointer select-none"
                    onClick={() => setActiveStage(prev => prev === stage.id ? null : stage.id as StageId)}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <span className="text-lg leading-none">{stage.emoji}</span>
                        <span className="text-sm font-semibold text-white">{stage.label}</span>
                      </div>
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${c.tag} border`}>
                        {stageDeals.length}
                      </span>
                    </div>
                    <p className="text-[10px] text-white/30">{stage.methodology}</p>
                    {stageValue > 0 && (
                      <p className={`text-xs font-medium mt-1 ${c.text}`}>${stageValue.toLocaleString('es-AR')}</p>
                    )}
                  </div>

                  {/* Activate Agent Button */}
                  <button
                    onClick={() => activateAgent(stage.id as StageId)}
                    className={`mx-3 mb-2 py-1.5 text-xs rounded-lg border transition-colors flex items-center justify-center gap-1.5 ${c.tag}`}
                  >
                    <Bot className="w-3 h-3" />
                    Agente {stage.label}
                  </button>

                  {/* Deal Cards */}
                  <div className="flex-1 px-2 pb-3 space-y-2 overflow-y-auto max-h-[500px]">
                    {stageDeals.length === 0 ? (
                      <div className="text-center py-8 text-white/15">
                        <div className="text-2xl mb-1">{stage.emoji}</div>
                        <p className="text-[10px]">Sin deals en esta etapa</p>
                        <button
                          onClick={() => activateAgent(stage.id as StageId)}
                          className={`mt-2 text-[10px] ${c.text} hover:underline`}
                        >
                          + Activar agente
                        </button>
                      </div>
                    ) : stageDeals.map(deal => (
                      <DealCard
                        key={deal.id}
                        deal={deal}
                        color={c}
                        onOpen={() => setSelectedDeal(deal)}
                        onActivate={() => activateAgent(stage.id as StageId, deal)}
                      />
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Stage Methodology Legend */}
        <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Metodologías por Etapa</h3>
          <div className="grid grid-cols-3 lg:grid-cols-9 gap-3">
            {STAGES.map(stage => {
              const c = STAGE_COLORS[stage.color]
              return (
                <button
                  key={stage.id}
                  onClick={() => activateAgent(stage.id as StageId)}
                  className="text-center group"
                >
                  <div className={`w-10 h-10 rounded-xl border mx-auto mb-1.5 flex items-center justify-center transition-all group-hover:scale-110 ${c.bg} ${c.border}`}>
                    <span className="text-lg">{stage.emoji}</span>
                  </div>
                  <p className="text-[10px] text-white/50 group-hover:text-white transition-colors">{stage.label}</p>
                  <p className={`text-[9px] ${c.text} opacity-60 group-hover:opacity-100 transition-opacity leading-tight mt-0.5`}>{stage.methodology}</p>
                </button>
              )
            })}
          </div>
        </div>

      </div>

      {/* Deal Detail Modal */}
      {selectedDeal && (
        <DealModal
          deal={selectedDeal}
          onClose={() => setSelectedDeal(null)}
          onActivate={(stage) => {
            setSelectedDeal(null)
            activateAgent(stage as StageId, selectedDeal)
          }}
        />
      )}
    </div>
  )
}

// ─── Deal Card ─────────────────────────────────────────────────────────────────

function DealCard({ deal, color, onOpen, onActivate }: {
  deal: Deal
  color: { bg: string; border: string; text: string; dot: string; tag: string }
  onOpen: () => void
  onActivate: () => void
}) {
  return (
    <div
      onClick={onOpen}
      className="bg-white/[0.04] hover:bg-white/[0.07] border border-white/[0.07] hover:border-white/[0.15] rounded-xl p-3 cursor-pointer transition-all group"
    >
      <div className="flex items-start justify-between gap-1 mb-1.5">
        <p className="text-white text-xs font-medium leading-snug flex-1">{deal.title}</p>
        <div className={`w-2 h-2 rounded-full mt-0.5 shrink-0 ${color.dot}`} />
      </div>
      {deal.contact_name && (
        <p className="text-white/40 text-[10px] mb-1.5">{deal.contact_name}</p>
      )}
      <div className="flex items-center justify-between">
        {deal.value ? (
          <span className={`text-[10px] font-semibold ${color.text}`}>${deal.value.toLocaleString('es-AR')}</span>
        ) : (
          <span className="text-white/20 text-[10px]">Sin valor</span>
        )}
        <button
          onClick={e => { e.stopPropagation(); onActivate() }}
          className={`opacity-0 group-hover:opacity-100 text-[9px] px-2 py-0.5 rounded-lg border transition-all ${color.tag}`}
        >
          <Bot className="w-2.5 h-2.5 inline mr-0.5" />
          IA
        </button>
      </div>
      {deal.probability > 0 && (
        <div className="mt-1.5 h-1 bg-white/5 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full ${color.dot}`}
            style={{ width: `${deal.probability}%`, opacity: 0.6 }}
          />
        </div>
      )}
    </div>
  )
}

// ─── Deal Modal ────────────────────────────────────────────────────────────────

function DealModal({ deal, onClose, onActivate }: {
  deal: Deal
  onClose: () => void
  onActivate: (stage: string) => void
}) {
  const stage = STAGES.find(s => s.id === deal.stage)
  const c = stage ? STAGE_COLORS[stage.color] : STAGE_COLORS.blue

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-[#0a0e1f] border border-white/10 rounded-2xl overflow-hidden">
        <div className={`px-5 py-4 flex items-center justify-between border-b border-white/5 ${c.bg}`}>
          <div className="flex items-center gap-3">
            <span className="text-xl">{stage?.emoji || '🎯'}</span>
            <div>
              <h3 className="text-white font-semibold">{deal.title}</h3>
              <p className={`text-xs ${c.text}`}>{stage?.label || deal.stage} • {stage?.methodology}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 hover:bg-white/10 rounded-lg text-white/40 hover:text-white transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {/* Contact & Value */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-white/5 border border-white/5 rounded-xl p-3">
              <p className="text-white/40 text-xs mb-1">Contacto</p>
              <p className="text-white text-sm">{deal.contact_name || '—'}</p>
              {deal.contact_email && <p className="text-white/40 text-[10px]">{deal.contact_email}</p>}
            </div>
            <div className="bg-white/5 border border-white/5 rounded-xl p-3">
              <p className="text-white/40 text-xs mb-1">Valor</p>
              <p className={`text-sm font-bold ${c.text}`}>
                {deal.value ? `$${deal.value.toLocaleString('es-AR')}` : '—'}
              </p>
              {deal.probability > 0 && (
                <p className="text-white/30 text-[10px]">{deal.probability}% probabilidad</p>
              )}
            </div>
          </div>

          {/* Activate Pipeline Agent */}
          <div className={`p-4 rounded-xl border ${c.bg} ${c.border}`}>
            <div className="flex items-center gap-2 mb-2">
              <Bot className={`w-4 h-4 ${c.text}`} />
              <p className="text-white text-sm font-medium">Agente de {stage?.label}</p>
            </div>
            <p className="text-white/40 text-xs mb-3">{stage?.description} — con metodología {stage?.methodology}</p>
            <button
              onClick={() => onActivate(deal.stage)}
              className={`w-full py-2.5 rounded-xl text-sm font-medium transition-colors ${c.tag} border`}
            >
              Activar agente para este deal
            </button>
          </div>

          {/* Quick stage jump */}
          <div>
            <p className="text-white/40 text-xs mb-2">Mover a otra etapa</p>
            <div className="flex flex-wrap gap-1.5">
              {STAGES.filter(s => s.id !== deal.stage).slice(0, 5).map(s => {
                const sc = STAGE_COLORS[s.color]
                return (
                  <button
                    key={s.id}
                    onClick={() => onActivate(s.id)}
                    className={`text-[10px] px-2.5 py-1.5 rounded-lg border transition-colors ${sc.tag}`}
                  >
                    {s.emoji} {s.label}
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
