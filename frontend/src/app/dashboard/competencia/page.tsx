'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { competitiveApi, Monitor, ChangeItem, StrategySuggestion } from '@/lib/api/competitive'
import { useAuth } from '@/hooks/useAuth'
import {
  Eye,
  Loader2,
  AlertCircle,
  Plus,
  ScanLine,
  Trash2,
  TrendingDown,
  TrendingUp,
  Minus,
  BrainCircuit,
  X,
  ExternalLink,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Zap,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/Dialog'

interface AlertBanner {
  severity: 'urgent' | 'warning'
  message: string
}

export default function CompetenciaPage() {
  const { user } = useAuth()
  const businessId = (user as any)?.business_id || (user as any)?.businesses?.[0]?.id || ''

  const [monitors, setMonitors] = useState<Monitor[]>([])
  const [changes, setChanges] = useState<ChangeItem[]>([])
  const [strategies, setStrategies] = useState<StrategySuggestion[]>([])
  const [alertsCount, setAlertsCount] = useState(0)
  const [unreadAlerts, setUnreadAlerts] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [addModalOpen, setAddModalOpen] = useState(false)
  const [scrapingId, setScrapingId] = useState<string | null>(null)
  const [strategyModal, setStrategyModal] = useState<StrategySuggestion | null>(null)

  const [newMonitor, setNewMonitor] = useState({
    competitor_name: '',
    competitor_url: '',
    products_to_track: '',
  })

  useEffect(() => {
    if (businessId) {
      fetchData()
    }
  }, [businessId])

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const dashboard = await competitiveApi.getIntelligence(businessId)
      setMonitors(dashboard.monitors || [])
      setChanges(dashboard.recent_changes || [])
      setStrategies(dashboard.strategies || [])
      setAlertsCount(dashboard.alerts_count || 0)
      setUnreadAlerts(dashboard.unread_alerts || 0)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Error cargando inteligencia competitiva')
    } finally {
      setLoading(false)
    }
  }

  const handleAddMonitor = async () => {
    if (!newMonitor.competitor_name.trim() || !newMonitor.competitor_url.trim()) return
    try {
      await competitiveApi.createMonitor({
        business_id: businessId,
        competitor_name: newMonitor.competitor_name,
        competitor_url: newMonitor.competitor_url,
        products_to_track: newMonitor.products_to_track
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
      })
      setNewMonitor({ competitor_name: '', competitor_url: '', products_to_track: '' })
      setAddModalOpen(false)
      await fetchData()
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Error creando monitor')
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('¿Eliminar este competidor del monitoreo?')) return
    try {
      await competitiveApi.deleteMonitor(id)
      await fetchData()
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Error eliminando monitor')
    }
  }

  const handleScrape = async (id: string) => {
    setScrapingId(id)
    try {
      await competitiveApi.scrapeMonitor(id)
      await fetchData()
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Error escaneando competidor')
    } finally {
      setScrapingId(null)
    }
  }

  const alertBanners: AlertBanner[] = changes
    .filter((c) => c.severity === 'critical' || c.severity === 'warning')
    .slice(0, 3)
    .map((c) => ({
      severity: c.severity === 'critical' ? 'urgent' : 'warning',
      message:
        c.change_type === 'price_down'
          ? `Urgente: ${c.competitor_name} bajó precio de ${c.product_name || 'producto'} ${c.diff_percent?.toFixed(0) || ''}%`
          : c.change_type === 'promo_started'
          ? `Aviso: ${c.competitor_name} lanzó promoción`
          : `Cambio detectado: ${c.competitor_name} — ${c.change_type}`,
    }))

  const severityIcon = (severity: string) => {
    if (severity === 'critical') return <AlertTriangle className="w-4 h-4 text-red-400" />
    if (severity === 'warning') return <AlertCircle className="w-4 h-4 text-amber-400" />
    return <CheckCircle2 className="w-4 h-4 text-emerald-400" />
  }

  const statusBadge = (status: string) => {
    if (status === 'active')
      return <Badge variant="success" className="text-[10px]">Activo</Badge>
    if (status === 'error')
      return <Badge variant="destructive" className="text-[10px]">Error</Badge>
    return <Badge variant="outline" className="text-[10px]">Pausado</Badge>
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#060812]">
      <div className="max-w-7xl mx-auto px-6 py-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-brand-orange/10">
              <Eye className="w-6 h-6 text-brand-orange" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Tu Espía 24/7</h1>
              <p className="text-sm text-white/50">La competencia no duerme. Nosotros tampoco.</p>
            </div>
          </div>
          <Button size="sm" leftIcon={<Plus className="w-4 h-4" />} onClick={() => setAddModalOpen(true)}>
            Agregar competidor
          </Button>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm mb-6">
            <AlertCircle className="w-4 h-4" />
            {error}
            <button onClick={() => setError(null)} className="ml-auto">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Alert Banners */}
        <AnimatePresence>
          {alertBanners.length > 0 && (
            <div className="space-y-3 mb-8">
              {alertBanners.map((alert, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl border text-sm font-medium ${
                    alert.severity === 'urgent'
                      ? 'bg-red-500/10 border-red-500/20 text-red-400'
                      : 'bg-amber-500/10 border-amber-500/20 text-amber-400'
                  }`}
                >
                  {alert.severity === 'urgent' ? (
                    <span className="text-base">🔴</span>
                  ) : (
                    <span className="text-base">🟡</span>
                  )}
                  {alert.message}
                </motion.div>
              ))}
            </div>
          )}
        </AnimatePresence>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="p-5 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
            <p className="text-xs uppercase tracking-wider text-white/40 mb-1">Monitoreados</p>
            <p className="text-2xl font-bold text-white">{monitors.length}</p>
          </div>
          <div className="p-5 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
            <p className="text-xs uppercase tracking-wider text-white/40 mb-1">Cambios hoy</p>
            <p className="text-2xl font-bold text-white">{changes.length}</p>
          </div>
          <div className="p-5 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
            <p className="text-xs uppercase tracking-wider text-white/40 mb-1">Alertas sin leer</p>
            <p className="text-2xl font-bold text-white">{unreadAlerts}</p>
          </div>
        </div>

        {/* Competitor Cards */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-white mb-4">Competidores monitoreados</h2>
          {monitors.length === 0 ? (
            <div className="p-8 rounded-2xl bg-white/[0.03] border border-white/[0.06] text-center">
              <Eye className="w-8 h-8 text-white/20 mx-auto mb-3" />
              <p className="text-sm text-white/40">No hay competidores monitoreados todavía.</p>
              <Button size="sm" className="mt-4" onClick={() => setAddModalOpen(true)}>
                Agregar el primero
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {monitors.map((monitor) => {
                const snapshotPrices = monitor.last_snapshot?.prices || {}
                const priceEntries = Object.entries(snapshotPrices).slice(0, 4)
                return (
                  <motion.div
                    key={monitor.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-5 rounded-2xl bg-white/[0.03] border border-white/[0.06] hover:border-white/[0.1] transition-colors"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-sm font-semibold text-white">{monitor.competitor_name}</h3>
                          {statusBadge(monitor.status)}
                        </div>
                        <a
                          href={monitor.competitor_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-white/40 hover:text-brand-orange flex items-center gap-1"
                        >
                          {monitor.competitor_url.replace(/^https?:\/\//, '').slice(0, 40)}
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                      <div className="flex items-center gap-1 text-xs text-white/30">
                        <Clock className="w-3 h-3" />
                        {monitor.last_scraped_at
                          ? new Date(monitor.last_scraped_at).toLocaleString('es-AR', {
                              hour: '2-digit',
                              minute: '2-digit',
                              day: 'numeric',
                              month: 'short',
                            })
                          : 'Sin escanear'}
                      </div>
                    </div>

                    {/* Price Table */}
                    {priceEntries.length > 0 && (
                      <div className="overflow-x-auto rounded-xl border border-white/[0.06] mb-4">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="border-b border-white/[0.06]">
                              <th className="text-left px-3 py-2 text-white/40 font-medium">Producto / Línea</th>
                              <th className="text-right px-3 py-2 text-white/40 font-medium">Precio detectado</th>
                              <th className="text-center px-3 py-2 text-white/40 font-medium">Tendencia</th>
                            </tr>
                          </thead>
                          <tbody>
                            {priceEntries.map(([key, val], i) => (
                              <tr key={i} className={i % 2 === 0 ? 'bg-white/[0.01]' : 'bg-transparent'}>
                                <td className="px-3 py-2 text-white/70 truncate max-w-[180px]">{key}</td>
                                <td className="px-3 py-2 text-right text-white font-medium">${String(val)}</td>
                                <td className="px-3 py-2 text-center">
                                  <Minus className="w-3.5 h-3.5 text-white/20 mx-auto" />
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-xs"
                        leftIcon={scrapingId === monitor.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <ScanLine className="w-3 h-3" />}
                        onClick={() => handleScrape(monitor.id)}
                        disabled={scrapingId === monitor.id}
                      >
                        Escanear ahora
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-xs text-white/40 hover:text-white"
                        onClick={() => {
                          const strat = strategies.find((s) => s.change.competitor_name === monitor.competitor_name)
                          if (strat) setStrategyModal(strat)
                        }}
                      >
                        Ver estrategia
                      </Button>
                      <button
                        onClick={() => handleDelete(monitor.id)}
                        className="ml-auto p-2 rounded-lg hover:bg-red-500/10 text-white/20 hover:text-red-400 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </motion.div>
                )
              })}
            </div>
          )}
        </div>

        {/* Strategy Panel */}
        {strategies.length > 0 && (
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-4">
              <BrainCircuit className="w-5 h-5 text-brand-violet" />
              <h2 className="text-lg font-semibold text-white">Estrategias sugeridas por IA</h2>
            </div>
            <div className="space-y-3">
              {strategies.map((strat, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className="p-5 rounded-2xl bg-white/[0.03] border border-white/[0.06]"
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-brand-violet/10 mt-0.5">
                      <Zap className="w-4 h-4 text-brand-violet" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-white mb-1">
                        {strat.change.competitor_name} — {strat.change.change_type}
                      </p>
                      <p className="text-sm text-white/60 mb-2">{strat.suggestion}</p>
                      {strat.risk_note && (
                        <p className="text-xs text-amber-400/80 mb-2">{strat.risk_note}</p>
                      )}
                      <div className="flex flex-wrap gap-2">
                        {strat.options.map((opt, i) => (
                          <Badge key={i} variant="outline" className="text-[10px]">
                            {opt}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Recent Changes */}
        {changes.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-white mb-4">Cambios recientes detectados</h2>
            <div className="space-y-2">
              {changes.map((change, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white/[0.02] border border-white/[0.06]"
                >
                  {severityIcon(change.severity)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white truncate">
                      {change.competitor_name}
                      {change.product_name ? ` — ${change.product_name}` : ''}
                    </p>
                    <p className="text-xs text-white/40">
                      {change.change_type}
                      {change.diff_percent !== undefined && change.diff_percent !== null
                        ? ` (${change.diff_percent > 0 ? '+' : ''}${change.diff_percent.toFixed(1)}%)`
                        : ''}
                    </p>
                  </div>
                  <span className="text-xs text-white/30 whitespace-nowrap">
                    {new Date(change.detected_at).toLocaleString('es-AR', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Add Competitor Modal */}
      <Dialog open={addModalOpen} onOpenChange={setAddModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Agregar competidor</DialogTitle>
            <DialogDescription>Registrá un competidor para monitoreo continuo 24/7.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <label className="text-xs font-medium text-white/50 mb-1.5 block">Nombre</label>
              <Input
                placeholder="Ej: Competidor X"
                value={newMonitor.competitor_name}
                onChange={(e) => setNewMonitor((prev) => ({ ...prev, competitor_name: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-xs font-medium text-white/50 mb-1.5 block">URL</label>
              <Input
                placeholder="https://..."
                value={newMonitor.competitor_url}
                onChange={(e) => setNewMonitor((prev) => ({ ...prev, competitor_url: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-xs font-medium text-white/50 mb-1.5 block">
                Productos a trackear <span className="text-white/30">(separados por coma)</span>
              </label>
              <Input
                placeholder="Ej: Camiseta Negra, Zapatillas Pro"
                value={newMonitor.products_to_track}
                onChange={(e) => setNewMonitor((prev) => ({ ...prev, products_to_track: e.target.value }))}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddModalOpen(false)}>
              Cancelar
            </Button>
            <Button
              onClick={handleAddMonitor}
              disabled={!newMonitor.competitor_name.trim() || !newMonitor.competitor_url.trim()}
            >
              Guardar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Strategy Detail Modal */}
      <Dialog open={!!strategyModal} onOpenChange={() => setStrategyModal(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Estrategia recomendada</DialogTitle>
            <DialogDescription>
              {strategyModal?.change.competitor_name} — {strategyModal?.change.change_type}
            </DialogDescription>
          </DialogHeader>
          <div className="py-2 space-y-4">
            <p className="text-sm text-white/70">{strategyModal?.suggestion}</p>
            {strategyModal?.risk_note && (
              <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20">
                <p className="text-xs text-amber-400">{strategyModal.risk_note}</p>
              </div>
            )}
            <div className="space-y-2">
              {strategyModal?.options.map((opt, i) => (
                <div key={i} className="flex items-start gap-2 text-sm text-white/60">
                  <span className="text-brand-orange font-bold">{i + 1}.</span>
                  <span>{opt}</span>
                </div>
              ))}
            </div>
          </div>
          <DialogFooter>
            <Button onClick={() => setStrategyModal(null)}>Cerrar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
