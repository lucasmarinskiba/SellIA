'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { api } from '@/lib/api'
import {
  ShieldAlert,
  Loader2,
  Mail,
  Tag,
  AlertTriangle,
  AlertOctagon,
  AlertCircle,
} from 'lucide-react'
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'

interface ChurnUser {
  id: string
  user_name: string
  user_email: string
  risk_level: 'critical' | 'high' | 'medium'
  risk_score: number
  signals: string[]
  last_activity: string
}

interface ChurnData {
  total_at_risk: number
  critical_count: number
  high_count: number
  medium_count: number
  users: ChurnUser[]
}

const RISK_COLORS = {
  critical: '#ef4444',
  high: '#f59e0b',
  medium: '#eab308',
}

const RISK_LABELS = {
  critical: 'Crítico',
  high: 'Alto',
  medium: 'Medio',
}

export default function AdminChurnPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const [data, setData] = useState<ChurnData | null>(null)
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
      const res = await api.get('/admin/churn-signals')
      setData(res.data)
    } catch (e: any) {
      if (e.response?.status === 403) {
        setForbidden(true)
      } else {
        setError('No se pudieron cargar los datos de churn')
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
          <ShieldAlert className="w-12 h-12 text-red-400 mx-auto mb-4" />
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

  const pieData = [
    { name: 'Crítico', value: data.critical_count, color: RISK_COLORS.critical },
    { name: 'Alto', value: data.high_count, color: RISK_COLORS.high },
    { name: 'Medio', value: data.medium_count, color: RISK_COLORS.medium },
  ].filter((d) => d.value > 0)

  return (
    <div className="min-h-screen bg-[#060812]">
      <div className="max-w-7xl mx-auto px-6 py-10">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-brand-orange/10 border border-brand-orange/20 flex items-center justify-center">
            <ShieldAlert className="w-5 h-5 text-brand-orange" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Churn Shield</h1>
            <p className="text-sm text-white/40">Usuarios en riesgo de cancelación</p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard
            icon={<AlertOctagon className="w-4 h-4 text-red-400" />}
            label="Total en riesgo"
            value={data.total_at_risk}
          />
          <StatCard
            icon={<AlertOctagon className="w-4 h-4 text-red-400" />}
            label="Críticos"
            value={data.critical_count}
          />
          <StatCard
            icon={<AlertTriangle className="w-4 h-4 text-amber-400" />}
            label="Altos"
            value={data.high_count}
          />
          <StatCard
            icon={<AlertCircle className="w-4 h-4 text-yellow-400" />}
            label="Medios"
            value={data.medium_count}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Pie Chart */}
          <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
            <h2 className="text-sm font-semibold text-white/80 mb-4">Distribución de riesgo</h2>
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
                      formatter={(value: any) => [value, 'Usuarios']}
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

          {/* Users Table */}
          <div className="lg:col-span-2 p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
            <h2 className="text-sm font-semibold text-white/80 mb-4">Usuarios en riesgo</h2>
            {data.users.length === 0 ? (
              <p className="text-sm text-white/30">No hay usuarios en riesgo</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/[0.06]">
                      <th className="text-left px-3 py-3 text-white/40 font-medium">Usuario</th>
                      <th className="text-left px-3 py-3 text-white/40 font-medium">Nivel de Riesgo</th>
                      <th className="text-left px-3 py-3 text-white/40 font-medium">Score</th>
                      <th className="text-left px-3 py-3 text-white/40 font-medium">Señales</th>
                      <th className="text-left px-3 py-3 text-white/40 font-medium">Última actividad</th>
                      <th className="text-left px-3 py-3 text-white/40 font-medium">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.users.map((u) => (
                      <tr key={u.id} className="border-b border-white/[0.04] hover:bg-white/[0.02]">
                        <td className="px-3 py-3">
                          <p className="text-white font-medium">{u.user_name}</p>
                          <p className="text-white/30 text-xs">{u.user_email}</p>
                        </td>
                        <td className="px-3 py-3">
                          <RiskBadge level={u.risk_level} />
                        </td>
                        <td className="px-3 py-3 text-white font-mono">{u.risk_score}</td>
                        <td className="px-3 py-3">
                          <div className="flex flex-wrap gap-1">
                            {u.signals.slice(0, 2).map((s, i) => (
                              <span key={i} className="px-1.5 py-0.5 rounded bg-white/5 text-[10px] text-white/50">
                                {s}
                              </span>
                            ))}
                            {u.signals.length > 2 && (
                              <span className="px-1.5 py-0.5 rounded bg-white/5 text-[10px] text-white/30">
                                +{u.signals.length - 2}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-3 py-3 text-white/40 text-xs">
                          {u.last_activity ? new Date(u.last_activity).toLocaleDateString('es-AR') : '—'}
                        </td>
                        <td className="px-3 py-3">
                          <div className="flex gap-2">
                            <button
                              onClick={() => alert(`Enviar email a ${u.user_email}`)}
                              className="flex items-center gap-1 px-2 py-1 rounded bg-blue-500/10 text-blue-400 text-xs hover:bg-blue-500/20 transition-colors"
                            >
                              <Mail className="w-3 h-3" />
                              Enviar email
                            </button>
                            <button
                              onClick={() => alert(`Ofrecer descuento a ${u.user_email}`)}
                              className="flex items-center gap-1 px-2 py-1 rounded bg-brand-teal/10 text-brand-teal text-xs hover:bg-brand-teal/20 transition-colors"
                            >
                              <Tag className="w-3 h-3" />
                              Ofrecer descuento
                            </button>
                          </div>
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

function RiskBadge({ level }: { level: 'critical' | 'high' | 'medium' }) {
  const config = {
    critical: { label: 'Crítico', color: 'bg-red-500/10 text-red-400 border-red-500/20' },
    high: { label: 'Alto', color: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
    medium: { label: 'Medio', color: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' },
  }
  const c = config[level] || config.medium
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs border ${c.color}`}>
      {c.label}
    </span>
  )
}
