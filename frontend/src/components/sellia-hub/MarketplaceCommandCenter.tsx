'use client'

/**
 * MARKETPLACE COMMAND CENTER
 *
 * IA opera 12 plataformas simultáneamente vía Computer Use:
 *   Amazon · Mercado Libre · Shopify · Hotmart · Instagram · IG Shop ·
 *   TikTok · TikTok Shop · Facebook · FB Shops · LinkedIn · Beacons · Linktree · custom page
 */

import { useState, useMemo, useEffect } from 'react'
import {
  ShoppingBag, Camera as Instagram, ShoppingCart, Globe, Link2, Award,
  Activity, Eye, Sparkles, ExternalLink, RefreshCw, AlertCircle,
  CheckCircle2, Pause, Bot, TrendingUp, Filter, Layers, Hash, Tv2
} from 'lucide-react'

// ── Design tokens ──────────────────────────────────────────────────────────────
const T = {
  bgApp:       '#0B0F19',
  bgCard:      '#151B2B',
  border:      '#2A3441',
  textPrim:    '#F3F4F6',
  textSub:     '#9CA3AF',
  cyan:        '#06B6D4',
  emerald:     '#10B981',
  amber:       '#F59E0B',
  glowCyan:    '0 0 22px rgba(6,182,212,0.50)',
  glowEmerald: '0 0 22px rgba(16,185,129,0.50)',
} as const

type PlatformCategory = 'marketplace' | 'social' | 'social-commerce' | 'bio-link' | 'custom'
type PlatformStatus = 'live' | 'syncing' | 'idle' | 'error'

interface Platform {
  id: string
  name: string
  emoji: string
  category: PlatformCategory
  brandColor: string
  status: PlatformStatus
  metric1: { label: string; value: string }
  metric2: { label: string; value: string }
  currentAction: string
  technique: string
  url: string
}

const PLATFORMS: Platform[] = [
  { id: 'amazon',   name: 'Amazon',         emoji: '📦', category: 'marketplace',       brandColor: '#FF9900', status: 'live',    metric1: { label: 'Órdenes hoy', value: '14' }, metric2: { label: 'ROAS', value: '4.2×' }, currentAction: 'Optimizando título + bullets de producto top', technique: 'A9 SEO + reviews mining', url: 'sellercentral.amazon.com' },
  { id: 'mercadolibre', name: 'Mercado Libre', emoji: '🟡', category: 'marketplace',    brandColor: '#FFE600', status: 'live',    metric1: { label: 'Ventas hoy', value: '8' },  metric2: { label: 'Preguntas', value: '23' }, currentAction: 'Respondiendo 4 preguntas pendientes', technique: 'Auto-respuesta + sales-trigger', url: 'mercadolibre.com.ar' },
  { id: 'shopify',  name: 'Shopify',        emoji: '🛍', category: 'marketplace',       brandColor: '#95BF47', status: 'live',    metric1: { label: 'Sesiones', value: '847' }, metric2: { label: 'Conv', value: '3.4%' }, currentAction: 'Recuperando 3 carritos abandonados', technique: 'Cart recovery secuencia', url: 'tienda.myshopify.com' },
  { id: 'hotmart',  name: 'Hotmart',        emoji: '🔥', category: 'marketplace',       brandColor: '#EF4E22', status: 'live',    metric1: { label: 'Ventas hoy', value: '5' },  metric2: { label: 'Comisión', value: '$890' }, currentAction: 'Configurando affiliate split en producto digital', technique: 'Affiliate optimization', url: 'app-vlc.hotmart.com' },
  { id: 'igshop',   name: 'IG Tienda',      emoji: '🌸', category: 'social-commerce',   brandColor: '#E1306C', status: 'syncing', metric1: { label: 'Catálogo', value: '47 prods' }, metric2: { label: 'Etiquetas', value: '12 posts' }, currentAction: 'Etiquetando productos en últimos 6 reels', technique: 'Product tagging auto', url: 'business.facebook.com/commerce' },
  { id: 'ttshop',   name: 'TikTok Shop',    emoji: '🎵', category: 'social-commerce',   brandColor: '#FF0050', status: 'live',    metric1: { label: 'Live shopping', value: 'AHORA' }, metric2: { label: 'Pedidos', value: '6' }, currentAction: 'Modero live shopping · 142 viewers', technique: 'Live commerce + pin product', url: 'seller-us.tiktok.com' },
  { id: 'fbshops',  name: 'FB Shops',       emoji: '🛒', category: 'social-commerce',   brandColor: '#1877F2', status: 'idle',    metric1: { label: 'Catálogo', value: '47 prods' }, metric2: { label: 'Clicks', value: '128' }, currentAction: 'Programada sincronización 22:00', technique: 'Catalog sync auto', url: 'business.facebook.com/shops' },
  { id: 'instagram', name: 'Instagram',     emoji: '📷', category: 'social',            brandColor: '#E4405F', status: 'live',    metric1: { label: 'Seguidores', value: '12.4k' }, metric2: { label: 'Engagement', value: '5.8%' }, currentAction: 'Posteando reel de oferta + responder 8 DMs', technique: 'Hashtag strategy + DM funnel', url: 'instagram.com/creator' },
  { id: 'tiktok',   name: 'TikTok',         emoji: '🎬', category: 'social',            brandColor: '#000000', status: 'live',    metric1: { label: 'Views/30d', value: '847k' }, metric2: { label: 'Followers', value: '+342' }, currentAction: 'Publicando video viral con trending sound', technique: 'Trending audio + CTA', url: 'tiktok.com/creator' },
  { id: 'facebook', name: 'Facebook',       emoji: '👍', category: 'social',            brandColor: '#1877F2', status: 'syncing', metric1: { label: 'Página', value: '8.2k fans' }, metric2: { label: 'Alcance', value: '23.4k' }, currentAction: 'Compartiendo en 3 grupos relevantes', technique: 'Group marketing orgánico', url: 'facebook.com/pages' },
  { id: 'linkedin', name: 'LinkedIn',       emoji: '💼', category: 'social',            brandColor: '#0A66C2', status: 'live',    metric1: { label: 'Conexiones', value: '+47/sem' }, metric2: { label: 'Views post', value: '4.8k' }, currentAction: 'Enviando 12 connection requests a ICP', technique: 'Targeted outreach B2B', url: 'linkedin.com/in/founder' },
  { id: 'beacons',  name: 'Beacons',        emoji: '🔗', category: 'bio-link',          brandColor: '#FFE066', status: 'live',    metric1: { label: 'Clicks hoy', value: '247' }, metric2: { label: 'CTR top', value: '34%' }, currentAction: 'A/B testing 2 versiones de hero', technique: 'Link-in-bio optimization', url: 'beacons.ai/marca' },
  { id: 'linktree', name: 'Linktree',       emoji: '🌳', category: 'bio-link',          brandColor: '#39E09B', status: 'idle',    metric1: { label: 'Visitas', value: '1.2k/sem' }, metric2: { label: 'CTR', value: '28%' }, currentAction: 'Backup activo · uso Beacons como primario', technique: 'Multi-platform redundancy', url: 'linktr.ee/marca' },
  { id: 'web',      name: 'Web propia',     emoji: '🌐', category: 'custom',            brandColor: '#06b6d4', status: 'live',    metric1: { label: 'Sesiones', value: '4.2k/día' }, metric2: { label: 'Conv', value: '2.8%' }, currentAction: 'SEO on-page · publicando artículo blog', technique: 'Content SEO + interlink', url: 'tudominio.com' },
]

const CATEGORY_CONFIG: Record<PlatformCategory, { label: string; emoji: string; color: string }> = {
  marketplace:        { label: 'Marketplaces',     emoji: '🛒', color: '#f59e0b' },
  'social-commerce':  { label: 'Social Commerce',  emoji: '🛍', color: '#ec4899' },
  social:             { label: 'Redes Sociales',   emoji: '📱', color: '#06b6d4' },
  'bio-link':         { label: 'Bio-Link',         emoji: '🔗', color: '#fbbf24' },
  custom:             { label: 'Tu propia web',    emoji: '🌐', color: '#a855f7' },
}

const STATUS_CONFIG: Record<PlatformStatus, { label: string; color: string }> = {
  live:    { label: '● LIVE',    color: '#22c55e' },
  syncing: { label: '◌ SYNC',    color: '#3b82f6' },
  idle:    { label: '⏸ IDLE',    color: '#9ca3af' },
  error:   { label: '⚠ ERROR',  color: '#ef4444' },
}

const card = (extra?: React.CSSProperties): React.CSSProperties => ({
  background: T.bgCard,
  border: `1px solid ${T.border}`,
  borderRadius: 16,
  ...extra,
})

export default function MarketplaceCommandCenter() {
  const [filter, setFilter] = useState<PlatformCategory | 'all'>('all')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [pulseTick, setPulseTick] = useState(0)

  useEffect(() => {
    const id = setInterval(() => setPulseTick(t => (t + 1) % 100), 500)
    return () => clearInterval(id)
  }, [])

  const filtered = useMemo(
    () => filter === 'all' ? PLATFORMS : PLATFORMS.filter(p => p.category === filter),
    [filter]
  )

  const stats = useMemo(() => {
    const live = PLATFORMS.filter(p => p.status === 'live').length
    const syncing = PLATFORMS.filter(p => p.status === 'syncing').length
    const totalConnected = PLATFORMS.filter(p => p.status !== 'error').length
    return { live, syncing, totalConnected, total: PLATFORMS.length }
  }, [])

  const categoryCounts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const p of PLATFORMS) c[p.category] = (c[p.category] || 0) + 1
    return c
  }, [])

  const selected = selectedId ? PLATFORMS.find(p => p.id === selectedId) : null

  return (
    <section style={{ background: T.bgApp, border: `1px solid ${T.border}`, borderRadius: 16, overflow: 'hidden', position: 'relative' }}>
      {/* Accent line */}
      <div style={{ height: 2, background: `linear-gradient(90deg, ${T.amber}, #f97316, transparent)` }} />

      {/* Header */}
      <div style={{ padding: '20px 24px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ position: 'relative', width: 40, height: 40, borderRadius: 12, background: 'rgba(245,158,11,0.15)', border: '1px solid rgba(245,158,11,0.35)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Layers style={{ width: 20, height: 20, color: T.amber, filter: 'drop-shadow(0 0 8px rgba(245,158,11,0.6))' }} />
            <div style={{ position: 'absolute', top: -4, right: -4, width: 12, height: 12, borderRadius: '50%', background: T.emerald, border: `2px solid ${T.bgApp}`, animation: 'pulse 2s infinite' }} />
          </div>
          <div>
            <h2 style={{ fontSize: 14, fontWeight: 900, color: T.textPrim, textTransform: 'uppercase', letterSpacing: '0.08em', margin: 0 }}>
              MARKETPLACE <span style={{ color: T.amber }}>COMMAND</span>
              <span style={{ color: T.textSub, fontWeight: 400, fontSize: 11, marginLeft: 8, textTransform: 'none', letterSpacing: 0 }}>· {PLATFORMS.length} plataformas en simultáneo</span>
              <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 999, background: 'rgba(16,185,129,0.15)', color: T.emerald, border: `1px solid rgba(16,185,129,0.30)`, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.1em', marginLeft: 8 }}>
                {stats.live}/{stats.total} LIVE
              </span>
            </h2>
            <p style={{ fontSize: 11, color: T.textSub, margin: '4px 0 0' }}>Computer Use orquesta Amazon, ML, Shopify, IG, TikTok, FB, LinkedIn y más — todo en paralelo</p>
          </div>
        </div>
        <button style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 16px', borderRadius: 999, background: 'rgba(245,158,11,0.12)', border: `1px solid rgba(245,158,11,0.35)`, color: T.amber, fontSize: 12, fontWeight: 700, cursor: 'pointer' }}>
          <Sparkles style={{ width: 12, height: 12 }} /> Conectar nueva plataforma
        </button>
      </div>

      {/* Category filter */}
      <div style={{ padding: '12px 24px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', gap: 8, overflowX: 'auto' }}>
        <Filter style={{ width: 12, height: 12, color: T.textSub, flexShrink: 0 }} />
        <button
          onClick={() => setFilter('all')}
          style={{ flexShrink: 0, padding: '4px 10px', borderRadius: 999, fontSize: 10, fontWeight: 700, cursor: 'pointer', background: filter === 'all' ? 'rgba(255,255,255,0.10)' : T.bgCard, border: filter === 'all' ? '1px solid rgba(255,255,255,0.20)' : `1px solid ${T.border}`, color: filter === 'all' ? T.textPrim : T.textSub }}>
          Todas · {PLATFORMS.length}
        </button>
        {(Object.keys(CATEGORY_CONFIG) as PlatformCategory[]).map(cat => {
          const cfg = CATEGORY_CONFIG[cat]
          const active = filter === cat
          const count = categoryCounts[cat] || 0
          return (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              style={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: 6, padding: '4px 10px', borderRadius: 999, fontSize: 10, fontWeight: 700, cursor: 'pointer', background: active ? `${cfg.color}20` : T.bgCard, border: active ? `1px solid ${cfg.color}50` : `1px solid ${T.border}`, color: active ? cfg.color : T.textSub }}
            >
              <span>{cfg.emoji}</span>
              {cfg.label} · {count}
            </button>
          )
        })}
      </div>

      {/* Platform grid */}
      <div style={{ padding: 20, display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>
        {filtered.map(p => {
          const status = STATUS_CONFIG[p.status]
          const isSelected = selectedId === p.id
          const barHeights = [3, 5, 4, 6, 5, 3, 7, 5, 4]
          return (
            <button
              key={p.id}
              onClick={() => setSelectedId(isSelected ? null : p.id)}
              style={{
                position: 'relative', background: T.bgCard, border: `1px solid ${isSelected ? `${p.brandColor}60` : T.border}`, borderRadius: 16,
                cursor: 'pointer', textAlign: 'left', overflow: 'hidden',
                boxShadow: p.status === 'live' ? `0 0 20px ${p.brandColor}12` : 'none',
                transition: 'transform 0.15s, box-shadow 0.15s',
              }}
            >
              {/* Brand accent bar */}
              <div style={{ height: 3, background: `linear-gradient(90deg, ${p.brandColor}, transparent)` }} />

              {/* Cockpit header */}
              <div style={{ padding: '10px 12px', borderBottom: `1px solid ${T.border}`, background: T.bgApp }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
                    <span style={{ fontSize: 22, flexShrink: 0 }}>{p.emoji}</span>
                    <div style={{ minWidth: 0 }}>
                      <p style={{ fontSize: 12, fontWeight: 700, color: T.textPrim, margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</p>
                      <p style={{ fontSize: 9, color: T.textSub, fontFamily: 'monospace', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.url}</p>
                    </div>
                  </div>
                  <span style={{ fontSize: 8, padding: '2px 6px', borderRadius: 5, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700, flexShrink: 0, background: `${status.color}20`, color: status.color }}>
                    {status.label}
                  </span>
                </div>
              </div>

              {/* Mini live preview bars */}
              <div style={{ padding: '8px 12px', background: T.bgApp }}>
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: 2, height: 24 }}>
                  {barHeights.map((h, i) => (
                    <div
                      key={i}
                      style={{
                        flex: 1, borderRadius: 2,
                        height: p.status === 'live' ? `${h * 3 + ((pulseTick + i) % 4)}px` : `${h * 2}px`,
                        background: p.status === 'live' ? p.brandColor : T.border,
                        opacity: p.status === 'live' ? 0.5 + ((pulseTick + i) % 5) * 0.1 : 0.3,
                      }}
                    />
                  ))}
                </div>
              </div>

              {/* Metrics */}
              <div style={{ padding: '8px 12px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <div>
                  <p style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.08em', color: T.textSub, fontFamily: 'monospace', margin: '0 0 2px' }}>{p.metric1.label}</p>
                  <p style={{ fontSize: 14, fontWeight: 900, color: T.textPrim, fontVariantNumeric: 'tabular-nums', margin: 0 }}>{p.metric1.value}</p>
                </div>
                <div>
                  <p style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.08em', color: T.textSub, fontFamily: 'monospace', margin: '0 0 2px' }}>{p.metric2.label}</p>
                  <p style={{ fontSize: 14, fontWeight: 900, fontVariantNumeric: 'tabular-nums', margin: 0, color: p.brandColor }}>{p.metric2.value}</p>
                </div>
              </div>

              {/* Current AI action */}
              <div style={{ padding: '8px 12px', borderTop: `1px solid ${T.border}` }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 6 }}>
                  {p.status === 'live' && <Bot style={{ width: 12, height: 12, color: T.emerald, flexShrink: 0, marginTop: 2, animation: 'pulse 2s infinite' }} />}
                  {p.status === 'syncing' && <RefreshCw style={{ width: 12, height: 12, color: '#3b82f6', flexShrink: 0, marginTop: 2, animation: 'spin 2s linear infinite' }} />}
                  {p.status === 'error' && <AlertCircle style={{ width: 12, height: 12, color: '#ef4444', flexShrink: 0, marginTop: 2 }} />}
                  {p.status === 'idle' && <Pause style={{ width: 12, height: 12, color: T.textSub, flexShrink: 0, marginTop: 2 }} />}
                  <p style={{ fontSize: 10, color: T.textSub, lineHeight: 1.4, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', flex: 1, margin: 0 }}>{p.currentAction}</p>
                </div>
              </div>
            </button>
          )
        })}
      </div>

      {/* Selected platform detail */}
      {selected && (
        <div style={{ margin: '0 20px 20px', padding: 20, borderRadius: 16, background: `${selected.brandColor}08`, border: `1px solid ${selected.brandColor}30`, boxShadow: `0 0 24px ${selected.brandColor}10` }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
            <div style={{ fontSize: 40, flexShrink: 0 }}>{selected.emoji}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
                <h3 style={{ fontSize: 18, fontWeight: 900, color: T.textPrim, margin: 0 }}>{selected.name}</h3>
                <span style={{ fontSize: 10, padding: '3px 8px', borderRadius: 6, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.06em', background: `${selected.brandColor}20`, color: selected.brandColor }}>
                  {CATEGORY_CONFIG[selected.category].label}
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 10, color: T.textSub, fontFamily: 'monospace' }}>
                  <ExternalLink style={{ width: 10, height: 10 }} />
                  {selected.url}
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
                {[
                  { label: 'Métrica clave', val: selected.metric1.value, sub: selected.metric1.label, color: T.textPrim },
                  { label: 'Performance',   val: selected.metric2.value, sub: selected.metric2.label, color: selected.brandColor },
                ].map((m, i) => (
                  <div key={i} style={{ padding: '12px 14px', borderRadius: 12, background: T.bgApp, border: `1px solid ${T.border}` }}>
                    <p style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.textSub, fontWeight: 700, margin: '0 0 4px' }}>{m.label}</p>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                      <span style={{ fontSize: 24, fontWeight: 900, color: m.color, fontVariantNumeric: 'tabular-nums' }}>{m.val}</span>
                      <span style={{ fontSize: 10, color: T.textSub }}>{m.sub.toLowerCase()}</span>
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ padding: '12px 14px', borderRadius: 12, background: 'rgba(16,185,129,0.05)', border: `1px solid rgba(16,185,129,0.22)` }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                  <Bot style={{ width: 12, height: 12, color: T.emerald }} />
                  <p style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.emerald, fontWeight: 700, margin: 0 }}>IA ESTÁ HACIENDO AHORA</p>
                </div>
                <p style={{ fontSize: 13, color: T.textPrim, margin: '0 0 6px' }}>{selected.currentAction}</p>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 8px', borderRadius: 6, background: 'rgba(168,85,247,0.15)', border: '1px solid rgba(168,85,247,0.28)', fontSize: 10, color: '#c084fc', fontFamily: 'monospace' }}>
                  <Sparkles style={{ width: 10, height: 10 }} />
                  Técnica: {selected.technique}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer stats */}
      <div style={{ padding: '12px 24px', borderTop: `1px solid ${T.border}`, background: 'rgba(0,0,0,0.15)', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, fontSize: 10, color: T.textSub }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: T.emerald, animation: 'pulse 2s infinite' }} />
          <span style={{ color: T.emerald, fontWeight: 700 }}>{stats.live} corriendo</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#3b82f6' }} />
          <span>{stats.syncing} sincronizando</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <CheckCircle2 style={{ width: 12, height: 12, color: T.emerald }} />
          <span>{stats.totalConnected}/{stats.total} conectadas</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
          <span>Computer Use orquesta todo en paralelo</span>
        </div>
      </div>
    </section>
  )
}
