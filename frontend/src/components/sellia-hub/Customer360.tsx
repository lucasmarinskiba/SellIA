'use client'

/**
 * CUSTOMER 360
 *
 * Unified profile · timeline cross-channel · LTV · health · next-best-action IA.
 */

import { useState } from 'react'
import {
  User, MessageCircle, ShoppingCart, Star, Activity,
  Mail, Phone, Bot,
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

interface Customer {
  id: string
  name: string
  email: string
  phone: string
  avatar: string
  tier: 'lead' | 'customer' | 'loyal' | 'champion' | 'evangelist'
  ltv: number
  monthsActive: number
  nps: number | null
  totalOrders: number
  avgOrderValue: number
  lastOrder: string
  health: number
  channels: string[]
  nextBestAction: string
  nextBestReason: string
}

interface TimelineEvent {
  ts: string
  channel: string
  type: 'message' | 'order' | 'review' | 'support' | 'ai'
  text: string
  color: string
}

const CUSTOMERS: Customer[] = [
  { id: 'c1', name: 'Tomás N.',        email: 'tomas@empresabeta.com',  phone: '+54 9 11 5555-2341', avatar: 'TN', tier: 'evangelist', ltv: 18400, monthsActive: 14, nps: 10, totalOrders: 23, avgOrderValue: 800,  lastOrder: 'Hace 3 días', health: 96, channels: ['WhatsApp', 'Email', 'IG'],         nextBestAction: 'Pedirle referidos en programa Embajador',          nextBestReason: 'NPS 10 + 14 meses · genera 4 referidos histórico' },
  { id: 'c2', name: 'Lucía F.',         email: 'lucia@moda.ar',          phone: '+54 9 11 4444-1289', avatar: 'LF', tier: 'champion',    ltv: 12400, monthsActive: 11, nps: 9,  totalOrders: 18, avgOrderValue: 689,  lastOrder: 'Ayer',         health: 91, channels: ['IG DM', 'WhatsApp'],                  nextBestAction: 'Solicitar testimonio en video para IG',             nextBestReason: 'Compra recurrente · highly engaged · NPS 9' },
  { id: 'c3', name: 'María L.',         email: 'maria@boutique.cl',      phone: '+56 9 8888-3421',     avatar: 'ML', tier: 'loyal',       ltv: 4800,  monthsActive: 7,  nps: 8,  totalOrders: 8,  avgOrderValue: 600,  lastOrder: 'Hace 1 sem',  health: 72, channels: ['Shopify', 'WhatsApp', 'Email'],       nextBestAction: 'Upsell pack 3 productos · descuento 12%',           nextBestReason: 'Patrón compra cada 21 días · próxima ventana' },
  { id: 'c4', name: 'Pedro K.',         email: 'pedro@logistik.com',     phone: '+54 9 11 6666-7890', avatar: 'PK', tier: 'customer',   ltv: 1450,  monthsActive: 3,  nps: 7,  totalOrders: 3,  avgOrderValue: 483,  lastOrder: 'Hace 2 sem',  health: 58, channels: ['Mercado Libre', 'Email'],             nextBestAction: 'Re-engagement · 14 días sin contacto',              nextBestReason: 'Riesgo medio · evitar churn temprano' },
  { id: 'c5', name: 'Carlos R.',         email: 'carlos.r@consultora.mx', phone: '+52 1 55 1234-5678', avatar: 'CR', tier: 'lead',       ltv: 0,     monthsActive: 0,  nps: null, totalOrders: 0, avgOrderValue: 0,    lastOrder: 'Nunca',         health: 42, channels: ['LinkedIn'],                            nextBestAction: 'Diagnóstico gratis · enviar caso éxito relevante', nextBestReason: 'Empresa B2B · perfil ICP · señales tibias' },
]

const TIMELINE: TimelineEvent[] = [
  { ts: 'Hoy 17:42',  channel: 'WhatsApp', type: 'ai',      text: 'IA respondió pregunta sobre garantía · empatía activa',     color: T.violet },
  { ts: 'Hoy 16:18',  channel: 'Stripe',   type: 'order',   text: 'Compra: Pack Premium · $2,400',                              color: T.emerald },
  { ts: 'Hoy 16:15',  channel: 'WhatsApp', type: 'message', text: '"Necesito que llegue para el viernes" · respondido auto',  color: T.cyan },
  { ts: 'Hace 2 días', channel: 'IG DM',   type: 'message', text: 'DM sobre nuevo lanzamiento · 4 mensajes intercambiados',  color: '#ec4899' },
  { ts: 'Hace 4 días', channel: 'Email',   type: 'review',  text: 'Dejó review 5⭐ · "El mejor producto que probé"',           color: T.amber },
  { ts: 'Hace 1 sem',  channel: 'WhatsApp', type: 'order',  text: 'Compra: Smartwatch SW-9 · $149',                             color: T.emerald },
  { ts: 'Hace 2 sem',  channel: 'Soporte', type: 'support', text: 'Ticket abierto · resuelto en 12min',                        color: '#3b82f6' },
  { ts: 'Hace 1 mes',  channel: 'NPS',     type: 'ai',      text: 'Survey NPS · score 10 · activado programa Embajador',      color: T.amber },
]

const TIER_CONFIG: Record<Customer['tier'], { color: string; emoji: string }> = {
  lead:       { color: '#94a3b8', emoji: '🎯' },
  customer:   { color: '#3b82f6', emoji: '💎' },
  loyal:      { color: T.violet,  emoji: '🏆' },
  champion:   { color: T.amber,   emoji: '⭐' },
  evangelist: { color: T.rose,    emoji: '🔥' },
}

const TYPE_ICON: Record<TimelineEvent['type'], React.ElementType> = {
  message: MessageCircle,
  order:   ShoppingCart,
  review:  Star,
  support: Activity,
  ai:      Bot,
}

export default function Customer360() {
  const [selected, setSelected] = useState<string>(CUSTOMERS[0].id)
  const current = CUSTOMERS.find(c => c.id === selected)!
  const tier = TIER_CONFIG[current.tier]
  const healthColor = current.health > 70 ? T.emerald : current.health > 50 ? T.amber : T.rose

  return (
    <section style={{ background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 16, overflow: 'hidden' }}>
      {/* Top accent */}
      <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, ' + T.emerald + '80, transparent)' }} />

      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ width: 40, height: 40, borderRadius: 10, background: T.violet + '22', border: '1px solid ' + T.violet + '44', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <User size={18} style={{ color: T.violet }} />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <h2 style={{ fontSize: 13, fontWeight: 900, color: T.textPrim, letterSpacing: '.06em', textTransform: 'uppercase', margin: 0 }}>CUSTOMER 360°</h2>
            <span style={{ fontSize: 10, color: T.textSub }}>· Profile · LTV · timeline · NBA</span>
          </div>
          <p style={{ fontSize: 11, color: T.textSub, marginTop: 2 }}>Vista unificada cross-canal · IA sugiere next-best-action</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr' }}>
        {/* Customer list */}
        <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 8, borderRight: '1px solid ' + T.border }}>
          <p style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, marginBottom: 4 }}>
            Clientes · {CUSTOMERS.length}
          </p>
          {CUSTOMERS.map(c => {
            const t = TIER_CONFIG[c.tier]
            const isActive = selected === c.id
            const hColor = c.health > 70 ? T.emerald : c.health > 50 ? T.amber : T.rose
            return (
              <button
                key={c.id}
                onClick={() => setSelected(c.id)}
                style={{
                  width: '100%', textAlign: 'left', borderRadius: 12,
                  background: isActive ? t.color + '18' : T.bgApp,
                  border: '1px solid ' + (isActive ? t.color + '50' : T.border),
                  boxShadow: isActive ? '0 0 16px ' + t.color + '22' : 'none',
                  padding: 12, cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{ position: 'relative', flexShrink: 0 }}>
                    <div style={{ width: 40, height: 40, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 900, fontSize: 11, background: t.color + '20', border: '2px solid ' + t.color + '50', color: t.color }}>
                      {c.avatar}
                    </div>
                    <div style={{ position: 'absolute', bottom: -2, right: -2, width: 14, height: 14, borderRadius: '50%', background: t.color, border: '2px solid ' + T.bgCard, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 7 }}>
                      {t.emoji}
                    </div>
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 4 }}>
                      <p style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.name}</p>
                      <p style={{ fontSize: 12, fontWeight: 900, color: t.color, flexShrink: 0, fontVariantNumeric: 'tabular-nums' }}>
                        {c.ltv > 0 ? `$${(c.ltv / 1000).toFixed(1)}k` : '—'}
                      </p>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6 }}>
                      <div style={{ flex: 1, height: 4, background: T.border, borderRadius: 2, overflow: 'hidden' }}>
                        <div style={{ height: '100%', borderRadius: 2, width: `${c.health}%`, background: hColor }} />
                      </div>
                      <span style={{ fontSize: 9, fontWeight: 700, color: hColor, flexShrink: 0 }}>{c.health}</span>
                    </div>
                  </div>
                </div>
              </button>
            )
          })}
        </div>

        {/* Profile + detail */}
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
          {/* Profile card */}
          <div style={{ background: tier.color + '08', border: '1px solid ' + tier.color + '28', borderRadius: 12, padding: 16 }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
              {/* Avatar */}
              <div style={{ position: 'relative', flexShrink: 0 }}>
                <div style={{ width: 64, height: 64, borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 900, fontSize: 20, background: tier.color + '20', border: '2px solid ' + tier.color + '50', boxShadow: '0 0 20px ' + tier.color + '25', color: tier.color }}>
                  {current.avatar}
                </div>
                <div style={{ position: 'absolute', bottom: -4, right: -4, width: 24, height: 24, borderRadius: '50%', background: tier.color, border: '2px solid ' + T.bgCard, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>
                  {tier.emoji}
                </div>
              </div>

              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4, flexWrap: 'wrap' }}>
                      <h3 style={{ fontSize: 17, fontWeight: 900, color: T.textPrim }}>{current.name}</h3>
                      <span style={{ fontSize: 9, padding: '2px 8px', borderRadius: 99, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.04em', background: tier.color + '20', color: tier.color, border: '1px solid ' + tier.color + '35' }}>
                        {current.tier}
                      </span>
                    </div>
                    <div style={{ fontSize: 10, color: T.textSub, display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Mail size={10} />{current.email}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Phone size={10} />{current.phone}
                      </div>
                    </div>
                  </div>
                  {/* Health ring */}
                  <div style={{ position: 'relative', width: 48, height: 48, flexShrink: 0 }}>
                    <svg viewBox="0 0 36 36" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }}>
                      <circle cx="18" cy="18" r="15" fill="none" stroke={T.border} strokeWidth="3" />
                      <circle cx="18" cy="18" r="15" fill="none" stroke={healthColor} strokeWidth="3"
                        strokeDasharray="94.2" strokeDashoffset={94.2 - (94.2 * current.health / 100)}
                        strokeLinecap="round" />
                    </svg>
                    <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                      <span style={{ fontSize: 11, fontWeight: 900, color: T.textPrim, fontVariantNumeric: 'tabular-nums', textShadow: '0 0 12px ' + healthColor + '88' }}>{current.health}</span>
                    </div>
                  </div>
                </div>

                {/* Channels */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
                  {current.channels.map(ch => (
                    <span key={ch} style={{ fontSize: 9, padding: '2px 6px', borderRadius: 4, background: T.bgApp, border: '1px solid ' + T.border, color: T.textSub, fontFamily: 'monospace' }}>{ch}</span>
                  ))}
                </div>
              </div>
            </div>

            {/* KPI row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 8, marginTop: 16 }}>
              {[
                { label: 'LTV',     value: current.ltv > 0 ? `$${current.ltv.toLocaleString()}` : '—', color: T.emerald },
                { label: 'Órdenes', value: String(current.totalOrders || '—'),                          color: '#3b82f6' },
                { label: 'AOV',     value: current.avgOrderValue > 0 ? `$${current.avgOrderValue}` : '—', color: T.violet },
                { label: 'NPS',     value: String(current.nps ?? '—'),                                  color: T.amber },
              ].map(k => (
                <div key={k.label} style={{ background: T.bgApp, border: '1px solid ' + T.border, borderRadius: 10, padding: '10px 8px', textAlign: 'center' }}>
                  <p style={{ fontSize: 15, fontWeight: 900, color: k.color, fontVariantNumeric: 'tabular-nums', textShadow: '0 0 20px ' + k.color + '88', marginBottom: 2 }}>{k.value}</p>
                  <p style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub }}>{k.label}</p>
                </div>
              ))}
            </div>

            {/* Next best action */}
            <div style={{ marginTop: 12, borderRadius: 10, padding: 12, background: T.violet + '10', border: '1px solid ' + T.violet + '30' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                <Bot size={14} style={{ color: T.violet }} />
                <p style={{ fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.violet }}>Próxima mejor acción · IA</p>
              </div>
              <p style={{ fontSize: 13, color: T.textPrim, fontWeight: 700, lineHeight: 1.4 }}>{current.nextBestAction}</p>
              <p style={{ fontSize: 10, color: T.textSub, fontStyle: 'italic', marginTop: 4 }}>{current.nextBestReason}</p>
              <button style={{ marginTop: 8, padding: '6px 14px', borderRadius: 8, background: T.violet + '18', border: '1px solid ' + T.violet + '40', color: T.violet, fontSize: 10, fontWeight: 700, cursor: 'pointer' }}>
                Ejecutar ahora
              </button>
            </div>
          </div>

          {/* Timeline */}
          <div style={{ background: T.bgApp, border: '1px solid ' + T.border, borderRadius: 12, overflow: 'hidden' }}>
            <div style={{ padding: '10px 16px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Activity size={12} style={{ color: T.textSub }} />
              <p style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub }}>Timeline cross-canal</p>
            </div>
            <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 260, overflowY: 'auto' }}>
              {TIMELINE.map((e, i) => {
                const Icon = TYPE_ICON[e.type]
                return (
                  <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: 10, borderRadius: 10, background: T.bgCard, border: '1px solid ' + T.border }}>
                    <div style={{ width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 2, background: e.color + '12', border: '1px solid ' + e.color + '30' }}>
                      <Icon size={13} style={{ color: e.color }} />
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2, flexWrap: 'wrap' }}>
                        <span style={{ fontSize: 9, color: T.textSub, fontFamily: 'monospace' }}>{e.ts}</span>
                        <span style={{ fontSize: 8, padding: '1px 6px', borderRadius: 3, fontWeight: 700, textTransform: 'uppercase', background: e.color + '15', color: e.color }}>{e.channel}</span>
                      </div>
                      <p style={{ fontSize: 11, color: T.textPrim, lineHeight: 1.4 }}>{e.text}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
