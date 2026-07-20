'use client'

/**
 * SALES → FIDELIZATION FLOW
 *
 * Conveyor visual del journey completo del cliente:
 * Prospect → Qualified → Discovery → Proposal → Negotiation → Won →
 * Onboarded → Engaged → Loyal → Advocate
 */

import { useState, useMemo } from 'react'
import {
  Target, Search, Lightbulb, Package, Handshake, CheckCircle2,
  Rocket, Heart, Award, Megaphone, Bot, ArrowRight, TrendingUp, Sparkles,
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

interface Stage {
  id: string
  emoji: string
  label: string
  shortLabel: string
  icon: React.ElementType
  color: string
  count: number
  delta: number
  aiActionsToday: number
  description: string
  customers: { name: string; value?: number; lastAction: string }[]
}

const SALES_STAGES: Stage[] = [
  { id: 'prospect',    emoji: '🎯', label: 'Prospección',    shortLabel: 'Prospect',    icon: Target,       color: '#3b82f6', count: 47, delta: 8,  aiActionsToday: 12, description: 'IA buscando y contactando leads en LinkedIn, Instagram y bases públicas', customers: [{ name: 'Juan G. (PyME logística)', lastAction: 'Mensaje IG hace 3min' }, { name: 'María L. (e-commerce moda)', lastAction: 'Email enviado hace 12min' }] },
  { id: 'qualified',   emoji: '🔍', label: 'Calificación',   shortLabel: 'Qualified',   icon: Search,       color: '#6366f1', count: 28, delta: 3,  aiActionsToday: 8,  description: 'Evaluando presupuesto, autoridad, necesidad y tiempo de cada lead', customers: [{ name: 'Empresa Beta SRL', value: 8400, lastAction: 'Diagnóstico vía WhatsApp' }, { name: 'Pedro K. (mayorista)', value: 3200, lastAction: 'Llamada agendada' }] },
  { id: 'discovery',   emoji: '💡', label: 'Descubrimiento', shortLabel: 'Discovery',   icon: Lightbulb,    color: T.cyan,    count: 15, delta: -2, aiActionsToday: 6,  description: 'Descubriendo el dolor real y el impacto del problema no resuelto', customers: [{ name: 'Acme SA', value: 12000, lastAction: 'Demo enviado por WhatsApp' }, { name: 'Pack 12 alumnos', value: 3564, lastAction: 'Propuesta personalizada' }] },
  { id: 'proposal',    emoji: '📦', label: 'Propuesta',      shortLabel: 'Proposal',    icon: Package,      color: T.amber,   count: 8,  delta: 1,  aiActionsToday: 4,  description: 'Oferta de alto valor con stack de beneficios y ecuación de valor', customers: [{ name: 'Tomás N.', value: 2400, lastAction: 'Propuesta + bonos enviada' }, { name: 'Lucía F.', value: 980, lastAction: 'Esperando feedback' }] },
  { id: 'negotiation', emoji: '🤝', label: 'Negociación',    shortLabel: 'Negotiating', icon: Handshake,    color: '#f97316', count: 5,  delta: 0,  aiActionsToday: 7,  description: 'IA manejando objeciones con protocolo de negociación y cierre calibrado', customers: [{ name: 'Juan G. (live ahora)', value: 1200, lastAction: 'Respondiendo objeción de precio' }, { name: 'Mariana P.', value: 850, lastAction: 'Esperando respuesta' }] },
  { id: 'closing',     emoji: '✅', label: 'Cierre',         shortLabel: 'Won',         icon: CheckCircle2, color: T.emerald, count: 12, delta: 3,  aiActionsToday: 5,  description: 'Cerradas hoy. IA procesando factura, envío de contrato, onboarding', customers: [{ name: 'Ana Suárez', value: 980, lastAction: 'Factura A generada · contrato firmado' }, { name: 'Empresa Beta', value: 1847, lastAction: 'Pago confirmado' }] },
]

const FIDELIZATION_STAGES: Stage[] = [
  { id: 'onboarded', emoji: '🚀', label: 'Bienvenida', shortLabel: 'Onboarded', icon: Rocket,    color: T.emerald, count: 9,  delta: 2,  aiActionsToday: 6,  description: 'Protocolo de bienvenida: primera victoria garantizada en primeras 48hs', customers: [{ name: 'Ana Suárez (Día 2)', lastAction: 'Video tutorial + sesión 1:1 agendada' }] },
  { id: 'engaged',   emoji: '💎', label: 'Engaged',    shortLabel: 'Engaged',   icon: Heart,     color: '#ec4899', count: 87, delta: 4,  aiActionsToday: 14, description: 'Monitoreando uso, enviando tips contextuales, anticipando necesidades', customers: [{ name: 'María L. (3 meses)', lastAction: 'Tip de uso + ROI report' }, { name: 'Acme SA (6 meses)', lastAction: 'Caso de éxito documentado' }] },
  { id: 'loyal',     emoji: '🏆', label: 'Fiel',       shortLabel: 'Loyal',     icon: Award,     color: T.violet,  count: 34, delta: 5,  aiActionsToday: 11, description: 'RFM + LTV optimizando — IA detectando momentos de upsell y reordenes', customers: [{ name: 'Empresa Gamma (12m)', value: 14200, lastAction: 'Upsell Premium ofrecido' }] },
  { id: 'advocate',  emoji: '📢', label: 'Embajador',  shortLabel: 'Advocate',  icon: Megaphone, color: T.amber,   count: 18, delta: 1,  aiActionsToday: 9,  description: 'NPS 9-10 — IA activando programa de referidos y testimonios públicos', customers: [{ name: 'Tomás N. (NPS 10)', lastAction: 'Generó 3 referidos esta semana' }] },
]

const FUNNEL_TICKER = [
  { from: 'prospect', to: 'qualified', customer: 'María L.',   delta: '+1',    color: '#6366f1' },
  { from: 'negotiation', to: 'closing', customer: 'Ana S.',    delta: '$980',  color: T.emerald },
  { from: 'loyal', to: 'advocate',     customer: 'Tomás N.',   delta: 'NPS 10',color: T.amber },
  { from: 'qualified', to: 'discovery',customer: 'Pedro K.',   delta: '+1',    color: T.cyan },
  { from: 'discovery', to: 'proposal', customer: 'Acme SA',    delta: '$12k',  color: T.amber },
]

type FlowProps = { onStageClick?: (stageId: string) => void }

export default function SalesFidelizationFlow({ onStageClick }: FlowProps) {
  const [hoveredStage, setHoveredStage] = useState<string | null>(null)

  const totals = useMemo(() => ({
    sales: SALES_STAGES.reduce((s, st) => s + st.count, 0),
    fidelization: FIDELIZATION_STAGES.reduce((s, st) => s + st.count, 0),
    aiActions: [...SALES_STAGES, ...FIDELIZATION_STAGES].reduce((s, st) => s + st.aiActionsToday, 0),
  }), [])

  const hoveredData = useMemo(
    () => [...SALES_STAGES, ...FIDELIZATION_STAGES].find(s => s.id === hoveredStage),
    [hoveredStage]
  )

  return (
    <section style={{ background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 16, overflow: 'hidden', position: 'relative' }}>
      {/* Top accent */}
      <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, ' + T.emerald + '80, transparent)' }} />

      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: T.emerald + '22', border: '1px solid ' + T.emerald + '44', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <TrendingUp size={18} style={{ color: T.emerald }} />
          </div>
          <div>
            <h2 style={{ fontSize: 13, fontWeight: 900, color: T.textPrim, letterSpacing: '.06em', textTransform: 'uppercase', margin: 0 }}>
              FLUJO COMPLETO <span style={{ color: T.textSub, fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>· Ventas → Fidelización</span>
            </h2>
            <p style={{ fontSize: 11, color: T.textSub, marginTop: 2 }}>Del primer contacto al embajador de marca — todo automatizado por IA</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ padding: '6px 12px', borderRadius: 8, background: T.bgApp, border: '1px solid ' + T.border, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Bot size={12} style={{ color: T.cyan }} />
            <span style={{ fontSize: 12, color: T.textSub }}>{totals.aiActions} acciones IA hoy</span>
          </div>
          <div style={{ padding: '6px 12px', borderRadius: 8, background: T.emerald + '15', border: '1px solid ' + T.emerald + '35' }}>
            <span style={{ fontSize: 12, color: T.emerald, fontWeight: 700 }}>{totals.sales + totals.fidelization} clientes en flujo</span>
          </div>
        </div>
      </div>

      {/* Phase headers */}
      <div style={{ padding: '16px 20px 0', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.cyan }}>
          <span>SALES PHASE</span>
          <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, ' + T.cyan + '40, transparent)' }} />
          <span style={{ color: T.textSub }}>{totals.sales} activos</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.emerald }}>
          <span>FIDELIZATION PHASE</span>
          <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, ' + T.emerald + '40, transparent)' }} />
          <span style={{ color: T.textSub }}>{totals.fidelization} clientes</span>
        </div>
      </div>

      {/* Conveyor stages */}
      <div style={{ padding: '16px 20px', overflowX: 'auto' }}>
        <div style={{ display: 'flex', alignItems: 'stretch', gap: 4, minWidth: 'max-content' }}>
          {SALES_STAGES.map(stage => (
            <StageCard key={stage.id} stage={stage} isHovered={hoveredStage === stage.id} onHover={setHoveredStage} onClick={() => onStageClick?.(stage.id)} />
          ))}

          {/* Conversion marker */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '0 8px', flexShrink: 0 }}>
            <div style={{ fontSize: 9, fontFamily: 'JetBrains Mono,monospace', textTransform: 'uppercase', color: T.emerald, marginBottom: 4 }}>Conversión</div>
            <div style={{ position: 'relative', width: 48, height: 48, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg className="animate-spin" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', animationDuration: '8s' }} viewBox="0 0 48 48">
                <circle cx="24" cy="24" r="20" fill="none" stroke={T.emerald} strokeWidth="1.5" strokeDasharray="60 80" strokeLinecap="round" />
              </svg>
              <Sparkles size={20} style={{ color: T.emerald, filter: 'drop-shadow(0 0 8px ' + T.emerald + '99)' }} />
            </div>
            <div style={{ fontSize: 9, color: T.textSub, marginTop: 4 }}>12 hoy</div>
          </div>

          {FIDELIZATION_STAGES.map(stage => (
            <StageCard key={stage.id} stage={stage} isHovered={hoveredStage === stage.id} onHover={setHoveredStage} onClick={() => onStageClick?.(stage.id)} />
          ))}
        </div>
      </div>

      {/* Hover detail panel */}
      {hoveredData && (
        <div style={{ margin: '0 20px 20px', borderRadius: 12, padding: 16, background: hoveredData.color + '08', border: '1px solid ' + hoveredData.color + '30' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
            <span style={{ fontSize: 28, flexShrink: 0 }}>{hoveredData.emoji}</span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 4 }}>
                <h3 style={{ fontSize: 14, fontWeight: 700, color: T.textPrim }}>{hoveredData.label}</h3>
                <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 99, fontFamily: 'monospace', textTransform: 'uppercase', background: hoveredData.color + '20', color: hoveredData.color }}>
                  {hoveredData.count} en stage
                </span>
                <span style={{ fontSize: 10, color: T.textSub, display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Bot size={10} />{hoveredData.aiActionsToday} acciones IA hoy
                </span>
              </div>
              <p style={{ fontSize: 12, color: T.textSub, marginBottom: 12 }}>{hoveredData.description}</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {hoveredData.customers.map((c, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, padding: '8px 10px', borderRadius: 8, background: T.bgApp, border: '1px solid ' + T.border }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1, minWidth: 0 }}>
                      <div className="animate-pulse" style={{ width: 6, height: 6, borderRadius: '50%', background: hoveredData.color, flexShrink: 0 }} />
                      <span style={{ fontSize: 12, color: T.textPrim, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.name}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                      {c.value !== undefined && <span style={{ fontSize: 10, color: T.emerald, fontWeight: 600 }}>${c.value.toLocaleString()}</span>}
                      <span style={{ fontSize: 10, color: T.textSub }}>{c.lastAction}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Live ticker */}
      <div style={{ borderTop: '1px solid ' + T.border, background: T.bgApp, overflow: 'hidden' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
            <div className="animate-pulse" style={{ width: 6, height: 6, borderRadius: '50%', background: T.emerald }} />
            <span style={{ fontSize: 9, color: T.emerald, fontFamily: 'JetBrains Mono,monospace', textTransform: 'uppercase', letterSpacing: '.08em' }}>LIVE</span>
          </div>
          <div style={{ flex: 1, overflow: 'hidden', position: 'relative', height: 20 }}>
            <div className="animate-marquee" style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', gap: 24, whiteSpace: 'nowrap' }}>
              {[...FUNNEL_TICKER, ...FUNNEL_TICKER].map((t, i) => (
                <span key={i} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 11, fontWeight: 500, color: t.color }}>
                  <span style={{ color: T.textPrim }}>{t.customer}</span>
                  <span style={{ color: T.textSub }}>{t.from} → {t.to}</span>
                  <span style={{ fontWeight: 700 }}>{t.delta}</span>
                  <span style={{ color: T.border }}>·</span>
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes marquee { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
        :global(.animate-marquee) { animation: marquee 40s linear infinite; }
      `}</style>
    </section>
  )
}

// ─── Stage Card ───────────────────────────────────────────────────────────────

interface StageCardProps {
  stage: Stage
  isHovered: boolean
  onHover: (id: string | null) => void
  onClick: () => void
}

const StageCard = ({ stage, isHovered, onHover, onClick }: StageCardProps) => {
  const Icon = stage.icon
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => onHover(stage.id)}
      onMouseLeave={() => onHover(null)}
      style={{
        position: 'relative', flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'center',
        padding: 12, borderRadius: 12, minWidth: 100, cursor: 'pointer',
        background: isHovered ? stage.color + '15' : T.bgApp,
        border: '1px solid ' + (isHovered ? stage.color + '50' : T.border),
        boxShadow: isHovered ? '0 0 24px ' + stage.color + '25' : 'none',
        transform: isHovered ? 'translateY(-2px)' : 'translateY(0)',
        transition: 'all .15s',
      }}
    >
      {/* Arrow connector */}
      <div style={{ position: 'absolute', right: -6, top: '50%', transform: 'translateY(-50%)', zIndex: 10, pointerEvents: 'none' }}>
        <ArrowRight size={12} style={{ color: isHovered ? stage.color : T.border }} />
      </div>

      {/* Icon */}
      <div style={{ position: 'relative', width: 40, height: 40, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 8, background: stage.color + '15', border: '1px solid ' + stage.color + '30' }}>
        <Icon size={16} style={{ color: stage.color, filter: isHovered ? 'drop-shadow(0 0 8px ' + stage.color + '80)' : 'none' }} />
        {stage.aiActionsToday > 0 && (
          <div style={{ position: 'absolute', top: -4, right: -4, width: 16, height: 16, borderRadius: '50%', background: T.amber, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ fontSize: 8, fontWeight: 700, color: T.bgApp }}>{stage.aiActionsToday}</span>
          </div>
        )}
      </div>

      <span style={{ fontSize: 10, fontWeight: 600, color: T.textPrim, marginBottom: 2, textAlign: 'center', lineHeight: 1.3 }}>{stage.shortLabel}</span>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
        <span style={{ fontSize: 20, fontWeight: 700, color: T.textPrim, fontVariantNumeric: 'tabular-nums', textShadow: isHovered ? '0 0 20px ' + stage.color + '88' : 'none' }}>{stage.count}</span>
        {stage.delta !== 0 && (
          <span style={{ fontSize: 9, fontWeight: 700, color: stage.delta > 0 ? T.emerald : T.rose }}>
            {stage.delta > 0 ? '+' : ''}{stage.delta}
          </span>
        )}
      </div>

      {stage.aiActionsToday > 0 && (
        <div style={{ position: 'absolute', bottom: 4, left: '50%', transform: 'translateX(-50%)', display: 'flex', alignItems: 'center', gap: 2 }}>
          {[0, 1, 2].map(i => (
            <div key={i} className="animate-pulse" style={{ width: 2, height: 2, borderRadius: '50%', background: stage.color, animationDelay: `${i * 0.2}s` }} />
          ))}
        </div>
      )}
    </button>
  )
}
