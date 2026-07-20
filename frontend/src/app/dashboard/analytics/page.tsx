'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { businessApi } from '@/lib/business'
import { analyticsApi, AnalyticsData, FunnelData, AttributionData } from '@/lib/analytics'
import {
  MessageSquare, Bot, Zap, TrendingUp, Users, Mail,
  Loader2, AlertCircle, X, BarChart3, ShoppingCart, Filter,
  DollarSign, MousePointerClick
} from 'lucide-react'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Legend, AreaChart, Area
} from 'recharts'

const COLORS = ['#FF6B35', '#7C3AED', '#00D4AA', '#0EA5E9', '#F59E0B', '#EC4899']

export default function AnalyticsPage() {
  const [businesses, setBusinesses] = useState<any[]>([])
  const [selectedBusinessId, setSelectedBusinessId] = useState<string>('')
  const [days, setDays] = useState(30)
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [funnelData, setFunnelData] = useState<FunnelData | null>(null)
  const [attributionData, setAttributionData] = useState<AttributionData | null>(null)
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
  }, [selectedBusinessId, days])

  const loadAll = async () => {
    setLoading(true)
    setError(null)
    try {
      const [analytics, funnel, attribution] = await Promise.all([
        analyticsApi.getAnalytics(selectedBusinessId, days),
        analyticsApi.getFunnel(selectedBusinessId, days),
        analyticsApi.getAttribution(selectedBusinessId, days),
      ])
      setData(analytics)
      setFunnelData(funnel)
      setAttributionData(attribution)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al cargar analytics')
    } finally {
      setLoading(false)
    }
  }

  const kpi = data?.kpi

  const channelData = data ? Object.entries(data.conversations_by_channel).map(([name, value]) => ({ name, value })) : []
  const workflowStatusData = data ? Object.entries(data.workflows.executions_by_status).map(([name, value]) => ({ name, value })) : []

  const funnelStages = funnelData ? [
    { name: 'Leads', value: funnelData.funnel.leads, color: '#0EA5E9' },
    { name: 'Calificados', value: funnelData.funnel.qualified, color: '#7C3AED' },
    { name: 'Propuestas', value: funnelData.funnel.proposals, color: '#F59E0B' },
    { name: 'Cerrados', value: funnelData.funnel.closed_won, color: '#00D4AA' },
    { name: 'Órdenes', value: funnelData.funnel.orders, color: '#FF6B35' },
  ] : []

  const attributionChannelData = attributionData?.by_channel?.slice(0, 6).map(c => ({
    name: c.channel,
    revenue: c.revenue,
    orders: c.orders,
  })) || []

  return (
    <div className="space-y-8 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">📊 Analytics</h1>
          <p className="text-sm text-white/40">Métricas de conversión, agentes y automatizaciones en tiempo real.</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={days}
            onChange={e => setDays(Number(e.target.value))}
            className="px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
          >
            <option value={7} className="bg-[#0A0E1A]">Últimos 7 días</option>
            <option value={30} className="bg-[#0A0E1A]">Últimos 30 días</option>
            <option value={90} className="bg-[#0A0E1A]">Últimos 90 días</option>
          </select>
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
      ) : data ? (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard icon={MessageSquare} label="Conversaciones" value={(kpi?.total_conversations ?? 0).toLocaleString()} color="text-brand-orange" bg="bg-brand-orange/10" trend={kpi?.trends.conversations ?? '0%'} />
            <KpiCard icon={Mail} label="Mensajes" value={(kpi?.total_messages ?? 0).toLocaleString()} color="text-brand-violet" bg="bg-brand-violet/10" trend={kpi?.trends.messages ?? '0%'} />
            <KpiCard icon={Zap} label="Ejecuciones Workflow" value={(kpi?.total_workflow_executions ?? 0).toLocaleString()} color="text-brand-teal" bg="bg-brand-teal/10" trend={kpi?.trends.executions ?? '0%'} />
            <KpiCard icon={Bot} label="Tokens IA" value={data.agents.total_tokens.toLocaleString()} color="text-blue-400" bg="bg-blue-400/10" trend="+5%" />
          </div>

          {/* Revenue KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard icon={DollarSign} label="Ingresos" value={`$${(kpi?.total_revenue ?? 0).toLocaleString()}`} color="text-green-400" bg="bg-green-400/10" trend={kpi?.trends.revenue ?? '0%'} />
            <KpiCard icon={ShoppingCart} label="Órdenes" value={(kpi?.total_orders ?? 0).toLocaleString()} color="text-pink-400" bg="bg-pink-400/10" trend={kpi?.trends.orders ?? '0%'} />
            <KpiCard icon={MousePointerClick} label="Tasa Conversión" value={`${(kpi?.conversion_rate ?? 0).toFixed(1)}%`} color="text-yellow-400" bg="bg-yellow-400/10" trend={kpi?.trends.orders ?? '0%'} />
            <KpiCard icon={BarChart3} label="Ticket Promedio" value={`$${(kpi?.avg_order_value ?? 0).toLocaleString()}`} color="text-cyan-400" bg="bg-cyan-400/10" trend={kpi?.trends.revenue ?? '0%'} />
          </div>

          {/* Charts Row 1 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <ChartCard title="Conversaciones por día" icon={TrendingUp}>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={data.conversations_trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="date" tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 11 }} stroke="rgba(255,255,255,0.1)" />
                  <YAxis tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 11 }} stroke="rgba(255,255,255,0.1)" />
                  <Tooltip
                    contentStyle={{ background: '#0A0E1A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', color: '#fff' }}
                  />
                  <Line type="monotone" dataKey="count" stroke="#FF6B35" strokeWidth={2} dot={{ fill: '#FF6B35', r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Workflows ejecutados por día" icon={Zap}>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={data.workflows.executions_trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="date" tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 11 }} stroke="rgba(255,255,255,0.1)" />
                  <YAxis tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 11 }} stroke="rgba(255,255,255,0.1)" />
                  <Tooltip
                    contentStyle={{ background: '#0A0E1A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', color: '#fff' }}
                  />
                  <Bar dataKey="count" fill="#7C3AED" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          {/* Funnel Section */}
          {funnelData && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-white/80 flex items-center gap-2">
                <Filter className="w-5 h-5 text-brand-orange" />
                Funnel de Conversión
              </h2>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
                <ChartCard title="Etapa del Funnel" icon={Filter}>
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={funnelStages} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis type="number" tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 11 }} stroke="rgba(255,255,255,0.1)" />
                      <YAxis dataKey="name" type="category" tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }} stroke="rgba(255,255,255,0.1)" width={90} />
                      <Tooltip
                        contentStyle={{ background: '#0A0E1A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', color: '#fff' }}
                      />
                      <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                        {funnelStages.map((entry, index) => (
                          <Cell key={index} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </ChartCard>

                <ChartCard title="Tasas de Conversión" icon={MousePointerClick}>
                  <div className="space-y-4 py-2">
                    {Object.entries(funnelData.conversion_rates).map(([key, value]) => {
                      const labels: Record<string, string> = {
                        lead_to_qualified: 'Lead → Calificado',
                        qualified_to_proposal: 'Calificado → Propuesta',
                        proposal_to_closed: 'Propuesta → Cerrado',
                        lead_to_order: 'Lead → Orden',
                        overall_conversion: 'Conversión Global',
                      }
                      return (
                        <div key={key} className="space-y-1">
                          <div className="flex justify-between text-xs text-white/60">
                            <span>{labels[key] || key}</span>
                            <span className="font-medium text-white">{value.toFixed(1)}%</span>
                          </div>
                          <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full bg-brand-orange transition-all"
                              style={{ width: `${Math.min(value, 100)}%` }}
                            />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </ChartCard>

                <ChartCard title="Tendencia Leads vs Órdenes" icon={TrendingUp}>
                  <ResponsiveContainer width="100%" height={260}>
                    <AreaChart data={funnelData.trend}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="date" tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10 }} stroke="rgba(255,255,255,0.1)" />
                      <YAxis tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 11 }} stroke="rgba(255,255,255,0.1)" />
                      <Tooltip contentStyle={{ background: '#0A0E1A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', color: '#fff' }} />
                      <Legend wrapperStyle={{ fontSize: 11, color: 'rgba(255,255,255,0.5)' }} />
                      <Area type="monotone" dataKey="leads" stackId="1" stroke="#0EA5E9" fill="#0EA5E9" fillOpacity={0.3} />
                      <Area type="monotone" dataKey="orders" stackId="2" stroke="#FF6B35" fill="#FF6B35" fillOpacity={0.3} />
                    </AreaChart>
                  </ResponsiveContainer>
                </ChartCard>
              </div>
            </div>
          )}

          {/* Attribution Section */}
          {attributionData && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-white/80 flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-brand-teal" />
                Atribución de Ingresos
              </h2>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                <ChartCard title="Ingresos por Canal" icon={BarChart3}>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={attributionChannelData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="name" tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 11 }} stroke="rgba(255,255,255,0.1)" />
                      <YAxis tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 11 }} stroke="rgba(255,255,255,0.1)" />
                      <Tooltip
                        contentStyle={{ background: '#0A0E1A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', color: '#fff' }}
                        formatter={(value: any, name: any) => [name === 'revenue' ? `$${Number(value).toLocaleString()}` : value, name === 'revenue' ? 'Ingresos' : 'Órdenes']}
                      />
                      <Legend wrapperStyle={{ fontSize: 11, color: 'rgba(255,255,255,0.5)' }} />
                      <Bar dataKey="revenue" fill="#FF6B35" radius={[4, 4, 0, 0]} name="Ingresos" />
                      <Bar dataKey="orders" fill="#7C3AED" radius={[4, 4, 0, 0]} name="Órdenes" />
                    </BarChart>
                  </ResponsiveContainer>
                </ChartCard>

                <ChartCard title="First Touch vs Last Touch" icon={MousePointerClick}>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart
                      data={(() => {
                        // Merge first_touch and last_touch by channel
                        const map: Record<string, { channel: string; first: number; last: number }> = {}
                        attributionData.first_touch.forEach(c => {
                          map[c.channel] = { channel: c.channel, first: c.revenue, last: 0 }
                        })
                        attributionData.last_touch.forEach(c => {
                          if (map[c.channel]) map[c.channel].last = c.revenue
                          else map[c.channel] = { channel: c.channel, first: 0, last: c.revenue }
                        })
                        return Object.values(map).slice(0, 6)
                      })()}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="channel" tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 11 }} stroke="rgba(255,255,255,0.1)" />
                      <YAxis tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 11 }} stroke="rgba(255,255,255,0.1)" />
                      <Tooltip
                        contentStyle={{ background: '#0A0E1A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', color: '#fff' }}
                        formatter={(value: any) => `$${Number(value).toLocaleString()}`}
                      />
                      <Legend wrapperStyle={{ fontSize: 11, color: 'rgba(255,255,255,0.5)' }} />
                      <Bar dataKey="first" fill="#00D4AA" radius={[4, 4, 0, 0]} name="First Touch" />
                      <Bar dataKey="last" fill="#0EA5E9" radius={[4, 4, 0, 0]} name="Last Touch" />
                    </BarChart>
                  </ResponsiveContainer>
                </ChartCard>
              </div>
            </div>
          )}

          {/* Charts Row 2 */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            <ChartCard title="Conversaciones por canal" icon={MessageSquare}>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={channelData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={4} dataKey="value">
                    {channelData.map((_, index) => (
                      <Cell key={index} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#0A0E1A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', color: '#fff' }} />
                  <Legend wrapperStyle={{ fontSize: 11, color: 'rgba(255,255,255,0.5)' }} />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Estado de ejecuciones" icon={Zap}>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={workflowStatusData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={4} dataKey="value">
                    {workflowStatusData.map((_, index) => (
                      <Cell key={index} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#0A0E1A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', color: '#fff' }} />
                  <Legend wrapperStyle={{ fontSize: 11, color: 'rgba(255,255,255,0.5)' }} />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Top Chatbot Rules" icon={Users}>
              <div className="space-y-3 overflow-y-auto max-h-[220px] no-scrollbar">
                {data.top_chatbot_rules.length === 0 && (
                  <p className="text-sm text-white/20 text-center py-8">Sin datos aún</p>
                )}
                {data.top_chatbot_rules.map((rule, i) => (
                  <div key={rule.name} className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-full bg-white/5 flex items-center justify-center text-[10px] font-bold text-white/40">{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-white/70 truncate">{rule.name}</p>
                      <div className="h-1.5 bg-white/5 rounded-full mt-1 overflow-hidden">
                        <div className="h-full rounded-full bg-brand-orange transition-all" style={{ width: `${Math.min((rule.usage / (data.top_chatbot_rules[0]?.usage || 1)) * 100, 100)}%` }} />
                      </div>
                    </div>
                    <span className="text-xs text-white/30">{rule.usage}</span>
                  </div>
                ))}
              </div>
            </ChartCard>
          </div>

          {/* AI Insights */}
          {data.insights && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card p-5 border-l-4 border-brand-orange"
            >
              <div className="flex items-start gap-3">
                <Bot className="w-5 h-5 text-brand-orange mt-0.5 shrink-0" />
                <div>
                  <h3 className="text-sm font-semibold text-white/80 mb-1">Insight de IA</h3>
                  <p className="text-sm text-white/60 leading-relaxed">{data.insights}</p>
                </div>
              </div>
            </motion.div>
          )}
        </>
      ) : (
        <div className="text-center py-20 text-white/20">
          <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p className="text-sm">Seleccioná un negocio para ver métricas</p>
        </div>
      )}
    </div>
  )
}

function KpiCard({ icon: Icon, label, value, color, bg, trend }: {
  icon: any; label: string; value: string; color: string; bg: string; trend: string
}) {
  const isPositive = trend.startsWith('+')
  const isNegative = trend.startsWith('-')
  const trendColor = isNegative ? 'text-red-400' : isPositive ? 'text-brand-teal' : 'text-white/40'
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-5"
    >
      <div className="flex items-center justify-between mb-3">
        <div className={`w-10 h-10 rounded-xl ${bg} flex items-center justify-center`}>
          <Icon className={`w-5 h-5 ${color}`} />
        </div>
        <span className={`text-xs font-medium ${trendColor}`}>{trend}</span>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-xs text-white/30 mt-1">{label}</p>
    </motion.div>
  )
}

function ChartCard({ title, icon: Icon, children }: {
  title: string; icon: any; children: React.ReactNode
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-5"
    >
      <div className="flex items-center gap-2 mb-4">
        <Icon className="w-4 h-4 text-white/30" />
        <h3 className="text-sm font-semibold text-white/70">{title}</h3>
      </div>
      {children}
    </motion.div>
  )
}
