'use client'

/**
 * WORKFLOW BUILDER
 *
 * Visual no-code automations. Trigger → Conditions → Actions chain.
 * User construye reglas sin tocar código.
 */

import { useState, useMemo } from 'react'
import {
  Zap, Plus, Play, Pause, Activity, ArrowRight, GitBranch,
  Bot, CheckCircle2
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

interface Workflow {
  id: string
  name: string
  trigger: { emoji: string; label: string; type: string }
  conditions: string[]
  actions: { emoji: string; label: string }[]
  active: boolean
  runsToday: number
  successRate: number
  revenueImpact: number
  color: string
}

const WORKFLOWS: Workflow[] = [
  {
    id: 'w1',
    name: 'Carrito abandonado · recovery 4 toques',
    trigger: { emoji: '🛒', label: 'Carrito abandonado >30min', type: 'event' },
    conditions: ['Valor > $50', 'No-comprado-últimos-7-días'],
    actions: [
      { emoji: '⏱', label: 'Esperar 1h' },
      { emoji: '✉️', label: 'Email recordatorio + foto producto' },
      { emoji: '⏱', label: 'Esperar 24h' },
      { emoji: '💬', label: 'WhatsApp con cupón 10%' },
      { emoji: '⏱', label: 'Esperar 48h' },
      { emoji: '🎁', label: 'Email "última oportunidad" + bonus' },
    ],
    active: true, runsToday: 47, successRate: 38, revenueImpact: 2847, color: T.amber,
  },
  {
    id: 'w2',
    name: 'Lead WA · responder en <30seg',
    trigger: { emoji: '💚', label: 'Mensaje WA entrante (lead nuevo)', type: 'webhook' },
    conditions: ['Primera vez · sin historial'],
    actions: [
      { emoji: '🤖', label: 'IA clasifica intención del lead' },
      { emoji: '💬', label: 'Respuesta con preguntas de calificación' },
      { emoji: '📝', label: 'Crear lead en CRM' },
      { emoji: '📅', label: 'Si calificado · agendar call' },
    ],
    active: true, runsToday: 142, successRate: 91, revenueImpact: 8420, color: '#25d366',
  },
  {
    id: 'w3',
    name: 'Stock bajo · auto-reorder',
    trigger: { emoji: '📦', label: 'Stock < reorder point', type: 'cron' },
    conditions: ['Auto-reorder enabled', 'Vendor activo'],
    actions: [
      { emoji: '🧾', label: 'Crear PO en sistema' },
      { emoji: '✉️', label: 'Email a supplier' },
      { emoji: '📅', label: 'Registrar ETA en calendar' },
      { emoji: '🔔', label: 'Notif al user' },
    ],
    active: true, runsToday: 4, successRate: 100, revenueImpact: 0, color: T.amber,
  },
  {
    id: 'w4',
    name: 'NPS 9-10 · pedir referido + testimonio',
    trigger: { emoji: '⭐', label: 'NPS score >= 9', type: 'event' },
    conditions: ['Cliente con >3 meses', 'No-pidió-referido-últimos-90d'],
    actions: [
      { emoji: '⏱', label: 'Esperar 24h post-survey' },
      { emoji: '💬', label: 'WA personalizado · gracias' },
      { emoji: '🎁', label: 'Ofrecer comisión 20% por referido' },
      { emoji: '🎥', label: 'Si acepta · solicitar testimonio video' },
    ],
    active: true, runsToday: 12, successRate: 67, revenueImpact: 4180, color: T.amber,
  },
  {
    id: 'w5',
    name: 'Churn risk · rescate 7 días sin actividad',
    trigger: { emoji: '🚨', label: 'Cliente sin engagement 7d', type: 'cron' },
    conditions: ['LTV > $500', 'Loyal/Champion tier'],
    actions: [
      { emoji: '🤖', label: 'IA analiza causa probable' },
      { emoji: '💬', label: 'WA personalizado de reactivación' },
      { emoji: '🎁', label: 'Ofrecer beneficio personalizado' },
      { emoji: '📅', label: 'Si no responde 48h · llamada' },
    ],
    active: true, runsToday: 8, successRate: 51, revenueImpact: 3247, color: T.rose,
  },
  {
    id: 'w6',
    name: 'Review 5⭐ · screenshot + share IG',
    trigger: { emoji: '🌟', label: 'Review 5⭐ recibida', type: 'webhook' },
    conditions: ['Texto >20 caracteres'],
    actions: [
      { emoji: '🖼', label: 'Generar imagen branded' },
      { emoji: '📷', label: 'Postear en IG Stories' },
      { emoji: '💬', label: 'Responder al cliente · gracias' },
    ],
    active: false, runsToday: 0, successRate: 89, revenueImpact: 0, color: T.amber,
  },
]

export default function WorkflowBuilder() {
  const [expanded, setExpanded] = useState<string | null>(WORKFLOWS[0].id)
  const [showInactive, setShowInactive] = useState(true)

  const stats = useMemo(() => ({
    active:    WORKFLOWS.filter(w => w.active).length,
    total:     WORKFLOWS.length,
    runsToday: WORKFLOWS.reduce((s, w) => s + w.runsToday, 0),
    revenue:   WORKFLOWS.reduce((s, w) => s + w.revenueImpact, 0),
  }), [])

  const visible = showInactive ? WORKFLOWS : WORKFLOWS.filter(w => w.active)

  return (
    <section style={{ background: T.bgCard, border: `1px solid ${T.border}`, borderRadius: 16, overflow: 'hidden' }}>
      <div style={{ height: 1, background: `linear-gradient(90deg, transparent, ${T.emerald}80, transparent)` }} />

      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: `${T.emerald}22`, border: `1px solid ${T.emerald}44`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Zap style={{ width: 20, height: 20, color: T.emerald, filter: `drop-shadow(0 0 8px ${T.emerald}b0)` }} />
          </div>
          <div>
            <h2 style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, letterSpacing: '.08em', textTransform: 'uppercase', margin: 0 }}>
              WORKFLOW BUILDER
              <span style={{ color: T.textSub, fontWeight: 400, textTransform: 'none', letterSpacing: 'normal', marginLeft: 8 }}>· No-code automations · trigger → action</span>
            </h2>
            <p style={{ fontSize: 11, color: T.textSub, margin: 0, marginTop: 2 }}>
              {stats.active}/{stats.total} activos · {stats.runsToday} ejecuciones hoy · +${stats.revenue.toLocaleString()} revenue atribuido
            </p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button
            onClick={() => setShowInactive(s => !s)}
            style={{ padding: '6px 12px', borderRadius: 8, background: 'rgba(255,255,255,0.04)', border: `1px solid ${T.border}`, color: T.textSub, fontSize: 11, cursor: 'pointer' }}
          >
            {showInactive ? 'Ocultar inactivos' : 'Mostrar todos'}
          </button>
          <button style={{ padding: '6px 14px', borderRadius: 8, background: `${T.emerald}18`, border: `1px solid ${T.emerald}40`, color: T.emerald, fontSize: 12, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}>
            <Plus style={{ width: 12, height: 12 }} />Nuevo workflow
          </button>
        </div>
      </div>

      {/* Quick stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', borderBottom: `1px solid ${T.border}` }}>
        {[
          { label: 'Activos',          value: stats.active,                             color: T.emerald, sub: `de ${stats.total} total` },
          { label: 'Ejecuciones hoy',  value: stats.runsToday,                          color: T.cyan,    sub: 'automáticas' },
          { label: 'Revenue atribuido', value: `$${(stats.revenue / 1000).toFixed(1)}k`, color: T.emerald, sub: 'esta semana' },
          { label: 'Avg éxito',        value: `${Math.round(WORKFLOWS.filter(w => w.active).reduce((s, w) => s + w.successRate, 0) / stats.active)}%`, color: T.amber, sub: 'workflows activos' },
        ].map((s, i) => (
          <div key={i} style={{ padding: 12, borderRight: i < 3 ? `1px solid ${T.border}` : undefined }}>
            <p style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, margin: 0, fontWeight: 700, marginBottom: 6 }}>{s.label}</p>
            <p style={{ fontSize: 20, fontWeight: 900, color: s.color, margin: 0, textShadow: `0 0 20px ${s.color}88` }}>{s.value}</p>
            <p style={{ fontSize: 9, color: T.textSub, margin: 0, marginTop: 2 }}>{s.sub}</p>
          </div>
        ))}
      </div>

      {/* Workflow list */}
      <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {visible.map(w => {
          const isExpanded = expanded === w.id
          return (
            <div key={w.id} style={{
              borderRadius: 12, overflow: 'hidden',
              background: w.active ? `${w.color}05` : 'rgba(255,255,255,0.015)',
              border: `1px solid ${w.active ? w.color + '28' : T.border}`,
              opacity: w.active ? 1 : 0.6,
            }}>
              <div style={{ height: 2, background: `linear-gradient(90deg, ${w.color}${w.active ? 'cc' : '44'}, transparent)` }} />

              <button
                onClick={() => setExpanded(isExpanded ? null : w.id)}
                style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 12, padding: 14, background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left' }}
              >
                <div style={{ width: 40, height: 40, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, background: `${w.color}18`, border: `1px solid ${w.color}30` }}>
                  <GitBranch style={{ width: 16, height: 16, color: w.color }} />
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 4 }}>
                    <p style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, margin: 0 }}>{w.name}</p>
                    {w.active ? (
                      <span style={{
                        fontSize: 8, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', fontWeight: 700,
                        padding: '2px 6px', borderRadius: 4,
                        background: `${T.emerald}20`, color: T.emerald,
                        display: 'flex', alignItems: 'center', gap: 4,
                      }}>
                        <div className="animate-pulse" style={{ width: 4, height: 4, borderRadius: '50%', background: T.emerald }} />
                        ON
                      </span>
                    ) : (
                      <span style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', fontWeight: 700, padding: '2px 6px', borderRadius: 4, background: 'rgba(255,255,255,0.10)', color: T.textSub }}>OFF</span>
                    )}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 10, color: T.textSub }}>
                    <span>{w.trigger.emoji} {w.trigger.label}</span>
                    <ArrowRight style={{ width: 10, height: 10 }} />
                    <span>{w.actions.length} acciones</span>
                  </div>
                </div>

                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <p style={{ fontSize: 22, fontWeight: 900, color: w.color, margin: 0, textShadow: `0 0 20px ${w.color}88` }}>{w.runsToday}</p>
                  <p style={{ fontSize: 8, color: T.textSub, fontFamily: 'monospace', textTransform: 'uppercase', margin: 0 }}>runs hoy</p>
                </div>
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <p style={{ fontSize: 16, fontWeight: 900, color: w.successRate > 60 ? '#22c55e' : T.amber, margin: 0, textShadow: `0 0 20px ${w.successRate > 60 ? '#22c55e' : T.amber}88` }}>{w.successRate}%</p>
                  <p style={{ fontSize: 8, color: T.textSub, fontFamily: 'monospace', textTransform: 'uppercase', margin: 0 }}>éxito</p>
                </div>
                {w.revenueImpact > 0 && (
                  <div style={{ textAlign: 'right', flexShrink: 0 }}>
                    <p style={{ fontSize: 16, fontWeight: 900, color: T.emerald, margin: 0, textShadow: '0 0 20px #10B98188' }}>${w.revenueImpact.toLocaleString()}</p>
                    <p style={{ fontSize: 8, color: T.textSub, fontFamily: 'monospace', textTransform: 'uppercase', margin: 0 }}>revenue</p>
                  </div>
                )}
              </button>

              {/* Expanded visual chain */}
              {isExpanded && (
                <div style={{ borderTop: `1px solid ${T.border}`, padding: 12, background: 'rgba(0,0,0,0.2)' }}>
                  <p style={{ fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, fontWeight: 700, marginBottom: 8 }}>FLUJO COMPLETO</p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4, overflowX: 'auto', paddingBottom: 8 }}>
                    {/* Trigger */}
                    <div style={{ borderRadius: 8, padding: 8, flexShrink: 0, minWidth: 150, background: `${w.color}18`, border: `1px solid ${w.color}50` }}>
                      <p style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: w.color, fontWeight: 700, marginBottom: 4 }}>TRIGGER</p>
                      <p style={{ fontSize: 11, fontWeight: 700, color: T.textPrim, margin: 0 }}>{w.trigger.emoji} {w.trigger.label}</p>
                    </div>

                    {/* Conditions */}
                    {w.conditions.length > 0 && (
                      <>
                        <ArrowRight style={{ width: 16, height: 16, color: T.textSub, flexShrink: 0 }} />
                        <div style={{ borderRadius: 8, padding: 8, flexShrink: 0, minWidth: 150, background: `${T.amber}12`, border: `1px solid ${T.amber}40` }}>
                          <p style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.amber, fontWeight: 700, marginBottom: 4 }}>IF</p>
                          {w.conditions.map((c, i) => (
                            <p key={i} style={{ fontSize: 10, color: T.textPrim, margin: 0, lineHeight: 1.5 }}>· {c}</p>
                          ))}
                        </div>
                      </>
                    )}

                    {/* Actions */}
                    {w.actions.map((a, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
                        <ArrowRight style={{ width: 14, height: 14, color: T.textSub, margin: '0 4px' }} />
                        <div style={{ borderRadius: 8, padding: 8, minWidth: 140, background: `${T.emerald}06`, border: `1px solid ${T.emerald}25` }}>
                          <p style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.emerald, fontWeight: 700, marginBottom: 4 }}>STEP {i + 1}</p>
                          <p style={{ fontSize: 11, fontWeight: 700, color: T.textPrim, margin: 0 }}>{a.emoji} {a.label}</p>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Toolbar */}
                  <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <button style={{
                      display: 'flex', alignItems: 'center', gap: 4, padding: '6px 12px', borderRadius: 6, fontSize: 10, fontWeight: 700, cursor: 'pointer',
                      background: w.active ? `${T.amber}18` : `${T.emerald}18`,
                      border: `1px solid ${w.active ? T.amber + '40' : T.emerald + '40'}`,
                      color: w.active ? T.amber : T.emerald,
                    }}>
                      {w.active ? <><Pause style={{ width: 10, height: 10 }} />Pausar</> : <><Play style={{ width: 10, height: 10 }} />Activar</>}
                    </button>
                    <button style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '6px 12px', borderRadius: 6, fontSize: 10, fontWeight: 700, cursor: 'pointer', background: 'rgba(255,255,255,0.05)', border: `1px solid ${T.border}`, color: T.textSub }}>
                      <Activity style={{ width: 10, height: 10 }} />Test run
                    </button>
                    <button style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '6px 12px', borderRadius: 6, fontSize: 10, fontWeight: 700, cursor: 'pointer', background: 'rgba(255,255,255,0.05)', border: `1px solid ${T.border}`, color: T.textSub }}>
                      <CheckCircle2 style={{ width: 10, height: 10 }} />Historial
                    </button>
                    <span style={{ marginLeft: 'auto', fontSize: 9, color: T.textSub, fontFamily: 'monospace' }}>trigger: {w.trigger.type}</span>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Footer */}
      <div style={{ borderTop: `1px solid ${T.border}`, background: `${T.emerald}04`, padding: '12px 20px', textAlign: 'center' }}>
        <p style={{ fontSize: 11, color: T.textSub, margin: 0 }}>
          <Bot style={{ width: 12, height: 12, display: 'inline', color: T.emerald, marginRight: 4 }} />
          IA detecta patrones y sugiere nuevos workflows automáticamente ·{' '}
          <span style={{ color: T.emerald, fontWeight: 700 }}>3 sugerencias pendientes</span>
        </p>
      </div>
    </section>
  )
}
