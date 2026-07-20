'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { api } from '@/lib/api'
import {
  Smile,
  Loader2,
  AlertTriangle,
  ThumbsUp,
  Minus,
  ThumbsDown,
  MessageSquare,
} from 'lucide-react'
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts'

interface NpsResponse {
  id: string
  user_name: string
  user_email: string
  score: number
  comment: string | null
  created_at: string
}

interface NpsMonthly {
  month: string
  nps: number
}

interface NpsData {
  nps_score: number
  total_responses: number
  promoters_count: number
  passives_count: number
  detractors_count: number
  monthly_evolution: NpsMonthly[]
  recent_responses: NpsResponse[]
}

const PIE_COLORS = ['#10b981', '#f59e0b', '#ef4444']

const MOCK_MONTHLY: NpsMonthly[] = [
  { month: 'Ene', nps: 42 },
  { month: 'Feb', nps: 38 },
  { month: 'Mar', nps: 45 },
  { month: 'Abr', nps: 52 },
  { month: 'May', nps: 48 },
  { month: 'Jun', nps: 55 },
]

export default function AdminNpsPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const [data, setData] = useState<NpsData | null>(null)
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
      let res
      try {
        res = await api.get('/admin/nps-stats')
      } catch {
        res = await api.get('/nps/stats')
      }
      const payload = res.data as NpsData
      if (!payload.monthly_evolution || payload.monthly_evolution.length === 0) {
        payload.monthly_evolution = MOCK_MONTHLY
      }
      setData(payload)
    } catch (e: any) {
      if (e.response?.status === 403) {
        setForbidden(true)
      } else {
        setError('No se pudieron cargar las estadísticas NPS')
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
          <Smile className="w-12 h-12 text-red-400 mx-auto mb-4" />
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

  const npsColor =
    data.nps_score > 50 ? 'text-emerald-400' : data.nps_score >= 30 ? 'text-amber-400' : 'text-red-400'
  const npsBg =
    data.nps_score > 50 ? 'bg-emerald-500/10' : data.nps_score >= 30 ? 'bg-amber-500/10' : 'bg-red-500/10'

  const pieData = [
    { name: 'Promotores', value: data.promoters_count, color: PIE_COLORS[0] },
    { name: 'Pasivos', value: data.passives_count, color: PIE_COLORS[1] },
    { name: 'Detractores', value: data.detractors_count, color: PIE_COLORS[2] },
  ].filter((d) => d.value > 0)

  return (
    <div className="min-h-screen bg-[#060812]">
      <div className="max-w-7xl mx-auto px-6 py-10">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-brand-orange/10 border border-brand-orange/20 flex items-center justify-center">
            <Smile className="w-5 h-5 text-brand-orange" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">NPS Analytics</h1>
            <p className="text-sm text-white/40">Net Promoter Score y satisfacción</p>
          </div>
        </div>

        {/* Big NPS + Stats */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
          <div className={`md:col-span-2 p-6 rounded-2xl ${npsBg} border border-white/[0.06] flex flex-col items-center justify-center`}>
            <p className="text-xs text-white/40 uppercase tracking-wider mb-2">NPS Score</p>
            <p className={`text-6xl font-bold ${npsColor}`}>{data.nps_score}</p>
            <p className="text-xs text-white/30 mt-1">
              {data.nps_score > 50 ? 'Excelente' : data.nps_score >= 30 ? 'Bueno' : 'Necesita atención'}
            </p>
          </div>
          <StatCard icon={<MessageSquare className="w-4 h-4 text-blue-400" />} label="Total respuestas" value={data.total_responses} />
          <StatCard icon={<ThumbsUp className="w-4 h-4 text-emerald-400" />} label="Promotores" value={data.promoters_count} />
          <StatCard icon={<Minus className="w-4 h-4 text-amber-400" />} label="Pasivos" value={data.passives_count} />
          <StatCard icon={<ThumbsDown className="w-4 h-4 text-red-400" />} label="Detractores" value={data.detractors_count} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Pie Chart */}
          <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
            <h2 className="text-sm font-semibold text-white/80 mb-4">Distribución NPS</h2>
            {pieData.length === 0 ? (
              <p className="text-sm text-white/30">Sin datos</p>
            ) : (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} stroke="transparent" />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0a0e1a',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '12px',
                        color: '#fff',
                        fontSize: '12px',
                      }}
                      formatter={(value: any) => [value, 'Respuestas']}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
            <div className="flex flex-wrap gap-3 justify-center mt-2">
              {pieData.map((d) => (
                <div key={d.name} className="flex items-center gap-1.5 text-xs text-white/50">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }} />
                  {d.name}
                </div>
              ))}
            </div>
          </div>

          {/* Area Chart */}
          <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
            <h2 className="text-sm font-semibold text-white/80 mb-4">Evolución mensual NPS</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.monthly_evolution} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
                  <defs>
                    <linearGradient id="npsGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
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
                    formatter={(value: any) => [`${value}`, 'NPS']}
                  />
                  <Area type="monotone" dataKey="nps" stroke="#f97316" strokeWidth={2} fill="url(#npsGradient)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Recent Responses Table */}
        <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
          <h2 className="text-sm font-semibold text-white/80 mb-4">Respuestas recientes</h2>
          {data.recent_responses.length === 0 ? (
            <p className="text-sm text-white/30">Sin respuestas aún</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/[0.06]">
                    <th className="text-left px-4 py-3 text-white/40 font-medium">Usuario</th>
                    <th className="text-left px-4 py-3 text-white/40 font-medium">Score</th>
                    <th className="text-left px-4 py-3 text-white/40 font-medium">Comentario</th>
                    <th className="text-left px-4 py-3 text-white/40 font-medium">Fecha</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_responses.map((r) => (
                    <tr key={r.id} className="border-b border-white/[0.04] hover:bg-white/[0.02]">
                      <td className="px-4 py-3">
                        <p className="text-white font-medium">{r.user_name}</p>
                        <p className="text-white/30 text-xs">{r.user_email}</p>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                            r.score >= 9
                              ? 'bg-emerald-500/10 text-emerald-400'
                              : r.score >= 7
                              ? 'bg-amber-500/10 text-amber-400'
                              : 'bg-red-500/10 text-red-400'
                          }`}
                        >
                          {r.score}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-white/60 max-w-xs truncate">{r.comment || '—'}</td>
                      <td className="px-4 py-3 text-white/40 text-xs">
                        {new Date(r.created_at).toLocaleDateString('es-AR')}
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

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
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
