'use client'

/**
 * HANDOFF LOG — Slack interno de la IA
 *
 * Muestra comunicación inter-agente como mensajes de chat.
 * Cada departamento tiene avatar/color propio. Entradas con Framer Motion.
 *
 * Backend integration: useEffect → WebSocket subscription pushing HandoffEvent[].
 */

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Mail, Megaphone, Radio, Headphones, MonitorCheck,
  ArrowRight, MessageSquare, Activity,
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

// ── Department config ──────────────────────────────────────────────────────────
type DeptId = 'sdr' | 'ads' | 'pr' | 'cs' | 'cua' | 'core'

interface DeptConfig {
  label: string
  short: string
  icon:  React.ElementType
  color: string
}

const DEPTS: Record<DeptId, DeptConfig> = {
  sdr:  { label: 'SDR · Ventas',         short: 'SDR', icon: Mail,         color: T.cyan    },
  ads:  { label: 'Growth & Ads',          short: 'ADS', icon: Megaphone,    color: T.amber   },
  pr:   { label: 'PR & Reputación',       short: 'PR',  icon: Radio,        color: T.violet  },
  cs:   { label: 'Customer Success',      short: 'CS',  icon: Headphones,   color: T.emerald },
  cua:  { label: 'Computer Use',          short: 'CUA', icon: MonitorCheck, color: T.rose    },
  core: { label: 'Core · Orquestador',    short: 'OPS', icon: Activity,     color: '#CCFF33' },
}

// ── Event type ────────────────────────────────────────────────────────────────
interface HandoffEvent {
  id:        string
  ts:        string             // ISO
  from:      DeptId
  to?:       DeptId             // undefined → broadcast / status update
  text:      string
  tag?:      'HANDOFF' | 'STATUS' | 'ALERT' | 'WIN'
}

// ── Seed log (replace with WS feed) ────────────────────────────────────────────
const NOW = Date.now()
const fmtTs = (offsetSec: number): string => new Date(NOW - offsetSec * 1000).toISOString()

const SEED_LOG: HandoffEvent[] = [
  { id: 'h1', ts: fmtTs(8),   from: 'pr',  to: 'sdr', tag: 'HANDOFF', text: 'Lead caliente detectado en hilo LinkedIn · @maria_acme menciona dolor de "facturación manual"' },
  { id: 'h2', ts: fmtTs(22),  from: 'sdr',             tag: 'STATUS',  text: 'Secuencia outbound iniciada · 5 mensajes calibrados al perfil ICP' },
  { id: 'h3', ts: fmtTs(47),  from: 'ads', to: 'core', tag: 'ALERT',   text: 'Campaña #G-12 superó ROAS 5.0 · solicito autorización para escalar +30% budget' },
  { id: 'h4', ts: fmtTs(72),  from: 'sdr', to: 'cs',   tag: 'HANDOFF', text: 'Lead convertido (Acme Corp, USD 4.8k) · pasando onboarding a Customer Success' },
  { id: 'h5', ts: fmtTs(120), from: 'cs',              tag: 'WIN',     text: 'NPS 9 recibido de cliente Beta SRL · candidato a programa Embajador' },
  { id: 'h6', ts: fmtTs(190), from: 'cua', to: 'core', tag: 'ALERT',   text: 'Pausa en checkout proveedor · CAPTCHA detectado · esperando aprobación humana' },
  { id: 'h7', ts: fmtTs(260), from: 'pr',  to: 'ads',  tag: 'HANDOFF', text: '23 menciones positivas en últimas 4h · momentum favorable para lanzar campaña brand' },
]

// New events queue — for demo
const NEW_EVENTS_POOL: Omit<HandoffEvent, 'id' | 'ts'>[] = [
  { from: 'sdr', to: 'cs',   tag: 'HANDOFF', text: 'Deal cerrado · USD 2.4k · cliente "Tomás N." asignado a onboarding' },
  { from: 'ads', to: 'core', tag: 'WIN',     text: 'CAC bajó a $14 · 22% por debajo del benchmark del sector' },
  { from: 'pr',              tag: 'STATUS',  text: 'Sentimiento de marca subió +0.08 esta semana · trending positivo' },
  { from: 'cua', to: 'sdr',  tag: 'HANDOFF', text: 'Catálogo Shopify actualizado · 47 productos sincronizados · stock OK' },
  { from: 'cs',  to: 'pr',   tag: 'HANDOFF', text: 'Testimonio en video recibido · solicitando publicación en redes' },
  { from: 'ads',             tag: 'ALERT',   text: 'CTR de campaña #M-08 bajó 18% · iniciando A/B test nuevo creative' },
]

// ── Helpers ────────────────────────────────────────────────────────────────────
const TAG_COLORS: Record<NonNullable<HandoffEvent['tag']>, string> = {
  HANDOFF: T.cyan,
  STATUS:  T.textSub,
  ALERT:   T.amber,
  WIN:     T.emerald,
}

const timeAgo = (iso: string): string => {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (diff < 60)   return `${diff}s`
  if (diff < 3600) return `${Math.floor(diff / 60)}m`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`
  return `${Math.floor(diff / 86400)}d`
}

// ── Avatar chip ────────────────────────────────────────────────────────────────
const Avatar = ({ dept, size = 28 }: { dept: DeptId; size?: number }): React.JSX.Element => {
  const cfg = DEPTS[dept]
  const Icon = cfg.icon
  return (
    <div style={{
      width: size, height: size, borderRadius: size / 4,
      background: `${cfg.color}18`,
      border: `1px solid ${cfg.color}40`,
      display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
    }}>
      <Icon size={size * 0.5} style={{ color: cfg.color }} />
    </div>
  )
}

// ── Component ─────────────────────────────────────────────────────────────────
interface HandoffLogProps {
  // Optional: pass external events from parent (e.g. WebSocket data)
  events?: HandoffEvent[]
  /** If true, simulates new events arriving every N seconds (demo only) */
  simulateLive?: boolean
}

export default function HandoffLog({ events: extEvents, simulateLive = true }: HandoffLogProps): React.JSX.Element {
  const [log, setLog] = useState<HandoffEvent[]>(extEvents ?? SEED_LOG)
  const [filter, setFilter] = useState<DeptId | 'all'>('all')

  // Sync external events
  useEffect(() => {
    if (extEvents) setLog(extEvents)
  }, [extEvents])

  // Simulated live feed
  useEffect(() => {
    if (extEvents || !simulateLive) return
    const id = setInterval(() => {
      const tmpl = NEW_EVENTS_POOL[Math.floor(Math.random() * NEW_EVENTS_POOL.length)]
      const newEv: HandoffEvent = {
        ...tmpl,
        id:  `live_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
        ts:  new Date().toISOString(),
      }
      setLog(p => [newEv, ...p].slice(0, 30))
    }, 7000)
    return () => clearInterval(id)
  }, [extEvents, simulateLive])

  const visible = filter === 'all' ? log : log.filter(e => e.from === filter || e.to === filter)

  return (
    <section style={{ background: T.bgCard, border: `1px solid ${T.border}`, borderRadius: 16, overflow: 'hidden' }}>
      <div style={{ height: 1, background: `linear-gradient(90deg, transparent, ${T.violet}80, ${T.cyan}60, transparent)` }} />

      {/* Header */}
      <div style={{ padding: '14px 18px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 34, height: 34, borderRadius: 9, background: `${T.violet}22`, border: `1px solid ${T.violet}44`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <MessageSquare size={16} style={{ color: T.violet }} />
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, fontFamily: "'Space Grotesk',sans-serif" }}>
              Handoff Log · Slack IA
            </div>
            <div style={{ fontSize: 10, color: T.textSub, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', marginTop: 2 }}>
              {visible.length} eventos · {Object.keys(DEPTS).length} departamentos
            </div>
          </div>
        </div>

        {/* Filter chips */}
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {(['all', ...Object.keys(DEPTS)] as (DeptId | 'all')[]).map(f => {
            const active = filter === f
            const col = f === 'all' ? T.textPrim : DEPTS[f as DeptId].color
            return (
              <button key={f} type="button" onClick={() => setFilter(f)}
                style={{
                  padding: '3px 9px', borderRadius: 6, fontSize: 10, fontWeight: 700, cursor: 'pointer',
                  fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.05em', textTransform: 'uppercase',
                  border: `1px solid ${active ? col : `${col}30`}`,
                  background: active ? `${col}20` : 'transparent',
                  color: active ? col : T.textSub,
                  transition: 'all .15s',
                }}>
                {f === 'all' ? 'TODOS' : DEPTS[f as DeptId].short}
              </button>
            )
          })}
        </div>
      </div>

      {/* Log entries */}
      <div style={{ padding: 12, maxHeight: 480, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
        <AnimatePresence initial={false} mode="popLayout">
          {visible.map(ev => {
            const fromCfg = DEPTS[ev.from]
            const toCfg   = ev.to ? DEPTS[ev.to] : null
            const tagCol  = ev.tag ? TAG_COLORS[ev.tag] : T.textSub
            return (
              <motion.div
                key={ev.id}
                layout
                initial={{ opacity: 0, y: -10, scale: 0.98 }}
                animate={{ opacity: 1, y: 0,   scale: 1    }}
                exit={{    opacity: 0, x: 30,  scale: 0.96 }}
                transition={{ duration: 0.32, ease: [0.2, 0.8, 0.2, 1] }}
                style={{
                  display: 'flex', gap: 10, padding: '10px 12px',
                  background: T.bgApp,
                  border: `1px solid ${T.border}`,
                  borderRadius: 10,
                  borderLeftWidth: 3,
                  borderLeftColor: fromCfg.color,
                }}>
                <Avatar dept={ev.from} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  {/* Header row */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', marginBottom: 4 }}>
                    <span style={{ fontSize: 12, fontWeight: 700, color: fromCfg.color, fontFamily: "'Space Grotesk',sans-serif" }}>
                      {fromCfg.short}
                    </span>
                    {toCfg && (
                      <>
                        <ArrowRight size={11} style={{ color: T.textSub }} />
                        <span style={{ fontSize: 12, fontWeight: 700, color: toCfg.color, fontFamily: "'Space Grotesk',sans-serif" }}>
                          {toCfg.short}
                        </span>
                      </>
                    )}
                    {ev.tag && (
                      <span style={{
                        padding: '1px 6px', borderRadius: 4, fontSize: 9, fontWeight: 700,
                        fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.04em',
                        background: `${tagCol}18`, border: `1px solid ${tagCol}30`, color: tagCol,
                      }}>
                        {ev.tag}
                      </span>
                    )}
                    <span style={{ fontSize: 10, color: T.textSub, fontFamily: 'JetBrains Mono,monospace', marginLeft: 'auto' }}>
                      {timeAgo(ev.ts)}
                    </span>
                  </div>

                  {/* Message text */}
                  <div style={{ fontSize: 12, color: T.textPrim, lineHeight: 1.45 }}>
                    {ev.text}
                  </div>
                </div>
              </motion.div>
            )
          })}
        </AnimatePresence>

        {visible.length === 0 && (
          <div style={{ padding: 24, textAlign: 'center', color: T.textSub, fontFamily: 'JetBrains Mono,monospace', fontSize: 12 }}>
            Sin eventos para este filtro
          </div>
        )}
      </div>
    </section>
  )
}

// ── Types export ──────────────────────────────────────────────────────────────
export type { HandoffEvent, DeptId }
