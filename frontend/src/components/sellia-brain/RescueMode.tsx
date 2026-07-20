'use client'

/**
 * MOTOR DE CRECIMIENTO
 *
 * 3 modos: Rescate (salir de quiebra), Crecer (más clientes cada día) y Escalar
 * (referente/autoridad/marca). Combina una biblioteca de estrategias real (salir
 * de quiebra, vender sin vender, branding, contenido, ventas) con un plan de
 * fases + flujos ejecutables por el cerebro (Computer Use sobre cuentas reales).
 */

import { useMemo, useState } from 'react'
import { LifeBuoy, TrendingUp, Crown, Landmark, AlertTriangle, Rocket, Check, BookOpen, Star } from 'lucide-react'
import { SELLIA } from '@/lib/sellia-theme'
import {
  type BusinessProfile, type RescueSituation, type PlannedFlow, type GrowthMode,
  growthPlan, isComplete, buildToolPlan,
} from '@/lib/business-profile'
import { relevantStrategies } from '@/lib/growth-strategies'
import { TOOL_BY_ID } from '@/lib/tools-catalog'

const T = SELLIA

interface Props { profile: BusinessProfile | null; onEdit: () => void; onRescue: (flows: PlannedFlow[]) => void }

const MODES: Array<{ id: GrowthMode; label: string; icon: React.ReactNode; accent: string }> = [
  { id: 'rescate', label: 'Rescate', icon: <LifeBuoy size={15} />, accent: T.amber },
  { id: 'crecer', label: 'Crecer', icon: <TrendingUp size={15} />, accent: T.cobalt },
  { id: 'escalar', label: 'Escalar', icon: <Crown size={15} />, accent: T.emerald },
  { id: 'cimientos', label: 'Cimientos', icon: <Landmark size={15} />, accent: '#EAB308' },
]

const SITU: Array<{ id: keyof RescueSituation; label: string }> = [
  { id: 'noSales', label: 'No vendo / nadie compra' },
  { id: 'hasSocial', label: 'Estoy en redes' },
  { id: 'hasAds', label: 'Pago anuncios' },
  { id: 'hasPhysical', label: 'Local físico' },
  { id: 'lowTraffic', label: 'Poco alcance' },
]

const card: React.CSSProperties = { background: T.panel, border: `1px solid ${T.border}`, borderRadius: 12, padding: 16, fontFamily: T.sans }

export default function RescueMode({ profile, onEdit, onRescue }: Props): React.JSX.Element {
  const [mode, setMode] = useState<GrowthMode>('rescate')
  const [s, setS] = useState<RescueSituation>({ noSales: true, hasSocial: false, hasAds: false, hasPhysical: false, lowTraffic: false })
  const [openStrat, setOpenStrat] = useState<string | null>(null)
  const plan = useMemo(() => growthPlan(profile, mode, s), [profile, mode, s])
  const relSet = useMemo(() => profile
    ? new Set(relevantStrategies({ bizType: profile.bizType, industry: profile.industry, product: profile.productDesc, goals: profile.goals }).filter(r => r.relevant).map(r => r.strategy.id))
    : new Set<string>(), [profile])
  const accent = MODES.find(m => m.id === mode)!.accent
  // herramientas ejecutables que activan las estrategias del modo (escalable)
  const execToolIds = useMemo(() => {
    const ids = new Set<string>()
    for (const st of plan.strategies) for (const a of st.activates ?? []) {
      const slug = a.split('.').slice(-1)[0]
      if (TOOL_BY_ID[slug]) ids.add(slug)
    }
    return [...ids]
  }, [plan.strategies])
  const execFlows = useMemo(() => [...plan.flows, ...buildToolPlan(profile, execToolIds)], [plan.flows, profile, execToolIds])

  if (!isComplete(profile)) {
    return (
      <div style={{ ...card, textAlign: 'center', padding: 24 }}>
        <Rocket size={20} style={{ color: T.cobalt }} />
        <div style={{ fontSize: 13, fontWeight: 700, color: T.text, marginTop: 6 }}>Completá tu negocio para activar el Motor de Crecimiento</div>
        <button type="button" onClick={onEdit} style={{ marginTop: 10, padding: '8px 16px', borderRadius: 9, border: 'none', background: T.cobalt, color: '#fff', fontWeight: 700, cursor: 'pointer', fontSize: 13 }}>Completar negocio</button>
      </div>
    )
  }

  return (
    <div style={card}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 12 }}>
        <span style={{ width: 28, height: 28, borderRadius: 8, display: 'grid', placeItems: 'center', background: `${accent}1F`, border: `1px solid ${accent}44`, color: accent }}><Rocket size={15} /></span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: T.text }}>Motor de Crecimiento</div>
          <div style={{ fontSize: 11, color: T.text2, fontFamily: T.mono }}>El cerebro sale a conseguir clientes y construir marca</div>
        </div>
      </div>

      {/* selector de modo */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
        {MODES.map(m => (
          <button key={m.id} type="button" onClick={() => setMode(m.id)} style={{
            flex: 1, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6,
            padding: '9px', borderRadius: 9, cursor: 'pointer', fontSize: 12.5, fontWeight: 700, fontFamily: T.sans,
            border: `1px solid ${mode === m.id ? m.accent : T.border}`,
            background: mode === m.id ? `${m.accent}1F` : 'transparent', color: mode === m.id ? m.accent : T.text2,
          }}>{m.icon}{m.label}</button>
        ))}
      </div>

      {/* situación (solo relevante en rescate) */}
      {mode === 'rescate' && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7, marginBottom: 12 }}>
          {SITU.map(it => {
            const on = s[it.id]
            return (
              <button key={it.id} type="button" onClick={() => setS(prev => ({ ...prev, [it.id]: !prev[it.id] }))}
                style={{ padding: '5px 10px', borderRadius: 100, fontSize: 11.5, fontWeight: 600, cursor: 'pointer', fontFamily: T.sans, border: `1px solid ${on ? accent : T.border}`, background: on ? `${accent}1F` : 'transparent', color: on ? accent : T.text2 }}>
                {on ? '✓ ' : ''}{it.label}
              </button>
            )
          })}
        </div>
      )}

      {/* diagnóstico */}
      <div style={{ display: 'flex', gap: 9, padding: '10px 12px', borderRadius: 9, background: `${accent}10`, border: `1px solid ${accent}33`, marginBottom: 14 }}>
        <AlertTriangle size={15} style={{ color: accent, flexShrink: 0, marginTop: 1 }} />
        <span style={{ fontSize: 12.5, color: T.text, lineHeight: 1.5 }}>{plan.diagnosis}</span>
      </div>

      {/* biblioteca de estrategias (navegable) */}
      <div style={{ fontSize: 11, color: T.text3, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
        <BookOpen size={13} /> Estrategias del modo {mode}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 14 }}>
        {plan.strategies.map(st => {
          const open = openStrat === st.id
          return (
            <div key={st.id} style={{ background: T.bg, border: `1px solid ${T.border}`, borderRadius: 9 }}>
              <button type="button" onClick={() => setOpenStrat(open ? null : st.id)} style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 8, padding: '10px 12px', background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left' }}>
                {relSet.has(st.id) && <Star size={12} style={{ color: '#EAB308', fill: '#EAB308', flexShrink: 0 }} />}
                <span style={{ fontSize: 12.5, fontWeight: 700, color: T.text, flex: 1 }}>{st.title}</span>
                <span style={{ fontSize: 16, color: T.text3 }}>{open ? '−' : '+'}</span>
              </button>
              {open && (
                <div style={{ padding: '0 12px 12px' }}>
                  {st.principles.map((pr, i) => <div key={`p${i}`} style={{ fontSize: 11.5, color: T.text2, marginBottom: 4, fontStyle: 'italic' }}>“{pr}”</div>)}
                  <div style={{ marginTop: 6 }}>
                    {st.tactics.map((tt, i) => (
                      <div key={`t${i}`} style={{ display: 'flex', gap: 6, fontSize: 11.5, color: T.text, marginBottom: 3 }}>
                        <Check size={12} style={{ color: T.emerald, flexShrink: 0, marginTop: 2 }} />{tt}
                      </div>
                    ))}
                  </div>
                  {st.activates && st.activates.length > 0 && (
                    <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                      {st.activates.map(a => (
                        <span key={a} style={{ fontSize: 10, color: accent, background: `${accent}14`, border: `1px solid ${accent}33`, borderRadius: 5, padding: '2px 6px', fontFamily: T.mono }}>
                          {a.split('.').slice(-1)[0]}
                        </span>
                      ))}
                    </div>
                  )}
                  <div style={{ marginTop: 7, fontSize: 10.5, color: T.text3, fontFamily: T.mono }}>fuente: {st.sourceHint}</div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      <button type="button" onClick={() => onRescue(execFlows)} disabled={execFlows.length === 0}
        style={{ width: '100%', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8, padding: '11px', borderRadius: 9, border: 'none', background: accent, color: '#101010', fontWeight: 800, cursor: execFlows.length ? 'pointer' : 'not-allowed', opacity: execFlows.length ? 1 : 0.5, fontSize: 13 }}>
        <Rocket size={15} /> Ejecutar plan ({execFlows.length} acciones)
      </button>
    </div>
  )
}
