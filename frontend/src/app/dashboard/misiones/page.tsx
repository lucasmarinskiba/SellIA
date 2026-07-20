'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { businessApi } from '@/lib/business'
import { missionsApi, Mission, Playbook, BusinessDiagnostic } from '@/lib/missions'
import { businessContextApi, BusinessContext, ReachAnalysis, ChannelGap } from '@/lib/businessContext'
import { useMissions, useDiagnostics, usePlaybooks } from '@/hooks/useMissions'
import MissionCard from '@/components/missions/MissionCard'
import MissionStepTimeline from '@/components/missions/MissionStepTimeline'
import PlaybookSelector from '@/components/missions/PlaybookSelector'
import BusinessContextWizard from '@/components/missions/BusinessContextWizard'
import ReachAnalysisCard from '@/components/missions/ReachAnalysisCard'
import ChannelGapList from '@/components/missions/ChannelGapList'
import ShippingAssistant from '@/components/missions/ShippingAssistant'
import AdSpendAssistant from '@/components/missions/AdSpendAssistant'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import {
  Target, AlertCircle, Loader2, X, Plus, Stethoscope, Play,
  CheckCircle, XCircle, TrendingUp, Zap, ChevronLeft, Activity,
  Building2, Globe, Wand2, Truck, Megaphone
} from 'lucide-react'

export default function MisionesPage() {
  const [businesses, setBusinesses] = useState<any[]>([])
  const [selectedBusinessId, setSelectedBusinessId] = useState('')
  const [selectedMission, setSelectedMission] = useState<Mission | null>(null)
  const [showPlaybooks, setShowPlaybooks] = useState(false)
  const [runningDiagnostic, setRunningDiagnostic] = useState(false)
  const [diagnosticResult, setDiagnosticResult] = useState<{ diagnostics: BusinessDiagnostic[]; recommended_missions: Playbook[] } | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  // Business Context state
  const [businessContext, setBusinessContext] = useState<BusinessContext | null>(null)
  const [showContextWizard, setShowContextWizard] = useState(false)
  const [showShippingAssistant, setShowShippingAssistant] = useState(false)
  const [showAdAssistant, setShowAdAssistant] = useState(false)
  const [reachAnalysis, setReachAnalysis] = useState<ReachAnalysis | null>(null)
  const [channelGaps, setChannelGaps] = useState<ChannelGap[] | null>(null)
  const [recommendedPlaybooks, setRecommendedPlaybooks] = useState<string[] | null>(null)
  const [contextLoading, setContextLoading] = useState(false)

  const { missions, loading: missionsLoading, error: missionsError, refetch: refetchMissions, approve, run, cancel } = useMissions(selectedBusinessId)
  const { diagnostics, loading: diagnosticsLoading, runDiagnostics } = useDiagnostics(selectedBusinessId)
  const { playbooks, loading: playbooksLoading } = usePlaybooks()

  useEffect(() => {
    businessApi.list().then(data => {
      setBusinesses(data)
      if (data.length > 0) setSelectedBusinessId(data[0].id)
    }).catch(() => {})
  }, [])

  useEffect(() => {
    if (!selectedBusinessId) return
    loadBusinessContext()
  }, [selectedBusinessId])

  const loadBusinessContext = async () => {
    setContextLoading(true)
    try {
      const ctx = await businessContextApi.getContext(selectedBusinessId)
      setBusinessContext(ctx)
      if (ctx.id) {
        const [reach, gaps, recs] = await Promise.all([
          businessContextApi.getReachAnalysis(ctx.id).catch(() => null),
          businessContextApi.getChannelGaps(ctx.id).catch(() => null),
          businessContextApi.getRecommendedPlaybooks(ctx.id).catch(() => null),
        ])
        setReachAnalysis(reach)
        setChannelGaps(gaps)
        setRecommendedPlaybooks(recs)
      }
    } catch (e) {
      // Context might not exist yet
    } finally {
      setContextLoading(false)
    }
  }

  const handleRunDiagnostic = async () => {
    setRunningDiagnostic(true)
    setActionError(null)
    try {
      const result = await runDiagnostics()
      setDiagnosticResult(result)
    } catch (e: any) {
      setActionError(e?.response?.data?.detail || 'Error al ejecutar diagnóstico')
    } finally {
      setRunningDiagnostic(false)
    }
  }

  const handleCreateFromPlaybook = async (playbook: Playbook) => {
    setActionError(null)
    try {
      await missionsApi.createMission({
        playbook_slug: playbook.slug,
        business_id: selectedBusinessId || undefined,
      })
      setShowPlaybooks(false)
      await refetchMissions()
    } catch (e: any) {
      setActionError(e?.response?.data?.detail || 'Error al crear misión')
    }
  }

  const handleCreateFromSlug = async (slug: string) => {
    setActionError(null)
    try {
      await missionsApi.createMission({
        playbook_slug: slug,
        business_id: selectedBusinessId || undefined,
      })
      await refetchMissions()
    } catch (e: any) {
      setActionError(e?.response?.data?.detail || 'Error al crear misión')
    }
  }

  const stats = {
    total: missions.length,
    running: missions.filter(m => m.status === 'running').length,
    completed: missions.filter(m => m.status === 'completed').length,
    proposed: missions.filter(m => m.status === 'proposed').length,
  }

  if (selectedMission) {
    return (
      <div className="space-y-6 max-w-4xl">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => setSelectedMission(null)}>
            <ChevronLeft className="w-4 h-4 mr-1" />
            Volver
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-white">{selectedMission.title}</h1>
            <p className="text-sm text-white/40">Detalle de misión y progreso de pasos</p>
          </div>
        </div>

        <Card>
          <CardContent className="p-6">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
              <div className="p-3 rounded-xl bg-white/5">
                <p className="text-xs text-white/40 mb-1">Estado</p>
                <Badge variant={selectedMission.status === 'completed' ? 'success' : selectedMission.status === 'running' ? 'orange' : 'secondary'}>
                  {selectedMission.status}
                </Badge>
              </div>
              <div className="p-3 rounded-xl bg-white/5">
                <p className="text-xs text-white/40 mb-1">Categoría</p>
                <p className="text-sm font-medium text-white capitalize">{selectedMission.category}</p>
              </div>
              <div className="p-3 rounded-xl bg-white/5">
                <p className="text-xs text-white/40 mb-1">Creada por</p>
                <p className="text-sm font-medium text-white">{selectedMission.created_by === 'ai' ? '🤖 IA' : '👤 Usuario'}</p>
              </div>
              <div className="p-3 rounded-xl bg-white/5">
                <p className="text-xs text-white/40 mb-1">Plataformas</p>
                <p className="text-sm font-medium text-white">{selectedMission.target_platforms.join(', ')}</p>
              </div>
            </div>

            {selectedMission.steps && selectedMission.steps.length > 0 ? (
              <MissionStepTimeline steps={selectedMission.steps} />
            ) : (
              <div className="text-center py-8 text-white/20 text-sm">
                No hay pasos definidos para esta misión.
              </div>
            )}

            <div className="flex gap-3 mt-6 pt-6 border-t border-white/5">
              {selectedMission.status === 'proposed' && (
                <Button onClick={() => { approve(selectedMission.id); setSelectedMission(null) }}>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Aprobar Misión
                </Button>
              )}
              {selectedMission.status === 'approved' && (
                <Button onClick={() => { run(selectedMission.id); setSelectedMission(null) }}>
                  <Play className="w-4 h-4 mr-2" />
                  Ejecutar Misión
                </Button>
              )}
              {(selectedMission.status === 'running' || selectedMission.status === 'approved') && (
                <Button variant="secondary" onClick={() => { cancel(selectedMission.id); setSelectedMission(null) }}>
                  <XCircle className="w-4 h-4 mr-2" />
                  Cancelar
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-8 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">🎯 Misiones SellIA</h1>
          <p className="text-sm text-white/40">Diagnóstico automático y ejecución de estrategias multi-plataforma.</p>
        </div>
        <div className="flex items-center gap-3">
          {businesses.length > 0 && (
            <select
              value={selectedBusinessId}
              onChange={e => setSelectedBusinessId(e.target.value)}
              className="px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
            >
              {businesses.map(b => (
                <option key={b.id} value={b.id} className="bg-[#0A0E1A]">{b.name}</option>
              ))}
            </select>
          )}
          <Button variant="secondary" onClick={() => setShowContextWizard(true)}>
            <Building2 className="w-4 h-4 mr-2" />
            Mi Negocio
          </Button>
          <Button variant="secondary" onClick={() => setShowShippingAssistant(true)}>
            <Truck className="w-4 h-4 mr-2" />
            Envíos
          </Button>
          <Button variant="secondary" onClick={() => setShowAdAssistant(true)}>
            <Megaphone className="w-4 h-4 mr-2" />
            Ads
          </Button>
          <Button onClick={() => setShowPlaybooks(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Nueva Misión
          </Button>
        </div>
      </div>

      {actionError && (
        <div className="flex items-center gap-2 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <AlertCircle className="w-4 h-4" />
          {actionError}
          <button onClick={() => setActionError(null)} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Total Misiones', value: stats.total, icon: <Target className="w-4 h-4" />, color: 'text-brand-orange' },
          { label: 'En Ejecución', value: stats.running, icon: <Activity className="w-4 h-4" />, color: 'text-brand-violet' },
          { label: 'Completadas', value: stats.completed, icon: <CheckCircle className="w-4 h-4" />, color: 'text-brand-teal' },
          { label: 'Pendientes', value: stats.proposed, icon: <AlertCircle className="w-4 h-4" />, color: 'text-amber-400' },
        ].map((stat) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-4"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className={stat.color}>{stat.icon}</span>
              <span className="text-xs text-white/40">{stat.label}</span>
            </div>
            <p className="text-2xl font-bold text-white">{stat.value}</p>
          </motion.div>
        ))}
      </div>

      {/* Business Context Section */}
      {contextLoading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-brand-orange" />
        </div>
      ) : businessContext ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white/80 flex items-center gap-2">
              <Building2 className="w-5 h-5 text-brand-orange" />
              Contexto de Negocio
            </h2>
            <Button size="sm" variant="ghost" onClick={() => setShowContextWizard(true)}>
              <Wand2 className="w-3.5 h-3.5 mr-1" />
              Editar
            </Button>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {reachAnalysis && <ReachAnalysisCard analysis={reachAnalysis} />}
            {channelGaps && channelGaps.length > 0 && (
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Globe className="w-4 h-4 text-brand-violet" />
                    Canales por Configurar
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ChannelGapList gaps={channelGaps.slice(0, 5)} onCreateMission={handleCreateFromSlug} />
                  {channelGaps.length > 5 && (
                    <p className="text-xs text-white/20 mt-2 text-center">+{channelGaps.length - 5} más...</p>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
          {recommendedPlaybooks && recommendedPlaybooks.length > 0 && (
            <div className="flex flex-wrap gap-2">
              <span className="text-xs text-white/40 self-center mr-2">Misiones recomendadas:</span>
              {recommendedPlaybooks.slice(0, 6).map(slug => (
                <Badge
                  key={slug}
                  variant="secondary"
                  className="cursor-pointer hover:bg-brand-orange/20 hover:text-brand-orange transition-colors"
                  onClick={() => handleCreateFromSlug(slug)}
                >
                  <Zap className="w-3 h-3 mr-1" />
                  {slug.replace(/_/g, ' ')}
                </Badge>
              ))}
            </div>
          )}
        </div>
      ) : (
        <Card className="p-6 text-center">
          <Building2 className="w-8 h-8 text-white/20 mx-auto mb-3" />
          <p className="text-sm text-white/30 mb-4">Configurá el contexto de tu negocio para obtener misiones personalizadas.</p>
          <Button onClick={() => setShowContextWizard(true)}>
            <Wand2 className="w-4 h-4 mr-2" />
            Configurar mi negocio
          </Button>
        </Card>
      )}

      {/* Diagnostic Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white/80 flex items-center gap-2">
            <Stethoscope className="w-5 h-5 text-brand-orange" />
            Diagnóstico de Negocio
          </h2>
          <Button
            size="sm"
            variant="secondary"
            onClick={handleRunDiagnostic}
            disabled={runningDiagnostic}
          >
            {runningDiagnostic ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin mr-2" />
            ) : (
              <Zap className="w-3.5 h-3.5 mr-2" />
            )}
            {runningDiagnostic ? 'Analizando...' : 'Ejecutar Diagnóstico'}
          </Button>
        </div>

        {diagnosticResult && diagnosticResult.diagnostics.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="space-y-3"
          >
            {diagnosticResult.diagnostics.map((d, i) => (
              <Card key={i} className="border-l-4" style={{ borderLeftColor: d.severity === 'critical' ? '#EF4444' : d.severity === 'warning' ? '#F59E0B' : '#3B82F6' }}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant={d.severity === 'critical' ? 'destructive' : d.severity === 'warning' ? 'warning' : 'info'} className="text-[10px]">
                          {d.severity.toUpperCase()}
                        </Badge>
                        <span className="text-xs text-white/40 capitalize">{d.category}</span>
                      </div>
                      <p className="text-sm text-white/80">{d.finding}</p>
                      {d.metric_value && d.benchmark_value && (
                        <p className="text-xs text-white/30 mt-1">
                          Métrica: {d.metric_value} · Benchmark: {d.benchmark_value}
                        </p>
                      )}
                    </div>
                    {d.recommended_mission_slug && (
                      <Button
                        size="sm"
                        onClick={() => handleCreateFromSlug(d.recommended_mission_slug!)}
                      >
                        <TrendingUp className="w-3 h-3 mr-1" />
                        Crear Misión
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </motion.div>
        )}

        {!diagnosticResult && !diagnosticsLoading && diagnostics.length === 0 && (
          <div className="glass-card p-8 text-center">
            <Stethoscope className="w-8 h-8 text-white/20 mx-auto mb-3" />
            <p className="text-sm text-white/30">Aún no hay diagnósticos. Ejecuta un análisis para detectar problemas y oportunidades.</p>
          </div>
        )}
      </div>

      {/* Missions Grid */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-white/80 flex items-center gap-2">
          <Target className="w-5 h-5 text-brand-violet" />
          Tus Misiones
        </h2>

        {missionsLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
          </div>
        ) : missionsError ? (
          <div className="glass-card p-8 text-center text-red-400 text-sm">
            {missionsError}
          </div>
        ) : missions.length === 0 ? (
          <div className="glass-card p-8 text-center">
            <Target className="w-8 h-8 text-white/20 mx-auto mb-3" />
            <p className="text-sm text-white/30 mb-4">No tienes misiones activas.</p>
            <Button size="sm" onClick={() => setShowPlaybooks(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Crear primera misión
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {missions.map((mission, i) => (
              <MissionCard
                key={mission.id}
                mission={mission}
                index={i}
                onApprove={approve}
                onRun={run}
                onCancel={cancel}
                onClick={setSelectedMission}
              />
            ))}
          </div>
        )}
      </div>

      {/* Modals */}
      <AnimatePresence>
        {showPlaybooks && (
          <PlaybookSelector
            playbooks={playbooks}
            onSelect={handleCreateFromPlaybook}
            onClose={() => setShowPlaybooks(false)}
          />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showContextWizard && businessContext && (
          <BusinessContextWizard
            contextId={businessContext.id}
            onComplete={() => {
              setShowContextWizard(false)
              loadBusinessContext()
            }}
          />
        )}
        {showContextWizard && !businessContext && (
          <BusinessContextWizard
            contextId="new"
            onComplete={() => {
              setShowContextWizard(false)
              loadBusinessContext()
            }}
          />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showShippingAssistant && <ShippingAssistant onClose={() => setShowShippingAssistant(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {showAdAssistant && <AdSpendAssistant onClose={() => setShowAdAssistant(false)} />}
      </AnimatePresence>
    </div>
  )
}
