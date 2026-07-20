'use client'

/**
 * BRAIN INTERACTION MAP · mapa de interacciones REAL
 *
 * Grafo interactivo (React Flow / @xyflow/react) del cerebro SellIA:
 * agentes, automatizaciones, skills, plataformas (ventas/publicación/anuncios/…)
 * y herramientas (creatividad/análisis/chat/…), clusterizados por categoría.
 *
 * Datos REALES: GET /api/v1/brain/graph (fallback /api/brain/graph). Las sinapsis
 * se encienden con telemetría real (/api/v1/brain/activity); idle si no hay
 * actividad — NUNCA inventa interacciones. Flechas direccionales + label de
 * relación (alimenta/usa/orquesta/opera/consulta/produce). Hover/click resalta
 * interacciones; chips filtran por categoría. Paleta corporativa fija.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  ReactFlow, ReactFlowProvider, Background, Controls, MiniMap,
  BackgroundVariant, MarkerType, Handle, Position,
  useNodesState, useEdgesState,
  type Node, type Edge, type NodeProps,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { SELLIA, GROUP_COLOR, GROUP_LABEL } from '@/lib/sellia-theme'

const BRAIN_BASE = '/api/v1/brain'

interface RawNode {
  id: string; label: string; kind: string; category: string
  layer: number; group: string; group_label?: string; health: number; tags: string[]
}
interface RawEdge { source: string; target: string; rel: string }
interface ActivityEvent { seq: number; ts: number; kind: string; source: string; target: string | null; detail: string }

const LAYER_X: Record<number, number> = { 0: 0, 1: 360, 2: 720, 3: 1060 }
const KIND_LABEL: Record<number, string> = { 0: 'Plataformas', 1: 'Skills / Herramientas', 2: 'Agentes', 3: 'Automatizaciones' }
const MAX_PER_COL = 22
const COL_GAP = 168
const ROW_GAP = 46

type CatData = { label: string; group: string; health: number; kind: string; dim: boolean; hot: boolean }

const CatNode = ({ data }: NodeProps<Node<CatData>>): React.JSX.Element => {
  const color = GROUP_COLOR[data.group] ?? SELLIA.text2
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 7, padding: '5px 10px',
      borderRadius: 8, fontFamily: SELLIA.sans, fontSize: 11, fontWeight: 600,
      color: SELLIA.text, whiteSpace: 'nowrap',
      background: data.hot ? `${color}26` : SELLIA.panel,
      border: `1px solid ${data.hot ? color : SELLIA.border}`,
      opacity: data.dim ? 0.18 : 0.45 + 0.55 * data.health,
      boxShadow: data.hot ? `0 0 0 1px ${color}, 0 6px 20px -8px ${color}` : 'none',
      transition: 'opacity .15s, border-color .15s, background .15s',
    }}>
      <Handle type="target" position={Position.Left} style={{ opacity: 0, width: 1, height: 1 }} />
      <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }} />
      <span style={{ maxWidth: 130, overflow: 'hidden', textOverflow: 'ellipsis' }}>{data.label}</span>
      <Handle type="source" position={Position.Right} style={{ opacity: 0, width: 1, height: 1 }} />
    </div>
  )
}

const nodeTypes = { cat: CatNode }

// layout determinista: columna por kind-layer, sub-columnas + filas ordenadas por grupo
const computePositions = (raw: RawNode[]): Map<string, { x: number; y: number }> => {
  const byLayer = new Map<number, RawNode[]>()
  for (const n of raw) {
    const a = byLayer.get(n.layer) ?? []; a.push(n); byLayer.set(n.layer, a)
  }
  const pos = new Map<string, { x: number; y: number }>()
  for (const [layer, arr] of byLayer) {
    arr.sort((a, b) => a.group.localeCompare(b.group) || a.label.localeCompare(b.label))
    const subCols = Math.max(1, Math.ceil(arr.length / MAX_PER_COL))
    const perCol = Math.ceil(arr.length / subCols)
    const baseX = LAYER_X[layer] ?? 0
    arr.forEach((n, i) => {
      const col = Math.floor(i / perCol)
      const row = i % perCol
      pos.set(n.id, { x: baseX + col * COL_GAP, y: 60 + row * ROW_GAP })
    })
  }
  return pos
}

const Inner = (): React.JSX.Element => {
  const [raw, setRaw] = useState<{ nodes: RawNode[]; edges: RawEdge[] }>({ nodes: [], edges: [] })
  const [offline, setOffline] = useState(false)
  const [src, setSrc] = useState<'live' | 'bundled'>('live')
  const [hovered, setHovered] = useState<string | null>(null)
  const [activeGroup, setActiveGroup] = useState<string | null>(null)
  const [hotEdges, setHotEdges] = useState<Set<string>>(new Set())
  const [lastEvent, setLastEvent] = useState<string>('—')
  const activityBase = useRef(BRAIN_BASE)
  const sinceSeq = useRef(0)

  // ── carga grafo real (live → bundled) ──
  useEffect(() => {
    const ctrl = new AbortController()
    const fetchGraph = async (base: string): Promise<{ nodes: RawNode[]; edges: RawEdge[] } | null> => {
      try {
        // timeout corto: si el backend live no responde, caer rápido al bundled
        const signal = AbortSignal.any([ctrl.signal, AbortSignal.timeout(2500)])
        const r = await fetch(`${base}/graph`, { signal })
        if (!r.ok) return null
        return (await r.json()) as { nodes: RawNode[]; edges: RawEdge[] }
      } catch { return null }
    }
    const load = async (): Promise<void> => {
      let g = await fetchGraph(BRAIN_BASE); let base = BRAIN_BASE; let s: 'live' | 'bundled' = 'live'
      if (!g || !g.nodes?.length) { g = await fetchGraph('/api/brain'); base = '/api/brain'; s = 'bundled' }
      if (!g || !g.nodes?.length) { setOffline(true); return }
      activityBase.current = base; setSrc(s); setOffline(false)
      setRaw({ nodes: g.nodes, edges: g.edges ?? [] })
      try {
        const a = await fetch(`${base}/activity?limit=1`, { signal: ctrl.signal })
        if (a.ok) sinceSeq.current = ((await a.json()).stats?.total) ?? 0
      } catch { /* idle */ }
    }
    void load()
    return () => ctrl.abort()
  }, [])

  const positions = useMemo(() => computePositions(raw.nodes), [raw.nodes])
  const edgeKey = (e: RawEdge): string => `${e.source}__${e.target}`

  // adyacencia para resaltar interacciones
  const adj = useMemo(() => {
    const m = new Map<string, Set<string>>()
    const ev = new Map<string, RawEdge[]>()
    for (const e of raw.edges) {
      ;(m.get(e.source) ?? m.set(e.source, new Set()).get(e.source)!).add(e.target)
      ;(m.get(e.target) ?? m.set(e.target, new Set()).get(e.target)!).add(e.source)
      ;(ev.get(e.source) ?? ev.set(e.source, []).get(e.source)!).push(e)
    }
    return { neighbors: m, bySource: ev }
  }, [raw.edges])

  // foco activo: hover o grupo
  const focusIds = useMemo(() => {
    if (hovered) return new Set<string>([hovered, ...(adj.neighbors.get(hovered) ?? [])])
    if (activeGroup) {
      const ids = new Set<string>()
      for (const n of raw.nodes) if (n.group === activeGroup) {
        ids.add(n.id); for (const nb of adj.neighbors.get(n.id) ?? []) ids.add(nb)
      }
      return ids
    }
    return null
  }, [hovered, activeGroup, raw.nodes, adj])

  // ── poll actividad real → enciende edges ──
  useEffect(() => {
    if (!raw.nodes.length) return
    let alive = true
    const tick = async (): Promise<void> => {
      try {
        const r = await fetch(`${activityBase.current}/activity?limit=30&since_seq=${sinceSeq.current}`)
        if (!r.ok) return
        const evs = ((await r.json()).events ?? []) as ActivityEvent[]
        if (!alive || !evs.length) return
        sinceSeq.current = Math.max(sinceSeq.current, ...evs.map(e => e.seq))
        const hot = new Set<string>()
        for (const e of evs) {
          const cand = adj.bySource.get(e.source)?.[0]
          if (cand) hot.add(edgeKey(cand))
        }
        if (hot.size) {
          setHotEdges(hot); setLastEvent(evs[evs.length - 1].detail)
          window.setTimeout(() => setHotEdges(new Set()), 1600)
        }
      } catch { /* idle */ }
    }
    void tick()
    const iv = window.setInterval(() => { void tick() }, 2500)
    return () => { alive = false; window.clearInterval(iv) }
  }, [raw.nodes.length, adj])

  const derivedNodes = useMemo<Node<CatData>[]>(() => raw.nodes.map(n => {
    const p = positions.get(n.id) ?? { x: 0, y: 0 }
    const dim = focusIds ? !focusIds.has(n.id) : false
    const hot = hovered === n.id || (!!activeGroup && n.group === activeGroup)
    return {
      id: n.id, type: 'cat', position: p, draggable: true,
      data: { label: n.label, group: n.group, health: n.health, kind: n.kind, dim, hot },
    }
  }), [raw.nodes, positions, focusIds, hovered, activeGroup])

  const derivedEdges = useMemo<Edge[]>(() => raw.edges.map(e => {
    const k = edgeKey(e)
    const hot = hotEdges.has(k)
    const focused = focusIds ? (focusIds.has(e.source) && focusIds.has(e.target)) : false
    const show = hot || focused
    const color = hot ? SELLIA.cobalt : focused ? SELLIA.text2 : SELLIA.border
    return {
      id: k, source: e.source, target: e.target, type: 'smoothstep',
      animated: hot,
      label: show ? e.rel : undefined,
      labelStyle: { fill: SELLIA.text2, fontSize: 9, fontFamily: SELLIA.mono },
      labelBgStyle: { fill: SELLIA.bg, fillOpacity: 0.8 },
      style: { stroke: color, strokeWidth: hot ? 1.8 : focused ? 1.1 : 0.5, opacity: focusIds && !focused ? 0.08 : hot ? 0.95 : 0.32 },
      markerEnd: { type: MarkerType.ArrowClosed, width: 14, height: 14, color },
    }
  }), [raw.edges, hotEdges, focusIds])

  // Estado controlado de React Flow + sync con los memos derivados (para que
  // los updates de estilo —dim/hot/labels— se reflejen tras el mount).
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<CatData>>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  useEffect(() => { setNodes(derivedNodes) }, [derivedNodes, setNodes])
  useEffect(() => { setEdges(derivedEdges) }, [derivedEdges, setEdges])

  const groupsPresent = useMemo(() => {
    const s = new Set<string>(); for (const n of raw.nodes) s.add(n.group)
    return [...s].sort((a, b) => (GROUP_LABEL[a] ?? a).localeCompare(GROUP_LABEL[b] ?? b))
  }, [raw.nodes])

  const onNodeEnter = useCallback((_: unknown, n: Node) => setHovered(n.id), [])
  const onNodeLeave = useCallback(() => setHovered(null), [])

  return (
    <div style={{ background: SELLIA.bg, borderRadius: 12, overflow: 'hidden', fontFamily: SELLIA.sans }}>
      {/* status + leyenda de categorías (chips de filtro) */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', borderBottom: `1px solid ${SELLIA.border}`, flexWrap: 'wrap', background: 'rgba(0,0,0,0.18)' }}>
        <span style={{ fontFamily: SELLIA.mono, fontSize: 11, fontWeight: 600, color: hotEdges.size ? SELLIA.emerald : SELLIA.text3, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 7, height: 7, borderRadius: '50%', background: hotEdges.size ? SELLIA.emerald : SELLIA.text3 }} />
          {hotEdges.size ? 'INTERACCIÓN REAL' : 'EN REPOSO'}
        </span>
        <span style={{ fontFamily: SELLIA.mono, fontSize: 11, color: SELLIA.text2 }}>{raw.nodes.length} nodos · {raw.edges.length} interacciones</span>
        <span style={{ fontFamily: SELLIA.mono, fontSize: 10, fontWeight: 600, padding: '2px 7px', borderRadius: 5, color: src === 'live' ? SELLIA.emerald : SELLIA.cobalt, background: `${src === 'live' ? SELLIA.emerald : SELLIA.cobalt}14`, border: `1px solid ${src === 'live' ? SELLIA.emerald : SELLIA.cobalt}33` }}>
          {offline ? 'OFFLINE' : src === 'live' ? 'BACKEND LIVE' : 'REGISTRY SNAPSHOT'}
        </span>
        <span style={{ flex: 1 }} />
        <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', alignItems: 'center' }}>
          {groupsPresent.map(g => {
            const on = activeGroup === g
            const c = GROUP_COLOR[g] ?? SELLIA.text2
            return (
              <button key={g} type="button" onClick={() => setActiveGroup(on ? null : g)}
                style={{ cursor: 'pointer', fontSize: 10, fontWeight: 600, fontFamily: SELLIA.sans, padding: '2px 8px', borderRadius: 100, display: 'inline-flex', alignItems: 'center', gap: 5, color: on ? SELLIA.bg : SELLIA.text2, background: on ? c : 'transparent', border: `1px solid ${c}${on ? '' : '55'}` }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: on ? SELLIA.bg : c }} />
                {GROUP_LABEL[g] ?? g}
              </button>
            )
          })}
          {activeGroup && (
            <button type="button" onClick={() => setActiveGroup(null)} style={{ cursor: 'pointer', fontSize: 10, color: SELLIA.text3, background: 'none', border: 'none', textDecoration: 'underline' }}>limpiar</button>
          )}
        </div>
      </div>

      <div style={{ height: 460, position: 'relative' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          onNodeMouseEnter={onNodeEnter}
          onNodeMouseLeave={onNodeLeave}
          fitView
          minZoom={0.2}
          maxZoom={2.5}
          proOptions={{ hideAttribution: true }}
          style={{ background: SELLIA.bg }}
        >
          <Background variant={BackgroundVariant.Dots} gap={26} size={1} color="rgba(255,255,255,0.06)" />
          <Controls showInteractive={false} />
          <MiniMap pannable zoomable nodeColor={(n) => GROUP_COLOR[(n.data as CatData)?.group] ?? SELLIA.text3} maskColor="rgba(10,15,26,0.7)" style={{ background: SELLIA.panel, border: `1px solid ${SELLIA.border}` }} />
          {/* etiquetas de columna (kind) */}
          {Object.entries(KIND_LABEL).map(([k, label]) => (
            <div key={k} style={{ position: 'absolute', top: 6, left: (LAYER_X[Number(k)] ?? 0), transform: 'translateX(0)', zIndex: 5, pointerEvents: 'none', fontFamily: SELLIA.mono, fontSize: 10, color: SELLIA.text3, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
              {label}
            </div>
          ))}
        </ReactFlow>
        {lastEvent !== '—' && (
          <div style={{ position: 'absolute', bottom: 8, left: 8, zIndex: 6, maxWidth: 380, padding: '4px 9px', borderRadius: 6, background: 'rgba(15,23,42,0.85)', border: `1px solid ${SELLIA.border}`, fontSize: 10, fontFamily: SELLIA.mono, color: SELLIA.text2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            último: {lastEvent}
          </div>
        )}
      </div>
    </div>
  )
}

export default function BrainInteractionMap(): React.JSX.Element {
  return (
    <ReactFlowProvider>
      <Inner />
    </ReactFlowProvider>
  )
}
