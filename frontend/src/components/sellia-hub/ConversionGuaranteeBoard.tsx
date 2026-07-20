'use client'

/**
 * CONVERSION GUARANTEE BOARD
 *
 * "El sistema garantiza ventas" — visualización que da CERTEZA al usuario:
 *
 * 1. Forecast cone (3 escenarios: pesimista / esperado / optimista) — próximos 30 días
 * 2. Confianza global con score visual
 * 3. Trust factors (lo que ya cerramos / pipeline maduro / IA en marcha)
 * 4. Risk factors (lo que puede fallar + cómo lo mitigamos)
 * 5. Garantías activas en oferta actual
 */

import { useMemo, useState } from 'react'
import {
  Shield, CheckCircle2, Sparkles,
  Target, Zap, Award, Brain, AlertTriangle
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

interface ForecastPoint {
  day: number
  pessimistic: number
  expected: number
  optimistic: number
}

interface TrustFactor {
  id: string
  icon: React.ElementType
  title: string
  value: string
  impact: string
  color: string
}

interface Guarantee {
  id: string
  emoji: string
  title: string
  description: string
  type: 'money-back' | 'performance' | 'time' | 'result'
}

const generateForecast = (): ForecastPoint[] => {
  const points: ForecastPoint[] = []
  for (let day = 1; day <= 30; day++) {
    const base = 320 * day
    const variance = Math.sin(day * 0.7) * 200 + Math.cos(day * 0.3) * 150
    const expected = Math.round(base + variance + 200)
    const pessimistic = Math.round(expected * 0.62)
    const optimistic = Math.round(expected * 1.42)
    points.push({ day, pessimistic, expected, optimistic })
  }
  return points
}

const TRUST_FACTORS: TrustFactor[] = [
  { id: 'closed',    icon: CheckCircle2, title: 'Cerrado este mes',          value: '$8,247',        impact: 'Base sólida',  color: T.emerald  },
  { id: 'pipeline',  icon: Target,       title: 'Pipeline maduro (>70% prob)', value: '12 deals · $14k', impact: 'Cierre alto',  color: '#3b82f6'  },
  { id: 'ai-active', icon: Brain,        title: 'IA trabajando 24/7',         value: '142 acciones/día', impact: 'Velocidad x4', color: T.violet   },
  { id: 'autopilot', icon: Zap,          title: 'Autopilot ON · 4 pilares',   value: '99.8% uptime',  impact: 'Sin pérdidas', color: T.amber    },
]

type RiskSeverity = 'high' | 'medium' | 'low'
const RISK_FACTORS: { id: string; emoji: string; title: string; mitigation: string; severity: RiskSeverity }[] = [
  { id: 'r1', emoji: '⚠️', title: 'Estacionalidad baja en mayo', mitigation: 'IA activó promo automática · NPS bonus', severity: 'medium' },
  { id: 'r2', emoji: '🔍', title: '3 deals sin actividad >7 días', mitigation: 'Auto-reactivación con presión temporal + bonus', severity: 'low' },
  { id: 'r3', emoji: '💸', title: 'Carrito abandonado: $1.8k', mitigation: 'Secuencia de recuperación 4 toques activa', severity: 'low' },
]

const ACTIVE_GUARANTEES: Guarantee[] = [
  { id: 'g1', emoji: '💰', title: 'Money-back 30 días', description: 'Si no ven resultado, devolución 100%. Reduce fricción en cierre.', type: 'money-back' },
  { id: 'g2', emoji: '📈', title: 'ROI 3× o no pagás', description: 'Triple del precio en valor recuperado o continúa gratis hasta lograrlo.', type: 'performance' },
  { id: 'g3', emoji: '⚡', title: 'Onboarding 48h o gratis', description: 'Primera victoria del cliente en 48hs o devolvemos el setup.', type: 'time' },
]

export default function ConversionGuaranteeBoard() {
  const forecast = useMemo(generateForecast, [])
  const [hoveredDay, setHoveredDay] = useState<number | null>(null)

  const totals = useMemo(() => {
    const last = forecast[forecast.length - 1]
    return { pessimistic: last.pessimistic, expected: last.expected, optimistic: last.optimistic }
  }, [forecast])

  const confidence = 87
  const targetRevenue = 12000
  const projectedRevenue = totals.expected
  const meetsTarget = projectedRevenue >= targetRevenue

  const W = 600
  const H = 180
  const maxY = totals.optimistic * 1.05
  const xStep = W / 29

  const pointsToPath = (key: 'pessimistic' | 'expected' | 'optimistic'): string =>
    forecast.map((p, i) => {
      const x = i * xStep
      const y = H - (p[key] / maxY) * H
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`
    }).join(' ')

  const conePath = useMemo(() => {
    const top = forecast.map((p, i) => `${i === 0 ? 'M' : 'L'} ${i * xStep} ${H - (p.optimistic / maxY) * H}`).join(' ')
    const bottom = forecast.slice().reverse().map((p, i) => {
      const idx = forecast.length - 1 - i
      return `L ${idx * xStep} ${H - (p.pessimistic / maxY) * H}`
    }).join(' ')
    return `${top} ${bottom} Z`
  }, [forecast, xStep, maxY])

  const hoveredPoint = hoveredDay !== null ? forecast[hoveredDay - 1] : null

  const severityColor = (s: RiskSeverity) =>
    s === 'high' ? T.rose : s === 'medium' ? T.amber : T.textSub

  return (
    <section style={{ background: T.bgCard, border: `1px solid ${T.border}`, borderRadius: 16, overflow: 'hidden' }}>
      <div style={{ height: 1, background: `linear-gradient(90deg, transparent, ${T.emerald}80, transparent)` }} />

      {/* Header */}
      <div style={{
        padding: '16px 20px', borderBottom: `1px solid ${T.border}`,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ position: 'relative', width: 40, height: 40, borderRadius: 10, background: `${T.emerald}22`, border: `1px solid ${T.emerald}44`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Shield style={{ width: 20, height: 20, color: T.emerald, filter: `drop-shadow(0 0 8px ${T.emerald}b0)` }} />
            <div className="animate-pulse" style={{ position: 'absolute', top: -4, right: -4, width: 12, height: 12, borderRadius: '50%', background: T.emerald }} />
          </div>
          <div>
            <h2 style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, letterSpacing: '.08em', textTransform: 'uppercase', margin: 0 }}>
              SALES GUARANTEE
              <span style={{ color: T.textSub, fontWeight: 400, textTransform: 'none', letterSpacing: 'normal', marginLeft: 8 }}>Engine</span>
              <span style={{
                fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase',
                padding: '2px 8px', borderRadius: 12, marginLeft: 8,
                background: `${T.emerald}18`, border: `1px solid ${T.emerald}28`, color: T.emerald,
              }}>CERTEZA · {confidence}%</span>
            </h2>
            <p style={{ fontSize: 11, color: T.textSub, margin: 0, marginTop: 2 }}>El sistema proyecta, garantiza y mitiga riesgos en tiempo real</p>
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <p style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, margin: 0 }}>Proyección 30d</p>
          <p style={{ fontSize: 28, fontWeight: 900, color: meetsTarget ? T.emerald : T.amber, margin: 0, textShadow: meetsTarget ? '0 0 20px #10B98188' : '0 0 20px #F59E0B88' }}>
            ${(projectedRevenue / 1000).toFixed(1)}k
          </p>
          <p style={{ fontSize: 10, color: T.textSub, margin: 0 }}>
            Meta: ${(targetRevenue / 1000).toFixed(0)}k {meetsTarget ? '✓ Superada' : '· en camino'}
          </p>
        </div>
      </div>

      {/* Body: Chart + side panel */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 16, padding: 20 }}>
        {/* Forecast chart */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 10, color: T.textSub, textTransform: 'uppercase', letterSpacing: '.06em' }}>
            <span>Cono de confianza · próximos 30 días</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 8, height: 8, borderRadius: 2, background: `${T.emerald}40`, display: 'inline-block' }} />Pesimista
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 8, height: 2, background: T.emerald, display: 'inline-block' }} />Esperado
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 8, height: 8, borderRadius: 2, background: `${T.emerald}20`, display: 'inline-block' }} />Optimista
              </span>
            </div>
          </div>

          <div style={{ position: 'relative', borderRadius: 12, background: '#070a14', border: `1px solid ${T.border}`, padding: 16 }}>
            <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 176, display: 'block' }} preserveAspectRatio="none">
              <defs>
                <linearGradient id="coneGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor={T.emerald} stopOpacity="0.35" />
                  <stop offset="50%" stopColor={T.emerald} stopOpacity="0.15" />
                  <stop offset="100%" stopColor={T.emerald} stopOpacity="0.04" />
                </linearGradient>
                <linearGradient id="lineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor={T.emerald} />
                  <stop offset="100%" stopColor="#34d399" />
                </linearGradient>
                <filter id="lineGlow">
                  <feGaussianBlur stdDeviation="2" result="coloredBlur" />
                  <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
                </filter>
              </defs>
              <path d={conePath} fill="url(#coneGrad)" />
              <path d={pointsToPath('pessimistic')} fill="none" stroke={T.emerald} strokeOpacity="0.35" strokeWidth="1" strokeDasharray="3 3" />
              <path d={pointsToPath('optimistic')} fill="none" stroke="#34d399" strokeOpacity="0.25" strokeWidth="1" strokeDasharray="3 3" />
              <path d={pointsToPath('expected')} fill="none" stroke="url(#lineGrad)" strokeWidth="2.5" strokeLinecap="round" filter="url(#lineGlow)" />
              {hoveredPoint && (
                <circle cx={(hoveredPoint.day - 1) * xStep} cy={H - (hoveredPoint.expected / maxY) * H} r="5" fill={T.emerald} className="animate-pulse" />
              )}
              <line x1="0" x2={W} y1={H - (targetRevenue / maxY) * H} y2={H - (targetRevenue / maxY) * H} stroke={T.amber} strokeOpacity="0.5" strokeWidth="1" strokeDasharray="6 4" />
              <text x={W - 55} y={H - (targetRevenue / maxY) * H - 4} fill={T.amber} fontSize="10" fontFamily="monospace">META ${(targetRevenue / 1000).toFixed(0)}k</text>
            </svg>

            {/* Hover interaction overlay */}
            <div style={{ position: 'absolute', top: 16, left: 16, right: 16, bottom: 24, display: 'flex' }}>
              {forecast.map((_, i) => (
                <div key={i} style={{ flex: 1, cursor: 'crosshair' }} onMouseEnter={() => setHoveredDay(i + 1)} onMouseLeave={() => setHoveredDay(null)} />
              ))}
            </div>

            {hoveredPoint && (
              <div style={{
                position: 'absolute', top: 8, left: 8,
                padding: '8px 12px', borderRadius: 8,
                background: 'rgba(0,0,0,0.85)', border: `1px solid ${T.emerald}40`,
                pointerEvents: 'none',
              }}>
                <p style={{ fontSize: 9, color: T.textSub, textTransform: 'uppercase', letterSpacing: '.06em', margin: 0 }}>Día {hoveredPoint.day}</p>
                <div style={{ marginTop: 4, display: 'flex', flexDirection: 'column', gap: 2, fontSize: 10, fontFamily: 'monospace' }}>
                  <p style={{ color: `${T.emerald}90`, margin: 0 }}>Pesim: ${hoveredPoint.pessimistic.toLocaleString()}</p>
                  <p style={{ color: T.emerald, fontWeight: 700, margin: 0 }}>Esper: ${hoveredPoint.expected.toLocaleString()}</p>
                  <p style={{ color: '#34d399', opacity: 0.7, margin: 0 }}>Optim: ${hoveredPoint.optimistic.toLocaleString()}</p>
                </div>
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4, paddingLeft: 4, paddingRight: 4, fontSize: 9, color: T.textSub, fontFamily: 'monospace' }}>
              <span>Hoy</span><span>+7d</span><span>+14d</span><span>+21d</span><span>+30d</span>
            </div>
          </div>

          {/* Scenarios row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 8 }}>
            <ScenarioCard label="Pesimista" value={totals.pessimistic} probability={95} description="Solo cierras el pipeline maduro" color={T.textSub} />
            <ScenarioCard label="Esperado" value={totals.expected} probability={confidence} description="Conversión histórica + IA optimizando" color={T.emerald} highlight />
            <ScenarioCard label="Optimista" value={totals.optimistic} probability={38} description="Todo cierra + recuperaciones funcionan" color={T.amber} />
          </div>
        </div>

        {/* Trust + guarantees + risk stacked */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))', gap: 12 }}>
          {/* Confidence gauge */}
          <div style={{
            borderRadius: 12, padding: 16, textAlign: 'center',
            background: `${T.emerald}06`, border: `1px solid ${T.emerald}28`,
            position: 'relative', overflow: 'hidden',
          }}>
            <p style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.emerald, marginBottom: 8, fontWeight: 700 }}>Confianza del sistema</p>
            <div style={{ position: 'relative', width: 112, height: 112, margin: '0 auto 8px' }}>
              <svg style={{ width: 112, height: 112, transform: 'rotate(-90deg)' }} viewBox="0 0 120 120">
                <defs>
                  <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor={T.emerald} />
                    <stop offset="100%" stopColor="#34d399" />
                  </linearGradient>
                </defs>
                <circle cx="60" cy="60" r="50" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
                <circle cx="60" cy="60" r="50" fill="none" stroke="url(#gaugeGrad)" strokeWidth="8" strokeLinecap="round"
                  strokeDasharray={`${(confidence / 100) * 314} 314`}
                  style={{ filter: `drop-shadow(0 0 8px ${T.emerald}80)` }} />
              </svg>
              <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontSize: 32, fontWeight: 900, color: T.textPrim, textShadow: '0 0 20px #10B98188' }}>{confidence}<span style={{ fontSize: 16, color: T.textSub }}>%</span></span>
                <span style={{ fontSize: 9, color: T.emerald, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '.06em' }}>CERTEZA</span>
              </div>
            </div>
            <p style={{ fontSize: 12, color: T.textSub, padding: '0 8px' }}>Basado en pipeline + histórico + IA en marcha</p>
          </div>

          {/* Active Guarantees */}
          <div style={{ borderRadius: 12, background: 'rgba(255,255,255,0.02)', border: `1px solid ${T.border}`, padding: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <Award style={{ width: 16, height: 16, color: T.amber }} />
              <h4 style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.amber, margin: 0, fontWeight: 700 }}>Garantías Activas</h4>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {ACTIVE_GUARANTEES.map(g => (
                <div key={g.id} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, padding: 8, borderRadius: 8, background: `${T.amber}06`, border: `1px solid ${T.amber}18` }}>
                  <span style={{ fontSize: 16, flexShrink: 0 }}>{g.emoji}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ fontSize: 12, fontWeight: 600, color: T.textPrim, margin: 0, lineHeight: 1.3 }}>{g.title}</p>
                    <p style={{ fontSize: 10, color: T.textSub, margin: 0, marginTop: 2 }}>{g.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Trust + Risk factors */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))', gap: 16, padding: '0 20px 20px' }}>
        {/* Trust factors */}
        <div style={{ borderRadius: 12, background: `${T.emerald}04`, border: `1px solid ${T.emerald}20`, padding: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <CheckCircle2 style={{ width: 16, height: 16, color: T.emerald }} />
            <h4 style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.emerald, margin: 0, fontWeight: 700 }}>Lo que respalda el cierre</h4>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {TRUST_FACTORS.map(t => {
              const Icon = t.icon
              return (
                <div key={t.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 10, borderRadius: 8, background: 'rgba(255,255,255,0.02)', border: `1px solid ${T.border}` }}>
                  <div style={{ width: 32, height: 32, borderRadius: 8, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: `${t.color}18`, border: `1px solid ${t.color}30` }}>
                    <Icon style={{ width: 14, height: 14, color: t.color }} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                      <p style={{ fontSize: 12, color: T.textPrim, margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.title}</p>
                      <span style={{ fontSize: 10, fontWeight: 700, color: t.color, flexShrink: 0, textShadow: `0 0 20px ${t.color}88` }}>{t.value}</span>
                    </div>
                    <p style={{ fontSize: 9, color: T.textSub, margin: 0, marginTop: 2 }}>{t.impact}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Risk factors */}
        <div style={{ borderRadius: 12, background: `${T.amber}04`, border: `1px solid ${T.amber}20`, padding: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <AlertTriangle style={{ width: 16, height: 16, color: T.amber }} />
            <h4 style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.amber, margin: 0, fontWeight: 700 }}>Riesgos · La IA ya está mitigando</h4>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {RISK_FACTORS.map(r => (
              <div key={r.id} style={{ padding: 10, borderRadius: 8, background: 'rgba(255,255,255,0.02)', border: `1px solid ${T.border}` }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                  <span style={{ fontSize: 16, flexShrink: 0 }}>{r.emoji}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ fontSize: 12, color: T.textPrim, margin: 0, lineHeight: 1.3 }}>{r.title}</p>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 6, marginTop: 6, padding: 6, borderRadius: 6, background: `${T.emerald}06`, border: `1px solid ${T.emerald}18` }}>
                      <Sparkles style={{ width: 10, height: 10, color: T.emerald, flexShrink: 0, marginTop: 1 }} />
                      <p style={{ fontSize: 10, color: T.emerald, margin: 0, lineHeight: 1.4 }}>{r.mitigation}</p>
                    </div>
                  </div>
                  <span style={{
                    fontSize: 8, padding: '2px 6px', borderRadius: 4, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '.06em', flexShrink: 0,
                    background: `${severityColor(r.severity)}18`, border: `1px solid ${severityColor(r.severity)}28`, color: severityColor(r.severity),
                  }}>{r.severity}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

// ─── Scenario Card ─────────────────────────────────────────────────────────────

interface ScenarioProps {
  label: string
  value: number
  probability: number
  description: string
  color: string
  highlight?: boolean
}

const ScenarioCard = ({ label, value, probability, description, color, highlight }: ScenarioProps) => (
  <div style={{
    position: 'relative', padding: 12, borderRadius: 12,
    background: highlight ? `${color}08` : 'rgba(255,255,255,0.02)',
    border: `1px solid ${highlight ? color + '40' : T.border}`,
    boxShadow: highlight ? `0 0 20px ${color}20` : 'none',
    overflow: 'hidden',
  }}>
    {highlight && (
      <div style={{ position: 'absolute', top: 8, right: 8 }}>
        <Sparkles style={{ width: 12, height: 12, color }} />
      </div>
    )}
    <p style={{ fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color, fontWeight: 700, marginBottom: 4 }}>{label}</p>
    <p style={{ fontSize: 22, fontWeight: 900, color: T.textPrim, margin: 0, textShadow: highlight ? `0 0 20px ${color}88` : 'none' }}>${(value / 1000).toFixed(1)}k</p>
    <p style={{ fontSize: 10, color: T.textSub, lineHeight: 1.4, marginTop: 4 }}>{description}</p>
    <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{ flex: 1, height: 4, borderRadius: 2, background: 'rgba(255,255,255,0.05)', overflow: 'hidden' }}>
        <div style={{ height: '100%', borderRadius: 2, background: color, width: `${probability}%` }} />
      </div>
      <span style={{ fontSize: 9, color: T.textSub, fontFamily: 'monospace' }}>{probability}%</span>
    </div>
  </div>
)
