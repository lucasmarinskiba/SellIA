'use client'

/**
 * BRAIN FLOWS VIEW · estilo n8n / Make
 *
 * Lista de flujos de interacción que se están llevando a cabo:
 *   - Automatizaciones reales del backend (GET /brain/flows): trigger → agentes → tools → plataformas.
 *   - Sesiones de Computer Use despachadas (GET /brain/cua/flows): indicación → agente → tools → plataformas.
 *
 * Cada flujo = un mini-canvas tipo n8n (nodos-tarjeta conectados por curvas con
 * flecha + etiqueta de relación). Los nodos/edges se iluminan con actividad real
 * (GET /brain/activity). Datos reales con fallback bundled (Vercel-safe).
 */

import { useEffect, useMemo, useRef, useState } from 'react'
import { Workflow, Bot, Zap, Cpu } from 'lucide-react'
import { SELLIA, GROUP_COLOR } from '@/lib/sellia-theme'

const BRAIN = '/api/v1/brain'

interface Step { id: string; label: string; kind: string; group?: string; col: number }
interface FlowEdge { source: string; target: string; rel: string }
interface Flow { id: string; name: string; kind: string; group?: string; mode?: string; status?: string; instruction?: string; steps: Step[]; edges: FlowEdge[] }
interface ActivityEvent { seq: number; source: string; target: string | null; detail: string }

const COL_W = 196
const ROW_H = 64
const NODE_W = 150
const NODE_H = 38

const KIND_ICON: Record<string, React.ReactNode> = {
  automation: <Zap size={12} />, agent: <Bot size={12} />, skill: <Cpu size={12} />,
  platform: <Workflow size={12} />, cua: <Cpu size={12} />,
}

const fetchJSON = async (live: string, bundled: string, signal?: AbortSignal): Promise<{ flows: Flow[] } | null> => {
  for (const url of [live, bundled]) {
    try {
      const s = signal ? AbortSignal.any([signal, AbortSignal.timeout(2500)]) : AbortSignal.timeout(2500)
      const r = await fetch(url, { signal: s })
      if (r.ok) { const d = await r.json(); if (Array.isArray(d.flows)) return d }
    } catch { /* next */ }
  }
  return null
}

const FlowCard = ({ flow, hotNodes }: { flow: Flow; hotNodes: Set<string> }): React.JSX.Element => {
  const pos = useMemo(() => {
    const byCol = new Map<number, Step[]>()
    for (const s of flow.steps) { const a = byCol.get(s.col) ?? []; a.push(s); byCol.set(s.col, a) }
    const m = new Map<string, { x: number; y: number }>()
    let maxRows = 1
    for (const [col, arr] of byCol) {
      maxRows = Math.max(maxRows, arr.length)
      arr.forEach((s, i) => m.set(s.id, { x: 16 + col * COL_W, y: 16 + i * ROW_H }))
    }
    return { m, w: 16 + 4 * COL_W, h: 32 + maxRows * ROW_H }
  }, [flow])

  const running = flow.status === 'running'
  return (
    <div style={{ background: SELLIA.panel, border: `1px solid ${running ? SELLIA.emerald + '55' : SELLIA.border}`, borderRadius: 12, overflow: 'hidden' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 9, padding: '10px 14px', borderBottom: `1px solid ${SELLIA.border}` }}>
        <span style={{ width: 26, height: 26, borderRadius: 7, display: 'grid', placeItems: 'center', background: `${GROUP_COLOR[flow.group ?? ''] ?? SELLIA.cobalt}1F`, border: `1px solid ${GROUP_COLOR[flow.group ?? ''] ?? SELLIA.cobalt}44`, color: GROUP_COLOR[flow.group ?? ''] ?? SELLIA.cobalt }}>
          {flow.kind === 'cua' ? <Cpu size={14} /> : <Workflow size={14} />}
        </span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: SELLIA.text, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{flow.name}</div>
          <div style={{ fontSize: 10.5, color: SELLIA.text2, fontFamily: SELLIA.mono }}>
            {flow.kind === 'cua' ? `Computer Use · ${flow.mode ?? ''}` : 'Automatización'}{flow.instruction ? ` · “${flow.instruction.slice(0, 48)}”` : ''}
          </div>
        </div>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 10, fontFamily: SELLIA.mono, fontWeight: 600, color: running ? SELLIA.emerald : SELLIA.text3 }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: running ? SELLIA.emerald : SELLIA.text3, animation: running ? 'flow-pulse 1.4s ease-in-out infinite' : 'none' }} />
          {running ? 'EN CURSO' : 'LISTO'}
        </span>
      </div>

      <div style={{ position: 'relative', width: '100%', overflowX: 'auto', background: SELLIA.bg }}>
        <div style={{ position: 'relative', width: pos.w, height: pos.h, minWidth: '100%' }}>
          <style>{`@keyframes flow-pulse{0%,100%{opacity:1}50%{opacity:.4}}@keyframes flow-dash{to{stroke-dashoffset:-12}}`}</style>
          <svg width={pos.w} height={pos.h} style={{ position: 'absolute', inset: 0 }}>
            <defs>
              <marker id="fl-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto" markerUnits="userSpaceOnUse">
                <path d="M0,0 L6,3 L0,6 Z" fill={SELLIA.text3} />
              </marker>
            </defs>
            {flow.edges.map((e, i) => {
              const a = pos.m.get(e.source); const b = pos.m.get(e.target)
              if (!a || !b) return null
              const x1 = a.x + NODE_W, y1 = a.y + NODE_H / 2, x2 = b.x, y2 = b.y + NODE_H / 2
              const mx = (x1 + x2) / 2
              const hot = hotNodes.has(e.source) || hotNodes.has(e.target)
              return (
                <g key={i}>
                  <path d={`M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`} fill="none"
                    stroke={hot ? SELLIA.cobalt : SELLIA.border} strokeWidth={hot ? 1.8 : 1}
                    strokeDasharray={hot ? '4 4' : undefined} style={hot ? { animation: 'flow-dash .6s linear infinite' } : undefined}
                    markerEnd="url(#fl-arrow)" opacity={hot ? 0.95 : 0.5} />
                  <text x={mx} y={(y1 + y2) / 2 - 3} textAnchor="middle" fill={SELLIA.text3} fontSize={8} fontFamily={SELLIA.mono}>{e.rel}</text>
                </g>
              )
            })}
          </svg>
          {flow.steps.map(s => {
            const p = pos.m.get(s.id)!; const c = GROUP_COLOR[s.group ?? ''] ?? SELLIA.text2
            const hot = hotNodes.has(s.id)
            return (
              <div key={s.id} style={{
                position: 'absolute', left: p.x, top: p.y, width: NODE_W, height: NODE_H,
                display: 'flex', alignItems: 'center', gap: 7, padding: '0 9px', borderRadius: 8,
                background: hot ? `${c}26` : SELLIA.panel, border: `1px solid ${hot ? c : SELLIA.border}`,
                color: SELLIA.text, fontSize: 11, fontWeight: 600, fontFamily: SELLIA.sans,
                boxShadow: hot ? `0 0 0 1px ${c}` : 'none', transition: 'background .2s, border-color .2s',
              }}>
                <span style={{ color: c, flexShrink: 0 }}>{KIND_ICON[s.kind] ?? <Cpu size={12} />}</span>
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.label}</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default function BrainFlowsView({ extraFlows = [] }: { extraFlows?: Flow[] }): React.JSX.Element {
  const [autoFlows, setAutoFlows] = useState<Flow[]>([])
  const [cuaFlows, setCuaFlows] = useState<Flow[]>([])
  const [hotNodes, setHotNodes] = useState<Set<string>>(new Set())
  const sinceSeq = useRef(0)
  const base = useRef(BRAIN)

  // automations (una vez) + base detection
  useEffect(() => {
    const ctrl = new AbortController()
    const load = async (): Promise<void> => {
      const live = await fetchJSON(`${BRAIN}/flows`, '', ctrl.signal)
      if (live) { base.current = BRAIN; setAutoFlows(live.flows) }
      else {
        const b = await fetchJSON('/api/brain/flows', '/api/brain/flows', ctrl.signal)
        base.current = '/api/brain'; if (b) setAutoFlows(b.flows)
      }
    }
    void load()
    return () => ctrl.abort()
  }, [])

  // CU sessions + activity poll (vivo)
  useEffect(() => {
    let alive = true
    const tick = async (): Promise<void> => {
      try {
        const r = await fetch(`${base.current}/cua/flows?limit=20`, { signal: AbortSignal.timeout(2500) })
        if (r.ok) { const d = await r.json(); if (alive && Array.isArray(d.flows)) setCuaFlows([...d.flows].reverse()) }
      } catch { /* idle */ }
      try {
        const r = await fetch(`${base.current}/activity?limit=30&since_seq=${sinceSeq.current}`, { signal: AbortSignal.timeout(2500) })
        if (r.ok) {
          const evs = ((await r.json()).events ?? []) as ActivityEvent[]
          if (alive && evs.length) {
            sinceSeq.current = Math.max(sinceSeq.current, ...evs.map(e => e.seq))
            const hot = new Set<string>()
            for (const e of evs) { hot.add(e.source); if (e.target) hot.add(e.target) }
            setHotNodes(hot)
            window.setTimeout(() => setHotNodes(new Set()), 1800)
          }
        }
      } catch { /* idle */ }
    }
    void tick()
    const iv = window.setInterval(() => { void tick() }, 2800)
    return () => { alive = false; window.clearInterval(iv) }
  }, [])

  const flows = useMemo(() => [...extraFlows, ...cuaFlows, ...autoFlows], [extraFlows, cuaFlows, autoFlows])

  return (
    <div style={{ background: SELLIA.bg, padding: 14, maxHeight: 620, overflowY: 'auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12, flexWrap: 'wrap' }}>
        <span style={{ fontFamily: SELLIA.mono, fontSize: 11, color: SELLIA.text2 }}>
          {extraFlows.length} plan por cuenta · {cuaFlows.length} sesiones CU · {autoFlows.length} automatizaciones
        </span>
        {cuaFlows.length === 0 && (
          <span style={{ fontSize: 11, color: SELLIA.text3 }}>Despachá una indicación de Computer Use para ver su flujo en vivo.</span>
        )}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {flows.map(f => <FlowCard key={f.id} flow={f} hotNodes={hotNodes} />)}
        {flows.length === 0 && (
          <div style={{ padding: 30, textAlign: 'center', color: SELLIA.text3, fontSize: 13 }}>
            Sin flujos disponibles. (¿backend del cerebro arriba?)
          </div>
        )}
      </div>
    </div>
  )
}
