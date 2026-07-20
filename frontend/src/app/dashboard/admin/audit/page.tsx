'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { api } from '@/lib/api'
import {
  Shield,
  Loader2,
  Search,
  Filter,
  Globe,
  Clock,
  CheckCircle2,
  XCircle,
  BarChart3,
  Users,
  Lock,
  AlertTriangle,
  Trash2,
} from 'lucide-react'

interface AuditLog {
  id: string
  user_id: string
  user_email: string | null
  ip_address: string
  user_agent: string | null
  country: string | null
  city: string | null
  success: boolean
  created_at: string
}

interface SecurityStats {
  total_logins_today: number
  failed_logins_today: number
  new_devices_today: number
  active_sessions: number
  blocked_attempts_today: number
  geofence_violations_today: number
}

interface AuditReport {
  period: string
  total_logins_7d: number
  failed_logins_7d: number
  failed_rate_pct: number
  data_access_logs_7d: number
  secret_rotations_7d: number
  data_retention_cleanups_7d: number
  records_deleted_7d: number
  active_sessions_now: number
}

export default function AdminAuditPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [stats, setStats] = useState<SecurityStats | null>(null)
  const [report, setReport] = useState<AuditReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState({
    event_type: '',
    ip: '',
    country: '',
    date_from: '',
    date_to: '',
  })

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
      fetchLogs()
      fetchStats()
      fetchReport()
    }
  }, [authLoading, user, router])

  const fetchLogs = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filter.event_type) params.append('event_type', filter.event_type)
      if (filter.ip) params.append('ip', filter.ip)
      if (filter.country) params.append('country', filter.country)
      if (filter.date_from) params.append('date_from', filter.date_from)
      if (filter.date_to) params.append('date_to', filter.date_to)
      params.append('limit', '100')

      const res = await api.get(`/security/audit-logs?${params.toString()}`)
      setLogs(res.data)
    } catch (e: any) {
      if (e.response?.status === 403) {
        router.push('/dashboard')
      }
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const res = await api.get('/security/audit-stats')
      setStats(res.data)
    } catch {
      // silencioso
    }
  }

  const fetchReport = async () => {
    try {
      const res = await api.get('/security/audit-report')
      setReport(res.data)
    } catch {
      // silencioso
    }
  }

  const applyFilters = () => {
    fetchLogs()
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <Loader2 className="w-8 h-8 text-brand-orange animate-spin" />
      </div>
    )
  }

  if (!user?.is_superuser) {
    return null
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-10">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl bg-brand-orange/10 border border-brand-orange/20 flex items-center justify-center">
          <Shield className="w-5 h-5 text-brand-orange" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Panel de Auditoría de Seguridad</h1>
          <p className="text-sm text-white/40">Monitoreo de logins, geofencing y amenazas</p>
        </div>
      </div>

      {/* Stats Cards — Hoy */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
          <StatCard
            icon={<CheckCircle2 className="w-4 h-4 text-emerald-400" />}
            label="Logins hoy"
            value={stats.total_logins_today}
          />
          <StatCard
            icon={<XCircle className="w-4 h-4 text-red-400" />}
            label="Fallidos hoy"
            value={stats.failed_logins_today}
          />
          <StatCard
            icon={<AlertTriangle className="w-4 h-4 text-amber-400" />}
            label="Nuevos dispositivos"
            value={stats.new_devices_today}
          />
          <StatCard
            icon={<Lock className="w-4 h-4 text-blue-400" />}
            label="Sesiones activas"
            value={stats.active_sessions}
          />
          <StatCard
            icon={<Globe className="w-4 h-4 text-purple-400" />}
            label="Bloqueados hoy"
            value={stats.blocked_attempts_today}
          />
          <StatCard
            icon={<BarChart3 className="w-4 h-4 text-rose-400" />}
            label="Geofence violations"
            value={stats.geofence_violations_today}
          />
        </div>
      )}

      {/* Weekly Audit Report */}
      {report && (
        <div className="mb-8 p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-5 h-5 text-brand-orange" />
            <h2 className="text-lg font-semibold text-white">Reporte Semanal de Seguridad</h2>
            <span className="text-xs text-white/30 ml-auto">{report.period}</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              icon={<Users className="w-4 h-4 text-emerald-400" />}
              label="Logins (7d)"
              value={report.total_logins_7d}
            />
            <StatCard
              icon={<XCircle className="w-4 h-4 text-red-400" />}
              label={`Fallidos (${report.failed_rate_pct}%)`}
              value={report.failed_logins_7d}
            />
            <StatCard
              icon={<Shield className="w-4 h-4 text-blue-400" />}
              label="Data Access Logs"
              value={report.data_access_logs_7d}
            />
            <StatCard
              icon={<Lock className="w-4 h-4 text-purple-400" />}
              label="Rotaciones de secretos"
              value={report.secret_rotations_7d}
            />
            <StatCard
              icon={<AlertTriangle className="w-4 h-4 text-amber-400" />}
              label="Cleanups de retención"
              value={report.data_retention_cleanups_7d}
            />
            <StatCard
              icon={<Trash2 className="w-4 h-4 text-rose-400" />}
              label="Registros eliminados"
              value={report.records_deleted_7d}
            />
            <StatCard
              icon={<Lock className="w-4 h-4 text-cyan-400" />}
              label="Sesiones activas"
              value={report.active_sessions_now}
            />
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="mb-6 p-4 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
        <div className="flex items-center gap-2 mb-3">
          <Filter className="w-4 h-4 text-brand-orange" />
          <span className="text-sm font-medium text-white/80">Filtros</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          <select
            value={filter.event_type}
            onChange={(e) => setFilter({ ...filter, event_type: e.target.value })}
            className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:border-brand-orange/50"
          >
            <option value="" className="bg-[#0a0e1a]">Todos los eventos</option>
            <option value="success" className="bg-[#0a0e1a]">Exitosos</option>
            <option value="failed" className="bg-[#0a0e1a]">Fallidos</option>
          </select>
          <input
            type="text"
            value={filter.ip}
            onChange={(e) => setFilter({ ...filter, ip: e.target.value })}
            placeholder="Filtrar por IP"
            className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm placeholder-white/20 focus:outline-none focus:border-brand-orange/50"
          />
          <input
            type="text"
            value={filter.country}
            onChange={(e) => setFilter({ ...filter, country: e.target.value })}
            placeholder="País"
            className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm placeholder-white/20 focus:outline-none focus:border-brand-orange/50"
          />
          <input
            type="date"
            value={filter.date_from}
            onChange={(e) => setFilter({ ...filter, date_from: e.target.value })}
            className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:border-brand-orange/50"
          />
          <button
            onClick={applyFilters}
            className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-brand-orange/10 border border-brand-orange/20 text-brand-orange text-sm hover:bg-brand-orange/20 transition-all"
          >
            <Search className="w-4 h-4" />
            Aplicar
          </button>
        </div>
      </div>

      {/* Logs Table */}
      <div className="rounded-2xl bg-white/[0.03] border border-white/[0.06] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/[0.06]">
                <th className="text-left px-4 py-3 text-white/40 font-medium">Estado</th>
                <th className="text-left px-4 py-3 text-white/40 font-medium">Usuario</th>
                <th className="text-left px-4 py-3 text-white/40 font-medium">IP</th>
                <th className="text-left px-4 py-3 text-white/40 font-medium">Ubicación</th>
                <th className="text-left px-4 py-3 text-white/40 font-medium">Dispositivo</th>
                <th className="text-left px-4 py-3 text-white/40 font-medium">Fecha</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center">
                    <Loader2 className="w-6 h-6 text-brand-orange animate-spin mx-auto" />
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-white/30">
                    No hay registros que coincidan con los filtros
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr
                    key={log.id}
                    className="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors"
                  >
                    <td className="px-4 py-3">
                      {log.success ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-xs">
                          <CheckCircle2 className="w-3 h-3" />
                          OK
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 text-xs">
                          <XCircle className="w-3 h-3" />
                          Fallido
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-white/80">
                      {log.user_email || log.user_id}
                    </td>
                    <td className="px-4 py-3 text-white/60 font-mono text-xs">
                      {log.ip_address}
                    </td>
                    <td className="px-4 py-3 text-white/60">
                      <span className="flex items-center gap-1">
                        <Globe className="w-3 h-3" />
                        {log.city || '?'}, {log.country || '?'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-white/40 text-xs truncate max-w-[200px]">
                      {log.user_agent || '—'}
                    </td>
                    <td className="px-4 py-3 text-white/40 text-xs">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(log.created_at).toLocaleString('es-AR')}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function StatCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: number
}) {
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
