'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { autopilotApi, AutopilotConfig, AutopilotStatus, AutopilotOverview, AutopilotActionLog, AutopilotDailyReport } from '@/lib/autopilot'
import { businessApi } from '@/lib/business'
import StatCard from '@/components/ui/StatCard'
import Button from '@/components/ui/Button'
import {
  Brain, Play, Pause, CheckCircle, XCircle, AlertTriangle,
  Clock, TrendingUp, MessageSquare, DollarSign, Users,
  ShoppingBag, ArrowRight, Shield, Activity, Zap
} from 'lucide-react'

export default function AutopilotPage() {
  const { user } = useAuth()
  const [businessId, setBusinessId] = useState<string | null>(null)
  const [config, setConfig] = useState<AutopilotConfig | null>(null)
  const [status, setStatus] = useState<AutopilotStatus | null>(null)
  const [overview, setOverview] = useState<AutopilotOverview | null>(null)
  const [reports, setReports] = useState<AutopilotDailyReport[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchBusiness = async () => {
      try {
        const businesses = await businessApi.list()
        if (businesses.length > 0) {
          setBusinessId(businesses[0].id)
        }
      } catch (e) {
        setError('No se pudo cargar el negocio')
      }
    }
    fetchBusiness()
  }, [user])

  useEffect(() => {
    if (!businessId) return
    loadAll()
  }, [businessId])

  const loadAll = async () => {
    if (!businessId) return
    setLoading(true)
    try {
      const [cfg, st, ov, rep] = await Promise.all([
        autopilotApi.getConfig(businessId),
        autopilotApi.getStatus(businessId),
        autopilotApi.getOverview(businessId),
        autopilotApi.getDailyReports(businessId, 7),
      ])
      setConfig(cfg)
      setStatus(st)
      setOverview(ov)
      setReports(rep)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error cargando autopilot')
    } finally {
      setLoading(false)
    }
  }

  const toggleAutopilot = async () => {
    if (!businessId || !config) return
    try {
      if (config.is_active) {
        await autopilotApi.pause(businessId, 'Pausado por usuario desde dashboard')
      } else {
        await autopilotApi.resume(businessId)
      }
      await loadAll()
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error toggling autopilot')
    }
  }

  const handleApprove = async (actionId: string) => {
    try {
      await autopilotApi.approveAction(actionId)
      await loadAll()
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error aprobando acción')
    }
  }

  const handleReject = async (actionId: string) => {
    try {
      await autopilotApi.rejectAction(actionId, 'Rechazado por usuario desde dashboard')
      await loadAll()
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error rechazando acción')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-3">
          <Brain className="w-10 h-10 text-brand-orange animate-pulse" />
          <p className="text-sm text-white/40">Cargando SellIA Autopilot...</p>
        </div>
      </div>
    )
  }

  const isRunning = config?.is_active && !config?.is_paused

  return (
    <div className="space-y-8 max-w-7xl">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${isRunning ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">SellIA Autopilot</h1>
              <p className="text-sm text-white/50">
                {isRunning ? 'Tu vendedor automático está trabajando 24/7' : 'Autopilot está pausado'}
              </p>
            </div>
          </div>
        </div>
        <Button
          variant={isRunning ? 'secondary' : 'primary'}
          leftIcon={isRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          onClick={toggleAutopilot}
        >
          {isRunning ? 'Pausar Autopilot' : 'Activar Autopilot'}
        </Button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Sleep Summary */}
      {overview?.message && (
        <div className="p-6 rounded-2xl bg-gradient-to-r from-brand-orange/10 to-brand-teal/10 border border-brand-orange/20">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-brand-orange/20 flex items-center justify-center shrink-0">
              <Zap className="w-6 h-6 text-brand-orange" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white mb-1">Mientras dormiste, SellIA...</h2>
              <p className="text-white/70">{overview.message}</p>
            </div>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Acciones hoy"
          value={String(status?.today_executed || 0)}
          icon={<Activity className="w-5 h-5" />}
          color="teal"
        />
        <StatCard
          label="Pendientes de aprobación"
          value={String(status?.today_pending || 0)}
          icon={<Clock className="w-5 h-5" />}
          color="orange"
        />
        <StatCard
          label="Escaladas a humano"
          value={String(status?.today_escalated || 0)}
          icon={<AlertTriangle className="w-5 h-5" />}
          color="violet"
        />
        <StatCard
          label="Revenue generado hoy"
          value={`$${Number(status?.today_revenue || 0).toLocaleString()}`}
          icon={<DollarSign className="w-5 h-5" />}
          color="teal"
        />
      </div>

      {/* Pending Actions */}
      {overview?.pending_actions && overview.pending_actions.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Clock className="w-5 h-5 text-brand-orange" />
            Acciones que requieren tu aprobación
          </h2>
          <div className="space-y-3">
            {overview.pending_actions.map((action) => (
              <ActionCard
                key={action.id}
                action={action}
                onApprove={() => handleApprove(action.id)}
                onReject={() => handleReject(action.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Escalations */}
      {overview?.escalations && overview.escalations.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            Escalaciones recientes
          </h2>
          <div className="space-y-3">
            {overview.escalations.map((action) => (
              <EscalationCard key={action.id} action={action} />
            ))}
          </div>
        </div>
      )}

      {/* Daily Reports */}
      {reports.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-brand-teal" />
            Historial diario
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {reports.map((report) => (
              <ReportCard key={report.id} report={report} />
            ))}
          </div>
        </div>
      )}

      {/* Configuration */}
      {config && (
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Shield className="w-5 h-5 text-brand-violet" />
            Configuración de Autopilot
          </h2>
          <ConfigGrid config={config} onToggle={loadAll} />
        </div>
      )}
    </div>
  )
}

function ActionCard({ action, onApprove, onReject }: { action: AutopilotActionLog; onApprove: () => void; onReject: () => void }) {
  return (
    <div className="p-4 rounded-xl bg-white/5 border border-white/10">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded-md bg-brand-orange/20 text-brand-orange text-xs font-medium uppercase">
              {action.action_type}
            </span>
            <span className="text-xs text-white/40">{new Date(action.created_at).toLocaleString()}</span>
          </div>
          <p className="text-sm text-white/80">{action.reason}</p>
          {action.ai_explanation && (
            <p className="text-xs text-white/50 mt-1">{action.ai_explanation}</p>
          )}
          {action.revenue_impact && (
            <p className="text-xs text-emerald-400 mt-1">Impacto: ${Number(action.revenue_impact).toLocaleString()}</p>
          )}
        </div>
        <div className="flex items-center gap-2 ml-4">
          <Button variant="primary" size="sm" leftIcon={<CheckCircle className="w-4 h-4" />} onClick={onApprove}>
            Aprobar
          </Button>
          <Button variant="secondary" size="sm" leftIcon={<XCircle className="w-4 h-4" />} onClick={onReject}>
            Rechazar
          </Button>
        </div>
      </div>
    </div>
  )
}

function EscalationCard({ action }: { action: AutopilotActionLog }) {
  return (
    <div className="p-4 rounded-xl bg-red-500/5 border border-red-500/20">
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded-md bg-red-500/20 text-red-400 text-xs font-medium uppercase">
              {action.action_type}
            </span>
            <span className="text-xs text-white/40">{new Date(action.created_at).toLocaleString()}</span>
          </div>
          <p className="text-sm text-white/80">{action.reason}</p>
          {action.error_message && (
            <p className="text-xs text-red-400 mt-1">Error: {action.error_message}</p>
          )}
        </div>
      </div>
    </div>
  )
}

function ReportCard({ report }: { report: AutopilotDailyReport }) {
  return (
    <div className="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-white/20 transition-colors">
      <h3 className="text-sm font-medium text-white/60 mb-3">
        {new Date(report.report_date).toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'short' })}
      </h3>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="text-xs text-white/40">Leads</p>
          <p className="text-lg font-bold text-white">{report.leads_contacted}</p>
        </div>
        <div>
          <p className="text-xs text-white/40">Deals cerrados</p>
          <p className="text-lg font-bold text-white">{report.deals_closed}</p>
        </div>
        <div>
          <p className="text-xs text-white/40">Mensajes</p>
          <p className="text-lg font-bold text-white">{report.messages_sent}</p>
        </div>
        <div>
          <p className="text-xs text-white/40">Revenue</p>
          <p className="text-lg font-bold text-emerald-400">${Number(report.revenue_generated).toLocaleString()}</p>
        </div>
      </div>
      {report.ai_summary && (
        <p className="text-xs text-white/50 mt-3 line-clamp-2">{report.ai_summary}</p>
      )}
    </div>
  )
}

function ConfigGrid({ config, onToggle }: { config: AutopilotConfig; onToggle: () => void }) {
  const [updating, setUpdating] = useState<string | null>(null)

  const toggleField = async (field: keyof AutopilotConfig) => {
    if (!config) return
    setUpdating(field)
    try {
      await autopilotApi.updateConfig(config.business_id, { [field]: !config[field] })
      onToggle()
    } finally {
      setUpdating(null)
    }
  }

  const fields: { key: keyof AutopilotConfig; label: string; icon: any; description: string }[] = [
    { key: 'auto_qualify_leads', label: 'Calificar leads', icon: Users, description: 'Asignar score automáticamente' },
    { key: 'auto_move_deals', label: 'Mover deals', icon: TrendingUp, description: 'Avanzar deals en el pipeline' },
    { key: 'auto_send_followups', label: 'Enviar seguimientos', icon: MessageSquare, description: 'Follow-ups automáticos con cadencia inteligente' },
    { key: 'auto_close_deals', label: 'Cerrar deals', icon: CheckCircle, description: 'Cierre automático cuando detecta señal de compra' },
    { key: 'auto_create_orders', label: 'Crear órdenes', icon: ShoppingBag, description: 'Generar órdenes desde deals cerrados' },
    { key: 'auto_request_reviews', label: 'Solicitar reviews', icon: Star, description: 'Pedir NPS post-compra' },
    { key: 'auto_activate_recovery_workflows', label: 'Recuperación', icon: Zap, description: 'Activar workflows de win-back' },
    { key: 'auto_escalate_to_human', label: 'Escalar a humano', icon: Shield, description: 'Escalar cuando el sistema no puede resolver' },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {fields.map(({ key, label, icon: Icon, description }) => (
        <button
          key={key}
          onClick={() => toggleField(key)}
          disabled={updating === key}
          className={`p-4 rounded-xl border text-left transition-all ${
            config[key]
              ? 'bg-emerald-500/10 border-emerald-500/30'
              : 'bg-white/5 border-white/10 hover:border-white/20'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <Icon className={`w-5 h-5 ${config[key] ? 'text-emerald-400' : 'text-white/40'}`} />
            <div className={`w-8 h-5 rounded-full transition-colors ${config[key] ? 'bg-emerald-500' : 'bg-white/20'}`}>
              <div className={`w-4 h-4 rounded-full bg-white transition-transform ${config[key] ? 'translate-x-4' : 'translate-x-0.5'} mt-0.5`} />
            </div>
          </div>
          <p className={`font-medium ${config[key] ? 'text-emerald-400' : 'text-white/60'}`}>{label}</p>
          <p className="text-xs text-white/40 mt-1">{description}</p>
        </button>
      ))}
    </div>
  )
}

// Missing import
function Star({ className }: { className?: string }) {
  return (
    <svg className={className} width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  )
}
