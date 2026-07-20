'use client'

/**
 * ENTERPRISE COMMAND CENTER · /sellia-brain
 *
 * B2B SaaS dark-mode mission control for the SellIA selling brain.
 * Palette: deep slate/navy, cobalt + emerald accents (no neon).
 * Layout: top KPI bar · main prospect data table · side agent audit log.
 *
 * Design system (strict):
 *   - cards: padding 24px, border 1px solid rgba(255,255,255,0.1), radius 8–12px
 *   - typography: Inter (UI), JetBrains Mono (terminal/metrics)
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Activity, ArrowDown, ArrowRight, ArrowUp, Brain, ChevronLeft, ChevronRight,
  Cpu, Filter, LifeBuoy, Search, Store, Target, TrendingUp, Users, Workflow,
} from 'lucide-react'

import MissionControlBar, {
  type CuaMode, type UserProfile, loadUser, clearUser,
} from './MissionControlBar'
import HandsFreeOverlay from './HandsFreeOverlay'
import ComputerUseLauncher from './ComputerUseLauncher'
import dynamic from 'next/dynamic'
import { type LobeId } from './toolIndex'
import { type BusinessProfile, type PlannedFlow, loadProfile, isComplete, planAccountFlows, buildToolPlan } from '@/lib/business-profile'

// React Flow trae su CSS — lazy-load (ssr:false) para evitar bundling SSR.
const BrainInteractionMap = dynamic(
  () => import('./BrainInteractionMap'),
  { ssr: false, loading: () => <div style={{ height: 460, display: 'grid', placeItems: 'center', color: '#5C6B85', fontFamily: 'monospace', fontSize: 11 }}>cargando mapa de interacciones…</div> },
)
const BrainFlowsView = dynamic(
  () => import('./BrainFlowsView'),
  { ssr: false, loading: () => <div style={{ height: 460, display: 'grid', placeItems: 'center', color: '#5C6B85', fontFamily: 'monospace', fontSize: 11 }}>cargando flujos…</div> },
)
const BusinessProfileWizard = dynamic(() => import('./BusinessProfileWizard'), { ssr: false })
const BusinessToolkit = dynamic(() => import('./BusinessToolkit'), { ssr: false })
const RescueMode = dynamic(() => import('./RescueMode'), { ssr: false })
const ToolStudio = dynamic(() => import('./ToolStudio'), { ssr: false })
import SquadStatusPanel from '../sellia-hub/SquadStatusPanel'
import HandoffLog from '../sellia-hub/HandoffLog'
import ApprovalsCenter from '../sellia-hub/ApprovalsCenter'

/* ─────────────────────────────────────────────
   DESIGN TOKENS — Enterprise SaaS Dark Mode
─────────────────────────────────────────────── */
const T = {
  bg:        '#0A0F1A', // deep navy/slate base
  panel:     '#0F1722', // card surface
  panelAlt:  '#131C2B', // raised surface / row hover
  border:    'rgba(255,255,255,0.10)',
  borderStr: 'rgba(255,255,255,0.16)',
  text:      '#E6EAF2', // crisp near-white
  text2:     '#9AA7BD', // slate-400 muted
  text3:     '#5C6B85', // slate-600 faint
  cobalt:    '#3B82F6', // corporate blue accent
  cobaltDk:  '#2563EB',
  emerald:   '#10B981', // success / ROI
  amber:     '#F59E0B', // attention
  red:       '#EF4444', // risk
  mono:      "'JetBrains Mono', ui-monospace, monospace",
  sans:      "'Inter', ui-sans-serif, system-ui, sans-serif",
} as const

const PAGE_SIZE = 8

/* ─────────────────────────────────────────────
   DATA MODEL
─────────────────────────────────────────────── */
type AIStage =
  | 'Prospectando'
  | 'Calificando'
  | 'Outreach'
  | 'Negociando'
  | 'Propuesta enviada'
  | 'Cierre'
  | 'Ganado'
  | 'En riesgo'

interface Prospect {
  id: string
  contact: string
  company: string
  industry: string
  stage: AIStage
  probability: number // 0–100
  score: number       // AI lead score 0–100
  value: number       // deal value USD
  lastAction: string
}

const STAGE_META: Record<AIStage, { color: string; bg: string }> = {
  'Prospectando':      { color: T.text2,   bg: 'rgba(154,167,189,0.10)' },
  'Calificando':       { color: T.cobalt,  bg: 'rgba(59,130,246,0.12)' },
  'Outreach':          { color: T.cobalt,  bg: 'rgba(59,130,246,0.12)' },
  'Negociando':        { color: T.amber,   bg: 'rgba(245,158,11,0.12)' },
  'Propuesta enviada': { color: T.amber,   bg: 'rgba(245,158,11,0.12)' },
  'Cierre':            { color: T.emerald, bg: 'rgba(16,185,129,0.12)' },
  'Ganado':            { color: T.emerald, bg: 'rgba(16,185,129,0.16)' },
  'En riesgo':         { color: T.red,     bg: 'rgba(239,68,68,0.12)' },
}

const COMPANIES: Array<[string, string, string]> = [
  ['Banco Galicia', 'Servicios Financieros', 'María Fernández'],
  ['Mercado Libre', 'E-commerce', 'Diego Sosa'],
  ['Globant', 'Tecnología', 'Carolina Ruiz'],
  ['Techint', 'Industrial', 'Roberto Paz'],
  ['YPF', 'Energía', 'Lucía Méndez'],
  ['Arcor', 'Consumo Masivo', 'Andrés Coria'],
  ['Despegar', 'Travel Tech', 'Valentina Roca'],
  ['Naranja X', 'Fintech', 'Joaquín Vera'],
  ['Pampa Energía', 'Energía', 'Sofía Aguirre'],
  ['Ualá', 'Fintech', 'Martín Ledesma'],
  ['Tenaris', 'Industrial', 'Paula Giménez'],
  ['Cencosud', 'Retail', 'Federico Lara'],
  ['Pomelo', 'Infra de Pagos', 'Ariana Ponce'],
  ['Auth0', 'Identidad SaaS', 'Nicolás Bravo'],
  ['Satellogic', 'Aeroespacial', 'Camila Ortiz'],
  ['Aleph', 'AdTech', 'Tomás Ferreyra'],
]

const STAGES: AIStage[] = [
  'Prospectando', 'Calificando', 'Outreach', 'Negociando',
  'Propuesta enviada', 'Cierre', 'Ganado', 'En riesgo',
]

const seedProspects = (): Prospect[] =>
  COMPANIES.map(([company, industry, contact], i) => {
    const stage = STAGES[i % STAGES.length]
    const score = 42 + ((i * 37) % 58)
    const probability = Math.min(96, Math.max(6, score - 8 + ((i * 13) % 20)))
    return {
      id: `PRSP-${(1042 + i).toString()}`,
      contact,
      company,
      industry,
      stage,
      probability,
      score,
      value: 8000 + ((i * 9173) % 142000),
      lastAction: 'hace ' + (1 + (i % 9)) + 'h',
    }
  })

/* ─────────────────────────────────────────────
   AGENT AUDIT LOG — reasoning stream
─────────────────────────────────────────────── */
type LogLevel = 'think' | 'data' | 'action' | 'win'
interface LogLine { id: number; ts: string; level: LogLevel; msg: string }

const LEVEL_META: Record<LogLevel, { color: string; tag: string }> = {
  think:  { color: T.cobalt,  tag: 'REASON' },
  data:   { color: T.text2,   tag: 'QUERY ' },
  action: { color: T.amber,   tag: 'ACTION' },
  win:    { color: T.emerald, tag: 'RESULT' },
}

const REASONING_POOL: Array<[LogLevel, string]> = [
  ['think',  'Analizando objeciones del cliente en último hilo de email…'],
  ['data',   'Consultando base de datos B2B · enriqueciendo firmographics'],
  ['think',  'Evaluando intent signals · scoring actualizado a 87/100'],
  ['action', 'Orquestando outreach en LinkedIn para 3 decisores'],
  ['action', 'Generando email hiper-personalizado con contexto de cuenta'],
  ['think',  'Estrategia de cierre seleccionada: anclaje de valor + urgencia'],
  ['data',   'Cruzando histórico de deals similares · win-rate 41%'],
  ['action', 'Agendando demo · propuesta de 3 slots al calendario'],
  ['think',  'Detectando deal estancado · activando secuencia de reactivación'],
  ['win',    'Lead Banco Galicia movido a Negociación · prob. +14%'],
  ['data',   'Verificando presupuesto vía señales de contratación'],
  ['action', 'Enviando propuesta firmada digitalmente a Globant'],
  ['think',  'Priorizando pipeline · 4 leads calientes requieren acción hoy'],
  ['win',    'Demo confirmada con Mercado Libre para mañana 15:00'],
]

const nowTs = (): string => {
  const d = new Date()
  const p = (n: number): string => n.toString().padStart(2, '0')
  return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

/* ─── live brain API (proxied via next rewrite /api/*) ─── */
const BRAIN_BASE = '/api/v1/brain'

interface BrainOverview {
  counts: { agents: number; skills: number; automations: number; total: number }
  health: number
}

type KpiAccent = 'emerald' | 'cobalt' | 'amber'
interface KpiTile {
  key: string
  label: string
  value: string
  delta: { value: number; up: boolean }
  accent: KpiAccent
}
const ACCENT_MAP: Record<KpiAccent, string> = { emerald: T.emerald, cobalt: T.cobalt, amber: T.amber }
const KPI_ICONS: Record<string, React.ReactNode> = {
  roi: <TrendingUp size={18} />, leads: <Users size={18} />,
  conversion: <Target size={18} />, pipeline: <Activity size={18} />,
}
const FALLBACK_KPIS: KpiTile[] = [
  { key: 'roi', label: 'ROI Global', value: '412%', delta: { value: 6.4, up: true }, accent: 'emerald' },
  { key: 'leads', label: 'Leads Procesados', value: '18.4K', delta: { value: 11.2, up: true }, accent: 'cobalt' },
  { key: 'conversion', label: 'Tasa de Conversión', value: '34.8%', delta: { value: 2.1, up: true }, accent: 'cobalt' },
  { key: 'pipeline', label: 'Pipeline Activo', value: '$2.7M', delta: { value: 0.9, up: false }, accent: 'amber' },
]

const TRACE_LEVEL_MAP: Record<string, LogLevel> = {
  REASON: 'think', QUERY: 'data', ACTION: 'action', RESULT: 'win',
}

/* ─────────────────────────────────────────────
   SUB-COMPONENTS
─────────────────────────────────────────────── */
const cardStyle: React.CSSProperties = {
  background: T.panel,
  border: `1px solid ${T.border}`,
  borderRadius: 12,
  padding: 24,
}

const KpiCard = ({
  icon, label, value, delta, deltaUp, accent,
}: {
  icon: React.ReactNode; label: string; value: string
  delta: string; deltaUp: boolean; accent: string
}): React.JSX.Element => (
  <div style={{ ...cardStyle, padding: 20, display: 'flex', flexDirection: 'column', gap: 12 }}>
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <span style={{
        width: 36, height: 36, borderRadius: 8, display: 'grid', placeItems: 'center',
        background: `${accent}1A`, border: `1px solid ${accent}33`, color: accent,
      }}>{icon}</span>
      <span style={{
        display: 'inline-flex', alignItems: 'center', gap: 3, fontFamily: T.mono,
        fontSize: 12, fontWeight: 600, color: deltaUp ? T.emerald : T.red,
      }}>
        {deltaUp ? <ArrowUp size={12} /> : <ArrowDown size={12} />}{delta}
      </span>
    </div>
    <div>
      <div style={{ fontFamily: T.mono, fontSize: 26, fontWeight: 700, color: T.text, letterSpacing: '-0.02em' }}>{value}</div>
      <div style={{ fontSize: 12, color: T.text2, marginTop: 2, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</div>
    </div>
  </div>
)

const ScoreBar = ({ score }: { score: number }): React.JSX.Element => {
  const color = score >= 75 ? T.emerald : score >= 50 ? T.cobalt : T.amber
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ width: 56, height: 6, borderRadius: 6, background: 'rgba(255,255,255,0.08)', overflow: 'hidden' }}>
        <div style={{ width: `${score}%`, height: '100%', borderRadius: 6, background: color }} />
      </div>
      <span style={{ fontFamily: T.mono, fontSize: 12, fontWeight: 600, color, width: 24 }}>{score}</span>
    </div>
  )
}

const StageBadge = ({ stage }: { stage: AIStage }): React.JSX.Element => {
  const m = STAGE_META[stage]
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6, padding: '3px 10px',
      borderRadius: 100, fontSize: 11, fontWeight: 600, color: m.color, background: m.bg,
      border: `1px solid ${m.color}2E`, whiteSpace: 'nowrap',
    }}>
      <span style={{ width: 5, height: 5, borderRadius: '50%', background: m.color }} />
      {stage}
    </span>
  )
}

/* ─────────────────────────────────────────────
   AI PROCESSING — observabilidad (qué procesa la IA)
─────────────────────────────────────────────── */
interface PipelineStage {
  key: string
  label: string
  detail: string
  active: number   // ítems en proceso ahora
  throughput: number // % de carga del stage 0–100
  accent: string
}

const PROCESSING_STAGES: PipelineStage[] = [
  { key: 'ingest',   label: 'Ingesta de señales', detail: '14 canales · WhatsApp, IG, Email, ML', active: 47, throughput: 72, accent: T.cobalt },
  { key: 'qualify',  label: 'Calificación',        detail: 'Lead scoring · intent + firmographics', active: 23, throughput: 58, accent: T.cobalt },
  { key: 'reason',   label: 'Razonamiento',        detail: 'Estrategia · objeciones · próxima acción', active: 12, throughput: 64, accent: T.amber },
  { key: 'act',      label: 'Ejecución',           detail: 'Outreach · propuestas · agenda', active: 9,  throughput: 41, accent: T.amber },
  { key: 'close',    label: 'Cierre & fidelización', detail: 'Negociación · postventa · recompra', active: 6,  throughput: 33, accent: T.emerald },
]

const AIProcessingPanel = (): React.JSX.Element => {
  const [tick, setTick] = useState(0)
  useEffect(() => {
    const iv = window.setInterval(() => setTick(t => t + 1), 2000)
    return () => window.clearInterval(iv)
  }, [])
  // jitter sutil determinista para sensación "en vivo" sin parecer videojuego
  const jitter = (base: number, i: number): number =>
    Math.max(4, Math.min(100, base + Math.round(8 * Math.sin((tick + i) * 1.3))))

  return (
    <div style={cardStyle}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
        <span style={{
          width: 32, height: 32, borderRadius: 8, display: 'grid', placeItems: 'center',
          background: `${T.cobalt}1A`, border: `1px solid ${T.cobalt}33`, color: T.cobalt,
        }}><Workflow size={16} /></span>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>Procesamiento de la IA en tiempo real</h2>
          <p style={{ margin: '2px 0 0', fontSize: 12, color: T.text2 }}>
            Observabilidad del pipeline autónomo · qué está procesando el agente ahora
          </p>
        </div>
        <span style={{
          display: 'inline-flex', alignItems: 'center', gap: 7, padding: '5px 11px',
          borderRadius: 8, border: `1px solid ${T.emerald}33`, background: `${T.emerald}14`,
          fontSize: 11, fontWeight: 600, color: T.emerald, fontFamily: T.mono,
        }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: T.emerald, animation: 'ecc-pulse 1.6s ease-in-out infinite' }} />
          PIPELINE ACTIVO
        </span>
      </div>

      <div style={{
        display: 'grid', gridTemplateColumns: `repeat(${PROCESSING_STAGES.length}, 1fr)`,
        gap: 12, marginTop: 18, alignItems: 'stretch',
      }}>
        {PROCESSING_STAGES.map((s, i) => {
          const load = jitter(s.throughput, i)
          return (
            <div key={s.key} style={{ position: 'relative', display: 'flex', flexDirection: 'column' }}>
              <div style={{
                background: T.bg, border: `1px solid ${T.border}`, borderRadius: 10,
                padding: 14, height: '100%', display: 'flex', flexDirection: 'column', gap: 10,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: T.text }}>{s.label}</span>
                  <span style={{
                    fontFamily: T.mono, fontSize: 12, fontWeight: 700, color: s.accent,
                  }}>{s.active}</span>
                </div>
                <p style={{ margin: 0, fontSize: 11, color: T.text3, lineHeight: 1.5, minHeight: 32 }}>{s.detail}</p>
                <div>
                  <div style={{ height: 5, borderRadius: 5, background: 'rgba(255,255,255,0.07)', overflow: 'hidden' }}>
                    <div style={{ width: `${load}%`, height: '100%', borderRadius: 5, background: s.accent, transition: 'width 1.4s ease' }} />
                  </div>
                  <div style={{ marginTop: 5, fontSize: 10, color: T.text3, fontFamily: T.mono, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    carga {load}%
                  </div>
                </div>
              </div>
              {i < PROCESSING_STAGES.length - 1 && (
                <ArrowRight
                  size={14}
                  style={{ position: 'absolute', right: -13, top: '50%', transform: 'translateY(-50%)', color: T.text3, zIndex: 1 }}
                />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

/* ─────────────────────────────────────────────
   SIDEBAR — barra de herramientas lateral (paleta corporativa)
─────────────────────────────────────────────── */
const NAV_ITEMS: Array<{ id: string; label: string; icon: React.ReactNode; accent: string }> = [
  { id: 'sec-business', label: 'Mi negocio', icon: <Store size={18} />, accent: T.emerald },
  { id: 'sec-rescue', label: 'Crecimiento', icon: <LifeBuoy size={18} />, accent: T.amber },
  { id: 'sec-kpis', label: 'Métricas', icon: <TrendingUp size={18} />, accent: T.emerald },
  { id: 'sec-pipeline', label: 'Pipeline', icon: <Target size={18} />, accent: T.cobalt },
  { id: 'sec-observability', label: 'Procesamiento IA', icon: <Workflow size={18} />, accent: T.cobalt },
  { id: 'sec-neural', label: 'Cerebro Neuronal', icon: <Brain size={18} />, accent: T.cobalt },
]

const SideToolbar = (): React.JSX.Element => {
  const go = (id: string): void => {
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
  return (
    <nav style={{
      position: 'fixed', top: 56, left: 0, bottom: 0, width: 64, zIndex: 30,
      background: T.panel, borderRight: `1px solid ${T.border}`,
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      padding: '16px 0', gap: 8,
    }}>
      <span style={{
        width: 36, height: 36, borderRadius: 9, display: 'grid', placeItems: 'center', marginBottom: 8,
        background: `linear-gradient(135deg, ${T.cobaltDk}, ${T.cobalt})`, color: '#fff',
      }}><Brain size={18} /></span>
      {NAV_ITEMS.map(it => (
        <button
          key={it.id}
          type="button"
          onClick={() => go(it.id)}
          title={it.label}
          aria-label={it.label}
          style={{
            width: 44, height: 44, borderRadius: 10, cursor: 'pointer',
            display: 'grid', placeItems: 'center',
            background: 'transparent', border: `1px solid transparent`,
            color: T.text2, transition: 'background .14s, color .14s, border-color .14s',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = `${it.accent}14`
            e.currentTarget.style.borderColor = `${it.accent}40`
            e.currentTarget.style.color = it.accent
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'transparent'
            e.currentTarget.style.borderColor = 'transparent'
            e.currentTarget.style.color = T.text2
          }}
        >
          {it.icon}
        </button>
      ))}
    </nav>
  )
}

/* ─────────────────────────────────────────────
   MAIN
─────────────────────────────────────────────── */
type SortKey = 'score' | 'probability' | 'value'

export const EnterpriseCommandCenter = (): React.JSX.Element => {
  const [prospects] = useState<Prospect[]>(seedProspects)
  const [query, setQuery] = useState('')
  const [stageFilter, setStageFilter] = useState<AIStage | 'all'>('all')
  const [sortKey, setSortKey] = useState<SortKey>('score')
  const [page, setPage] = useState(0)

  // ── header controls (search / voz / Computer Use) — portados del MissionControlBar ──
  const [handsFree, setHandsFree] = useState(false)
  const [cuaMode, setCuaMode] = useState<CuaMode>('off')
  const [cuaLauncherOpen, setCuaLauncherOpen] = useState(false)
  const [user, setUser] = useState<UserProfile | null>(null)
  useEffect(() => { const u = loadUser(); if (u) setUser(u) }, [])

  // ── vista del cerebro: flujos (n8n) vs overview (grafo apagado) ──
  const [neuralView, setNeuralView] = useState<'flows' | 'overview'>('flows')
  // ── prompt de Computer Use (aparece al elegir Piloto Automático/Supervisado) ──
  const [cuaPrompt, setCuaPrompt] = useState('')
  const [cuaSending, setCuaSending] = useState(false)
  const [cuaMsg, setCuaMsg] = useState('')

  // ── perfil de negocio (cuestionario + links) ──
  const [profile, setProfile] = useState<BusinessProfile | null>(null)
  const [profileOpen, setProfileOpen] = useState(false)
  const [openToolId, setOpenToolId] = useState<string | null>(null)
  useEffect(() => { setProfile(loadProfile()) }, [])
  const profileDone = isComplete(profile)

  // Computer Use acciona sobre flujos planificados (por cuenta o de rescate).
  const [plannedFlows, setPlannedFlows] = useState<PlannedFlow[]>([])
  const executePlan = useCallback((flows: PlannedFlow[]): void => {
    setPlannedFlows(flows)
    setCuaMode('supervised')
    setNeuralView('flows')
    document.getElementById('sec-neural')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    // Ejecución real best-effort: una sesión CU por flujo (si hay backend+key).
    flows.forEach(f => {
      void fetch('/api/v1/brain/cua/dispatch', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instruction: f.instruction ?? f.name, mode: 'supervised' }),
      }).catch(() => { /* sin backend → queda como plan visible */ })
    })
  }, [])
  const planFromToolkit = useCallback((): void => { executePlan(planAccountFlows(loadProfile())) }, [executePlan])

  const dispatchCua = useCallback(async (): Promise<void> => {
    const instruction = cuaPrompt.trim()
    if (!instruction || cuaMode === 'off') return
    setCuaSending(true); setCuaMsg('')
    try {
      const r = await fetch('/api/v1/brain/cua/dispatch', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instruction, mode: cuaMode === 'auto' ? 'auto' : 'supervised' }),
      })
      if (!r.ok) throw new Error(String(r.status))
      const d = await r.json()
      const base = `Flujo creado: ${d.flow?.name ?? 'OK'}.`
      if (d.can_execute) {
        setCuaMsg(`${base} Ejecución real disponible — abriendo sesión Computer Use.`)
        setCuaLauncherOpen(true)
      } else {
        setCuaMsg(`${base} Plan + telemetría (ver en Flujos). Para ejecutar de verdad falta API key del cerebro.`)
      }
      setCuaPrompt(''); setNeuralView('flows')
      document.getElementById('sec-neural')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    } catch {
      setCuaMsg('No se pudo despachar (¿backend del cerebro arriba?). Intentá de nuevo.')
    } finally {
      setCuaSending(false)
    }
  }, [cuaPrompt, cuaMode])

  // ── view router (multi-page nav within shell) ─────────────────────────────
  type ViewId = 'dashboard' | 'squads' | 'pipeline' | 'audit' | 'handoff' | 'approvals' | 'neural'
  const [view, setView] = useState<ViewId>('dashboard')
  const showSquads    = view === 'dashboard' || view === 'squads'
  const showPipeline  = view === 'dashboard' || view === 'pipeline'
  const showAudit     = view === 'dashboard' || view === 'audit'
  const showHandoff   = view === 'dashboard' || view === 'handoff'
  const showApprovals = view === 'dashboard' || view === 'approvals'
  const showNeural    = view === 'dashboard' || view === 'neural'
  const showKpis      = view === 'dashboard'

  // El command bar busca/abre módulos; en este shell scrolleamos al destino si existe.
  const handleJump = useCallback((componentId: string, _lobe?: LobeId): void => {
    const el = document.getElementById(componentId)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [])

  // Resuelve y EJECUTA una orden de voz; retorna la respuesta hablada.
  const handleVoiceCommand = useCallback((text: string): string => {
    const t = text.toLowerCase()
    const scrollTo = (id: string, label: string): string => {
      document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      return `Listo, te muestro ${label}.`
    }
    if (/cerebro|neuronal|sinapsis|red neuronal|grafo/.test(t)) return scrollTo('sec-neural', 'el cerebro neuronal en vivo')
    if (/pipeline|ventas|prospecto|deal|embudo/.test(t)) return scrollTo('sec-pipeline', 'el pipeline de ventas')
    if (/m[eé]trica|kpi|roi|conversi[oó]n|n[uú]mero/.test(t)) return scrollTo('sec-kpis', 'las métricas')
    if (/procesa|observabilidad|qu[eé] (est[aá]|hace)|actividad/.test(t)) return scrollTo('sec-observability', 'qué está procesando la IA')
    if (/(computer use|navegador|sandbox|operar)/.test(t)) {
      setCuaMode('supervised'); setCuaLauncherOpen(true)
      return 'Abro Computer Use en modo supervisado.'
    }
    if (/(autopiloto|aut[oó]nomo|piloto)/.test(t)) {
      setCuaMode('auto'); return 'Activo Computer Use en piloto automático.'
    }
    if (/(detener|desactivar|para[r]?|pausa)/.test(t)) {
      setCuaMode('off'); return 'Computer Use desactivado.'
    }
    return `No reconocí la orden: "${text}". Probá: mostrá el pipeline, abrí Computer Use, o mostrá el cerebro neuronal.`
  }, [])

  // ── audit log stream ──
  const [logs, setLogs] = useState<LogLine[]>(() =>
    REASONING_POOL.slice(0, 6).map(([level, msg], i) => ({ id: i, ts: nowTs(), level, msg })),
  )
  const logCounter = useRef(REASONING_POOL.length)
  const logBody = useRef<HTMLDivElement>(null)

  // ── live brain metadata (graceful fallback to mock) ──
  const [brain, setBrain] = useState<BrainOverview | null>(null)
  const [kpis, setKpis] = useState<KpiTile[]>(FALLBACK_KPIS)

  useEffect(() => {
    const ctrl = new AbortController()
    const load = async (): Promise<void> => {
      try {
        const [ovRes, trRes, kpiRes] = await Promise.all([
          fetch(`${BRAIN_BASE}/overview`, { signal: ctrl.signal }),
          fetch(`${BRAIN_BASE}/audit-trace?limit=8`, { signal: ctrl.signal }),
          fetch(`${BRAIN_BASE}/kpis`, { signal: ctrl.signal }),
        ])
        if (kpiRes.ok) {
          const data = (await kpiRes.json()) as { tiles: KpiTile[] }
          if (Array.isArray(data.tiles) && data.tiles.length) setKpis(data.tiles)
        }
        if (ovRes.ok) setBrain((await ovRes.json()) as BrainOverview)
        if (trRes.ok) {
          const data = (await trRes.json()) as { lines: Array<{ level: string; message: string }> }
          if (Array.isArray(data.lines) && data.lines.length) {
            setLogs(data.lines.map((l, i) => ({
              id: i,
              ts: nowTs(),
              level: TRACE_LEVEL_MAP[l.level] ?? 'think',
              msg: l.message,
            })))
            logCounter.current = data.lines.length
          }
        }
      } catch {
        /* offline / backend down → keep mock seed */
      }
    }
    void load()
    return () => ctrl.abort()
  }, [])

  useEffect(() => {
    const iv = window.setInterval(() => {
      const [level, msg] = REASONING_POOL[Math.floor(Math.random() * REASONING_POOL.length)]
      logCounter.current += 1
      setLogs(prev => [...prev.slice(-40), { id: logCounter.current, ts: nowTs(), level, msg }])
    }, 2200)
    return () => window.clearInterval(iv)
  }, [])

  useEffect(() => {
    if (logBody.current) logBody.current.scrollTop = logBody.current.scrollHeight
  }, [logs])

  // ── derived table ──
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return prospects
      .filter(p => stageFilter === 'all' || p.stage === stageFilter)
      .filter(p =>
        !q ||
        p.company.toLowerCase().includes(q) ||
        p.contact.toLowerCase().includes(q) ||
        p.industry.toLowerCase().includes(q),
      )
      .sort((a, b) => b[sortKey] - a[sortKey])
  }, [prospects, query, stageFilter, sortKey])

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const safePage = Math.min(page, pageCount - 1)
  const rows = filtered.slice(safePage * PAGE_SIZE, safePage * PAGE_SIZE + PAGE_SIZE)

  useEffect(() => { setPage(0) }, [query, stageFilter, sortKey])

  const sortBtn = (key: SortKey, label: string): React.JSX.Element => (
    <button
      type="button"
      onClick={() => setSortKey(key)}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 4, padding: '4px 10px',
        borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer',
        fontFamily: T.sans,
        background: sortKey === key ? `${T.cobalt}1F` : 'transparent',
        border: `1px solid ${sortKey === key ? `${T.cobalt}55` : T.border}`,
        color: sortKey === key ? T.cobalt : T.text2,
      }}
    >
      {sortKey === key && <ArrowDown size={11} />}{label}
    </button>
  )

  return (
    <div data-sellia-shell="brain" style={{ minHeight: '100vh', background: T.bg, color: T.text, fontFamily: T.sans, paddingTop: 56, paddingLeft: 64 }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
        *,*::before,*::after{box-sizing:border-box;}
        .ecc-row{transition:background .12s;}
        .ecc-row:hover{background:${T.panelAlt};}
        .ecc-input::placeholder{color:${T.text3};}
        @keyframes ecc-pulse{0%,100%{opacity:1;}50%{opacity:.35;}}
        ::-webkit-scrollbar{width:8px;height:8px;background:transparent;}
        ::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.12);border-radius:6px;}
      `}</style>

      {/* ── COMMAND BAR (search + voz + Computer Use) — portado del MissionControlBar ── */}
      <MissionControlBar
        onJump={handleJump}
        handsFree={handsFree}
        onHandsFreeToggle={() => setHandsFree(v => !v)}
        onLaunchCUA={() => setCuaLauncherOpen(true)}
        cuaMode={cuaMode}
        onCuaMode={setCuaMode}
        activeTasks={0}
        isRunning={cuaMode !== 'off'}
        user={user}
        onLogin={(u) => setUser(u)}
        onLogout={() => { clearUser(); setUser(null) }}
      />
      <HandsFreeOverlay open={handsFree} onClose={() => setHandsFree(false)} onCommand={handleVoiceCommand} />
      <ComputerUseLauncher open={cuaLauncherOpen} onClose={() => setCuaLauncherOpen(false)} onJump={handleJump} />

      {/* ── SIDEBAR lateral izquierdo ── */}
      <SideToolbar />

      {/* ── Cuestionario de negocio (modal) ── */}
      <BusinessProfileWizard open={profileOpen} onClose={() => setProfileOpen(false)} onSaved={(p) => setProfile(p)} />

      {/* ── Tool Studio (detalle + lanzar herramienta) ── */}
      <ToolStudio toolId={openToolId} profile={profile} onClose={() => setOpenToolId(null)} onLaunch={(f) => executePlan([f])}
        onAddToPlan={(f) => { setPlannedFlows(prev => [...prev, f]); setNeuralView('flows'); document.getElementById('sec-neural')?.scrollIntoView({ behavior: 'smooth', block: 'start' }) }} />

      {/* ── Banner obligatorio si el perfil no está completo ── */}
      {!profileDone && (
        <div style={{
          position: 'sticky', top: 56, zIndex: 19, display: 'flex', alignItems: 'center', gap: 12,
          padding: '10px 28px', background: `${T.amber}14`, borderBottom: `1px solid ${T.amber}40`,
        }}>
          <Store size={16} style={{ color: T.amber }} />
          <span style={{ fontSize: 13, color: T.text }}>
            Completá tu negocio (qué vendés + tus links de venta/anuncios/redes) para que SellIA venda por vos.
          </span>
          <span style={{ flex: 1 }} />
          <button type="button" onClick={() => setProfileOpen(true)} style={{
            padding: '7px 14px', borderRadius: 8, border: 'none', background: T.amber, color: '#1a1205',
            fontWeight: 700, fontSize: 12, cursor: 'pointer',
          }}>Completar</button>
        </div>
      )}

      {/* ── TOP BAR ── */}
      <header style={{
        position: 'sticky', top: 56, zIndex: 20, background: 'rgba(10,15,26,0.85)',
        backdropFilter: 'blur(12px)', borderBottom: `1px solid ${T.border}`,
        padding: '16px 28px', display: 'flex', alignItems: 'center', gap: 16,
      }}>
        <span style={{
          width: 38, height: 38, borderRadius: 9, display: 'grid', placeItems: 'center',
          background: `linear-gradient(135deg, ${T.cobaltDk}, ${T.cobalt})`, color: '#fff',
        }}><Brain size={20} /></span>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: '-0.01em' }}>SellIA · Command Center</div>
          <div style={{ fontSize: 11, color: T.text2, fontFamily: T.mono }}>Súper Agente de Ventas B2B</div>
        </div>
        <div style={{ flex: 1 }} />
        {brain && (
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: 8, padding: '6px 12px',
            borderRadius: 8, border: `1px solid ${T.border}`, background: T.panel,
            fontSize: 12, fontWeight: 600, color: T.text2, fontFamily: T.mono,
          }}>
            <Brain size={13} style={{ color: T.cobalt }} />
            {brain.counts.total} capacidades
            <span style={{ color: T.text3 }}>·</span>
            <span style={{ color: T.emerald }}>salud {(brain.health * 100).toFixed(0)}%</span>
          </span>
        )}
        <span style={{
          display: 'inline-flex', alignItems: 'center', gap: 7, padding: '6px 12px',
          borderRadius: 8, border: `1px solid ${T.emerald}33`, background: `${T.emerald}14`,
          fontSize: 12, fontWeight: 600, color: T.emerald, fontFamily: T.mono,
        }}>
          <span style={{ width: 7, height: 7, borderRadius: '50%', background: T.emerald, animation: 'ecc-pulse 2s ease-in-out infinite' }} />
          AGENTE ACTIVO
        </span>
      </header>

      {/* ── VIEW NAV · separa cada herramienta en su propia "página" ── */}
      <nav style={{
        position: 'sticky', top: 56 + 70, zIndex: 19,
        background: 'rgba(10,15,26,0.92)', backdropFilter: 'blur(12px)',
        borderBottom: `1px solid ${T.border}`, padding: '10px 28px',
        display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap',
      }}>
        {([
          { id: 'dashboard',  label: 'Dashboard',          icon: <Activity   size={13} /> },
          { id: 'squads',     label: 'Escuadrones',        icon: <Users      size={13} /> },
          { id: 'pipeline',   label: 'Pipeline de Ventas', icon: <Target     size={13} /> },
          { id: 'audit',      label: 'Agent Audit Log',    icon: <Cpu        size={13} /> },
          { id: 'handoff',    label: 'Handoff · Slack IA', icon: <Workflow   size={13} /> },
          { id: 'approvals',  label: 'Aprobaciones',       icon: <TrendingUp size={13} /> },
          { id: 'neural',     label: 'Cerebro Neuronal',   icon: <Brain      size={13} /> },
        ] as { id: ViewId; label: string; icon: React.JSX.Element }[]).map(tab => {
          const active = view === tab.id
          return (
            <button key={tab.id} type="button" onClick={() => setView(tab.id)}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 6,
                padding: '7px 12px', borderRadius: 8, cursor: 'pointer',
                fontFamily: T.sans, fontSize: 12, fontWeight: 600,
                border: `1px solid ${active ? T.cobalt : T.border}`,
                background: active ? `${T.cobalt}22` : 'transparent',
                color: active ? T.cobalt : T.text2,
                transition: 'background .15s, border-color .15s, color .15s',
              }}>
              {tab.icon}{tab.label}
            </button>
          )
        })}
        <div style={{ flex: 1 }} />
        <span style={{
          fontSize: 10, color: T.text3, fontFamily: T.mono,
          letterSpacing: '0.06em', textTransform: 'uppercase',
        }}>
          vista: {view}
        </span>
      </nav>

      {/* ── MI NEGOCIO: toolkit (recomendaciones + validador de links) ── */}
      {showKpis && (
      <section id="sec-business" style={{ padding: '20px 28px 0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
          <span style={{ width: 30, height: 30, borderRadius: 8, display: 'grid', placeItems: 'center', background: `${T.emerald}1A`, border: `1px solid ${T.emerald}33`, color: T.emerald }}>
            <Store size={16} />
          </span>
          <div>
            <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: T.text }}>Mi negocio</h2>
            <p style={{ margin: '2px 0 0', fontSize: 12, color: T.text2 }}>Lo que vendés, tus plataformas y links · recomendaciones para vender + lanzar Computer Use sobre tus canales.</p>
          </div>
        </div>
        <BusinessToolkit profile={profile} onEdit={() => setProfileOpen(true)} onPlan={planFromToolkit} onOpenTool={setOpenToolId}
          onPlanComplete={(ids) => executePlan(buildToolPlan(loadProfile(), ids))} />
      </section>
      )}

      {/* ── MODO RESCATE: sin clientes → estrategia de adquisición ── */}
      {showKpis && (
      <section id="sec-rescue" style={{ padding: '20px 28px 0' }}>
        <RescueMode profile={profile} onEdit={() => setProfileOpen(true)} onRescue={executePlan} />
      </section>
      )}

      {/* ── KPI ROW ── (solo en Dashboard) */}
      {showKpis && (
      <section id="sec-kpis" style={{ padding: '24px 28px 0', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
        {kpis.map(k => (
          <KpiCard
            key={k.key}
            icon={KPI_ICONS[k.key] ?? <Activity size={18} />}
            label={k.label}
            value={k.value}
            delta={`${k.delta.value}%`}
            deltaUp={k.delta.up}
            accent={ACCENT_MAP[k.accent] ?? T.cobalt}
          />
        ))}
      </section>
      )}

      {/* ── ESCUADRONES IA · telemetría por departamento ── */}
      {showSquads && (
      <section id="sec-squads" style={{ padding: '20px 28px 0' }}>
        <SquadStatusPanel />
      </section>
      )}

      {/* ── MAIN GRID: table + audit log ──
          dashboard: side-by-side  ·  pipeline-only: full width  ·  audit-only: small column */}
      {(showPipeline || showAudit) && (
      <main id="sec-pipeline" style={{
        padding: 24, paddingTop: 20, display: 'grid',
        gridTemplateColumns: view === 'pipeline' ? '1fr'
                          : view === 'audit'    ? '1fr'
                          : 'minmax(0, 1fr) 380px',
        gap: 16, alignItems: 'start',
      }}>
        {/* ─ DATA TABLE ─ */}
        {showPipeline && (
        <div style={cardStyle}>
          {/* table header / controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 18 }}>
            <div>
              <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>Pipeline de Ventas</h2>
              <p style={{ margin: '2px 0 0', fontSize: 12, color: T.text2 }}>
                Gestionado por el agente · {filtered.length} prospectos
              </p>
            </div>
            <div style={{ flex: 1 }} />
            <div style={{
              display: 'flex', alignItems: 'center', gap: 8, padding: '7px 12px',
              borderRadius: 8, border: `1px solid ${T.border}`, background: T.bg, minWidth: 220,
            }}>
              <Search size={15} style={{ color: T.text3 }} />
              <input
                className="ecc-input"
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Buscar empresa, contacto, industria…"
                style={{ flex: 1, background: 'none', border: 'none', outline: 'none', color: T.text, fontSize: 13, fontFamily: T.sans }}
              />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Filter size={14} style={{ color: T.text3 }} />
              <select
                value={stageFilter}
                onChange={e => setStageFilter(e.target.value as AIStage | 'all')}
                style={{
                  padding: '7px 10px', borderRadius: 8, border: `1px solid ${T.border}`,
                  background: T.bg, color: T.text, fontSize: 13, fontFamily: T.sans, cursor: 'pointer', outline: 'none',
                }}
              >
                <option value="all">Todos los estados</option>
                {STAGES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>

          {/* sort controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <span style={{ fontSize: 11, color: T.text3, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Ordenar:</span>
            {sortBtn('score', 'Lead Score')}
            {sortBtn('probability', 'Prob. Cierre')}
            {sortBtn('value', 'Valor')}
          </div>

          {/* table */}
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 720 }}>
              <thead>
                <tr style={{ textAlign: 'left' }}>
                  {['ID', 'Empresa / Contacto', 'Estado IA', 'Lead Score', 'Prob. Cierre', 'Valor'].map(h => (
                    <th key={h} style={{
                      padding: '0 14px 10px', fontSize: 11, fontWeight: 600, color: T.text3,
                      textTransform: 'uppercase', letterSpacing: '0.06em',
                      borderBottom: `1px solid ${T.border}`, whiteSpace: 'nowrap',
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map(p => (
                  <tr key={p.id} className="ecc-row" style={{ borderBottom: `1px solid ${T.border}` }}>
                    <td style={{ padding: '14px', fontFamily: T.mono, fontSize: 12, color: T.text3, whiteSpace: 'nowrap' }}>{p.id}</td>
                    <td style={{ padding: '14px' }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: T.text }}>{p.company}</div>
                      <div style={{ fontSize: 11, color: T.text2 }}>{p.contact} · {p.industry}</div>
                    </td>
                    <td style={{ padding: '14px' }}><StageBadge stage={p.stage} /></td>
                    <td style={{ padding: '14px' }}><ScoreBar score={p.score} /></td>
                    <td style={{ padding: '14px' }}>
                      <span style={{
                        fontFamily: T.mono, fontSize: 13, fontWeight: 600,
                        color: p.probability >= 60 ? T.emerald : p.probability >= 35 ? T.amber : T.text2,
                      }}>{p.probability}%</span>
                    </td>
                    <td style={{ padding: '14px', fontFamily: T.mono, fontSize: 13, fontWeight: 600, color: T.text }}>
                      ${(p.value / 1000).toFixed(1)}K
                    </td>
                  </tr>
                ))}
                {rows.length === 0 && (
                  <tr><td colSpan={6} style={{ padding: 40, textAlign: 'center', color: T.text3, fontSize: 13 }}>
                    Sin prospectos para los filtros aplicados.
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>

          {/* pagination */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 16 }}>
            <span style={{ fontSize: 12, color: T.text2 }}>
              {filtered.length === 0 ? 0 : safePage * PAGE_SIZE + 1}–{Math.min((safePage + 1) * PAGE_SIZE, filtered.length)} de {filtered.length}
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <button
                type="button"
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={safePage === 0}
                style={{
                  display: 'grid', placeItems: 'center', width: 32, height: 32, borderRadius: 8,
                  border: `1px solid ${T.border}`, background: T.bg, color: T.text2,
                  cursor: safePage === 0 ? 'not-allowed' : 'pointer', opacity: safePage === 0 ? 0.4 : 1,
                }}
              ><ChevronLeft size={16} /></button>
              <span style={{ fontFamily: T.mono, fontSize: 13, color: T.text, minWidth: 60, textAlign: 'center' }}>
                {safePage + 1} / {pageCount}
              </span>
              <button
                type="button"
                onClick={() => setPage(p => Math.min(pageCount - 1, p + 1))}
                disabled={safePage >= pageCount - 1}
                style={{
                  display: 'grid', placeItems: 'center', width: 32, height: 32, borderRadius: 8,
                  border: `1px solid ${T.border}`, background: T.bg, color: T.text2,
                  cursor: safePage >= pageCount - 1 ? 'not-allowed' : 'pointer', opacity: safePage >= pageCount - 1 ? 0.4 : 1,
                }}
              ><ChevronRight size={16} /></button>
            </div>
          </div>
        </div>
        )}

        {/* ─ AGENT AUDIT LOG ─ */}
        {showAudit && (
        <aside style={{ ...cardStyle, padding: 0, overflow: 'hidden', position: view === 'audit' ? 'static' : 'sticky', top: 88 }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10, padding: '18px 20px',
            borderBottom: `1px solid ${T.border}`,
          }}>
            <span style={{
              width: 32, height: 32, borderRadius: 8, display: 'grid', placeItems: 'center',
              background: `${T.cobalt}1A`, border: `1px solid ${T.cobalt}33`, color: T.cobalt,
            }}><Cpu size={16} /></span>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13, fontWeight: 700 }}>Agent Audit Log</div>
              <div style={{ fontSize: 11, color: T.text2, fontFamily: T.mono }}>Razonamiento en tiempo real</div>
            </div>
            <span style={{ width: 7, height: 7, borderRadius: '50%', background: T.emerald, animation: 'ecc-pulse 1.6s ease-in-out infinite' }} />
          </div>

          <div ref={logBody} style={{
            height: 520, overflowY: 'auto', padding: '14px 16px', background: '#070B12',
            fontFamily: T.mono, fontSize: 12, lineHeight: 1.7,
          }}>
            {logs.map(l => {
              const m = LEVEL_META[l.level]
              return (
                <div key={l.id} style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                  <span style={{ color: T.text3, flexShrink: 0 }}>{l.ts}</span>
                  <span style={{ color: m.color, flexShrink: 0, fontWeight: 600 }}>{m.tag}</span>
                  <span style={{ color: l.level === 'win' ? T.emerald : T.text }}>{l.msg}</span>
                </div>
              )
            })}
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', color: T.cobalt }}>
              <span style={{ color: T.text3 }}>{nowTs()}</span>
              <span style={{ width: 7, height: 14, background: T.cobalt, display: 'inline-block', animation: 'ecc-pulse 1s steps(2) infinite' }} />
            </div>
          </div>
        </aside>
        )}
      </main>
      )}

      {/* ── HANDOFF LOG + APPROVALS — vista combinada o por separado ── */}
      {(showHandoff || showApprovals) && (
      <section id="sec-collab" style={{
        padding: '12px 28px 8px', display: 'grid',
        gridTemplateColumns: view === 'handoff'   ? '1fr'
                          : view === 'approvals' ? '1fr'
                          : '1fr 1fr',
        gap: 16, alignItems: 'start',
      }}>
        {showHandoff   && <HandoffLog />}
        {showApprovals && <ApprovalsCenter />}
      </section>
      )}

      {/* ── OBSERVABILIDAD: procesamiento de la IA ── */}
      {showNeural && (
      <section id="sec-observability" style={{ padding: '4px 28px 8px' }}>
        <AIProcessingPanel />
      </section>
      )}

      {/* ── CEREBRO NEURONAL EN VIVO ── */}
      {showNeural && (
      <section id="sec-neural" style={{ padding: '12px 28px 36px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
          <span style={{
            width: 32, height: 32, borderRadius: 8, display: 'grid', placeItems: 'center',
            background: `${T.cobalt}1A`, border: `1px solid ${T.cobalt}33`, color: T.cobalt,
          }}><Brain size={16} /></span>
          <div style={{ flex: 1 }}>
            <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: T.text }}>Mapa de Interacciones del Cerebro</h2>
            <p style={{ margin: '2px 0 0', fontSize: 12, color: T.text2 }}>
              {neuralView === 'flows'
                ? 'Flujos en vivo estilo n8n: automatizaciones y sesiones de Computer Use ejecutándose. Los nodos se iluminan con actividad real.'
                : 'Vista general (apagado): todo el cerebro — agentes, automatizaciones, skills, plataformas y herramientas, por categoría.'}
            </p>
          </div>
          {/* toggle Flujos / Vista general */}
          <div style={{ display: 'inline-flex', borderRadius: 9, border: `1px solid ${T.border}`, overflow: 'hidden' }}>
            {(['flows', 'overview'] as const).map(v => (
              <button key={v} type="button" onClick={() => setNeuralView(v)}
                style={{
                  padding: '7px 13px', fontSize: 12, fontWeight: 600, cursor: 'pointer', border: 'none',
                  fontFamily: T.sans,
                  background: neuralView === v ? `${T.cobalt}1F` : 'transparent',
                  color: neuralView === v ? T.cobalt : T.text2,
                }}>
                {v === 'flows' ? 'Flujos en vivo' : 'Vista general'}
              </button>
            ))}
          </div>
        </div>

        {/* ── Panel de indicaciones Computer Use (al elegir Piloto Automático / Supervisado) ── */}
        {cuaMode !== 'off' && (
          <div style={{ ...cardStyle, padding: 16, marginBottom: 14, borderColor: `${T.cobalt}44` }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <Cpu size={15} style={{ color: T.cobalt }} />
              <span style={{ fontSize: 13, fontWeight: 700, color: T.text }}>
                Indicaciones para Computer Use · {cuaMode === 'auto' ? 'Piloto Automático' : 'Supervisado'}
              </span>
            </div>
            <p style={{ margin: '0 0 10px', fontSize: 12, color: T.text2 }}>
              Escribí qué querés que el cerebro resuelva: planificar, crear, comunicar, publicar, vender… SellIA elegirá agentes, herramientas, skills y plataformas y lo ejecutará como un flujo.
            </p>
            <textarea
              value={cuaPrompt}
              onChange={e => setCuaPrompt(e.target.value)}
              placeholder="Ej: Creá una campaña de anuncios en Instagram para vender zapatillas y respondé las consultas por WhatsApp."
              rows={3}
              style={{
                width: '100%', resize: 'vertical', padding: '10px 12px', borderRadius: 9,
                background: T.bg, border: `1px solid ${T.border}`, color: T.text,
                fontSize: 13, fontFamily: T.sans, outline: 'none', boxSizing: 'border-box',
              }}
            />
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 10 }}>
              <button type="button" onClick={() => { void dispatchCua() }} disabled={cuaSending || !cuaPrompt.trim()}
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: 7, padding: '9px 16px', borderRadius: 9,
                  fontSize: 13, fontWeight: 700, cursor: cuaSending || !cuaPrompt.trim() ? 'not-allowed' : 'pointer',
                  border: 'none', background: T.cobalt, color: '#fff', opacity: cuaSending || !cuaPrompt.trim() ? 0.5 : 1,
                }}>
                <ArrowRight size={14} /> {cuaSending ? 'Despachando…' : 'Dar indicación'}
              </button>
              {cuaMsg && <span style={{ fontSize: 12, color: T.text2 }}>{cuaMsg}</span>}
            </div>
          </div>
        )}

        <div style={{ ...cardStyle, padding: 0, overflow: 'hidden' }}>
          {neuralView === 'flows' ? <BrainFlowsView extraFlows={plannedFlows} /> : <BrainInteractionMap />}
        </div>
      </section>
      )}
    </div>
  )
}

export default EnterpriseCommandCenter
