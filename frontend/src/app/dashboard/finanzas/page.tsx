'use client'

import { logger } from '@/lib/logger';
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { businessApi } from '@/lib/business'
import { ordersApi, RevenueSummary, AttributionSummary } from '@/lib/orders'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import {
  CircleDollarSign, TrendingUp, ShoppingBag, CreditCard,
  RotateCcw, Loader2, ArrowUpRight, ArrowDownRight
} from 'lucide-react'

const COLORS = ['#FF6B35', '#3B82F6', '#00D4AA', '#F59E0B', '#8B5CF6', '#EC4899', '#22C55E']

export default function FinanzasPage() {
  const [businesses, setBusinesses] = useState<any[]>([])
  const [selectedBusinessId, setSelectedBusinessId] = useState('')
  const [days, setDays] = useState(30)
  const [revenue, setRevenue] = useState<RevenueSummary | null>(null)
  const [attribution, setAttribution] = useState<AttributionSummary | null>(null)
  const [loading, setLoading] = useState(true)

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
  }, [selectedBusinessId, days])

  const loadData = async () => {
    setLoading(true)
    try {
      const [revData, attrData] = await Promise.all([
        ordersApi.getRevenueSummary(selectedBusinessId, days),
        ordersApi.getAttribution(selectedBusinessId, days),
      ])
      setRevenue(revData)
      setAttribution(attrData)
    } catch (e) {
      logger.error(String(e))
    } finally {
      setLoading(false)
    }
  }

  const channelData = revenue ? Object.entries(revenue.revenue_by_channel).map(([name, value]) => ({ name, value })) : []
  const platformData = revenue ? Object.entries(revenue.revenue_by_platform).map(([name, value]) => ({ name, value })) : []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <CircleDollarSign className="w-6 h-6 text-brand-orange" />
            Finanzas
          </h1>
          <p className="text-sm text-white/40 mt-1">Ingresos, atribución y métricas de ventas.</p>
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
          <select
            value={days}
            onChange={e => setDays(Number(e.target.value))}
            className="px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
          >
            <option value={7} className="bg-[#0A0E1A]">Últimos 7 días</option>
            <option value={30} className="bg-[#0A0E1A]">Últimos 30 días</option>
            <option value={90} className="bg-[#0A0E1A]">Últimos 90 días</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20 text-white/30">
          <Loader2 className="w-6 h-6 animate-spin mr-2" />
          Cargando finanzas...
        </div>
      ) : revenue && attribution ? (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <KPICard icon={<CircleDollarSign className="w-4 h-4" />} label="Ingresos" value={`$${revenue.total_revenue.toLocaleString()}`} color="#22C55E" />
            <KPICard icon={<ShoppingBag className="w-4 h-4" />} label="Órdenes" value={revenue.total_orders} color="#3B82F6" />
            <KPICard icon={<TrendingUp className="w-4 h-4" />} label="Ticket Promedio" value={`$${revenue.avg_order_value.toFixed(0)}`} color="#00D4AA" />
            <KPICard icon={<CreditCard className="w-4 h-4" />} label="Pagados" value={revenue.paid_orders} color="#F59E0B" />
          </div>

          {/* Charts Row 1 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Revenue Trend */}
            <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06]">
              <h3 className="text-sm font-semibold text-white mb-4">Tendencia de Ingresos</h3>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={revenue.revenue_trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="date" stroke="rgba(255,255,255,0.2)" fontSize={10} tickFormatter={(v) => v.slice(5)} />
                  <YAxis stroke="rgba(255,255,255,0.2)" fontSize={10} tickFormatter={(v) => `$${v}`} />
                  <Tooltip
                    contentStyle={{ background: '#0A0E1A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                    labelStyle={{ color: 'rgba(255,255,255,0.5)' }}
                    itemStyle={{ color: '#22C55E' }}
                    formatter={(value: any) => [`$${Number(value).toLocaleString()}`, 'Ingresos']}
                  />
                  <Line type="monotone" dataKey="revenue" stroke="#22C55E" strokeWidth={2} dot={{ r: 3, fill: '#22C55E' }} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Revenue by Channel */}
            <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06]">
              <h3 className="text-sm font-semibold text-white mb-4">Ingresos por Canal</h3>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie data={channelData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} labelLine={false} label={(props: any) => `${props.name || ''}: ${((props.percent || 0) * 100).toFixed(0)}%`}>
                    {channelData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: '#0A0E1A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                    formatter={(value: any) => `$${Number(value).toLocaleString()}`}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Charts Row 2 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Revenue by Platform */}
            <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06]">
              <h3 className="text-sm font-semibold text-white mb-4">Ingresos por Plataforma</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={platformData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="name" stroke="rgba(255,255,255,0.2)" fontSize={10} />
                  <YAxis stroke="rgba(255,255,255,0.2)" fontSize={10} tickFormatter={(v) => `$${v}`} />
                  <Tooltip
                    contentStyle={{ background: '#0A0E1A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                    formatter={(value: any) => `$${Number(value).toLocaleString()}`}
                  />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {platformData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Attribution Summary */}
            <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06]">
              <h3 className="text-sm font-semibold text-white mb-4">Atribución por Canal</h3>
              <div className="space-y-3">
                {attribution.by_channel.map((ch, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-white/70 capitalize">{ch.channel}</span>
                        <span className="text-xs text-white font-medium">${ch.revenue.toLocaleString()}</span>
                      </div>
                      <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${(ch.revenue / (attribution.total_revenue || 1)) * 100}%` }}
                          className="h-full rounded-full"
                          style={{ background: COLORS[i % COLORS.length] }}
                        />
                      </div>
                    </div>
                    <span className="text-[10px] text-white/30">{ch.orders} órdenes</span>
                  </div>
                ))}
                {attribution.by_channel.length === 0 && (
                  <p className="text-xs text-white/20 text-center py-4">Sin datos de atribución aún</p>
                )}
              </div>
            </div>
          </div>

          {/* First vs Last Touch */}
          <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06]">
            <h3 className="text-sm font-semibold text-white mb-4">First Touch vs Last Touch</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-white/30 mb-2">First Touch (dónde descubrieron tu negocio)</p>
                <div className="space-y-2">
                  {Object.entries(attribution.first_touch_revenue).map(([channel, amount]) => (
                    <div key={channel} className="flex items-center justify-between p-2 rounded-lg bg-white/5">
                      <span className="text-xs text-white/70 capitalize">{channel}</span>
                      <span className="text-xs text-white font-medium">${amount.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-xs text-white/30 mb-2">Last Touch (dónde compraron)</p>
                <div className="space-y-2">
                  {Object.entries(attribution.last_touch_revenue).map(([channel, amount]) => (
                    <div key={channel} className="flex items-center justify-between p-2 rounded-lg bg-white/5">
                      <span className="text-xs text-white/70 capitalize">{channel}</span>
                      <span className="text-xs text-white font-medium">${amount.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </>
      ) : null}
    </div>
  )
}

function KPICard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string | number; color: string }) {
  return (
    <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06]">
      <div className="flex items-center gap-1.5 mb-2">
        <span style={{ color }}>{icon}</span>
        <span className="text-[10px] font-medium text-white/30 uppercase tracking-wider">{label}</span>
      </div>
      <p className="text-xl font-bold text-white">{value}</p>
    </div>
  )
}
