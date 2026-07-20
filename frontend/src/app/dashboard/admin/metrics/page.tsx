'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { api } from '@/lib/api'
import {
  BarChart3,
  Loader2,
  Shield,
  Globe,
  Smartphone,
  Monitor,
  AlertTriangle,
  Users,
  Activity,
  Clock,
} from 'lucide-react'

interface Metrics {
  total_logins_24h: number
  failed_logins_24h: number
  unique_users_24h: number
  active_sessions: number
  avg_risk_score: number
  top_countries: { country: string; count: number }[]
  login_timeline: { hour: string; logins: number; failed: number }[]
  device_breakdown: { type: string; count: number }[]
}

export default function SecurityMetricsPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [loading, setLoading] = useState(true)

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
      fetchMetrics()
    }
  }, [authLoading, user, router])

  const fetchMetrics = async () => {
    try {
      const res = await api.get('/security/metrics')
      setMetrics(res.data)
    } catch (e: any) {
      if (e.response?.status === 403) {
        router.push('/dashboard')
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

  if (!metrics) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-10 text-white/40">
        No se pudieron cargar las métricas
      </div>
    )
  }

  const maxTimeline = Math.max(
    ...metrics.login_timeline.map((t) => t.logins + t.failed),
    1
  )

  const maxCountry = Math.max(
    ...metrics.top_countries.map((c) => c.count),
    1
  )

  const totalDevices = metrics.device_breakdown.reduce((s, d) => s + d.count, 0)

  return (
    <div className="max-w-7xl mx-auto px-6 py-10">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl bg-brand-orange/10 border border-brand-orange/20 flex items-center justify-center">
          <BarChart3 className="w-5 h-5 text-brand-orange" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Métricas de Seguridad</h1>
          <p className="text-sm text-white/40">Dashboard de monitoreo en tiempo real</p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          icon={<Activity className="w-4 h-4 text-emerald-400" />}
          label="Logins 24h"
          value={metrics.total_logins_24h}
          trend={metrics.failed_logins_24h > 0 ? `${metrics.failed_logins_24h} fallidos` : 'OK'}
          trendColor={metrics.failed_logins_24h > 0 ? 'text-amber-400' : 'text-emerald-400'}
        />
        <StatCard
          icon={<Users className="w-4 h-4 text-blue-400" />}
          label="Usuarios únicos"
          value={metrics.unique_users_24h}
        />
        <StatCard
          icon={<Shield className="w-4 h-4 text-brand-orange" />}
          label="Sesiones activas"
          value={metrics.active_sessions}
        />
        <StatCard
          icon={<AlertTriangle className="w-4 h-4 text-red-400" />}
          label="Intentos fallidos"
          value={metrics.failed_logins_24h}
          trendColor={metrics.failed_logins_24h > 5 ? 'text-red-400' : 'text-white/40'}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Timeline */}
        <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
          <div className="flex items-center gap-2 mb-6">
            <Clock className="w-4 h-4 text-brand-orange" />
            <h2 className="text-sm font-semibold text-white/80">Timeline de logins (24h)</h2>
          </div>

          {metrics.login_timeline.length === 0 ? (
            <p className="text-sm text-white/30">Sin datos en las últimas 24 horas</p>
          ) : (
            <div className="space-y-3">
              {metrics.login_timeline.map((point) => {
                const total = point.logins + point.failed
                const successPct = total > 0 ? (point.logins / total) * 100 : 0
                const failedPct = total > 0 ? (point.failed / total) * 100 : 0
                const barHeight = total > 0 ? (total / maxTimeline) * 100 : 0

                return (
                  <div key={point.hour} className="space-y-1">
                    <div className="flex items-center justify-between text-xs text-white/40">
                      <span>{new Date(point.hour).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })}</span>
                      <span>{total} logins</span>
                    </div>
                    <div className="h-6 flex rounded-lg overflow-hidden bg-white/5">
                      <div
                        className="bg-emerald-500/60 transition-all"
                        style={{ width: `${successPct}%` }}
                        title={`${point.logins} exitosos`}
                      />
                      <div
                        className="bg-red-500/60 transition-all"
                        style={{ width: `${failedPct}%` }}
                        title={`${point.failed} fallidos`}
                      />
                    </div>
                  </div>
                )
              })}
              <div className="flex items-center gap-4 text-[10px] text-white/30 pt-2">
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-emerald-500/60" /> Exitosos
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-red-500/60" /> Fallidos
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Countries */}
        <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
          <div className="flex items-center gap-2 mb-6">
            <Globe className="w-4 h-4 text-brand-orange" />
            <h2 className="text-sm font-semibold text-white/80">Top países</h2>
          </div>

          {metrics.top_countries.length === 0 ? (
            <p className="text-sm text-white/30">Sin datos de geolocalización</p>
          ) : (
            <div className="space-y-3">
              {metrics.top_countries.map((c) => (
                <div key={c.country} className="space-y-1">
                  <div className="flex items-center justify-between text-xs text-white/40">
                    <span className="font-medium text-white/60">{c.country}</span>
                    <span>{c.count} logins</span>
                  </div>
                  <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                    <div
                      className="h-full bg-brand-orange/60 rounded-full transition-all"
                      style={{ width: `${(c.count / maxCountry) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Devices */}
        <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
          <div className="flex items-center gap-2 mb-6">
            <Smartphone className="w-4 h-4 text-brand-orange" />
            <h2 className="text-sm font-semibold text-white/80">Dispositivos</h2>
          </div>

          {totalDevices === 0 ? (
            <p className="text-sm text-white/30">Sin datos de dispositivos</p>
          ) : (
            <div className="flex items-end gap-4 h-32">
              {metrics.device_breakdown.map((d) => {
                const pct = totalDevices > 0 ? (d.count / totalDevices) * 100 : 0
                const icons: Record<string, React.ReactNode> = {
                  mobile: <Smartphone className="w-4 h-4" />,
                  desktop: <Monitor className="w-4 h-4" />,
                  other: <Activity className="w-4 h-4" />,
                }
                const colors: Record<string, string> = {
                  mobile: 'bg-brand-orange/60',
                  desktop: 'bg-brand-teal/60',
                  other: 'bg-brand-violet/60',
                }

                return (
                  <div key={d.type} className="flex-1 flex flex-col items-center gap-2">
                    <div className="text-xs text-white/60 font-mono">{d.count}</div>
                    <div
                      className={`w-full rounded-t-lg ${colors[d.type] || 'bg-white/20'} transition-all`}
                      style={{ height: `${pct}%` }}
                    />
                    <div className="text-white/40">{icons[d.type]}</div>
                    <div className="text-[10px] text-white/30 capitalize">{d.type}</div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Quick links */}
        <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
          <div className="flex items-center gap-2 mb-6">
            <Shield className="w-4 h-4 text-brand-orange" />
            <h2 className="text-sm font-semibold text-white/80">Acciones rápidas</h2>
          </div>
          <div className="space-y-2">
            <a
              href="/dashboard/admin/audit"
              className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-sm text-white/70 hover:bg-white/[0.08] hover:text-white transition-all"
            >
              <Activity className="w-4 h-4 text-brand-orange" />
              Ver logs de auditoría
            </a>
            <a
              href="/dashboard/seguridad"
              className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-sm text-white/70 hover:bg-white/[0.08] hover:text-white transition-all"
            >
              <Shield className="w-4 h-4 text-emerald-400" />
              Configurar seguridad
            </a>
          </div>
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
  value: number
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
