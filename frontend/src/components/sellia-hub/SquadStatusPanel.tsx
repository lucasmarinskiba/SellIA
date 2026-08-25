'use client'

/**
 * SQUAD STATUS PANEL
 *
 * Divide la IA en departamentos visibles. Cada tarjeta = un agente líder
 * con telemetría en vivo + indicador de estado titilante.
 *
 * Squads:
 *   - SDR (Ventas)       — emails enviados, respuestas
 *   - Growth/Ads          — ROAS en tiempo real, presupuesto consumido
 *   - PR / Reputación     — menciones monitoreadas, sentimiento
 *   - Customer Success    — tickets, NPS
 *   - Operations / CUA    — tareas automáticas, navegador
 */

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Mail, Megaphone, Radio, Headphones, MonitorCheck,
  TrendingUp, TrendingDown, Activity, Pause,
} from 'lucide-react'

// ── Design tokens ──────────────────────────────────────────────────────────────
const T = {
  bgApp:      '#0B0F19',
  bgCard:     '#151B2B',
  bgCardHov:  '#1A2235',
  border:     '#2A3441',
  textPrim:   '#F3F4F6',
  textSub:    '#9CA3AF',
  emerald:    '#10B981',
  cyan:       '#06B6D4',
  amber:      '#F59E0B',
  violet:     '#8B5CF6',
  rose:       '#ef4444',
} as const

// ── Types ──────────────────────────────────────────────────────────────────────
type SquadStatus = 'executing' | 'idle' | 'paused' | 'attention'

interface SquadMetric {
  label: string
  value: string
  trend?: 'up' | 'down' | 'flat'
  delta?: string
}

interface Squad {
  id:        string
  name:      string
  role:      string
  icon:      React.ElementType
  color:     string
  status:    SquadStatus
  statusMsg: string
  metrics:   SquadMetric[]
  lastAction: string
}

// ── Real data from backend (GET /api/v1/brain/squads) ──────────────────────────
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://sellia-production.up.railway.app'

const SQUAD_ICON: Record<string, React.ElementType> = {
  sdr: Mail, ads: Megaphone, pr: Radio, cs: Headphones, cua: MonitorCheck,
}
const SQUAD_ROLE: Record<string, string> = {
  sdr: 'Prospección & ventas',
  ads: 'Adquisición · leads inbound',
  pr: 'Social listening · brand',
  cs: 'Retención · soporte',
  cua: 'Operaciones · navegador',
}

interface RawSquad {
  id: string
  name: string
  color: string
  leads: number
  won: number
  avg_score: number
  pipeline_value: number
  conversion_rate: number
}

const mapRawSquad = (r: RawSquad): Squad => ({
  id: r.id,
  name: r.name,
  role: SQUAD_ROLE[r.id] || 'Operaciones',
  icon: SQUAD_ICON[r.id] || Activity,
  color: r.color,
  status: r.leads > 0 ? 'executing' : 'idle',
  statusMsg: r.leads > 0
    ? `${r.leads} leads en pipeline · ${r.won} ganados`
    : 'Sin actividad registrada aún',
  lastAction: r.leads > 0 ? `Score promedio ${r.avg_score.toFixed(1)}` : '—',
  metrics: [
    { label: 'Leads',        value: String(r.leads) },
    { label: 'Ganados',      value: String(r.won) },
    { label: 'Conversión',   value: `${r.conversion_rate}%` },
    { label: 'Pipeline $',   value: `$${r.pipeline_value.toLocaleString()}` },
  ],
})

// ── Helpers ────────────────────────────────────────────────────────────────────
const STATUS_CONFIG: Record<SquadStatus, { label: string; color: string; pulse: boolean }> = {
  executing: { label: 'EJECUTANDO',  color: T.emerald, pulse: true  },
  idle:      { label: 'EN REPOSO',    color: T.textSub, pulse: false },
  paused:    { label: 'PAUSADO',      color: T.amber,   pulse: false },
  attention: { label: 'ATENCIÓN',     color: T.rose,    pulse: true  },
}

const trendIcon = (t?: 'up' | 'down' | 'flat'): React.JSX.Element | null => {
  if (t === 'up')   return <TrendingUp  size={10} style={{ color: T.emerald }} />
  if (t === 'down') return <TrendingDown size={10} style={{ color: T.rose }} />
  return null
}

// ── Component ─────────────────────────────────────────────────────────────────
export default function SquadStatusPanel(): React.JSX.Element {
  const [squads, setSquads] = useState<Squad[]>([])

  // Poll real squad data from backend every 20s
  useEffect(() => {
    let alive = true
    const fetchSquads = async (): Promise<void> => {
      try {
        const r = await fetch(`${BACKEND_URL}/api/v1/brain/squads`, { cache: 'no-store' })
        if (!r.ok) throw new Error(String(r.status))
        const data = (await r.json()) as { squads: RawSquad[] }
        if (!alive) return
        setSquads(data.squads.map(mapRawSquad))
      } catch {
        // Backend unreachable — leave squads empty rather than fabricate data
      }
    }
    void fetchSquads()
    const id = window.setInterval(() => { void fetchSquads() }, 20000)
    return () => { alive = false; window.clearInterval(id) }
  }, [])

  return (
    <section style={{ background: T.bgCard, border: `1px solid ${T.border}`, borderRadius: 16, overflow: 'hidden' }}>
      <div style={{ height: 1, background: `linear-gradient(90deg, transparent, ${T.cyan}80, ${T.violet}60, transparent)` }} />

      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 36, height: 36, borderRadius: 10, background: `${T.cyan}22`, border: `1px solid ${T.cyan}44`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Activity size={17} style={{ color: T.cyan }} />
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: T.textPrim, fontFamily: "'Space Grotesk',sans-serif" }}>
              Escuadrones SellIA
            </div>
            <div style={{ fontSize: 10, color: T.textSub, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', marginTop: 2 }}>
              {squads.filter(s => s.status === 'executing').length}/{squads.length} ejecutando · telemetría en vivo
            </div>
          </div>
        </div>
      </div>

      {/* Cards grid */}
      <div style={{ padding: 16, display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
        <AnimatePresence mode="popLayout">
          {squads.map((s, idx) => {
            const cfg = STATUS_CONFIG[s.status]
            const Icon = s.icon
            return (
              <motion.div
                key={s.id}
                layout
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ delay: idx * 0.05, duration: 0.32, ease: [0.2, 0.8, 0.2, 1] }}
                style={{
                  background: T.bgCard,
                  border: `1px solid ${s.color}28`,
                  borderRadius: 12,
                  padding: 14,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 12,
                  boxShadow: s.status === 'executing' ? `0 0 24px -10px ${s.color}40` : 'none',
                }}
              >
                {/* Header row */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 9, minWidth: 0 }}>
                    <div style={{ width: 30, height: 30, borderRadius: 8, background: `${s.color}18`, border: `1px solid ${s.color}30`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <Icon size={14} style={{ color: s.color }} />
                    </div>
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, fontFamily: "'Space Grotesk',sans-serif", lineHeight: 1.2 }}>
                        {s.name}
                      </div>
                      <div style={{ fontSize: 10, color: T.textSub, marginTop: 1 }}>
                        {s.role}
                      </div>
                    </div>
                  </div>

                  {/* Status pill with pulse dot */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '3px 8px', borderRadius: 6, background: `${cfg.color}14`, border: `1px solid ${cfg.color}30`, flexShrink: 0 }}>
                    {cfg.pulse ? (
                      <motion.div
                        animate={{ opacity: [0.4, 1, 0.4], scale: [1, 1.25, 1] }}
                        transition={{ duration: 1.4, repeat: Infinity, ease: 'easeInOut' }}
                        style={{ width: 6, height: 6, borderRadius: 3, background: cfg.color, boxShadow: `0 0 8px ${cfg.color}` }}
                      />
                    ) : (
                      <Pause size={8} style={{ color: cfg.color }} />
                    )}
                    <span style={{ fontSize: 9, fontWeight: 700, color: cfg.color, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.05em' }}>
                      {cfg.label}
                    </span>
                  </div>
                </div>

                {/* Status message */}
                <div style={{ padding: '7px 10px', borderRadius: 8, background: `${T.bgApp}80`, border: `1px solid ${T.border}` }}>
                  <div style={{ fontSize: 11, color: T.textPrim, lineHeight: 1.35 }}>
                    {s.statusMsg}
                  </div>
                  <div style={{ fontSize: 10, color: T.textSub, fontFamily: 'JetBrains Mono,monospace', marginTop: 3 }}>
                    {s.lastAction}
                  </div>
                </div>

                {/* Metrics 2×2 grid */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                  {s.metrics.map(m => (
                    <div key={m.label} style={{ padding: '8px 9px', borderRadius: 8, background: `${s.color}06`, border: `1px solid ${s.color}18` }}>
                      <div style={{ fontSize: 9, color: T.textSub, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.05em', textTransform: 'uppercase', marginBottom: 3 }}>
                        {m.label}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
                        <span style={{ fontSize: 15, fontWeight: 800, color: s.color, fontFamily: "'Space Grotesk',sans-serif", letterSpacing: '-0.02em', textShadow: `0 0 14px ${s.color}66`, fontVariantNumeric: 'tabular-nums' }}>
                          {m.value}
                        </span>
                      </div>
                      {m.delta && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 3, marginTop: 2 }}>
                          {trendIcon(m.trend)}
                          <span style={{ fontSize: 9, color: m.trend === 'up' ? T.emerald : m.trend === 'down' ? T.rose : T.textSub, fontFamily: 'JetBrains Mono,monospace' }}>
                            {m.delta}
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>
    </section>
  )
}

// ── Types export for API consumers ─────────────────────────────────────────────
export type { Squad, SquadStatus, SquadMetric }

