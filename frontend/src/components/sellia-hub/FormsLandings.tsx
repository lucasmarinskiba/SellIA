'use client'

/**
 * FORMS + LANDING PAGES
 *
 * No-code builder · lead capture · split-tests · auto-publish a Vercel.
 */

import { useMemo, useState } from 'react'
import { FileText, Sparkles, Plus, Eye, Activity, MousePointer2, Bot, Edit3, ExternalLink, Globe } from 'lucide-react'

// ── Design tokens ──────────────────────────────────────────────────────────────
const T = {
  bgApp:       '#0B0F19',
  bgCard:      '#151B2B',
  bgCardHov:   '#1A2235',
  border:      '#2A3441',
  textPrim:    '#F3F4F6',
  textSub:     '#9CA3AF',
  cyan:        '#06B6D4',
  emerald:     '#10B981',
  amber:       '#F59E0B',
  glowCyan:    '0 0 22px rgba(6,182,212,0.50)',
  glowEmerald: '0 0 22px rgba(16,185,129,0.50)',
} as const

type AssetKind = 'form' | 'landing' | 'popup' | 'survey'

interface Asset {
  id: string
  emoji: string
  name: string
  kind: AssetKind
  url: string
  visits: number
  submissions: number
  convRate: number
  abVariant?: string
  aiNote?: string
  status: 'live' | 'draft' | 'paused'
  color: string
}

const ASSETS: Asset[] = [
  { id: 'a1', emoji: '📋', name: 'Contact form · home',                kind: 'form',     url: 'sellia.app/contact',                visits: 12400, submissions: 487, convRate: 3.9, status: 'live', color: '#06b6d4' },
  { id: 'a2', emoji: '🚀', name: 'Landing · Pack Premium oferta',      kind: 'landing',  url: 'sellia.app/pack-premium',           visits: 8400,  submissions: 287, convRate: 3.4, abVariant: 'B (hook gana 23%)', status: 'live', aiNote: 'A/B: variant B con hook urgencia gana · IA promovió a default', color: '#a855f7' },
  { id: 'a3', emoji: '🎯', name: 'Lead magnet · Ebook ventas IA',       kind: 'landing',  url: 'sellia.app/ebook',                  visits: 4847,  submissions: 1247,convRate: 25.7, status: 'live', aiNote: 'Conv >25% · IA replicó estructura en 2 landings nuevas', color: '#22c55e' },
  { id: 'a4', emoji: '⏱', name: 'Exit-intent popup · 10% off',          kind: 'popup',    url: 'sellia.app/* (global)',             visits: 18400, submissions: 847, convRate: 4.6, status: 'live', color: '#fbbf24' },
  { id: 'a5', emoji: '📊', name: 'Encuesta NPS post-compra',             kind: 'survey',   url: 'sellia.app/nps/{order_id}',         visits: 1247,  submissions: 894, convRate: 71.7, status: 'live', color: '#ec4899' },
  { id: 'a6', emoji: '🏠', name: 'Landing · pricing tiers',             kind: 'landing',  url: 'sellia.app/pricing',                visits: 6400,  submissions: 124, convRate: 1.9, abVariant: 'A · B · C testing', status: 'live', aiNote: 'CTR bajo · IA sugiere reducir tiers de 4→3 + social proof', color: '#3b82f6' },
  { id: 'a7', emoji: '📝', name: 'Booking form · demo call',             kind: 'form',     url: 'sellia.app/book-demo',              visits: 2840,  submissions: 412, convRate: 14.5, status: 'live', color: '#10b981' },
  { id: 'a8', emoji: '🎁', name: 'Black Friday landing',                  kind: 'landing',  url: '— (draft)',                          visits: 0,     submissions: 0,   convRate: 0,    status: 'draft', aiNote: 'IA está generando 3 variantes con copy + diseño', color: '#f97316' },
]

const KIND_CONFIG: Record<AssetKind, { label: string; color: string }> = {
  form:    { label: 'Form',    color: '#06b6d4' },
  landing: { label: 'Landing', color: '#a855f7' },
  popup:   { label: 'Popup',   color: '#fbbf24' },
  survey:  { label: 'Survey',  color: '#ec4899' },
}

const card = (extra?: React.CSSProperties): React.CSSProperties => ({
  background: T.bgCard,
  border: `1px solid ${T.border}`,
  borderRadius: 16,
  ...extra,
})

export default function FormsLandings() {
  const [filter, setFilter] = useState<AssetKind | 'all'>('all')

  const filtered = useMemo(() => filter === 'all' ? ASSETS : ASSETS.filter(a => a.kind === filter), [filter])

  const stats = useMemo(() => ({
    total: ASSETS.length,
    visits: ASSETS.reduce((s, a) => s + a.visits, 0),
    submissions: ASSETS.reduce((s, a) => s + a.submissions, 0),
    avgConv: Math.round(ASSETS.filter(a => a.convRate > 0).reduce((s, a) => s + a.convRate, 0) / ASSETS.filter(a => a.convRate > 0).length * 10) / 10,
  }), [])

  return (
    <section style={{ background: T.bgApp, border: `1px solid ${T.border}`, borderRadius: 16, overflow: 'hidden', position: 'relative' }}>
      {/* Accent line */}
      <div style={{ height: 2, background: `linear-gradient(90deg, ${T.cyan}, transparent)` }} />

      {/* Header */}
      <div style={{ padding: '20px 24px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, background: 'rgba(6,182,212,0.12)', border: `1px solid rgba(6,182,212,0.30)`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <FileText style={{ width: 20, height: 20, color: T.cyan }} />
          </div>
          <div>
            <h2 style={{ fontSize: 14, fontWeight: 900, color: T.textPrim, textTransform: 'uppercase', letterSpacing: '0.08em', margin: 0 }}>
              FORMS <span style={{ color: T.cyan }}>+</span> LANDINGS
              <span style={{ color: T.textSub, fontWeight: 400, fontSize: 11, marginLeft: 8, textTransform: 'none', letterSpacing: 0 }}>· No-code builder · A/B · IA copywriter</span>
            </h2>
            <p style={{ fontSize: 11, color: T.textSub, margin: '4px 0 0' }}>{stats.total} assets · {(stats.visits / 1000).toFixed(1)}k visitas · {stats.submissions.toLocaleString()} submissions · <span style={{ color: T.emerald, fontWeight: 700 }}>{stats.avgConv}% conv avg</span></p>
          </div>
        </div>
        <button style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 16px', borderRadius: 999, background: 'rgba(6,182,212,0.12)', border: `1px solid rgba(6,182,212,0.35)`, color: T.cyan, fontSize: 12, fontWeight: 700, cursor: 'pointer' }}>
          <Plus style={{ width: 14, height: 14 }} /> Nuevo asset
        </button>
      </div>

      {/* Filter chips */}
      <div style={{ padding: '12px 24px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        {(['all', ...Object.keys(KIND_CONFIG)] as const).map(k => {
          const cfg = k === 'all' ? null : KIND_CONFIG[k as AssetKind]
          const c = k === 'all' ? ASSETS.length : ASSETS.filter(a => a.kind === k).length
          const active = filter === k
          return (
            <button key={k} onClick={() => setFilter(k as AssetKind | 'all')}
              style={{
                fontSize: 10, padding: '4px 10px', borderRadius: 999, fontWeight: 700, textTransform: 'uppercase', cursor: 'pointer',
                background: active ? (cfg ? `${cfg.color}20` : 'rgba(255,255,255,0.10)') : `${T.bgCard}`,
                border: active ? `1px solid ${cfg ? `${cfg.color}50` : 'rgba(255,255,255,0.2)'}` : `1px solid ${T.border}`,
                color: active ? (cfg ? cfg.color : T.textPrim) : T.textSub,
              }}>
              {k === 'all' ? 'Todos' : cfg?.label} · {c}
            </button>
          )
        })}
      </div>

      {/* Asset grid */}
      <div style={{ padding: 20, display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
        {filtered.map(a => {
          const kind = KIND_CONFIG[a.kind]
          const convColor = a.convRate > 20 ? T.emerald : a.convRate > 5 ? T.amber : '#ef4444'
          const convGlow = a.convRate > 20 ? T.glowEmerald : a.convRate > 5 ? '0 0 16px rgba(245,158,11,0.45)' : '0 0 16px rgba(239,68,68,0.45)'
          return (
            <div key={a.id} style={{ ...card(), overflow: 'hidden', opacity: a.status === 'draft' ? 0.75 : 1 }}>
              {/* Accent line */}
              <div style={{ height: 2, background: `linear-gradient(90deg, ${a.color}, transparent)` }} />

              <div style={{ padding: 20 }}>
                {/* Header */}
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 16 }}>
                  <span style={{ fontSize: 24, flexShrink: 0 }}>{a.emoji}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 6 }}>
                      <p style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{a.name}</p>
                      <span style={{ fontSize: 9, padding: '3px 7px', borderRadius: 6, fontWeight: 700, textTransform: 'uppercase', background: `${kind.color}18`, color: kind.color, border: `1px solid ${kind.color}30` }}>{kind.label}</span>
                      {a.status === 'draft' && <span style={{ fontSize: 9, padding: '3px 7px', borderRadius: 6, background: `${T.bgApp}`, color: T.textSub, fontWeight: 700, textTransform: 'uppercase', border: `1px solid ${T.border}` }}>DRAFT</span>}
                      {a.abVariant && <span style={{ fontSize: 9, padding: '3px 7px', borderRadius: 6, background: 'rgba(168,85,247,0.15)', color: '#c084fc', fontWeight: 700, border: '1px solid rgba(168,85,247,0.28)' }}>A/B</span>}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Globe style={{ width: 10, height: 10, color: T.textSub, flexShrink: 0 }} />
                      <code style={{ fontSize: 9, color: T.textSub, fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{a.url}</code>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 4, flexShrink: 0 }}>
                    <button style={{ padding: 6, borderRadius: 8, background: 'transparent', border: `1px solid ${T.border}`, color: T.textSub, cursor: 'pointer' }}><Eye style={{ width: 12, height: 12 }} /></button>
                    <button style={{ padding: 6, borderRadius: 8, background: 'transparent', border: `1px solid ${T.border}`, color: T.textSub, cursor: 'pointer' }}><Edit3 style={{ width: 12, height: 12 }} /></button>
                  </div>
                </div>

                {/* Metrics */}
                {a.status === 'live' && a.visits > 0 && (
                  <div style={{ marginBottom: 12 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
                        <div style={{ textAlign: 'center' }}>
                          <p style={{ fontSize: 10, color: T.textSub, textTransform: 'uppercase', letterSpacing: '0.06em', margin: 0 }}>Visitas</p>
                          <p style={{ fontSize: 18, fontWeight: 900, color: T.textPrim, fontVariantNumeric: 'tabular-nums', margin: 0 }}>{a.visits >= 1000 ? `${(a.visits/1000).toFixed(1)}k` : a.visits}</p>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                          <p style={{ fontSize: 10, color: T.textSub, textTransform: 'uppercase', letterSpacing: '0.06em', margin: 0 }}>Leads</p>
                          <p style={{ fontSize: 18, fontWeight: 900, color: T.textPrim, fontVariantNumeric: 'tabular-nums', margin: 0 }}>{a.submissions >= 1000 ? `${(a.submissions/1000).toFixed(1)}k` : a.submissions}</p>
                        </div>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <p style={{ fontSize: 10, color: T.textSub, textTransform: 'uppercase', letterSpacing: '0.06em', margin: 0 }}>Conv.</p>
                        <p style={{ fontSize: 28, fontWeight: 900, fontVariantNumeric: 'tabular-nums', lineHeight: 1, margin: 0, color: convColor, textShadow: convGlow }}>{a.convRate}%</p>
                      </div>
                    </div>
                    <div style={{ height: 5, background: T.bgApp, borderRadius: 999, overflow: 'hidden' }}>
                      <div style={{ height: '100%', borderRadius: 999, width: `${Math.min(a.convRate * 3, 100)}%`, background: convColor, boxShadow: `0 0 8px ${convColor}` }} />
                    </div>
                  </div>
                )}

                {a.abVariant && (
                  <p style={{ fontSize: 11, color: '#c084fc', marginBottom: 8 }}>🅰️🅱️ {a.abVariant}</p>
                )}

                {a.aiNote && (
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, padding: '10px 12px', borderRadius: 10, background: 'rgba(6,182,212,0.06)', border: `1px solid rgba(6,182,212,0.20)` }}>
                    <Bot style={{ width: 12, height: 12, color: T.cyan, flexShrink: 0, marginTop: 2 }} />
                    <p style={{ fontSize: 11, color: T.cyan, lineHeight: 1.4, margin: 0 }}>{a.aiNote}</p>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Footer */}
      <div style={{ borderTop: `1px solid ${T.border}`, padding: '14px 24px', background: 'rgba(6,182,212,0.03)' }}>
        <p style={{ fontSize: 11, color: T.textSub, margin: 0 }}>
          <Sparkles style={{ width: 12, height: 12, display: 'inline', color: T.cyan, marginRight: 6 }} />
          IA genera variants, copy y diseño · publish 1-click a Vercel · A/B con split-traffic 50/50 · gana variant promueve automático.
        </p>
      </div>
    </section>
  )
}
