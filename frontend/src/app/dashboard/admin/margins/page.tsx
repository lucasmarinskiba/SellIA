'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { api } from '@/lib/api'
import {
  PieChart as PieChartIcon,
  Loader2,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  Cpu,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

interface MarginUser {
  user_id: string
  user_name: string
  user_email: string
  plan_name: string
  plan_price: number
  ai_cost: number
  margin_amount: number
  margin_percent: number
}

interface MarginsData {
  users: MarginUser[]
  avg_margin_percent: number
  negative_margin_count: number
  total_ai_cost: number
}

const BAR_COLORS = ['#f97316', '#14b8a6', '#8b5cf6', '#3b82f6', '#ef4444', '#eab308', '#06b6d4', '#ec4899', '#10b981', '#6366f1']

export default function AdminMarginsPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const [data, setData] = useState<MarginsData | null>(null)
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
      const res = await api.get('/admin/margins')
      setData(res.data)
    } catch (e: any) {
      if (e.response?.status === 403) {
        setForbidden(true)
      } else {
        setError('No se pudieron cargar los datos de márgenes')
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
          <PieChartIcon className="w-12 h-12 text-red-400 mx-auto mb-4" />
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

  const top10 = [...data.users]
    .sort((a, b) => b.margin_amount - a.margin_amount)
    .slice(0, 10)
    .map((u) => ({
      name: u.user_name.split(' ')[0] || u.user_email.split('@')[0],
      margin: u.margin_amount,
    }))

  return (
    <div className="min-h-screen bg-[#060812]">
      <div className="max-w-7xl mx-auto px-6 py-10">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-brand-orange/10 border border-brand-orange/20 flex items-center justify-center">
            <PieChartIcon className="w-5 h-5 text-brand-orange" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Margen por Usuario</h1>
            <p className="text-sm text-white/40">Análisis de rentabilidad por cuenta</p>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <StatCard
            icon={<TrendingUp className="w-4 h-4 text-brand-teal" />}
            label="Margen promedio"
            value={`${data.avg_margin_percent.toFixed(1)}%`}
            trend={data.avg_margin_percent >= 0 ? 'Positivo' : 'Negativo'}
            trendColor={data.avg_margin_percent >= 0 ? 'text-brand-teal' : 'text-red-400'}
          />
          <StatCard
            icon={<Users className="w-4 h-4 text-red-400" />}
            label="Margen negativo"
            value={data.negative_margin_count}
            trend="usuarios"
            trendColor="text-white/40"
          />
          <StatCard
            icon={<Cpu className="w-4 h-4 text-brand-violet" />}
            label="Costo IA total"
            value={`$${data.total_ai_cost.toLocaleString()}`}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Bar Chart */}
          <div className="lg:col-span-2 p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
            <h2 className="text-sm font-semibold text-white/80 mb-4">Top 10 usuarios por margen</h2>
            {top10.length === 0 ? (
              <p className="text-sm text-white/30">Sin datos</p>
            ) : (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={top10} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="name" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }} axisLine={{ stroke: 'rgba(255,255,255,0.1)' }} />
                    <YAxis tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }} axisLine={{ stroke: 'rgba(255,255,255,0.1)' }} tickFormatter={(v) => `$${v}`} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0a0e1a',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '12px',
                        color: '#fff',
                        fontSize: '12px',
                      }}
                      formatter={(value: any) => [`$${(value as number).toLocaleString()}`, 'Margen']}
                    />
                    <Bar dataKey="margin" radius={[6, 6, 0, 0]}>
                      {top10.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={BAR_COLORS[index % BAR_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Quick stats */}
          <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
            <h2 className="text-sm font-semibold text-white/80 mb-4">Resumen rápido</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 rounded-xl bg-white/5">
                <div className="flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-brand-orange" />
                  <span className="text-sm text-white/60">Usuarios analizados</span>
                </div>
                <span className="text-sm font-semibold text-white">{data.users.length}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-white/5">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-brand-teal" />
                  <span className="text-sm text-white/60">Margen positivo</span>
                </div>
                <span className="text-sm font-semibold text-brand-teal">
                  {data.users.filter((u) => u.margin_amount > 0).length}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-white/5">
                <div className="flex items-center gap-2">
                  <TrendingDown className="w-4 h-4 text-red-400" />
                  <span className="text-sm text-white/60">Margen negativo</span>
                </div>
                <span className="text-sm font-semibold text-red-400">
                  {data.negative_margin_count}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
          <h2 className="text-sm font-semibold text-white/80 mb-4">Detalle por usuario</h2>
          {data.users.length === 0 ? (
            <p className="text-sm text-white/30">Sin datos</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/[0.06]">
                    <th className="text-left px-4 py-3 text-white/40 font-medium">Usuario</th>
                    <th className="text-left px-4 py-3 text-white/40 font-medium">Plan</th>
                    <th className="text-left px-4 py-3 text-white/40 font-medium">Precio Plan</th>
                    <th className="text-left px-4 py-3 text-white/40 font-medium">Costo IA</th>
                    <th className="text-left px-4 py-3 text-white/40 font-medium">Margen $</th>
                    <th className="text-left px-4 py-3 text-white/40 font-medium">Margen %</th>
                    <th className="text-left px-4 py-3 text-white/40 font-medium">Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {data.users.map((u) => (
                    <tr key={u.user_id} className="border-b border-white/[0.04] hover:bg-white/[0.02]">
                      <td className="px-4 py-3">
                        <p className="text-white font-medium">{u.user_name}</p>
                        <p className="text-white/30 text-xs">{u.user_email}</p>
                      </td>
                      <td className="px-4 py-3 text-white/60">{u.plan_name}</td>
                      <td className="px-4 py-3 text-white">${u.plan_price.toLocaleString()}</td>
                      <td className="px-4 py-3 text-white">${u.ai_cost.toLocaleString()}</td>
                      <td className="px-4 py-3">
                        <span className={u.margin_amount >= 0 ? 'text-brand-teal' : 'text-red-400'}>
                          ${u.margin_amount.toLocaleString()}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={u.margin_percent >= 0 ? 'text-brand-teal' : 'text-red-400'}>
                          {u.margin_percent.toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex px-2 py-0.5 rounded-full text-xs ${
                            u.margin_amount >= 0
                              ? 'bg-brand-teal/10 text-brand-teal'
                              : 'bg-red-500/10 text-red-400'
                          }`}
                        >
                          {u.margin_amount >= 0 ? 'Positivo' : 'Negativo'}
                        </span>
                      </td>
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

function StatCard({
  icon,
  label,
  value,
  trend,
  trendColor,
}: {
  icon: React.ReactNode
  label: string
  value: string | number
  trend?: string
  trendColor?: string
}) {
  return (
    <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-xs text-white/40">{label}</span>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      {trend && <p className={`text-[11px] ${trendColor || 'text-white/30'}`}>{trend}</p>}
    </div>
  )
}
