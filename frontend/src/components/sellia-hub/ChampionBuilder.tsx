'use client'

/**
 * CHAMPION BUILDER
 *
 * "De cliente a embajador" — sistema de fidelización progresivo.
 *
 * Escalera de 5 niveles:
 *   Engaged → Loyal → Champion → Advocate → Evangelist
 *
 * Cada nivel desbloquea acciones IA específicas.
 * Hall of Fame con los embajadores top + impacto en revenue.
 */

import { useState, useMemo } from 'react'
import {
  Crown, Award, Trophy, Star, Megaphone, Heart, Sparkles,
  Users, TrendingUp, ChevronRight, Bot, Flame, Rocket, Target
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

type TierId = 'engaged' | 'loyal' | 'champion' | 'advocate' | 'evangelist'

interface Tier {
  id: TierId
  emoji: string
  label: string
  icon: React.ElementType
  color: string
  count: number
  delta: number
  description: string
  unlockedActions: string[]
  aiActionsThisWeek: number
}

interface Champion {
  id: string
  name: string
  tier: TierId
  ltv: number
  monthsActive: number
  referralsBrought: number
  referralRevenue: number
  testimonialGiven: boolean
  nps: number
  recentImpact: string
}

const TIERS: Tier[] = [
  {
    id: 'engaged', emoji: '💎', label: 'Engaged', icon: Heart, color: '#ec4899',
    count: 87, delta: 4,
    description: 'Cliente activo. Usa el producto regularmente.',
    unlockedActions: ['Tips contextuales', 'Tutorial drip', 'Health score monitoring'],
    aiActionsThisWeek: 124,
  },
  {
    id: 'loyal', emoji: '🏆', label: 'Loyal', icon: Trophy, color: T.violet,
    count: 34, delta: 5,
    description: 'Más de 6 meses + 2 compras. LTV crece.',
    unlockedActions: ['Reorder automático', 'Upsell Premium', 'Programa de lealtad', 'Birthday gifts'],
    aiActionsThisWeek: 78,
  },
  {
    id: 'champion', emoji: '⭐', label: 'Champion', icon: Award, color: T.amber,
    count: 18, delta: 1,
    description: 'NPS 9-10 + recompra recurrente. Listo para impulsar marca.',
    unlockedActions: ['Solicitud testimonio', 'Caso de éxito', 'Beta access', 'Programa referidos'],
    aiActionsThisWeek: 42,
  },
  {
    id: 'advocate', emoji: '📢', label: 'Advocate', icon: Megaphone, color: T.emerald,
    count: 9, delta: 2,
    description: 'Ya trajo 1+ referido. IA potencia su rol de embajador.',
    unlockedActions: ['Comisión referidos', 'Co-marketing', 'Webinar invitado', 'Panel asesor'],
    aiActionsThisWeek: 28,
  },
  {
    id: 'evangelist', emoji: '🔥', label: 'Evangelist', icon: Flame, color: T.rose,
    count: 3, delta: 0,
    description: 'Trajo 5+ referidos. Movimiento orgánico. Pilar de marca.',
    unlockedActions: ['Pack VIP', 'Acceso CEO', 'Co-creación producto', 'Eventos exclusivos'],
    aiActionsThisWeek: 12,
  },
]

const HALL_OF_FAME: Champion[] = [
  {
    id: 'c1', name: 'Tomás N. (NPS 10)', tier: 'evangelist', ltv: 18400, monthsActive: 14,
    referralsBrought: 7, referralRevenue: 9800, testimonialGiven: true, nps: 10,
    recentImpact: 'Acaba de traer a Empresa Gamma · $4.2k',
  },
  {
    id: 'c2', name: 'Lucía F. (e-commerce moda)', tier: 'evangelist', ltv: 24800, monthsActive: 18,
    referralsBrought: 5, referralRevenue: 12400, testimonialGiven: true, nps: 10,
    recentImpact: 'Video testimonio publicado en IG · 14k views',
  },
  {
    id: 'c3', name: 'Ana Suárez', tier: 'advocate', ltv: 9800, monthsActive: 9,
    referralsBrought: 3, referralRevenue: 4200, testimonialGiven: true, nps: 9,
    recentImpact: 'Webinar testimonial agendado · viernes',
  },
  {
    id: 'c4', name: 'Empresa Beta SRL', tier: 'champion', ltv: 14200, monthsActive: 11,
    referralsBrought: 1, referralRevenue: 1800, testimonialGiven: false, nps: 9,
    recentImpact: 'Caso de éxito en proceso',
  },
]

const ACTIVE_CAMPAIGNS = [
  { id: 'c1', emoji: '🎁', name: 'Referral Cash · 20% cada uno', target: '34 Loyal+', enrolled: 28, conversions: 7 },
  { id: 'c2', emoji: '⭐', name: 'NPS Survey trimestral', target: '87 Engaged+', enrolled: 87, conversions: 23 },
  { id: 'c3', emoji: '🎬', name: 'Video testimonios', target: '18 Champions', enrolled: 14, conversions: 6 },
  { id: 'c4', emoji: '🚀', name: 'Beta Premium 2.0 access', target: '9 Advocates', enrolled: 9, conversions: 4 },
]

const REFERRAL_TREE = [
  { name: 'Tomás N.', children: ['Empresa Gamma · $4.2k', 'Carlos R. · $1.8k', 'Pedro K. (close pending)', '+ 4 más'] },
  { name: 'Lucía F.', children: ['Pack 12 alumnos · $3.5k', 'Maria L. · $1.2k', 'Acme SA (engaged)', '+ 2 más'] },
]

export default function ChampionBuilder() {
  const [selectedTier, setSelectedTier] = useState<TierId>('champion')
  const [view, setView] = useState<'tiers' | 'hall' | 'tree'>('tiers')

  const stats = useMemo(() => {
    const totalChampions = TIERS.reduce((s, t) => s + t.count, 0)
    const totalAIActions = TIERS.reduce((s, t) => s + t.aiActionsThisWeek, 0)
    const referralRevenue = HALL_OF_FAME.reduce((s, c) => s + c.referralRevenue, 0)
    const totalReferrals = HALL_OF_FAME.reduce((s, c) => s + c.referralsBrought, 0)
    return { totalChampions, totalAIActions, referralRevenue, totalReferrals }
  }, [])

  const tier = TIERS.find(t => t.id === selectedTier)!

  const VIEWS = [
    { id: 'tiers' as const, label: 'Escalera', icon: TrendingUp },
    { id: 'hall' as const, label: 'Hall of Fame', icon: Trophy },
    { id: 'tree' as const, label: 'Árbol referidos', icon: Users },
  ]

  return (
    <section style={{ background: T.bgCard, border: `1px solid ${T.border}`, borderRadius: 16, overflow: 'hidden' }}>
      <div style={{ height: 1, background: `linear-gradient(90deg, transparent, ${T.amber}80, transparent)` }} />

      {/* Header */}
      <div style={{
        padding: '16px 20px', borderBottom: `1px solid ${T.border}`,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: `${T.amber}22`, border: `1px solid ${T.amber}44`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Crown style={{ width: 20, height: 20, color: T.amber, filter: `drop-shadow(0 0 8px ${T.amber}b0)` }} />
          </div>
          <div>
            <h2 style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, letterSpacing: '.08em', textTransform: 'uppercase', margin: 0 }}>
              CHAMPION BUILDER
              <span style={{ color: T.textSub, fontWeight: 400, textTransform: 'none', letterSpacing: 'normal', marginLeft: 8 }}>· De cliente a embajador</span>
            </h2>
            <p style={{ fontSize: 11, color: T.textSub, margin: 0, marginTop: 2 }}>Sistema progresivo de fidelización · 5 niveles · IA activa en cada uno</p>
          </div>
        </div>

        {/* View switcher */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, padding: 4, borderRadius: 12, background: 'rgba(255,255,255,0.04)', border: `1px solid ${T.border}` }}>
          {VIEWS.map(v => {
            const Icon = v.icon
            const active = view === v.id
            return (
              <button key={v.id} onClick={() => setView(v.id)} style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '6px 12px', borderRadius: 8, fontSize: 11, fontWeight: 600,
                background: active ? `${T.amber}20` : 'transparent',
                border: active ? `1px solid ${T.amber}40` : '1px solid transparent',
                color: active ? T.amber : T.textSub,
                cursor: 'pointer',
              }}>
                <Icon style={{ width: 12, height: 12 }} />
                {v.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', borderBottom: `1px solid ${T.border}` }}>
        {[
          { icon: Users, color: T.amber, label: 'Total clientes activos', value: stats.totalChampions, sub: 'en escalera' },
          { icon: Bot, color: T.violet, label: 'Acciones IA esta semana', value: stats.totalAIActions, sub: 'automatizadas' },
          { icon: Megaphone, color: T.emerald, label: 'Referidos generados', value: stats.totalReferrals, sub: 'por embajadores' },
          { icon: TrendingUp, color: T.emerald, label: 'Revenue por referido', value: `$${(stats.referralRevenue / 1000).toFixed(1)}k`, sub: 'orgánico · sin ads' },
        ].map((s, i) => {
          const Icon = s.icon
          return (
            <div key={i} style={{ padding: 12, borderRight: i < 3 ? `1px solid ${T.border}` : undefined }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                <Icon style={{ width: 12, height: 12, color: s.color }} />
                <p style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, margin: 0, fontWeight: 700 }}>{s.label}</p>
              </div>
              <p style={{ fontSize: 20, fontWeight: 900, color: i === 3 ? T.emerald : T.textPrim, margin: 0, textShadow: `0 0 20px ${s.color}88` }}>{s.value}</p>
              <p style={{ fontSize: 9, color: s.color, margin: 0, marginTop: 2 }}>{s.sub}</p>
            </div>
          )
        })}
      </div>

      {/* Views */}
      {view === 'tiers' && (
        <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Tier ladder */}
          <div style={{ display: 'flex', alignItems: 'stretch', gap: 8, overflowX: 'auto' }}>
            {TIERS.map((t, i) => {
              const Icon = t.icon
              const isActive = selectedTier === t.id
              return (
                <button key={t.id} onClick={() => setSelectedTier(t.id)} style={{
                  position: 'relative', flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'center',
                  padding: 12, borderRadius: 12, minWidth: 110,
                  background: isActive ? `${t.color}18` : 'rgba(255,255,255,0.02)',
                  border: `1px solid ${isActive ? t.color + '50' : T.border}`,
                  boxShadow: isActive ? `0 0 24px ${t.color}28` : 'none',
                  transform: isActive ? 'translateY(-4px)' : 'none',
                  transition: 'all 0.2s',
                  cursor: 'pointer',
                }}>
                  <span style={{ fontSize: 8, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '.06em', color: T.textSub, marginBottom: 4 }}>LVL {i + 1}</span>
                  <div style={{ fontSize: 28, marginBottom: 4 }}>{t.emoji}</div>
                  <span style={{ fontSize: 10, fontWeight: 700, color: T.textPrim, textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>{t.label}</span>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
                    <span style={{ fontSize: 22, fontWeight: 900, color: T.textPrim, textShadow: `0 0 20px ${t.color}88` }}>{t.count}</span>
                    {t.delta !== 0 && (
                      <span style={{ fontSize: 9, fontWeight: 700, color: t.delta > 0 ? T.emerald : T.rose }}>
                        {t.delta > 0 ? '+' : ''}{t.delta}
                      </span>
                    )}
                  </div>
                  {i < TIERS.length - 1 && (
                    <div style={{ position: 'absolute', right: -14, top: '50%', transform: 'translateY(-50%)', zIndex: 10 }}>
                      <ChevronRight style={{ width: 16, height: 16, color: isActive ? t.color : T.border }} />
                    </div>
                  )}
                  {t.aiActionsThisWeek > 0 && (
                    <div style={{ position: 'absolute', top: -4, right: -4, width: 20, height: 20, borderRadius: '50%', background: T.violet, display: 'flex', alignItems: 'center', justifyContent: 'center', border: `2px solid ${T.bgCard}` }}>
                      <Bot style={{ width: 10, height: 10, color: '#fff' }} />
                    </div>
                  )}
                  <Icon style={{ width: 0, height: 0 }} />
                </button>
              )
            })}
          </div>

          {/* Selected tier detail */}
          <div style={{ borderRadius: 12, padding: 20, background: `${tier.color}08`, border: `1px solid ${tier.color}30` }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, marginBottom: 16 }}>
              <div style={{ fontSize: 40, flexShrink: 0 }}>{tier.emoji}</div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 4 }}>
                  <h3 style={{ fontSize: 18, fontWeight: 700, color: T.textPrim, textTransform: 'uppercase', letterSpacing: '.08em', margin: 0 }}>{tier.label}</h3>
                  <span style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', padding: '2px 8px', borderRadius: 12, background: `${tier.color}20`, color: tier.color }}>
                    {tier.count} CLIENTES
                  </span>
                  <span style={{ fontSize: 10, color: T.violet, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Bot style={{ width: 10, height: 10 }} />{tier.aiActionsThisWeek} acciones IA esta semana
                  </span>
                </div>
                <p style={{ fontSize: 14, color: T.textSub, margin: 0 }}>{tier.description}</p>
              </div>
            </div>
            <div>
              <p style={{ fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, fontWeight: 700, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 4 }}>
                <Sparkles style={{ width: 10, height: 10 }} />ACCIONES IA DESBLOQUEADAS EN ESTE NIVEL
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(180px,1fr))', gap: 8 }}>
                {tier.unlockedActions.map((a, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: 8, borderRadius: 8, background: 'rgba(255,255,255,0.04)', border: `1px solid ${T.border}` }}>
                    <div className="animate-pulse" style={{ width: 6, height: 6, borderRadius: '50%', background: tier.color, flexShrink: 0 }} />
                    <span style={{ fontSize: 11, color: T.textPrim }}>{a}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Active campaigns */}
          <div>
            <p style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, fontWeight: 700, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 4 }}>
              <Target style={{ width: 10, height: 10 }} />CAMPAÑAS DE FIDELIZACIÓN ACTIVAS
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(260px,1fr))', gap: 8 }}>
              {ACTIVE_CAMPAIGNS.map(c => (
                <div key={c.id} style={{ borderRadius: 12, overflow: 'hidden', border: `1px solid ${T.border}`, background: 'rgba(255,255,255,0.02)' }}>
                  <div style={{ height: 2, background: `linear-gradient(90deg, ${T.amber}80, transparent)` }} />
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 12 }}>
                    <span style={{ fontSize: 22, flexShrink: 0 }}>{c.emoji}</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 2 }}>
                        <p style={{ fontSize: 12, fontWeight: 600, color: T.textPrim, margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.name}</p>
                        <span style={{ fontSize: 10, color: T.emerald, fontWeight: 700, textShadow: '0 0 20px #10B98188' }}>{c.conversions} conv</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                        <p style={{ fontSize: 10, color: T.textSub, margin: 0 }}>Target: {c.target}</p>
                        <span style={{ fontSize: 10, color: T.textSub }}>{c.enrolled} enrolled</span>
                      </div>
                      <div style={{ height: 4, borderRadius: 2, background: 'rgba(255,255,255,0.05)', overflow: 'hidden', marginTop: 6 }}>
                        <div style={{ height: '100%', background: `linear-gradient(90deg, ${T.amber}, #f97316)`, borderRadius: 2, width: `${(c.conversions / c.enrolled) * 100}%` }} />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {view === 'hall' && (
        <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 12 }}>
          {HALL_OF_FAME.map((champion, i) => {
            const champTier = TIERS.find(t => t.id === champion.tier)!
            const isPodium = i < 3
            return (
              <div key={champion.id} style={{
                position: 'relative', borderRadius: 12, overflow: 'hidden',
                background: `${champTier.color}06`,
                border: `1px solid ${champTier.color}28`,
                boxShadow: isPodium ? `0 0 20px ${champTier.color}12` : 'none',
              }}>
                <div style={{ height: 2, background: `linear-gradient(90deg, ${champTier.color}, transparent)` }} />
                <div style={{ padding: 16 }}>
                  <div style={{ position: 'absolute', top: 8, right: 8 }}>
                    {i === 0 && <span style={{ fontSize: 22 }}>🥇</span>}
                    {i === 1 && <span style={{ fontSize: 22 }}>🥈</span>}
                    {i === 2 && <span style={{ fontSize: 22 }}>🥉</span>}
                    {i >= 3 && <span style={{ fontSize: 10, color: T.textSub, fontFamily: 'monospace', fontWeight: 700 }}>#{i + 1}</span>}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
                    <div style={{
                      width: 56, height: 56, borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 28, flexShrink: 0,
                      background: `${champTier.color}18`,
                      border: `2px solid ${champTier.color}40`,
                      boxShadow: `0 0 16px ${champTier.color}20`,
                    }}>
                      {champTier.emoji}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 4 }}>
                        <h4 style={{ fontSize: 14, fontWeight: 700, color: T.textPrim, margin: 0 }}>{champion.name}</h4>
                        <span style={{
                          fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase',
                          padding: '2px 6px', borderRadius: 4,
                          background: `${champTier.color}20`, color: champTier.color, border: `1px solid ${champTier.color}28`,
                        }}>{champTier.label}</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          {Array.from({ length: champion.nps - 7 }).map((_, j) => (
                            <Star key={j} style={{ width: 12, height: 12, fill: T.amber, color: T.amber }} />
                          ))}
                        </div>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 8, marginBottom: 8 }}>
                        <StatMini label="LTV" value={`$${(champion.ltv / 1000).toFixed(1)}k`} color={T.emerald} />
                        <StatMini label="Activo" value={`${champion.monthsActive}m`} color={T.cyan} />
                        <StatMini label="Referidos" value={champion.referralsBrought} color={T.violet} />
                        <StatMini label="$ referidos" value={`$${(champion.referralRevenue / 1000).toFixed(1)}k`} color={T.amber} />
                      </div>
                      {champion.testimonialGiven && (
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '2px 8px', borderRadius: 6, background: `${T.emerald}18`, border: `1px solid ${T.emerald}28`, color: T.emerald, fontSize: 10, fontWeight: 500, marginBottom: 6 }}>
                          <Sparkles style={{ width: 10, height: 10 }} />Dio testimonio público
                        </div>
                      )}
                      <p style={{ fontSize: 11, color: T.textSub, fontStyle: 'italic', margin: 0 }}>
                        <span style={{ color: T.border }}>Reciente:</span> {champion.recentImpact}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {view === 'tree' && (
        <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
          {REFERRAL_TREE.map(root => (
            <div key={root.name} style={{ borderRadius: 12, border: `1px solid ${T.amber}28`, background: `${T.amber}04`, padding: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, paddingBottom: 12, borderBottom: `1px solid ${T.border}` }}>
                <div style={{ width: 40, height: 40, borderRadius: 10, background: `${T.amber}20`, border: `1px solid ${T.amber}40`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, flexShrink: 0 }}>
                  🔥
                </div>
                <div>
                  <p style={{ fontSize: 14, fontWeight: 700, color: T.textPrim, margin: 0 }}>{root.name}</p>
                  <p style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.amber, fontWeight: 700, margin: 0 }}>Embajador raíz · Evangelist</p>
                </div>
                <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Megaphone style={{ width: 14, height: 14, color: T.amber }} />
                  <span style={{ fontSize: 12, fontWeight: 700, color: T.amber }}>{root.children.length} referidos</span>
                </div>
              </div>
              <div style={{ marginTop: 12, marginLeft: 20, display: 'flex', flexDirection: 'column', gap: 8, position: 'relative' }}>
                <div style={{ position: 'absolute', left: -12, top: 0, bottom: 0, width: 1, background: `${T.amber}40` }} />
                {root.children.map((child, i) => (
                  <div key={i} style={{ position: 'relative', display: 'flex', alignItems: 'center', gap: 8, paddingLeft: 16 }}>
                    <div style={{ position: 'absolute', left: -12, top: '50%', width: 12, height: 1, background: `${T.amber}40` }} />
                    <Sparkles style={{ width: 12, height: 12, color: `${T.amber}90`, flexShrink: 0 }} />
                    <span style={{ fontSize: 12, color: T.textPrim }}>{child}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}

          <div style={{ borderRadius: 12, border: `1px solid ${T.emerald}28`, background: `${T.emerald}04`, padding: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <Rocket style={{ width: 16, height: 16, color: T.emerald }} />
              <p style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.emerald, fontWeight: 700, margin: 0 }}>Impacto orgánico</p>
            </div>
            <p style={{ fontSize: 14, color: T.textSub, margin: 0, lineHeight: 1.6 }}>
              Tus <span style={{ color: T.amber, fontWeight: 700 }}>{HALL_OF_FAME.length} embajadores top</span> generaron{' '}
              <span style={{ color: T.emerald, fontWeight: 700, textShadow: '0 0 20px #10B98188' }}>${stats.referralRevenue.toLocaleString()}</span> en ventas referidas — sin invertir un peso en ads.
            </p>
          </div>
        </div>
      )}
    </section>
  )
}

// ─── Stat sub-components ────────────────────────────────────────────────────────

const StatMini = ({ label, value, color }: { label: string; value: string | number; color: string }) => (
  <div style={{ borderRadius: 8, padding: 8, background: 'rgba(255,255,255,0.03)', border: `1px solid ${T.border}` }}>
    <p style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, fontWeight: 700, marginBottom: 2 }}>{label}</p>
    <p style={{ fontSize: 14, fontWeight: 900, color, margin: 0, textShadow: `0 0 20px ${color}88` }}>{value}</p>
  </div>
)
