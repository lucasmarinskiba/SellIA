'use client'

import { useState, useMemo, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Sparkles, Settings, Volume2, VolumeX } from 'lucide-react'
import SellIAVoiceSession from './SellIAVoiceSession'
import ComputerUseMainStage from './ComputerUseMainStage'
import ComputerUseSessionCarousel, { CUSessionMini } from './ComputerUseSessionCarousel'
import AgentBrainMap, { BrainNode } from './AgentBrainMap'
import SellIAActionQueue, { PendingAction } from './SellIAActionQueue'
import SellIANarrationBar from './SellIANarrationBar'
import SalesFidelizationFlow from './SalesFidelizationFlow'
import LiveActivityFeed from './LiveActivityFeed'
import ConversionGuaranteeBoard from './ConversionGuaranteeBoard'
import DealDoctor from './DealDoctor'
import RecoveryLab from './RecoveryLab'
import ChampionBuilder from './ChampionBuilder'
import NeuralBrain from './NeuralBrain'
import AgentMeshGraph from './AgentMeshGraph'
import ServiceVerticals from './ServiceVerticals'
import OmnipresentBrain from './OmnipresentBrain'
import UnifiedBrainCore from './UnifiedBrainCore'
import InfiniteTokensInfra from './InfiniteTokensInfra'
import OmniTouchpoints from './OmniTouchpoints'
import LaunchReadiness from './LaunchReadiness'
import PricingPlans from './PricingPlans'
import OnboardingWizard from './OnboardingWizard'
import AnalyticsDashboards from './AnalyticsDashboards'
import AuditLogs from './AuditLogs'
import AdminPanel from './AdminPanel'
import InventoryManager from './InventoryManager'
import OrderLifecycle from './OrderLifecycle'
import Customer360 from './Customer360'
import KnowledgeBaseIngest from './KnowledgeBaseIngest'
import WorkflowBuilder from './WorkflowBuilder'
import CalendarScheduling from './CalendarScheduling'
import InvoicingQuotes from './InvoicingQuotes'
import EmailCampaigns from './EmailCampaigns'
import FormsLandings from './FormsLandings'
import ReturnsRMA from './ReturnsRMA'
import ReviewsAggregator from './ReviewsAggregator'
import TaxSync from './TaxSync'
import ARCAComplianceHub from './ARCAComplianceHub'
import CustomsExportHub from './CustomsExportHub'
import ReportsCustom from './ReportsCustom'
import BrowserExtensions from './BrowserExtensions'
import ExtensionStack from './ExtensionStack'
import AutonomousMode from './AutonomousMode'
import MarketplaceCommandCenter from './MarketplaceCommandCenter'
import AdsCockpit from './AdsCockpit'
import GrowthEngine from './GrowthEngine'
import ReachAndShipping from './ReachAndShipping'
import PlaybookLibrary from './PlaybookLibrary'
import SkillsLibrary from './SkillsLibrary'
import MasterMindCouncil from './MasterMindCouncil'
import SalesLegendsBrain from './SalesLegendsBrain'
import VoiceCommandPalette from './VoiceCommandPalette'
import { useTextToSpeech } from '@/hooks/useTextToSpeech'
import { CUSessionStatus } from '@/hooks/useComputerUseWebSocket'

// ─── Types ─────────────────────────────────────────────────────────────────────

interface SellIAHubProps {
  userName?: string
  userEmail?: string
  initialSessions?: CUSessionMini[]
  initialNodes?: BrainNode[]
  initialActions?: PendingAction[]
}

// ─── Default brain nodes ───────────────────────────────────────────────────────

const DEFAULT_NODES: BrainNode[] = [
  { id: 'whatsapp', name: 'WhatsApp', icon: 'message', status: 'active', color: '#10b981', connections: ['crm', 'pipeline'], metric: '3 chats abiertos' },
  { id: 'instagram', name: 'Instagram', icon: 'instagram', status: 'active', color: '#ec4899', connections: ['content'], metric: '1 story programada' },
  { id: 'email', name: 'Email', icon: 'mail', status: 'idle', color: '#3b82f6', connections: ['crm'], metric: '0 emails pendientes' },
  { id: 'crm', name: 'CRM', icon: 'chart', status: 'active', color: '#a855f7', connections: ['whatsapp', 'email', 'pipeline'], metric: '12 leads activos' },
  { id: 'pipeline', name: 'Pipeline', icon: 'target', status: 'active', color: '#f59e0b', connections: ['crm'], metric: '2 deals en cierre' },
  { id: 'afip', name: 'AFIP', icon: 'file', status: 'idle', color: '#ef4444', connections: [], metric: 'Sin tareas' },
  { id: 'analytics', name: 'Analytics', icon: 'trend', status: 'active', color: '#06b6d4', connections: ['pipeline'], metric: '$3,247 hoy' },
]

// ─── Default actions ───────────────────────────────────────────────────────────

const DEFAULT_ACTIONS: PendingAction[] = [
  { id: 'ap1', action: 'Otorgar 25% descuento a Tomás N.', reason: 'Cliente histórico, LTV $14k, riesgo de churn alto', confidence: 87, impact: 2400, type: 'discount', icon: '💰' },
  { id: 'ap2', action: 'Enviar propuesta de upgrade Premium', reason: 'Patrón de uso indica readiness · ROI estimado 4.2×', confidence: 92, impact: 980, type: 'upgrade', icon: '⬆️' },
]

// ─── Default sessions ──────────────────────────────────────────────────────────

const DEFAULT_SESSIONS: CUSessionMini[] = [
  { id: 'sess-2174', task: 'Contactar leads tibios por WhatsApp', browser: 'Chromium', steps: 17, status: 'running', url: 'web.whatsapp.com', color: '#10b981' },
  { id: 'sess-2175', task: 'Postear oferta en Instagram Stories', browser: 'Firefox', steps: 8, status: 'running', url: 'instagram.com/stories', color: '#ec4899' },
  { id: 'sess-2176', task: 'Generar factura A para Empresa Beta', browser: 'Chromium', steps: 23, status: 'paused', url: 'afip.gob.ar/portal', color: '#3b82f6' },
]

// ─── Component ─────────────────────────────────────────────────────────────────

export default function SellIAHub({
  userName = 'Usuario',
  initialSessions = DEFAULT_SESSIONS,
  initialNodes = DEFAULT_NODES,
  initialActions = DEFAULT_ACTIONS,
}: SellIAHubProps) {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(initialSessions[0]?.id || null)
  const [sessions, setSessions] = useState<CUSessionMini[]>(initialSessions)
  const [nodes, setNodes] = useState<BrainNode[]>(initialNodes)
  const [actions, setActions] = useState<PendingAction[]>(initialActions)
  const [isWorking, setIsWorking] = useState(false)
  const [narrationText, setNarrationText] = useState('Esperando instrucciones...')
  const [ttsEnabled, setTtsEnabled] = useState(true)
  const { speak, stop: stopTTS, isSpeaking } = useTextToSpeech()

  const activeSession = useMemo(() => sessions.find(s => s.id === activeSessionId), [sessions, activeSessionId])

  const handleStartWorking = useCallback(() => {
    setIsWorking(true)
    const text = 'Iniciando sesiones de computer use. Abriendo WhatsApp Web...'
    setNarrationText(text)
    if (ttsEnabled) speak(text)
  }, [ttsEnabled, speak])

  const handleStopWorking = useCallback(() => {
    setIsWorking(false)
    setNarrationText('Sesión pausada. Esperando instrucciones...')
    stopTTS()
  }, [stopTTS])

  const handleSessionStatusChange = useCallback((status: CUSessionStatus) => {
    if (status === 'running') {
      setNarrationText('Sesión activa. La IA está operando el navegador...')
    } else if (status === 'paused') {
      setNarrationText('Sesión pausada. Esperando reanudación...')
    }
  }, [])

  const handleApproveAction = useCallback((id: string) => {
    setActions(prev => prev.filter(a => a.id !== id))
    const text = `Acción aprobada. Ejecutando...`
    setNarrationText(text)
    if (ttsEnabled) speak(text)
  }, [ttsEnabled, speak])

  const handleRejectAction = useCallback((id: string) => {
    setActions(prev => prev.filter(a => a.id !== id))
  }, [])

  const handleCreateSession = useCallback(() => {
    const newId = `sess-${Date.now().toString().slice(-4)}`
    const newSession: CUSessionMini = {
      id: newId,
      task: 'Nueva tarea de automatización',
      browser: 'Chromium',
      steps: 0,
      status: 'pending',
      color: '#a855f7',
    }
    setSessions(prev => [...prev, newSession])
    setActiveSessionId(newId)
  }, [])

  const runningCount = sessions.filter(s => s.status === 'running').length

  return (
    <div className="min-h-screen bg-[#060812] text-white">
      {/* Ambient background */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10">
        <div className="absolute top-0 left-1/4 w-96 h-96 rounded-full bg-brand-orange/5 blur-[120px] animate-pulse" style={{ animationDuration: '6s' }} />
        <div className="absolute top-1/3 right-0 w-80 h-80 rounded-full bg-purple-500/5 blur-[100px] animate-pulse" style={{ animationDuration: '8s', animationDelay: '1s' }} />
        <div className="absolute bottom-0 left-1/3 w-96 h-96 rounded-full bg-emerald-500/[0.04] blur-[120px] animate-pulse" style={{ animationDuration: '10s', animationDelay: '2s' }} />
      </div>

      {/* ═══ Header ═══════════════════════════════════════════════════════ */}
      <header className="sticky top-0 z-40 bg-[#060812]/80 backdrop-blur-xl border-b border-white/[0.06]">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-orange to-brand-orange-dark flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">
                SellIA <span className="text-white/40 font-light">Brain Hub</span>
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* TTS Toggle */}
            <button
              onClick={() => {
                setTtsEnabled(p => !p)
                if (ttsEnabled) stopTTS()
              }}
              className={`p-2 rounded-xl transition-all ${
                ttsEnabled ? 'bg-brand-orange/20 text-brand-orange' : 'bg-white/5 text-white/30'
              }`}
              title={ttsEnabled ? 'Desactivar voz' : 'Activar voz'}
            >
              {ttsEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
            </button>

            {/* SellIA Avatar + Voice Session */}
            <div className="hidden sm:block">
              <SellIAVoiceSession
                userName={userName}
                enabled={true}
                onStartWorking={handleStartWorking}
                onStopWorking={handleStopWorking}
              />
            </div>
          </div>
        </div>
      </header>

      {/* ═══ Main Content ═════════════════════════════════════════════════ */}
      <main className="max-w-[1600px] mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Status bar */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/[0.03] border border-white/[0.06]">
            <div className={`w-1.5 h-1.5 rounded-full ${isWorking ? 'bg-emerald-400 animate-pulse' : 'bg-white/20'}`} />
            <span className="text-xs text-white/50">
              {isWorking ? `${runningCount} sesiones activas` : 'SellIA en espera'}
            </span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/[0.03] border border-white/[0.06]">
            <span className="text-xs text-white/50">{nodes.filter(n => n.status === 'active').length} agentes conectados</span>
          </div>
          {actions.length > 0 && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-amber-500/10 border border-amber-500/20">
              <span className="text-xs text-amber-400">{actions.length} decisiones pendientes</span>
            </div>
          )}
        </div>

        {/* ═══ Unified Brain Core · ONE BRAIN, N ARMS ═══════════════════ */}
        <UnifiedBrainCore />

        {/* ═══ Infinite Tokens · Ollama+routing+DB ══════════════════════ */}
        <InfiniteTokensInfra />

        {/* ═══ Omni Touchpoints · donde vive SellIA ═════════════════════ */}
        <OmniTouchpoints />

        {/* ═══ Onboarding Wizard · user nuevo → vendiendo en <10min ═════ */}
        <OnboardingWizard />

        {/* ═══ Pricing Plans · 4 tiers + add-ons ════════════════════════ */}
        <PricingPlans />

        {/* ═══ Analytics Dashboards · revenue · conv · margin · cohorts ═ */}
        <AnalyticsDashboards />

        {/* ═══ Admin Panel · team + API keys ════════════════════════════ */}
        <AdminPanel />

        {/* ═══ Audit Logs · compliance + forense ════════════════════════ */}
        <AuditLogs />

        {/* ═══ Inventory · stock · warehouses · auto-reorder ════════════ */}
        <InventoryManager />

        {/* ═══ Orders lifecycle · kanban ════════════════════════════════ */}
        <OrderLifecycle />

        {/* ═══ Customer 360 · unified profile · NBA ═════════════════════ */}
        <Customer360 />

        {/* ═══ Knowledge Base · IA aprende biz · RAG ════════════════════ */}
        <KnowledgeBaseIngest />

        {/* ═══ Workflow Builder · no-code automations ═══════════════════ */}
        <WorkflowBuilder />

        {/* ═══ Calendar + Scheduling · slots · sync GCal ════════════════ */}
        <CalendarScheduling />

        {/* ═══ Invoicing + Quotes · PDF · firma · AFIP ══════════════════ */}
        <InvoicingQuotes />

        {/* ═══ Email Campaigns · drips · broadcasts · A/B ═══════════════ */}
        <EmailCampaigns />

        {/* ═══ Forms + Landings · no-code builder ═══════════════════════ */}
        <FormsLandings />

        {/* ═══ Returns / RMA · auto-approve · refund tracking ═══════════ */}
        <ReturnsRMA />

        {/* ═══ Reviews Aggregator · multi-source · IA responde ══════════ */}
        <ReviewsAggregator />

        {/* ═══ Tax Sync · AFIP · SAT · DIAN · SUNAT · OSS ══════════════ */}
        <TaxSync />

        {/* ═══ ARCA Compliance · ex-AFIP · trámites impositivos AR ═════ */}
        <ARCAComplianceHub />

        {/* ═══ Customs Export · DGA · exportá a cualquier país ═════════ */}
        <CustomsExportHub />

        {/* ═══ Reports Custom · P&L · cohort · SQL · exports ════════════ */}
        <ReportsCustom />

        {/* ═══ Launch Readiness · qué falta para GA ═════════════════════ */}
        <LaunchReadiness />

        {/* ═══ Omnipresent Brain · set & forget hero ════════════════════ */}
        <OmnipresentBrain />

        {/* ═══ Autonomous Mode (centered above the brain) ═══════════════ */}
        <AutonomousMode />

        {/* ═══ Voice Command Palette · multi-lang hands-free ══════════════ */}
        <VoiceCommandPalette userName={userName} />

        {/* ═══ Neural Brain — Living network visualization ════════════════ */}
        <NeuralBrain />

        {/* ═══ Agent Mesh Graph · inter-agent comms ══════════════════════ */}
        <AgentMeshGraph />

        {/* ═══ Service Verticals · industrias pre-configuradas ═══════════ */}
        <ServiceVerticals />

        {/* ═══ Browser Extensions · brazos del cerebro ══════════════════ */}
        <BrowserExtensions />

        {/* ═══ Extension Stack · anatomía CUA + agents + skills + plugins */}
        <ExtensionStack />

        {/* ═══ Top Row: Computer Use Stage + Brain Map ═══════════════════ */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Main Stage (2/3) */}
          <div className="lg:col-span-2 space-y-4">
            <ComputerUseMainStage
              sessionId={activeSessionId}
              onSessionStatusChange={handleSessionStatusChange}
            />

            {/* Narration bar inside stage area */}
            <div className="relative h-14">
              <SellIANarrationBar
                text={narrationText}
                isSpeaking={isSpeaking}
                isTyping={isWorking}
              />
            </div>
          </div>

          {/* Right Column: Brain Map + Action Queue (1/3) */}
          <div className="space-y-4">
            {/* Brain Map */}
            <div className="bg-white/[0.02] border border-white/[0.08] rounded-2xl p-5">
              <h3 className="text-sm font-semibold text-white mb-1 text-center">Agent Brain Map</h3>
              <p className="text-[10px] text-white/30 text-center mb-3">Cerebro de ventas en tiempo real</p>
              <AgentBrainMap nodes={nodes} />
            </div>

            {/* Action Queue */}
            <SellIAActionQueue
              actions={actions}
              onApprove={handleApproveAction}
              onReject={handleRejectAction}
            />
          </div>
        </div>

        {/* ═══ SALES GUARANTEE ENGINE ════════════════════════════════════ */}
        <ConversionGuaranteeBoard />

        {/* ═══ Sales → Fidelization Flow ═════════════════════════════════ */}
        <SalesFidelizationFlow />

        {/* ═══ Deal Doctor + Live Feed (2 cols) ══════════════════════════ */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          <div className="xl:col-span-2">
            <DealDoctor />
          </div>
          <div className="xl:col-span-1">
            <LiveActivityFeed />
          </div>
        </div>

        {/* ═══ Recovery Lab ══════════════════════════════════════════════ */}
        <RecoveryLab />

        {/* ═══ Champion Builder ══════════════════════════════════════════ */}
        <ChampionBuilder />

        {/* ═══ Playbook Library (15 workflows 1-click) ═══════════════════ */}
        <PlaybookLibrary />

        {/* ═══ Marketplace Command Center (14 plataformas) ═══════════════ */}
        <MarketplaceCommandCenter />

        {/* ═══ Ads Cockpit (Meta + Google + TikTok) ═════════════════════ */}
        <AdsCockpit />

        {/* ═══ Growth Engine (SEO + branding + diagnóstico) ═════════════ */}
        <GrowthEngine />

        {/* ═══ Reach & Shipping (geo + couriers) ═════════════════════════ */}
        <ReachAndShipping />

        {/* ═══ Skills Library (50 capacidades del cerebro) ══════════════ */}
        <SkillsLibrary />

        {/* ═══ MasterMind Council (top business minds) ══════════════════ */}
        <MasterMindCouncil />

        {/* ═══ Sales Legends Brain (top sellers · scripts) ══════════════ */}
        <SalesLegendsBrain />

        {/* ═══ Session Carousel ════════════════════════════════════════ */}
        <ComputerUseSessionCarousel
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={setActiveSessionId}
          onCreateSession={handleCreateSession}
        />

        {/* ═══ Mobile Voice Session ══════════════════════════════════════ */}
        <div className="sm:hidden flex justify-center py-4">
          <SellIAVoiceSession
            userName={userName}
            enabled={true}
            onStartWorking={handleStartWorking}
            onStopWorking={handleStopWorking}
          />
        </div>
      </main>
    </div>
  )
}
