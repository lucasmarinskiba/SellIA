'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { logger } from '@/lib/logger'
import { businessApi } from '@/lib/business'
import {
  financeApi,
  FinanceDashboard,
  FinanceAutopilotStatus,
  CashFlowForecast,
  TaxReport,
  DunningPipeline,
} from '@/lib/finance'
import {
  Banknote, AlertTriangle, TrendingUp, PieChart,
  Send, Bell, Download, Loader2, RefreshCw,
  ChevronRight, ToggleLeft, ToggleRight,
} from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart,
} from 'recharts'

const COLORS = {
  green: '#22C55E',
  red: '#EF4444',
  orange: '#F59E0B',
  blue: '#3B82F6',
  purple: '#8B5CF6',
}

export default function FinanzasAutopilotPage() {
  const router = useRouter()
  const [businesses, setBusinesses] = useState<any[]>([])
  const [selectedBusinessId, setSelectedBusinessId] = useState('')
  const [dashboard, setDashboard] = useState<FinanceDashboard | null>(null)
  const [status, setStatus] = useState<FinanceAutopilotStatus | null>(null)
  const [cashFlow, setCashFlow] = useState<CashFlowForecast | null>(null)
  const [taxReport, setTaxReport] = useState<TaxReport | null>(null)
  const [dunning, setDunning] = useState<DunningPipeline | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [reportMonth, setReportMonth] = useState(new Date().getMonth() + 1)
  const [reportYear, setReportYear] = useState(new Date().getFullYear())

  useEffect(() => {
    businessApi.list().then(data => {
      setBusinesses(data)
      if (data.length > 0) setSelectedBusinessId(data[0].id)
    }).catch(() => {})
  }, [])

  const loadData = useCallback(async (silent = false) => {
    if (!selectedBusinessId) return
    if (!silent) setLoading(true)
    else setRefreshing(true)
    try {
      const [dash, stat, cf, dp] = await Promise.all([
        financeApi.getDashboard(selectedBusinessId).catch(() => null),
        financeApi.getAutopilotStatus(selectedBusinessId).catch(() => null),
        financeApi.getCashFlow(selectedBusinessId, 30).catch(() => null),
        financeApi.getDunningPipeline(selectedBusinessId).catch(() => null),
      ])
      setDashboard(dash)
      setStatus(stat)
      setCashFlow(cf)
      setDunning(dp)
      // Load tax report for current selection
      const tr = await financeApi.getTaxReport(selectedBusinessId, reportMonth, reportYear).catch(() => null)
      setTaxReport(tr)
    } catch (e) {
      logger.error(String(e))
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [selectedBusinessId, reportMonth, reportYear])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleToggle = async () => {
    if (!selectedBusinessId) return
    setActionLoading('toggle')
    try {
      const res = await financeApi.toggleAutopilot(selectedBusinessId)
      setStatus(prev => prev ? { ...prev, is_active: res.is_active } : null)
    } catch (e) {
      logger.error(String(e))
    } finally {
      setActionLoading(null)
    }
  }

  const handleTriggerDelivery = async () => {
    if (!selectedBusinessId) return
    setActionLoading('delivery')
    try {
      await financeApi.triggerDelivery(selectedBusinessId)
      await loadData(true)
    } catch (e) {
      logger.error(String(e))
    } finally {
      setActionLoading(null)
    }
  }

  const handleTriggerDunning = async () => {
    if (!selectedBusinessId) return
    setActionLoading('dunning')
    try {
      await financeApi.triggerDunning(selectedBusinessId)
      await loadData(true)
    } catch (e) {
      logger.error(String(e))
    } finally {
      setActionLoading(null)
    }
  }

  const handleLoadTaxReport = async () => {
    if (!selectedBusinessId) return
    setActionLoading('tax')
    try {
      const tr = await financeApi.getTaxReport(selectedBusinessId, reportMonth, reportYear)
      setTaxReport(tr)
    } catch (e) {
      logger.error(String(e))
    } finally {
      setActionLoading(null)
    }
  }

  const formatCurrency = (v: number) => `$${(v || 0).toLocaleString('es-AR')}`

  const negativeDay = cashFlow?.daily_projection.find(d => d.projected_inflow < 0)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Banknote className="w-6 h-6 text-brand-orange" />
            Autopilot Financiero
          </h1>
          <p className="text-sm text-white/40 mt-1">Tu contador, cobrador y tesorero 24/7</p>
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
            onClick={() => loadData(true)}
            disabled={refreshing}
            className="p-2.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-white/40 hover:text-white transition-all disabled:opacity-30"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Autopilot Toggle */}
      <div className="flex items-center justify-between p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${status?.is_active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-white/5 text-white/30'}`}>
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <p className="text-white font-medium text-sm">Autopilot activo</p>
            <p className="text-white/30 text-xs">
              {status?.is_active ? 'Facturación, cobranza y reporting automáticos' : 'Autopilot financiero desactivado'}
            </p>
          </div>
        </div>
        <button
          onClick={handleToggle}
          disabled={actionLoading === 'toggle'}
          className="flex items-center gap-2 transition-opacity disabled:opacity-50"
        >
          {status?.is_active ? (
            <ToggleRight className="w-10 h-10 text-emerald-400" />
          ) : (
            <ToggleLeft className="w-10 h-10 text-white/20" />
          )}
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20 text-white/30">
          <Loader2 className="w-6 h-6 animate-spin mr-2" />
          Cargando autopilot financiero...
        </div>
      ) : dashboard ? (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatCard
              icon={<Banknote className="w-4 h-4" />}
              label="Por cobrar"
              value={formatCurrency(dashboard.total_receivables)}
              sub={`${dashboard.invoice_count} facturas`}
              color={COLORS.blue}
            />
            <StatCard
              icon={<AlertTriangle className="w-4 h-4" />}
              label="Vencidas"
              value={formatCurrency(dashboard.overdue_amount)}
              sub={`${dashboard.overdue_count} facturas`}
              color={COLORS.red}
            />
            <StatCard
              icon={<TrendingUp className="w-4 h-4" />}
              label="Flujo proyectado (30 días)"
              value={formatCurrency(cashFlow?.daily_projection.reduce((s, d) => s + d.projected_inflow, 0) || 0)}
              sub="Proyección estimada"
              color={COLORS.green}
            />
            <StatCard
              icon={<PieChart className="w-4 h-4" />}
              label="Tasa de cobranza"
              value={`${(dashboard.collection_rate || 0).toFixed(1)}%`}
              sub="Últimos 30 días"
              color={COLORS.orange}
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Dunning Pipeline */}
            <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06]">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-white">Pipeline de Cobranza</h3>
                <button
                  onClick={handleTriggerDunning}
                  disabled={actionLoading === 'dunning'}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-orange/20 hover:bg-brand-orange/30 text-brand-orange text-xs font-medium transition-colors disabled:opacity-50"
                >
                  {actionLoading === 'dunning' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Bell className="w-3 h-3" />}
                  Enviar recordatorios ahora
                </button>
              </div>
              <div className="space-y-2">
                {dunning && [
                  { key: 'level_1', color: COLORS.green },
                  { key: 'level_2', color: COLORS.orange },
                  { key: 'level_3', color: '#F97316' },
                  { key: 'level_4', color: COLORS.red },
                ].map(({ key, color }) => {
                  const item = dunning[key as keyof DunningPipeline]
                  return (
                    <div key={key} className="flex items-center gap-3 p-3 rounded-xl bg-white/5">
                      <div className="w-2 h-2 rounded-full" style={{ background: color }} />
                      <div className="flex-1">
                        <p className="text-xs text-white/70">{item.label}</p>
                        <p className="text-xs text-white/30">{item.count} facturas</p>
                      </div>
                      <p className="text-sm font-semibold text-white">{formatCurrency(item.amount)}</p>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Cash Flow Chart */}
            <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06]">
              <h3 className="text-sm font-semibold text-white mb-4">Proyección de Flujo de Caja</h3>
              {cashFlow && cashFlow.daily_projection.length > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={220}>
                    <AreaChart data={cashFlow.daily_projection}>
                      <defs>
                        <linearGradient id="flowGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={COLORS.green} stopOpacity={0.3} />
                          <stop offset="95%" stopColor={COLORS.green} stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="date" stroke="rgba(255,255,255,0.2)" fontSize={10} tickFormatter={(v) => v.slice(5)} />
                      <YAxis stroke="rgba(255,255,255,0.2)" fontSize={10} tickFormatter={(v) => `$${v}`} />
                      <Tooltip
                        contentStyle={{ background: '#0A0E1A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                        labelStyle={{ color: 'rgba(255,255,255,0.5)' }}
                        itemStyle={{ color: COLORS.green }}
                        formatter={(value: any) => [`$${Number(value).toLocaleString()}`, 'Ingreso proyectado']}
                      />
                      <Area type="monotone" dataKey="projected_inflow" stroke={COLORS.green} strokeWidth={2} fill="url(#flowGradient)" />
                    </AreaChart>
                  </ResponsiveContainer>
                  {negativeDay && (
                    <div className="mt-3 flex items-start gap-2 p-2.5 rounded-lg bg-red-500/10 border border-red-500/20">
                      <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                      <p className="text-xs text-red-300">
                        ⚠️ Flujo negativo proyectado el día {negativeDay.date.slice(8)}. ¿Activar promoción?
                      </p>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-xs text-white/20 text-center py-10">Sin datos de proyección aún</p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Recent Activity */}
            <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06]">
              <h3 className="text-sm font-semibold text-white mb-4">Actividad Reciente</h3>
              <div className="space-y-3">
                {dashboard.dunning_active > 0 ? (
                  <ActivityRow
                    icon={<Bell className="w-3.5 h-3.5 text-amber-400" />}
                    text={`${dashboard.dunning_active} recordatorios de cobranza enviados recientemente`}
                    time="Últimos 30 días"
                  />
                ) : null}
                {dashboard.overdue_count > 0 ? (
                  <ActivityRow
                    icon={<AlertTriangle className="w-3.5 h-3.5 text-red-400" />}
                    text={`${dashboard.overdue_count} facturas vencidas requieren atención`}
                    time="Ahora"
                  />
                ) : (
                  <ActivityRow
                    icon={<TrendingUp className="w-3.5 h-3.5 text-emerald-400" />}
                    text="Sin facturas vencidas. ¡Excelente trabajo!"
                    time="Ahora"
                  />
                )}
                <ActivityRow
                  icon={<Banknote className="w-3.5 h-3.5 text-blue-400" />}
                  text={`${dashboard.invoice_count} facturas pendientes de cobro`}
                  time="Ahora"
                />
                {dashboard.autopilot_active && (
                  <ActivityRow
                    icon={<Send className="w-3.5 h-3.5 text-brand-orange" />}
                    text="Autopilot financiero activo: entrega y cobranza automáticas"
                    time="Siempre"
                  />
                )}
              </div>
              <button
                onClick={handleTriggerDelivery}
                disabled={actionLoading === 'delivery'}
                className="mt-4 w-full py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-white/60 hover:text-white text-xs font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {actionLoading === 'delivery' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />}
                Entregar facturas pendientes ahora
              </button>
            </div>

            {/* Tax Report Card */}
            <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06]">
              <h3 className="text-sm font-semibold text-white mb-4">Reporte de Impuestos</h3>
              <div className="flex items-center gap-2 mb-4">
                <select
                  value={reportMonth}
                  onChange={e => setReportMonth(Number(e.target.value))}
                  className="px-2 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs text-white focus:outline-none"
                >
                  {Array.from({ length: 12 }, (_, i) => i + 1).map(m => (
                    <option key={m} value={m} className="bg-[#0A0E1A]">{m.toString().padStart(2, '0')}</option>
                  ))}
                </select>
                <select
                  value={reportYear}
                  onChange={e => setReportYear(Number(e.target.value))}
                  className="px-2 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs text-white focus:outline-none"
                >
                  {[2024, 2025, 2026].map(y => (
                    <option key={y} value={y} className="bg-[#0A0E1A]">{y}</option>
                  ))}
                </select>
                <button
                  onClick={handleLoadTaxReport}
                  disabled={actionLoading === 'tax'}
                  className="ml-auto px-3 py-1.5 rounded-lg bg-brand-orange/20 hover:bg-brand-orange/30 text-brand-orange text-xs font-medium transition-colors disabled:opacity-50"
                >
                  {actionLoading === 'tax' ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Calcular'}
                </button>
              </div>

              {taxReport ? (
                <div className="space-y-2">
                  <TaxRow label="Total facturado" value={formatCurrency(taxReport.total_invoiced)} />
                  <TaxRow label="IVA Débito" value={formatCurrency(taxReport.iva_debito)} />
                  <TaxRow label="IVA Crédito" value={formatCurrency(taxReport.iva_credito)} />
                  <div className="h-px bg-white/10 my-2" />
                  <TaxRow label="Saldo" value={formatCurrency(taxReport.saldo)} highlight />
                  <p className="text-[10px] text-white/20 mt-2">{taxReport.invoice_count} facturas en el período</p>
                </div>
              ) : (
                <p className="text-xs text-white/20 text-center py-4">Seleccioná un período para ver el reporte</p>
              )}

              <button
                onClick={() => {
                  if (!taxReport) return
                  const blob = new Blob([JSON.stringify(taxReport, null, 2)], { type: 'application/json' })
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement('a')
                  a.href = url
                  a.download = `tax-report-${taxReport.period}.json`
                  a.click()
                  URL.revokeObjectURL(url)
                }}
                disabled={!taxReport}
                className="mt-4 w-full py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-white/60 hover:text-white text-xs font-medium transition-colors disabled:opacity-30 flex items-center justify-center gap-2"
              >
                <Download className="w-3 h-3" />
                Descargar reporte
              </button>
            </div>
          </div>
        </>
      ) : null}
    </div>
  )
}

function StatCard({ icon, label, value, sub, color }: { icon: React.ReactNode; label: string; value: string; sub: string; color: string }) {
  return (
    <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06]">
      <div className="flex items-center gap-1.5 mb-2">
        <span style={{ color }}>{icon}</span>
        <span className="text-[10px] font-medium text-white/30 uppercase tracking-wider">{label}</span>
      </div>
      <p className="text-xl font-bold text-white">{value}</p>
      <p className="text-[10px] text-white/30 mt-0.5">{sub}</p>
    </div>
  )
}

function ActivityRow({ icon, text, time }: { icon: React.ReactNode; text: string; time: string }) {
  return (
    <div className="flex items-start gap-3 p-2.5 rounded-lg bg-white/5">
      <div className="mt-0.5">{icon}</div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-white/70 leading-relaxed">{text}</p>
        <p className="text-[10px] text-white/20 mt-0.5">{time}</p>
      </div>
    </div>
  )
}

function TaxRow({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <span className={`text-xs ${highlight ? 'text-white font-medium' : 'text-white/50'}`}>{label}</span>
      <span className={`text-xs font-medium ${highlight ? 'text-brand-orange' : 'text-white'}`}>{value}</span>
    </div>
  )
}
