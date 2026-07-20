'use client'

/**
 * INVOICING + QUOTES
 *
 * Cotizaciones · facturas · firma digital · AFIP · multi-país tax.
 * Rich interactive rows with status, CAE/AFIP badges, AI actions.
 */

import { useMemo, useState } from 'react'
import {
  FileText, Send, CheckCircle2, Clock, DollarSign, Plus, Bot,
  Filter, AlertTriangle, Eye, Sparkles, TrendingUp
} from 'lucide-react'

const T = {
  bgApp:       '#0B0F19',
  bgCard:      '#151B2B',
  bgCardHov:   '#1A2235',
  border:      '#2A3441',
  textPrim:    '#F3F4F6',
  textSub:     '#9CA3AF',
  violet:      '#8B5CF6',
  emerald:     '#10B981',
  amber:       '#F59E0B',
  rose:        '#ef4444',
  cyan:        '#06B6D4',
  glowViolet:  '0 0 22px rgba(139,92,246,0.50)',
  glowEmerald: '0 0 22px rgba(16,185,129,0.50)',
  glowAmber:   '0 0 22px rgba(245,158,11,0.45)',
} as const

type DocType = 'quote' | 'invoice' | 'credit_note'
type DocStatus = 'draft' | 'sent' | 'viewed' | 'signed' | 'paid' | 'overdue' | 'void'

interface Doc {
  id: string
  number: string
  type: DocType
  customer: string
  amount: number
  currency: string
  status: DocStatus
  issued: string
  due: string
  signedAt?: string
  paidAt?: string
  taxAuthority?: string
  cae?: string
  aiAction?: string
  viewCount?: number
}

const DOCS: Doc[] = [
  { id: 'd1', number: 'INV-2847', type: 'invoice',     customer: 'Ana Suárez',       amount: 980,   currency: 'ARS', status: 'paid',    issued: 'Hoy 17:42',    due: '—',           paidAt: 'Hoy 17:50',   taxAuthority: 'AFIP A', cae: '75412988411' },
  { id: 'd2', number: 'INV-2848', type: 'invoice',     customer: 'Tomás N.',         amount: 2400,  currency: 'USD', status: 'sent',    issued: 'Hoy 17:18',    due: '24 Mayo',     taxAuthority: 'Stripe Tax', aiAction: 'Recordatorio automático en 3 días si no paga' },
  { id: 'd3', number: 'QTE-1241', type: 'quote',       customer: 'Empresa Beta SRL', amount: 8400,  currency: 'USD', status: 'viewed',  issued: 'Ayer',         due: '27 Mayo',     aiAction: 'Cliente vio 4 veces · IA sugiere follow-up con bonus de urgencia', viewCount: 4 },
  { id: 'd4', number: 'QTE-1242', type: 'quote',       customer: 'María L.',          amount: 1240,  currency: 'ARS', status: 'signed',  issued: 'Hace 2 días',  due: 'Vence al firmar', signedAt: 'Hace 1h' },
  { id: 'd5', number: 'INV-2849', type: 'invoice',     customer: 'Pedro K.',          amount: 320,   currency: 'ARS', status: 'overdue', issued: 'Hace 8 días',  due: 'Hace 2 días', aiAction: 'Dunning automático · 2 recordatorios enviados · llamada programada para hoy', taxAuthority: 'AFIP B' },
  { id: 'd6', number: 'INV-2850', type: 'invoice',     customer: 'Mariana Pérez',     amount: 850,   currency: 'ARS', status: 'paid',    issued: 'Hace 1 sem',   due: '—',           paidAt: 'Hace 6 días', taxAuthority: 'AFIP A', cae: '75412987392' },
  { id: 'd7', number: 'CN-0184',  type: 'credit_note', customer: 'Carlos R.',          amount: -240,  currency: 'ARS', status: 'paid',    issued: 'Hace 2 días',  due: '—',           paidAt: 'Hace 2 días', taxAuthority: 'AFIP A' },
  { id: 'd8', number: 'QTE-1243', type: 'quote',       customer: 'Lucía F.',           amount: 1840,  currency: 'USD', status: 'draft',   issued: 'Hace 12min',   due: 'Por enviar',  aiAction: 'Generando PDF · adjuntando análisis comparativo vs competidor' },
]

const STATUS_CONFIG: Record<DocStatus, { color: string; label: string }> = {
  draft:   { color: '#94a3b8', label: 'DRAFT'    },
  sent:    { color: '#3b82f6', label: 'ENVIADO'  },
  viewed:  { color: T.amber,   label: 'VISTO'    },
  signed:  { color: T.violet,  label: 'FIRMADO'  },
  paid:    { color: '#22c55e', label: 'PAGADO'   },
  overdue: { color: T.rose,    label: 'VENCIDO'  },
  void:    { color: '#64748b', label: 'ANULADO'  },
}

const TYPE_CONFIG: Record<DocType, { label: string; color: string; emoji: string }> = {
  quote:       { label: 'Cotización', color: T.cyan,    emoji: '📋' },
  invoice:     { label: 'Factura',    color: T.emerald, emoji: '🧾' },
  credit_note: { label: 'NC',         color: T.violet,  emoji: '↩️' },
}

export default function InvoicingQuotes() {
  const [typeFilter, setTypeFilter] = useState<DocType | 'all'>('all')
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const filtered = useMemo(
    () => typeFilter === 'all' ? DOCS : DOCS.filter(d => d.type === typeFilter),
    [typeFilter]
  )

  const stats = useMemo(() => {
    const paid = DOCS.filter(d => d.status === 'paid')
    const overdue = DOCS.filter(d => d.status === 'overdue')
    const outstanding = DOCS.filter(d => ['sent', 'viewed'].includes(d.status))
    const signed = DOCS.filter(d => d.status === 'signed')
    return {
      paidValue: paid.reduce((s, d) => s + d.amount, 0),
      outstandingValue: outstanding.reduce((s, d) => s + d.amount, 0),
      overdueValue: overdue.reduce((s, d) => s + d.amount, 0),
      signedValue: signed.reduce((s, d) => s + d.amount, 0),
    }
  }, [])

  return (
    <section style={{ background: T.bgCard, border: `1px solid ${T.border}`, borderRadius: 16, overflow: 'hidden' }}>
      <div style={{ height: 1, background: `linear-gradient(90deg, transparent, ${T.emerald}80, transparent)` }} />

      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: `${T.emerald}22`, border: `1px solid ${T.emerald}44`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <FileText style={{ width: 20, height: 20, color: T.emerald, filter: `drop-shadow(0 0 8px ${T.emerald}b0)` }} />
          </div>
          <div>
            <h2 style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, letterSpacing: '.08em', textTransform: 'uppercase', margin: 0 }}>
              INVOICING + QUOTES
              <span style={{ color: T.textSub, fontWeight: 400, textTransform: 'none', letterSpacing: 'normal', marginLeft: 8 }}>· PDF · firma · AFIP · multi-país tax</span>
            </h2>
            <p style={{ fontSize: 11, color: T.textSub, margin: 0, marginTop: 2 }}>
              {DOCS.length} documentos · ${stats.paidValue.toLocaleString()} cobrado · ${stats.outstandingValue.toLocaleString()} pendiente
            </p>
          </div>
        </div>

        {/* AI generate button */}
        <button style={{
          padding: '6px 14px', borderRadius: 8, background: `${T.violet}18`, border: `1px solid ${T.violet}40`, color: T.violet,
          fontSize: 12, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6,
        }}>
          <Sparkles style={{ width: 12, height: 12 }} />Generar cotización IA
        </button>
      </div>

      {/* Stats bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', borderBottom: `1px solid ${T.border}` }}>
        {[
          { icon: CheckCircle2, color: '#22c55e', label: 'Cobrado', value: `$${(stats.paidValue / 1000).toFixed(1)}k` },
          { icon: Send,         color: '#3b82f6', label: 'Por cobrar', value: `$${(stats.outstandingValue / 1000).toFixed(1)}k` },
          { icon: Clock,        color: T.violet,  label: 'Firmado', value: `$${(stats.signedValue / 1000).toFixed(1)}k` },
          { icon: AlertTriangle, color: T.rose,   label: 'Vencido', value: `$${stats.overdueValue}` },
        ].map((s, i) => {
          const Icon = s.icon
          return (
            <div key={i} style={{ padding: 12, borderRight: i < 3 ? `1px solid ${T.border}` : undefined }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                <Icon style={{ width: 12, height: 12, color: s.color }} />
                <p style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, margin: 0, fontWeight: 700 }}>{s.label}</p>
              </div>
              <p style={{ fontSize: 18, fontWeight: 900, color: s.color, margin: 0, textShadow: `0 0 20px ${s.color}88` }}>{s.value}</p>
            </div>
          )
        })}
      </div>

      {/* Filter bar */}
      <div style={{ padding: '10px 20px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <Filter style={{ width: 12, height: 12, color: T.textSub, flexShrink: 0 }} />
        <button onClick={() => setTypeFilter('all')} style={{
          fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', fontWeight: 700,
          padding: '2px 8px', borderRadius: 4, cursor: 'pointer',
          background: typeFilter === 'all' ? 'rgba(255,255,255,0.10)' : 'rgba(255,255,255,0.02)',
          border: `1px solid ${typeFilter === 'all' ? 'rgba(255,255,255,0.20)' : T.border}`,
          color: typeFilter === 'all' ? T.textPrim : T.textSub,
        }}>Todos · {DOCS.length}</button>
        {(Object.keys(TYPE_CONFIG) as DocType[]).map(t => {
          const cfg = TYPE_CONFIG[t]
          const count = DOCS.filter(d => d.type === t).length
          const active = typeFilter === t
          return (
            <button key={t} onClick={() => setTypeFilter(t)} style={{
              fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', fontWeight: 700,
              padding: '2px 8px', borderRadius: 4, cursor: 'pointer',
              background: active ? `${cfg.color}20` : 'rgba(255,255,255,0.02)',
              border: `1px solid ${active ? cfg.color + '50' : T.border}`,
              color: active ? cfg.color : T.textSub,
            }}>{cfg.emoji} {cfg.label} · {count}</button>
          )
        })}
        <button style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 4, fontSize: 10, padding: '4px 10px', borderRadius: 8, background: `${T.emerald}20`, border: `1px solid ${T.emerald}40`, color: T.emerald, fontWeight: 700, cursor: 'pointer' }}>
          <Plus style={{ width: 10, height: 10 }} />Nuevo
        </button>
      </div>

      {/* Document list */}
      <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 520, overflowY: 'auto' }}>
        {filtered.map(d => {
          const type = TYPE_CONFIG[d.type]
          const status = STATUS_CONFIG[d.status]
          const isExpanded = expandedId === d.id
          return (
            <div key={d.id} style={{
              borderRadius: 12, overflow: 'hidden',
              background: `${status.color}04`,
              border: `1px solid ${status.color}20`,
            }}>
              <div style={{ height: 2, background: `linear-gradient(90deg, ${status.color}, ${type.color}, transparent)` }} />

              <button
                onClick={() => setExpandedId(isExpanded ? null : d.id)}
                style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 12, padding: 14, background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left' }}
              >
                {/* Doc type icon */}
                <div style={{ width: 40, height: 40, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, flexShrink: 0, background: `${type.color}12`, border: `1px solid ${type.color}25` }}>
                  {type.emoji}
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  {/* Top row */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 4 }}>
                    <code style={{ fontSize: 11, fontWeight: 900, fontFamily: 'JetBrains Mono,monospace', color: T.textPrim }}>{d.number}</code>
                    <span style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', padding: '2px 6px', borderRadius: 4, background: `${type.color}18`, color: type.color, border: `1px solid ${type.color}28`, fontWeight: 700 }}>{type.label}</span>
                    <span style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', padding: '2px 6px', borderRadius: 4, background: `${status.color}18`, color: status.color, border: `1px solid ${status.color}28`, fontWeight: 700 }}>{status.label}</span>
                    {d.cae && <span style={{ fontSize: 8, color: T.textSub, fontFamily: 'monospace' }}>CAE {d.cae}</span>}
                    {d.viewCount && (
                      <span style={{ fontSize: 8, display: 'flex', alignItems: 'center', gap: 4, color: T.amber }}>
                        <Eye style={{ width: 8, height: 8 }} />{d.viewCount}× visto
                      </span>
                    )}
                  </div>

                  {/* Customer */}
                  <p style={{ fontSize: 14, fontWeight: 700, color: T.textPrim, margin: 0, marginBottom: 4 }}>{d.customer}</p>

                  {/* Metadata */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 9, color: T.textSub, flexWrap: 'wrap' }}>
                    <span>{d.issued}</span>
                    {d.due !== '—' && (
                      <span style={{ color: d.status === 'overdue' ? T.rose : T.textSub, fontWeight: d.status === 'overdue' ? 700 : 400 }}>
                        vence {d.due}
                      </span>
                    )}
                    {d.paidAt && <span style={{ color: '#22c55e', fontWeight: 700 }}>✓ {d.paidAt}</span>}
                    {d.signedAt && <span style={{ color: T.violet, fontWeight: 700 }}>✍ {d.signedAt}</span>}
                    {d.taxAuthority && <span style={{ color: '#3b82f6' }}>{d.taxAuthority}</span>}
                  </div>

                  {d.aiAction && (
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 6, padding: '6px 10px', borderRadius: 8, background: `${T.violet}06`, border: `1px solid ${T.violet}18`, marginTop: 8 }}>
                      <Bot style={{ width: 12, height: 12, color: T.violet, flexShrink: 0, marginTop: 1 }} />
                      <p style={{ fontSize: 10, color: T.violet, margin: 0, lineHeight: 1.5 }}>{d.aiAction}</p>
                    </div>
                  )}
                </div>

                {/* Amount */}
                <div style={{ textAlign: 'right', flexShrink: 0, marginLeft: 8 }}>
                  <p style={{ fontSize: 22, fontWeight: 900, color: status.color, margin: 0, textShadow: `0 0 20px ${status.color}88` }}>
                    {d.amount < 0 ? '-' : ''}${Math.abs(d.amount).toLocaleString()}
                  </p>
                  <p style={{ fontSize: 9, color: T.textSub, fontFamily: 'monospace', margin: 0, marginTop: 2 }}>{d.currency}</p>
                </div>
              </button>

              {/* Expanded actions */}
              {isExpanded && (
                <div style={{ padding: '0 14px 14px', borderTop: `1px solid ${T.border}`, paddingTop: 10, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  <button style={{ padding: '6px 14px', borderRadius: 8, background: `${T.emerald}18`, border: `1px solid ${T.emerald}40`, color: T.emerald, fontSize: 12, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Send style={{ width: 10, height: 10 }} />Enviar PDF
                  </button>
                  {d.status === 'sent' && (
                    <button style={{ padding: '6px 14px', borderRadius: 8, background: `${T.violet}18`, border: `1px solid ${T.violet}40`, color: T.violet, fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
                      Pedir firma
                    </button>
                  )}
                  <button style={{ padding: '6px 14px', borderRadius: 8, background: `${T.violet}18`, border: `1px solid ${T.violet}40`, color: T.violet, fontSize: 12, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Bot style={{ width: 10, height: 10 }} />Recordatorio IA
                  </button>
                  <button style={{ padding: '6px 14px', borderRadius: 8, background: 'rgba(255,255,255,0.04)', border: `1px solid ${T.border}`, color: T.textSub, fontSize: 12, cursor: 'pointer' }}>
                    Duplicar
                  </button>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Footer */}
      <div style={{ padding: '10px 20px', borderTop: `1px solid ${T.border}`, background: `${T.emerald}04`, display: 'flex', alignItems: 'center', gap: 8 }}>
        <TrendingUp style={{ width: 14, height: 14, color: T.emerald, flexShrink: 0 }} />
        <p style={{ fontSize: 11, color: T.textSub, margin: 0 }}>
          <span style={{ color: T.emerald, fontWeight: 700 }}>IA genera cotizaciones en 30 segundos</span> · con precios dinámicos, análisis comparativo y presión de urgencia integrada.
        </p>
        <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 10, color: T.violet, marginLeft: 'auto', flexShrink: 0 }}>
          <DollarSign style={{ width: 12, height: 12 }} />
          <span style={{ fontWeight: 700, textShadow: '0 0 20px #8B5CF688' }}>+$28.4k</span> facturado este mes
        </span>
      </div>
    </section>
  )
}
