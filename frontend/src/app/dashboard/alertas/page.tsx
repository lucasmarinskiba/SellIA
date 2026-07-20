'use client'

import { logger } from '@/lib/logger';
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bell, Check, X, Trash2, AlertTriangle, Info, AlertCircle, Loader2, Search, Filter } from 'lucide-react'
import { alertsApi, Alert, AlertStats } from '@/lib/alerts'
import { businessApi } from '@/lib/business'
import { Button } from '@/components/ui/Button'

export default function AlertasPage() {
  const [businesses, setBusinesses] = useState<any[]>([])
  const [selectedBusinessId, setSelectedBusinessId] = useState('')
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [stats, setStats] = useState<AlertStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [severityFilter, setSeverityFilter] = useState('')

  useEffect(() => {
    businessApi.list().then(res => {
      setBusinesses(res)
      if (res.length > 0) setSelectedBusinessId(res[0].id)
    })
  }, [])

  useEffect(() => {
    if (!selectedBusinessId) return
    loadData()
  }, [selectedBusinessId, statusFilter, severityFilter])

  async function loadData() {
    setLoading(true)
    try {
      const [alertsData, statsData] = await Promise.all([
        alertsApi.getAlerts(selectedBusinessId, {
          status: statusFilter || undefined,
          severity: severityFilter || undefined,
          limit: 100,
        }),
        alertsApi.getAlertStats(selectedBusinessId),
      ])
      setAlerts(alertsData)
      setStats(statsData)
    } catch (e) {
      logger.error(String(e))
    } finally {
      setLoading(false)
    }
  }

  async function markRead(id: string) {
    await alertsApi.markRead(id)
    loadData()
  }

  async function dismiss(id: string) {
    await alertsApi.dismissAlert(id)
    loadData()
  }

  async function remove(id: string) {
    await alertsApi.deleteAlert(id)
    loadData()
  }

  const severityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <AlertCircle className="w-5 h-5 text-red-400" />
      case 'warning': return <AlertTriangle className="w-5 h-5 text-amber-400" />
      default: return <Info className="w-5 h-5 text-blue-400" />
    }
  }

  const severityBadge = (severity: string) => {
    const classes = {
      critical: 'bg-red-500/10 text-red-400 border-red-500/20',
      warning: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      info: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    }
    return (
      <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${classes[severity as keyof typeof classes] || classes.info}`}>
        {severity}
      </span>
    )
  }

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Bell className="w-7 h-7 text-brand-orange" />
            Alertas
          </h1>
          <p className="text-sm text-white/40 mt-1">Notificaciones inteligentes de tu negocio</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={selectedBusinessId}
            onChange={e => setSelectedBusinessId(e.target.value)}
            className="bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-brand-orange/50"
          >
            {businesses.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl p-4">
            <p className="text-xs text-white/40">No leídas</p>
            <p className="text-2xl font-bold text-white mt-1">{stats.total_unread}</p>
          </div>
          <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl p-4">
            <p className="text-xs text-white/40">Leídas</p>
            <p className="text-2xl font-bold text-white/70 mt-1">{stats.total_read}</p>
          </div>
          <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl p-4">
            <p className="text-xs text-white/40">Descartadas</p>
            <p className="text-2xl font-bold text-white/50 mt-1">{stats.total_dismissed}</p>
          </div>
          <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl p-4">
            <p className="text-xs text-white/40">Críticas</p>
            <p className="text-2xl font-bold text-red-400 mt-1">{stats.by_severity.critical || 0}</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="bg-white/[0.04] border border-white/[0.08] rounded-xl px-3 py-2 text-sm text-white"
        >
          <option value="">Todos los estados</option>
          <option value="unread">No leídas</option>
          <option value="read">Leídas</option>
          <option value="dismissed">Descartadas</option>
        </select>
        <select
          value={severityFilter}
          onChange={e => setSeverityFilter(e.target.value)}
          className="bg-white/[0.04] border border-white/[0.08] rounded-xl px-3 py-2 text-sm text-white"
        >
          <option value="">Todas las severidades</option>
          <option value="critical">Crítica</option>
          <option value="warning">Advertencia</option>
          <option value="info">Info</option>
        </select>
        <button
          onClick={loadData}
          className="px-3 py-2 rounded-xl bg-white/[0.04] border border-white/[0.08] text-white/60 hover:text-white hover:bg-white/[0.08] transition-colors text-sm"
        >
          <Loader2 className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Alerts list */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-brand-orange animate-spin" />
        </div>
      ) : alerts.length === 0 ? (
        <div className="text-center py-20">
          <Bell className="w-12 h-12 text-white/10 mx-auto mb-4" />
          <p className="text-white/30">No hay alertas</p>
        </div>
      ) : (
        <div className="space-y-3">
          <AnimatePresence>
            {alerts.map((alert) => (
              <motion.div
                key={alert.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className={`bg-white/[0.02] border border-white/[0.06] rounded-2xl p-4 flex items-start gap-4 hover:bg-white/[0.04] transition-colors ${alert.status === 'unread' ? 'border-l-4 border-l-brand-orange' : ''}`}
              >
                <div className="mt-0.5">{severityIcon(alert.severity)}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className={`text-sm font-semibold ${alert.status === 'unread' ? 'text-white' : 'text-white/70'}`}>
                      {alert.title}
                    </h3>
                    {severityBadge(alert.severity)}
                    <span className="text-xs text-white/20">{new Date(alert.created_at).toLocaleString()}</span>
                  </div>
                  {alert.description && (
                    <p className="text-sm text-white/50 mb-2">{alert.description}</p>
                  )}
                  {alert.recommended_action && (
                    <p className="text-xs text-brand-orange/80 mb-2">💡 {alert.recommended_action}</p>
                  )}
                  <div className="flex items-center gap-2">
                    {alert.status === 'unread' && (
                      <button onClick={() => markRead(alert.id)} className="text-xs flex items-center gap-1 text-white/40 hover:text-white/70 transition-colors">
                        <Check className="w-3 h-3" /> Marcar leída
                      </button>
                    )}
                    {alert.status !== 'dismissed' && (
                      <button onClick={() => dismiss(alert.id)} className="text-xs flex items-center gap-1 text-white/40 hover:text-white/70 transition-colors">
                        <X className="w-3 h-3" /> Descartar
                      </button>
                    )}
                    <button onClick={() => remove(alert.id)} className="text-xs flex items-center gap-1 text-white/20 hover:text-red-400 transition-colors">
                      <Trash2 className="w-3 h-3" /> Eliminar
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}
