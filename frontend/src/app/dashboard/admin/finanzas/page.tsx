'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { adminApi, RevenueSummary, BankTransferOrder, AdminSubscription, CancellationFeedback } from '@/lib/subscriptions'
import {
  DollarSign, TrendingUp, Users, AlertCircle, Loader2,
  CheckCircle2, XCircle, Clock, Calendar, CreditCard,
  Building, Bitcoin, Wallet, Search, Filter, ThumbsDown,
  MessageSquare, BarChart3, ArrowUpRight, ArrowDownRight,
} from 'lucide-react'

interface RetentionData {
  total_cancellations: number
  cancellations_this_month: number
  churn_rate_percent: number
  avg_nps: number | null
  top_reasons: { reason: string; count: number }[]
  top_competitors: { name: string; count: number }[]
}

export default function AdminFinanzasPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()

  const [revenue, setRevenue] = useState<RevenueSummary | null>(null)
  const [transfers, setTransfers] = useState<BankTransferOrder[]>([])
  const [subscriptions, setSubscriptions] = useState<AdminSubscription[]>([])
  const [retention, setRetention] = useState<RetentionData | null>(null)
  const [feedbacks, setFeedbacks] = useState<CancellationFeedback[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'overview' | 'transfers' | 'retention' | 'subscriptions'>('overview')
  const [transferFilter, setTransferFilter] = useState({ status: '', date_from: '', date_to: '' })
  const [approvingId, setApprovingId] = useState<string | null>(null)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
      return
    }
    if (!authLoading && user && !user.is_superuser) {
      router.push('/dashboard')
      return
    }
    if (user?.is_superuser) {
      loadAll()
    }
  }, [authLoading, user, router])

  const loadAll = async () => {
    setLoading(true)
    try {
      const [rev, ret, fb] = await Promise.all([
        adminApi.getRevenue(),
        adminApi.getRetention(),
        adminApi.getFeedbacks(),
      ])
      setRevenue(rev)
      setRetention(ret)
      setFeedbacks(fb.slice(0, 20))
      await loadTransfers()
      await loadSubscriptions()
    } catch (e: any) {
      if (e.response?.status === 403) router.push('/dashboard')
    } finally {
      setLoading(false)
    }
  }

  const loadTransfers = async () => {
    try {
      const data = await adminApi.getBankTransfers({
        status: transferFilter.status || undefined,
        date_from: transferFilter.date_from || undefined,
        date_to: transferFilter.date_to || undefined,
        limit: 50,
      })
      setTransfers(data)
    } catch {
      // silent
    }
  }

  const loadSubscriptions = async () => {
    try {
      const data = await adminApi.getSubscriptions({ limit: 50 })
      setSubscriptions(data)
    } catch {
      // silent
    }
  }

  const handleApprove = async (orderId: string, approved: boolean) => {
    setApprovingId(orderId)
    try {
      await adminApi.approveTransfer(orderId, { approved, notes: approved ? undefined : 'Rechazado por admin' })
      await loadTransfers()
      await loadAll()
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Error')
    } finally {
      setApprovingId(null)
    }
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <Loader2 className="w-8 h-8 text-brand-orange animate-spin" />
      </div>
    )
  }

  if (!user?.is_superuser) return null

  const tabs = [
    { id: 'overview' as const, label: 'Resumen', icon: BarChart3 },
    { id: 'transfers' as const, label: 'Transferencias', icon: Building },
    { id: 'retention' as const, label: 'Retención', icon: ThumbsDown },
    { id: 'subscriptions' as const, label: 'Suscripciones', icon: Users },
  ]

  return (
    <div className="min-h-screen bg-[#060812] text-white">
      <div className="max-w-7xl mx-auto px-6 py-10">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-brand-orange/10 border border-brand-orange/20 flex items-center justify-center">
            <DollarSign className="w-5 h-5 text-brand-orange" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Finanzas & Suscripciones</h1>
            <p className="text-sm text-white/40">Ingresos, transferencias y retención</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1 mb-8 p-1 rounded-xl bg-white/5 w-fit">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === tab.id ? 'bg-brand-orange text-white' : 'text-white/40 hover:text-white/60'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            )
          })}
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-brand-orange animate-spin" />
          </div>
        ) : (
          <>
            {/* OVERVIEW TAB */}
            {activeTab === 'overview' && revenue && (
              <div className="space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <StatCard icon={<TrendingUp className="w-4 h-4 text-brand-teal" />} label="MRR" value={`$${revenue.mrr.toLocaleString()}`} />
                  <StatCard icon={<TrendingUp className="w-4 h-4 text-brand-violet" />} label="ARR" value={`$${revenue.arr.toLocaleString()}`} />
                  <StatCard icon={<DollarSign className="w-4 h-4 text-brand-orange" />} label="Este mes" value={`$${revenue.revenue_this_month.toLocaleString()}`} />
                  <StatCard icon={<Users className="w-4 h-4 text-blue-400" />} label="Activas" value={revenue.active_subscriptions_count} />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
                    <p className="text-xs text-white/30 uppercase mb-3">Por método de pago (mes)</p>
                    <div className="space-y-2">
                      <ProviderRow icon={<Wallet className="w-4 h-4 text-brand-orange" />} label="MercadoPago" amount={revenue.revenue_by_provider.mercadopago || 0} />
                      <ProviderRow icon={<Building className="w-4 h-4 text-brand-teal" />} label="Transferencia" amount={revenue.revenue_by_provider.bank_transfer || 0} />
                      <ProviderRow icon={<Bitcoin className="w-4 h-4 text-brand-violet" />} label="Crypto" amount={revenue.revenue_by_provider.crypto || 0} />
                    </div>
                  </div>
                  <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
                    <p className="text-xs text-white/30 uppercase mb-3">Pendientes</p>
                    <p className="text-3xl font-bold text-white">{revenue.pending_transfers_count}</p>
                    <p className="text-sm text-white/40 mt-1">transferencias por confirmar</p>
                  </div>
                  <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
                    <p className="text-xs text-white/30 uppercase mb-3">Churn rate</p>
                    <p className="text-3xl font-bold text-white">{retention?.churn_rate_percent ?? 0}%</p>
                    <p className="text-sm text-white/40 mt-1">cancelaciones / activas</p>
                  </div>
                </div>
              </div>
            )}

            {/* TRANSFERS TAB */}
            {activeTab === 'transfers' && (
              <div className="space-y-4">
                <div className="flex flex-wrap items-center gap-3 p-4 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
                  <Filter className="w-4 h-4 text-brand-orange" />
                  <select
                    value={transferFilter.status}
                    onChange={(e) => setTransferFilter({ ...transferFilter, status: e.target.value })}
                    className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm focus:outline-none"
                  >
                    <option value="" className="bg-[#0a0e1a]">Todos los estados</option>
                    <option value="pending" className="bg-[#0a0e1a]">Pendiente</option>
                    <option value="paid" className="bg-[#0a0e1a]">Pagado</option>
                    <option value="confirmed" className="bg-[#0a0e1a]">Confirmado</option>
                    <option value="expired" className="bg-[#0a0e1a]">Expirado</option>
                    <option value="cancelled" className="bg-[#0a0e1a]">Cancelado</option>
                  </select>
                  <input type="date" value={transferFilter.date_from} onChange={(e) => setTransferFilter({ ...transferFilter, date_from: e.target.value })} className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm" />
                  <input type="date" value={transferFilter.date_to} onChange={(e) => setTransferFilter({ ...transferFilter, date_to: e.target.value })} className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm" />
                  <button onClick={loadTransfers} className="px-4 py-2 rounded-lg bg-brand-orange/10 border border-brand-orange/20 text-brand-orange text-sm hover:bg-brand-orange/20">Buscar</button>
                </div>

                <div className="rounded-2xl bg-white/[0.03] border border-white/[0.06] overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/[0.06]">
                        <th className="text-left px-4 py-3 text-white/40 font-medium">Orden</th>
                        <th className="text-left px-4 py-3 text-white/40 font-medium">Monto</th>
                        <th className="text-left px-4 py-3 text-white/40 font-medium">Estado</th>
                        <th className="text-left px-4 py-3 text-white/40 font-medium">Creación</th>
                        <th className="text-left px-4 py-3 text-white/40 font-medium">Acciones</th>
                      </tr>
                    </thead>
                    <tbody>
                      {transfers.length === 0 ? (
                        <tr><td colSpan={5} className="px-4 py-12 text-center text-white/30">Sin transferencias</td></tr>
                      ) : transfers.map((t) => (
                        <tr key={t.id} className="border-b border-white/[0.04] hover:bg-white/[0.02]">
                          <td className="px-4 py-3">
                            <p className="text-white font-mono text-xs">{t.order_number}</p>
                            <p className="text-white/30 text-xs">{t.alias}</p>
                          </td>
                          <td className="px-4 py-3 text-white">{t.currency === 'ARS' ? '$' : 'USD '}{Number(t.amount).toLocaleString()}</td>
                          <td className="px-4 py-3">
                            <StatusBadge status={t.status} />
                          </td>
                          <td className="px-4 py-3 text-white/40 text-xs">{new Date(t.created_at).toLocaleDateString('es-AR')}</td>
                          <td className="px-4 py-3">
                            {t.status === 'paid' && (
                              <div className="flex gap-2">
                                <button onClick={() => handleApprove(t.id, true)} disabled={approvingId === t.id} className="px-2 py-1 rounded bg-brand-teal/10 text-brand-teal text-xs hover:bg-brand-teal/20 disabled:opacity-50">Aprobar</button>
                                <button onClick={() => handleApprove(t.id, false)} disabled={approvingId === t.id} className="px-2 py-1 rounded bg-red-500/10 text-red-400 text-xs hover:bg-red-500/20 disabled:opacity-50">Rechazar</button>
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* RETENTION TAB */}
            {activeTab === 'retention' && retention && (
              <div className="space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <StatCard icon={<ThumbsDown className="w-4 h-4 text-red-400" />} label="Cancelaciones total" value={retention.total_cancellations} />
                  <StatCard icon={<Calendar className="w-4 h-4 text-amber-400" />} label="Este mes" value={retention.cancellations_this_month} />
                  <StatCard icon={<ArrowDownRight className="w-4 h-4 text-rose-400" />} label="Churn rate" value={`${retention.churn_rate_percent}%`} />
                  <StatCard icon={<MessageSquare className="w-4 h-4 text-blue-400" />} label="NPS promedio" value={retention.avg_nps ?? '—'} />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="p-5 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
                    <h3 className="text-sm font-medium text-white mb-4">Top razones de cancelación</h3>
                    <div className="space-y-3">
                      {retention.top_reasons.map((r, i) => (
                        <div key={i} className="flex items-center gap-3">
                          <span className="text-xs text-white/30 w-4">{i + 1}</span>
                          <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                            <div className="h-full bg-brand-orange rounded-full" style={{ width: `${Math.min((r.count / (retention.top_reasons[0]?.count || 1)) * 100, 100)}%` }} />
                          </div>
                          <span className="text-xs text-white/60 w-24 text-right truncate">{r.reason}</span>
                          <span className="text-xs text-white/40 w-6 text-right">{r.count}</span>
                        </div>
                      ))}
                      {retention.top_reasons.length === 0 && <p className="text-sm text-white/20">Sin datos aún</p>}
                    </div>
                  </div>

                  <div className="p-5 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
                    <h3 className="text-sm font-medium text-white mb-4">Competidores mencionados</h3>
                    <div className="space-y-2">
                      {retention.top_competitors.map((c, i) => (
                        <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-white/5">
                          <span className="text-sm text-white/60">{c.name}</span>
                          <span className="text-xs text-white/30">{c.count} veces</span>
                        </div>
                      ))}
                      {retention.top_competitors.length === 0 && <p className="text-sm text-white/20">Sin datos aún</p>}
                    </div>
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
                  <h3 className="text-sm font-medium text-white mb-4">Feedbacks recientes</h3>
                  <div className="space-y-2 max-h-80 overflow-y-auto">
                    {feedbacks.map((f) => (
                      <div key={f.id} className="p-3 rounded-xl bg-white/5">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs px-2 py-0.5 rounded-full bg-brand-orange/10 text-brand-orange">{f.reason_category}</span>
                          {f.rating_nps !== null && <span className="text-xs text-white/40">NPS: {f.rating_nps}</span>}
                          <span className="text-xs text-white/20 ml-auto">{new Date(f.cancelled_at).toLocaleDateString('es-AR')}</span>
                        </div>
                        {f.reason_text && <p className="text-sm text-white/50 mt-1">{f.reason_text}</p>}
                        {f.competitor_name && <p className="text-xs text-white/30 mt-1">Competidor: {f.competitor_name}</p>}
                      </div>
                    ))}
                    {feedbacks.length === 0 && <p className="text-sm text-white/20">Sin feedbacks aún</p>}
                  </div>
                </div>
              </div>
            )}

            {/* SUBSCRIPTIONS TAB */}
            {activeTab === 'subscriptions' && (
              <div className="rounded-2xl bg-white/[0.03] border border-white/[0.06] overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/[0.06]">
                      <th className="text-left px-4 py-3 text-white/40 font-medium">Usuario</th>
                      <th className="text-left px-4 py-3 text-white/40 font-medium">Plan</th>
                      <th className="text-left px-4 py-3 text-white/40 font-medium">Método</th>
                      <th className="text-left px-4 py-3 text-white/40 font-medium">Próx. facturación</th>
                      <th className="text-left px-4 py-3 text-white/40 font-medium">Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {subscriptions.length === 0 ? (
                      <tr><td colSpan={5} className="px-4 py-12 text-center text-white/30">Sin suscripciones</td></tr>
                    ) : subscriptions.map((s) => (
                      <tr key={s.id} className="border-b border-white/[0.04] hover:bg-white/[0.02]">
                        <td className="px-4 py-3">
                          <p className="text-white text-sm">{s.user_full_name || s.user_email || s.user_id}</p>
                          {s.user_email && <p className="text-white/30 text-xs">{s.user_email}</p>}
                        </td>
                        <td className="px-4 py-3 text-white/60">{s.plan_name}</td>
                        <td className="px-4 py-3 text-white/40 text-xs capitalize">{s.payment_provider || '—'}</td>
                        <td className="px-4 py-3 text-white/40 text-xs">{s.next_billing_date ? new Date(s.next_billing_date).toLocaleDateString('es-AR') : '—'}</td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex px-2 py-0.5 rounded-full text-xs ${
                            s.status === 'active' ? 'bg-brand-teal/10 text-brand-teal' :
                            s.status === 'past_due' ? 'bg-amber-500/10 text-amber-400' :
                            'bg-white/5 text-white/40'
                          }`}>{s.status}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string | number }) {
  return (
    <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-xs text-white/40">{label}</span>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  )
}

function ProviderRow({ icon, label, amount }: { icon: React.ReactNode; label: string; amount: number }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-sm text-white/60">{label}</span>
      </div>
      <span className="text-sm text-white font-medium">${amount.toLocaleString()}</span>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { color: string; label: string }> = {
    pending: { color: 'bg-amber-500/10 text-amber-400', label: 'Pendiente' },
    paid: { color: 'bg-blue-500/10 text-blue-400', label: 'Pagado' },
    confirmed: { color: 'bg-brand-teal/10 text-brand-teal', label: 'Confirmado' },
    expired: { color: 'bg-white/5 text-white/40', label: 'Expirado' },
    cancelled: { color: 'bg-red-500/10 text-red-400', label: 'Cancelado' },
  }
  const c = config[status] || { color: 'bg-white/5 text-white/40', label: status }
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs ${c.color}`}>{c.label}</span>
  )
}
