'use client'

/**
 * RETURNS / RMA FLOW
 *
 * Devoluciones · auto-approve por reglas · refund tracking · reasons analytics.
 */

import { useMemo, useState } from 'react'
import { RotateCcw, CheckCircle2, XCircle, Clock, AlertTriangle, Bot, Filter, Package, Truck } from 'lucide-react'

const T = {
  bgApp:       '#0B0F19',
  bgCard:      '#151B2B',
  bgCardHov:   '#1A2235',
  border:      '#2A3441',
  textPrim:    '#F3F4F6',
  textSub:     '#9CA3AF',
  emerald:     '#10B981',
  cyan:        '#06B6D4',
  amber:       '#F59E0B',
  violet:      '#8B5CF6',
  rose:        '#ef4444',
  glowEmerald: '0 0 22px rgba(16,185,129,0.50)',
  glowCyan:    '0 0 22px rgba(6,182,212,0.50)',
  glowAmber:   '0 0 22px rgba(245,158,11,0.45)',
} as const

type RMAStatus = 'requested' | 'approved' | 'in_transit' | 'received' | 'refunded' | 'rejected'

interface RMA {
  id: string
  customer: string
  orderId: string
  reason: string
  reasonTag: 'defect' | 'wrong_item' | 'changed_mind' | 'size' | 'late' | 'other'
  amount: number
  status: RMAStatus
  requestedAt: string
  aiDecision?: string
  trackingBack?: string
}

const RMAS: RMA[] = [
  { id: 'r1', customer: 'María L.',     orderId: 'O-2847', reason: 'Talla equivocada · necesita L',                  reasonTag: 'size',         amount: 89,  status: 'approved',  requestedAt: 'hace 2h',     aiDecision: 'Auto-aprobado · generada etiqueta envío vuelta + cupón replacement',     trackingBack: 'OCA #5478421' },
  { id: 'r2', customer: 'Pedro K.',     orderId: 'O-2841', reason: 'Llegó dañado · pantalla rota',                    reasonTag: 'defect',       amount: 149, status: 'received',   requestedAt: 'hace 4 días', aiDecision: 'Defecto confirmado · refund full + envío gratis nuevo · escalado a calidad', trackingBack: 'Andreani #8412390 ✓' },
  { id: 'r3', customer: 'Ana Suárez',   orderId: 'O-2845', reason: 'Me arrepentí',                                    reasonTag: 'changed_mind', amount: 47,  status: 'refunded',   requestedAt: 'hace 6 días', aiDecision: 'Dentro de ventana 30d · refund automático procesado',                      trackingBack: 'OCA · entregado' },
  { id: 'r4', customer: 'Carlos R.',    orderId: 'O-2848', reason: 'Llegó equivocado · vino negro pedí blanco',       reasonTag: 'wrong_item',   amount: 184, status: 'in_transit', requestedAt: 'hace 1 día',  aiDecision: 'Error de packing nuestro · cubrimos shipping + bonus 15% próx compra',    trackingBack: 'Correo Arg #7841' },
  { id: 'r5', customer: 'Tomás N.',     orderId: 'O-2820', reason: 'Demora · llegó 12 días tarde',                    reasonTag: 'late',         amount: 320, status: 'refunded',   requestedAt: 'hace 2 sem',  aiDecision: 'Partial refund 15% por demora · cliente acepta · entregado igual' },
  { id: 'r6', customer: 'Mariana P.',   orderId: 'O-2842', reason: 'Cambié de opinión',                               reasonTag: 'changed_mind', amount: 67,  status: 'rejected',   requestedAt: 'hace 5 días', aiDecision: 'Fuera de ventana 30d · ofrecido store-credit 50%' },
  { id: 'r7', customer: 'Lucía F.',     orderId: 'O-2855', reason: 'Defecto · zipper roto',                           reasonTag: 'defect',       amount: 220, status: 'requested',  requestedAt: 'hace 12min',  aiDecision: 'Analizando foto adjunta · 95% confianza es defecto real' },
]

const STATUS_CONFIG: Record<RMAStatus, { color: string; label: string; icon: React.ElementType }> = {
  requested:  { color: T.amber,   label: 'SOLICITADO',  icon: Clock },
  approved:   { color: '#3b82f6', label: 'APROBADO',    icon: CheckCircle2 },
  in_transit: { color: T.violet,  label: 'EN TRÁNSITO', icon: Truck },
  received:   { color: T.cyan,    label: 'RECIBIDO',    icon: Package },
  refunded:   { color: T.emerald, label: 'REEMBOLSADO', icon: CheckCircle2 },
  rejected:   { color: T.rose,    label: 'RECHAZADO',   icon: XCircle },
}

const REASON_TAGS = {
  defect:       { color: T.rose,    label: 'Defecto' },
  wrong_item:   { color: '#f97316', label: 'Equivocado' },
  changed_mind: { color: T.textSub, label: 'Cambio opinión' },
  size:         { color: T.cyan,    label: 'Talla' },
  late:         { color: T.amber,   label: 'Demora' },
  other:        { color: T.violet,  label: 'Otro' },
} as const

export default function ReturnsRMA() {
  const [filter, setFilter] = useState<RMAStatus | 'all'>('all')

  const filtered = useMemo(() => filter === 'all' ? RMAS : RMAS.filter(r => r.status === filter), [filter])

  const stats = useMemo(() => {
    const reasonsBreakdown: Record<string, number> = {}
    for (const r of RMAS) reasonsBreakdown[r.reasonTag] = (reasonsBreakdown[r.reasonTag] || 0) + 1
    return {
      total: RMAS.length,
      refunded: RMAS.filter(r => r.status === 'refunded').length,
      pending: RMAS.filter(r => ['requested', 'approved', 'in_transit', 'received'].includes(r.status)).length,
      refundedValue: RMAS.filter(r => r.status === 'refunded').reduce((s, r) => s + r.amount, 0),
      reasonsBreakdown,
      returnRate: ((RMAS.length / 247) * 100).toFixed(1),
    }
  }, [])

  return (
    <section style={{ background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 16, overflow: 'hidden' }}>
      {/* Top accent */}
      <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, ' + T.rose + '80, transparent)' }} />

      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: T.rose + '22', border: '1px solid ' + T.rose + '44', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <RotateCcw size={18} style={{ color: T.rose }} />
          </div>
          <div>
            <h2 style={{ fontSize: 13, fontWeight: 900, color: T.textPrim, letterSpacing: '.06em', textTransform: 'uppercase', margin: 0 }}>
              RETURNS / RMA <span style={{ color: T.textSub, fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>· Auto-approve · refund tracking</span>
            </h2>
            <p style={{ fontSize: 11, color: T.textSub, marginTop: 2 }}>
              {stats.total} solicitudes · <span style={{ color: T.rose, fontWeight: 700 }}>{stats.returnRate}%</span> return rate · <span style={{ color: T.emerald }}>${stats.refundedValue}</span> reembolsado
            </p>
          </div>
        </div>
        {/* Stats pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ textAlign: 'center', padding: '6px 12px', borderRadius: 8, background: T.amber + '12', border: '1px solid ' + T.amber + '28' }}>
            <p style={{ fontSize: 16, fontWeight: 900, color: T.amber, fontVariantNumeric: 'tabular-nums', textShadow: T.glowAmber }}>{stats.pending}</p>
            <p style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', textTransform: 'uppercase', color: T.textSub }}>Pending</p>
          </div>
          <div style={{ textAlign: 'center', padding: '6px 12px', borderRadius: 8, background: T.emerald + '12', border: '1px solid ' + T.emerald + '28' }}>
            <p style={{ fontSize: 16, fontWeight: 900, color: T.emerald, fontVariantNumeric: 'tabular-nums', textShadow: T.glowEmerald }}>{stats.refunded}</p>
            <p style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', textTransform: 'uppercase', color: T.textSub }}>Refunded</p>
          </div>
          <div style={{ textAlign: 'center', padding: '6px 12px', borderRadius: 8, background: T.cyan + '12', border: '1px solid ' + T.cyan + '28' }}>
            <p style={{ fontSize: 16, fontWeight: 900, color: T.cyan, fontVariantNumeric: 'tabular-nums', textShadow: T.glowCyan }}>{stats.returnRate}%</p>
            <p style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', textTransform: 'uppercase', color: T.textSub }}>Rate</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div style={{ padding: '10px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <Filter size={12} style={{ color: T.textSub }} />
        <button
          onClick={() => setFilter('all')}
          style={{ fontSize: 9, padding: '2px 8px', borderRadius: 99, fontWeight: 700, textTransform: 'uppercase', cursor: 'pointer', background: filter === 'all' ? 'rgba(255,255,255,0.12)' : T.bgApp, border: '1px solid ' + (filter === 'all' ? 'rgba(255,255,255,0.25)' : T.border), color: filter === 'all' ? T.textPrim : T.textSub }}
        >
          Todos · {RMAS.length}
        </button>
        {(Object.keys(STATUS_CONFIG) as RMAStatus[]).map(s => {
          const cfg = STATUS_CONFIG[s]
          const c = RMAS.filter(r => r.status === s).length
          const active = filter === s
          return (
            <button key={s} onClick={() => setFilter(s)} style={{ fontSize: 9, padding: '2px 8px', borderRadius: 99, fontWeight: 700, textTransform: 'uppercase', cursor: 'pointer', background: active ? cfg.color + '20' : T.bgApp, border: '1px solid ' + (active ? cfg.color + '50' : T.border), color: active ? cfg.color : T.textSub }}>
              {cfg.label} · {c}
            </button>
          )
        })}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 220px', gap: 16, padding: 16 }}>
        {/* RMA list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 440, overflowY: 'auto' }}>
          {filtered.map(r => {
            const status = STATUS_CONFIG[r.status]
            const reason = REASON_TAGS[r.reasonTag]
            const StatusIcon = status.icon
            return (
              <div key={r.id} style={{ borderRadius: 12, overflow: 'hidden', background: status.color + '04', border: '1px solid ' + status.color + '22' }}>
                <div style={{ height: 2, background: 'linear-gradient(90deg, ' + status.color + ', ' + reason.color + ', transparent)' }} />
                <div style={{ padding: '12px 14px', display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                  <div style={{ width: 40, height: 40, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, background: status.color + '15', border: '1px solid ' + status.color + '30' }}>
                    <StatusIcon size={16} style={{ color: status.color }} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 2 }}>
                      <p style={{ fontSize: 13, fontWeight: 700, color: T.textPrim }}>{r.customer}</p>
                      <code style={{ fontSize: 9, color: T.textSub, fontFamily: 'monospace' }}>{r.orderId}</code>
                      <span style={{ padding: '1px 4px', borderRadius: 3, fontSize: 8, fontFamily: 'monospace', fontWeight: 700, textTransform: 'uppercase', background: reason.color + '20', color: reason.color }}>{reason.label}</span>
                      <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 10, fontFamily: 'monospace', background: status.color + '18', border: '1px solid ' + status.color + '28', color: status.color }}>{status.label}</span>
                    </div>
                    <p style={{ fontSize: 11, color: T.textSub, fontStyle: 'italic', marginBottom: 4 }}>"{r.reason}"</p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 10, color: T.textSub }}>
                      <span>📅 {r.requestedAt}</span>
                      {r.trackingBack && <span>🚚 {r.trackingBack}</span>}
                    </div>
                    {r.aiDecision && (
                      <div style={{ marginTop: 6, display: 'flex', alignItems: 'flex-start', gap: 6, padding: '6px 10px', borderRadius: 8, background: T.violet + '08', border: '1px solid ' + T.violet + '22' }}>
                        <Bot size={10} style={{ color: T.violet, flexShrink: 0, marginTop: 1 }} />
                        <p style={{ fontSize: 10, color: T.violet, lineHeight: 1.4 }}>{r.aiDecision}</p>
                      </div>
                    )}
                  </div>
                  <div style={{ textAlign: 'right', flexShrink: 0 }}>
                    <p style={{ fontSize: 20, fontWeight: 900, color: status.color, fontVariantNumeric: 'tabular-nums', textShadow: '0 0 16px ' + status.color + '88', lineHeight: 1 }}>-${r.amount}</p>
                    <p style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', textTransform: 'uppercase', color: T.textSub, marginTop: 2 }}>devol.</p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Reasons breakdown */}
        <div style={{ background: T.bgApp, border: '1px solid ' + T.border, borderRadius: 12, padding: 12 }}>
          <p style={{ fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 4 }}>
            <AlertTriangle size={10} /> RAZONES · BREAKDOWN
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {Object.entries(stats.reasonsBreakdown).map(([k, v]) => {
              const cfg = REASON_TAGS[k as keyof typeof REASON_TAGS]
              const pct = Math.round((v / stats.total) * 100)
              return (
                <div key={k}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 10, marginBottom: 4 }}>
                    <span style={{ color: cfg.color }}>{cfg.label}</span>
                    <span style={{ fontFamily: 'monospace', color: T.textSub, fontVariantNumeric: 'tabular-nums' }}>{v} · {pct}%</span>
                  </div>
                  <div style={{ height: 4, background: T.border, borderRadius: 2, overflow: 'hidden' }}>
                    <div style={{ height: '100%', borderRadius: 2, background: cfg.color, width: `${pct}%` }} />
                  </div>
                </div>
              )
            })}
          </div>
          <div style={{ marginTop: 16, paddingTop: 12, borderTop: '1px solid ' + T.border }}>
            <p style={{ fontSize: 10, color: T.violet, lineHeight: 1.5 }}>
              <Bot size={10} style={{ display: 'inline', marginRight: 4 }} />
              IA detectó: <span style={{ fontWeight: 700 }}>talla incorrecta en sneakers 42</span> es el top motivo → sugiere actualizar guía de tallas.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
