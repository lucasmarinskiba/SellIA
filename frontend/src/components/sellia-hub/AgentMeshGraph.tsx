'use client'

/**
 * AGENT MESH GRAPH
 *
 * Mesh circular de inter-comunicación agente-a-agente. No flujo lineal —
 * agentes envían mensajes entre sí. Diseñado como network sociogram:
 * cada nodo = agente, cada arista = canal de comunicación + freq mensajes.
 *
 * Métrica clave: cuántos mensajes/min se intercambian entre agentes.
 * Muestra que cerebro = sistema multi-agente, no chain lineal.
 */

import { useState, useEffect, useMemo } from 'react'
import {
  Brain, MessageSquare, Activity, Sparkles, Bot, Network, Hash
} from 'lucide-react'

interface MeshAgent {
  id: string
  name: string
  short: string
  emoji: string
  color: string
  cluster: 'sense' | 'think' | 'act' | 'learn'
  msgsPerMin: number
}

interface AgentLink {
  from: string
  to: string
  weight: number // 1-10 freq
}

const AGENTS: MeshAgent[] = [
  // SENSE cluster (perception/input)
  { id: 'a1', name: 'Channel-Listener', short: 'CHN',  emoji: '👂', color: '#06b6d4', cluster: 'sense',  msgsPerMin: 47 },
  { id: 'a2', name: 'Sentiment-Reader', short: 'SNT',  emoji: '😊', color: '#3b82f6', cluster: 'sense',  msgsPerMin: 23 },
  { id: 'a3', name: 'Intent-Classifier', short: 'INT', emoji: '🎯', color: '#0ea5e9', cluster: 'sense',  msgsPerMin: 34 },
  { id: 'a4', name: 'Context-Loader',   short: 'CTX',  emoji: '📚', color: '#14b8a6', cluster: 'sense',  msgsPerMin: 18 },

  // THINK cluster (reasoning/planning)
  { id: 'a5', name: 'Planner-Agent',     short: 'PLN', emoji: '🗺',  color: '#a855f7', cluster: 'think',  msgsPerMin: 28 },
  { id: 'a6', name: 'Strategist-Agent',   short: 'STR', emoji: '🎲', color: '#8b5cf6', cluster: 'think',  msgsPerMin: 19 },
  { id: 'a7', name: 'Offer-Designer',    short: 'OFR', emoji: '💎', color: '#d946ef', cluster: 'think',  msgsPerMin: 22 },
  { id: 'a8', name: 'Pricing-Optimizer', short: 'PRC', emoji: '💰', color: '#a78bfa', cluster: 'think',  msgsPerMin: 31 },
  { id: 'a9', name: 'Risk-Assessor',     short: 'RSK', emoji: '⚖️', color: '#7c3aed', cluster: 'think',  msgsPerMin: 14 },

  // ACT cluster (Computer Use execution)
  { id: 'a10', name: 'Browser-Bot',     short: 'BRW', emoji: '🌐', color: '#fbbf24', cluster: 'act',     msgsPerMin: 67 },
  { id: 'a11', name: 'Mobile-Bot',      short: 'MOB', emoji: '📱', color: '#f59e0b', cluster: 'act',     msgsPerMin: 23 },
  { id: 'a12', name: 'Form-Filler',     short: 'FRM', emoji: '📝', color: '#f97316', cluster: 'act',     msgsPerMin: 41 },
  { id: 'a13', name: 'Payment-Bot',     short: 'PAY', emoji: '💳', color: '#84cc16', cluster: 'act',     msgsPerMin: 12 },
  { id: 'a14', name: 'Messenger-Bot',   short: 'MSG', emoji: '💬', color: '#10b981', cluster: 'act',     msgsPerMin: 89 },
  { id: 'a15', name: 'Calendar-Bot',    short: 'CAL', emoji: '📅', color: '#22c55e', cluster: 'act',     msgsPerMin: 8 },

  // LEARN cluster (feedback/improvement)
  { id: 'a16', name: 'Outcome-Tracker', short: 'OUT', emoji: '📊', color: '#ef4444', cluster: 'learn',  msgsPerMin: 31 },
  { id: 'a17', name: 'Failure-Analyzer',short: 'FAI', emoji: '🔍', color: '#dc2626', cluster: 'learn',  msgsPerMin: 9 },
  { id: 'a18', name: 'Skill-Builder',   short: 'SKL', emoji: '🧬', color: '#f43f5e', cluster: 'learn',  msgsPerMin: 4 },
  { id: 'a19', name: 'Memory-Curator',  short: 'MEM', emoji: '🧠', color: '#e11d48', cluster: 'learn',  msgsPerMin: 16 },
]

// Hand-picked high-traffic edges (mesh topology, not strict layers)
const LINKS: AgentLink[] = [
  // Sense → Think
  { from: 'a1',  to: 'a5',  weight: 9 },
  { from: 'a1',  to: 'a3',  weight: 8 },
  { from: 'a2',  to: 'a6',  weight: 6 },
  { from: 'a3',  to: 'a5',  weight: 9 },
  { from: 'a3',  to: 'a7',  weight: 7 },
  { from: 'a4',  to: 'a5',  weight: 7 },
  { from: 'a4',  to: 'a8',  weight: 5 },

  // Think internal (heavy chatter)
  { from: 'a5',  to: 'a6',  weight: 8 },
  { from: 'a5',  to: 'a7',  weight: 9 },
  { from: 'a5',  to: 'a8',  weight: 7 },
  { from: 'a6',  to: 'a7',  weight: 6 },
  { from: 'a7',  to: 'a8',  weight: 8 },
  { from: 'a8',  to: 'a9',  weight: 5 },
  { from: 'a9',  to: 'a5',  weight: 4 },

  // Think → Act
  { from: 'a5',  to: 'a10', weight: 9 },
  { from: 'a5',  to: 'a14', weight: 10 },
  { from: 'a6',  to: 'a14', weight: 9 },
  { from: 'a7',  to: 'a10', weight: 7 },
  { from: 'a7',  to: 'a12', weight: 6 },
  { from: 'a8',  to: 'a13', weight: 5 },
  { from: 'a8',  to: 'a12', weight: 7 },

  // Act internal (bots coordinate)
  { from: 'a10', to: 'a12', weight: 8 },
  { from: 'a10', to: 'a14', weight: 9 },
  { from: 'a11', to: 'a14', weight: 6 },
  { from: 'a12', to: 'a13', weight: 7 },
  { from: 'a14', to: 'a15', weight: 5 },
  { from: 'a13', to: 'a15', weight: 4 },

  // Act → Learn
  { from: 'a10', to: 'a16', weight: 8 },
  { from: 'a13', to: 'a16', weight: 6 },
  { from: 'a14', to: 'a16', weight: 9 },
  { from: 'a16', to: 'a17', weight: 7 },

  // Learn internal + back to Think (feedback loop)
  { from: 'a17', to: 'a18', weight: 5 },
  { from: 'a18', to: 'a19', weight: 4 },
  { from: 'a19', to: 'a5',  weight: 7 },
  { from: 'a19', to: 'a6',  weight: 5 },
  { from: 'a16', to: 'a8',  weight: 8 }, // outcome → repricing
  { from: 'a17', to: 'a9',  weight: 6 }, // failure → risk update

  // Cross-cluster shortcuts
  { from: 'a1',  to: 'a14', weight: 7 },
  { from: 'a4',  to: 'a19', weight: 6 },
  { from: 'a15', to: 'a16', weight: 4 },
]

const CLUSTER_CONFIG = {
  sense: { label: 'SENSE',  color: '#06b6d4', angleStart:  -90, angleEnd:    0 },
  think: { label: 'THINK',  color: '#a855f7', angleStart:    0, angleEnd:   90 },
  act:   { label: 'ACT',    color: '#fbbf24', angleStart:   90, angleEnd:  180 },
  learn: { label: 'LEARN',  color: '#ef4444', angleStart:  180, angleEnd:  270 },
} as const

export default function AgentMeshGraph() {
  const [tick, setTick] = useState(0)
  const [hoveredAgent, setHoveredAgent] = useState<string | null>(null)
  const [selectedLink, setSelectedLink] = useState<string | null>(null)

  useEffect(() => {
    const id = setInterval(() => setTick(t => (t + 1) % 1000), 60)
    return () => clearInterval(id)
  }, [])

  // Compute node positions: circular layout grouped by cluster
  const positions = useMemo(() => {
    const map: Record<string, { x: number; y: number }> = {}
    const clusterCounts: Record<string, number> = {}
    for (const a of AGENTS) clusterCounts[a.cluster] = (clusterCounts[a.cluster] || 0) + 1

    const clusterIndex: Record<string, number> = { sense: 0, think: 0, act: 0, learn: 0 }
    const R = 38 // radius % of viewBox
    const cx = 50, cy = 50

    for (const a of AGENTS) {
      const c = CLUSTER_CONFIG[a.cluster]
      const idx = clusterIndex[a.cluster]++
      const span = c.angleEnd - c.angleStart
      const angle = (c.angleStart + (span / (clusterCounts[a.cluster] + 1)) * (idx + 1)) * Math.PI / 180
      map[a.id] = { x: cx + Math.cos(angle) * R, y: cy + Math.sin(angle) * R }
    }
    return map
  }, [])

  const totalMsgsPerMin = useMemo(() => AGENTS.reduce((s, a) => s + a.msgsPerMin, 0), [])
  const topChatty = useMemo(() => [...AGENTS].sort((a, b) => b.msgsPerMin - a.msgsPerMin).slice(0, 3), [])

  const W = 700
  const H = 700

  const hoveredData = hoveredAgent ? AGENTS.find(a => a.id === hoveredAgent) : null

  return (
    <section className="relative rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-[#081a14]/85 via-[#0a0e1a]/90 to-[#0a0e1a]/95 backdrop-blur overflow-hidden">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-400/80 to-transparent" />

      {/* Header */}
      <div className="px-5 py-4 border-b border-white/[0.06] flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/25 to-cyan-500/15 border border-emerald-500/40 flex items-center justify-center">
            <Network className="w-5 h-5 text-emerald-400" style={{ filter: 'drop-shadow(0 0 8px rgba(16,185,129,0.7))' }} />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 flex-wrap">
              <span className="bg-gradient-to-r from-emerald-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">AGENT MESH GRAPH</span>
              <span className="text-white/40 font-light normal-case tracking-normal">·  {AGENTS.length} agentes · {LINKS.length} canales bi-direccional</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-mono uppercase tracking-widest">
                ● {totalMsgsPerMin} msg/min
              </span>
            </h2>
            <p className="text-[11px] text-white/40 mt-0.5">Agentes hablan entre sí (no chain lineal) · SENSE → THINK → ACT → LEARN → feedback loop</p>
          </div>
        </div>
      </div>

      {/* Cluster legend */}
      <div className="px-5 py-2 border-b border-white/[0.06] flex items-center gap-3 flex-wrap text-[10px]">
        {(Object.keys(CLUSTER_CONFIG) as (keyof typeof CLUSTER_CONFIG)[]).map(k => {
          const c = CLUSTER_CONFIG[k]
          const count = AGENTS.filter(a => a.cluster === k).length
          return (
            <div key={k} className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full" style={{ background: c.color }} />
              <span className="font-mono uppercase tracking-widest font-bold" style={{ color: c.color }}>{c.label}</span>
              <span className="text-white/40">· {count} agentes</span>
            </div>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 p-4">
        {/* SVG mesh */}
        <div className="lg:col-span-2 relative rounded-xl bg-black/30 border border-emerald-500/15 overflow-hidden" style={{ aspectRatio: '1 / 1' }}>
          {/* Background concentric rings */}
          <svg viewBox={`0 0 ${W} ${H}`} className="absolute inset-0 w-full h-full">
            <defs>
              <radialGradient id="meshBg" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="rgba(16,185,129,0.05)" />
                <stop offset="100%" stopColor="transparent" />
              </radialGradient>
            </defs>
            <circle cx={W / 2} cy={H / 2} r="200" fill="url(#meshBg)" />
            <circle cx={W / 2} cy={H / 2} r="200" fill="none" stroke="rgba(16,185,129,0.06)" />
            <circle cx={W / 2} cy={H / 2} r="120" fill="none" stroke="rgba(16,185,129,0.06)" />
            <circle cx={W / 2} cy={H / 2} r="60"  fill="none" stroke="rgba(16,185,129,0.06)" />

            {/* Center brain */}
            <circle cx={W / 2} cy={H / 2} r="14" fill="rgba(168,85,247,0.2)" stroke="#a855f7" strokeWidth="1" />
            <text x={W / 2} y={H / 2 + 4} textAnchor="middle" fontSize="14">🧠</text>

            {/* Edges */}
            {LINKS.map((link, i) => {
              const fromPos = positions[link.from]
              const toPos = positions[link.to]
              if (!fromPos || !toPos) return null
              const x1 = (fromPos.x / 100) * W
              const y1 = (fromPos.y / 100) * H
              const x2 = (toPos.x / 100) * W
              const y2 = (toPos.y / 100) * H
              const linkId = `${link.from}-${link.to}`
              const isHover = selectedLink === linkId || (hoveredAgent && (link.from === hoveredAgent || link.to === hoveredAgent))
              const opacity = isHover ? 0.9 : Math.min(0.08 + link.weight * 0.04, 0.45)
              return (
                <line
                  key={i}
                  x1={x1} y1={y1} x2={x2} y2={y2}
                  stroke={isHover ? '#10b981' : 'rgba(16,185,129,0.6)'}
                  strokeWidth={isHover ? 1.6 : Math.min(0.4 + link.weight * 0.12, 1.4)}
                  strokeOpacity={opacity}
                  onMouseEnter={() => setSelectedLink(linkId)}
                  onMouseLeave={() => setSelectedLink(null)}
                  style={{ cursor: 'pointer', transition: 'all 200ms' }}
                />
              )
            })}

            {/* Animated message packets (deterministic, phase by link.weight + tick) */}
            {LINKS.filter(l => l.weight >= 7).slice(0, 8).map((link, i) => {
              const fromPos = positions[link.from]
              const toPos = positions[link.to]
              if (!fromPos || !toPos) return null
              const phase = ((tick * 1.5 + i * 12) % 100) / 100
              const x = (fromPos.x + (toPos.x - fromPos.x) * phase) / 100 * W
              const y = (fromPos.y + (toPos.y - fromPos.y) * phase) / 100 * H
              return (
                <g key={`p-${i}`}>
                  <circle cx={x} cy={y} r="4" fill="#34d399" opacity="0.4" />
                  <circle cx={x} cy={y} r="2" fill="#fff" />
                </g>
              )
            })}

            {/* Nodes */}
            {AGENTS.map(a => {
              const pos = positions[a.id]
              if (!pos) return null
              const x = (pos.x / 100) * W
              const y = (pos.y / 100) * H
              const isHover = hoveredAgent === a.id
              const r = isHover ? 18 : 14
              return (
                <g
                  key={a.id}
                  onMouseEnter={() => setHoveredAgent(a.id)}
                  onMouseLeave={() => setHoveredAgent(null)}
                  style={{ cursor: 'pointer' }}
                >
                  {isHover && (
                    <circle cx={x} cy={y} r={r + 8} fill="none" stroke={a.color} strokeOpacity="0.5" strokeWidth="1" strokeDasharray="3 3" />
                  )}
                  <circle cx={x} cy={y} r={r} fill={`${a.color}20`} stroke={a.color} strokeWidth={isHover ? 2 : 1} />
                  <text x={x} y={y + 4} textAnchor="middle" fontSize="12">{a.emoji}</text>
                  <text x={x} y={y + r + 9} textAnchor="middle" fontSize="7" fill={isHover ? a.color : 'rgba(255,255,255,0.4)'} fontFamily="monospace" fontWeight="bold">
                    {a.short}
                  </text>
                </g>
              )
            })}
          </svg>

          {/* Hover info */}
          {hoveredData && (
            <div className="absolute bottom-2 left-2 right-2 sm:right-auto sm:max-w-xs rounded-xl bg-black/85 border backdrop-blur p-3 pointer-events-none"
              style={{ borderColor: `${hoveredData.color}40` }}>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-2xl">{hoveredData.emoji}</span>
                <div>
                  <p className="text-xs font-bold text-white">{hoveredData.name}</p>
                  <p className="text-[9px] uppercase tracking-widest" style={{ color: hoveredData.color }}>
                    {hoveredData.cluster} cluster
                  </p>
                </div>
              </div>
              <p className="text-[10px] text-white/60 font-mono mt-1">
                {hoveredData.msgsPerMin} msg/min · {LINKS.filter(l => l.from === hoveredData.id || l.to === hoveredData.id).length} canales
              </p>
            </div>
          )}

          {/* Cluster labels overlaid */}
          <div className="absolute top-3 right-3 flex flex-col gap-1 text-[9px] font-mono uppercase tracking-widest">
            {(Object.keys(CLUSTER_CONFIG) as (keyof typeof CLUSTER_CONFIG)[]).map(k => (
              <span key={k} style={{ color: CLUSTER_CONFIG[k].color }}>{CLUSTER_CONFIG[k].label}</span>
            ))}
          </div>
        </div>

        {/* Side panel · stats + top chatty */}
        <div className="space-y-3">
          {/* Total flux */}
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/[0.05] p-4">
            <p className="text-[9px] uppercase tracking-widest text-emerald-400 font-bold mb-2 flex items-center gap-1">
              <Activity className="w-2.5 h-2.5" /> FLUJO TOTAL
            </p>
            <p className="text-3xl font-black text-white tabular-nums">{totalMsgsPerMin}</p>
            <p className="text-[10px] text-white/50 mt-0.5">mensajes inter-agente / minuto</p>
            <div className="h-1 bg-white/5 rounded-full mt-2 overflow-hidden">
              <div className="h-full bg-gradient-to-r from-emerald-500 to-cyan-400 rounded-full animate-pulse" style={{ width: '78%' }} />
            </div>
          </div>

          {/* Top chatty agents */}
          <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
            <p className="text-[9px] uppercase tracking-widest text-white/40 font-bold mb-2 flex items-center gap-1">
              <MessageSquare className="w-2.5 h-2.5" /> TOP COMUNICADORES
            </p>
            <div className="space-y-2">
              {topChatty.map((a, i) => (
                <div key={a.id} className="flex items-center gap-2">
                  <span className="text-[9px] font-mono font-bold text-white/30 w-3">{i + 1}</span>
                  <span className="text-lg">{a.emoji}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-[11px] font-semibold text-white truncate">{a.name}</p>
                    <p className="text-[9px]" style={{ color: a.color }}>{a.msgsPerMin} msg/min</p>
                  </div>
                  <div className="w-12 h-1 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${(a.msgsPerMin / topChatty[0].msgsPerMin) * 100}%`, background: a.color }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Cluster breakdown */}
          <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
            <p className="text-[9px] uppercase tracking-widest text-white/40 font-bold mb-2 flex items-center gap-1">
              <Hash className="w-2.5 h-2.5" /> CARGAS POR CLUSTER
            </p>
            <div className="space-y-1.5">
              {(Object.keys(CLUSTER_CONFIG) as (keyof typeof CLUSTER_CONFIG)[]).map(k => {
                const c = CLUSTER_CONFIG[k]
                const sum = AGENTS.filter(a => a.cluster === k).reduce((s, a) => s + a.msgsPerMin, 0)
                const pct = Math.round((sum / totalMsgsPerMin) * 100)
                return (
                  <div key={k}>
                    <div className="flex items-center justify-between text-[10px] mb-0.5">
                      <span className="font-mono font-bold" style={{ color: c.color }}>{c.label}</span>
                      <span className="text-white/60 tabular-nums">{sum} ({pct}%)</span>
                    </div>
                    <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${pct}%`, background: c.color, opacity: 0.7 }} />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Footer call to action */}
          <div className="rounded-xl border border-purple-500/20 bg-gradient-to-br from-purple-500/[0.06] to-transparent p-3">
            <div className="flex items-center gap-2 text-[10px]">
              <Bot className="w-3 h-3 text-purple-400 shrink-0" />
              <span className="text-white/70">
                Feedback loop activo: cada outcome retroalimenta <span className="text-purple-300 font-bold">Skill-Builder</span> que crea skills nuevos.
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
