'use client'

/**
 * EMAIL CAMPAIGNS
 *
 * Drips · broadcasts · segments · A/B subject test · deliverability stats.
 */

import { useMemo, useState } from 'react'
import { Mail, Activity, Users, Bot, Plus, Filter } from 'lucide-react'

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

type CampaignKind   = 'drip' | 'broadcast' | 'transactional' | 'abandoned' | 'winback'
type CampaignStatus = 'active' | 'paused' | 'draft' | 'scheduled'

interface Campaign {
  id: string
  emoji: string
  name: string
  kind: CampaignKind
  segment: string
  recipients: number
  steps: number
  status: CampaignStatus
  openRate: number
  clickRate: number
  conversionRate: number
  revenue: number
  aiNote?: string
  color: string
}

const CAMPAIGNS: Campaign[] = [
  { id: 'c1', emoji: '🎁', name: 'Welcome drip · onboarding 14d',      kind: 'drip',          segment: 'Nuevos signups',               recipients: 247,  steps: 7, status: 'active',    openRate: 47, clickRate: 23, conversionRate: 18, revenue: 4180, aiNote: 'Subject A/B winner: "Tu primer paso 🚀"',                          color: T.emerald },
  { id: 'c2', emoji: '🛒', name: 'Cart abandoned · recovery 3-toques', kind: 'abandoned',     segment: 'Carrito >$50 últimos 7d',      recipients: 89,   steps: 3, status: 'active',    openRate: 62, clickRate: 38, conversionRate: 24, revenue: 6420, aiNote: 'Touch 2 (cupón 10%) genera 71% del revenue total',                 color: T.amber },
  { id: 'c3', emoji: '📰', name: 'Newsletter · ofertas semanales',      kind: 'broadcast',     segment: 'All subscribers',              recipients: 4847, steps: 1, status: 'scheduled', openRate: 0,  clickRate: 0,  conversionRate: 0,  revenue: 0,    aiNote: 'Programado viernes 09:00 · best-time per cohort analysis',         color: T.violet },
  { id: 'c4', emoji: '💸', name: 'Win-back · 90 días sin compra',      kind: 'winback',       segment: 'Clientes inactivos 90d',       recipients: 412,  steps: 4, status: 'active',    openRate: 28, clickRate: 14, conversionRate: 7,  revenue: 1847, aiNote: 'Touch 3 (15% off + bonus) → max conversión',                      color: T.rose },
  { id: 'c5', emoji: '⭐', name: 'NPS request · post-orden 14d',       kind: 'transactional', segment: 'Clientes · 14d post-compra',   recipients: 167,  steps: 1, status: 'active',    openRate: 71, clickRate: 42, conversionRate: 38, revenue: 0,    color: '#3b82f6' },
  { id: 'c6', emoji: '🎂', name: 'Birthday · 20% off',                  kind: 'transactional', segment: 'Clientes · día cumpleaños',    recipients: 12,   steps: 1, status: 'active',    openRate: 84, clickRate: 56, conversionRate: 41, revenue: 980,  color: '#ec4899' },
  { id: 'c7', emoji: '🚀', name: 'Re-engagement seq · 5 toques',       kind: 'drip',          segment: 'Leads fríos >60d',             recipients: 847,  steps: 5, status: 'draft',     openRate: 0,  clickRate: 0,  conversionRate: 0,  revenue: 0,    aiNote: 'IA generó copy basado en campañas ganadoras previas',              color: T.cyan },
]

const KIND_CONFIG: Record<CampaignKind, { label: string; color: string }> = {
  drip:          { label: 'Drip',          color: T.emerald },
  broadcast:     { label: 'Broadcast',     color: T.violet },
  transactional: { label: 'Transaccional', color: '#3b82f6' },
  abandoned:     { label: 'Cart recovery', color: T.amber },
  winback:       { label: 'Win-back',      color: T.rose },
}

const STATUS_CONFIG: Record<CampaignStatus, { label: string; color: string }> = {
  active:    { label: 'ACTIVA',     color: T.emerald },
  paused:    { label: 'PAUSADA',    color: T.amber },
  draft:     { label: 'BORRADOR',   color: T.textSub },
  scheduled: { label: 'PROGRAMADA', color: '#3b82f6' },
}

export default function EmailCampaigns() {
  const [filter, setFilter] = useState<CampaignKind | 'all'>('all')

  const filtered = useMemo(() => filter === 'all' ? CAMPAIGNS : CAMPAIGNS.filter(c => c.kind === filter), [filter])

  const stats = useMemo(() => ({
    active: CAMPAIGNS.filter(c => c.status === 'active').length,
    recipients: CAMPAIGNS.reduce((s, c) => s + c.recipients, 0),
    revenue: CAMPAIGNS.reduce((s, c) => s + c.revenue, 0),
    avgOpen: Math.round(
      CAMPAIGNS.filter(c => c.openRate > 0).reduce((s, c) => s + c.openRate, 0) /
      Math.max(CAMPAIGNS.filter(c => c.openRate > 0).length, 1)
    ),
  }), [])

  const AI_SUGGESTIONS = [
    { text: 'Campaña "Gracias por tu compra + referido" · est. 12% conversión', color: T.emerald },
    { text: 'Re-engagement VIP 6 meses inactivos · estimado $2.4k', color: T.amber },
    { text: 'Newsletter estacional · temporada alta próxima semana', color: T.violet },
  ]

  return (
    <section style={{ background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 16, overflow: 'hidden' }}>
      {/* Top accent */}
      <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, ' + T.cyan + '80, transparent)' }} />

      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: T.cyan + '22', border: '1px solid ' + T.cyan + '44', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Mail size={18} style={{ color: T.cyan }} />
          </div>
          <div>
            <h2 style={{ fontSize: 13, fontWeight: 900, color: T.textPrim, letterSpacing: '.06em', textTransform: 'uppercase', margin: 0 }}>
              EMAIL CAMPAIGNS <span style={{ color: T.textSub, fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>· Drips · broadcasts · A/B</span>
            </h2>
            <p style={{ fontSize: 11, color: T.textSub, marginTop: 2 }}>
              {stats.active} activas · {stats.recipients.toLocaleString()} recipients · <span style={{ color: T.violet, fontWeight: 700 }}>{stats.avgOpen}%</span> open avg
            </p>
          </div>
        </div>
        <button style={{ padding: '6px 14px', borderRadius: 8, background: T.cyan + '18', border: '1px solid ' + T.cyan + '40', color: T.cyan, fontSize: 12, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}>
          <Plus size={12} /> Nueva campaña
        </button>
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', borderBottom: '1px solid ' + T.border }}>
        {[
          { label: 'Recipients',      value: stats.recipients.toLocaleString(), color: T.cyan },
          { label: 'Open rate avg',   value: `${stats.avgOpen}%`,              color: T.violet },
          { label: 'Revenue total',   value: `$${(stats.revenue / 1000).toFixed(1)}k`, color: T.emerald },
          { label: 'Inbox placement', value: '98.4%',                           color: T.amber },
        ].map(s => (
          <div key={s.label} style={{ padding: 16, borderRight: '1px solid ' + T.border, textAlign: 'center' }}>
            <p style={{ fontSize: 20, fontWeight: 900, color: s.color, fontVariantNumeric: 'tabular-nums', textShadow: '0 0 18px ' + s.color + '88', marginBottom: 4 }}>{s.value}</p>
            <p style={{ fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub }}>{s.label}</p>
          </div>
        ))}
      </div>

      {/* AI suggested campaigns */}
      <div style={{ padding: '12px 20px', borderBottom: '1px solid ' + T.border, background: T.violet + '04' }}>
        <p style={{ fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.violet, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 4 }}>
          <Bot size={10} /> Campañas sugeridas por IA
        </p>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {AI_SUGGESTIONS.map((s, i) => (
            <button key={i} style={{ padding: '6px 14px', borderRadius: 8, background: s.color + '18', border: '1px solid ' + s.color + '40', color: s.color, fontSize: 11, fontWeight: 600, cursor: 'pointer' }}>
              + {s.text}
            </button>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div style={{ padding: '10px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <Filter size={12} style={{ color: T.textSub }} />
        <button onClick={() => setFilter('all')} style={{ fontSize: 9, padding: '2px 8px', borderRadius: 99, fontWeight: 700, textTransform: 'uppercase', cursor: 'pointer', background: filter === 'all' ? 'rgba(255,255,255,0.12)' : T.bgApp, border: '1px solid ' + (filter === 'all' ? 'rgba(255,255,255,0.25)' : T.border), color: filter === 'all' ? T.textPrim : T.textSub }}>
          Todas · {CAMPAIGNS.length}
        </button>
        {(Object.keys(KIND_CONFIG) as CampaignKind[]).map(k => {
          const cfg = KIND_CONFIG[k]
          const c = CAMPAIGNS.filter(camp => camp.kind === k).length
          const active = filter === k
          return (
            <button key={k} onClick={() => setFilter(k)} style={{ fontSize: 9, padding: '2px 8px', borderRadius: 99, fontWeight: 700, textTransform: 'uppercase', cursor: 'pointer', background: active ? cfg.color + '20' : T.bgApp, border: '1px solid ' + (active ? cfg.color + '50' : T.border), color: active ? cfg.color : T.textSub }}>
              {cfg.label} · {c}
            </button>
          )
        })}
      </div>

      {/* Campaign list */}
      <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {filtered.map(c => {
          const kind   = KIND_CONFIG[c.kind]
          const status = STATUS_CONFIG[c.status]
          const hasStats = c.status === 'active' && c.openRate > 0
          return (
            <div
              key={c.id}
              style={{ borderRadius: 12, overflow: 'hidden', background: c.color + '04', border: '1px solid ' + c.color + '22', opacity: c.status === 'draft' ? 0.65 : 1 }}
            >
              <div style={{ height: 2, background: 'linear-gradient(90deg, ' + c.color + ', transparent)' }} />
              <div style={{ padding: '12px 14px', display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                <span style={{ fontSize: 22, flexShrink: 0, marginTop: 2 }}>{c.emoji}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  {/* Header */}
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8, marginBottom: 8 }}>
                    <div>
                      <p style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, marginBottom: 6 }}>{c.name}</p>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                        <span style={{ fontSize: 8, padding: '2px 6px', borderRadius: 4, fontWeight: 700, textTransform: 'uppercase', background: kind.color + '15', color: kind.color, border: '1px solid ' + kind.color + '28' }}>{kind.label}</span>
                        <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 10, fontFamily: 'monospace', background: status.color + '18', border: '1px solid ' + status.color + '28', color: status.color }}>{status.label}</span>
                        {c.steps > 1 && <span style={{ fontSize: 9, color: T.textSub, fontFamily: 'monospace' }}>{c.steps} pasos</span>}
                      </div>
                    </div>
                    {hasStats && c.revenue > 0 && (
                      <div style={{ textAlign: 'right', flexShrink: 0 }}>
                        <p style={{ fontSize: 17, fontWeight: 900, color: T.emerald, fontVariantNumeric: 'tabular-nums', textShadow: T.glowEmerald }}>${c.revenue.toLocaleString()}</p>
                        <p style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', textTransform: 'uppercase', color: T.textSub }}>revenue</p>
                      </div>
                    )}
                  </div>

                  {/* Segment */}
                  <p style={{ fontSize: 10, color: T.textSub, marginBottom: 10, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Users size={10} />
                    {c.segment} · <span style={{ fontWeight: 700, color: T.textPrim }}>{c.recipients.toLocaleString()}</span> recipients
                  </p>

                  {/* Stats bars */}
                  {hasStats && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 10 }}>
                      {[
                        { label: 'Open rate', value: c.openRate,       color: T.cyan,   max: 100 },
                        { label: 'Click rate', value: c.clickRate,     color: T.violet, max: 50 },
                        { label: 'Conversión', value: c.conversionRate, color: T.emerald, max: 30 },
                      ].map(stat => (
                        <div key={stat.label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontSize: 8, color: T.textSub, width: 56, flexShrink: 0, fontFamily: 'JetBrains Mono,monospace', textTransform: 'uppercase', letterSpacing: '.04em' }}>{stat.label}</span>
                          <div style={{ flex: 1, height: 6, background: T.border, borderRadius: 3, overflow: 'hidden' }}>
                            <div style={{ height: '100%', borderRadius: 3, background: stat.color, width: `${(stat.value / stat.max) * 100}%` }} />
                          </div>
                          <span style={{ fontSize: 10, fontWeight: 700, color: stat.color, fontVariantNumeric: 'tabular-nums', width: 30, textAlign: 'right', flexShrink: 0 }}>{stat.value}%</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* AI note */}
                  {c.aiNote && (
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 6, padding: '8px 12px', borderRadius: 10, background: T.violet + '08', border: '1px solid ' + T.violet + '20' }}>
                      <Bot size={12} style={{ color: T.violet, flexShrink: 0, marginTop: 1 }} />
                      <p style={{ fontSize: 10, color: T.violet, lineHeight: 1.4 }}>{c.aiNote}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Footer */}
      <div style={{ padding: '12px 20px', borderTop: '1px solid ' + T.border, background: T.bgApp, display: 'flex', alignItems: 'center', gap: 8 }}>
        <Activity size={12} style={{ color: T.emerald }} className="animate-pulse" />
        <span style={{ fontSize: 11, color: T.textSub }}>
          {stats.active} campañas activas generando <span style={{ color: T.emerald, fontWeight: 700, textShadow: T.glowEmerald }}>${stats.revenue.toLocaleString()}</span> de revenue automático
        </span>
      </div>
    </section>
  )
}
