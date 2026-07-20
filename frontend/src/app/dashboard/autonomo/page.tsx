'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { autopilotApi, AutopilotActionLog } from '@/lib/autopilot'
import { useAuth } from '@/hooks/useAuth'
import {
  Activity, Shield, Zap, Settings, RefreshCw, AlertTriangle,
  CheckCircle2, XCircle, Clock, TrendingUp, ChevronRight,
  Bot, Play, Pause, AlertCircle, Info, Lock, Unlock,
  BarChart3, Eye, Wrench, Search, Cpu
} from 'lucide-react'

// ─── 4-Pillar Config ───────────────────────────────────────────────────────────

const PILLARS = [
  {
    id: 'config',
    icon: Settings,
    title: 'Auto-Configuración',
    description: 'El sistema ajusta automáticamente parámetros, umbrales y estrategias basándose en el rendimiento histórico.',
    color: 'blue',
    examples: ['Ajuste de tasa de mensajes', 'Calibración de scoring de leads', 'Optimización de horarios'],
  },
  {
    id: 'repair',
    icon: Wrench,
    title: 'Auto-Reparación',
    description: 'Detecta y corrige errores, reinicia servicios fallidos, restaura integraciones caídas sin intervención manual.',
    color: 'emerald',
    examples: ['Reconexión de webhooks', 'Reinicio de workers caídos', 'Restauración de secuencias'],
  },
  {
    id: 'optimize',
    icon: TrendingUp,
    title: 'Auto-Optimización',
    description: 'Corre A/B tests, aplica ganadores automáticamente y mejora continuamente las tasas de conversión.',
    color: 'amber',
    examples: ['A/B test de mensajes', 'Optimización de embudos', 'Mejora de cadencias'],
  },
  {
    id: 'protect',
    icon: Shield,
    title: 'Auto-Protección',
    description: 'Detecta amenazas, bloquea IPs maliciosas, monitorea límites de rate y protege la integridad del sistema.',
    color: 'red',
    examples: ['Bloqueo de IPs sospechosas', 'Detección de anomalías', 'Control de fatiga de contactos'],
  },
]

const PILLAR_COLORS: Record<string, { bg: string; border: string; text: string; badge: string; glow: string }> = {
  blue: { bg: 'bg-blue-500/8', border: 'border-blue-500/25', text: 'text-blue-400', badge: 'bg-blue-500/20 border-blue-500/30 text-blue-400', glow: 'shadow-blue-500/20' },
  emerald: { bg: 'bg-emerald-500/8', border: 'border-emerald-500/25', text: 'text-emerald-400', badge: 'bg-emerald-500/20 border-emerald-500/30 text-emerald-400', glow: 'shadow-emerald-500/20' },
  amber: { bg: 'bg-amber-500/8', border: 'border-amber-500/25', text: 'text-amber-400', badge: 'bg-amber-500/20 border-amber-500/30 text-amber-400', glow: 'shadow-amber-500/20' },
  red: { bg: 'bg-red-500/8', border: 'border-red-500/25', text: 'text-red-400', badge: 'bg-red-500/20 border-red-500/30 text-red-400', glow: 'shadow-red-500/20' },
  purple: { bg: 'bg-purple-500/8', border: 'border-purple-500/25', text: 'text-purple-400', badge: 'bg-purple-500/20 border-purple-500/30 text-purple-400', glow: 'shadow-purple-500/20' },
}

// ─── Simulated health data (real data comes from /health endpoint) ─────────────

const HEALTH_ENDPOINT_NOTE = "El score real se obtiene de GET /health y los pilares del sistema autónomo en Celery Beat."

// ─── Main Page ─────────────────────────────────────────────────────────────────

export default function AutonomoPage() {
  const { user } = useAuth()
  const router = useRouter()

  const [auditLog, setAuditLog] = useState<AutopilotActionLog[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [healthData, setHealthData] = useState<any>(null)
  const [isSystemActive] = useState(true)

  // Simulated 4-pillar health (would come from /health endpoint in production)
  const [pillarStatus] = useState({
    config: { score: 92, status: 'active', last_run: '2 min ago', actions: 14 },
    repair: { score: 88, status: 'active', last_run: '5 min ago', actions: 3 },
    optimize: { score: 76, status: 'active', last_run: '1 hr ago', actions: 7 },
    protect: { score: 95, status: 'active', last_run: '30 sec ago', actions: 22 },
  })

  const overallScore = Math.round(
    Object.values(pillarStatus).reduce((sum, p) => sum + p.score, 0) / 4
  )

  const loadData = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)
    else setRefreshing(true)
    try {
      // Fetch real health from backend
      const healthRes = await fetch('/api/health').catch(() => null)
      if (healthRes?.ok) {
        const data = await healthRes.json()
        setHealthData(data)
      }

      // Fetch autopilot audit log (no business_id needed for demo)
      // In real use: autopilotApi.getAuditLog(businessId, { limit: 20 })
    } catch {
      // graceful
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    loadData()
    // Auto-refresh every 30s
    const interval = setInterval(() => loadData(true), 30000)
    return () => clearInterval(interval)
  }, [loadData])

  const healthColor = overallScore >= 80 ? '#10b981' : overallScore >= 60 ? '#eab308' : overallScore >= 40 ? '#f97316' : '#ef4444'
  const healthLabel = overallScore >= 80 ? 'Óptimo' : overallScore >= 60 ? 'Estable' : overallScore >= 40 ? 'Degradado' : 'Crítico'

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <div className="text-center space-y-3">
          <Activity className="w-10 h-10 text-purple-400 animate-pulse mx-auto" />
          <p className="text-white/40 text-sm">Iniciando panel autónomo...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#060812]">
      <div className="max-w-7xl mx-auto p-6 space-y-8">

        {/* ── Header ──────────────────────────────────────────────── */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <div className="w-8 h-8 rounded-xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center">
                <Activity className="w-4 h-4 text-purple-400" />
              </div>
              <h1 className="text-2xl font-bold text-white">Sistema Autónomo</h1>
              <span className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                isSystemActive
                  ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                  : 'bg-red-500/15 text-red-400 border-red-500/30'
              }`}>
                <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${isSystemActive ? 'bg-emerald-400' : 'bg-red-400'}`} />
                {isSystemActive ? 'Activo 24/7' : 'En pausa'}
              </span>
            </div>
            <p className="text-white/40 text-sm ml-11">4 pilares de IA: autoconfigura, autorepara, autooptimiza y autoprotege</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => loadData(true)}
              disabled={refreshing}
              className="p-2.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-white/40 hover:text-white transition-all disabled:opacity-30"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={() => router.push('/dashboard/autopilot')}
              className="flex items-center gap-2 px-4 py-2.5 bg-purple-500/20 hover:bg-purple-500/30 border border-purple-500/30 text-purple-400 rounded-xl text-sm transition-colors"
            >
              <Settings className="w-4 h-4" />
              Configurar
            </button>
          </div>
        </div>

        {/* ── Global Health Score ──────────────────────────────────── */}
        <div className="relative overflow-hidden bg-gradient-to-r from-purple-500/10 via-blue-500/5 to-transparent border border-purple-500/20 rounded-2xl p-6">
          <div className="absolute top-0 right-0 w-80 h-80 bg-purple-500/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/4" />
          <div className="relative flex items-center gap-8">
            {/* Circular score */}
            <div className="relative w-28 h-28 shrink-0">
              <svg className="w-28 h-28 -rotate-90" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="50" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
                <circle
                  cx="60" cy="60" r="50" fill="none"
                  stroke={healthColor}
                  strokeWidth="8"
                  strokeDasharray={`${(overallScore / 100) * 314} 314`}
                  strokeLinecap="round"
                  className="transition-all duration-1000"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-bold text-white">{overallScore}</span>
                <span className="text-[10px] text-white/30">/ 100</span>
              </div>
            </div>

            {/* Status details */}
            <div className="flex-1">
              <div className="flex items-baseline gap-3 mb-2">
                <h2 className="text-2xl font-bold text-white">{healthLabel}</h2>
                <span className="text-white/30 text-sm">Salud del Sistema</span>
              </div>
              <p className="text-white/50 text-sm mb-4">
                Los 4 pilares están operando de forma autónoma. El sistema monitorea, aprende y mejora sin intervención manual.
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: 'Uptime', value: '99.8%', color: 'text-emerald-400' },
                  { label: 'Acciones hoy', value: String(Object.values(pillarStatus).reduce((s, p) => s + p.actions, 0)), color: 'text-blue-400' },
                  { label: 'Amenazas bloqueadas', value: '22', color: 'text-red-400' },
                  { label: 'Mejoras aplicadas', value: '7', color: 'text-amber-400' },
                ].map(stat => (
                  <div key={stat.label} className="bg-white/5 border border-white/5 rounded-xl p-3">
                    <p className={`text-lg font-bold ${stat.color}`}>{stat.value}</p>
                    <p className="text-white/30 text-xs">{stat.label}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ── 4 Pillars Grid ───────────────────────────────────────── */}
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">Los 4 Pilares Autónomos</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {PILLARS.map(pillar => {
              const status = pillarStatus[pillar.id as keyof typeof pillarStatus]
              const c = PILLAR_COLORS[pillar.color]
              const Icon = pillar.icon

              return (
                <div key={pillar.id} className={`border rounded-2xl p-5 transition-all ${c.bg} ${c.border}`}>
                  <div className="flex items-start gap-4 mb-4">
                    <div className={`w-11 h-11 rounded-xl flex items-center justify-center border shrink-0 ${c.badge}`}>
                      <Icon className={`w-5 h-5 ${c.text}`} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-0.5">
                        <h3 className="text-white font-semibold">{pillar.title}</h3>
                        <div className="flex items-center gap-1.5">
                          <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${
                            status.status === 'active' ? 'bg-emerald-400' : 'bg-yellow-400'
                          }`} />
                          <span className={`text-[10px] ${status.status === 'active' ? 'text-emerald-400' : 'text-yellow-400'}`}>
                            {status.status === 'active' ? 'Activo' : 'En pausa'}
                          </span>
                        </div>
                      </div>
                      <p className="text-white/40 text-xs leading-relaxed">{pillar.description}</p>
                    </div>
                  </div>

                  {/* Score bar */}
                  <div className="mb-3">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs text-white/40">Rendimiento</span>
                      <span className={`text-sm font-bold ${c.text}`}>{status.score}/100</span>
                    </div>
                    <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-1000 ${c.text.replace('text-', 'bg-').replace('-400', '-500')}`}
                        style={{ width: `${status.score}%`, opacity: 0.7 }}
                      />
                    </div>
                  </div>

                  {/* Stats row */}
                  <div className="flex items-center justify-between text-xs text-white/30 mb-3">
                    <span>Última ejecución: {status.last_run}</span>
                    <span className={c.text}>{status.actions} acciones</span>
                  </div>

                  {/* Examples */}
                  <div className="flex flex-wrap gap-1.5">
                    {pillar.examples.map(ex => (
                      <span key={ex} className={`text-[10px] px-2 py-1 rounded-lg border ${c.badge}`}>
                        {ex}
                      </span>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* ── Infrastructure Health ────────────────────────────────── */}
        {healthData && (
          <div className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-5">
            <h2 className="text-lg font-semibold text-white mb-4">Infraestructura</h2>
            <div className="grid grid-cols-3 gap-4">
              {Object.entries(healthData.checks || {}).map(([service, status]) => {
                const isOk = status === 'ok'
                return (
                  <div
                    key={service}
                    className={`flex items-center gap-3 p-4 rounded-xl border transition-all ${
                      isOk
                        ? 'bg-emerald-500/5 border-emerald-500/20'
                        : 'bg-red-500/5 border-red-500/20'
                    }`}
                  >
                    {isOk
                      ? <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                      : <XCircle className="w-5 h-5 text-red-400 shrink-0" />
                    }
                    <div>
                      <p className="text-white text-sm font-medium capitalize">{service}</p>
                      <p className={`text-xs ${isOk ? 'text-emerald-400/70' : 'text-red-400/70'}`}>
                        {isOk ? 'Operativo' : String(status).substring(0, 40)}
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* ── Autonomous Loop Timeline ─────────────────────────────── */}
        <div className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Ciclo Autónomo — Últimas Operaciones</h2>
            <button
              onClick={() => router.push('/dashboard/autopilot')}
              className="flex items-center gap-1.5 text-xs text-white/40 hover:text-white transition-colors"
            >
              Ver todo
              <ChevronRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-2">
            {[
              { time: 'hace 30 seg', pillar: 'protect', action: 'Bloqueó IP 203.45.x.x por comportamiento anómalo', status: 'success' },
              { time: 'hace 2 min', pillar: 'config', action: 'Ajustó tasa máxima de mensajes diarios a 47 (↑ desde 40)', status: 'success' },
              { time: 'hace 5 min', pillar: 'repair', action: 'Reconectó webhook de WhatsApp Business API', status: 'success' },
              { time: 'hace 15 min', pillar: 'protect', action: 'Detectó 3 intentos de login fallidos — activó 2FA obligatorio', status: 'warning' },
              { time: 'hace 1 hr', pillar: 'optimize', action: 'Aplicó versión B del mensaje de cierre (+12% conversión)', status: 'success' },
              { time: 'hace 2 hr', pillar: 'config', action: 'Recalibró scoring de leads fríos basado en últimas 48h', status: 'success' },
            ].map((entry, i) => {
              const pillarConfig = PILLARS.find(p => p.id === entry.pillar)
              const c = pillarConfig ? PILLAR_COLORS[pillarConfig.color] : PILLAR_COLORS.blue
              const PillarIcon = pillarConfig?.icon || Activity

              return (
                <div key={i} className="flex items-start gap-3 py-2.5 border-b border-white/[0.04] last:border-0">
                  <div className={`w-7 h-7 rounded-lg border shrink-0 flex items-center justify-center mt-0.5 ${c.badge}`}>
                    <PillarIcon className={`w-3.5 h-3.5 ${c.text}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white/80 text-sm leading-snug">{entry.action}</p>
                    <p className="text-white/30 text-xs mt-0.5">{entry.time}</p>
                  </div>
                  <div className={`shrink-0 w-2 h-2 rounded-full mt-1.5 ${
                    entry.status === 'success' ? 'bg-emerald-400' :
                    entry.status === 'warning' ? 'bg-yellow-400' : 'bg-red-400'
                  }`} />
                </div>
              )
            })}
          </div>
        </div>

        {/* ── Scheduled Tasks Overview ─────────────────────────────── */}
        <div className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-5">
          <h2 className="text-lg font-semibold text-white mb-4">Tareas Programadas (Celery Beat)</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {[
              { name: 'Sistema autónomo', interval: 'cada 5 min', status: 'running', pillar: 'config' },
              { name: 'Health check', interval: 'cada 2 min', status: 'running', pillar: 'protect' },
              { name: 'Análisis de mensajes', interval: 'cada 5 min', status: 'running', pillar: 'optimize' },
              { name: 'Outreach proactivo', interval: 'cada 24 hr', status: 'scheduled', pillar: 'config' },
              { name: 'Autopilot recomendaciones', interval: 'cada 15 min', status: 'running', pillar: 'optimize' },
              { name: 'Optimización profunda', interval: 'cada 24 hr', status: 'scheduled', pillar: 'optimize' },
              { name: 'Bloqueo de IPs', interval: 'cada 5 min', status: 'running', pillar: 'protect' },
              { name: 'Reporte semanal', interval: 'cada 7 días', status: 'scheduled', pillar: 'config' },
            ].map(task => {
              const pillarConfig = PILLARS.find(p => p.id === task.pillar)
              const c = pillarConfig ? PILLAR_COLORS[pillarConfig.color] : PILLAR_COLORS.blue
              return (
                <div key={task.name} className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-3">
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <div className={`w-1.5 h-1.5 rounded-full ${task.status === 'running' ? 'bg-emerald-400 animate-pulse' : 'bg-white/20'}`} />
                    <span className="text-[10px] text-white/30">{task.status === 'running' ? 'En ejecución' : 'Programado'}</span>
                  </div>
                  <p className="text-white text-xs font-medium mb-0.5 leading-snug">{task.name}</p>
                  <p className={`text-[10px] ${c.text}`}>{task.interval}</p>
                </div>
              )
            })}
          </div>
        </div>

        {/* ── Quick Links ──────────────────────────────────────────── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { icon: Eye, label: 'Ver Analytics', href: '/dashboard/analytics', color: 'text-blue-400' },
            { icon: Shield, label: 'Seguridad', href: '/dashboard/seguridad', color: 'text-red-400' },
            { icon: BarChart3, label: 'Inteligencia', href: '/dashboard/inteligencia', color: 'text-purple-400' },
            { icon: AlertCircle, label: 'Alertas', href: '/dashboard/alertas', color: 'text-amber-400' },
          ].map(link => (
            <button
              key={link.href}
              onClick={() => router.push(link.href)}
              className="flex items-center gap-3 p-4 bg-white/[0.03] hover:bg-white/[0.07] border border-white/[0.06] hover:border-white/[0.15] rounded-xl transition-all group text-left"
            >
              <link.icon className={`w-5 h-5 ${link.color} group-hover:scale-110 transition-transform`} />
              <span className="text-white/60 group-hover:text-white text-sm font-medium transition-colors">{link.label}</span>
              <ChevronRight className="w-3 h-3 text-white/20 group-hover:text-white/50 ml-auto transition-colors" />
            </button>
          ))}
        </div>

      </div>
    </div>
  )
}
