'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { businessApi } from '@/lib/business'
import { biApi, FunnelMetrics, InsightAlert } from '@/lib/bi'
import {
  Brain, TrendingUp, AlertTriangle, Loader2, AlertCircle, X,
  Filter, BarChart3, Lightbulb, ArrowUpRight, ArrowDownRight, Minus
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts'

const COLORS = ['#FF6B35', '#7C3AED', '#00D4AA', '#0EA5E9', '#F59E0B', '#EC4899']

const SEVERITY_ICONS: Record<string, any> = {
  critical: AlertTriangle,
  warning: AlertTriangle,
  info: Lightbulb,
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'text-red-400',
  warning: 'text-yellow-400',
  info: 'text-blue-400',
}

export default function InteligenciaPage() {
  const [businesses, setBusinesses] = useState<any[]>([])
  const [selectedBusinessId, setSelectedBusinessId] = useState('')
  const [funnel, setFunnel] = useState<FunnelMetrics | null>(null)
  const [insights, setInsights] = useState<InsightAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

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
      const [funnelData, insightsData] = await Promise.all([
        biApi.getLatestFunnel(selectedBusinessId),
        biApi.getInsights(selectedBusinessId),
      ])
      setFunnel(funnelData)
      setInsights(insightsData)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al cargar inteligencia de negocios')
    } finally {
      setLoading(false)
    }
  }

  const funnelStages = funnel ? [
    { name: 'Leads', value: funnel.leads_count, color: '#0EA5E9' },
    { name: 'Calificados', value: funnel.qualified_count, color: '#7C3AED' },
    { name: 'Deals', value: funnel.deals_count, color: '#F59E0B' },
    { name: 'Órdenes', value: funnel.orders_count, color: '#00D4AA' },
    { name: 'Repetición', value: funnel.repeat_orders_count, color: '#FF6B35' },
  ] : []

  const conversionRates = funnel ? [
    { name: 'Lead → Calif', value: funnel.conversion_lead_to_qualified },
    { name: 'Calif → Deal', value: funnel.conversion_qualified_to_deal },
    { name: 'Deal → Orden', value: funnel.conversion_deal_to_order },
    { name: 'Orden → Repet', value: funnel.conversion_order_to_repeat },
  ] : []

  return (
    <div className="space-y-8 max-w-7xl">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">🧠 Inteligencia de Negocios</h1>
          <p className="text-sm text-white/40">Funnel, insights y predicciones de tu empresa virtual.</p>
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
          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KpiCard label="Ingresos" value={funnel ? `$${funnel.revenue_total.toLocaleString()}` : '$0'} color="#22C55E" icon={TrendingUp} />
            <KpiCard label="Ticket Promedio" value={funnel ? `$${funnel.avg_order_value.toFixed(0)}` : '$0'} color="#3B82F6" icon={BarChart3} />
            <KpiCard label="Leads" value={funnel ? funnel.leads_count.toLocaleString() : '0'} color="#0EA5E9" icon={Filter} />
            <KpiCard label="Órdenes" value={funnel ? funnel.orders_count.toLocaleString() : '0'} color="#FF6B35" icon={TrendingUp} />
          </div>

          {/* Funnel Charts */}
          {funnel && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-card p-5"
              >
                <div className="flex items-center gap-2 mb-4">
                  <Filter className="w-4 h-4 text-white/30" />
                  <h3 className="text-sm font-semibold text-white/70">Funnel de Conversión</h3>
                </div>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={funnelStages} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis type="number" tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 11 }} stroke="rgba(255,255,255,0.1)" />
                    <YAxis dataKey="name" type="category" tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }} stroke="rgba(255,255,255,0.1)" width={90} />
                    <Tooltip contentStyle={{ background: '#0A0E1A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', color: '#fff' }} />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                      {funnelStages.map((entry, index) => (
                        <Cell key={index} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-card p-5"
              >
                <div className="flex items-center gap-2 mb-4">
                  <TrendingUp className="w-4 h-4 text-white/30" />
                  <h3 className="text-sm font-semibold text-white/70">Tasas de Conversión</h3>
                </div>
                <div className="space-y-4 py-2">
                  {conversionRates.map((rate) => (
                    <div key={rate.name} className="space-y-1">
                      <div className="flex justify-between text-xs text-white/60">
                        <span>{rate.name}</span>
                        <span className="font-medium text-white">{rate.value.toFixed(1)}%</span>
                      </div>
                      <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${Math.min(rate.value, 100)}%` }}
                          className="h-full rounded-full bg-brand-orange"
                          transition={{ duration: 0.8 }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            </div>
          )}

          {/* Insights */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-white/80 flex items-center gap-2">
              <Brain className="w-5 h-5 text-brand-violet" />
              Insights de IA
              <span className="text-xs text-white/30 font-normal ml-2">({insights.length})</span>
            </h2>
            <div className="space-y-3">
              {insights.map(insight => {
                const Icon = SEVERITY_ICONS[insight.severity] || Lightbulb
                const color = SEVERITY_COLORS[insight.severity] || 'text-white/40'
                return (
                  <motion.div
                    key={insight.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="glass-card p-4 border-l-4"
                    style={{ borderLeftColor: insight.severity === 'critical' ? '#EF4444' : insight.severity === 'warning' ? '#F59E0B' : '#3B82F6' }}
                  >
                    <div className="flex items-start gap-3">
                      <Icon className={`w-5 h-5 mt-0.5 shrink-0 ${color}`} />
                      <div className="flex-1">
                        <h3 className="text-sm font-semibold text-white">{insight.title}</h3>
                        <p className="text-xs text-white/40 mt-1">{insight.description}</p>
                        {insight.recommended_action && (
                          <p className="text-xs text-brand-orange mt-2">💡 {insight.recommended_action}</p>
                        )}
                        {insight.metric_change_percent && (
                          <div className="flex items-center gap-1 mt-2">
                            {insight.metric_change_percent > 0 ? (
                              <ArrowUpRight className="w-3 h-3 text-brand-teal" />
                            ) : insight.metric_change_percent < 0 ? (
                              <ArrowDownRight className="w-3 h-3 text-red-400" />
                            ) : (
                              <Minus className="w-3 h-3 text-white/30" />
                            )}
                            <span className={`text-xs font-medium ${insight.metric_change_percent > 0 ? 'text-brand-teal' : insight.metric_change_percent < 0 ? 'text-red-400' : 'text-white/30'}`}>
                              {insight.metric_change_percent > 0 ? '+' : ''}{insight.metric_change_percent.toFixed(1)}%
                            </span>
                          </div>
                        )}
                      </div>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-white/30 uppercase">
                        {insight.insight_type}
                      </span>
                    </div>
                  </motion.div>
                )
              })}
              {insights.length === 0 && (
                <div className="glass-card p-5 text-center text-white/20 text-sm">
                  No hay insights generados aún.
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function KpiCard({ label, value, color, icon: Icon }: { label: string; value: string; color: string; icon: any }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-5"
    >
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-4 h-4" style={{ color }} />
        <span className="text-[10px] font-medium text-white/30 uppercase tracking-wider">{label}</span>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
    </motion.div>
  )
}
