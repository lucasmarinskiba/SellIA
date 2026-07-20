'use client'

/**
 * ADS COCKPIT — Design System 2026
 * Tokens: #0B0F19 app · #151B2B cards · #2A3441 borders
 * Accent: #06B6D4 cyan · #10B981 emerald · text-shadow glow
 */

import { useState, useMemo, useCallback } from 'react'
import {
  Megaphone, TrendingUp, Eye, DollarSign, MousePointer2,
  Target, Sparkles, Bot, CheckCircle2, Users,
  ArrowUpRight, ArrowDownRight, Minus, ChevronRight
} from 'lucide-react'

// ── Design tokens ──────────────────────────────────────────────────────────────
const T = {
  bgApp:     '#0B0F19',
  bgCard:    '#151B2B',
  bgCardHov: '#1A2235',
  border:    '#2A3441',
  textPrim:  '#F3F4F6',
  textSub:   '#9CA3AF',
  cyan:      '#06B6D4',
  emerald:   '#10B981',
  amber:     '#F59E0B',
  glowCyan:    '0 0 22px rgba(6,182,212,0.50)',
  glowEmerald: '0 0 22px rgba(16,185,129,0.50)',
  glowAmber:   '0 0 22px rgba(245,158,11,0.45)',
} as const

type AdPlatform    = 'meta' | 'google' | 'tiktok'
type CampaignStatus = 'active' | 'optimizing' | 'paused' | 'learning'
type BudgetMode    = 'daily' | 'monthly'
type ConvPeriod    = 'daily' | 'weekly' | 'monthly'

interface Campaign {
  id: string; platform: AdPlatform; name: string; status: CampaignStatus
  budgetSpent: number; budgetTotal: number
  impressions: number; reach: number; clicks: number; conversions: number
  ctr: number; cpc: number; roas: number; trend: 'up' | 'down' | 'flat'
  aiRec?: string
}

const BASE: Campaign[] = [
  { id: 'm1', platform: 'meta',   name: 'Pack Premium · Conversiones',  status: 'active',     budgetSpent: 142, budgetTotal: 200, impressions: 28400, reach: 21300, clicks: 847,  conversions: 23, ctr: 2.98, cpc: 0.17, roas: 4.3, trend: 'up',   aiRec: 'Escalar +30% · lookalike ROAS 4.3×' },
  { id: 'm2', platform: 'meta',   name: 'Retargeting · Carrito',         status: 'optimizing', budgetSpent: 48,  budgetTotal: 80,  impressions: 12800, reach: 9600,  clicks: 412,  conversions: 8,  ctr: 3.22, cpc: 0.12, roas: 5.1, trend: 'up' },
  { id: 'm3', platform: 'meta',   name: 'Brand Awareness',               status: 'learning',   budgetSpent: 22,  budgetTotal: 50,  impressions: 18200, reach: 14560, clicks: 234,  conversions: 3,  ctr: 1.28, cpc: 0.09, roas: 1.2, trend: 'flat', aiRec: 'Esperá 3 días · learning phase' },
  { id: 'g1', platform: 'google', name: 'Search "agente IA ventas"',     status: 'active',     budgetSpent: 89,  budgetTotal: 150, impressions: 8400,  reach: 7980,  clicks: 287,  conversions: 12, ctr: 3.42, cpc: 0.31, roas: 3.8, trend: 'up',   aiRec: '+8 keywords negativas · limpiar tráfico' },
  { id: 'g2', platform: 'google', name: 'Performance Max · Tienda',      status: 'active',     budgetSpent: 124, budgetTotal: 180, impressions: 42100, reach: 36890, clicks: 1124, conversions: 31, ctr: 2.67, cpc: 0.11, roas: 5.2, trend: 'up' },
  { id: 'g3', platform: 'google', name: 'Display · Remarketing',         status: 'paused',     budgetSpent: 18,  budgetTotal: 50,  impressions: 23400, reach: 21060, clicks: 142,  conversions: 2,  ctr: 0.61, cpc: 0.13, roas: 0.8, trend: 'down', aiRec: 'CTR crítico · reasignar a TikTok' },
  { id: 't1', platform: 'tiktok', name: 'Viral hook · Demo producto',    status: 'active',     budgetSpent: 67,  budgetTotal: 100, impressions: 84200, reach: 71570, clicks: 1842, conversions: 18, ctr: 2.19, cpc: 0.04, roas: 4.7, trend: 'up',   aiRec: 'Spark Ads post orgánico viral' },
  { id: 't2', platform: 'tiktok', name: 'Conversiones · Curso online',   status: 'optimizing', budgetSpent: 42,  budgetTotal: 80,  impressions: 28400, reach: 24140, clicks: 412,  conversions: 6,  ctr: 1.45, cpc: 0.10, roas: 2.8, trend: 'flat' },
]

const PLAT = {
  meta:   { label: 'Meta',   sym: '◼', color: '#4F87FF' },
  google: { label: 'Google', sym: 'G',  color: '#34D399' },
  tiktok: { label: 'TikTok', sym: '♪', color: '#FF375F' },
} as const

const STATUS_CONF = {
  active:     { label: 'LIVE',   color: '#10B981' },
  optimizing: { label: 'OPTIM',  color: '#06B6D4' },
  paused:     { label: 'PAUSA',  color: '#6B7280' },
  learning:   { label: 'LEARN',  color: '#A78BFA' },
} as const

interface Sug { id: string; emoji: string; label: string; color: string; campaignId: string; mutation: Partial<Campaign> }
const SUGS: Sug[] = [
  { id: 's1', emoji: '🚀', label: 'Escalar Pack +30%', color: '#10B981', campaignId: 'm1', mutation: { budgetTotal: 260 } },
  { id: 's2', emoji: '💸', label: 'Pausar Display',     color: '#F59E0B', campaignId: 'g3', mutation: { status: 'paused' as CampaignStatus, budgetTotal: 30 } },
  { id: 's3', emoji: '⚡', label: 'Boost TikTok +$40', color: '#A78BFA', campaignId: 't1', mutation: { budgetTotal: 140 } },
]

const CM: Record<ConvPeriod, number> = { daily: 1, weekly: 7, monthly: 30 }
const fn = (n: number) => n >= 10000 ? `${(n / 1000).toFixed(0)}k` : n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n)

// ── Sparkline SVG ──────────────────────────────────────────────────────────────
const Spark = ({ vals, color }: { vals: number[]; color: string }) => {
  if (vals.length < 2) return null
  const mx = Math.max(...vals), mn = Math.min(...vals), rng = mx - mn || 1
  const W = 60, H = 24
  const pts = vals.map((v, i) => `${(i / (vals.length - 1)) * W},${H - ((v - mn) / rng) * (H - 4) - 2}`).join(' ')
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" opacity={0.8} />
      <circle
        cx={(vals.length - 1) / (vals.length - 1) * W}
        cy={H - ((vals[vals.length - 1] - mn) / rng) * (H - 4) - 2}
        r="2.5" fill={color}
      />
    </svg>
  )
}

// ── Budget arc SVG ─────────────────────────────────────────────────────────────
const BudgetArc = ({ pct, color }: { pct: number; color: string }) => {
  const r = 26, cx = 32, cy = 32
  const circ = 2 * Math.PI * r
  const dash = (Math.min(pct, 100) / 100) * circ
  return (
    <svg width={64} height={64} viewBox="0 0 64 64" style={{ transform: 'rotate(-90deg)' }}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={T.border} strokeWidth={6} />
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth={6}
        strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
        style={{ filter: `drop-shadow(0 0 6px ${color})` }} />
    </svg>
  )
}

// ── Card style helper ──────────────────────────────────────────────────────────
const card = (extra?: React.CSSProperties): React.CSSProperties => ({
  background: T.bgCard,
  border: `1px solid ${T.border}`,
  borderRadius: 16,
  ...extra,
})

export default function AdsCockpit() {
  const [plat,  setPlat]  = useState<AdPlatform | 'all'>('all')
  const [bMode, setBMode] = useState<BudgetMode>('daily')
  const [cPer,  setCPer]  = useState<ConvPeriod>('daily')
  const [expId, setExpId] = useState<string | null>(null)
  const [camps, setCamps] = useState<Campaign[]>(BASE)
  const [done,  setDone]  = useState<Set<string>>(new Set())
  const [flash, setFlash] = useState(false)

  const bm = bMode === 'monthly' ? 30 : 1
  const cm = CM[cPer]

  const view = useMemo(
    () => plat === 'all' ? camps : camps.filter(c => c.platform === plat),
    [plat, camps]
  )

  const totals = useMemo(() => {
    const d = view
    const spent  = d.reduce((s, c) => s + c.budgetSpent, 0) * bm
    const budget = d.reduce((s, c) => s + c.budgetTotal, 0) * bm
    const impr   = d.reduce((s, c) => s + c.impressions, 0) * bm
    const reach  = d.reduce((s, c) => s + c.reach, 0) * bm
    const clicks = d.reduce((s, c) => s + c.clicks, 0) * bm
    const conv   = d.reduce((s, c) => s + c.conversions, 0) * cm
    const roas   = d.length ? d.reduce((s, c) => s + c.roas, 0) / d.length : 0
    const ctr    = impr ? clicks / impr * 100 : 0
    const roi    = spent ? (roas * spent - spent) / spent * 100 : 0
    return { spent, budget, impr, reach, clicks, conv, roas, ctr, roi, bpct: budget ? spent / budget * 100 : 0 }
  }, [view, bm, cm])

  const pStats = useMemo(() => {
    const r = { meta: { s: 0, roas: 0, n: 0 }, google: { s: 0, roas: 0, n: 0 }, tiktok: { s: 0, roas: 0, n: 0 } } as Record<AdPlatform, { s: number; roas: number; n: number }>
    for (const c of camps) { r[c.platform].s += c.budgetSpent * bm; r[c.platform].roas += c.roas; r[c.platform].n++ }
    for (const k of ['meta', 'google', 'tiktok'] as AdPlatform[]) if (r[k].n) r[k].roas /= r[k].n
    return r
  }, [camps, bm])

  const apply = useCallback((sid: string) => {
    const sg = SUGS.find(x => x.id === sid); if (!sg || done.has(sid)) return
    setCamps(p => p.map(c => c.id === sg.campaignId ? { ...c, ...sg.mutation } : c))
    setDone(p => new Set([...p, sid]))
  }, [done])

  const applyAll = useCallback(() => {
    setCamps(p => { let u = [...p]; for (const sg of SUGS) u = u.map(c => c.id === sg.campaignId ? { ...c, ...sg.mutation } : c); return u })
    setDone(new Set(SUGS.map(s => s.id))); setFlash(true); setTimeout(() => setFlash(false), 2500)
  }, [])

  const activeColor = plat !== 'all' ? PLAT[plat].color : T.cyan
  const sparkVals = [2.1, 2.8, 3.1, 3.4, 3.5, totals.roas]

  return (
    <section style={{ background: T.bgApp, borderRadius: 20, border: `1px solid ${T.border}`, overflow: 'hidden' }}>

      {/* ── Top accent ──────────────────────────────────────────────── */}
      <div style={{ height: 2, background: `linear-gradient(90deg, transparent, ${activeColor}, transparent)`, transition: 'all 0.4s' }} />

      {/* ── Header ──────────────────────────────────────────────────── */}
      <div style={{ padding: '16px 24px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>

        {/* Logo + title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ ...card(), width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 10, flexShrink: 0 }}>
            <Megaphone style={{ width: 18, height: 18, color: activeColor, filter: `drop-shadow(${T.glowCyan})`, transition: 'color 0.3s' }} />
          </div>
          <div>
            <p style={{ color: T.textPrim, fontWeight: 900, fontSize: 15, letterSpacing: '-0.3px', lineHeight: 1 }}>Ads Cockpit</p>
            <p style={{ color: T.textSub, fontSize: 10, marginTop: 2 }}>Meta · Google · TikTok · live</p>
          </div>
        </div>

        {/* Platform pills */}
        <div style={{ display: 'flex', gap: 6, marginLeft: 8 }}>
          {(['all', 'meta', 'google', 'tiktok'] as const).map(p => {
            const cfg = p !== 'all' ? PLAT[p] : null
            const ps  = p !== 'all' ? pStats[p] : null
            const act = plat === p
            return (
              <button key={p} onClick={() => setPlat(p)}
                style={{
                  padding: '6px 14px', borderRadius: 999, fontSize: 10, fontWeight: 700, cursor: 'pointer',
                  border: `1px solid ${act ? (cfg?.color ?? T.cyan) : T.border}`,
                  background: act ? `${cfg?.color ?? T.cyan}18` : T.bgCard,
                  color: act ? (cfg?.color ?? T.textPrim) : T.textSub,
                  boxShadow: act ? `0 0 12px ${cfg?.color ?? T.cyan}30` : 'none',
                  transition: 'all 0.2s',
                  display: 'flex', alignItems: 'center', gap: 5,
                }}>
                {cfg && <span>{cfg.sym}</span>}
                {p === 'all' ? `All · ${camps.length}` : cfg!.label}
                {act && ps && <span style={{ opacity: 0.6, fontFamily: 'monospace' }}>{ps.roas.toFixed(1)}×</span>}
              </button>
            )
          })}
        </div>

        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}>
          {/* Budget mode */}
          <div style={{ display: 'flex', padding: 3, borderRadius: 999, background: T.bgCard, border: `1px solid ${T.border}` }}>
            {(['daily', 'monthly'] as BudgetMode[]).map(m => (
              <button key={m} onClick={() => setBMode(m)}
                style={{
                  padding: '4px 12px', borderRadius: 999, fontSize: 10, fontWeight: 700, cursor: 'pointer', border: 'none',
                  background: bMode === m ? activeColor : 'transparent',
                  color: bMode === m ? '#000' : T.textSub,
                  transition: 'all 0.2s',
                }}>
                {m === 'daily' ? 'Diario' : 'Mensual'}
              </button>
            ))}
          </div>
          {/* Spend display */}
          <div style={{ ...card(), padding: '6px 14px', display: 'flex', alignItems: 'baseline', gap: 4 }}>
            <span style={{ color: T.textPrim, fontWeight: 900, fontSize: 13, fontFamily: 'monospace' }}>${totals.spent.toLocaleString()}</span>
            <span style={{ color: T.textSub, fontSize: 10 }}>/ ${totals.budget.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* ── Bento hero grid ─────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.4fr 0.9fr', gap: 16, padding: 20 }}>

        {/* ROAS hero */}
        <div style={{ ...card({ padding: 24, position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: 160 }) }}>
          <div style={{ position: 'absolute', top: -40, right: -40, width: 160, height: 160, borderRadius: '50%', background: `radial-gradient(circle, ${T.cyan}18, transparent 65%)`, pointerEvents: 'none' }} />
          <div>
            <p style={{ color: T.textSub, fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.18em', fontWeight: 700 }}>ROAS PROMEDIO</p>
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, marginTop: 8 }}>
              <span style={{ color: T.cyan, fontSize: 52, fontWeight: 900, lineHeight: 1, fontFamily: 'monospace', textShadow: T.glowCyan }}>
                {totals.roas.toFixed(1)}
              </span>
              <span style={{ color: T.cyan, fontSize: 22, fontWeight: 300, marginBottom: 6, opacity: 0.7 }}>×</span>
            </div>
            <p style={{ color: T.textSub, fontSize: 10, marginTop: 4 }}>retorno × inversión</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginTop: 16 }}>
            <Spark vals={sparkVals} color={T.cyan} />
            <div style={{ textAlign: 'right' }}>
              <p style={{ color: T.textSub, fontSize: 9, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em' }}>ROI</p>
              <p style={{ color: T.cyan, fontSize: 18, fontWeight: 900, fontFamily: 'monospace', textShadow: T.glowCyan }}>{totals.roi.toFixed(0)}%</p>
            </div>
          </div>
        </div>

        {/* Spend + micro-stats */}
        <div style={{ ...card({ padding: 24, display: 'flex', flexDirection: 'column', gap: 20 }) }}>
          {/* Spend */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{ position: 'relative', flexShrink: 0 }}>
              <BudgetArc pct={totals.bpct} color={activeColor} />
              <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ color: T.textPrim, fontSize: 10, fontWeight: 900, fontFamily: 'monospace' }}>{totals.bpct.toFixed(0)}%</span>
              </div>
            </div>
            <div>
              <p style={{ color: T.textSub, fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.18em', fontWeight: 700 }}>
                {bMode === 'daily' ? 'GASTADO HOY' : 'GASTADO MES'}
              </p>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginTop: 6 }}>
                <span style={{ color: T.textPrim, fontSize: 28, fontWeight: 900, lineHeight: 1, fontFamily: 'monospace' }}>${totals.spent.toLocaleString()}</span>
                <span style={{ color: T.textSub, fontSize: 12 }}>/ ${totals.budget.toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* 4 micro stats */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            {[
              { icon: Eye,           v: fn(totals.impr),   l: 'Impresiones',  c: '#A78BFA' },
              { icon: Users,         v: fn(totals.reach),  l: 'Alcance real', c: T.cyan    },
              { icon: MousePointer2, v: fn(totals.clicks), l: `CTR ${totals.ctr.toFixed(1)}%`, c: '#F472B6' },
              { icon: Target,        v: fn(totals.clicks), l: 'Clicks totales', c: T.emerald },
            ].map(s => {
              const Icon = s.icon
              return (
                <div key={s.l} style={{ background: T.bgApp, border: `1px solid ${T.border}`, borderRadius: 12, padding: '12px 14px', display: 'flex', alignItems: 'center', gap: 10 }}>
                  <Icon style={{ width: 14, height: 14, color: s.c, flexShrink: 0 }} />
                  <div>
                    <p style={{ color: T.textPrim, fontSize: 13, fontWeight: 900, lineHeight: 1, fontFamily: 'monospace' }}>{s.v}</p>
                    <p style={{ color: T.textSub, fontSize: 9, marginTop: 3 }}>{s.l}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Conversions */}
        <div style={{ ...card({ padding: 24, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', position: 'relative', overflow: 'hidden' }) }}>
          <div style={{ position: 'absolute', bottom: -30, right: -30, width: 120, height: 120, borderRadius: '50%', background: `radial-gradient(circle, ${T.emerald}18, transparent 65%)`, pointerEvents: 'none' }} />
          <div>
            <p style={{ color: T.textSub, fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.18em', fontWeight: 700 }}>CONVERSIONES</p>
            <p style={{ color: T.emerald, fontSize: 46, fontWeight: 900, lineHeight: 1, marginTop: 8, fontFamily: 'monospace', textShadow: T.glowEmerald }}>
              {totals.conv.toLocaleString()}
            </p>
            <p style={{ color: T.textSub, fontSize: 10, marginTop: 4 }}>{cPer === 'daily' ? 'hoy' : cPer === 'weekly' ? 'esta semana' : 'este mes'}</p>
          </div>
          <div>
            <p style={{ color: T.textSub, fontSize: 9, marginBottom: 8 }}>Período:</p>
            <div style={{ display: 'flex', gap: 6 }}>
              {(['daily', 'weekly', 'monthly'] as ConvPeriod[]).map(pd => (
                <button key={pd} onClick={() => setCPer(pd)}
                  style={{
                    flex: 1, padding: '6px 0', borderRadius: 10, fontSize: 9, fontWeight: 700, cursor: 'pointer', textAlign: 'center',
                    border: `1px solid ${cPer === pd ? T.emerald : T.border}`,
                    background: cPer === pd ? `${T.emerald}18` : T.bgApp,
                    color: cPer === pd ? T.emerald : T.textSub,
                    transition: 'all 0.2s',
                  }}>
                  {pd === 'daily' ? 'D' : pd === 'weekly' ? 'S' : 'M'}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Campaign table ──────────────────────────────────────────── */}
      <div style={{ padding: '0 20px 20px' }}>
        <p style={{ color: T.textSub, fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.18em', fontWeight: 700, marginBottom: 12 }}>
          CAMPAÑAS · {view.length} seleccionadas
        </p>

        <div style={{ ...card({ overflow: 'hidden', padding: 0 }) }}>
          {view.map((c, i) => {
            const pl   = PLAT[c.platform]
            const st   = STATUS_CONF[c.status]
            const bpct = c.budgetSpent / c.budgetTotal * 100
            const rc   = c.roas < 1.5 ? '#F87171' : c.roas >= 3.5 ? T.emerald : T.amber
            const isExp = expId === c.id

            return (
              <div key={c.id}>
                <div
                  onClick={() => setExpId(isExp ? null : c.id)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 14, padding: '14px 20px', cursor: 'pointer',
                    background: isExp ? `${pl.color}0a` : 'transparent',
                    transition: 'background 0.15s',
                  }}
                >
                  {/* Left stripe */}
                  <div style={{ width: 3, height: 36, borderRadius: 99, background: pl.color, flexShrink: 0, boxShadow: `0 0 8px ${pl.color}70`, opacity: c.status === 'paused' ? 0.3 : 1 }} />

                  {/* Platform badge */}
                  <div style={{ width: 28, height: 28, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 900, flexShrink: 0, background: `${pl.color}20`, color: pl.color }}>
                    {pl.sym}
                  </div>

                  {/* Name + status */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <p style={{ color: T.textPrim, fontSize: 12, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.name}</p>
                      <span style={{ padding: '2px 7px', borderRadius: 6, fontSize: 8, fontWeight: 700, textTransform: 'uppercase', flexShrink: 0, background: `${st.color}18`, color: st.color }}>
                        {st.label}
                      </span>
                    </div>
                    <p style={{ color: T.textSub, fontSize: 9, marginTop: 2 }}>{pl.label} · CPC ${c.cpc.toFixed(2)}</p>
                  </div>

                  {/* Metrics */}
                  <div style={{ display: 'flex', gap: 20, flexShrink: 0 }}>
                    {[
                      { v: fn(c.impressions * bm), l: 'impr'   },
                      { v: fn(c.clicks * bm),      l: 'clicks' },
                      { v: `${c.ctr}%`,            l: 'CTR'    },
                      { v: String(c.conversions * cm), l: 'conv' },
                    ].map(s => (
                      <div key={s.l} style={{ textAlign: 'center', minWidth: 40 }}>
                        <p style={{ color: T.textPrim, fontSize: 12, fontWeight: 700, fontFamily: 'monospace', lineHeight: 1 }}>{s.v}</p>
                        <p style={{ color: T.textSub, fontSize: 8, marginTop: 3, textTransform: 'uppercase' }}>{s.l}</p>
                      </div>
                    ))}
                  </div>

                  {/* Budget bar */}
                  <div style={{ width: 56, flexShrink: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ color: T.textSub, fontSize: 8, fontFamily: 'monospace' }}>${c.budgetSpent * bm}</span>
                      <span style={{ color: T.textSub, fontSize: 8, opacity: 0.6 }}>{bpct.toFixed(0)}%</span>
                    </div>
                    <div style={{ height: 3, borderRadius: 99, background: T.border, overflow: 'hidden' }}>
                      <div style={{ height: '100%', borderRadius: 99, background: pl.color, width: `${bpct}%`, boxShadow: `0 0 6px ${pl.color}`, transition: 'width 0.7s' }} />
                    </div>
                  </div>

                  {/* ROAS badge */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px', borderRadius: 99, background: `${rc}15`, border: `1px solid ${rc}35`, flexShrink: 0 }}>
                    <span style={{ color: rc, fontSize: 15, fontWeight: 900, fontFamily: 'monospace', textShadow: rc === T.emerald ? T.glowEmerald : rc === T.amber ? T.glowAmber : undefined }}>
                      {c.roas.toFixed(1)}×
                    </span>
                    {c.trend === 'up'   && <ArrowUpRight   style={{ width: 13, height: 13, color: rc }} />}
                    {c.trend === 'down' && <ArrowDownRight style={{ width: 13, height: 13, color: '#F87171' }} />}
                    {c.trend === 'flat' && <Minus          style={{ width: 13, height: 13, color: T.textSub }} />}
                  </div>

                  <ChevronRight style={{ width: 14, height: 14, color: T.textSub, opacity: 0.4, flexShrink: 0, transform: isExp ? 'rotate(90deg)' : undefined, transition: 'transform 0.2s' }} />
                </div>

                {/* AI rec */}
                {isExp && c.aiRec && (
                  <div style={{ margin: '0 20px 14px', display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', borderRadius: 12, background: `${pl.color}0c`, border: `1px solid ${pl.color}25` }}>
                    <Bot style={{ width: 12, height: 12, color: pl.color, flexShrink: 0 }} />
                    <p style={{ color: pl.color, fontSize: 11 }}>{c.aiRec}</p>
                  </div>
                )}

                {i < view.length - 1 && <div style={{ height: 1, margin: '0 20px', background: T.border }} />}
              </div>
            )
          })}
        </div>
      </div>

      {/* ── AI suggestion bar ───────────────────────────────────────── */}
      <div style={{ padding: '16px 20px', borderTop: `1px solid ${T.border}`, background: `${T.bgCard}80`, display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
        <Sparkles style={{ width: 13, height: 13, color: '#A78BFA', flexShrink: 0 }} />
        <span style={{ color: T.textSub, fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.15em', fontWeight: 700 }}>IA sugiere:</span>

        {SUGS.map(sg => {
          const isDone = done.has(sg.id)
          return (
            <button key={sg.id} onClick={() => apply(sg.id)} disabled={isDone}
              style={{
                display: 'flex', alignItems: 'center', gap: 7, padding: '7px 16px', borderRadius: 99,
                fontSize: 10, fontWeight: 700, cursor: isDone ? 'default' : 'pointer',
                background: `${sg.color}12`, border: `1px solid ${sg.color}${isDone ? '22' : '35'}`,
                color: sg.color, opacity: isDone ? 0.5 : 1, transition: 'all 0.2s',
              }}>
              {isDone ? <CheckCircle2 style={{ width: 12, height: 12 }} /> : <span style={{ fontSize: 13 }}>{sg.emoji}</span>}
              {sg.label}
            </button>
          )
        })}

        <button onClick={applyAll}
          style={{
            marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8, padding: '8px 20px', borderRadius: 99,
            fontSize: 11, fontWeight: 900, cursor: 'pointer', transition: 'all 0.3s',
            background: flash ? `${T.emerald}20` : `${T.cyan}15`,
            border: `1px solid ${flash ? T.emerald : T.cyan}55`,
            color: flash ? T.emerald : T.cyan,
            boxShadow: flash ? `0 0 16px ${T.emerald}30` : `0 0 16px ${T.cyan}20`,
          }}>
          {flash ? <><CheckCircle2 style={{ width: 14, height: 14 }} /> Aplicadas</> : <><Sparkles style={{ width: 14, height: 14 }} /> Aplicar todas las sugerencias</>}
        </button>
      </div>

    </section>
  )
}
