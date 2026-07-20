'use client'

/**
 * DEAL DOCTOR
 *
 * Diagnóstico médico de deals en riesgo. Por cada deal:
 *   - "Síntomas" detectados por IA
 *   - "Diagnóstico" automático
 *   - "Prescripción" — acción concreta que ya está en marcha o lista para ejecutar
 *   - Probabilidad de cierre (gauge)
 *
 * Garantiza que ningún deal se pierda por inacción.
 */

import { useState, useMemo } from 'react'
import {
  Stethoscope, Heart, Activity, Pill, Sparkles, Bot,
  Clock, AlertTriangle, CheckCircle2, ChevronRight, Play,
  TrendingDown, TrendingUp, Brain
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

type DealHealth = 'critical' | 'risk' | 'stable' | 'healthy'

interface Deal {
  id: string
  customer: string
  value: number
  stage: string
  daysSinceContact: number
  closeProbability: number
  health: DealHealth
  symptoms: { emoji: string; text: string }[]
  diagnosis: string
  prescription: {
    action: string
    technique: string
    confidence: number
    eta: string
    status: 'queued' | 'running' | 'done'
  }
  trend: 'up' | 'down' | 'flat'
}

const DEALS: Deal[] = [
  {
    id: 'd1',
    customer: 'Tomás N.',
    value: 2400,
    stage: 'Negociación',
    daysSinceContact: 4,
    closeProbability: 38,
    health: 'critical',
    symptoms: [
      { emoji: '👻', text: 'Sin respuesta hace 4 días' },
      { emoji: '💸', text: 'Pidió 30% descuento (rechazado)' },
      { emoji: '😶', text: 'Lectura confirmada pero no responde' },
    ],
    diagnosis: 'Ghosting clásico post-objeción de precio. Probable comparación con competidor.',
    prescription: {
      action: 'Mensaje con pregunta calibrada + bonus de cierre 48hs',
      technique: 'Protocolo de empatía calibrada',
      confidence: 87,
      eta: 'En 6 min',
      status: 'queued',
    },
    trend: 'down',
  },
  {
    id: 'd2',
    customer: 'Empresa Beta SRL',
    value: 8400,
    stage: 'Propuesta',
    daysSinceContact: 1,
    closeProbability: 64,
    health: 'risk',
    symptoms: [
      { emoji: '🤔', text: 'Múltiples decisores involucrados' },
      { emoji: '⏰', text: 'Plazo de decisión vence en 5 días' },
    ],
    diagnosis: 'Deal complejo — falta identificar Decisor económico y Champion interno.',
    prescription: {
      action: 'Email a Champion + meeting con Decisor económico',
      technique: 'Habilitación de champion interno',
      confidence: 79,
      eta: 'En 2h',
      status: 'running',
    },
    trend: 'up',
  },
  {
    id: 'd3',
    customer: 'Mariana P.',
    value: 850,
    stage: 'Cierre',
    daysSinceContact: 0,
    closeProbability: 82,
    health: 'stable',
    symptoms: [
      { emoji: '✋', text: 'Pidió un día para hablar con su socio' },
    ],
    diagnosis: 'Objeción clásica de "necesito consultar". IA activó protocolo de cierre.',
    prescription: {
      action: 'Follow-up automático mañana 10am con bonus de urgencia · audio personalizado',
      technique: 'Cierre asuntivo + escasez',
      confidence: 91,
      eta: 'Mañana 10:00',
      status: 'queued',
    },
    trend: 'up',
  },
  {
    id: 'd4',
    customer: 'Carlos R.',
    value: 1200,
    stage: 'Calificación',
    daysSinceContact: 8,
    closeProbability: 22,
    health: 'critical',
    symptoms: [
      { emoji: '🥶', text: 'Lead frío hace 8 días' },
      { emoji: '🚫', text: 'Cambió de timezone sin avisar' },
      { emoji: '💡', text: 'Última conversación fue muy positiva' },
    ],
    diagnosis: 'Lead potencial pero perdido por inactividad. Necesita re-activación con valor previo.',
    prescription: {
      action: 'Secuencia reactivación 4 toques: video → caso éxito → oferta → urgencia',
      technique: 'Presión temporal + experiencia premium',
      confidence: 64,
      eta: 'Iniciando ahora',
      status: 'running',
    },
    trend: 'flat',
  },
]

const HEALTH_CONFIG: Record<DealHealth, { label: string; color: string; pulse: boolean }> = {
  critical: { label: 'Crítico',    color: T.rose,    pulse: true  },
  risk:     { label: 'En riesgo',  color: T.amber,   pulse: true  },
  stable:   { label: 'Estable',    color: '#3b82f6', pulse: false },
  healthy:  { label: 'Saludable',  color: T.emerald, pulse: false },
}

export default function DealDoctor() {
  const [expandedId, setExpandedId] = useState<string | null>(DEALS[0]?.id ?? null)

  const stats = useMemo(() => {
    const critical = DEALS.filter(d => d.health === 'critical').length
    const totalValue = DEALS.reduce((s, d) => s + d.value, 0)
    const recoverable = DEALS.reduce((s, d) => s + (d.value * d.closeProbability / 100), 0)
    return { critical, totalValue, recoverable }
  }, [])

  return (
    <section style={{
      background: T.bgCard,
      border: `1px solid ${T.border}`,
      borderRadius: 16,
      overflow: 'hidden',
      position: 'relative',
    }}>
      {/* Top accent line */}
      <div style={{ height: 1, background: `linear-gradient(90deg, transparent, ${T.rose}80, transparent)` }} />

      {/* Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: `1px solid ${T.border}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 12,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 40, height: 40, borderRadius: 10,
            background: `${T.rose}22`,
            border: `1px solid ${T.rose}44`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Stethoscope style={{ width: 20, height: 20, color: T.rose, filter: `drop-shadow(0 0 8px ${T.rose}99)` }} />
          </div>
          <div>
            <h2 style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, letterSpacing: '.08em', textTransform: 'uppercase', margin: 0 }}>
              DEAL DOCTOR
              <span style={{ color: T.textSub, fontWeight: 400, textTransform: 'none', letterSpacing: 'normal', marginLeft: 8 }}>· Sin deal perdido</span>
            </h2>
            <p style={{ fontSize: 11, color: T.textSub, margin: 0, marginTop: 2 }}>Diagnóstico médico de cada deal · IA prescribe la próxima acción</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            padding: '6px 12px', borderRadius: 8,
            background: `${T.rose}18`, border: `1px solid ${T.rose}40`,
            display: 'flex', alignItems: 'center', gap: 6,
          }}>
            <div className="animate-pulse" style={{ width: 6, height: 6, borderRadius: '50%', background: T.rose }} />
            <span style={{ fontSize: 12, color: T.rose, fontWeight: 600 }}>{stats.critical} críticos</span>
          </div>
          <div style={{
            padding: '6px 12px', borderRadius: 8,
            background: `${T.emerald}18`, border: `1px solid ${T.emerald}40`,
          }}>
            <span style={{ fontSize: 12, color: T.emerald, fontWeight: 600 }}>${stats.recoverable.toFixed(0)} recuperables</span>
          </div>
        </div>
      </div>

      {/* Quick stats bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', borderBottom: `1px solid ${T.border}` }}>
        <StatTile label="Deals analizados" value={DEALS.length} sub="bajo monitoreo" icon={Heart} color={T.rose} />
        <StatTile label="En tratamiento" value={DEALS.filter(d => d.prescription.status === 'running').length} sub="acciones IA activas" icon={Activity} color={T.emerald} />
        <StatTile label="Valor en riesgo" value={`$${(stats.totalValue / 1000).toFixed(1)}k`} sub="potencial total" icon={AlertTriangle} color={T.amber} />
        <StatTile label="Confianza recovery" value={`${Math.round((stats.recoverable / stats.totalValue) * 100)}%`} sub="vs valor total" icon={Brain} color={T.violet} />
      </div>

      {/* Deal list */}
      <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {DEALS.map(deal => {
          const isExpanded = expandedId === deal.id
          const cfg = HEALTH_CONFIG[deal.health]
          return (
            <div key={deal.id} style={{
              position: 'relative',
              background: `${cfg.color}08`,
              border: `1px solid ${cfg.color}30`,
              borderRadius: 12,
              overflow: 'hidden',
            }}>
              {/* Health pulse bar on left */}
              <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 3, background: cfg.color }} />
              {cfg.pulse && (
                <div className="animate-pulse" style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 3, background: cfg.color }} />
              )}

              {/* Row header */}
              <button
                onClick={() => setExpandedId(isExpanded ? null : deal.id)}
                style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: 12,
                  padding: 12, background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left',
                }}
              >
                {/* Probability gauge */}
                <div style={{ position: 'relative', width: 48, height: 48, flexShrink: 0 }}>
                  <svg style={{ width: 48, height: 48, transform: 'rotate(-90deg)' }} viewBox="0 0 40 40">
                    <circle cx="20" cy="20" r="16" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="3" />
                    <circle
                      cx="20" cy="20" r="16"
                      fill="none"
                      stroke={cfg.color}
                      strokeWidth="3"
                      strokeLinecap="round"
                      strokeDasharray={`${(deal.closeProbability / 100) * 100.5} 100.5`}
                      style={{ filter: `drop-shadow(0 0 4px ${cfg.color}80)` }}
                    />
                  </svg>
                  <span style={{
                    position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 11, fontWeight: 700, color: T.textPrim,
                    textShadow: `0 0 20px ${cfg.color}88`,
                  }}>
                    {deal.closeProbability}%
                  </span>
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    <span style={{ fontSize: 14, fontWeight: 700, color: T.textPrim }}>{deal.customer}</span>
                    <span style={{
                      fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase',
                      padding: '2px 8px', borderRadius: 4,
                      background: `${cfg.color}18`, border: `1px solid ${cfg.color}28`, color: cfg.color,
                    }}>{cfg.label}</span>
                    <span style={{ fontSize: 10, color: T.textSub, fontFamily: 'monospace' }}>· {deal.stage}</span>
                    {deal.trend === 'up' && <TrendingUp style={{ width: 12, height: 12, color: T.emerald }} />}
                    {deal.trend === 'down' && <TrendingDown style={{ width: 12, height: 12, color: T.rose }} />}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 4, fontSize: 10, color: T.textSub }}>
                    <span style={{ color: T.emerald, fontWeight: 600, textShadow: '0 0 20px #10B98188' }}>${deal.value.toLocaleString()}</span>
                    <span>·</span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <Clock style={{ width: 10, height: 10 }} />
                      {deal.daysSinceContact === 0 ? 'Hoy' : `${deal.daysSinceContact}d sin contacto`}
                    </span>
                  </div>
                </div>

                {/* Prescription status pill */}
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  padding: '4px 8px', borderRadius: 8, flexShrink: 0,
                  background: deal.prescription.status === 'running'
                    ? `${T.emerald}18`
                    : deal.prescription.status === 'done'
                      ? `${T.violet}18`
                      : 'rgba(255,255,255,0.04)',
                }}>
                  {deal.prescription.status === 'running' && (
                    <>
                      <Activity className="animate-pulse" style={{ width: 12, height: 12, color: T.emerald }} />
                      <span style={{ fontSize: 10, color: T.emerald, fontFamily: 'monospace', textTransform: 'uppercase' }}>RX activo</span>
                    </>
                  )}
                  {deal.prescription.status === 'queued' && (
                    <>
                      <Pill style={{ width: 12, height: 12, color: T.amber }} />
                      <span style={{ fontSize: 10, color: T.amber, fontFamily: 'monospace', textTransform: 'uppercase' }}>RX listo</span>
                    </>
                  )}
                  {deal.prescription.status === 'done' && (
                    <>
                      <CheckCircle2 style={{ width: 12, height: 12, color: T.violet }} />
                      <span style={{ fontSize: 10, color: T.violet, fontFamily: 'monospace', textTransform: 'uppercase' }}>curado</span>
                    </>
                  )}
                </div>

                <ChevronRight style={{
                  width: 16, height: 16, color: T.textSub, flexShrink: 0,
                  transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)',
                  transition: 'transform 0.2s',
                }} />
              </button>

              {/* Expanded body */}
              {isExpanded && (
                <div style={{ padding: '0 12px 12px', borderTop: `1px solid ${T.border}`, display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {/* Symptoms */}
                  <div style={{ paddingTop: 12 }}>
                    <p style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, marginBottom: 8, fontWeight: 700 }}>SÍNTOMAS DETECTADOS</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {deal.symptoms.map((s, i) => (
                        <span key={i} style={{
                          display: 'inline-flex', alignItems: 'center', gap: 6,
                          padding: '4px 8px', borderRadius: 8,
                          background: 'rgba(255,255,255,0.04)', border: `1px solid ${T.border}`,
                          fontSize: 11, color: T.textPrim,
                        }}>
                          <span>{s.emoji}</span>{s.text}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Diagnosis */}
                  <div style={{
                    borderRadius: 8, padding: 10,
                    background: 'rgba(255,255,255,0.03)', border: `1px solid ${T.border}`,
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                      <Brain style={{ width: 12, height: 12, color: T.violet }} />
                      <p style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.violet, fontWeight: 700 }}>DIAGNÓSTICO IA</p>
                    </div>
                    <p style={{ fontSize: 12, color: T.textPrim, fontStyle: 'italic', lineHeight: 1.5 }}>&ldquo;{deal.diagnosis}&rdquo;</p>
                  </div>

                  {/* Prescription */}
                  <div style={{
                    borderRadius: 8, padding: 12,
                    background: `${T.emerald}08`, border: `1px solid ${T.emerald}30`,
                  }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, marginBottom: 8 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Pill style={{ width: 14, height: 14, color: T.emerald }} />
                        <p style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.emerald, fontWeight: 700 }}>PRESCRIPCIÓN</p>
                      </div>
                      <span style={{ fontSize: 10, color: T.textSub, fontFamily: 'monospace', display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Clock style={{ width: 10, height: 10 }} />
                        {deal.prescription.eta}
                      </span>
                    </div>
                    <p style={{ fontSize: 14, fontWeight: 600, color: T.textPrim, marginBottom: 6 }}>{deal.prescription.action}</p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                      <span style={{
                        display: 'inline-flex', alignItems: 'center', gap: 4,
                        padding: '2px 8px', borderRadius: 6,
                        background: `${T.violet}18`, border: `1px solid ${T.violet}28`, color: T.violet,
                        fontSize: 10, fontFamily: 'monospace',
                      }}>
                        <Bot style={{ width: 10, height: 10 }} />
                        {deal.prescription.technique}
                      </span>
                      <span style={{ fontSize: 10, color: T.textSub }}>·</span>
                      <span style={{ fontSize: 10, color: T.textSub }}>
                        Confianza IA: <span style={{ color: T.emerald, fontWeight: 700, textShadow: '0 0 20px #10B98188' }}>{deal.prescription.confidence}%</span>
                      </span>
                    </div>

                    {deal.prescription.status === 'queued' && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 12 }}>
                        <button style={{
                          flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                          padding: '8px 12px', borderRadius: 8,
                          background: `${T.emerald}20`, border: `1px solid ${T.emerald}40`, color: T.emerald,
                          fontSize: 12, fontWeight: 600, cursor: 'pointer',
                        }}>
                          <Play style={{ width: 12, height: 12 }} />
                          Ejecutar ahora
                        </button>
                        <button style={{
                          padding: '8px 12px', borderRadius: 8,
                          background: 'rgba(255,255,255,0.05)', border: `1px solid ${T.border}`,
                          color: T.textSub, fontSize: 12, cursor: 'pointer',
                        }}>
                          Personalizar
                        </button>
                      </div>
                    )}
                    {deal.prescription.status === 'running' && (
                      <div style={{
                        display: 'flex', alignItems: 'center', gap: 8, marginTop: 12,
                        padding: '8px 12px', borderRadius: 8,
                        background: `${T.emerald}05`, border: `1px solid ${T.emerald}20`,
                      }}>
                        <div style={{ display: 'flex', gap: 4 }}>
                          <div className="animate-bounce" style={{ width: 4, height: 4, borderRadius: '50%', background: T.emerald }} />
                          <div className="animate-bounce" style={{ width: 4, height: 4, borderRadius: '50%', background: T.emerald, animationDelay: '0.15s' }} />
                          <div className="animate-bounce" style={{ width: 4, height: 4, borderRadius: '50%', background: T.emerald, animationDelay: '0.3s' }} />
                        </div>
                        <span style={{ fontSize: 11, color: T.emerald, fontWeight: 500 }}>Ejecutándose ahora...</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </section>
  )
}

// ─── Stat Tile ─────────────────────────────────────────────────────────────────

interface StatTileProps {
  label: string
  value: string | number
  sub: string
  icon: React.ElementType
  color: string
}

const StatTile = ({ label, value, sub, icon: Icon, color }: StatTileProps) => (
  <div style={{ padding: 12, borderRight: `1px solid ${T.border}` }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
      <Icon style={{ width: 12, height: 12, color }} />
      <p style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, fontWeight: 700, margin: 0 }}>{label}</p>
    </div>
    <p style={{ fontSize: 18, fontWeight: 900, color: T.textPrim, margin: 0, textShadow: `0 0 20px ${color}88` }}>{value}</p>
    <p style={{ fontSize: 10, color: T.textSub, margin: 0, marginTop: 2 }}>{sub}</p>
  </div>
)
