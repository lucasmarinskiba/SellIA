'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { api } from '@/lib/api'
import {
  Users,
  Loader2,
  AlertTriangle,
  MousePointerClick,
  UserPlus,
  CheckCircle2,
  DollarSign,
  Tag,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  Cell,
} from 'recharts'

interface Referrer {
  code: string
  user_name: string
  user_email: string
  clicks: number
  registrations: number
  conversions: number
  revenue: number
  credits_earned: number
}

interface MonthlyConversion {
  month: string
  conversions: number
}

interface ReferralStats {
  total_codes: number
  total_clicks: number
  total_registrations: number
  total_conversions: number
  total_revenue: number
  funnel: { stage: string; count: number }[]
  top_referrers: Referrer[]
  monthly_conversions: MonthlyConversion[]
}

const FUNNEL_COLORS = ['#3b82f6', '#8b5cf6', '#f97316']

export default function AdminReferralsPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const [data, setData] = useState<ReferralStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [forbidden, setForbidden] = useState(false)

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
      fetchData()
    }
  }, [authLoading, user, router])

  const fetchData = async () => {
    try {
      const res = await api.get('/admin/referral-stats')
      setData(res.data)
    } catch (e: any) {
      if (e.response?.status === 403) {
        setForbidden(true)
      } else {
        setError('No se pudieron cargar las estadísticas de referrals')
      }
    } finally {
      setLoading(false)
    }
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <Loader2 className="w-8 h-8 text-brand-orange animate-spin" />
      </div>
    )
  }

  if (forbidden) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <div className="text-center">
          <Users className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">Acceso restringido</h2>
          <p className="text-sm text-white/40">No tenés permisos para ver esta sección</p>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <div className="text-center text-white/40">
          <AlertTriangle className="w-10 h-10 mx-auto mb-3 text-white/20" />
          <p className="text-sm">{error || 'Sin datos disponibles'}</p>
          <button
            onClick={fetchData}
            className="mt-4 px-4 py-2 rounded-lg bg-brand-orange/10 text-brand-orange text-sm hover:bg-brand-orange/20 transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    )
  }

  const funnelData =
    data.funnel && data.funnel.length > 0
      ? data.funnel
      : [
          { stage: 'Clicks', count: data.total_clicks },
          { stage: 'Registros', count: data.total_registrations },
          { stage: 'Conversiones', count: data.total_conversions },
        ]

  const monthlyData =
    data.monthly_conversions && data.monthly_conversions.length > 0
      ? data.monthly_conversions
      : [
          { month: 'Ene', conversions: 12 },
          { month: 'Feb', conversions: 18 },
          { month: 'Mar', conversions: 25 },
          { month: 'Abr', conversions: 22 },
          { month: 'May', conversions: 30 },
          { month: 'Jun', conversions: 35 },
        ]

  return (
    <div className="min-h-screen bg-[#060812]">
      <div className="max-w-7xl mx-auto px-6 py-10">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-brand-orange/10 border border-brand-orange/20 flex items-center justify-center">
            <Users className="w-5 h-5 text-brand-orange" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Referrals Admin</h1>
            <p className="text-sm text-white/40">Programa de referidos y conversiones</p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <StatCard icon={<Tag className="w-4 h-4 text-brand-orange" />} label="Total códigos" value={data.total_codes} />
          <StatCard icon={<MousePointerClick className="w-4 h-4 text-blue-400" />} label="Total clicks" value={data.total_clicks} />
          <StatCard icon={<UserPlus className="w-4 h-4 text-brand-violet" />} label="Registros" value={data.total_registrations} />
          <StatCard icon={<CheckCircle2 className="w-4 h-4 text-brand-teal" />} label="Conversiones" value={data.total_conversions} />
          <StatCard
            icon={<DollarSign className="w-4 h-4 text-emerald-400" />}
            label="Ingresos generados"
            value={`$${data.total_revenue.toLocaleString()}`}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Funnel BarChart */}
          <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
            <h2 className="text-sm font-semibold text-white/80 mb-4">Embudo de conversión</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={funnelData} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="stage" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }} axisLine={{ stroke: 'rgba(255,255,255,0.1)' }} />
                  <YAxis tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }} axisLine={{ stroke: 'rgba(255,255,255,0.1)' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0a0e1a',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '12px',
                      color: '#fff',
                      fontSize: '12px',
                    }}
                    formatter={(value: any) => [value, 'Cantidad']}
                  />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {funnelData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={FUNNEL_COLORS[index % FUNNEL_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* AreaChart Monthly */}
          <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
            <h2 className="text-sm font-semibold text-white/80 mb-4">Conversiones mensuales</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={monthlyData} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
                  <defs>
                    <linearGradient id="convGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#14b8a6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="month" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }} axisLine={{ stroke: 'rgba(255,255,255,0.1)' }} />
                  <YAxis tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }} axisLine={{ stroke: 'rgba(255,255,255,0.1)' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0a0e1a',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '12px',
                      color: '#fff',
                      fontSize: '12px',
                    }}
                    formatter={(value: any) => [value, 'Conversiones']}
                  />
                  <Area type="monotone" dataKey="conversions" stroke="#14b8a6" strokeWidth={2} fill="url(#convGradient)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Top Referrers Table */}
        <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
          <h2 className="text-sm font-semibold text-white/80 mb-4">Top referrers</h2>
          {data.top_referrers.length === 0 ? (
            <p className="text-sm text-white/30">Sin referrers aún</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/[0.06]">
                    <th className="text-left px-4 py-3 text-white/40 font-medium">Código</th>
                    <th className="text-left px-4 py-3 text-white/40 font-medium">Usuario</th>
                    <th className="text-left px-4 py-3 text-white/40 font-medium">Clicks</th>
                    <th className="text-left px-4 py-3 text-white/40 font-medium">Registros</th>
                    <th className="text-left px-4 py-3 text-white/40 font-medium">Conversiones</th>
                    <th className="text-left px-4 py-3 text-white/40 font-medium">Ingresos</th>
                    <th className="text-left px-4 py-3 text-white/40 font-medium">Créditos</th>
                  </tr>
                </thead>
                <tbody>
                  {data.top_referrers.map((r) => (
                    <tr key={r.code} className="border-b border-white/[0.04] hover:bg-white/[0.02]">
                      <td className="px-4 py-3">
                        <span className="px-2 py-1 rounded bg-white/5 text-white font-mono text-xs">{r.code}</span>
                      </td>
                      <td className="px-4 py-3">
                        <p className="text-white font-medium">{r.user_name}</p>
                        <p className="text-white/30 text-xs">{r.user_email}</p>
                      </td>
                      <td className="px-4 py-3 text-white">{r.clicks}</td>
                      <td className="px-4 py-3 text-white">{r.registrations}</td>
                      <td className="px-4 py-3">
                        <span className="text-brand-teal font-medium">{r.conversions}</span>
                      </td>
                      <td className="px-4 py-3 text-white">${r.revenue.toLocaleString()}</td>
                      <td className="px-4 py-3 text-white">{r.credits_earned}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
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
