'use client'

import { logger } from '@/lib/logger';
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { businessApi } from '@/lib/business'
import { crmApi, Deal, CRMSummary } from '@/lib/crm'
import Button from '@/components/ui/Button'
import {
  KanbanSquare, Plus, TrendingUp, DollarSign, Target, Flame,
  Snowflake, Thermometer, Loader2, Search
} from 'lucide-react'

const STAGE_CONFIG: Record<string, { label: string; color: string }> = {
  new_lead: { label: 'Nuevo Lead', color: '#3B82F6' },
  contacted: { label: 'Contactado', color: '#8B5CF6' },
  qualified: { label: 'Cualificado', color: '#00D4AA' },
  proposal_sent: { label: 'Propuesta', color: '#F59E0B' },
  negotiating: { label: 'Negociando', color: '#FF6B35' },
  closed_won: { label: 'Cerrado ✅', color: '#22C55E' },
  closed_lost: { label: 'Perdido ❌', color: '#EF4444' },
  nurture: { label: 'Nurture', color: '#64748B' },
}

export default function CRMPage() {
  const [businesses, setBusinesses] = useState<any[]>([])
  const [selectedBusinessId, setSelectedBusinessId] = useState('')
  const [deals, setDeals] = useState<Deal[]>([])
  const [summary, setSummary] = useState<CRMSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showAddModal, setShowAddModal] = useState(false)
  const [newDeal, setNewDeal] = useState({ title: '', value: '', contact_name: '', stage: 'new_lead' })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    businessApi.list().then(data => {
      setBusinesses(data)
      if (data.length > 0) setSelectedBusinessId(data[0].id)
    }).catch(() => {})
  }, [])

  useEffect(() => {
    if (!selectedBusinessId) return
    loadData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBusinessId])

  const loadData = async () => {
    setLoading(true)
    try {
      const [dealsData, summaryData] = await Promise.all([
        crmApi.getDeals(selectedBusinessId),
        crmApi.getSummary(selectedBusinessId),
      ])
      setDeals(dealsData)
      setSummary(summaryData)
    } catch (e) {
      logger.error(String(e))
    } finally {
      setLoading(false)
    }
  }

  const filteredDeals = deals.filter(d =>
    !search || d.title.toLowerCase().includes(search.toLowerCase()) ||
    (d.contact_name && d.contact_name.toLowerCase().includes(search.toLowerCase()))
  )

  const dealsByStage = Object.keys(STAGE_CONFIG).reduce((acc, stage) => {
    acc[stage] = filteredDeals.filter(d => d.stage === stage)
    return acc
  }, {} as Record<string, Deal[]>)

  const handleCreateDeal = async () => {
    if (!newDeal.title.trim() || !selectedBusinessId) return
    setSaving(true)
    try {
      await crmApi.createDeal({
        business_id: selectedBusinessId,
        title: newDeal.title,
        value: newDeal.value ? parseFloat(newDeal.value) : null,
        contact_name: newDeal.contact_name || null,
        stage: newDeal.stage,
        currency: 'ARS',
        description: null,
        contact_email: null,
        contact_phone: null,
        expected_close_date: null,
        extra_data: {},
        pipeline_id: null,
        conversation_id: null,
        probability: 10,
        priority: 0,
      })
      setShowAddModal(false)
      setNewDeal({ title: '', value: '', contact_name: '', stage: 'new_lead' })
      loadData()
    } catch (e) {
      logger.error(String(e))
    } finally {
      setSaving(false)
    }
  }

  const handleMoveDeal = async (dealId: string, newStage: string) => {
    try {
      await crmApi.moveDeal(dealId, newStage)
      loadData()
    } catch (e) {
      logger.error(String(e))
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <KanbanSquare className="w-6 h-6 text-brand-orange" />
            CRM Pipeline
          </h1>
          <p className="text-sm text-white/40 mt-1">Gestiona tus oportunidades de venta y el pipeline de leads.</p>
        </div>
        <div className="flex items-center gap-2">
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
          <Button onClick={() => setShowAddModal(true)} leftIcon={<Plus className="w-4 h-4" />}>
            Nuevo Deal
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          <KPICard icon={<Target className="w-4 h-4" />} label="Total Deals" value={summary.total_deals} color="#3B82F6" />
          <KPICard icon={<DollarSign className="w-4 h-4" />} label="Valor Total" value={`$${(summary.total_value || 0).toLocaleString()}`} color="#22C55E" />
          <KPICard icon={<TrendingUp className="w-4 h-4" />} label="Win Rate" value={`${(summary.win_rate || 0).toFixed(1)}%`} color="#00D4AA" />
          <KPICard icon={<Flame className="w-4 h-4" />} label="Hot Leads" value={summary.hot_leads} color="#FF6B35" />
          <KPICard icon={<Thermometer className="w-4 h-4" />} label="Warm Leads" value={summary.warm_leads} color="#F59E0B" />
          <KPICard icon={<Snowflake className="w-4 h-4" />} label="Cold Leads" value={summary.cold_leads} color="#64748B" />
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Buscar deals..."
          className="w-full max-w-md pl-9 pr-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
        />
      </div>

      {/* Kanban Board */}
      {loading ? (
        <div className="flex items-center justify-center py-20 text-white/30">
          <Loader2 className="w-6 h-6 animate-spin mr-2" />
          Cargando pipeline...
        </div>
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-4 no-scrollbar">
          {Object.entries(STAGE_CONFIG).map(([stageKey, config]) => {
            const stageDeals = dealsByStage[stageKey] || []
            return (
              <div key={stageKey} className="w-72 shrink-0">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ background: config.color }} />
                    <span className="text-sm font-medium text-white">{config.label}</span>
                  </div>
                  <span className="text-xs text-white/30 px-2 py-0.5 rounded-md bg-white/5">{stageDeals.length}</span>
                </div>
                <div className="space-y-2">
                  {stageDeals.map(deal => (
                    <motion.div
                      key={deal.id}
                      layout
                      className="p-3 rounded-xl border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04] transition-colors cursor-pointer group"
                    >
                      <div className="flex items-start justify-between mb-1.5">
                        <h4 className="text-sm font-medium text-white line-clamp-2">{deal.title}</h4>
                        {deal.priority >= 3 && <Flame className="w-3.5 h-3.5 text-brand-orange shrink-0 ml-1" />}
                      </div>
                      {deal.contact_name && (
                        <p className="text-xs text-white/30 mb-1.5">{deal.contact_name}</p>
                      )}
                      <div className="flex items-center justify-between">
                        {deal.value ? (
                          <span className="text-xs font-semibold" style={{ color: config.color }}>
                            ${Number(deal.value).toLocaleString()}
                          </span>
                        ) : (
                          <span />
                        )}
                        <span className="text-[10px] text-white/20">{deal.probability}% prob</span>
                      </div>
                      {/* Move buttons */}
                      <div className="flex gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity flex-wrap">
                        {Object.keys(STAGE_CONFIG).map(s => (
                          s !== deal.stage && (
                            <button
                              key={s}
                              onClick={() => handleMoveDeal(deal.id, s)}
                              className="px-1.5 py-0.5 rounded text-[9px] bg-white/5 text-white/40 hover:text-white/70 hover:bg-white/10 transition-colors"
                              title={`Mover a ${STAGE_CONFIG[s].label}`}
                            >
                              {STAGE_CONFIG[s].label.substring(0, 3)}
                            </button>
                          )
                        ))}
                      </div>
                    </motion.div>
                  ))}
                  {stageDeals.length === 0 && (
                    <div className="p-4 rounded-xl border border-dashed border-white/[0.06] text-center">
                      <p className="text-xs text-white/20">Sin deals</p>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Add Deal Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="w-full max-w-md p-6 rounded-2xl bg-[#0A0E1A] border border-white/[0.08] shadow-2xl"
          >
            <h3 className="text-lg font-semibold text-white mb-4">Nuevo Deal</h3>
            <div className="space-y-3">
              <input
                type="text"
                value={newDeal.title}
                onChange={e => setNewDeal({ ...newDeal, title: e.target.value })}
                placeholder="Título del deal *"
                className="w-full px-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
              />
              <input
                type="text"
                value={newDeal.contact_name}
                onChange={e => setNewDeal({ ...newDeal, contact_name: e.target.value })}
                placeholder="Nombre del contacto"
                className="w-full px-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
              />
              <input
                type="number"
                value={newDeal.value}
                onChange={e => setNewDeal({ ...newDeal, value: e.target.value })}
                placeholder="Valor estimado (ARS)"
                className="w-full px-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
              />
              <select
                value={newDeal.stage}
                onChange={e => setNewDeal({ ...newDeal, stage: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
              >
                {Object.entries(STAGE_CONFIG).map(([key, cfg]) => (
                  <option key={key} value={key} className="bg-[#0A0E1A]">{cfg.label}</option>
                ))}
              </select>
              <div className="flex gap-2 pt-2">
                <Button variant="secondary" onClick={() => setShowAddModal(false)} className="flex-1">Cancelar</Button>
                <Button onClick={handleCreateDeal} disabled={saving || !newDeal.title.trim()} className="flex-1">
                  {saving ? 'Guardando...' : 'Crear Deal'}
                </Button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}

function KPICard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string | number; color: string }) {
  return (
    <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.06]">
      <div className="flex items-center gap-1.5 mb-1.5">
        <span style={{ color }}>{icon}</span>
        <span className="text-[10px] font-medium text-white/30 uppercase tracking-wider">{label}</span>
      </div>
      <p className="text-lg font-bold text-white">{value}</p>
    </div>
  )
}
