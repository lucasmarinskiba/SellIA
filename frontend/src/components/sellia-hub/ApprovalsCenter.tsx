'use client'

/**
 * APPROVALS CENTER — Human-in-the-Loop · Corporate minimalist
 *
 * Bandeja de decisiones críticas. Tarjetas colapsadas/desplegables.
 * Estilo enterprise: bg-slate-900 base · bg-slate-800/50 cards · border-slate-700/50.
 *
 * Backend wiring (props):
 *   - requests: ApprovalRequest[]      (de tu API/SSE)
 *   - onApprove(id): Promise<void>
 *   - onReject(id, reason?): Promise<void>
 */

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Shield, ShieldAlert, Check, X, Clock, ChevronDown, ChevronUp,
  AlertTriangle, Megaphone, Mail, Headphones, MonitorCheck, Radio,
  DollarSign, Sparkles, Inbox,
} from 'lucide-react'

// ── Design tokens (Enterprise Dark Mode) ───────────────────────────────────────
const T = {
  bgBase:      '#0F172A',   // slate-900
  bgCard:      'rgba(30, 41, 59, 0.50)',     // slate-800/50
  bgCardHov:   'rgba(30, 41, 59, 0.75)',
  bgSubtle:    'rgba(15, 23, 42, 0.60)',
  border:      'rgba(51, 65, 85, 0.50)',     // slate-700/50
  borderStr:   'rgba(71, 85, 105, 0.65)',    // slate-600/65
  textPrim:    '#F1F5F9',                    // slate-100
  textSec:     '#CBD5E1',                    // slate-300
  textMuted:   '#94A3B8',                    // slate-400
  textFaint:   '#64748B',                    // slate-500
  emerald:     '#10B981',
  emeraldDk:   '#059669',
  cyan:        '#06B6D4',
  amber:       '#F59E0B',
  violet:      '#8B5CF6',
  rose:        '#EF4444',
  mono:        "'JetBrains Mono', ui-monospace, monospace",
  sans:        "'Inter', ui-sans-serif, system-ui, sans-serif",
} as const

// ── Types ──────────────────────────────────────────────────────────────────────
type AgentDept = 'sdr' | 'ads' | 'pr' | 'cs' | 'cua'
type Severity  = 'low' | 'medium' | 'high' | 'critical'
type ActionKind = 'budget_increase' | 'discount' | 'mass_send' | 'data_export' | 'integration' | 'price_change' | 'autonomous_purchase'

export interface ApprovalRequest {
  id:           string
  createdAt:    string
  dept:         AgentDept
  kind:         ActionKind
  title:        string
  description:  string
  rationale:    string
  severity:     Severity
  expiresAt?:   string
  delta?:       { label: string; before: string; after: string }
  context?:     Record<string, string | number>
}

interface ApprovalsCenterProps {
  requests?:   ApprovalRequest[]
  onApprove?:  (id: string) => Promise<void> | void
  onReject?:   (id: string, reason?: string) => Promise<void> | void
  demoMode?:   boolean
}

// ── Dept config ────────────────────────────────────────────────────────────────
const DEPT_CONFIG: Record<AgentDept, { label: string; short: string; color: string; icon: React.ElementType }> = {
  sdr: { label: 'SDR · Ventas',         short: 'SDR', color: T.cyan,    icon: Mail        },
  ads: { label: 'Growth & Ads',          short: 'ADS', color: T.amber,   icon: Megaphone   },
  pr:  { label: 'PR & Reputación',       short: 'PR',  color: T.violet,  icon: Radio       },
  cs:  { label: 'Customer Success',      short: 'CS',  color: T.emerald, icon: Headphones  },
  cua: { label: 'Computer Use',          short: 'CUA', color: T.rose,    icon: MonitorCheck },
}

const SEV_CONFIG: Record<Severity, { label: string; color: string; weight: number }> = {
  low:      { label: 'BAJO',    color: T.textMuted, weight: 1 },
  medium:   { label: 'MEDIO',   color: T.cyan,      weight: 2 },
  high:     { label: 'ALTO',    color: T.amber,     weight: 3 },
  critical: { label: 'CRÍTICO', color: T.rose,      weight: 4 },
}

const KIND_LABELS: Record<ActionKind, string> = {
  budget_increase:     'Aumento de presupuesto',
  discount:            'Descuento al cliente',
  mass_send:           'Envío masivo',
  data_export:         'Exportación de datos',
  integration:         'Nueva integración / API',
  price_change:        'Cambio de precio',
  autonomous_purchase: 'Compra autónoma',
}

// ── Seed (demo) ────────────────────────────────────────────────────────────────
const NOW = Date.now()
const fmtIso = (offsetSec: number): string => new Date(NOW + offsetSec * 1000).toISOString()

const SEED_REQUESTS: ApprovalRequest[] = [
  {
    id: 'apr_001',
    createdAt: fmtIso(-180),
    dept: 'ads',
    kind: 'budget_increase',
    severity: 'high',
    title: 'Escalar campaña Meta #G-12 +30% budget',
    description: 'Campaña "Pack Premium · Conversiones" alcanzó ROAS 5.1× sostenido por 72hs. Solicito autorización para subir budget diario de $200 → $260.',
    rationale: 'Ventana de oportunidad limitada · audiencia lookalike performando 2.3× sobre baseline · CAC actual $14 (target $25).',
    delta: { label: 'Budget diario', before: '$200', after: '$260' },
    expiresAt: fmtIso(3600 * 4),
    context: { roas: '5.1×', cac: '$14', conversiones_7d: 87 },
  },
  {
    id: 'apr_002',
    createdAt: fmtIso(-95),
    dept: 'sdr',
    kind: 'discount',
    severity: 'medium',
    title: 'Aplicar descuento 20% para cerrar Acme Corp',
    description: 'Lead "Acme Corp" (USD 4.8k) pidió ajuste de precio. Probabilidad de cierre actual 68%. Análisis predice +27pts con descuento del 20%.',
    rationale: 'Cliente estratégico · 3 referidos potenciales en su red · LTV proyectado USD 18k.',
    delta: { label: 'Precio final', before: '$4,800', after: '$3,840' },
    context: { close_prob: '68%', ltv_proj: '$18k' },
  },
  {
    id: 'apr_003',
    createdAt: fmtIso(-32),
    dept: 'cua',
    kind: 'autonomous_purchase',
    severity: 'critical',
    title: 'Reponer stock crítico de SKU "SW-9" en proveedor',
    description: 'Stock SW-9 = 8 unidades · ventas 7d = 42 · ruptura estimada en 36hs. CUA propone OC de 200 unidades al proveedor habitual.',
    rationale: 'Producto top-3 en ventas · ruptura impactaría 12% del revenue mensual.',
    delta: { label: 'Monto compra', before: '—', after: '$4,200' },
    expiresAt: fmtIso(3600 * 2),
    context: { sku: 'SW-9', stock_actual: 8, ventas_7d: 42 },
  },
  {
    id: 'apr_004',
    createdAt: fmtIso(-12),
    dept: 'pr',
    kind: 'mass_send',
    severity: 'low',
    title: 'Publicar caso de éxito en LinkedIn',
    description: 'Cliente Beta SRL aprobó publicar testimonio. Post programado para hoy 18:00 · alcance estimado 12k impresiones.',
    rationale: 'Momentum favorable · sentimiento de marca +0.62 · ventana óptima de publicación.',
    context: { alcance_est: '12k', engagement_est: '4.8%' },
  },
]

const DEMO_NEW_REQUESTS: Omit<ApprovalRequest, 'id' | 'createdAt'>[] = [
  {
    dept: 'ads', kind: 'integration', severity: 'medium',
    title: 'Conectar TikTok Ads API para nueva audiencia',
    description: 'Análisis detectó 38% del público target activo en TikTok. Solicito permiso para conectar TikTok Ads y replicar campaña ganadora.',
    rationale: 'Diversificación de canales · reducción de dependencia de Meta · expansión 18-24 años.',
  },
  {
    dept: 'cs', kind: 'discount', severity: 'medium',
    title: 'Aplicar bonus retención 15% a 12 clientes en churn risk',
    description: 'Modelo detectó 12 cuentas con score de churn >75. Bonus retención propuesto: 15% off próxima renovación + onboarding extra.',
    rationale: 'LTV combinado USD 28k · costo bonus USD 1.2k · ROI 23×.',
  },
]

// ── Helpers ────────────────────────────────────────────────────────────────────
const timeAgo = (iso: string): string => {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (diff < 60)    return `hace ${diff}s`
  if (diff < 3600)  return `hace ${Math.floor(diff / 60)}m`
  if (diff < 86400) return `hace ${Math.floor(diff / 3600)}h`
  return `hace ${Math.floor(diff / 86400)}d`
}

const timeRemaining = (iso: string): string => {
  const diff = Math.floor((new Date(iso).getTime() - Date.now()) / 1000)
  if (diff <= 0)    return 'expirado'
  if (diff < 3600)  return `${Math.floor(diff / 60)}m`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ${Math.floor((diff % 3600) / 60)}m`
  return `${Math.floor(diff / 86400)}d`
}

// ── Filter chip ────────────────────────────────────────────────────────────────
interface FilterChipProps {
  active:   boolean
  label:    string
  count:    number
  color:    string
  onClick:  () => void
}

const FilterChip = ({ active, label, count, color, onClick }: FilterChipProps): React.JSX.Element => (
  <button
    type="button"
    onClick={onClick}
    style={{
      display: 'inline-flex', alignItems: 'center', gap: 10,
      padding: '8px 16px',
      borderRadius: 10,
      cursor: 'pointer',
      fontFamily: T.mono,
      fontSize: 11,
      fontWeight: 700,
      letterSpacing: '0.08em',
      textTransform: 'uppercase',
      border: `1px solid ${active ? color : T.border}`,
      background: active ? `${color}1A` : 'transparent',
      color: active ? color : T.textMuted,
      transition: 'background .18s, border-color .18s, color .18s, transform .12s',
    }}
    onMouseEnter={e => {
      const el = e.currentTarget as HTMLButtonElement
      if (!active) {
        el.style.background = 'rgba(51, 65, 85, 0.25)'
        el.style.borderColor = T.borderStr
        el.style.color = T.textSec
      }
    }}
    onMouseLeave={e => {
      const el = e.currentTarget as HTMLButtonElement
      if (!active) {
        el.style.background = 'transparent'
        el.style.borderColor = T.border
        el.style.color = T.textMuted
      }
    }}
  >
    <span>{label}</span>
    <span style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      minWidth: 22, height: 18, padding: '0 6px',
      borderRadius: 6,
      background: active ? `${color}26` : 'rgba(51, 65, 85, 0.45)',
      color: active ? color : T.textMuted,
      fontSize: 10, fontWeight: 700, fontFamily: T.mono,
      letterSpacing: 0,
    }}>{count}</span>
  </button>
)

// ── Approval card (collapsed/expanded) ─────────────────────────────────────────
interface ApprovalCardProps {
  req:        ApprovalRequest
  expanded:   boolean
  busy:       boolean
  onToggle:   () => void
  onApprove:  () => void
  onReject:   () => void
}

const ApprovalCard = ({ req, expanded, busy, onToggle, onApprove, onReject }: ApprovalCardProps): React.JSX.Element => {
  const dept = DEPT_CONFIG[req.dept]
  const sev  = SEV_CONFIG[req.severity]
  const DeptIcon = dept.icon
  const isCritical = req.severity === 'critical'

  return (
    <motion.article
      layout
      initial={{ opacity: 0, y: 18, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, x: 36, scale: 0.96, transition: { duration: 0.22 } }}
      transition={{ duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
      style={{
        position: 'relative',
        background: T.bgCard,
        border: `1px solid ${T.border}`,
        borderRadius: 12,
        overflow: 'hidden',
        boxShadow: isCritical ? `0 0 28px -12px ${T.rose}50` : 'none',
      }}
    >
      {/* Severity left bar — minimal accent */}
      <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 2, background: sev.color }} />
      {isCritical && (
        <motion.div
          animate={{ opacity: [0.35, 1, 0.35] }}
          transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
          style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 2, background: sev.color }}
        />
      )}

      {/* Collapsed header — always visible */}
      <button
        type="button"
        onClick={onToggle}
        style={{
          width: '100%',
          padding: '18px 20px 18px 22px',
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          textAlign: 'left',
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          fontFamily: T.sans,
        }}
      >
        {/* Dept badge */}
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 7,
          padding: '6px 10px', borderRadius: 8,
          background: `${dept.color}14`,
          border: `1px solid ${dept.color}33`,
          flexShrink: 0,
        }}>
          <DeptIcon size={13} style={{ color: dept.color }} />
          <span style={{ fontSize: 10, fontWeight: 700, color: dept.color, fontFamily: T.mono, letterSpacing: '0.08em' }}>
            {dept.short}
          </span>
        </div>

        {/* Title + meta */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <h3 style={{
            margin: 0,
            fontSize: 14,
            fontWeight: 600,
            color: T.textPrim,
            lineHeight: 1.35,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: expanded ? 'normal' : 'nowrap',
          }}>
            {req.title}
          </h3>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 12,
            marginTop: 5, fontSize: 11, color: T.textFaint, fontFamily: T.mono,
          }}>
            <span>{KIND_LABELS[req.kind]}</span>
            <span style={{ color: T.border }}>·</span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
              <Clock size={10} />{timeAgo(req.createdAt)}
            </span>
            {req.expiresAt && (
              <>
                <span style={{ color: T.border }}>·</span>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, color: T.amber }}>
                  <AlertTriangle size={10} />{timeRemaining(req.expiresAt)} restante
                </span>
              </>
            )}
          </div>
        </div>

        {/* Severity pill */}
        <div style={{
          padding: '5px 11px',
          borderRadius: 6,
          background: `${sev.color}14`,
          border: `1px solid ${sev.color}33`,
          fontSize: 10, fontWeight: 700, fontFamily: T.mono,
          letterSpacing: '0.08em',
          color: sev.color,
          flexShrink: 0,
          display: 'inline-flex', alignItems: 'center', gap: 5,
        }}>
          {isCritical && <ShieldAlert size={11} />}
          {sev.label}
        </div>

        {/* Expand chevron */}
        <motion.span
          animate={{ rotate: expanded ? 180 : 0 }}
          transition={{ duration: 0.24 }}
          style={{
            display: 'grid', placeItems: 'center',
            width: 30, height: 30, borderRadius: 8,
            background: T.bgSubtle,
            border: `1px solid ${T.border}`,
            color: T.textMuted, flexShrink: 0,
          }}
        >
          <ChevronDown size={14} />
        </motion.span>
      </button>

      {/* Expanded body */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            key="body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.32, ease: [0.2, 0.8, 0.2, 1] }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{
              padding: '4px 22px 22px 22px',
              display: 'flex', flexDirection: 'column', gap: 16,
              fontFamily: T.sans,
            }}>
              {/* Divider */}
              <div style={{ height: 1, background: T.border }} />

              {/* Description */}
              <p style={{
                margin: 0,
                fontSize: 13,
                color: T.textSec,
                lineHeight: 1.6,
              }}>
                {req.description}
              </p>

              {/* Delta box */}
              {req.delta && (
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap',
                  padding: '14px 18px',
                  borderRadius: 10,
                  background: T.bgSubtle,
                  border: `1px solid ${T.border}`,
                }}>
                  <div style={{
                    display: 'grid', placeItems: 'center',
                    width: 32, height: 32, borderRadius: 8,
                    background: `${T.amber}14`,
                    border: `1px solid ${T.amber}33`,
                  }}>
                    <DollarSign size={15} style={{ color: T.amber }} />
                  </div>
                  <span style={{
                    fontSize: 10, fontWeight: 700, color: T.textMuted, fontFamily: T.mono,
                    letterSpacing: '0.08em', textTransform: 'uppercase',
                  }}>
                    {req.delta.label}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginLeft: 'auto' }}>
                    <span style={{ fontSize: 14, color: T.textMuted, fontFamily: T.mono, fontWeight: 600 }}>
                      {req.delta.before}
                    </span>
                    <span style={{ fontSize: 14, color: T.textFaint }}>→</span>
                    <span style={{
                      fontSize: 18, fontWeight: 700,
                      color: T.emerald, fontFamily: T.mono,
                      fontVariantNumeric: 'tabular-nums',
                      textShadow: `0 0 14px ${T.emerald}55`,
                    }}>
                      {req.delta.after}
                    </span>
                  </div>
                </div>
              )}

              {/* Rationale */}
              <div style={{
                padding: '14px 18px',
                borderRadius: 10,
                background: T.bgSubtle,
                border: `1px solid ${T.border}`,
                borderLeft: `2px solid ${T.violet}`,
              }}>
                <div style={{
                  display: 'inline-flex', alignItems: 'center', gap: 7,
                  marginBottom: 8,
                }}>
                  <Sparkles size={11} style={{ color: T.violet }} />
                  <span style={{
                    fontSize: 10, fontWeight: 700, color: T.violet, fontFamily: T.mono,
                    letterSpacing: '0.10em', textTransform: 'uppercase',
                  }}>
                    Justificación IA
                  </span>
                </div>
                <p style={{
                  margin: 0, fontSize: 12, lineHeight: 1.65, color: T.textSec,
                  fontStyle: 'italic',
                }}>
                  &ldquo;{req.rationale}&rdquo;
                </p>
              </div>

              {/* Context chips */}
              {req.context && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7 }}>
                  {Object.entries(req.context).map(([k, v]) => (
                    <span key={k} style={{
                      padding: '5px 10px',
                      borderRadius: 6,
                      background: T.bgSubtle,
                      border: `1px solid ${T.border}`,
                      fontSize: 11, fontFamily: T.mono,
                      color: T.textMuted,
                    }}>
                      <span style={{ color: T.textFaint }}>{k}:</span>
                      {' '}
                      <span style={{ color: T.textSec, fontWeight: 600 }}>{v}</span>
                    </span>
                  ))}
                </div>
              )}

              {/* Action buttons */}
              <div style={{ display: 'flex', gap: 10, marginTop: 4 }}>
                <button
                  type="button"
                  onClick={onApprove}
                  disabled={busy}
                  style={{
                    flex: 1, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                    padding: '12px 18px',
                    borderRadius: 10,
                    background: T.emeraldDk,
                    border: `1px solid ${T.emerald}`,
                    color: '#FFFFFF',
                    fontSize: 13, fontWeight: 700,
                    cursor: busy ? 'wait' : 'pointer',
                    opacity: busy ? 0.55 : 1,
                    fontFamily: T.sans,
                    boxShadow: '0 4px 16px -6px rgba(16,185,129,0.45)',
                    transition: 'background .15s, transform .12s',
                  }}
                  onMouseEnter={e => { if (!busy) (e.currentTarget as HTMLButtonElement).style.background = T.emerald }}
                  onMouseLeave={e => { if (!busy) (e.currentTarget as HTMLButtonElement).style.background = T.emeraldDk }}
                >
                  <Check size={15} />
                  {busy ? 'Procesando…' : 'Aprobar'}
                </button>

                <button
                  type="button"
                  onClick={onReject}
                  disabled={busy}
                  style={{
                    flex: 1, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                    padding: '12px 18px',
                    borderRadius: 10,
                    background: 'transparent',
                    border: `1px solid ${T.borderStr}`,
                    color: T.textSec,
                    fontSize: 13, fontWeight: 600,
                    cursor: busy ? 'wait' : 'pointer',
                    opacity: busy ? 0.55 : 1,
                    fontFamily: T.sans,
                    transition: 'background .15s, color .15s',
                  }}
                  onMouseEnter={e => {
                    if (!busy) {
                      const el = e.currentTarget as HTMLButtonElement
                      el.style.background = 'rgba(239, 68, 68, 0.08)'
                      el.style.borderColor = `${T.rose}66`
                      el.style.color = T.rose
                    }
                  }}
                  onMouseLeave={e => {
                    if (!busy) {
                      const el = e.currentTarget as HTMLButtonElement
                      el.style.background = 'transparent'
                      el.style.borderColor = T.borderStr
                      el.style.color = T.textSec
                    }
                  }}
                >
                  <X size={15} />
                  Rechazar
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.article>
  )
}

// ── Main component ────────────────────────────────────────────────────────────
export default function ApprovalsCenter({
  requests: extRequests,
  onApprove,
  onReject,
  demoMode = true,
}: ApprovalsCenterProps): React.JSX.Element {
  const [requests, setRequests] = useState<ApprovalRequest[]>(extRequests ?? (demoMode ? SEED_REQUESTS : []))
  const [busy, setBusy] = useState<Set<string>>(new Set())
  const [filter, setFilter] = useState<Severity | 'all'>('all')
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  // External sync
  useEffect(() => {
    if (extRequests) setRequests(extRequests)
  }, [extRequests])

  // Demo: new requests every ~14s
  useEffect(() => {
    if (extRequests || !demoMode) return
    const id = setInterval(() => {
      if (Math.random() > 0.5 || requests.length >= 8) return
      const tmpl = DEMO_NEW_REQUESTS[Math.floor(Math.random() * DEMO_NEW_REQUESTS.length)]
      const newReq: ApprovalRequest = {
        ...tmpl,
        id: `apr_live_${Date.now()}`,
        createdAt: new Date().toISOString(),
      }
      setRequests(p => [newReq, ...p])
    }, 14000)
    return () => clearInterval(id)
  }, [extRequests, demoMode, requests.length])

  const toggle = (id: string): void => {
    setExpanded(p => {
      const n = new Set(p)
      if (n.has(id)) n.delete(id); else n.add(id)
      return n
    })
  }

  const handleApprove = async (id: string): Promise<void> => {
    setBusy(p => new Set(p).add(id))
    try {
      if (onApprove) await onApprove(id)
      setTimeout(() => {
        setRequests(p => p.filter(r => r.id !== id))
        setBusy(p => { const n = new Set(p); n.delete(id); return n })
        setExpanded(p => { const n = new Set(p); n.delete(id); return n })
      }, 380)
    } catch {
      setBusy(p => { const n = new Set(p); n.delete(id); return n })
    }
  }

  const handleReject = async (id: string): Promise<void> => {
    setBusy(p => new Set(p).add(id))
    try {
      if (onReject) await onReject(id)
      setTimeout(() => {
        setRequests(p => p.filter(r => r.id !== id))
        setBusy(p => { const n = new Set(p); n.delete(id); return n })
        setExpanded(p => { const n = new Set(p); n.delete(id); return n })
      }, 380)
    } catch {
      setBusy(p => { const n = new Set(p); n.delete(id); return n })
    }
  }

  // Filter
  const visible = filter === 'all' ? requests : requests.filter(r => r.severity === filter)

  // Counts per severity (used in filter chips)
  const counts: Record<Severity | 'all', number> = {
    all:      requests.length,
    critical: requests.filter(r => r.severity === 'critical').length,
    high:     requests.filter(r => r.severity === 'high').length,
    medium:   requests.filter(r => r.severity === 'medium').length,
    low:      requests.filter(r => r.severity === 'low').length,
  }

  return (
    <section style={{
      background: T.bgBase,
      border: `1px solid ${T.border}`,
      borderRadius: 16,
      overflow: 'hidden',
      fontFamily: T.sans,
    }}>
      {/* Top accent line */}
      <div style={{
        height: 1,
        background: `linear-gradient(90deg, transparent, ${T.rose}50, ${T.amber}40, transparent)`,
      }} />

      {/* Header */}
      <div style={{
        padding: '22px 24px 18px',
        borderBottom: `1px solid ${T.border}`,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        flexWrap: 'wrap', gap: 14,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{
            position: 'relative',
            width: 42, height: 42, borderRadius: 11,
            background: 'rgba(30, 41, 59, 0.65)',
            border: `1px solid ${T.borderStr}`,
            display: 'grid', placeItems: 'center',
          }}>
            <Shield size={20} style={{ color: T.rose, filter: `drop-shadow(0 0 6px ${T.rose}66)` }} />
            {counts.critical > 0 && (
              <motion.span
                animate={{ scale: [1, 1.18, 1] }}
                transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
                style={{
                  position: 'absolute', top: -5, right: -5,
                  minWidth: 18, height: 18, padding: '0 5px',
                  borderRadius: 9,
                  background: T.rose,
                  color: '#fff',
                  fontSize: 10, fontWeight: 700, fontFamily: T.mono,
                  display: 'grid', placeItems: 'center',
                  boxShadow: `0 0 10px ${T.rose}90`,
                }}>
                {counts.critical}
              </motion.span>
            )}
          </div>
          <div>
            <h2 style={{
              margin: 0, fontSize: 16, fontWeight: 700, color: T.textPrim, letterSpacing: '-0.01em',
            }}>
              Centro de Aprobaciones
            </h2>
            <p style={{
              margin: '3px 0 0', fontSize: 11, color: T.textMuted, fontFamily: T.mono,
              letterSpacing: '0.06em', textTransform: 'uppercase',
            }}>
              Human-in-the-Loop · {requests.length} pendiente{requests.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
      </div>

      {/* Filter bar — generous spacing */}
      <div style={{
        padding: '18px 24px',
        borderBottom: `1px solid ${T.border}`,
        display: 'flex', alignItems: 'center', flexWrap: 'wrap',
        gap: 12,
        background: T.bgSubtle,
      }}>
        <FilterChip
          active={filter === 'all'}
          label="Todas"
          count={counts.all}
          color={T.textPrim}
          onClick={() => setFilter('all')}
        />
        <FilterChip
          active={filter === 'critical'}
          label="Crítico"
          count={counts.critical}
          color={T.rose}
          onClick={() => setFilter('critical')}
        />
        <FilterChip
          active={filter === 'high'}
          label="Alto"
          count={counts.high}
          color={T.amber}
          onClick={() => setFilter('high')}
        />
        <FilterChip
          active={filter === 'medium'}
          label="Medio"
          count={counts.medium}
          color={T.cyan}
          onClick={() => setFilter('medium')}
        />
        <FilterChip
          active={filter === 'low'}
          label="Bajo"
          count={counts.low}
          color={T.textMuted}
          onClick={() => setFilter('low')}
        />

        <div style={{ flex: 1 }} />

        {/* Expand/collapse all toggle */}
        {visible.length > 0 && (
          <button
            type="button"
            onClick={() => {
              if (expanded.size === visible.length) {
                setExpanded(new Set())
              } else {
                setExpanded(new Set(visible.map(r => r.id)))
              }
            }}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              padding: '6px 12px',
              borderRadius: 8,
              background: 'transparent',
              border: `1px solid ${T.border}`,
              color: T.textMuted,
              fontSize: 11, fontWeight: 600, fontFamily: T.mono,
              letterSpacing: '0.05em', textTransform: 'uppercase',
              cursor: 'pointer',
              transition: 'background .15s, color .15s',
            }}
            onMouseEnter={e => {
              const el = e.currentTarget as HTMLButtonElement
              el.style.background = 'rgba(51, 65, 85, 0.25)'
              el.style.color = T.textSec
            }}
            onMouseLeave={e => {
              const el = e.currentTarget as HTMLButtonElement
              el.style.background = 'transparent'
              el.style.color = T.textMuted
            }}
          >
            {expanded.size === visible.length ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            {expanded.size === visible.length ? 'Colapsar' : 'Expandir'} todo
          </button>
        )}
      </div>

      {/* Cards list */}
      <div style={{
        padding: '18px 20px 22px',
        maxHeight: 680,
        overflowY: 'auto',
        display: 'flex', flexDirection: 'column',
        gap: 12,
      }}>
        <AnimatePresence initial={false} mode="popLayout">
          {visible.map(req => (
            <ApprovalCard
              key={req.id}
              req={req}
              expanded={expanded.has(req.id)}
              busy={busy.has(req.id)}
              onToggle={() => toggle(req.id)}
              onApprove={() => handleApprove(req.id)}
              onReject={() => handleReject(req.id)}
            />
          ))}
        </AnimatePresence>

        {/* Empty state */}
        {visible.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              padding: '48px 20px',
              textAlign: 'center',
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14,
            }}
          >
            <div style={{
              width: 56, height: 56, borderRadius: 28,
              background: `${T.emerald}10`,
              border: `1px solid ${T.emerald}33`,
              display: 'grid', placeItems: 'center',
            }}>
              <Inbox size={24} style={{ color: T.emerald }} />
            </div>
            <div>
              <p style={{ margin: 0, fontSize: 14, fontWeight: 600, color: T.textPrim }}>
                Sin decisiones pendientes
              </p>
              <p style={{
                margin: '5px 0 0', fontSize: 11, color: T.textMuted, fontFamily: T.mono,
                letterSpacing: '0.04em',
              }}>
                IA operando dentro de parámetros aprobados
              </p>
            </div>
          </motion.div>
        )}
      </div>
    </section>
  )
}
