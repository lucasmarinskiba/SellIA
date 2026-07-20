'use client'

/**
 * RECOVERY LAB
 *
 * "Cámara de resurrección" — nada se pierde definitivamente.
 *
 * 3 sub-tanques:
 *   1. Carritos abandonados (compraron y se fueron)
 *   2. Leads fríos (no respondieron)
 *   3. Cerrados perdidos (dijeron NO)
 */

import { useState, useMemo } from 'react'
import {
  FlaskConical, RefreshCw, Skull, Snowflake,
  Heart, Activity, Bot, Sparkles, TrendingUp, ChevronRight,
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

type RecoveryCategory = 'cart' | 'cold' | 'lost'

interface RecoveryLead {
  id: string
  customer: string
  daysDead: number
  lastValue: number
  category: RecoveryCategory
  technique: string
  protocol: string[]
  progress: number
  successRate: number
  status: 'reviving' | 'engaged' | 'recovered' | 'flatlined'
  lastTouch: string
}

const RECOVERY_LEADS: RecoveryLead[] = [
  { id: 'r1', customer: 'María L.',             daysDead: 3,  lastValue: 1240, category: 'cart', technique: 'Recuperación de carrito · Escasez + Bonus',      protocol: ['Recordatorio 1h', 'Reseña social proof', 'Bonus por completar hoy', 'Descuento 10% último intento'], progress: 75, successRate: 68, status: 'engaged',  lastTouch: 'Abrió email hace 12min' },
  { id: 'r2', customer: 'Pedro K.',             daysDead: 1,  lastValue: 890,  category: 'cart', technique: 'Recuperación de carrito · Regalo Sorpresa',       protocol: ['Recordatorio amable', 'Regalo sorpresa + bonus', 'Urgencia genuina'],                              progress: 50, successRate: 82, status: 'reviving', lastTouch: 'WhatsApp leído' },
  { id: 'r3', customer: 'Carlos R.',            daysDead: 14, lastValue: 3200, category: 'cold', technique: 'Presión temporal + re-stack de valor',            protocol: ['Caso de éxito relacionado', 'Video tutorial gratis', 'Oferta personalizada', 'Última oportunidad'], progress: 35, successRate: 41, status: 'reviving', lastTouch: 'Sin actividad' },
  { id: 'r4', customer: 'Lucía F. (e-commerce)',daysDead: 21, lastValue: 5400, category: 'cold', technique: 'Sorpresa estratégica · reactivación CX premium',  protocol: ['Email "Cómo te fue?"', 'Bonus regalo no esperado', 'Reagendar demo'],                              progress: 88, successRate: 73, status: 'engaged',  lastTouch: 'Respondió "interesa"' },
  { id: 'r5', customer: 'Empresa Beta SRL',     daysDead: 45, lastValue: 8400, category: 'lost', technique: 'Recuperación · Pivot de precio',                  protocol: ['Diagnóstico cualitativo', 'Plan alternativo más económico', 'Garantía extendida', 'Caso éxito similar'], progress: 60, successRate: 38, status: 'reviving', lastTouch: 'Solicitó info' },
  { id: 'r6', customer: 'Tomás N.',             daysDead: 7,  lastValue: 2400, category: 'lost', technique: 'Re-entrada calibrada',                            protocol: ['Pregunta calibrada de apertura', 'Acknowledge dolor pasado', 'Oferta sin descuento + bono'],       progress: 92, successRate: 65, status: 'engaged',  lastTouch: 'Audio respondido' },
]

const CATEGORY_CONFIG: Record<RecoveryCategory, { label: string; emoji: string; icon: React.ElementType; color: string; description: string; successAvg: number }> = {
  cart: { label: 'Carritos abandonados', emoji: '🛒', icon: RefreshCw, color: T.amber,  description: 'Recovery rate hasta 75%', successAvg: 75 },
  cold: { label: 'Leads fríos',          emoji: '🥶', icon: Snowflake, color: T.cyan,   description: 'Recovery rate hasta 57%', successAvg: 57 },
  lost: { label: 'Cerrados perdidos',    emoji: '💀', icon: Skull,     color: T.rose,   description: 'Recovery rate hasta 51%', successAvg: 51 },
}

const STATUS_CONFIG: Record<RecoveryLead['status'], { label: string; color: string }> = {
  reviving:  { label: 'En reanimación', color: T.amber },
  engaged:   { label: 'Respondiendo',   color: T.emerald },
  recovered: { label: 'Recuperado',     color: T.violet },
  flatlined: { label: 'Sin respuesta',  color: '#6b7280' },
}

export default function RecoveryLab() {
  const [filter, setFilter] = useState<RecoveryCategory | 'all'>('all')
  const [expandedId, setExpandedId] = useState<string | null>(RECOVERY_LEADS[0]?.id ?? null)

  const filtered = useMemo(
    () => filter === 'all' ? RECOVERY_LEADS : RECOVERY_LEADS.filter(l => l.category === filter),
    [filter]
  )

  const stats = useMemo(() => {
    const totalValue = RECOVERY_LEADS.reduce((s, l) => s + l.lastValue, 0)
    const expectedRecovery = RECOVERY_LEADS.reduce((s, l) => s + (l.lastValue * l.successRate / 100), 0)
    return { totalValue, expectedRecovery, count: RECOVERY_LEADS.length }
  }, [])

  const categoryCounts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const l of RECOVERY_LEADS) c[l.category] = (c[l.category] || 0) + 1
    return c
  }, [])

  return (
    <section style={{ background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 16, overflow: 'hidden', position: 'relative' }}>
      {/* Top accent */}
      <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, ' + T.cyan + '80, transparent)' }} />

      {/* Bubbling decorators */}
      <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'hidden', opacity: 0.25 }}>
        <div className="animate-bounce" style={{ position: 'absolute', bottom: 16, left: '10%', width: 4, height: 4, borderRadius: '50%', background: T.cyan + '66', animationDuration: '3s' }} />
        <div className="animate-bounce" style={{ position: 'absolute', bottom: 32, left: '25%', width: 2, height: 2, borderRadius: '50%', background: T.cyan + '88', animationDuration: '4s', animationDelay: '.5s' }} />
        <div className="animate-bounce" style={{ position: 'absolute', bottom: 8,  left: '60%', width: 4, height: 4, borderRadius: '50%', background: T.cyan + '66', animationDuration: '3.5s', animationDelay: '1s' }} />
      </div>

      {/* Header */}
      <div style={{ position: 'relative', padding: '16px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ position: 'relative', width: 40, height: 40, borderRadius: 10, background: T.cyan + '22', border: '1px solid ' + T.cyan + '44', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <FlaskConical size={18} style={{ color: T.cyan, filter: 'drop-shadow(0 0 8px ' + T.cyan + 'aa)' }} />
            <div className="animate-pulse" style={{ position: 'absolute', top: -4, right: -4, width: 10, height: 10, borderRadius: '50%', background: T.cyan }} />
          </div>
          <div>
            <h2 style={{ fontSize: 13, fontWeight: 900, color: T.textPrim, letterSpacing: '.06em', textTransform: 'uppercase', margin: 0 }}>
              RECOVERY LAB <span style={{ color: T.textSub, fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>· Nada se pierde</span>
            </h2>
            <p style={{ fontSize: 11, color: T.textSub, marginTop: 2 }}>Cámara de resurrección · IA aplica protocolos de recovery</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ padding: '6px 12px', borderRadius: 8, background: T.bgApp, border: '1px solid ' + T.border }}>
            <span style={{ fontSize: 11, color: T.textPrim }}><span style={{ color: T.textSub, fontSize: 10 }}>Resucitando: </span><b>{stats.count} leads</b></span>
          </div>
          <div style={{ padding: '6px 12px', borderRadius: 8, background: T.emerald + '15', border: '1px solid ' + T.emerald + '35' }}>
            <span style={{ fontSize: 11, color: T.emerald, fontWeight: 700 }}>+${stats.expectedRecovery.toFixed(0)} esperados</span>
          </div>
        </div>
      </div>

      {/* Category filter chips */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', borderBottom: '1px solid ' + T.border }}>
        {(Object.keys(CATEGORY_CONFIG) as RecoveryCategory[]).map(cat => {
          const cfg = CATEGORY_CONFIG[cat]
          const Icon = cfg.icon
          const active = filter === cat
          const count = categoryCounts[cat] || 0
          return (
            <button
              key={cat}
              onClick={() => setFilter(active ? 'all' : cat)}
              style={{
                position: 'relative', padding: 16, textAlign: 'left', cursor: 'pointer',
                background: active ? cfg.color + '10' : 'transparent',
                border: 'none', borderRight: '1px solid ' + T.border,
              }}
            >
              {active && <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: cfg.color }} />}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                <div style={{ width: 28, height: 28, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', background: cfg.color + '15', border: '1px solid ' + cfg.color + '30' }}>
                  <Icon size={14} style={{ color: cfg.color }} />
                </div>
                <span style={{ fontSize: 22, fontWeight: 900, color: T.textPrim, fontVariantNumeric: 'tabular-nums' }}>{count}</span>
              </div>
              <p style={{ fontSize: 11, fontWeight: 700, color: T.textPrim, textTransform: 'uppercase', letterSpacing: '.04em' }}>{cfg.label}</p>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 4 }}>
                <p style={{ fontSize: 10, color: T.textSub }}>{cfg.description}</p>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Activity size={10} style={{ color: cfg.color }} />
                  <span style={{ fontSize: 10, fontWeight: 700, color: cfg.color }}>{cfg.successAvg}%</span>
                </div>
              </div>
            </button>
          )
        })}
      </div>

      {/* Leads list */}
      <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {filtered.map(lead => {
          const cfg = CATEGORY_CONFIG[lead.category]
          const status = STATUS_CONFIG[lead.status]
          const isExpanded = expandedId === lead.id
          return (
            <div
              key={lead.id}
              style={{
                position: 'relative', borderRadius: 12, overflow: 'hidden',
                background: T.bgApp,
                border: '1px solid ' + (lead.status === 'engaged' ? cfg.color + '40' : T.border),
              }}
            >
              {/* Progress bar at top */}
              <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: T.border }}>
                <div style={{ height: '100%', background: 'linear-gradient(90deg, ' + cfg.color + '80, ' + cfg.color + ')', width: `${lead.progress}%`, boxShadow: '0 0 6px ' + cfg.color }} />
              </div>

              <button
                onClick={() => setExpandedId(isExpanded ? null : lead.id)}
                style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 12, padding: '12px 12px 12px 12px', paddingTop: 14, textAlign: 'left', cursor: 'pointer', background: 'transparent', border: 'none' }}
              >
                <div style={{ position: 'relative', width: 40, height: 40, flexShrink: 0 }}>
                  <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: cfg.color + '10', border: '1px solid ' + cfg.color + '30' }}>
                    <Heart size={16} style={{ color: cfg.color }} />
                  </div>
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    <span style={{ fontSize: 18 }}>{cfg.emoji}</span>
                    <span style={{ fontSize: 14, fontWeight: 700, color: T.textPrim }}>{lead.customer}</span>
                    <span style={{ fontSize: 10, color: T.textSub }}>· Murió hace {lead.daysDead}d</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4, flexWrap: 'wrap' }}>
                    <span style={{ fontSize: 10, fontWeight: 600, color: status.color }}>{status.label}</span>
                    <span style={{ fontSize: 10, color: T.emerald, fontWeight: 600 }}>${lead.lastValue.toLocaleString()}</span>
                    <span style={{ fontSize: 10, color: T.textSub }}>{lead.successRate}% éxito IA</span>
                  </div>
                </div>

                {/* Circular gauge */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
                  <div style={{ position: 'relative', width: 40, height: 40 }}>
                    <svg style={{ width: 40, height: 40, transform: 'rotate(-90deg)' }} viewBox="0 0 36 36">
                      <circle cx="18" cy="18" r="14" fill="none" stroke={T.border} strokeWidth="3" />
                      <circle cx="18" cy="18" r="14" fill="none" stroke={cfg.color} strokeWidth="3" strokeLinecap="round" strokeDasharray={`${(lead.progress / 100) * 88} 88`} />
                    </svg>
                    <span style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 9, fontWeight: 700, color: T.textPrim }}>{lead.progress}%</span>
                  </div>
                  <span style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', textTransform: 'uppercase', color: T.textSub, marginTop: 2 }}>protocolo</span>
                </div>

                <ChevronRight size={16} style={{ color: T.textSub, flexShrink: 0, transform: isExpanded ? 'rotate(90deg)' : 'none', transition: 'transform .2s' }} />
              </button>

              {isExpanded && (
                <div style={{ padding: '0 12px 12px', borderTop: '1px solid ' + T.border, display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {/* Technique badge */}
                  <div style={{ paddingTop: 12, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '4px 8px', borderRadius: 8, background: T.violet + '15', border: '1px solid ' + T.violet + '30', fontSize: 10, color: T.violet, fontFamily: 'monospace' }}>
                      <Bot size={10} />
                      {lead.technique}
                    </span>
                    <span style={{ fontSize: 10, color: T.textSub }}>· Último contacto: {lead.lastTouch}</span>
                  </div>

                  {/* Protocol steps */}
                  <div>
                    <p style={{ fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 4 }}>
                      PROTOCOLO DE RECOVERY
                    </p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      {lead.protocol.map((step, i) => {
                        const totalSteps = lead.protocol.length
                        const currentStep = Math.floor((lead.progress / 100) * totalSteps)
                        const stepDone = i < currentStep
                        const stepCurrent = i === currentStep && lead.progress < 100
                        const stepBg = stepDone ? T.emerald + '10' : stepCurrent ? T.amber + '10' : T.bgCard
                        const stepBorder = stepDone ? T.emerald + '28' : stepCurrent ? T.amber + '40' : T.border
                        return (
                          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px', borderRadius: 8, background: stepBg, border: '1px solid ' + stepBorder }}>
                            <div style={{ width: 20, height: 20, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, background: stepDone ? T.emerald + '20' : stepCurrent ? T.amber + '20' : T.bgApp, border: '1px solid ' + (stepDone ? T.emerald + '40' : stepCurrent ? T.amber + '40' : T.border) }}>
                              {stepDone
                                ? <Sparkles size={10} style={{ color: T.emerald }} />
                                : stepCurrent
                                ? <div className="animate-pulse" style={{ width: 6, height: 6, borderRadius: '50%', background: T.amber }} />
                                : <span style={{ fontSize: 9, fontWeight: 700, color: T.textSub }}>{i + 1}</span>
                              }
                            </div>
                            <span style={{ fontSize: 12, color: stepDone ? T.textSub : stepCurrent ? T.textPrim : T.textSub, fontWeight: stepCurrent ? 700 : 400, textDecoration: stepDone ? 'line-through' : 'none' }}>
                              {step}
                            </span>
                            {stepCurrent && (
                              <span className="animate-pulse" style={{ marginLeft: 'auto', fontSize: 9, color: T.amber, fontFamily: 'monospace', textTransform: 'uppercase' }}>EN MARCHA</span>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  {/* Action */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, paddingTop: 4 }}>
                    <div style={{ fontSize: 10, color: T.textSub, display: 'flex', alignItems: 'center', gap: 4 }}>
                      <Activity size={10} style={{ color: cfg.color }} />
                      IA controlando · sin necesidad de tu intervención
                    </div>
                    <button style={{ padding: '6px 14px', borderRadius: 8, background: T.bgCard, border: '1px solid ' + T.border, color: T.textSub, fontSize: 10, fontWeight: 600, cursor: 'pointer' }}>
                      Intervenir manual
                    </button>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Footer */}
      <div style={{ padding: '12px 20px', borderTop: '1px solid ' + T.border, background: T.bgApp, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <TrendingUp size={14} style={{ color: T.emerald }} />
          <span style={{ fontSize: 11, color: T.textSub }}>
            Valor potencial recuperable: <span style={{ color: T.textPrim, fontWeight: 700 }}>${stats.totalValue.toLocaleString()}</span>
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 10, color: T.textSub }}>Recovery rate sistema:</span>
          <span style={{ fontSize: 11, color: T.emerald, fontWeight: 700, textShadow: '0 0 20px ' + T.emerald + '88' }}>
            {Math.round((stats.expectedRecovery / stats.totalValue) * 100)}%
          </span>
        </div>
      </div>
    </section>
  )
}
