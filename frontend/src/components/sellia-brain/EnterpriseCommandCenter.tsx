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
  Bot, Power,
} from 'lucide-react'
import { t } from '@/lib/sellia-i18n'

import MissionControlBar, {
  type CuaMode, type UserProfile, loadUser, clearUser, isAuthenticated,
} from './MissionControlBar'
import { useLeads } from '@/hooks/useSellIA'
import HandsFreeOverlay from './HandsFreeOverlay'
import ComputerUseLauncher from './ComputerUseLauncher'
import dynamic from 'next/dynamic'
import { type LobeId } from './toolIndex'
import { type BusinessProfile, type PlannedFlow, loadProfile, isComplete, planAccountFlows, buildToolPlan } from '@/lib/business-profile'
import { getDisabledCapabilities, onCapabilitiesChanged } from '@/lib/brain-capability-toggles'
import { getToken } from '@/lib/sellia-api'
import { businessContextApi } from '@/lib/businessContext'

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
// Real, backend-synced questionnaire (business_context) -- used for logged-in
// users instead of the fake localStorage-only BusinessProfileWizard below.
const RealBusinessContextWizard = dynamic(() => import('../missions/BusinessContextWizard'), { ssr: false })
const BusinessToolkit = dynamic(() => import('./BusinessToolkit'), { ssr: false })
const RescueMode = dynamic(() => import('./RescueMode'), { ssr: false })
const ToolStudio = dynamic(() => import('./ToolStudio'), { ssr: false })
import SquadStatusPanel from '../sellia-hub/SquadStatusPanel'
import HandoffLog, { type HandoffEvent, type DeptId } from '../sellia-hub/HandoffLog'
import ApprovalsCenter, { type ApprovalRequest } from '../sellia-hub/ApprovalsCenter'

const BRAIN_BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://sellia-production.up.railway.app'

interface RawAuditLog {
  id: string
  created_at: string | null
  platform: string | null
  action_type: string | null
  agent_name: string | null
  strategy_name: string | null
  confidence_score: number
  status: string
  input_data: string | null
  output_data: string | null
  error_message: string | null
}

const PLATFORM_TO_DEPT: Record<string, DeptId> = {
  whatsapp: 'sdr', instagram: 'sdr', tiktok: 'ads', facebook: 'ads',
  mercadolibre: 'cua', amazon: 'cua', hotmart: 'cs', website: 'cs',
  slack: 'core', email: 'sdr',
}

const mapToApprovalRequest = (l: RawAuditLog): ApprovalRequest => ({
  id: l.id,
  createdAt: l.created_at || new Date().toISOString(),
  dept: (PLATFORM_TO_DEPT[l.platform || ''] as ApprovalRequest['dept']) || 'cua',
  kind: 'autonomous_purchase',
  title: `${l.action_type || 'Acción'} · ${l.platform || 'plataforma desconocida'}`,
  description: l.input_data || 'Acción de agente pendiente de aprobación humana.',
  rationale: l.strategy_name ? `Estrategia: ${l.strategy_name}` : 'Generado por agente autónomo.',
  severity: l.confidence_score < 0.5 ? 'high' : l.confidence_score < 0.75 ? 'medium' : 'low',
  context: { confianza: `${Math.round((l.confidence_score || 0) * 100)}%`, agente: l.agent_name || 'n/a' },
})

const mapToHandoffEvent = (l: RawAuditLog): HandoffEvent => ({
  id: l.id,
  ts: l.created_at || new Date().toISOString(),
  from: PLATFORM_TO_DEPT[l.platform || ''] || 'core',
  tag: l.status === 'failed' ? 'ALERT' : l.status === 'success' ? 'WIN' : 'STATUS',
  text: l.output_data || l.input_data || `${l.action_type || 'actividad'} vía ${l.platform || 'n/a'}`,
})

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

const nowTs = (): string => {
  const d = new Date()
  const p = (n: number): string => n.toString().padStart(2, '0')
  return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

interface BrainOverview {
  counts: { agents: number; skills: number; automations: number; total: number }
  health: number
}

// Mirrors backend/app/domains/ai_activity/service.py's get_account_summary --
// the real, per-account source of truth for whether this account's AI is
// actually ready to be shown as active anywhere in the UI.
interface AccountSetupSummary {
  questionnaire: { is_fully_complete?: boolean; completed_steps?: number; total_steps?: number }
  setup: {
    has_business: boolean
    has_subdomain: boolean
    subdomain?: string | null
    questionnaire_complete: boolean
    has_channel_declared: boolean
    setup_complete: boolean
  }
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
  active: <TrendingUp size={18} />, leads: <Users size={18} />,
  conversion: <Target size={18} />, pipeline: <Activity size={18} />,
  channels: <Workflow size={18} />, conversations: <Users size={18} />,
  ai_replies: <Bot size={18} />, ai_actions: <Cpu size={18} />,
}
/** Strip mostrado sobre los paneles alimentados por endpoints GLOBALES
 *  (/brain/squads, /brain/handoff-log, /brain/audit-log, la tabla `leads`).
 *  Ninguno de esos datos tiene dueño: son de la plataforma, no de la cuenta
 *  logueada. Antes se mostraban tal cual dentro del dashboard de un usuario,
 *  que los leía como propios ("1/1 ejecutando" en una cuenta recién creada).
 *  No se ocultan —siguen sirviendo como demo— pero quedan rotulados. */
const DemoDataNotice = ({ what }: { what: string }): React.JSX.Element => (
  <div style={{
    display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap',
    padding: '7px 12px', marginBottom: 10, borderRadius: 8,
    border: `1px solid ${T.amber}33`, background: `${T.amber}0F`,
    fontSize: 11, color: T.amber, fontFamily: T.mono, letterSpacing: '0.03em',
  }}>
    DEMO · {what} de la plataforma, no de tu cuenta
    <a href="/dashboard/conversaciones" style={{ color: T.emerald, fontWeight: 700, textDecoration: 'none' }}>
      ver lo real de tu cuenta →
    </a>
  </div>
)

// Mirrors backend/app/domains/ai_activity/service.py's get_account_kpis --
// every number is scoped to the logged-in account (Business.user_id), unlike
// /brain/kpis which aggregates an unowned global table.
interface AccountKpis {
  channels_connected: number
  conversations_total: number
  messages_total: number
  messages_ai: number
  ai_actions_total: number
  last_action_at: string | null
}

const FALLBACK_KPIS: KpiTile[] = [
  { key: 'active', label: 'Leads Activos', value: '—', delta: { value: 0, up: true }, accent: 'emerald' },
  { key: 'leads', label: 'Leads Totales', value: '—', delta: { value: 0, up: true }, accent: 'cobalt' },
  { key: 'conversion', label: 'Tasa de Conversión', value: '—', delta: { value: 0, up: true }, accent: 'cobalt' },
  { key: 'pipeline', label: 'Pipeline Activo', value: '—', delta: { value: 0, up: false }, accent: 'amber' },
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

const PIPELINE_STAGE_META: Record<string, { label: string; detail: string; accent: string }> = {
  new:       { label: 'Ingesta de señales', detail: 'Leads nuevos sin contactar aún', accent: T.cobalt },
  contacted: { label: 'Calificación',        detail: 'Primer contacto realizado',      accent: T.cobalt },
  engaged:   { label: 'Razonamiento',        detail: 'Lead respondió · en conversación', accent: T.amber },
  qualified: { label: 'Ejecución',           detail: 'Calificado · propuesta en curso', accent: T.amber },
  won:       { label: 'Cierre & fidelización', detail: 'Deal ganado',                  accent: T.emerald },
}
const STAGE_ORDER = ['new', 'contacted', 'engaged', 'qualified', 'won']

const AIProcessingPanel = (): React.JSX.Element => {
  const [stages, setStages] = useState<PipelineStage[]>([])

  useEffect(() => {
    let alive = true
    const fetchPipeline = async (): Promise<void> => {
      try {
        const r = await fetch(`${BRAIN_BACKEND_URL}/api/v1/brain/pipeline-summary`, { cache: 'no-store' })
        if (!r.ok) throw new Error(String(r.status))
        const d = await r.json() as { by_status: Array<{ status: string; count: number; value: number }> }
        if (!alive) return
        const byStatus = new Map(d.by_status.map(s => [s.status, s.count]))
        const total = d.by_status.reduce((sum, s) => sum + s.count, 0) || 1
        setStages(STAGE_ORDER.map(key => {
          const count = byStatus.get(key) || 0
          const meta = PIPELINE_STAGE_META[key]
          return {
            key, label: meta.label, detail: meta.detail,
            active: count, throughput: Math.round((count / total) * 100), accent: meta.accent,
          }
        }))
      } catch {
        // backend unreachable — leave stages empty rather than fabricate load %
      }
    }
    void fetchPipeline()
    const id = window.setInterval(() => { void fetchPipeline() }, 20000)
    return () => { alive = false; window.clearInterval(id) }
  }, [])

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

      {stages.length === 0 ? (
        <div style={{ padding: '24px 0', textAlign: 'center', fontSize: 12, color: T.text3, fontFamily: T.mono }}>
          Sin actividad de pipeline registrada aún
        </div>
      ) : (
      <div style={{
        display: 'grid', gridTemplateColumns: `repeat(${stages.length}, 1fr)`,
        gap: 12, marginTop: 18, alignItems: 'stretch',
      }}>
        {stages.map((s, i) => (
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
                    <div style={{ width: `${s.throughput}%`, height: '100%', borderRadius: 5, background: s.accent, transition: 'width 1.4s ease' }} />
                  </div>
                  <div style={{ marginTop: 5, fontSize: 10, color: T.text3, fontFamily: T.mono, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    {s.throughput}% del pipeline
                  </div>
                </div>
              </div>
              {i < stages.length - 1 && (
                <ArrowRight
                  size={14}
                  style={{ position: 'absolute', right: -13, top: '50%', transform: 'translateY(-50%)', color: T.text3, zIndex: 1 }}
                />
              )}
            </div>
        ))}
      </div>
      )}
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

// Shared by the sidebar nav and every other "jump to section" action in this
// file. Used to call scrollIntoView({ behavior: 'smooth', ... }) -- with the
// global CSS `html { scroll-behavior: smooth }` this app already sets, that
// is a redundant, doubly-smooth request, and it is genuinely fragile: any
// layout shift or re-render while the animation is in flight (this page
// polls KPIs/notifications continuously) makes some browsers silently
// abandon an in-progress smooth scroll rather than resume it, so the button
// looked like it had stopped working entirely -- not just "less smooth".
// `behavior: 'instant'` always overrides the CSS-level smooth setting per
// spec, trading the animation for a scroll that reliably happens every time.
const scrollToSection = (id: string): void => {
  document.getElementById(id)?.scrollIntoView({ behavior: 'instant', block: 'start' })
}

const SideToolbar = (): React.JSX.Element => {
  const go = scrollToSection
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
  // Fetch real data from backend
  const { leads = [], loading: leadsLoading } = useLeads()

  // Real audit log — powers Approvals Center, Handoff Log, Agent Audit Log sidebar
  const [auditLogs, setAuditLogs] = useState<RawAuditLog[]>([])
  const [pendingApprovals, setPendingApprovals] = useState<RawAuditLog[]>([])
  useEffect(() => {
    let alive = true
    const fetchAudit = async (): Promise<void> => {
      try {
        const [logsRes, pendingRes] = await Promise.all([
          fetch(`${BRAIN_BACKEND_URL}/api/v1/brain/handoff-log?limit=30`, { cache: 'no-store' }),
          fetch(`${BRAIN_BACKEND_URL}/api/v1/brain/audit-log/pending`, { cache: 'no-store' }),
        ])
        if (!alive) return
        if (logsRes.ok) setAuditLogs((await logsRes.json()).logs ?? [])
        if (pendingRes.ok) setPendingApprovals((await pendingRes.json()).logs ?? [])
      } catch {
        // backend unreachable — keep empty, do not fabricate
      }
    }
    void fetchAudit()
    const id = window.setInterval(() => { void fetchAudit() }, 20000)
    return () => { alive = false; window.clearInterval(id) }
  }, [])

  const handoffEvents = useMemo(() => auditLogs.map(mapToHandoffEvent), [auditLogs])
  const approvalRequests = useMemo(() => pendingApprovals.map(mapToApprovalRequest), [pendingApprovals])

  const handleApproveAction = useCallback(async (id: string): Promise<void> => {
    await fetch(`${BRAIN_BACKEND_URL}/api/v1/brain/audit-log/${id}/approve`, { method: 'POST' })
    setPendingApprovals(p => p.filter(l => l.id !== id))
  }, [])

  const handleRejectAction = useCallback(async (id: string, reason?: string): Promise<void> => {
    await fetch(`${BRAIN_BACKEND_URL}/api/v1/brain/audit-log/${id}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason }),
    })
    setPendingApprovals(p => p.filter(l => l.id !== id))
  }, [])

  // Convert leads to prospects for table display
  const prospects: Prospect[] = useMemo(() =>
    leads.map((lead, i) => ({
      id: `LEAD-${lead.id || i}`,
      contact: lead.name || 'Unknown',
      company: lead.company || 'N/A',
      industry: lead.industry || 'N/A',
      stage: (lead.status?.split('_')[0]?.toLowerCase() === 'contacted' ? 'Outreach' :
              lead.status?.split('_')[0]?.toLowerCase() === 'engaged' ? 'Calificando' :
              lead.status?.split('_')[0]?.toLowerCase() === 'qualified' ? 'Negociando' :
              lead.status?.split('_')[0]?.toLowerCase() === 'won' ? 'Ganado' :
              'Prospectando') as AIStage,
      probability: Math.min(96, Math.max(6, lead.score || 20)),
      score: lead.score || 0,
      value: lead.estimated_value || 50000,
      lastAction: 'hace poco',
    })),
    [leads],
  )

  const [query, setQuery] = useState('')
  const [stageFilter, setStageFilter] = useState<AIStage | 'all'>('all')
  const [sortKey, setSortKey] = useState<SortKey>('score')
  const [page, setPage] = useState(0)

  // ── header controls (search / voz / Computer Use) — portados del MissionControlBar ──
  const [handsFree, setHandsFree] = useState(false)
  const [cuaMode, setCuaMode] = useState<CuaMode>('off')
  const [cuaLauncherOpen, setCuaLauncherOpen] = useState(false)
  const [user, setUser] = useState<UserProfile | null>(null)
  // A cached display profile with no real backend token behind it (token
  // cleared/expired elsewhere) must never render as "logged in" -- see
  // isAuthenticated() in MissionControlBar.tsx.
  useEffect(() => { if (isAuthenticated()) { const u = loadUser(); if (u) setUser(u) } }, [])

  // ── vista del cerebro: flujos (n8n) vs overview (grafo apagado) ──
  const [neuralView, setNeuralView] = useState<'flows' | 'overview'>('flows')
  // Real ON/OFF count for the Dashboard-level summary card -- the toggle
  // grid itself (BrainInteractionMap) lives 2 clicks deep (Cerebro Neuronal
  // -> Vista general), which is why it went unnoticed even after being
  // built: this surfaces the same real state on the very first screen.
  const [disabledCount, setDisabledCount] = useState(0)
  useEffect(() => {
    const sync = (): void => setDisabledCount(getDisabledCapabilities().size)
    sync()
    return onCapabilitiesChanged(sync)
  }, [])

  // Real, backend-truthful setup readiness -- replaces the old gate, which
  // read a completely separate localStorage-only "business profile"
  // (lib/business-profile.ts) that never touched this account's real
  // Business/BusinessContext/Domain rows at all. A logged-in user now sees
  // "AGENTE ACTIVO" / no setup banner only once all four real things exist:
  // an account, a claimed subdomain, the questionnaire fully answered, and
  // at least one channel declared. Anonymous visitors (the public demo)
  // keep the old localStorage-profile behavior untouched below.
  const [accountSetup, setAccountSetup] = useState<AccountSetupSummary | null>(null)
  const refetchAccountSetup = useCallback((): void => {
    const token = getToken()
    if (!token) { setAccountSetup(null); return }
    fetch(`${BRAIN_BACKEND_URL}/api/v1/ai-activity/summary`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => (r.ok ? r.json() : null))
      .then(data => { if (data) setAccountSetup(data) })
      .catch(() => { /* stay as-is -> never a false "active" claim */ })
  }, [])
  useEffect(() => { refetchAccountSetup() }, [user, refetchAccountSetup])

  // Logged-in users get the REAL, backend-synced questionnaire; anonymous
  // demo visitors keep the local fake one (BusinessProfileWizard) below.
  const isLoggedIn = !!user
  const [contextWizardId, setContextWizardId] = useState<string | null>(null)
  const [contextWizardLoading, setContextWizardLoading] = useState(false)
  const openRealContextWizard = useCallback(async (): Promise<void> => {
    setContextWizardLoading(true)
    try {
      const ctx = await businessContextApi.getContext()
      setContextWizardId(ctx.id)
    } catch {
      /* no backend / not logged in -> wizard just won't open */
    } finally {
      setContextWizardLoading(false)
    }
  }, [])
  // ── Client-only timestamp (fixes hydration mismatch) ──
  const [currentTime, setCurrentTime] = useState('')
  useEffect(() => {
    setCurrentTime(nowTs())
    const interval = setInterval(() => setCurrentTime(nowTs()), 1000)
    return () => clearInterval(interval)
  }, [])
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
  // Which editor "Completar / Editar negocio" should open:
  //  - real questionnaire (backend BusinessContext) while the account's real
  //    setup is still missing -- that's what actually gates the AI;
  //  - the local links wizard once setup is done, since per-platform URLs
  //    (ML/Amazon/IG/web) only exist there and are what Computer Use needs.
  const openBusinessEditor = useCallback((): void => {
    if (isLoggedIn && !accountSetup?.setup.setup_complete) { void openRealContextWizard(); return }
    setProfileOpen(true)
  }, [isLoggedIn, accountSetup, openRealContextWizard])
  // Real, honest readiness gate: a logged-in account is only "ready" per the
  // backend's setup block (real Business + subdomain + questionnaire +
  // declared channel) -- the local fake profile is never consulted for
  // logged-in users. Anonymous demo visitors keep the old local-profile gate.
  const setupComplete = isLoggedIn ? !!accountSetup?.setup.setup_complete : profileDone
  // Exactly what this account is still missing, straight from the backend --
  // no invented steps, no "casi listo" when nothing has been answered.
  const missingSetupParts = useMemo((): string[] => {
    const s = accountSetup?.setup
    if (!s) return []
    const parts: string[] = []
    if (!s.has_subdomain) parts.push('tu subdominio')
    if (!s.questionnaire_complete) parts.push('el cuestionario (qué vendés, modelo de venta, público, propuesta de valor)')
    else if (!s.has_channel_declared) parts.push('declarar un canal (redes, web, MercadoLibre/Amazon)')
    return parts
  }, [accountSetup])

  // Computer Use acciona sobre flujos planificados (por cuenta o de rescate).
  const [plannedFlows, setPlannedFlows] = useState<PlannedFlow[]>([])
  const executePlan = useCallback((flows: PlannedFlow[]): void => {
    setPlannedFlows(flows)
    setCuaMode('supervised')
    setNeuralView('flows')
    scrollToSection('sec-neural')
    // Ejecución real best-effort: una sesión CU por flujo (si hay backend+key).
    const disabled = [...getDisabledCapabilities()]
    // Attaching the real Bearer token (when logged in) is what lets the
    // backend persist this dispatch to ai_action_logs for this account --
    // an anonymous/demo visitor with no token behaves exactly as before.
    const authHeaders: Record<string, string> = { 'Content-Type': 'application/json' }
    const token = getToken()
    if (token) authHeaders.Authorization = `Bearer ${token}`
    flows.forEach(f => {
      void fetch('/api/v1/brain/cua/dispatch', {
        method: 'POST', headers: authHeaders,
        body: JSON.stringify({ instruction: f.instruction ?? f.name, mode: 'supervised', disabled }),
      }).catch(() => { /* sin backend → queda como plan visible */ })
    })
  }, [])
  const planFromToolkit = useCallback((): void => { executePlan(planAccountFlows(loadProfile())) }, [executePlan])

  const dispatchCua = useCallback(async (): Promise<void> => {
    const instruction = cuaPrompt.trim()
    if (!instruction || cuaMode === 'off') return
    setCuaSending(true); setCuaMsg('')
    try {
      const dispatchHeaders: Record<string, string> = { 'Content-Type': 'application/json' }
      const dispatchToken = getToken()
      if (dispatchToken) dispatchHeaders.Authorization = `Bearer ${dispatchToken}`
      const r = await fetch('/api/v1/brain/cua/dispatch', {
        method: 'POST', headers: dispatchHeaders,
        body: JSON.stringify({
          instruction, mode: cuaMode === 'auto' ? 'auto' : 'supervised',
          disabled: [...getDisabledCapabilities()],
        }),
      })
      if (!r.ok) throw new Error(String(r.status))
      const d = await r.json()
      if (d.ok === false) {
        setCuaMsg(`Los agentes disponibles para esto están desactivados en el mapa (${(d.skipped_disabled_agents ?? []).join(', ')}). Activalos para continuar.`)
        return
      }
      const skippedNote = d.skipped_disabled_agents?.length
        ? ` (saltó: ${d.skipped_disabled_agents.join(', ')} — desactivados)`
        : ''
      const base = `Flujo creado: ${d.flow?.name ?? 'OK'}${skippedNote}.`
      if (d.can_execute) {
        setCuaMsg(`${base} Ejecución real disponible — abriendo sesión Computer Use.`)
        setCuaLauncherOpen(true)
      } else {
        setCuaMsg(`${base} Plan + telemetría (ver en Flujos). Para ejecutar de verdad falta API key del cerebro.`)
      }
      setCuaPrompt(''); setNeuralView('flows')
      scrollToSection('sec-neural')
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
    scrollToSection(componentId)
  }, [])

  // Resuelve y EJECUTA una orden de voz; retorna la respuesta hablada.
  const handleVoiceCommand = useCallback((text: string): string => {
    const t = text.toLowerCase()
    const scrollTo = (id: string, label: string): string => {
      scrollToSection(id)
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

  // ── audit log stream (real — derived from computer-use audit log) ──
  const [logs, setLogs] = useState<LogLine[]>([])
  const logBody = useRef<HTMLDivElement>(null)

  // ── live brain metadata + KPIs (real, computed from the leads table) ──
  const [brain, setBrain] = useState<BrainOverview | null>(null)
  const [kpis, setKpis] = useState<KpiTile[]>(FALLBACK_KPIS)
  const prevKpiRaw = useRef<{ active: number; leads: number; conversion: number; pipeline: number } | null>(null)

  useEffect(() => {
    let alive = true
    const fetchKpis = async (): Promise<void> => {
      try {
        const r = await fetch(`${BRAIN_BACKEND_URL}/api/v1/brain/kpis`, { cache: 'no-store' })
        if (!r.ok) throw new Error(String(r.status))
        const d = await r.json() as {
          total_leads: number; won_leads: number; active_leads: number
          conversion_rate: number; pipeline_value: number
        }
        if (!alive) return

        const raw = {
          active: d.active_leads, leads: d.total_leads,
          conversion: d.conversion_rate, pipeline: d.pipeline_value,
        }
        const prev = prevKpiRaw.current
        const pct = (now: number, before: number | undefined): { value: number; up: boolean } => {
          if (before === undefined || before === 0) return { value: 0, up: true }
          const change = ((now - before) / before) * 100
          return { value: Math.abs(Math.round(change * 10) / 10), up: change >= 0 }
        }

        setKpis([
          { key: 'active', label: 'Leads Activos', value: raw.active.toLocaleString(), delta: pct(raw.active, prev?.active), accent: 'emerald' },
          { key: 'leads', label: 'Leads Totales', value: raw.leads.toLocaleString(), delta: pct(raw.leads, prev?.leads), accent: 'cobalt' },
          { key: 'conversion', label: 'Tasa de Conversión', value: `${raw.conversion.toFixed(1)}%`, delta: pct(raw.conversion, prev?.conversion), accent: 'cobalt' },
          { key: 'pipeline', label: 'Pipeline Activo', value: `$${(raw.pipeline / 1000).toFixed(1)}K`, delta: pct(raw.pipeline, prev?.pipeline), accent: 'amber' },
        ])
        prevKpiRaw.current = raw
        setBrain({
          counts: { agents: 5, skills: 12, automations: 8, total: 25 },
          health: d.total_leads > 0 ? Math.min(0.99, 0.6 + d.conversion_rate / 200) : 0,
        })
      } catch {
        // backend unreachable — keep last known KPIs rather than fabricate
      }
    }
    void fetchKpis()
    const id = window.setInterval(() => { void fetchKpis() }, 20000)
    return () => { alive = false; window.clearInterval(id) }
  }, [])

  // ── KPIs REALES de la cuenta ──
  // GET /brain/kpis (arriba) agrega la tabla `leads` entera, que no tiene
  // columna de dueño: sus números no son de nadie en particular, así que
  // mostrárselos a un usuario logueado como "tus leads / tu pipeline" es
  // justamente inventar actividad. Para una cuenta real usamos
  // /ai-activity/account-kpis, que sí está scopeado por Business.user_id y
  // devuelve ceros honestos cuando todavía no pasó nada.
  const [accountKpis, setAccountKpis] = useState<AccountKpis | null>(null)
  useEffect(() => {
    const token = getToken()
    if (!token) { setAccountKpis(null); return }
    let alive = true
    const fetchAccountKpis = async (): Promise<void> => {
      try {
        const r = await fetch(`${BRAIN_BACKEND_URL}/api/v1/ai-activity/account-kpis`, {
          headers: { Authorization: `Bearer ${token}` }, cache: 'no-store',
        })
        if (!r.ok) return
        const d = await r.json() as AccountKpis
        if (alive) setAccountKpis(d)
      } catch {
        /* sin backend → se mantiene el último valor real conocido */
      }
    }
    void fetchAccountKpis()
    const id = window.setInterval(() => { void fetchAccountKpis() }, 20000)
    return () => { alive = false; window.clearInterval(id) }
  }, [user])

  // Cuenta real → métricas de la cuenta. Visitante anónimo → demo pública
  // (los KPIs globales de siempre, ya rotulados como demo en la sección).
  const displayedKpis = useMemo((): KpiTile[] => {
    if (!isLoggedIn) return kpis
    if (!accountKpis) return FALLBACK_KPIS.map(k => ({ ...k, value: '—' }))
    const flat = { value: 0, up: true }
    return [
      { key: 'channels', label: 'Canales conectados', value: accountKpis.channels_connected.toLocaleString(), delta: flat, accent: 'emerald' },
      { key: 'conversations', label: 'Conversaciones', value: accountKpis.conversations_total.toLocaleString(), delta: flat, accent: 'cobalt' },
      { key: 'ai_replies', label: 'Respuestas de la IA', value: accountKpis.messages_ai.toLocaleString(), delta: flat, accent: 'emerald' },
      { key: 'ai_actions', label: 'Acciones IA registradas', value: accountKpis.ai_actions_total.toLocaleString(), delta: flat, accent: 'cobalt' },
    ]
  }, [isLoggedIn, accountKpis, kpis])

  // Map real audit log entries (already polled every 20s above) into log lines
  useEffect(() => {
    const toLevel = (l: RawAuditLog): LogLevel =>
      l.status === 'success' ? 'win' : l.status === 'failed' ? 'action' : l.strategy_name ? 'think' : 'data'
    const mapped: LogLine[] = auditLogs.slice(0, 40).map((l, i) => ({
      id: i,
      ts: l.created_at ? new Date(l.created_at).toLocaleTimeString('es-AR', { hour12: false }) : nowTs(),
      level: toLevel(l),
      msg: l.output_data || l.input_data || `${l.action_type || 'actividad'} · ${l.agent_name || l.platform || 'agente'}`,
    }))
    setLogs(mapped)
  }, [auditLogs])

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

      {/* ── Cuestionario de negocio (modal) ── anónimo: fake local; logueado: real backend */}
      <BusinessProfileWizard open={profileOpen} onClose={() => setProfileOpen(false)} onSaved={(p) => setProfile(p)} />
      {contextWizardId && (
        <RealBusinessContextWizard
          contextId={contextWizardId}
          onComplete={() => { setContextWizardId(null); refetchAccountSetup() }}
        />
      )}

      {/* ── Tool Studio (detalle + lanzar herramienta) ── */}
      <ToolStudio toolId={openToolId} profile={profile} onClose={() => setOpenToolId(null)} onLaunch={(f) => executePlan([f])}
        onAddToPlan={(f) => { setPlannedFlows(prev => [...prev, f]); setNeuralView('flows'); scrollToSection('sec-neural') }} />

      {/* ── Banner obligatorio si el setup no está completo -- logueado: gate
          real (cuenta + subdominio + cuestionario + canal declarado);
          anónimo (demo público): gate local de siempre, sin cambios. ── */}
      {!setupComplete && (
        <div style={{
          position: 'sticky', top: 56, zIndex: 19, display: 'flex', alignItems: 'center', gap: 12,
          padding: '10px 28px', background: `${T.amber}14`, borderBottom: `1px solid ${T.amber}40`,
        }}>
          <Store size={16} style={{ color: T.amber }} />
          <span style={{ fontSize: 13, color: T.text }}>
            {isLoggedIn
              ? `Completá tu negocio para que SellIA venda por vos — falta ${missingSetupParts.join(' · ') || 'terminar la configuración'}.`
              : 'Completá tu negocio (qué vendés + tus links de venta/anuncios/redes) para que SellIA venda por vos.'}
          </span>
          <span style={{ flex: 1 }} />
          {isLoggedIn && !accountSetup?.setup.has_subdomain && (
            <a href="/sellia-onboarding" style={{
              padding: '7px 14px', borderRadius: 8, border: `1px solid ${T.amber}`, color: T.amber,
              fontWeight: 700, fontSize: 12, textDecoration: 'none',
            }}>Reclamar subdominio</a>
          )}
          <button
            type="button"
            disabled={contextWizardLoading}
            onClick={() => { if (isLoggedIn) { void openRealContextWizard() } else { setProfileOpen(true) } }}
            style={{
              padding: '7px 14px', borderRadius: 8, border: 'none', background: T.amber, color: '#1a1205',
              fontWeight: 700, fontSize: 12, cursor: contextWizardLoading ? 'default' : 'pointer',
              opacity: contextWizardLoading ? 0.6 : 1,
            }}>{contextWizardLoading ? 'Abriendo…' : 'Completar'}</button>
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
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: '-0.01em' }}>SellIA · Command Center (LIVE)</div>
            <div style={{ fontSize: 11, color: T.text2, fontFamily: T.mono }}>Súper Agente de Ventas B2B</div>
          </div>
          <a href="/dashboard/phase12" style={{
            display: 'inline-flex', alignItems: 'center', gap: 6, padding: '6px 12px',
            borderRadius: 8, border: `1px solid ${T.cobalt}33`, background: `${T.cobalt}14`,
            fontSize: 12, fontWeight: 600, color: T.cobalt, textDecoration: 'none',
            transition: 'background .14s, border-color .14s',
            cursor: 'pointer',
          }} onMouseEnter={e => {
            e.currentTarget.style.background = `${T.cobalt}22`;
            e.currentTarget.style.borderColor = `${T.cobalt}55`;
          }} onMouseLeave={e => {
            e.currentTarget.style.background = `${T.cobalt}14`;
            e.currentTarget.style.borderColor = `${T.cobalt}33`;
          }}>
            <TrendingUp size={14} />
            {t('phases.seo_foundation')}
          </a>
          <a href="/dashboard/phase3" style={{
            display: 'inline-flex', alignItems: 'center', gap: 6, padding: '6px 12px',
            borderRadius: 8, border: `1px solid rgba(168,85,247,0.33)`, background: `rgba(168,85,247,0.14)`,
            fontSize: 12, fontWeight: 600, color: '#a855f7', textDecoration: 'none',
            transition: 'background .14s, border-color .14s',
            cursor: 'pointer',
          }} onMouseEnter={e => {
            e.currentTarget.style.background = `rgba(168,85,247,0.22)`;
            e.currentTarget.style.borderColor = `rgba(168,85,247,0.55)`;
          }} onMouseLeave={e => {
            e.currentTarget.style.background = `rgba(168,85,247,0.14)`;
            e.currentTarget.style.borderColor = `rgba(168,85,247,0.33)`;
          }}>
            <Users size={14} />
            Phase 3 · Authority Building
          </a>
          <a href="/dashboard/phase33" style={{
            display: 'inline-flex', alignItems: 'center', gap: 6, padding: '6px 12px',
            borderRadius: 8, border: `1px solid ${T.emerald}33`, background: `${T.emerald}14`,
            fontSize: 12, fontWeight: 600, color: T.emerald, textDecoration: 'none',
            transition: 'background .14s, border-color .14s',
            cursor: 'pointer',
          }} onMouseEnter={e => {
            e.currentTarget.style.background = `${T.emerald}22`;
            e.currentTarget.style.borderColor = `${T.emerald}55`;
          }} onMouseLeave={e => {
            e.currentTarget.style.background = `${T.emerald}14`;
            e.currentTarget.style.borderColor = `${T.emerald}33`;
          }}>
            <Store size={14} />
            Phase 33 · Vendedor Multi-Plataforma
          </a>
          <a href="/dashboard/conversaciones" style={{
            display: 'inline-flex', alignItems: 'center', gap: 6, padding: '6px 12px',
            borderRadius: 8, border: `1px solid rgba(16,185,129,0.4)`, background: `rgba(16,185,129,0.16)`,
            fontSize: 12, fontWeight: 700, color: '#10b981', textDecoration: 'none',
            transition: 'background .14s, border-color .14s',
            cursor: 'pointer',
          }} onMouseEnter={e => {
            e.currentTarget.style.background = `rgba(16,185,129,0.26)`;
            e.currentTarget.style.borderColor = `rgba(16,185,129,0.6)`;
          }} onMouseLeave={e => {
            e.currentTarget.style.background = `rgba(16,185,129,0.16)`;
            e.currentTarget.style.borderColor = `rgba(16,185,129,0.4)`;
          }} title="Ver conversaciones reales de WhatsApp, Instagram, MercadoLibre y más — con prueba de qué respondió la IA">
            <Bot size={14} />
            Conversaciones IA en vivo
          </a>
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
            {/* "salud" sale de la tabla global de leads, que no pertenece a
                ninguna cuenta: para un usuario logueado sería un número
                inventado sobre su negocio, así que solo se muestra en la
                demo pública. */}
            {!isLoggedIn && (
              <>
                <span style={{ color: T.text3 }}>·</span>
                <span style={{ color: T.emerald }}>salud {(brain.health * 100).toFixed(0)}%</span>
              </>
            )}
          </span>
        )}
        {/* Real, honest state -- was a static, unconditional "AGENTE ACTIVO"
            regardless of whether the account had ever finished setup. */}
        <span style={{
          display: 'inline-flex', alignItems: 'center', gap: 7, padding: '6px 12px',
          borderRadius: 8, border: `1px solid ${(setupComplete ? T.emerald : T.amber)}33`,
          background: `${setupComplete ? T.emerald : T.amber}14`,
          fontSize: 12, fontWeight: 600, color: setupComplete ? T.emerald : T.amber, fontFamily: T.mono,
        }}>
          <span style={{ width: 7, height: 7, borderRadius: '50%', background: setupComplete ? T.emerald : T.amber, animation: 'ecc-pulse 2s ease-in-out infinite' }} />
          {setupComplete ? 'AGENTE ACTIVO' : 'CONFIGURACIÓN PENDIENTE'}
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

      {/* ── CONTROL ON/OFF: resumen real + acceso directo -- el grid de
          toggles (BrainInteractionMap) vive 2 clicks adentro (Cerebro
          Neuronal → Vista general), así que estaba construido pero nadie
          lo encontraba. Esto lo pone en la primera pantalla, con el
          conteo real. ── */}
      {showKpis && brain && (
      <section style={{ padding: '20px 28px 0' }}>
        <button
          onClick={() => { setView('neural'); setNeuralView('overview') }}
          style={{
            width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            gap: 16, padding: '14px 18px', borderRadius: 12, cursor: 'pointer', textAlign: 'left',
            background: disabledCount > 0 ? `${T.amber}0F` : `${T.emerald}0F`,
            border: `1px solid ${disabledCount > 0 ? T.amber : T.emerald}40`,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{
              width: 34, height: 34, borderRadius: 9, display: 'grid', placeItems: 'center',
              background: `${disabledCount > 0 ? T.amber : T.emerald}1F`,
              color: disabledCount > 0 ? T.amber : T.emerald,
            }}>
              <Power size={17} />
            </span>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: T.text }}>
                {brain.counts.total - disabledCount} de {brain.counts.total} {setupComplete ? 'activados' : 'habilitados'}
                {disabledCount > 0 && <span style={{ color: T.amber }}> · {disabledCount} desactivados</span>}
              </div>
              {/* "Activado" acá significa "no apagado en el mapa". Con el
                  setup real incompleto nada de esto corre todavía, así que
                  decir "activados" sería anunciar automatizaciones que no
                  existen. */}
              <div style={{ fontSize: 12, color: setupComplete ? T.text2 : T.amber, marginTop: 2 }}>
                {setupComplete
                  ? 'Agentes, skills, automatizaciones y plataformas · encendé o apagá cada uno acá'
                  : 'Quedan habilitados pero no corren hasta que completes el setup de tu cuenta'}
              </div>
            </div>
          </div>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 12, fontWeight: 700, color: T.cobalt, flexShrink: 0 }}>
            Ver y controlar <ChevronRight size={14} />
          </span>
        </button>
      </section>
      )}

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
        <BusinessToolkit profile={profile} setupDone={setupComplete} onEdit={openBusinessEditor} onPlan={planFromToolkit} onOpenTool={setOpenToolId}
          onPlanComplete={(ids) => executePlan(buildToolPlan(loadProfile(), ids))} />
      </section>
      )}

      {/* ── MODO RESCATE: sin clientes → estrategia de adquisición ── */}
      {showKpis && (
      <section id="sec-rescue" style={{ padding: '20px 28px 0' }}>
        <RescueMode profile={profile} setupDone={setupComplete} onEdit={openBusinessEditor} onRescue={executePlan} />
      </section>
      )}

      {/* ── KPI ROW ── (solo en Dashboard) */}
      {showKpis && (
      <section id="sec-kpis" style={{ padding: '24px 28px 0' }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10,
          fontSize: 11, fontFamily: T.mono, letterSpacing: '0.04em',
          color: isLoggedIn ? T.text2 : T.amber, textTransform: 'uppercase',
        }}>
          {isLoggedIn
            ? 'Datos reales de tu cuenta'
            : 'Demo pública · totales de la plataforma, no de una cuenta'}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
          {displayedKpis.map(k => (
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
        </div>
        {isLoggedIn && accountKpis && accountKpis.conversations_total === 0 && (
          <div style={{ marginTop: 10, fontSize: 12, color: T.text2 }}>
            Todavía no hay conversaciones reales en esta cuenta. Los números se llenan solos
            cuando conectes un canal (WhatsApp, Instagram, MercadoLibre, Amazon…) y entren mensajes.
          </div>
        )}
      </section>
      )}

      {/* ── ESCUADRONES IA · telemetría por departamento ── */}
      {showSquads && (
      <section id="sec-squads" style={{ padding: '20px 28px 0' }}>
        {isLoggedIn && <DemoDataNotice what="telemetría de escuadrones" />}
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
          {isLoggedIn && <DemoDataNotice what="prospectos" />}
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
              <div style={{ fontSize: 11, color: isLoggedIn ? T.amber : T.text2, fontFamily: T.mono }}>
                {isLoggedIn ? 'DEMO · razonamiento de la plataforma, no de tu cuenta' : 'Razonamiento en tiempo real'}
              </div>
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
              <span style={{ color: T.text3 }}>{currentTime || '—'}</span>
              <span style={{ width: 7, height: 14, background: T.cobalt, display: 'inline-block', animation: 'ecc-pulse 1s steps(2) infinite' }} />
            </div>
          </div>
        </aside>
        )}
      </main>
      )}

      {/* ── HANDOFF LOG + APPROVALS — vista combinada o por separado ── */}
      {(showHandoff || showApprovals) && (
      <section id="sec-collab" style={{ padding: '12px 28px 8px' }}>
        {isLoggedIn && <DemoDataNotice what="handoffs y aprobaciones" />}
        <div style={{
          display: 'grid',
          gridTemplateColumns: view === 'handoff'   ? '1fr'
                            : view === 'approvals' ? '1fr'
                            : '1fr 1fr',
          gap: 16, alignItems: 'start',
        }}>
        {showHandoff   && <HandoffLog events={handoffEvents} simulateLive={false} />}
        {showApprovals && (
          <ApprovalsCenter
            requests={approvalRequests}
            demoMode={false}
            onApprove={handleApproveAction}
            onReject={handleRejectAction}
          />
        )}
        </div>
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
                {v === 'flows' ? 'Flujos en vivo' : 'Activar / Desactivar'}
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

