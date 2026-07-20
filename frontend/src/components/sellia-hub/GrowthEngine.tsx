'use client'

/**
 * GROWTH ENGINE
 * Diagnostica los problemas reales que impiden vender y ejecuta soluciones.
 * SEO orgánico · SEM · Brand positioning · Ejecución automática
 */

import { useState, useMemo } from 'react'
import {
  TrendingUp, Search, Globe, Target, AlertTriangle,
  CheckCircle2, Bot, Sparkles, Hash, Eye,
  ArrowUpRight, ArrowDownRight, BarChart3, Megaphone,
  FileText, Brain, Activity, Zap, Shield
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
  rose:        '#ef4444',
  glowCyan:    '0 0 22px rgba(6,182,212,0.50)',
  glowEmerald: '0 0 22px rgba(16,185,129,0.50)',
  glowRose:    '0 0 22px rgba(239,68,68,0.50)',
} as const

type Severity = 'critical' | 'high' | 'medium' | 'low'

interface Blocker {
  id: string
  emoji: string
  title: string
  description: string
  severity: Severity
  impactPercent: number
  category: string
  aiActions: { action: string; status: 'running' | 'queued' | 'done' }[]
  metric?: { label: string; current: string; target: string }
}

const BLOCKERS: Blocker[] = [
  {
    id: 'b1', emoji: '👻', title: 'Invisible en búsquedas relevantes',
    description: 'No aparecés en Google para las keywords donde tus clientes te buscan',
    severity: 'critical', impactPercent: 42, category: 'SEO',
    aiActions: [
      { action: 'Auditoría técnica SEO completa (Lighthouse + Search Console)', status: 'done' },
      { action: 'Generando 12 artículos blog con keywords target', status: 'running' },
      { action: 'Backlink outreach a 47 sitios de tu nicho', status: 'queued' },
    ],
    metric: { label: 'Posición Google', current: 'Pos 38', target: 'Top 5' },
  },
  {
    id: 'b2', emoji: '🚪', title: 'Visitantes que no compran',
    description: 'Conv. rate debajo del benchmark del sector (3.4% vs 8% promedio)',
    severity: 'high', impactPercent: 28, category: 'CRO',
    aiActions: [
      { action: 'A/B test 4 variantes de hero copy + CTA', status: 'running' },
      { action: '6 trust signals implementadas en checkout', status: 'done' },
      { action: 'Heatmap → reposicionando CTA above the fold', status: 'queued' },
    ],
    metric: { label: 'Conv. rate', current: '3.4%', target: '8.0%' },
  },
  {
    id: 'b3', emoji: '🌫', title: 'Marca sin diferenciación',
    description: 'Tu marca no se distingue de los 8 competidores principales',
    severity: 'high', impactPercent: 22, category: 'Brand',
    aiActions: [
      { action: '8 competidores mapeados y analizados', status: 'done' },
      { action: '5 propuestas de positioning único generadas', status: 'done' },
      { action: 'Aplicando nueva voz de marca en 23 posts', status: 'running' },
    ],
    metric: { label: 'Brand recall', current: '12%', target: '45%' },
  },
  {
    id: 'b4', emoji: '🎯', title: 'Audiencia mal segmentada en ads',
    description: 'ICP real no coincide con quienes ven tus ads actualmente',
    severity: 'medium', impactPercent: 15, category: 'Ads',
    aiActions: [
      { action: 'ICP construido desde tus 50 mejores clientes', status: 'done' },
      { action: '4 audiencias lookalike en Meta · 2 en TikTok', status: 'running' },
      { action: 'Reasignando 35% del budget a lookalikes 1%', status: 'queued' },
    ],
  },
  {
    id: 'b5', emoji: '🤐', title: 'Contenido RRSS inconsistente',
    description: 'Postear irregularmente mata el algoritmo y el reach orgánico',
    severity: 'medium', impactPercent: 12, category: 'Social',
    aiActions: [
      { action: 'Calendar editorial de 90 días generado', status: 'done' },
      { action: 'Publicando 5 reels/sem + 3 carruseles + 14 stories/sem', status: 'running' },
      { action: 'Engaging con 30 cuentas afines/día', status: 'running' },
    ],
    metric: { label: 'Posts/semana', current: '1-2', target: '12+' },
  },
]

const SEVERITY_CONFIG: Record<Severity, { label: string; color: string }> = {
  critical: { label: 'CRÍTICO', color: '#ef4444' },
  high:     { label: 'ALTO',    color: '#f59e0b' },
  medium:   { label: 'MEDIO',   color: '#3b82f6' },
  low:      { label: 'BAJO',    color: '#6b7280' },
}

const KEYWORDS = [
  { kw: 'agente ia ventas',        pos: 4,  prev: 12, vol: '2.4k/mes', intent: 'transactional' },
  { kw: 'automatización whatsapp', pos: 7,  prev: 18, vol: '8.1k/mes', intent: 'commercial' },
  { kw: 'cerrar ventas online',    pos: 12, prev: 23, vol: '1.8k/mes', intent: 'informational' },
  { kw: 'vendedor virtual',        pos: 18, prev: 31, vol: '720/mes',  intent: 'commercial' },
  { kw: 'chatbot empresa',         pos: 22, prev: 47, vol: '3.2k/mes', intent: 'commercial' },
  { kw: 'crm con ia',              pos: 5,  prev: 14, vol: '1.1k/mes', intent: 'transactional' },
]

const BRAND_METRICS = [
  { label: 'Menciones mes',      value: '247',  delta: '+38%', icon: Megaphone,  color: '#a855f7' },
  { label: 'Share of Voice',     value: '14%',  delta: '+4pp', icon: BarChart3,  color: '#ec4899' },
  { label: 'Sentiment positivo', value: '87%',  delta: '+12%', icon: Sparkles,   color: '#22c55e' },
  { label: 'Tráfico orgánico',   value: '4.2k', delta: '+62%', icon: TrendingUp, color: '#06b6d4' },
]

const CONTENT_STREAM = [
  { type: 'Blog',    action: 'Publicando "Cómo automatizar ventas con IA en 2026"', status: 'live',  platform: 'Web' },
  { type: 'Reel',    action: 'Generando reel "antes/después" · ya editado',         status: 'live',  platform: 'IG + TikTok' },
  { type: 'Backlink',action: 'Pitch a 8 medios tech para guest post',               status: 'live',  platform: 'PR' },
  { type: 'Search',  action: 'Optimizando 12 product pages para "long tail"',       status: 'queue', platform: 'Web' },
]

const card = (extra?: React.CSSProperties): React.CSSProperties => ({
  background: T.bgCard,
  border: `1px solid ${T.border}`,
  borderRadius: 16,
  ...extra,
})

export default function GrowthEngine() {
  const [view, setView] = useState<'diagnosis' | 'seo' | 'brand'>('diagnosis')
  const [expandedBlocker, setExpandedBlocker] = useState<string | null>(BLOCKERS[0]?.id || null)

  const totalImpact = useMemo(() => BLOCKERS.reduce((s, b) => s + b.impactPercent, 0), [])
  const recoverable = useMemo(() => BLOCKERS.reduce((s, b) => {
    const done = b.aiActions.filter(a => a.status === 'done').length
    return s + (b.impactPercent * (done / b.aiActions.length))
  }, 0), [])

  const healthScore = Math.round(100 - totalImpact + recoverable)

  return (
    <section style={{ background: T.bgApp, border: `1px solid ${T.border}`, borderRadius: 16, overflow: 'hidden', position: 'relative' }}>
      {/* Accent line */}
      <div style={{ height: 2, background: `linear-gradient(90deg, #6366f1, #ec4899, transparent)` }} />

      {/* Header */}
      <div style={{ padding: '20px 24px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.30)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Brain style={{ width: 20, height: 20, color: '#818cf8', filter: 'drop-shadow(0 0 8px rgba(99,102,241,0.6))' }} />
          </div>
          <div>
            <h2 style={{ fontSize: 14, fontWeight: 900, color: T.textPrim, textTransform: 'uppercase', letterSpacing: '0.08em', margin: 0 }}>
              GROWTH <span style={{ color: '#818cf8' }}>ENGINE</span>
              <span style={{ color: T.textSub, fontWeight: 400, fontSize: 11, marginLeft: 8, textTransform: 'none', letterSpacing: 0 }}>· Por qué no vendés (y cómo lo arreglamos)</span>
            </h2>
            <p style={{ fontSize: 11, color: T.textSub, margin: '4px 0 0' }}>Diagnóstico + SEO + branding + ejecución automática</p>
          </div>
        </div>

        {/* View switcher */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, padding: 4, borderRadius: 12, background: T.bgCard, border: `1px solid ${T.border}` }}>
          {([
            { id: 'diagnosis' as const, label: 'Diagnóstico', icon: AlertTriangle },
            { id: 'seo'       as const, label: 'SEO / SEM',   icon: Search },
            { id: 'brand'     as const, label: 'Branding',    icon: Megaphone },
          ]).map(v => {
            const Icon = v.icon
            const active = view === v.id
            return (
              <button
                key={v.id}
                onClick={() => setView(v.id)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px', borderRadius: 8, fontSize: 11, fontWeight: 700, cursor: 'pointer',
                  background: active ? 'rgba(99,102,241,0.20)' : 'transparent',
                  border: active ? '1px solid rgba(99,102,241,0.35)' : '1px solid transparent',
                  color: active ? '#818cf8' : T.textSub,
                }}
              >
                <Icon style={{ width: 12, height: 12 }} />
                {v.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* ── DIAGNOSIS VIEW ───────────────────────────────── */}
      {view === 'diagnosis' && (
        <>
          {/* Health summary bar */}
          <div style={{ padding: '20px 24px', borderBottom: `1px solid ${T.border}` }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
              {/* Health score gauge */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div style={{ position: 'relative', width: 64, height: 64, flexShrink: 0 }}>
                  <svg viewBox="0 0 36 36" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }}>
                    <circle cx="18" cy="18" r="15.5" fill="none" stroke={T.border} strokeWidth="3" />
                    <circle cx="18" cy="18" r="15.5" fill="none"
                      stroke={healthScore >= 60 ? T.emerald : healthScore >= 40 ? T.amber : T.rose}
                      strokeWidth="3" strokeDasharray="97.4" strokeDashoffset={97.4 - (97.4 * healthScore / 100)}
                      strokeLinecap="round" />
                  </svg>
                  <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ fontSize: 13, fontWeight: 900, color: T.textPrim, fontVariantNumeric: 'tabular-nums' }}>{healthScore}</span>
                  </div>
                </div>
                <div>
                  <p style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.12em', color: T.textSub, fontWeight: 700, margin: 0 }}>Health Score</p>
                  <p style={{ fontSize: 12, fontWeight: 700, color: T.textPrim, margin: '3px 0 2px' }}>Salud del negocio</p>
                  <p style={{ fontSize: 10, color: T.textSub, margin: 0 }}>{BLOCKERS.length} bloqueadores activos</p>
                </div>
              </div>

              {/* Revenue lost */}
              <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', paddingLeft: 16, borderLeft: `1px solid ${T.border}` }}>
                <p style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.12em', color: T.textSub, fontWeight: 700, margin: '0 0 4px' }}>Revenue bloqueado</p>
                <p style={{ fontSize: 32, fontWeight: 900, color: T.rose, fontVariantNumeric: 'tabular-nums', lineHeight: 1, margin: '0 0 6px', textShadow: T.glowRose }}>-{totalImpact}%</p>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontSize: 9, padding: '2px 7px', borderRadius: 6, background: 'rgba(239,68,68,0.15)', color: T.rose, fontWeight: 700, border: '1px solid rgba(239,68,68,0.25)' }}>
                    {BLOCKERS.filter(b => b.severity === 'critical').length} crítico
                  </span>
                  <span style={{ fontSize: 9, padding: '2px 7px', borderRadius: 6, background: 'rgba(245,158,11,0.15)', color: T.amber, fontWeight: 700, border: '1px solid rgba(245,158,11,0.25)' }}>
                    {BLOCKERS.filter(b => b.severity === 'high').length} alto
                  </span>
                </div>
              </div>

              {/* IA recovered */}
              <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', paddingLeft: 16, borderLeft: `1px solid ${T.border}` }}>
                <p style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.12em', color: T.textSub, fontWeight: 700, margin: '0 0 4px' }}>IA ya recuperó</p>
                <p style={{ fontSize: 32, fontWeight: 900, color: T.emerald, fontVariantNumeric: 'tabular-nums', lineHeight: 1, margin: '0 0 6px', textShadow: T.glowEmerald }}>+{recoverable.toFixed(0)}%</p>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 80, height: 6, background: T.bgApp, borderRadius: 999, overflow: 'hidden' }}>
                    <div style={{ height: '100%', borderRadius: 999, background: T.emerald, width: `${(recoverable / totalImpact) * 100}%` }} />
                  </div>
                  <span style={{ fontSize: 10, color: T.textSub }}>{Math.round((recoverable / totalImpact) * 100)}%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Blocker cards */}
          <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 10 }}>
            {BLOCKERS.map(b => {
              const cfg = SEVERITY_CONFIG[b.severity]
              const isExpanded = expandedBlocker === b.id
              const done = b.aiActions.filter(a => a.status === 'done').length
              const running = b.aiActions.filter(a => a.status === 'running').length
              const progress = (done / b.aiActions.length) * 100

              return (
                <div key={b.id} style={{ background: T.bgCard, border: `1px solid ${T.border}`, borderRadius: 16, overflow: 'hidden' }}>
                  <div style={{ height: 2, background: `linear-gradient(90deg, ${cfg.color}, transparent)` }} />

                  <button
                    onClick={() => setExpandedBlocker(isExpanded ? null : b.id)}
                    style={{ width: '100%', padding: '14px 16px', display: 'flex', alignItems: 'flex-start', gap: 12, textAlign: 'left', background: 'transparent', border: 'none', cursor: 'pointer' }}
                  >
                    <span style={{ fontSize: 24, flexShrink: 0, marginTop: 2 }}>{b.emoji}</span>

                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 4 }}>
                        <p style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, margin: 0, lineHeight: 1.3 }}>{b.title}</p>
                        <span style={{ fontSize: 9, padding: '3px 7px', borderRadius: 6, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', background: `${cfg.color}18`, color: cfg.color, border: `1px solid ${cfg.color}30` }}>
                          {cfg.label}
                        </span>
                        <span style={{ fontSize: 10, fontWeight: 900, color: T.rose, fontVariantNumeric: 'tabular-nums' }}>-{b.impactPercent}% revenue</span>
                        <span style={{ fontSize: 9, color: T.textSub, fontFamily: 'monospace', textTransform: 'uppercase' }}>{b.category}</span>
                      </div>
                      <p style={{ fontSize: 11, color: T.textSub, lineHeight: 1.4, margin: '0 0 10px' }}>{b.description}</p>

                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{ flex: 1, height: 5, background: T.bgApp, borderRadius: 999, overflow: 'hidden' }}>
                          <div style={{ height: '100%', borderRadius: 999, width: `${progress}%`, background: cfg.color, boxShadow: `0 0 6px ${cfg.color}` }} />
                        </div>
                        <span style={{ fontSize: 9, color: T.textSub, fontFamily: 'monospace', flexShrink: 0 }}>{done}/{b.aiActions.length} acciones</span>
                        {running > 0 && (
                          <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 9, color: T.amber, flexShrink: 0 }}>
                            <span style={{ width: 6, height: 6, borderRadius: '50%', background: T.amber, animation: 'pulse 2s infinite', display: 'inline-block' }} />
                            {running} activa{running > 1 ? 's' : ''}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Metric pill */}
                    {b.metric && (
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', flexShrink: 0, gap: 2 }}>
                        <p style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.textSub, fontFamily: 'monospace', margin: 0 }}>{b.metric.label}</p>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <span style={{ fontSize: 11, fontWeight: 700, color: T.rose }}>{b.metric.current}</span>
                          <span style={{ color: T.textSub }}>→</span>
                          <span style={{ fontSize: 11, fontWeight: 700, color: T.emerald }}>{b.metric.target}</span>
                        </div>
                      </div>
                    )}

                    <span style={{ color: T.textSub, flexShrink: 0, fontSize: 16, marginTop: 2 }}>{isExpanded ? '↑' : '↓'}</span>
                  </button>

                  {isExpanded && (
                    <div style={{ padding: '0 16px 16px', borderTop: `1px solid ${T.border}` }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '12px 0 8px' }}>
                        <Bot style={{ width: 12, height: 12, color: T.emerald }} />
                        <p style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.emerald, fontWeight: 700, margin: 0 }}>Soluciones IA en marcha</p>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {b.aiActions.map((a, i) => (
                          <div key={i} style={{
                            display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px', borderRadius: 12, border: '1px solid',
                            background: a.status === 'done' ? 'rgba(16,185,129,0.04)' : a.status === 'running' ? 'rgba(245,158,11,0.05)' : T.bgApp,
                            borderColor: a.status === 'done' ? 'rgba(16,185,129,0.25)' : a.status === 'running' ? 'rgba(245,158,11,0.28)' : T.border,
                          }}>
                            <div style={{ width: 24, height: 24, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, background: a.status === 'done' ? 'rgba(16,185,129,0.15)' : a.status === 'running' ? 'rgba(245,158,11,0.15)' : T.bgCard, border: `1px solid ${a.status === 'done' ? 'rgba(16,185,129,0.40)' : a.status === 'running' ? 'rgba(245,158,11,0.40)' : T.border}` }}>
                              {a.status === 'done' && <CheckCircle2 style={{ width: 14, height: 14, color: T.emerald }} />}
                              {a.status === 'running' && <span style={{ width: 8, height: 8, borderRadius: '50%', background: T.amber, animation: 'pulse 2s infinite', display: 'inline-block' }} />}
                              {a.status === 'queued' && <span style={{ fontSize: 9, color: T.textSub, fontWeight: 700 }}>{i + 1}</span>}
                            </div>
                            <p style={{ fontSize: 11, flex: 1, lineHeight: 1.4, margin: 0, color: a.status === 'done' ? T.textSub : a.status === 'running' ? T.textPrim : T.textSub, textDecoration: a.status === 'done' ? 'line-through' : 'none', fontWeight: a.status === 'running' ? 600 : 400 }}>{a.action}</p>
                            {a.status === 'running' && (
                              <span style={{ fontSize: 8, fontWeight: 700, color: T.amber, background: 'rgba(245,158,11,0.12)', border: '1px solid rgba(245,158,11,0.28)', padding: '3px 7px', borderRadius: 6, textTransform: 'uppercase', letterSpacing: '0.08em', flexShrink: 0 }}>EN CURSO</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}

      {/* ── SEO VIEW ──────────────────────────────────────── */}
      {view === 'seo' && (
        <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12 }}>
            {[
              { icon: Search,       label: 'Keywords top 10', value: '14',   delta: '+8 vs mes',  color: T.cyan },
              { icon: Eye,          label: 'Impr. SERP',      value: '148k', delta: '+42%',        color: '#a855f7' },
              { icon: ArrowUpRight, label: 'Clicks org.',     value: '4.2k', delta: '+62%',        color: T.emerald },
              { icon: Shield,       label: 'Domain Rating',   value: '38',   delta: '+5',          color: T.amber },
            ].map((k, i) => {
              const Icon = k.icon
              return (
                <div key={i} style={{ ...card({ padding: 20 }) }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                    <Icon style={{ width: 14, height: 14, color: k.color }} />
                    <p style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.textSub, fontWeight: 700, margin: 0 }}>{k.label}</p>
                  </div>
                  <p style={{ fontSize: 26, fontWeight: 900, color: T.textPrim, fontVariantNumeric: 'tabular-nums', margin: '0 0 4px' }}>{k.value}</p>
                  <p style={{ fontSize: 11, fontWeight: 700, margin: 0, color: k.color }}>{k.delta}</p>
                </div>
              )
            })}
          </div>

          {/* Keywords table */}
          <div style={{ ...card(), overflow: 'hidden' }}>
            <div style={{ padding: '12px 16px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Hash style={{ width: 12, height: 12, color: '#818cf8' }} />
                <p style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.textSub, fontWeight: 700, margin: 0 }}>Keywords · IA posicionando</p>
              </div>
              <span style={{ fontSize: 10, color: T.emerald, fontWeight: 700 }}>+12 subieron esta semana ↑</span>
            </div>
            <div>
              {KEYWORDS.map((k, i) => {
                const movement = k.prev - k.pos
                const isTop10 = k.pos <= 10
                return (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '12px 16px', borderBottom: i < KEYWORDS.length - 1 ? `1px solid ${T.border}` : 'none' }}>
                    <p style={{ fontSize: 22, fontWeight: 900, fontVariantNumeric: 'tabular-nums', width: 40, textAlign: 'right', flexShrink: 0, margin: 0, color: isTop10 ? T.emerald : T.textPrim }}>
                      #{k.pos}
                    </p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4, width: 48, flexShrink: 0 }}>
                      {movement > 0
                        ? <ArrowUpRight style={{ width: 14, height: 14, color: T.emerald }} />
                        : <ArrowDownRight style={{ width: 14, height: 14, color: T.rose }} />
                      }
                      <span style={{ fontSize: 11, fontWeight: 700, color: movement > 0 ? T.emerald : T.rose }}>
                        {movement > 0 ? `+${movement}` : movement}
                      </span>
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ fontSize: 12, fontFamily: 'monospace', color: T.textPrim, margin: '0 0 2px' }}>"{k.kw}"</p>
                      <p style={{ fontSize: 9, color: T.textSub, textTransform: 'uppercase', letterSpacing: '0.06em', margin: 0 }}>{k.intent} · {k.vol}</p>
                    </div>
                    {isTop10 && (
                      <span style={{ fontSize: 9, padding: '3px 8px', borderRadius: 999, fontWeight: 700, textTransform: 'uppercase', background: 'rgba(16,185,129,0.15)', color: T.emerald, border: `1px solid rgba(16,185,129,0.30)`, flexShrink: 0 }}>
                        TOP 10
                      </span>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Content stream */}
          <div style={{ ...card({ padding: 20 }) }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <FileText style={{ width: 12, height: 12, color: '#818cf8' }} />
              <p style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#818cf8', fontWeight: 700, margin: 0 }}>IA produciendo contenido ahora</p>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {CONTENT_STREAM.map((c, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px', borderRadius: 10, background: T.bgApp, border: `1px solid ${T.border}` }}>
                  <span style={{ fontSize: 9, padding: '3px 8px', borderRadius: 6, fontWeight: 700, textTransform: 'uppercase', background: T.bgCard, color: T.textSub, flexShrink: 0, width: 64, textAlign: 'center', border: `1px solid ${T.border}` }}>{c.type}</span>
                  <p style={{ fontSize: 12, color: T.textPrim, flex: 1, lineHeight: 1.4, margin: 0 }}>{c.action}</p>
                  <span style={{ fontSize: 9, color: T.textSub, flexShrink: 0 }}>{c.platform}</span>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', flexShrink: 0, background: c.status === 'live' ? T.emerald : T.border, animation: c.status === 'live' ? 'pulse 2s infinite' : 'none', boxShadow: c.status === 'live' ? T.glowEmerald : 'none' }} />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── BRAND VIEW ────────────────────────────────────── */}
      {view === 'brand' && (
        <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12 }}>
            {BRAND_METRICS.map(m => {
              const Icon = m.icon
              return (
                <div key={m.label} style={{ ...card({ padding: 20 }) }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                    <Icon style={{ width: 14, height: 14, color: m.color }} />
                    <p style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.textSub, fontWeight: 700, margin: 0 }}>{m.label}</p>
                  </div>
                  <p style={{ fontSize: 26, fontWeight: 900, color: T.textPrim, fontVariantNumeric: 'tabular-nums', margin: '0 0 4px' }}>{m.value}</p>
                  <p style={{ fontSize: 11, fontWeight: 700, margin: 0, color: m.color }}>{m.delta} vs mes anterior</p>
                </div>
              )
            })}
          </div>

          {/* Positioning canvas */}
          <div style={{ ...card({ padding: 20 }) }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
              <Target style={{ width: 14, height: 14, color: '#ec4899' }} />
              <p style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#ec4899', fontWeight: 700, margin: 0 }}>Posicionamiento único · generado por IA</p>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 12 }}>
              {[
                { label: '¿Para quién?', text: 'Dueños de PyMEs (5-50 empleados) que venden online en LATAM con tickets $200-$5,000' },
                { label: '¿Qué problema?', text: 'Cierran 10-30% menos por no estar 24/7 disponibles para responder y cerrar' },
                { label: '¿Por qué nosotros?', text: 'Único agente IA que opera el navegador real como humano + especializado en LATAM (AFIP, ML, WhatsApp Business)' },
                { label: 'Tagline', text: '"Cruzá los brazos. Tu IA vende sola."', bold: true },
              ].map((item, i) => (
                <div key={i} style={{ padding: '14px 16px', borderRadius: 12, background: T.bgApp, border: `1px solid ${T.border}` }}>
                  <p style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.textSub, fontWeight: 700, margin: '0 0 6px' }}>{item.label}</p>
                  <p style={{ fontSize: 13, color: T.textPrim, lineHeight: 1.4, margin: 0, fontWeight: item.bold ? 700 : 400, fontStyle: item.bold ? 'italic' : 'normal' }}>{item.text}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Channel activations */}
          <div style={{ ...card({ padding: 20 }) }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <Megaphone style={{ width: 12, height: 12, color: T.textSub }} />
              <p style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.textSub, fontWeight: 700, margin: 0 }}>Activación de marca en curso</p>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 10 }}>
              {[
                { ch: 'IG · Reels',     action: '14 publicados',              delta: '+342 followers' },
                { ch: 'TikTok',         action: '6 viral hooks',              delta: '+847k views' },
                { ch: 'LinkedIn',       action: '8 posts thought leadership', delta: '+1.2k engagement' },
                { ch: 'Podcasts pitch', action: '4 invitaciones',             delta: 'agendados' },
                { ch: 'PR media',       action: 'Pitch a 8 medios tech',      delta: '2 respondieron' },
                { ch: 'Comunidades',    action: '8 Discord/Slack activos',    delta: 'autoridad creciente' },
              ].map((c, i) => (
                <div key={i} style={{ padding: '12px 14px', borderRadius: 12, background: T.bgApp, border: `1px solid ${T.border}` }}>
                  <p style={{ fontSize: 11, fontWeight: 700, color: T.textPrim, margin: '0 0 3px' }}>{c.ch}</p>
                  <p style={{ fontSize: 11, color: T.textSub, lineHeight: 1.3, margin: '0 0 6px' }}>{c.action}</p>
                  <p style={{ fontSize: 11, color: T.emerald, fontWeight: 700, margin: 0 }}>{c.delta}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
