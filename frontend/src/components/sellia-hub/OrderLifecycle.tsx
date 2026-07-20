'use client'

/**
 * ORDER LIFECYCLE
 * Kanban de órdenes · 6 stages · IA mueve y gestiona automáticamente.
 */

import { useState, useMemo } from 'react'
import {
  ShoppingCart, DollarSign, Package, Truck, CheckCircle2,
  XCircle, Bot, AlertTriangle, Activity, TrendingUp, Zap,
} from 'lucide-react'

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

type OrderStatus = 'new' | 'paid' | 'preparing' | 'shipped' | 'delivered' | 'cancelled'

interface Order {
  id: string
  customer: string
  channel: string
  amount: number
  items: number
  status: OrderStatus
  ts: string
  aiHandling: string
  alert?: string
}

const ORDERS: Order[] = [
  { id: 'O-2847', customer: 'Ana Suárez',    channel: 'Shopify',        amount: 980,  items: 2, status: 'new',       ts: '17:42', aiHandling: 'Confirmando pago Stripe' },
  { id: 'O-2848', customer: 'Tomás N.',      channel: 'WhatsApp',       amount: 2400, items: 1, status: 'paid',      ts: '17:18', aiHandling: 'Generando factura AFIP' },
  { id: 'O-2849', customer: 'María L.',      channel: 'Mercado Libre',  amount: 1240, items: 3, status: 'paid',      ts: '16:54', aiHandling: 'Esperando picking' },
  { id: 'O-2850', customer: 'Pedro K.',      channel: 'Instagram DM',   amount: 320,  items: 1, status: 'preparing', ts: '16:32', aiHandling: 'Picking · CABA warehouse' },
  { id: 'O-2851', customer: 'Empresa Beta',  channel: 'Email',          amount: 1847, items: 5, status: 'preparing', ts: '15:47', aiHandling: 'Packing · empaque pendiente' },
  { id: 'O-2852', customer: 'Mariana Pérez', channel: 'WhatsApp',       amount: 850,  items: 2, status: 'shipped',   ts: '14:21', aiHandling: 'Andreani · tracking 5478421' },
  { id: 'O-2853', customer: 'Lautaro M.',    channel: 'Shopify',        amount: 420,  items: 1, status: 'shipped',   ts: '12:08', aiHandling: 'OCA · tracking 8412390' },
  { id: 'O-2854', customer: 'Lucía F.',      channel: 'TikTok Shop',    amount: 1240, items: 4, status: 'delivered', ts: '10:34', aiHandling: 'Review solicitada · enviado' },
  { id: 'O-2855', customer: 'Carlos R.',     channel: 'LinkedIn',       amount: 680,  items: 1, status: 'delivered', ts: '09:18', aiHandling: 'NPS solicitado · 9/10' },
  { id: 'O-2856', customer: 'Pedro K.',      channel: 'WhatsApp',       amount: 240,  items: 1, status: 'cancelled', ts: 'Ayer',  aiHandling: 'Refund procesado', alert: 'Investigar motivo cancelación' },
]

const STATUS_CONFIG: Record<OrderStatus, { label: string; color: string; icon: React.ElementType }> = {
  new:       { label: 'Nueva',       color: '#3b82f6', icon: ShoppingCart },
  paid:      { label: 'Pagada',      color: T.emerald, icon: DollarSign },
  preparing: { label: 'Preparando',  color: T.amber,   icon: Package },
  shipped:   { label: 'En camino',   color: T.violet,  icon: Truck },
  delivered: { label: 'Entregada',   color: T.cyan,    icon: CheckCircle2 },
  cancelled: { label: 'Cancelada',   color: T.rose,    icon: XCircle },
}

const PIPELINE: OrderStatus[] = ['new', 'paid', 'preparing', 'shipped', 'delivered']

export default function OrderLifecycle() {
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const grouped = useMemo(() => {
    const g: Record<OrderStatus, Order[]> = { new: [], paid: [], preparing: [], shipped: [], delivered: [], cancelled: [] }
    for (const o of ORDERS) g[o.status].push(o)
    return g
  }, [])

  const stats = useMemo(() => {
    const valid = ORDERS.filter(o => o.status !== 'cancelled')
    return {
      today: ORDERS.length,
      revenue: valid.reduce((s, o) => s + o.amount, 0),
      avgTicket: Math.round(valid.reduce((s, o) => s + o.amount, 0) / Math.max(valid.length, 1)),
      active: ORDERS.filter(o => o.status !== 'delivered' && o.status !== 'cancelled').length,
      transit: grouped['shipped'].length,
      delivered: grouped['delivered'].length,
      cancelled: grouped['cancelled'].length,
    }
  }, [grouped])

  return (
    <section style={{ background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 16, overflow: 'hidden' }}>
      {/* Top accent */}
      <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, ' + T.cyan + '80, transparent)' }} />

      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: T.cyan + '22', border: '1px solid ' + T.cyan + '44', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ShoppingCart size={18} style={{ color: T.cyan }} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <h2 style={{ fontSize: 13, fontWeight: 900, color: T.textPrim, letterSpacing: '.06em', textTransform: 'uppercase', margin: 0 }}>ORDER LIFECYCLE</h2>
              <span style={{ fontSize: 10, color: T.textSub }}>· Kanban · IA opera solo</span>
            </div>
            <p style={{ fontSize: 11, color: T.textSub, marginTop: 2 }}>
              {stats.today} órdenes hoy · <span style={{ color: T.emerald, fontWeight: 700, textShadow: '0 0 14px ' + T.emerald + '88' }}>${stats.revenue.toLocaleString()}</span> revenue · ticket avg ${stats.avgTicket}
            </p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px', borderRadius: 10, background: T.emerald + '15', border: '1px solid ' + T.emerald + '35' }}>
            <Activity size={12} style={{ color: T.emerald }} className="animate-pulse" />
            <span style={{ fontSize: 11, fontWeight: 700, color: T.emerald }}>{stats.active} activas</span>
          </div>
        </div>
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', borderBottom: '1px solid ' + T.border }}>
        {[
          { label: 'Órdenes hoy',   value: String(stats.today),         color: T.cyan },
          { label: 'En tránsito',   value: String(stats.transit),       color: T.violet },
          { label: 'Entregadas',    value: String(stats.delivered),     color: T.emerald },
          { label: 'Canceladas',    value: String(stats.cancelled),     color: T.rose },
        ].map(s => (
          <div key={s.label} style={{ padding: 16, borderRight: '1px solid ' + T.border, textAlign: 'center' }}>
            <p style={{ fontSize: 22, fontWeight: 900, color: s.color, fontVariantNumeric: 'tabular-nums', textShadow: '0 0 20px ' + s.color + '88', marginBottom: 4 }}>{s.value}</p>
            <p style={{ fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub }}>{s.label}</p>
          </div>
        ))}
      </div>

      {/* Pipeline progress bar */}
      <div style={{ padding: '12px 20px', borderBottom: '1px solid ' + T.border }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          {PIPELINE.map((s, i) => {
            const cfg = STATUS_CONFIG[s]
            const count = grouped[s].length
            const isLast = i === PIPELINE.length - 1
            return (
              <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 4, flex: 1 }}>
                <div style={{ flex: 1, borderRadius: 8, padding: '8px 4px', textAlign: 'center', background: cfg.color + '10', border: '1px solid ' + cfg.color + '28' }}>
                  <p style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', textTransform: 'uppercase', color: cfg.color, letterSpacing: '.04em', marginBottom: 2 }}>{cfg.label}</p>
                  <p style={{ fontSize: 16, fontWeight: 900, color: T.textPrim, fontVariantNumeric: 'tabular-nums' }}>{count}</p>
                </div>
                {!isLast && <div style={{ width: 12, height: 1, background: T.border, flexShrink: 0 }} />}
              </div>
            )
          })}
          <div style={{ width: 1, height: 32, background: T.border, margin: '0 6px', flexShrink: 0 }} />
          <div style={{ borderRadius: 8, padding: '8px 12px', textAlign: 'center', background: T.rose + '08', border: '1px solid ' + T.rose + '25' }}>
            <p style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', textTransform: 'uppercase', color: T.rose, letterSpacing: '.04em', marginBottom: 2 }}>Canc.</p>
            <p style={{ fontSize: 16, fontWeight: 900, color: T.rose, fontVariantNumeric: 'tabular-nums' }}>{grouped['cancelled'].length}</p>
          </div>
        </div>
      </div>

      {/* Kanban */}
      <div style={{ padding: 12, overflowX: 'auto' }}>
        <div style={{ display: 'flex', gap: 12, minWidth: 'max-content' }}>
          {(Object.keys(STATUS_CONFIG) as OrderStatus[]).map(status => {
            const cfg = STATUS_CONFIG[status]
            const Icon = cfg.icon
            const orders = grouped[status]
            return (
              <div key={status} style={{ width: 210, borderRadius: 12, padding: 10, display: 'flex', flexDirection: 'column', gap: 8, background: cfg.color + '06', border: '1px solid ' + cfg.color + '25' }}>
                {/* Column header */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '4px 4px 4px 4px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Icon size={14} style={{ color: cfg.color }} />
                    <span style={{ fontSize: 10, fontWeight: 900, textTransform: 'uppercase', letterSpacing: '.04em', color: cfg.color }}>{cfg.label}</span>
                  </div>
                  <span style={{ width: 20, height: 20, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 900, background: cfg.color + '20', color: cfg.color }}>
                    {orders.length}
                  </span>
                </div>

                {/* Order cards */}
                {orders.map(o => {
                  const isSelected = selectedId === o.id
                  return (
                    <button
                      key={o.id}
                      onClick={() => setSelectedId(isSelected ? null : o.id)}
                      style={{
                        position: 'relative', borderRadius: 10, padding: 10, textAlign: 'left', cursor: 'pointer', width: '100%',
                        background: isSelected ? cfg.color + '12' : T.bgCard,
                        border: '1px solid ' + (isSelected ? cfg.color + '50' : T.border),
                      }}
                    >
                      {/* Status accent line */}
                      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, borderRadius: '10px 10px 0 0', background: 'linear-gradient(90deg, ' + cfg.color + ', transparent)' }} />

                      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8, marginBottom: 6 }}>
                        <code style={{ fontSize: 8, color: T.textSub, fontFamily: 'monospace' }}>{o.id}</code>
                        <span style={{ fontSize: 8, color: T.textSub, flexShrink: 0 }}>{o.ts}</span>
                      </div>

                      <p style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, marginBottom: 4 }}>{o.customer}</p>

                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                        <span style={{ fontSize: 9, color: T.textSub, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{o.channel}</span>
                        <span style={{ fontSize: 13, fontWeight: 900, color: cfg.color, fontVariantNumeric: 'tabular-nums', textShadow: '0 0 14px ' + cfg.color + '88' }}>${o.amount.toLocaleString()}</span>
                      </div>

                      {/* AI action */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 8px', borderRadius: 8, background: T.violet + '08', border: '1px solid ' + T.violet + '20' }}>
                        <Bot size={10} style={{ color: T.violet, flexShrink: 0 }} />
                        <p style={{ fontSize: 9, color: T.violet, lineHeight: 1.3 }}>{o.aiHandling}</p>
                      </div>

                      {o.alert && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '4px 8px', borderRadius: 8, marginTop: 6, background: T.amber + '10', border: '1px solid ' + T.amber + '28' }}>
                          <AlertTriangle size={10} style={{ color: T.amber, flexShrink: 0 }} />
                          <p style={{ fontSize: 9, color: T.amber }}>{o.alert}</p>
                        </div>
                      )}
                    </button>
                  )
                })}

                {orders.length === 0 && (
                  <div style={{ padding: '16px 0', textAlign: 'center' }}>
                    <p style={{ fontSize: 10, color: T.textSub, fontStyle: 'italic' }}>sin órdenes</p>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Footer */}
      <div style={{ padding: '12px 20px', borderTop: '1px solid ' + T.border, display: 'flex', alignItems: 'center', gap: 16, fontSize: 10, color: T.textSub }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Zap size={12} style={{ color: T.cyan }} />
          <span>IA gestiona picking, facturación, tracking y post-venta automáticamente</span>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6 }}>
          <TrendingUp size={12} style={{ color: T.emerald }} />
          <span style={{ color: T.emerald, fontWeight: 700, textShadow: '0 0 14px ' + T.emerald + '88' }}>${stats.revenue.toLocaleString()} facturado hoy</span>
        </div>
      </div>
    </section>
  )
}
