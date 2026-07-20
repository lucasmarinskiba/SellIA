'use client'

/**
 * UNIFIED BRAIN CORE
 *
 * Singularidad. UN cerebro con N brazos.
 * Visualiza el sistema como entidad única, no colección de módulos:
 *   - Mandala central rotativo (rings concéntricos = subsistemas)
 *   - 4 cuadrantes: razonamiento · memoria · conocimiento · IQ
 *   - Live chain-of-thought ticker
 *   - Mapa unificado de TODOS los componentes con data-flow
 */

import { useState, useEffect, useMemo } from 'react'
import {
  Brain, Sparkles, Activity, Cpu, Database, Network, Eye,
  Zap, Layers, GitBranch, Gauge, Atom, ArrowRight, Bot
} from 'lucide-react'

interface ReasoningEngine {
  id: string
  emoji: string
  name: string
  acronym: string
  description: string
  utilization: number // 0-100
  color: string
}

interface MemoryLayer {
  id: string
  emoji: string
  name: string
  scope: string
  size: string
  color: string
}

interface ThoughtFrame {
  obs: string
  hyp: string
  dec: string
  act: string
  technique: string
  ms: number
}

const REASONING_ENGINES: ReasoningEngine[] = [
  { id: 'cot',  emoji: '🔗', name: 'Chain-of-Thought',     acronym: 'CoT',  description: 'Razonamiento paso-a-paso explicado',           utilization: 87, color: '#a855f7' },
  { id: 'tot',  emoji: '🌳', name: 'Tree-of-Thought',      acronym: 'ToT',  description: 'Múltiples ramas exploradas en paralelo · pick best', utilization: 62, color: '#06b6d4' },
  { id: 'react',emoji: '⚡', name: 'ReAct',                acronym: 'ReA',  description: 'Razonar + Actuar alternado · tool-use loop',   utilization: 94, color: '#fbbf24' },
  { id: 'refl', emoji: '🪞', name: 'Reflection / Critique',acronym: 'REF',  description: 'Auto-crítica + iteración hasta converger',     utilization: 71, color: '#ec4899' },
  { id: 'causal',emoji: '🎯', name: 'Causal Inference',     acronym: 'CSI',  description: 'X causó Y · counterfactuals · do-calculus',   utilization: 58, color: '#22c55e' },
  { id: 'bayes',emoji: '📊', name: 'Bayesian Update',      acronym: 'BAY',  description: 'Beliefs actualizan con nueva evidencia',       utilization: 78, color: '#3b82f6' },
  { id: 'ana',  emoji: '🔄', name: 'Analogical Reasoning', acronym: 'ANA',  description: 'Mapea problema actual a uno ya resuelto',      utilization: 65, color: '#f59e0b' },
  { id: 'tom',  emoji: '🧠', name: 'Theory of Mind',       acronym: 'ToM',  description: 'Modela mente del cliente · qué siente/piensa',  utilization: 82, color: '#dc2626' },
]

const MEMORY_LAYERS: MemoryLayer[] = [
  { id: 'work',     emoji: '⚡', name: 'Working memory',      scope: 'Sesión actual',    size: '128k tokens · 47 contextos', color: '#fbbf24' },
  { id: 'short',    emoji: '📌', name: 'Short-term',          scope: 'Últimas 24h',      size: '4.2M tokens · 1,847 events', color: '#ec4899' },
  { id: 'long',     emoji: '🗄', name: 'Long-term knowledge', scope: 'Todo histórico',   size: '847M tokens · vector DB',    color: '#a855f7' },
  { id: 'episodic', emoji: '🎬', name: 'Episodic',            scope: 'Casos exitosos',   size: '12,478 deals cerrados',      color: '#22c55e' },
  { id: 'semantic', emoji: '📚', name: 'Semantic · conceptos',scope: 'Permanente',       size: '142 skills · 36 legends',    color: '#06b6d4' },
  { id: 'proc',     emoji: '🔧', name: 'Procedural · how-to', scope: 'Playbooks',        size: '58 verticales · 89 flows',   color: '#10b981' },
]

const THOUGHT_FRAMES: ThoughtFrame[] = [
  { obs: 'Juan abandonó carrito $1.2k tras ver precio',          hyp: 'Sticker shock · necesita prueba de ROI',            dec: 'Enviar caso éxito + bonus 48h',                              act: 'Escribiendo WA · storytelling de caso real',           technique: 'CoT + Bayesian',   ms: 187 },
  { obs: 'María vio reel 3 veces sin DM',                        hyp: 'Interés alto · falta CTA explícito',                dec: 'Comentar en reel + DM con pregunta abierta',                 act: 'IG comment + DM con pregunta abierta calibrada',       technique: 'ToM + ReAct',      ms: 142 },
  { obs: 'Competidor bajó precio 12% en Amazon',                 hyp: 'Inventario nuevo · necesita liquidar rápido',       dec: 'NO bajar precio · vender en valor + bundle',                  act: 'Bundle accesorios · precio firme · upgrade premium',   technique: 'Causal + Tree',    ms: 234 },
  { obs: 'Stock Nike 42 baja a 2 unidades',                      hyp: 'Auto-reorder no se disparó · supplier slow',        dec: 'Disparar reorder ahora + reservar lead time backup',         act: 'AFIP factura compra + email supplier',                 technique: 'Reflection',       ms: 167 },
  { obs: 'Mariana NPS 9 · compró Premium',                       hyp: 'Candidata embajador · pedirle testimonio',          dec: 'Ofrecer comisión 20% por referido + video',                  act: 'WA con CTA de referidos · programa embajadores',       technique: 'Analogical',       ms: 198 },
  { obs: 'LinkedIn DM "estoy explorando opciones"',              hyp: 'Está comparando · necesita diferencial claro',      dec: 'Diagnóstico gratis + battlecard vs competidor #2',           act: 'Calendly link + PDF battlecard',                       technique: 'CoT + ToT',        ms: 156 },
]

const SYSTEM_NODES = [
  { id: 'omni',  emoji: '🌌', label: 'Omnipresent UI',     color: '#a855f7', kind: 'surface' as const },
  { id: 'voice', emoji: '🎙', label: 'Voice (12 lang)',   color: '#06b6d4', kind: 'surface' as const },
  { id: 'ext',   emoji: '🧩', label: 'Extensions × 8',    color: '#3b82f6', kind: 'surface' as const },
  { id: 'cua',   emoji: '🤖', label: 'Computer Use × 6',  color: '#fbbf24', kind: 'execution' as const },
  { id: 'mesh',  emoji: '🕸',  label: 'Agent Mesh × 19',   color: '#10b981', kind: 'reasoning' as const },
  { id: 'sl',    emoji: '🏆', label: 'Sales Legends × 36', color: '#dc2626', kind: 'knowledge' as const },
  { id: 'mm',    emoji: '👑', label: 'MasterMind × 28',    color: '#fbbf24', kind: 'knowledge' as const },
  { id: 'sk',    emoji: '🛠', label: 'Skills × 142',        color: '#ec4899', kind: 'knowledge' as const },
  { id: 'vert',  emoji: '🏢', label: 'Verticals × 58',     color: '#14b8a6', kind: 'knowledge' as const },
]

const KIND_COLOR = {
  surface:   '#a855f7',
  execution: '#fbbf24',
  reasoning: '#10b981',
  knowledge: '#ec4899',
} as const

export default function UnifiedBrainCore() {
  const [rot, setRot] = useState(0)
  const [thoughtIdx, setThoughtIdx] = useState(0)
  const [pulse, setPulse] = useState(0)

  useEffect(() => {
    const id = setInterval(() => setRot(r => (r + 0.4) % 360), 50)
    return () => clearInterval(id)
  }, [])
  useEffect(() => {
    const id = setInterval(() => setPulse(p => (p + 1) % 100), 80)
    return () => clearInterval(id)
  }, [])
  useEffect(() => {
    const id = setInterval(() => setThoughtIdx(i => (i + 1) % THOUGHT_FRAMES.length), 4200)
    return () => clearInterval(id)
  }, [])

  const stats = useMemo(() => {
    const decisionsPerSec = 23
    const avgLatency = 187
    const accuracy = 87
    const reasoningEnginesActive = REASONING_ENGINES.filter(e => e.utilization > 50).length
    return { decisionsPerSec, avgLatency, accuracy, reasoningEnginesActive }
  }, [])

  const thought = THOUGHT_FRAMES[thoughtIdx]

  return (
    <section className="relative rounded-2xl border border-purple-500/30 bg-gradient-to-br from-[#08081a]/95 via-[#0a0e1a]/93 to-[#08081a]/95 backdrop-blur overflow-hidden">
      {/* Multi-color edges suggesting "everything converges here" */}
      <div className="absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-cyan-400 via-purple-400 via-pink-400 via-amber-400 to-emerald-400" />
      <div className="absolute inset-x-0 bottom-0 h-[2px] bg-gradient-to-r from-emerald-400 via-amber-400 via-pink-400 via-purple-400 to-cyan-400" />

      {/* Background quantum dots */}
      <div className="absolute inset-0 pointer-events-none opacity-30 overflow-hidden">
        {[15, 32, 48, 67, 81, 92].map((x, i) => (
          <div key={i} className="absolute w-1 h-1 rounded-full animate-pulse"
            style={{
              left: `${x}%`,
              top: `${(i * 17 + 20) % 80}%`,
              background: ['#a855f7', '#06b6d4', '#fbbf24', '#ec4899', '#22c55e', '#3b82f6'][i],
              boxShadow: `0 0 8px ${['#a855f7', '#06b6d4', '#fbbf24', '#ec4899', '#22c55e', '#3b82f6'][i]}`,
              animationDuration: `${2 + i * 0.4}s`,
            }}
          />
        ))}
      </div>

      {/* Header */}
      <div className="relative px-5 py-5 border-b border-white/[0.06]">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className="relative w-12 h-12">
              <div className="absolute inset-0 rounded-full bg-gradient-to-br from-purple-500 via-cyan-500 to-pink-500"
                style={{ transform: `scale(${1 + Math.sin(pulse * 0.1) * 0.05})`, boxShadow: '0 0 40px rgba(168,85,247,0.7)' }} />
              <div className="absolute inset-2 rounded-full bg-[#08081a] flex items-center justify-center">
                <Atom className="w-5 h-5 text-purple-300" style={{ filter: 'drop-shadow(0 0 12px rgba(168,85,247,1))', animation: 'spin 8s linear infinite' }} />
              </div>
            </div>
            <div>
              <h2 className="text-base font-black tracking-tight">
                <span className="bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text text-transparent uppercase tracking-widest">SISTEMA UNIFICADO</span>
                <span className="text-white/70 ml-2 text-xs font-light">· One brain, many arms</span>
              </h2>
              <p className="text-[11px] text-white/40 mt-0.5">
                {SYSTEM_NODES.length} subsistemas convergen en una sola entidad · razona · recuerda · ejecuta · aprende
              </p>
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Stat label="Decisiones/s" value={stats.decisionsPerSec} color="#a855f7" />
            <Stat label="Latencia" value={`${stats.avgLatency}ms`} color="#06b6d4" />
            <Stat label="Acierto" value={`${stats.accuracy}%`} color="#22c55e" />
            <Stat label="Engines on" value={`${stats.reasoningEnginesActive}/${REASONING_ENGINES.length}`} color="#ec4899" />
          </div>
        </div>

        {/* Live chain of thought */}
        <div className="mt-4 rounded-xl p-3 bg-gradient-to-r from-purple-500/[0.08] to-cyan-500/[0.08] border border-purple-500/25">
          <div className="flex items-center gap-2 mb-2">
            <Brain className="w-3.5 h-3.5 text-purple-300 animate-pulse" />
            <span className="text-[10px] uppercase tracking-widest font-bold text-purple-300">PENSAMIENTO EN VIVO</span>
            <span className="ml-auto text-[10px] text-white/40 font-mono">{thought.technique} · {thought.ms}ms</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-2 text-[11px]">
            <ThoughtStep label="OBSERVA" text={thought.obs} color="#06b6d4" />
            <ThoughtStep label="HIPÓTESIS" text={thought.hyp} color="#fbbf24" />
            <ThoughtStep label="DECIDE" text={thought.dec} color="#a855f7" />
            <ThoughtStep label="ACTÚA" text={thought.act} color="#22c55e" />
          </div>
        </div>
      </div>

      {/* Body grid: mandala + 3 panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 p-5">
        {/* MANDALA · central brain visualization */}
        <div className="relative rounded-xl bg-black/40 border border-purple-500/15 overflow-hidden aspect-square flex items-center justify-center">
          <svg viewBox="0 0 400 400" className="absolute inset-0 w-full h-full">
            <defs>
              <radialGradient id="coreGrad" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#a855f7" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#a855f7" stopOpacity="0" />
              </radialGradient>
            </defs>
            {/* Rings concentric · 6 layers · counter-rotating */}
            {[180, 150, 120, 90, 60, 30].map((r, i) => {
              const dashCount = 16 + i * 4
              const dashLen = (2 * Math.PI * r) / dashCount / 2
              const direction = i % 2 === 0 ? 1 : -1
              const color = ['#a855f7', '#06b6d4', '#fbbf24', '#ec4899', '#22c55e', '#3b82f6'][i]
              return (
                <g key={i} style={{ transform: `rotate(${rot * direction * (1 + i * 0.3)}deg)`, transformOrigin: '200px 200px' }}>
                  <circle cx="200" cy="200" r={r} fill="none" stroke={color} strokeOpacity="0.3" strokeWidth="1.5" strokeDasharray={`${dashLen} ${dashLen}`} />
                </g>
              )
            })}
            {/* Core glow */}
            <circle cx="200" cy="200" r="40" fill="url(#coreGrad)" />
            <circle cx="200" cy="200" r="14" fill="rgba(168,85,247,0.4)" stroke="#a855f7" strokeWidth="1.5" />
            <text x="200" y="208" textAnchor="middle" fontSize="22">🧠</text>

            {/* Orbiting subsystem nodes (counter-rotating positions on rings) */}
            {SYSTEM_NODES.map((n, i) => {
              const ringRadius = 60 + (i % 4) * 38
              const angle = (rot * (i % 2 === 0 ? 1 : -1) * 0.5 + i * 360 / SYSTEM_NODES.length) * Math.PI / 180
              const x = 200 + Math.cos(angle) * ringRadius
              const y = 200 + Math.sin(angle) * ringRadius
              return (
                <g key={n.id}>
                  <line x1="200" y1="200" x2={x} y2={y} stroke={n.color} strokeOpacity="0.25" strokeWidth="0.8" />
                  <circle cx={x} cy={y} r="10" fill={`${n.color}25`} stroke={n.color} strokeWidth="1.2" />
                  <text x={x} y={y + 4} textAnchor="middle" fontSize="11">{n.emoji}</text>
                </g>
              )
            })}
          </svg>
          {/* Caption */}
          <div className="absolute bottom-3 left-3 right-3 text-center">
            <p className="text-[9px] uppercase tracking-widest text-purple-300 font-bold">CORE SINGULARITY</p>
            <p className="text-[10px] text-white/40 mt-0.5">9 subsistemas orbitando · sincronizados a 50Hz</p>
          </div>
        </div>

        {/* REASONING ENGINES panel */}
        <div className="rounded-xl bg-white/[0.02] border border-purple-500/15 p-4">
          <div className="flex items-center gap-2 mb-3">
            <GitBranch className="w-4 h-4 text-purple-400" />
            <h3 className="text-[11px] uppercase tracking-widest font-bold text-purple-300">RAZONAMIENTO · {REASONING_ENGINES.length} ENGINES</h3>
          </div>
          <div className="space-y-2 max-h-[360px] overflow-y-auto pr-1">
            {REASONING_ENGINES.map(e => (
              <div key={e.id} className="rounded-lg p-2.5 bg-white/[0.02] border border-white/[0.04]">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg shrink-0">{e.emoji}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-[11px] font-bold text-white truncate">{e.name}</p>
                      <span className="text-[8px] px-1 py-0.5 rounded font-mono font-bold shrink-0" style={{ background: `${e.color}20`, color: e.color }}>
                        {e.acronym}
                      </span>
                    </div>
                  </div>
                  <span className="text-xs font-black tabular-nums shrink-0" style={{ color: e.color }}>{e.utilization}%</span>
                </div>
                <p className="text-[10px] text-white/50 leading-snug mb-1.5">{e.description}</p>
                <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all" style={{ width: `${e.utilization}%`, background: e.color, boxShadow: `0 0 6px ${e.color}` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* MEMORY + KNOWLEDGE panel */}
        <div className="space-y-3">
          {/* Memory layers */}
          <div className="rounded-xl bg-white/[0.02] border border-cyan-500/15 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Database className="w-4 h-4 text-cyan-400" />
              <h3 className="text-[11px] uppercase tracking-widest font-bold text-cyan-300">MEMORIA · {MEMORY_LAYERS.length} CAPAS</h3>
            </div>
            <div className="space-y-1.5">
              {MEMORY_LAYERS.map(m => (
                <div key={m.id} className="flex items-center gap-2 p-2 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                  <span className="text-lg shrink-0">{m.emoji}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-[11px] font-bold text-white truncate">{m.name}</p>
                    <p className="text-[9px] truncate" style={{ color: m.color }}>{m.scope} · {m.size}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Live IQ gauge */}
          <div className="rounded-xl bg-gradient-to-br from-emerald-500/[0.08] to-transparent border border-emerald-500/20 p-4">
            <div className="flex items-center gap-2 mb-2">
              <Gauge className="w-4 h-4 text-emerald-400" />
              <h3 className="text-[11px] uppercase tracking-widest font-bold text-emerald-400">IQ COMPUESTO</h3>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <p className="text-2xl font-black text-emerald-400 tabular-nums">142</p>
                <p className="text-[9px] text-white/40 uppercase tracking-widest">Composite IQ</p>
              </div>
              <div>
                <p className="text-2xl font-black text-purple-400 tabular-nums">↗18%</p>
                <p className="text-[9px] text-white/40 uppercase tracking-widest">Learning rate</p>
              </div>
              <div>
                <p className="text-2xl font-black text-amber-400 tabular-nums">3.4k</p>
                <p className="text-[9px] text-white/40 uppercase tracking-widest">Inferencias/h</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Unified system map */}
      <div className="px-5 pb-5">
        <div className="flex items-center gap-2 mb-3">
          <Network className="w-4 h-4 text-pink-400" />
          <h3 className="text-[11px] uppercase tracking-widest font-bold text-pink-400">MAPA DEL SISTEMA UNIFICADO</h3>
        </div>
        <div className="rounded-xl bg-black/30 border border-white/[0.06] p-4">
          {/* 4 columns by kind */}
          <div className="grid grid-cols-4 gap-3 mb-3 text-center">
            {(['surface', 'execution', 'reasoning', 'knowledge'] as const).map(k => (
              <p key={k} className="text-[9px] uppercase tracking-widest font-bold font-mono" style={{ color: KIND_COLOR[k] }}>
                {k === 'surface' ? 'INTERFACES' : k === 'execution' ? 'EJECUCIÓN' : k === 'reasoning' ? 'RAZONAMIENTO' : 'CONOCIMIENTO'}
              </p>
            ))}
          </div>
          <div className="grid grid-cols-4 gap-3">
            {(['surface', 'execution', 'reasoning', 'knowledge'] as const).map(k => (
              <div key={k} className="space-y-2">
                {SYSTEM_NODES.filter(n => n.kind === k).map(n => (
                  <div key={n.id} className="rounded-lg p-2 border flex items-center gap-2 text-left"
                    style={{ background: `${n.color}10`, borderColor: `${n.color}30` }}>
                    <span className="text-base shrink-0">{n.emoji}</span>
                    <p className="text-[10px] font-bold text-white truncate">{n.label}</p>
                  </div>
                ))}
              </div>
            ))}
          </div>
          {/* Flow arrows */}
          <div className="flex items-center justify-center gap-3 mt-4 text-[9px] uppercase tracking-widest text-white/40 font-mono">
            <span style={{ color: KIND_COLOR.surface }}>Interfaces</span>
            <ArrowRight className="w-3 h-3 text-pink-400" />
            <span style={{ color: KIND_COLOR.execution }}>Ejecución</span>
            <ArrowRight className="w-3 h-3 text-pink-400" />
            <span style={{ color: KIND_COLOR.reasoning }}>Razonamiento</span>
            <ArrowRight className="w-3 h-3 text-pink-400 rotate-180" />
            <span style={{ color: KIND_COLOR.knowledge }}>Conocimiento</span>
          </div>
        </div>
      </div>

      <div className="border-t border-white/[0.06] bg-black/30 px-5 py-3 text-center">
        <p className="text-[11px] text-white/60 leading-snug">
          <Sparkles className="w-3 h-3 inline text-purple-400 mr-1" />
          Cuando ves esto, no son N módulos. <span className="text-white font-bold">Es UN cerebro con N brazos.</span> Razona, recuerda, ejecuta y aprende como entidad única.
        </p>
      </div>

      <style jsx>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </section>
  )
}

const Stat = ({ label, value, color }: { label: string; value: string | number; color: string }) => (
  <div className="text-center">
    <p className="text-lg font-black tabular-nums" style={{ color }}>{value}</p>
    <p className="text-[8px] uppercase tracking-widest text-white/40 font-mono">{label}</p>
  </div>
)

const ThoughtStep = ({ label, text, color }: { label: string; text: string; color: string }) => (
  <div className="rounded-lg p-2 bg-white/[0.03] border border-white/[0.05]">
    <p className="text-[8px] uppercase tracking-widest font-bold mb-1" style={{ color }}>{label}</p>
    <p className="text-[10px] text-white/80 leading-snug">{text}</p>
  </div>
)
