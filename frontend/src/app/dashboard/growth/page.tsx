'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { growthApi, GrowthDashboardMetrics, GrowthCampaign, LeadMagnet, InboundLead, SocialProofItem, ReferralMetrics, ValueSequence } from '@/lib/growth'
import { businessApi } from '@/lib/business'
import StatCard from '@/components/ui/StatCard'
import Button from '@/components/ui/Button'
import {
  TrendingUp, Users, Target, Award, MessageCircle, Share2,
  BookOpen, Zap, BarChart3, Megaphone, Gift, Star,
  Camera, ChevronRight, Pause, Play, Eye, CheckCircle,
  XCircle, Clock, ArrowUpRight, Heart
} from 'lucide-react'

type TabType = 'overview' | 'campaigns' | 'magnets' | 'leads' | 'referrals' | 'social' | 'sequences'

export default function GrowthPage() {
  const { user } = useAuth()
  const [businessId, setBusinessId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [metrics, setMetrics] = useState<GrowthDashboardMetrics | null>(null)
  const [campaigns, setCampaigns] = useState<GrowthCampaign[]>([])
  const [magnets, setMagnets] = useState<LeadMagnet[]>([])
  const [leads, setLeads] = useState<InboundLead[]>([])
  const [socialProofs, setSocialProofs] = useState<SocialProofItem[]>([])
  const [referralMetrics, setReferralMetrics] = useState<ReferralMetrics | null>(null)
  const [sequences, setSequences] = useState<ValueSequence[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchBusiness = async () => {
      try {
        const businesses = await businessApi.list()
        if (businesses.length > 0) {
          setBusinessId(businesses[0].id)
        }
      } catch (e) {
        setError('No se pudo cargar el negocio')
      }
    }
    fetchBusiness()
  }, [user])

  useEffect(() => {
    if (!businessId) return
    loadAll()
  }, [businessId])

  const loadAll = async () => {
    setLoading(true)
    try {
      const [m, c, mg, l, sp, rm, sq] = await Promise.all([
        growthApi.getDashboard(),
        growthApi.listCampaigns(),
        growthApi.listLeadMagnets(),
        growthApi.listInboundLeads({ limit: 20 }),
        growthApi.getSocialProofWall({ count: 10 }),
        growthApi.getReferralMetrics().catch(() => null),
        growthApi.listValueSequences(),
      ])
      setMetrics(m)
      setCampaigns(c)
      setMagnets(mg)
      setLeads(l)
      setSocialProofs(sp)
      setReferralMetrics(rm)
      setSequences(sq)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error cargando datos de growth')
    } finally {
      setLoading(false)
    }
  }

  const tabs: { id: TabType; label: string; icon: any }[] = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'campaigns', label: 'Campañas', icon: Megaphone },
    { id: 'magnets', label: 'Lead Magnets', icon: Magnet },
    { id: 'leads', label: 'Leads', icon: Users },
    { id: 'referrals', label: 'Referidos', icon: Share2 },
    { id: 'social', label: 'Social Proof', icon: Star },
    { id: 'sequences', label: 'Secuencias', icon: MessageCircle },
  ]

  if (loading) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-white/5 rounded w-1/4" />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[1,2,3,4].map(i => (
              <div key={i} className="h-24 bg-white/5 rounded-xl" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <TrendingUp className="w-7 h-7 text-emerald-400" />
            Growth Engine
          </h1>
          <p className="text-white/50 text-sm mt-1">Vender sin vender — Adquisición orgánica 24/7</p>
        </div>
        <Button onClick={loadAll} variant="outline" size="sm">
          <Zap className="w-4 h-4 mr-2" />
          Actualizar
        </Button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 overflow-x-auto pb-2">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
              activeTab === tab.id
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'text-white/60 hover:text-white hover:bg-white/5'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && <OverviewTab metrics={metrics} campaigns={campaigns} magnets={magnets} referralMetrics={referralMetrics} />}
      {activeTab === 'campaigns' && <CampaignsTab campaigns={campaigns} onRefresh={loadAll} />}
      {activeTab === 'magnets' && <MagnetsTab magnets={magnets} />}
      {activeTab === 'leads' && <LeadsTab leads={leads} />}
      {activeTab === 'referrals' && <ReferralsTab metrics={referralMetrics} />}
      {activeTab === 'social' && <SocialTab items={socialProofs} />}
      {activeTab === 'sequences' && <SequencesTab sequences={sequences} />}
    </div>
  )
}

// ========== Overview Tab ==========

function OverviewTab({ metrics, campaigns, magnets, referralMetrics }: {
  metrics: GrowthDashboardMetrics | null
  campaigns: GrowthCampaign[]
  magnets: LeadMagnet[]
  referralMetrics: ReferralMetrics | null
}) {
  if (!metrics) return null

  const topMagnet = magnets.filter(m => m.conversion_rate > 0).sort((a, b) => b.conversion_rate - a.conversion_rate)[0]

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Leads esta semana"
          value={metrics.leads_this_week}
          icon={<Users className="w-5 h-5" />}
          color="emerald"
        />
        <StatCard
          label="Conversion Rate"
          value={`${metrics.conversion_rate}%`}
          icon={<Target className="w-5 h-5" />}
          color="blue"
        />
        <StatCard
          label="Coeficiente Viral (K)"
          value={referralMetrics?.k_factor?.toFixed(2) || '0.00'}
          icon={<Share2 className="w-5 h-5" />}
          color="purple"
        />
        <StatCard
          label="Campañas Activas"
          value={metrics.active_campaigns}
          icon={<Megaphone className="w-5 h-5" />}
          color="amber"
        />
      </div>

      {/* Secondary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white/5 border border-white/10 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-white font-medium flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-emerald-400" />
              Lead Magnets
            </h3>
            <span className="text-emerald-400 text-sm font-medium">{magnets.length} activos</span>
          </div>
          {topMagnet ? (
            <div>
              <p className="text-white/80 text-sm">{topMagnet.title}</p>
              <p className="text-emerald-400 text-2xl font-bold mt-1">{topMagnet.conversion_rate.toFixed(1)}%</p>
              <p className="text-white/40 text-xs">conversion rate — mejor performer</p>
            </div>
          ) : (
            <p className="text-white/40 text-sm">No hay lead magnets activos</p>
          )}
        </div>

        <div className="bg-white/5 border border-white/10 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-white font-medium flex items-center gap-2">
              <Target className="w-4 h-4 text-blue-400" />
              Fuentes de Leads
            </h3>
          </div>
          <div className="space-y-2">
            {Object.entries(metrics.sources_breakdown || {}).slice(0, 4).map(([source, count]) => (
              <div key={source} className="flex items-center justify-between">
                <span className="text-white/60 text-sm capitalize">{source.replace('_', ' ')}</span>
                <span className="text-white font-medium text-sm">{count}</span>
              </div>
            ))}
            {Object.keys(metrics.sources_breakdown || {}).length === 0 && (
              <p className="text-white/40 text-sm">Sin leads orgánicos aún</p>
            )}
          </div>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-white font-medium flex items-center gap-2">
              <Award className="w-4 h-4 text-purple-400" />
              Viralidad
            </h3>
          </div>
          {referralMetrics ? (
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-white/60 text-sm">Referidores</span>
                <span className="text-white font-medium">{referralMetrics.unique_referrers}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/60 text-sm">Signups</span>
                <span className="text-white font-medium">{referralMetrics.total_signups}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/60 text-sm">Ingresos</span>
                <span className="text-emerald-400 font-medium">${referralMetrics.total_revenue.toFixed(0)}</span>
              </div>
              <div className={`mt-2 px-2 py-1 rounded text-xs font-medium text-center ${
                referralMetrics.exponential_growth
                  ? 'bg-emerald-500/20 text-emerald-400'
                  : 'bg-white/5 text-white/40'
              }`}>
                {referralMetrics.exponential_growth ? '🚀 Crecimiento viral!' : 'Crecimiento lineal'}
              </div>
            </div>
          ) : (
            <p className="text-white/40 text-sm">No hay datos de referidos</p>
          )}
        </div>
      </div>

      {/* Active Campaigns Preview */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-5">
        <h3 className="text-white font-medium mb-4 flex items-center gap-2">
          <Megaphone className="w-4 h-4 text-amber-400" />
          Campañas Activas
        </h3>
        <div className="space-y-3">
          {campaigns.filter(c => c.status === 'active').slice(0, 3).map(campaign => (
            <div key={campaign.id} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
              <div>
                <p className="text-white text-sm font-medium">{campaign.name}</p>
                <p className="text-white/40 text-xs capitalize">{campaign.campaign_type.replace('_', ' ')}</p>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className="text-white text-sm font-medium">{campaign.leads_generated}</p>
                  <p className="text-white/40 text-xs">leads</p>
                </div>
                <div className="text-right">
                  <p className="text-emerald-400 text-sm font-medium">{campaign.conversions}</p>
                  <p className="text-white/40 text-xs">conversiones</p>
                </div>
              </div>
            </div>
          ))}
          {campaigns.filter(c => c.status === 'active').length === 0 && (
            <p className="text-white/40 text-sm">No hay campañas activas. Crea una para empezar a crecer orgánicamente.</p>
          )}
        </div>
      </div>
    </div>
  )
}

// ========== Campaigns Tab ==========

function CampaignsTab({ campaigns, onRefresh }: { campaigns: GrowthCampaign[]; onRefresh: () => void }) {
  const handleActivate = async (id: string) => {
    try {
      await growthApi.activateCampaign(id)
      onRefresh()
    } catch (e) {
      console.error(e)
    }
  }

  const handlePause = async (id: string) => {
    try {
      await growthApi.pauseCampaign(id)
      onRefresh()
    } catch (e) {
      console.error(e)
    }
  }

  const statusColors: Record<string, string> = {
    active: 'bg-emerald-500/20 text-emerald-400',
    paused: 'bg-amber-500/20 text-amber-400',
    draft: 'bg-white/5 text-white/40',
    completed: 'bg-blue-500/20 text-blue-400',
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Campañas de Crecimiento</h2>
        <Button variant="primary" size="sm">
          <Megaphone className="w-4 h-4 mr-2" />
          Nueva Campaña
        </Button>
      </div>

      <div className="grid gap-3">
        {campaigns.map(campaign => (
          <div key={campaign.id} className="bg-white/5 border border-white/10 rounded-xl p-4">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-white font-medium">{campaign.name}</h3>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[campaign.status] || 'bg-white/5 text-white/40'}`}>
                    {campaign.status}
                  </span>
                </div>
                <p className="text-white/50 text-sm mt-1">{campaign.description}</p>
                <div className="flex items-center gap-4 mt-2 text-xs text-white/40">
                  <span className="capitalize">{campaign.campaign_type.replace('_', ' ')}</span>
                  <span>•</span>
                  <span>{campaign.leads_generated} leads</span>
                  <span>•</span>
                  <span>{campaign.conversions} conversiones</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {campaign.status === 'draft' && (
                  <Button onClick={() => handleActivate(campaign.id)} variant="outline" size="sm">
                    <Play className="w-3 h-3 mr-1" />
                    Activar
                  </Button>
                )}
                {campaign.status === 'active' && (
                  <Button onClick={() => handlePause(campaign.id)} variant="outline" size="sm">
                    <Pause className="w-3 h-3 mr-1" />
                    Pausar
                  </Button>
                )}
              </div>
            </div>
          </div>
        ))}
        {campaigns.length === 0 && (
          <div className="text-center py-12">
            <Megaphone className="w-12 h-12 text-white/10 mx-auto mb-4" />
            <p className="text-white/40">No hay campañas creadas</p>
          </div>
        )}
      </div>
    </div>
  )
}

// ========== Lead Magnets Tab ==========

function MagnetsTab({ magnets }: { magnets: LeadMagnet[] }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Lead Magnets</h2>
        <Button variant="primary" size="sm">
          <Gift className="w-4 h-4 mr-2" />
          Crear Lead Magnet
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {magnets.map(magnet => (
          <div key={magnet.id} className="bg-white/5 border border-white/10 rounded-xl p-4">
            <div className="flex items-start justify-between mb-2">
              <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 rounded text-xs font-medium capitalize">
                {magnet.format.replace('_', ' ')}
              </span>
              {magnet.conversion_rate >= 10 && (
                <Star className="w-4 h-4 text-amber-400" />
              )}
            </div>
            <h3 className="text-white font-medium text-sm">{magnet.title}</h3>
            <p className="text-white/40 text-xs mt-1">{magnet.topic}</p>
            <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-white/5">
              <div className="text-center">
                <p className="text-white font-medium text-sm">{magnet.times_delivered}</p>
                <p className="text-white/30 text-xs">entregas</p>
              </div>
              <div className="text-center">
                <p className="text-white font-medium text-sm">{magnet.times_converted}</p>
                <p className="text-white/30 text-xs">conversiones</p>
              </div>
              <div className="text-center">
                <p className={`font-medium text-sm ${magnet.conversion_rate >= 10 ? 'text-emerald-400' : 'text-white'}`}>
                  {magnet.conversion_rate.toFixed(1)}%
                </p>
                <p className="text-white/30 text-xs">rate</p>
              </div>
            </div>
          </div>
        ))}
        {magnets.length === 0 && (
          <div className="col-span-full text-center py-12">
            <Gift className="w-12 h-12 text-white/10 mx-auto mb-4" />
            <p className="text-white/40">No hay lead magnets creados</p>
          </div>
        )}
      </div>
    </div>
  )
}

// ========== Leads Tab ==========

function LeadsTab({ leads }: { leads: InboundLead[] }) {
  const stageColors: Record<string, string> = {
    new: 'bg-white/5 text-white/40',
    awareness: 'bg-blue-500/20 text-blue-400',
    interest: 'bg-emerald-500/20 text-emerald-400',
    consideration: 'bg-amber-500/20 text-amber-400',
    evaluation: 'bg-purple-500/20 text-purple-400',
    converted: 'bg-emerald-500/20 text-emerald-400',
    dormant: 'bg-red-500/20 text-red-400',
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-white">Inbound Leads Orgánicos</h2>

      <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left text-white/40 text-xs font-medium px-4 py-3">Fuente</th>
              <th className="text-left text-white/40 text-xs font-medium px-4 py-3">Etapa</th>
              <th className="text-left text-white/40 text-xs font-medium px-4 py-3">Engagement</th>
              <th className="text-left text-white/40 text-xs font-medium px-4 py-3">Touches</th>
              <th className="text-left text-white/40 text-xs font-medium px-4 py-3">Fecha</th>
            </tr>
          </thead>
          <tbody>
            {leads.map(lead => (
              <tr key={lead.id} className="border-b border-white/5 hover:bg-white/5">
                <td className="px-4 py-3">
                  <span className="text-white text-sm capitalize">{lead.source_type.replace('_', ' ')}</span>
                  {lead.source_detail && (
                    <p className="text-white/30 text-xs">{lead.source_detail}</p>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium capitalize ${stageColors[lead.nurturing_stage] || 'bg-white/5 text-white/40'}`}>
                    {lead.nurturing_stage}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="w-16 h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-400 rounded-full"
                      style={{ width: `${Math.min(lead.engagement_score, 100)}%` }}
                    />
                  </div>
                </td>
                <td className="px-4 py-3 text-white/60 text-sm">
                  {lead.value_touches_received}V / {lead.sales_touches_received}S
                </td>
                <td className="px-4 py-3 text-white/40 text-sm">
                  {new Date(lead.first_touch_at).toLocaleDateString('es-AR')}
                </td>
              </tr>
            ))}
            {leads.length === 0 && (
              <tr>
                <td colSpan={5} className="text-center py-12 text-white/40">
                  <Users className="w-12 h-12 text-white/10 mx-auto mb-4" />
                  No hay leads orgánicos capturados
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ========== Referrals Tab ==========

function ReferralsTab({ metrics }: { metrics: ReferralMetrics | null }) {
  if (!metrics) {
    return (
      <div className="text-center py-12">
        <Share2 className="w-12 h-12 text-white/10 mx-auto mb-4" />
        <p className="text-white/40">No hay datos de referidos</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-white">Programa de Referidos</h2>

      {/* K-Factor Big Display */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-8 text-center">
        <p className="text-white/50 text-sm mb-2">Coeficiente Viral (K-Factor)</p>
        <p className={`text-6xl font-bold ${metrics.exponential_growth ? 'text-emerald-400' : 'text-white'}`}>
          {metrics.k_factor.toFixed(2)}
        </p>
        <p className={`mt-2 text-sm font-medium ${metrics.exponential_growth ? 'text-emerald-400' : 'text-white/40'}`}>
          {metrics.exponential_growth ? '🚀 Crecimiento exponencial alcanzado' : 'Crecimiento lineal — optimiza para K > 1.0'}
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Referidores" value={metrics.unique_referrers} icon={<Users className="w-5 h-5" />} color="blue" />
        <StatCard label="Signups" value={metrics.total_signups} icon={<ArrowUpRight className="w-5 h-5" />} color="emerald" />
        <StatCard label="Conversiones" value={metrics.total_conversions} icon={<CheckCircle className="w-5 h-5" />} color="purple" />
        <StatCard label="Ingresos" value={`$${metrics.total_revenue.toFixed(0)}`} icon={<Award className="w-5 h-5" />} color="amber" />
      </div>

      <div className="bg-white/5 border border-white/10 rounded-xl p-5">
        <h3 className="text-white font-medium mb-4">Métricas Detalladas</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-white/40 text-xs">Signups por referidor</p>
            <p className="text-white font-medium">{metrics.signups_per_referrer.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-white/40 text-xs">Tasa de conversión</p>
            <p className="text-white font-medium">{metrics.conversion_rate.toFixed(1)}%</p>
          </div>
          <div>
            <p className="text-white/40 text-xs">Interpretación</p>
            <p className="text-white font-medium capitalize">{metrics.k_interpretation}</p>
          </div>
          <div>
            <p className="text-white/40 text-xs">Meta K-Factor</p>
            <p className="text-emerald-400 font-medium">≥ 1.0</p>
          </div>
        </div>
      </div>
    </div>
  )
}

// ========== Social Proof Tab ==========

function SocialTab({ items }: { items: SocialProofItem[] }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Social Proof</h2>
        <Button variant="outline" size="sm">
          <Eye className="w-4 h-4 mr-2" />
          Ver cola de moderación
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {items.map(item => (
          <div key={item.id} className="bg-white/5 border border-white/10 rounded-xl p-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
                <Heart className="w-5 h-5 text-emerald-400" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-white font-medium text-sm">{item.customer_name || 'Cliente anónimo'}</p>
                  {item.rating && (
                    <div className="flex items-center gap-0.5">
                      {Array.from({ length: item.rating }).map((_, i) => (
                        <Star key={i} className="w-3 h-3 text-amber-400 fill-amber-400" />
                      ))}
                    </div>
                  )}
                </div>
                <p className="text-white/60 text-sm mt-1 line-clamp-3">"{item.content}"</p>
                {item.ai_summary && (
                  <p className="text-emerald-400/60 text-xs mt-2">{item.ai_summary}</p>
                )}
                <div className="flex items-center gap-3 mt-2 text-xs text-white/30">
                  <span className="capitalize">{item.item_type.replace('_', ' ')}</span>
                  <span>•</span>
                  <span>Usado {item.usage_count}x</span>
                  <span>•</span>
                  <span>Sentiment: {(item.sentiment_score * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>
          </div>
        ))}
        {items.length === 0 && (
          <div className="col-span-full text-center py-12">
            <Star className="w-12 h-12 text-white/10 mx-auto mb-4" />
            <p className="text-white/40">No hay social proof aprobado aún</p>
          </div>
        )}
      </div>
    </div>
  )
}

// ========== Sequences Tab ==========

function SequencesTab({ sequences }: { sequences: ValueSequence[] }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Secuencias de Valor</h2>
        <Button variant="primary" size="sm">
          <MessageCircle className="w-4 h-4 mr-2" />
          Nueva Secuencia
        </Button>
      </div>

      <div className="grid gap-3">
        {sequences.map(seq => (
          <div key={seq.id} className="bg-white/5 border border-white/10 rounded-xl p-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-white font-medium">{seq.name}</h3>
                <p className="text-white/50 text-sm">{seq.topic}</p>
                <div className="flex items-center gap-3 mt-2 text-xs text-white/40">
                  <span>{seq.message_count} mensajes</span>
                  <span>•</span>
                  <span>{seq.total_duration_days} días</span>
                  <span>•</span>
                  <span className="capitalize">target: {seq.target_segment}</span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-white font-medium">{seq.times_started}</p>
                <p className="text-white/30 text-xs">inicios</p>
                <p className="text-emerald-400 font-medium mt-1">{seq.conversion_rate.toFixed(1)}%</p>
                <p className="text-white/30 text-xs">conversion</p>
              </div>
            </div>
          </div>
        ))}
        {sequences.length === 0 && (
          <div className="text-center py-12">
            <MessageCircle className="w-12 h-12 text-white/10 mx-auto mb-4" />
            <p className="text-white/40">No hay secuencias de valor creadas</p>
          </div>
        )}
      </div>
    </div>
  )
}

// Custom icon component
function Magnet(props: any) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="m6 15-4-4 6.75-6.77a7.79 7.79 0 0 1 11 11L13 22l-4-4" />
      <path d="m5 8 4 4" />
      <path d="m14 17 4 4" />
      <path d="m2 12 10-10" />
      <path d="M7 21 18 10" />
      <path d="m11 11 1 1" />
    </svg>
  )
}
