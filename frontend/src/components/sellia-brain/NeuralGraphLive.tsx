'use client'

/**
 * NEURAL GRAPH LIVE · sinapsis REALES
 *
 * Compact viewport con zoom/pan. Vista completa por default · zoom IN para detalle.
 * Empty state minimalista cuando offline o sin nodos.
 */

import { useCallback, useEffect, useMemo, useRef, useState, type WheelEvent, type MouseEvent } from 'react'
import { Maximize2, ZoomIn, ZoomOut, Move, WifiOff, Brain } from 'lucide-react'
import { SELLIA, KIND_COLOR, LAYER_COLOR } from '@/lib/sellia-theme'

const BRAIN_BASE = '/api/v1/brain'
const VW = 1000
const VH = 620
const VIEWPORT_H = 380              // fixed viewport in pixels
const LAYER_X: Record<number, number> = { 0: 110, 1: 400, 2: 660, 3: 910 }
const LAYER_LABEL: Record<number, string> = { 0: 'Plataformas', 1: 'Skills', 2: 'Agentes', 3: 'Automatizaciones' }
const MAX_PER_COL = 16

interface GraphNode {
  id: string; label: string; kind: string; category: string
  layer: number; health: number; tags: string[]
}
interface GraphEdge { source: string; target: string; rel: string }
interface ActivityEvent { seq: number; ts: number; kind: string; source: string; target: string | null; detail: string }

interface Positioned extends GraphNode { x: number; y: number }
interface Pulse { id: number; x1: number; y1: number; x2: number; y2: number; color: string }

const layout = (nodes: GraphNode[]): Map<string, Positioned> => {
  const byLayer = new Map<number, GraphNode[]>()
  for (const n of nodes) {
    const arr = byLayer.get(n.layer) ?? []
    arr.push(n)
    byLayer.set(n.layer, arr)
  }
  const pos = new Map<string, Positioned>()
  for (const [layer, arr] of byLayer) {
    const baseX = LAYER_X[layer] ?? 500
    const subCols = Math.max(1, Math.ceil(arr.length / MAX_PER_COL))
    const perCol = Math.ceil(arr.length / subCols)
    arr.forEach((n, i) => {
      const col = Math.floor(i / perCol)
      const row = i % perCol
      const rowsHere = Math.min(perCol, arr.length - col * perCol)
      const x = baseX + (col - (subCols - 1) / 2) * 92
      const yStep = (VH - 80) / Math.max(1, rowsHere)
      const y = 50 + yStep * (row + 0.5)
      pos.set(n.id, { ...n, x, y })
    })
  }
  return pos
}

export default function NeuralGraphLive(): React.JSX.Element {
  const [nodes, setNodes] = useState<GraphNode[]>([])
  const [edges, setEdges] = useState<GraphEdge[]>([])
  const [pulses, setPulses] = useState<Pulse[]>([])
  const [hotEdges, setHotEdges] = useState<Set<string>>(new Set())
  const [lastEvent, setLastEvent] = useState<string>('—')
  const [eventCount, setEventCount] = useState(0)
  const [offline, setOffline] = useState(false)
  const sinceSeq = useRef(0)
  const pulseId = useRef(0)
  // Base de actividad: backend live (/api/v1/brain) si responde, si no bundled (/api/brain).
  const activityBase = useRef<string>(BRAIN_BASE)
  const [graphSource, setGraphSource] = useState<'live' | 'bundled'>('live')

  // ── viewport (zoom + pan) ─────────────────────────────────────────────────
  const [scale, setScale] = useState(1)
  const [tx, setTx] = useState(0)
  const [ty, setTy] = useState(0)
  const dragRef = useRef<{ x: number; y: number; tx: number; ty: number } | null>(null)
  const [dragging, setDragging] = useState(false)

  const resetView = useCallback((): void => { setScale(1); setTx(0); setTy(0) }, [])
  const zoomIn  = useCallback((): void => setScale(s => Math.min(4,  s * 1.25)), [])
  const zoomOut = useCallback((): void => setScale(s => Math.max(0.5, s / 1.25)), [])

  const handleWheel = (e: WheelEvent<SVGSVGElement>): void => {
    e.preventDefault()
    setScale(s => {
      const next = e.deltaY < 0 ? s * 1.10 : s / 1.10
      return Math.max(0.5, Math.min(4, next))
    })
  }

  const onMouseDown = (e: MouseEvent<SVGSVGElement>): void => {
    dragRef.current = { x: e.clientX, y: e.clientY, tx, ty }
    setDragging(true)
  }
  const onMouseMove = (e: MouseEvent<SVGSVGElement>): void => {
    if (!dragRef.current) return
    const dx = e.clientX - dragRef.current.x
    const dy = e.clientY - dragRef.current.y
    setTx(dragRef.current.tx + dx)
    setTy(dragRef.current.ty + dy)
  }
  const onMouseUp = (): void => { dragRef.current = null; setDragging(false) }

  // ── carga del grafo real (una vez) ──
  // Prefiere backend FastAPI live (/api/v1/brain); si no responde, cae al snapshot
  // self-contained de Next (/api/brain) → grafo real garantizado en Vercel.
  useEffect(() => {
    const ctrl = new AbortController()
    const fetchGraph = async (base: string): Promise<{ nodes: GraphNode[]; edges: GraphEdge[] } | null> => {
      try {
        const r = await fetch(`${base}/graph`, { signal: ctrl.signal })
        if (!r.ok) return null
        return (await r.json()) as { nodes: GraphNode[]; edges: GraphEdge[] }
      } catch { return null }
    }
    const load = async (): Promise<void> => {
      let g = await fetchGraph(BRAIN_BASE)
      let base = BRAIN_BASE
      let src: 'live' | 'bundled' = 'live'
      if (!g || !(g.nodes?.length)) {
        g = await fetchGraph('/api/brain')
        base = '/api/brain'
        src = 'bundled'
      }
      if (!g || !(g.nodes?.length)) { setOffline(true); return }
      activityBase.current = base
      setGraphSource(src)
      setNodes(g.nodes ?? [])
      setEdges(g.edges ?? [])
      setOffline(false)
      try {
        const a = await fetch(`${base}/activity?limit=1`, { signal: ctrl.signal })
        if (a.ok) {
          const data = (await a.json()) as { stats?: { total?: number } }
          sinceSeq.current = data.stats?.total ?? 0
        }
      } catch { /* idle */ }
    }
    void load()
    return () => ctrl.abort()
  }, [])

  const positioned = useMemo(() => layout(nodes), [nodes])

  const edgeKey = (e: GraphEdge): string => `${e.source}__${e.target}`

  const edgesByNode = useMemo(() => {
    const m = new Map<string, GraphEdge[]>()
    for (const e of edges) {
      for (const id of [e.source, e.target]) {
        const arr = m.get(id) ?? []
        arr.push(e)
        m.set(id, arr)
      }
    }
    return m
  }, [edges])

  // ── poll de actividad REAL → dispara sinapsis ──
  useEffect(() => {
    if (!nodes.length) return
    let alive = true
    const tick = async (): Promise<void> => {
      try {
        const r = await fetch(`${activityBase.current}/activity?limit=30&since_seq=${sinceSeq.current}`)
        if (!r.ok) return
        const data = (await r.json()) as { events: ActivityEvent[] }
        const evs = data.events ?? []
        if (!alive || !evs.length) return
        sinceSeq.current = Math.max(sinceSeq.current, ...evs.map(e => e.seq))
        const newPulses: Pulse[] = []
        const newHot = new Set<string>()
        for (const ev of evs) {
          const cands = edgesByNode.get(ev.source) ?? []
          const e = cands[0]
          if (!e) continue
          const a = positioned.get(e.source)
          const b = positioned.get(e.target)
          if (!a || !b) continue
          pulseId.current += 1
          newPulses.push({ id: pulseId.current, x1: a.x, y1: a.y, x2: b.x, y2: b.y, color: KIND_COLOR[ev.kind] ?? SELLIA.cobalt })
          newHot.add(edgeKey(e))
        }
        if (newPulses.length) {
          setPulses(p => [...p, ...newPulses])
          setHotEdges(newHot)
          setEventCount(c => c + evs.length)
          setLastEvent(evs[evs.length - 1].detail)
          const ids = new Set(newPulses.map(p => p.id))
          window.setTimeout(() => {
            setPulses(p => p.filter(x => !ids.has(x.id)))
            setHotEdges(new Set())
          }, 1400)
        }
      } catch { /* idle */ }
    }
    void tick()
    const iv = window.setInterval(() => { void tick() }, 2500)
    return () => { alive = false; window.clearInterval(iv) }
  }, [nodes.length, edgesByNode, positioned])

  const hasContent = nodes.length > 0
  const isIdle     = !hasContent || offline

  return (
    <div style={{ background: SELLIA.bg, fontFamily: SELLIA.sans, borderRadius: 12, overflow: 'hidden' }}>
      {/* ── compact status bar ── */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12, padding: '10px 16px',
        borderBottom: `1px solid ${SELLIA.border}`, flexWrap: 'wrap',
        background: 'rgba(0,0,0,0.18)',
      }}>
        <span style={{
          display: 'inline-flex', alignItems: 'center', gap: 6, fontFamily: SELLIA.mono,
          fontSize: 11, fontWeight: 600, color: pulses.length ? SELLIA.emerald : SELLIA.text3,
        }}>
          <span style={{
            width: 7, height: 7, borderRadius: '50%',
            background: pulses.length ? SELLIA.emerald : SELLIA.text3,
            animation: pulses.length ? 'ng-pulse 1.2s ease-in-out infinite' : 'none',
          }} />
          {pulses.length ? 'SINAPSIS ACTIVAS' : 'EN REPOSO'}
        </span>
        <span style={{ fontFamily: SELLIA.mono, fontSize: 11, color: SELLIA.text2 }}>
          {nodes.length} nodos · {edges.length} edges · {eventCount} eventos
        </span>
        {!isIdle && (
          <span style={{
            fontFamily: SELLIA.mono, fontSize: 10, fontWeight: 600,
            padding: '2px 7px', borderRadius: 5,
            color: graphSource === 'live' ? SELLIA.emerald : SELLIA.cobalt,
            background: `${graphSource === 'live' ? SELLIA.emerald : SELLIA.cobalt}14`,
            border: `1px solid ${graphSource === 'live' ? SELLIA.emerald : SELLIA.cobalt}33`,
          }}>
            {graphSource === 'live' ? 'BACKEND LIVE' : 'REGISTRY SNAPSHOT'}
          </span>
        )}
        <span style={{ flex: 1 }} />
        {/* Layer legend */}
        {Object.entries(LAYER_LABEL).map(([k, label]) => (
          <span key={k} style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 10, color: SELLIA.text2, fontFamily: SELLIA.mono }}>
            <span style={{ width: 7, height: 7, borderRadius: '50%', background: LAYER_COLOR[Number(k)] }} />{label}
          </span>
        ))}
      </div>

      {/* ── viewport ── */}
      {isIdle ? (
        /* Empty/offline → compact card, NO empty 620px canvas */
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 14,
          padding: '28px 20px', minHeight: 120,
        }}>
          <div style={{
            width: 40, height: 40, borderRadius: 10,
            display: 'grid', placeItems: 'center',
            background: offline ? `${SELLIA.amber}14` : 'rgba(255,255,255,0.04)',
            border: `1px solid ${offline ? SELLIA.amber + '40' : SELLIA.border}`,
          }}>
            {offline
              ? <WifiOff size={18} style={{ color: SELLIA.amber }} />
              : <Brain  size={18} style={{ color: SELLIA.text3 }} />}
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: SELLIA.text, lineHeight: 1.3 }}>
              {offline ? 'Cerebro offline · reintentando…' : 'Cerebro en reposo'}
            </div>
            <div style={{ fontSize: 11, color: SELLIA.text3, fontFamily: SELLIA.mono, marginTop: 2 }}>
              {offline
                ? 'sin conexión con /api/v1/brain · polling activo'
                : 'sin nodos cargados · grafo se activará con la primera interacción real'}
            </div>
          </div>
        </div>
      ) : (
        /* Active graph viewport — compact + zoom + pan */
        <div style={{ position: 'relative', height: VIEWPORT_H, background: SELLIA.bg }}>
          {/* zoom controls overlay */}
          <div style={{
            position: 'absolute', top: 10, right: 10, zIndex: 5,
            display: 'flex', flexDirection: 'column', gap: 4,
          }}>
            {[
              { icon: <ZoomIn    size={13} />, label: 'Zoom +', onClick: zoomIn  },
              { icon: <ZoomOut   size={13} />, label: 'Zoom −', onClick: zoomOut },
              { icon: <Maximize2 size={13} />, label: 'Ajustar', onClick: resetView },
            ].map(b => (
              <button key={b.label} type="button" onClick={b.onClick} title={b.label}
                style={{
                  width: 28, height: 28, borderRadius: 6,
                  display: 'grid', placeItems: 'center',
                  background: 'rgba(15,23,42,0.85)',
                  border: `1px solid ${SELLIA.border}`,
                  color: SELLIA.text2,
                  cursor: 'pointer',
                  backdropFilter: 'blur(6px)',
                  transition: 'background .15s, color .15s',
                }}
                onMouseEnter={e => {
                  const el = e.currentTarget as HTMLButtonElement
                  el.style.background = 'rgba(30,41,59,0.95)'
                  el.style.color = SELLIA.text
                }}
                onMouseLeave={e => {
                  const el = e.currentTarget as HTMLButtonElement
                  el.style.background = 'rgba(15,23,42,0.85)'
                  el.style.color = SELLIA.text2
                }}>
                {b.icon}
              </button>
            ))}
          </div>

          {/* zoom level indicator */}
          <div style={{
            position: 'absolute', bottom: 10, left: 10, zIndex: 5,
            padding: '4px 9px', borderRadius: 6,
            background: 'rgba(15,23,42,0.85)', backdropFilter: 'blur(6px)',
            border: `1px solid ${SELLIA.border}`,
            fontSize: 10, fontFamily: SELLIA.mono, color: SELLIA.text3,
            letterSpacing: '0.05em',
            display: 'inline-flex', alignItems: 'center', gap: 6,
          }}>
            <Move size={10} />
            {Math.round(scale * 100)}% · arrastrá para mover · scroll para zoom
          </div>

          {/* last event ticker */}
          {lastEvent !== '—' && (
            <div style={{
              position: 'absolute', bottom: 10, right: 10, zIndex: 5,
              maxWidth: 360, padding: '4px 9px', borderRadius: 6,
              background: 'rgba(15,23,42,0.85)', backdropFilter: 'blur(6px)',
              border: `1px solid ${SELLIA.border}`,
              fontSize: 10, fontFamily: SELLIA.mono, color: SELLIA.text2,
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            }}>
              último: {lastEvent}
            </div>
          )}

          <svg
            viewBox={`0 0 ${VW} ${VH}`}
            preserveAspectRatio="xMidYMid meet"
            onWheel={handleWheel}
            onMouseDown={onMouseDown}
            onMouseMove={onMouseMove}
            onMouseUp={onMouseUp}
            onMouseLeave={onMouseUp}
            style={{
              width: '100%', height: '100%', display: 'block',
              cursor: dragging ? 'grabbing' : 'grab',
              userSelect: 'none',
            }}
          >
            <style>{`@keyframes ng-pulse{0%,100%{opacity:1}50%{opacity:.35}}`}</style>

            {/* arrowhead markers — rutas direccionales reales */}
            <defs>
              <marker id="ng-arrow" markerWidth="7" markerHeight="7" refX="5.5" refY="3"
                orient="auto" markerUnits="userSpaceOnUse">
                <path d="M0,0 L6,3 L0,6 Z" fill={SELLIA.text3} opacity={0.5} />
              </marker>
              <marker id="ng-arrow-hot" markerWidth="8" markerHeight="8" refX="6" refY="3.2"
                orient="auto" markerUnits="userSpaceOnUse">
                <path d="M0,0 L6.4,3.2 L0,6.4 Z" fill={SELLIA.cobalt} />
              </marker>
            </defs>

            {/* zoom + pan group */}
            <g transform={`translate(${tx} ${ty}) scale(${scale})`}>
              {/* edges — flecha source→target, recortada antes del nodo destino */}
              {edges.map(e => {
                const a = positioned.get(e.source); const b = positioned.get(e.target)
                if (!a || !b) return null
                const hot = hotEdges.has(edgeKey(e))
                const dx = b.x - a.x, dy = b.y - a.y
                const len = Math.hypot(dx, dy) || 1
                const ux = dx / len, uy = dy / len
                const ex = b.x - ux * 9, ey = b.y - uy * 9 // dejar lugar a la punta
                return (
                  <line key={edgeKey(e)} x1={a.x} y1={a.y} x2={ex} y2={ey}
                    stroke={hot ? SELLIA.cobalt : SELLIA.border}
                    strokeWidth={hot ? 1.6 : 0.6}
                    opacity={hot ? 0.9 : 0.3}
                    markerEnd={hot ? 'url(#ng-arrow-hot)' : 'url(#ng-arrow)'} />
                )
              })}

              {/* pulsos */}
              {pulses.map(p => (
                <circle key={p.id} r={4} fill={p.color}>
                  <animate attributeName="cx" from={p.x1} to={p.x2} dur="1.3s" fill="freeze" />
                  <animate attributeName="cy" from={p.y1} to={p.y2} dur="1.3s" fill="freeze" />
                  <animate attributeName="opacity" from="1" to="0" dur="1.3s" fill="freeze" />
                </circle>
              ))}

              {/* nodos */}
              {[...positioned.values()].map(n => {
                const color = KIND_COLOR[n.kind] ?? LAYER_COLOR[n.layer] ?? SELLIA.text2
                return (
                  <g key={n.id} opacity={0.45 + 0.55 * n.health}>
                    <circle cx={n.x} cy={n.y} r={5} fill={color} stroke={SELLIA.bg} strokeWidth={1}>
                      <title>{`${n.label} · ${n.category} (${n.kind})`}</title>
                    </circle>
                  </g>
                )
              })}

              {/* etiquetas de capa */}
              {Object.entries(LAYER_X).map(([k, x]) => (
                <text key={k} x={x} y={24} textAnchor="middle"
                  fill={SELLIA.text3} fontSize={11} fontFamily={SELLIA.mono}
                  style={{ textTransform: 'uppercase', letterSpacing: '0.12em' }}>
                  {LAYER_LABEL[Number(k)]}
                </text>
              ))}
            </g>
          </svg>
        </div>
      )}
    </div>
  )
}
