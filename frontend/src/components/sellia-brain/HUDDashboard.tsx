'use client'

/**
 * SELLIA HUD · JARVIS-style mission deck.
 *
 *   - bg-slate-950 base · text-cyan-400 accents · JetBrains Mono everywhere.
 *   - Bento grid dense (12-col) packed with radial gauges, ring widgets, network radar,
 *     scrolling log terminal, audio waveform, holographic prompt bar.
 *   - Hover micro-interactions: scale-105 + cyan glow + corner brackets light up.
 *   - Modals overlay with backdrop-blur-md.
 *   - All numbers tick in real time (mocked) to simulate continuous analysis.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Activity, ArrowRight, Bot, Brain, ChevronRight, Command, Cpu, MessageSquare, Mic,
  MonitorCheck, Pause, Play, Radio, Search, Sparkles, Target, TrendingUp, Wifi, Zap,
} from 'lucide-react'

import { LOBES, TOOLS, TOOLS_BY_LOBE, fuzzyMatch, type LobeId, type Tool } from './toolIndex'
import {
  loadBrainSnapshot, seedBrainData, tickSnapshot, generateEvent, persistMetricsTick,
  type BrainSnapshot, type BrainAgent, type BrainEvent,
} from '@/lib/brain-metrics'


/* ────────────────────────  Real data hook  ─────────────── */

const BIZ_KEY = 'sellia_biz_ctx_v1'

const useBrainData = (): BrainSnapshot | null => {
  const [snap, setSnap] = useState<BrainSnapshot | null>(null)

  useEffect(() => {
    let isMounted = true
    const init = async (): Promise<void> => {
      // Try to load existing snapshot
      const existing = await loadBrainSnapshot()
      if (existing && isMounted) { setSnap(existing); return }

      // Seed from businessCtx if available
      try {
        const raw = localStorage.getItem(BIZ_KEY)
        if (raw) {
          const biz = JSON.parse(raw) as {
            businessName: string; bizType: string; volume: string; channels: string[]; goals: string[]
          }
          const seeded = await seedBrainData(biz)
          if (isMounted) setSnap(seeded)
          return
        }
      } catch { /* ignore */ }

      // Fallback: seed with generic demo data
      const demo = await seedBrainData({
        businessName: 'Mi Negocio', bizType: 'ambos', volume: '50-200',
        channels: ['whatsapp', 'instagram', 'meta'], goals: ['leads', 'conversion', 'automate'],
      })
      if (isMounted) setSnap(demo)
    }
    void init()
    return () => { isMounted = false }
  }, [])

  // Tick every 5s: small random deltas for "live" feel
  useEffect(() => {
    if (!snap) return
    const id = window.setInterval(() => {
      setSnap(prev => {
        if (!prev) return prev
        // Prepend new event occasionally
        const addEvent = Math.random() > 0.6
        const ticked = tickSnapshot(prev)
        if (addEvent) {
          const newEvt = generateEvent()
          ticked.events = [newEvt, ...ticked.events.slice(0, 18)]
        }
        return ticked
      })
    }, 5_000)
    return () => window.clearInterval(id)
  }, [snap !== null]) // eslint-disable-line react-hooks/exhaustive-deps

  // Persist back to Supabase every 30s
  useEffect(() => {
    if (!snap) return
    const id = window.setInterval(() => {
      void persistMetricsTick(snap)
    }, 30_000)
    return () => window.clearInterval(id)
  }, [snap !== null]) // eslint-disable-line react-hooks/exhaustive-deps

  return snap
}


interface HUDDashboardProps {
  onLobeSelect: (id: LobeId) => void
  onToolSelect: (componentId: string) => void
  onCommand: (q: string) => void
  onHandsFree: () => void
  onCUA: () => void
}


export const HUDDashboard = ({
  onLobeSelect, onToolSelect, onCommand, onHandsFree, onCUA,
}: HUDDashboardProps): React.JSX.Element => {
  const snap = useBrainData()

  const kpis       = snap?.kpis
  const agents     = snap?.agents ?? []
  const pipeline   = snap?.pipeline
  const events     = snap?.events ?? []

  return (
    <section className="relative">
      <HUDStyles />
      <HUDBackdrop />
      <div className="relative max-w-[1500px] mx-auto px-4 sm:px-6 pt-8 pb-10">
        <HUDStatusBar agentsLive={kpis?.agentsLive} automations={kpis?.automations} />
        <HUDTitle agentsLive={kpis?.agentsLive} />
        <HUDPromptBar onCommand={onCommand} onToolSelect={onToolSelect} />

        {/* Bento dense grid · 12 col */}
        <div className="mt-6 grid grid-cols-12 gap-3 auto-rows-[110px]">
          <GaugeCell label="WIN RATE"    value={kpis?.winRate   ?? 0}   suffix="%" color="#22d3ee" sublabel="trial avg"      span="col-span-6 sm:col-span-3 row-span-2" />
          <GaugeCell label="LEAD VEL."   value={kpis?.leadVel   ?? 0}   suffix=""  color="#a3e635" sublabel="signals/min"    span="col-span-6 sm:col-span-3 row-span-2" />
          <GaugeCell label="MRR GROWTH"  value={kpis?.mrrGrowth ?? 0}   suffix="%" color="#f97316" sublabel="qoq"            span="col-span-6 sm:col-span-3 row-span-2" />
          <GaugeCell label="LATENCY"     value={kpis?.latencyMs ?? 999} suffix="ms"color="#22d3ee" sublabel="p50 inference"  span="col-span-6 sm:col-span-3 row-span-2" maxValue={1000} reverse />

          <RadarNetwork  span="col-span-12 lg:col-span-7 row-span-4" onLobeSelect={onLobeSelect} />
          <LogTerminal   span="col-span-12 sm:col-span-7 lg:col-span-5 row-span-4" events={events} />

          <AgentRoster     span="col-span-12 sm:col-span-6 lg:col-span-4 row-span-3" onToolSelect={onToolSelect} agents={agents} />
          <WaveformWidget  span="col-span-12 sm:col-span-6 lg:col-span-4 row-span-3" onHandsFree={onHandsFree} />
          <CUAQuickCell    span="col-span-12 lg:col-span-4 row-span-3" onCUA={onCUA} automations={kpis?.automations ?? 0} />

          <PipelineBar span="col-span-12 row-span-2" pipeline={pipeline} />

          {(['acquire', 'convert', 'retain'] as LobeId[]).map((id) => (
            <LobeQuickCell
              key={id}
              span="col-span-12 sm:col-span-4 row-span-3"
              id={id}
              onSelect={onLobeSelect}
              onToolSelect={onToolSelect}
            />
          ))}
        </div>
      </div>
    </section>
  )
}


/* ────────────────────────  styles + backdrop  ───────────────────── */


const HUDStyles = (): React.JSX.Element => (
  <style>{`
    .hud-mono { font-family: "JetBrains Mono", ui-monospace, "Geist Mono", monospace; font-feature-settings: "ss02","zero"; }
    .hud-panel {
      background: rgba(2,6,23,0.55);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(34,211,238,0.18);
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.03),
        0 0 0 1px rgba(2,6,23,0.4),
        0 30px 80px -40px rgba(2,6,23,0.9);
      transition: transform 200ms ease, border-color 200ms ease, box-shadow 200ms ease;
      position: relative;
      overflow: hidden;
    }
    .hud-panel:hover {
      border-color: rgba(34,211,238,0.48);
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.05),
        0 0 0 1px rgba(34,211,238,0.18),
        0 0 60px -10px rgba(34,211,238,0.35);
      transform: scale(1.012);
    }
    .hud-bracket::before, .hud-bracket::after,
    .hud-bracket > .br-tl::before, .hud-bracket > .br-tr::before,
    .hud-bracket > .br-bl::before, .hud-bracket > .br-br::before {
      content: '';
      position: absolute;
      width: 14px; height: 14px;
      border-color: rgba(34,211,238,0.7);
      border-style: solid;
      border-width: 0;
      pointer-events: none;
    }
    .hud-bracket::before { top: 6px; left: 6px;  border-top-width: 1px; border-left-width: 1px; }
    .hud-bracket::after  { top: 6px; right: 6px; border-top-width: 1px; border-right-width: 1px; }
    .hud-bracket > .br-bl::before { bottom: 6px; left: 6px;  border-bottom-width: 1px; border-left-width: 1px; }
    .hud-bracket > .br-br::before { bottom: 6px; right: 6px; border-bottom-width: 1px; border-right-width: 1px; }
    .hud-glow-cyan { box-shadow: 0 0 24px rgba(34,211,238,0.45); }
    .scanline {
      position: absolute; inset: 0; pointer-events: none;
      background: repeating-linear-gradient(
        180deg,
        rgba(34,211,238,0.04) 0px,
        rgba(34,211,238,0.04) 1px,
        transparent 1px,
        transparent 4px
      );
      mix-blend-mode: overlay;
    }
    @keyframes hud-spin { from { transform: rotate(0); } to { transform: rotate(360deg); } }
    @keyframes hud-rev  { from { transform: rotate(0); } to { transform: rotate(-360deg); } }
    @keyframes hud-blink { 0%, 49% { opacity: 1; } 50%, 100% { opacity: 0; } }
    @keyframes hud-pulse { 0%,100%{opacity:.45} 50%{opacity:1} }
    @keyframes hud-sweep { 0% { transform: translateX(-100%); } 100% { transform: translateX(120%); } }
    @keyframes hud-radar {
      0% { transform: rotate(0deg); opacity: 0.5; }
      100% { transform: rotate(360deg); opacity: 0.5; }
    }
    @keyframes hud-wave {
      0%   { transform: scaleY(0.3); }
      50%  { transform: scaleY(1); }
      100% { transform: scaleY(0.3); }
    }
    @keyframes log-scroll {
      0%   { transform: translateY(0); }
      100% { transform: translateY(-50%); }
    }
  `}</style>
)


const HUDBackdrop = (): React.JSX.Element => (
  <div className="absolute inset-0 pointer-events-none overflow-hidden">
    <div className="absolute inset-0" style={{
      background:
        'radial-gradient(ellipse at 50% -10%, rgba(34,211,238,0.10), transparent 55%),' +
        'radial-gradient(ellipse at 80% 100%, rgba(99,102,241,0.10), transparent 55%),' +
        'linear-gradient(180deg, #020617 0%, #030712 100%)',
    }} />
    <div className="absolute inset-0 opacity-[0.25]" style={{
      backgroundImage:
        'linear-gradient(rgba(34,211,238,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(34,211,238,0.06) 1px, transparent 1px)',
      backgroundSize: '40px 40px',
      maskImage: 'radial-gradient(circle at 50% 40%, black, transparent 80%)',
    }} />
    {/* radial concentric */}
    <svg className="absolute inset-0 w-full h-full opacity-[0.06]">
      <defs>
        <radialGradient id="hud-grid" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="rgba(34,211,238,1)" />
          <stop offset="100%" stopColor="rgba(34,211,238,0)" />
        </radialGradient>
      </defs>
      {Array.from({ length: 9 }).map((_, i) => (
        <circle key={i} cx="50%" cy="50%" r={`${(i + 1) * 8}%`} fill="none" stroke="url(#hud-grid)" strokeWidth="1" strokeDasharray="2 6" />
      ))}
    </svg>
  </div>
)


/* ────────────────────────  status bar (chrome)  ─────────────────── */


const HUDStatusBar = ({ agentsLive, automations }: { agentsLive?: number; automations?: number }): React.JSX.Element => {
  const [t, setT] = useState<number>(Date.now())
  useEffect(() => {
    const id = window.setInterval(() => setT(Date.now()), 1000)
    return () => window.clearInterval(id)
  }, [])
  const time = useMemo<string>(() => new Date(t).toISOString().slice(11, 19), [t])
  return (
    <div className="hud-mono flex items-center justify-between text-[10.5px] tracking-[0.3em] uppercase text-cyan-400/70">
      <span className="inline-flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" style={{ animation: 'hud-pulse 1.6s infinite' }} />
        SYS · ACTIVE
        {agentsLive !== undefined && (
          <span className="text-cyan-300">{agentsLive} AGT</span>
        )}
      </span>
      <span className="hidden sm:inline">
        SELL/IA · REVENUE-OS
        {automations !== undefined && ` · ${automations} AUTOS`}
      </span>
      <span>UTC {time}<span className="inline-block w-1.5" style={{ animation: 'hud-blink 1s steps(2) infinite' }}>_</span></span>
    </div>
  )
}


/* ────────────────────────  title  ───────────────────── */


const HUDTitle = ({ agentsLive }: { agentsLive?: number }): React.JSX.Element => (
  <div className="mt-3 mb-5">
    <h1 className="text-[clamp(2rem,4.5vw,3.4rem)] font-[800] tracking-tight leading-tight text-white"
      style={{ fontFamily: '"Inter", ui-sans-serif, system-ui' }}
    >
      Mission Control{' '}
      <span className="text-cyan-400">/</span>{' '}
      <span className="text-cyan-300">Sales Cortex</span>
    </h1>
    <p className="hud-mono mt-1 text-[11px] tracking-[0.3em] uppercase text-cyan-400/55">
      tres lóbulos · cuatro nodos · operación continua · {agentsLive ?? '…'} agentes vivos
    </p>
  </div>
)


/* ────────────────────────  prompt bar  ───────────────────── */


const HUDPromptBar = (
  { onCommand, onToolSelect }: { onCommand: (q: string) => void; onToolSelect: (cid: string) => void },
): React.JSX.Element => {
  const [q, setQ] = useState<string>('')
  const [focused, setFocused] = useState<boolean>(false)
  const results = useMemo<Tool[]>(() => {
    if (!q.trim()) return []
    return TOOLS
      .map((t) => ({ tool: t, score: fuzzyMatch(q, t) }))
      .filter((x) => x.score > 0)
      .sort((a, b) => b.score - a.score || b.tool.weight - a.tool.weight)
      .slice(0, 7)
      .map((x) => x.tool)
  }, [q])

  return (
    <div className="hud-panel rounded-xl">
      <span className="scanline" />
      <div className="flex items-center gap-2.5 px-4 py-3 border-b border-cyan-400/15">
        <span className="hud-mono text-[10px] tracking-[0.3em] uppercase text-cyan-400/70">CMD</span>
        <span className="hud-mono text-[10px] text-cyan-400/40">›</span>
        <span className="w-7 h-7 rounded-md bg-cyan-500/20 border border-cyan-400/50 flex items-center justify-center">
          <Command className="w-3.5 h-3.5 text-cyan-300" />
        </span>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => window.setTimeout(() => setFocused(false), 180)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && results[0]) onToolSelect(results[0].componentId)
            else if (e.key === 'Enter' && q.trim()) onCommand(q.trim())
          }}
          placeholder='"recuperá los carritos abandonados de hoy" · "lanzá Computer Use" · "emití factura E"'
          className="flex-1 bg-transparent text-cyan-50 placeholder:text-cyan-400/30 outline-none text-[14px] hud-mono"
        />
        <span className="hud-mono text-[10px] tracking-widest uppercase text-cyan-400/40 hidden md:inline-flex items-center gap-1 px-2 py-0.5 rounded border border-cyan-400/20">⌘K</span>
        <button
          type="button"
          disabled={!q.trim()}
          onClick={() => results[0] ? onToolSelect(results[0].componentId) : onCommand(q.trim())}
          className="hud-mono px-3 py-1.5 rounded-md text-[11px] font-bold tracking-widest uppercase bg-cyan-500 hover:bg-cyan-400 disabled:opacity-30 disabled:cursor-not-allowed text-slate-950 transition hover:scale-105 active:scale-100"
        >
          EXEC ↵
        </button>
      </div>
      {focused && results.length > 0 && (
        <div className="max-h-64 overflow-y-auto">
          {results.map((t) => (
            <button
              key={t.id}
              type="button"
              onMouseDown={(e) => { e.preventDefault(); onToolSelect(t.componentId) }}
              className="w-full flex items-center gap-3 px-4 py-2 hover:bg-cyan-500/[0.06] text-left transition"
            >
              <ChevronRight className="w-3 h-3 text-cyan-400" />
              <span className="hud-mono text-[12px] text-cyan-50 truncate flex-1">{t.title}</span>
              <span className="hud-mono text-[10px] text-cyan-400/55 hidden sm:inline truncate max-w-[260px]">{t.subtitle}</span>
              <span className="hud-mono text-[8.5px] uppercase tracking-widest px-1.5 py-0.5 rounded border border-cyan-400/30 text-cyan-300 bg-cyan-500/10">
                {LOBES[t.lobe].label}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}


/* ────────────────────────  Gauge cell (radial ring)  ─────────────── */


const GaugeCell = ({
  label, value, suffix, color, sublabel, span, maxValue = 100, reverse,
}: {
  label: string
  value: number
  suffix: string
  color: string
  sublabel: string
  span: string
  maxValue?: number
  reverse?: boolean
}): React.JSX.Element => {
  const pct = Math.min(value / maxValue, 1)
  const c = 2 * Math.PI * 34
  const dash = c * (reverse ? 1 - pct : pct)
  const [v, setV] = useState<number>(0)
  useEffect(() => {
    let raf = 0; const start = performance.now()
    const tick = (t: number): void => {
      const p = Math.min((t - start) / 1300, 1)
      setV(value * (1 - Math.pow(1 - p, 3)))
      if (p < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [value])
  return (
    <div className={`hud-panel hud-bracket rounded-xl p-3 ${span} flex flex-col`}>
      <span className="br-tl" /><span className="br-tr" /><span className="br-bl" /><span className="br-br" />
      <div className="hud-mono text-[9px] tracking-[0.3em] uppercase text-cyan-400/55 mb-1">{label}</div>
      <div className="flex-1 flex items-center gap-3">
        <div className="relative w-[78px] h-[78px] shrink-0">
          <svg viewBox="0 0 80 80" className="w-full h-full -rotate-90">
            <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(34,211,238,0.12)" strokeWidth="6" />
            <circle
              cx="40" cy="40" r="34" fill="none"
              stroke={color} strokeWidth="6" strokeLinecap="round"
              strokeDasharray={`${dash} ${c}`}
              style={{ transition: 'stroke-dasharray 1.2s cubic-bezier(0.16,1,0.3,1)' }}
            />
          </svg>
          {/* rotating outer ticks */}
          <span className="absolute inset-[-6px] pointer-events-none" style={{ animation: 'hud-spin 18s linear infinite' }}>
            <span className="absolute top-0 left-1/2 -translate-x-1/2 w-px h-1.5 bg-cyan-300" />
            <span className="absolute right-0 top-1/2 -translate-y-1/2 w-1.5 h-px bg-cyan-300" />
            <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-px h-1.5 bg-cyan-300" />
            <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-px bg-cyan-300" />
          </span>
          <span className="absolute inset-0 flex items-center justify-center hud-mono text-[18px] font-bold tabular-nums" style={{ color }}>
            {Math.round(v)}{suffix}
          </span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="hud-mono text-[10.5px] text-cyan-400/70 tracking-wider uppercase">{sublabel}</div>
          <div className="mt-1 h-[3px] rounded-full bg-cyan-500/10 overflow-hidden">
            <div className="h-full rounded-full" style={{ width: `${pct * 100}%`, background: color, boxShadow: `0 0 10px ${color}` }} />
          </div>
        </div>
      </div>
    </div>
  )
}


/* ────────────────────────  Radar network (lobe map)  ─────────────── */


const RadarNetwork = (
  { span, onLobeSelect }: { span: string; onLobeSelect: (id: LobeId) => void },
): React.JSX.Element => (
  <div className={`hud-panel hud-bracket rounded-xl p-3 ${span} flex flex-col`}>
    <span className="br-tl" /><span className="br-tr" /><span className="br-bl" /><span className="br-br" />
    <div className="flex items-center justify-between mb-1.5">
      <span className="hud-mono text-[10px] tracking-[0.3em] uppercase text-cyan-400/70">SALES NETWORK · LIVE TOPOLOGY</span>
      <span className="hud-mono text-[10px] tracking-widest uppercase text-cyan-400/45 inline-flex items-center gap-1.5">
        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" style={{ animation: 'hud-pulse 1.6s infinite' }} />
        scanning
      </span>
    </div>
    <div className="relative flex-1 rounded-md overflow-hidden bg-slate-950/40 border border-cyan-400/10">
      {/* concentric rings */}
      <svg viewBox="0 0 400 240" className="absolute inset-0 w-full h-full">
        {Array.from({ length: 5 }).map((_, i) => (
          <ellipse key={i} cx="200" cy="120" rx={(i + 1) * 35} ry={(i + 1) * 22} fill="none" stroke="rgba(34,211,238,0.12)" strokeWidth="1" strokeDasharray="2 6" />
        ))}
        {/* axes */}
        <line x1="200" y1="0" x2="200" y2="240" stroke="rgba(34,211,238,0.08)" />
        <line x1="0" y1="120" x2="400" y2="120" stroke="rgba(34,211,238,0.08)" />
        {/* sweep */}
        <g style={{ transformOrigin: '200px 120px', animation: 'hud-radar 6s linear infinite' }}>
          <defs>
            <linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%"  stopColor="rgba(34,211,238,0)" />
              <stop offset="100%" stopColor="rgba(34,211,238,0.55)" />
            </linearGradient>
          </defs>
          <path d="M200,120 L400,120 A200,120 0 0,0 200,0 Z" fill="url(#sweep)" />
        </g>
        {/* synapses */}
        <path d="M70,160 C 150,80 260,80 330,160" stroke="rgba(163,230,53,0.55)" strokeWidth="1.2" fill="none" />
        <path d="M70,160 C 130,200 260,200 330,160" stroke="rgba(249,115,22,0.45)" strokeWidth="1.2" fill="none" strokeDasharray="2 4" />
        {/* photons */}
        <circle r="3" fill="#22d3ee">
          <animateMotion dur="5s" repeatCount="indefinite" path="M70,160 C 150,80 260,80 330,160" />
        </circle>
        <circle r="3" fill="#a3e635">
          <animateMotion dur="5s" repeatCount="indefinite" begin="2s" path="M70,160 C 150,80 260,80 330,160" />
        </circle>
        <circle r="3" fill="#f97316">
          <animateMotion dur="7s" repeatCount="indefinite" path="M70,160 C 130,200 260,200 330,160" />
        </circle>
      </svg>
      {/* nodes */}
      <NetworkNode label="ACQUIRE"  hint="captación" x={18}  y={66} dotColor="#22d3ee" onClick={() => onLobeSelect('acquire')} />
      <NetworkNode label="CONVERT"  hint="cierre"    x={50}  y={20} dotColor="#a3e635" onClick={() => onLobeSelect('convert')} pulse />
      <NetworkNode label="RETAIN"   hint="loyalty"   x={82}  y={66} dotColor="#f97316" onClick={() => onLobeSelect('retain')} />
      <NetworkNode label="CORE"     hint="cerebro"   x={50}  y={84} dotColor="#ef4444" onClick={() => onLobeSelect('core')} small />
    </div>
  </div>
)


const NetworkNode = ({
  label, hint, x, y, dotColor, onClick, pulse, small,
}: {
  label: string; hint: string; x: number; y: number
  dotColor: string; onClick: () => void; pulse?: boolean; small?: boolean
}): React.JSX.Element => (
  <button
    type="button"
    onClick={onClick}
    className="group absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center gap-1 focus:outline-none transition hover:scale-110"
    style={{ left: `${x}%`, top: `${y}%` }}
  >
    <span className="relative">
      <span
        className={`block rounded-full border ${small ? 'w-3 h-3' : 'w-4 h-4'}`}
        style={{
          background: 'rgba(2,6,23,0.85)',
          borderColor: dotColor,
          boxShadow: `0 0 12px ${dotColor}88`,
        }}
      />
      {pulse && (
        <span
          className="absolute inset-0 rounded-full"
          style={{ background: dotColor, animation: 'hud-pulse 1.4s infinite', opacity: 0.4 }}
        />
      )}
    </span>
    <span className="hud-mono text-[8.5px] tracking-[0.25em] uppercase font-bold" style={{ color: dotColor }}>{label}</span>
    <span className="hud-mono text-[8px] text-cyan-400/40 opacity-0 group-hover:opacity-100 transition">{hint}</span>
  </button>
)


/* ────────────────────────  Log terminal  ─────────────── */


const LogTerminal = ({ span, events }: { span: string; events: BrainEvent[] }): React.JSX.Element => {
  const lines = events.length > 0 ? events : [
    { ts: '--:--:--', tag: 'SYS', text: 'Cargando datos…', color: '#22d3ee' },
  ]
  return (
    <div className={`hud-panel hud-bracket rounded-xl p-3 ${span} flex flex-col`}>
      <span className="br-tl" /><span className="br-tr" /><span className="br-bl" /><span className="br-br" />
      <div className="flex items-center justify-between mb-2">
        <span className="hud-mono text-[10px] tracking-[0.3em] uppercase text-cyan-400/70">SYSTEM LOG · BACKGROUND OPS</span>
        <span className="hud-mono text-[10px] tracking-widest uppercase text-cyan-400/45 inline-flex items-center gap-1.5">
          <Radio className="w-3 h-3" />
          live tail
        </span>
      </div>
      <div className="relative flex-1 rounded-md overflow-hidden border border-cyan-400/10 bg-black/40">
        <div className="absolute inset-0 overflow-hidden">
          <div className="hud-mono text-[10.5px] leading-[1.5] tracking-wide" style={{ animation: 'log-scroll 22s linear infinite' }}>
            {[...lines, ...lines].map((l, i) => (
              <div key={i} className="grid grid-cols-[58px_48px_1fr] gap-2 px-3 py-1 border-b border-cyan-400/5">
                <span className="text-cyan-400/50">{l.ts}</span>
                <span style={{ color: l.color }} className="font-bold">{l.tag}</span>
                <span className="text-cyan-100/85 truncate">{l.text}</span>
              </div>
            ))}
          </div>
          <div className="absolute inset-x-0 top-0 h-6 bg-gradient-to-b from-black/80 to-transparent pointer-events-none" />
          <div className="absolute inset-x-0 bottom-0 h-6 bg-gradient-to-t from-black/80 to-transparent pointer-events-none" />
        </div>
      </div>
    </div>
  )
}


/* ────────────────────────  Agent roster  ─────────────── */


const AgentRoster = (
  { span, onToolSelect, agents }: { span: string; onToolSelect: (cid: string) => void; agents: BrainAgent[] },
): React.JSX.Element => {
  const list = agents.length > 0 ? agents : [
    { code: '…', name: 'Cargando agentes…', busyPct: 0, color: '#22d3ee' },
  ]
  return (
    <div className={`hud-panel hud-bracket rounded-xl p-3 ${span} flex flex-col`}>
      <span className="br-tl" /><span className="br-tr" /><span className="br-bl" /><span className="br-br" />
      <div className="flex items-center justify-between mb-2">
        <span className="hud-mono text-[10px] tracking-[0.3em] uppercase text-cyan-400/70">
          AGENT ROSTER · {agents.length > 0 ? `${agents.length} ACTIVOS` : 'CARGANDO'}
        </span>
        <button onClick={() => onToolSelect('lobe-convert-legends')} className="hud-mono text-[10px] tracking-widest uppercase text-cyan-300 hover:text-cyan-200 inline-flex items-center gap-1 transition">
          ver todos <ChevronRight className="w-3 h-3" />
        </button>
      </div>
      <ul className="flex-1 flex flex-col justify-between gap-1">
        {list.map((a) => (
          <li key={a.code} className="flex items-center gap-2 px-2 py-1 rounded hover:bg-cyan-500/[0.05] transition">
            <span className="hud-mono text-[9.5px] tracking-widest w-10 font-bold" style={{ color: a.color }}>{a.code}</span>
            <span className="hud-mono text-[11.5px] text-cyan-50/85 flex-1 truncate">{a.name}</span>
            <span className="relative h-1.5 w-16 rounded-full bg-cyan-500/10 overflow-hidden">
              <span className="absolute inset-y-0 left-0 rounded-full" style={{ width: `${a.busyPct}%`, background: a.color, boxShadow: `0 0 8px ${a.color}` }} />
            </span>
            <span className="hud-mono text-[10px] w-8 text-right" style={{ color: a.color }}>{a.busyPct}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}


/* ────────────────────────  Waveform (hands-free)  ─────────────── */


const WaveformWidget = (
  { span, onHandsFree }: { span: string; onHandsFree: () => void },
): React.JSX.Element => (
  <div className={`hud-panel hud-bracket rounded-xl p-3 ${span} flex flex-col`}>
    <span className="br-tl" /><span className="br-tr" /><span className="br-bl" /><span className="br-br" />
    <div className="flex items-center justify-between mb-2">
      <span className="hud-mono text-[10px] tracking-[0.3em] uppercase text-cyan-400/70">VOICE · MANOS LIBRES</span>
      <span className="hud-mono text-[10px] tracking-widest uppercase text-cyan-400/45 inline-flex items-center gap-1.5">
        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" style={{ animation: 'hud-pulse 1.6s infinite' }} />
        idle
      </span>
    </div>
    <div className="flex-1 flex flex-col items-center justify-center gap-3">
      <div className="flex items-end gap-[3px] h-12 w-full justify-center">
        {Array.from({ length: 36 }).map((_, i) => (
          <span
            key={i}
            className="w-1 rounded-full bg-cyan-400"
            style={{
              height: `${30 + ((i * 13) % 60)}%`,
              opacity: 0.85,
              animation: `hud-wave ${0.55 + (i % 5) * 0.13}s ease-in-out infinite alternate`,
              animationDelay: `${i * 0.04}s`,
              boxShadow: '0 0 6px rgba(34,211,238,0.55)',
            }}
          />
        ))}
      </div>
      <div className="hud-mono text-[10.5px] tracking-wide text-cyan-200/85 text-center">
        Decí <span className="text-cyan-300 font-bold">"Hola SellIA"</span> · 12 idiomas
      </div>
      <button
        type="button"
        onClick={onHandsFree}
        className="hud-mono inline-flex items-center gap-1.5 px-3.5 py-2 rounded-md text-[11px] font-bold tracking-widest uppercase bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition hover:scale-105 active:scale-100 hud-glow-cyan"
      >
        <Mic className="w-3.5 h-3.5" /> Activar
      </button>
    </div>
  </div>
)


/* ────────────────────────  CUA quick cell  ─────────────── */


const CUAQuickCell = (
  { span, onCUA, automations }: { span: string; onCUA: () => void; automations: number },
): React.JSX.Element => (
  <div className={`hud-panel hud-bracket rounded-xl p-3 ${span} flex flex-col`}>
    <span className="br-tl" /><span className="br-tr" /><span className="br-bl" /><span className="br-br" />
    <div className="flex items-center justify-between mb-2">
      <span className="hud-mono text-[10px] tracking-[0.3em] uppercase text-cyan-400/70">COMPUTER USE · SANDBOXES</span>
      <span className="hud-mono text-[10px] tracking-widest uppercase text-emerald-400 inline-flex items-center gap-1.5">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" style={{ animation: 'hud-pulse 1.6s infinite' }} />
        {automations > 0 ? `${automations} autos` : '…'}
      </span>
    </div>
    <div className="grid grid-cols-3 gap-1.5">
      {['sb-01', 'sb-02', 'sb-03'].map((sb, i) => (
        <div key={sb} className="rounded-md border border-cyan-400/20 bg-slate-950/60 p-2 flex flex-col gap-1">
          <span className="hud-mono text-[8.5px] tracking-widest text-cyan-300/65 uppercase">{sb}</span>
          <span className="hud-mono text-[10px] text-cyan-100">
            {['ML listings', 'recovery', 'pagos rec.'][i]}
          </span>
          <div className="relative h-1 rounded-full bg-cyan-500/10 overflow-hidden mt-auto">
            <span className="absolute inset-y-0 left-0 rounded-full bg-cyan-400" style={{ width: `${30 + i * 25}%` }} />
            <span className="absolute inset-0" style={{ background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent)', animation: 'hud-sweep 2.4s linear infinite' }} />
          </div>
        </div>
      ))}
    </div>
    <button
      type="button"
      onClick={onCUA}
      className="hud-mono mt-auto inline-flex items-center justify-center gap-1.5 px-3.5 py-2.5 rounded-md text-[11px] font-bold tracking-widest uppercase bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition hover:scale-105 active:scale-100 hud-glow-cyan"
    >
      <MonitorCheck className="w-3.5 h-3.5" /> Abrir Computer Use
      <ArrowRight className="w-3 h-3" />
    </button>
  </div>
)


/* ────────────────────────  Pipeline bar (full width)  ─────────────── */


const PipelineBar = ({ span, pipeline }: { span: string; pipeline?: { acquire: number; convert: number; retain: number } }): React.JSX.Element => {
  const adq = pipeline?.acquire ?? 0
  const con = pipeline?.convert ?? 0
  const ret = pipeline?.retain  ?? 0
  const pctCon = adq > 0 ? Math.round((con / adq) * 100) : 0
  const pctRet = adq > 0 ? Math.round((ret / adq) * 100) : 0
  return (
    <div className={`hud-panel hud-bracket rounded-xl p-3 ${span} flex flex-col`}>
      <span className="br-tl" /><span className="br-tr" /><span className="br-bl" /><span className="br-br" />
      <div className="flex items-center justify-between mb-1.5">
        <span className="hud-mono text-[10px] tracking-[0.3em] uppercase text-cyan-400/70">PIPELINE FLOW · LAST 24H</span>
        <span className="hud-mono text-[10px] tracking-widest uppercase text-cyan-400/45">live stream</span>
      </div>
      <div className="relative flex-1 rounded-md overflow-hidden border border-cyan-400/10 bg-slate-950/60 grid grid-cols-3">
        <FlowCell tag="ADQ" count={adq} pct={100}    color="#22d3ee" />
        <FlowCell tag="CON" count={con} pct={pctCon} color="#a3e635" />
        <FlowCell tag="RET" count={ret} pct={pctRet} color="#f97316" />
        <span className="absolute inset-0 pointer-events-none">
          <span className="absolute inset-y-0 w-1/4" style={{ background: 'linear-gradient(90deg, transparent, rgba(34,211,238,0.18), transparent)', animation: 'hud-sweep 4s linear infinite' }} />
        </span>
      </div>
    </div>
  )
}


const FlowCell = (
  { tag, count, pct, color }: { tag: string; count: number; pct: number; color: string },
): React.JSX.Element => (
  <div className="relative flex items-baseline gap-3 px-4 py-2 border-r border-cyan-400/10 last:border-r-0">
    <span className="hud-mono text-[10px] tracking-[0.3em] uppercase font-bold" style={{ color }}>{tag}</span>
    <span className="hud-mono text-[22px] font-bold tabular-nums" style={{ color }}>{count.toLocaleString('es-AR')}</span>
    <span className="hud-mono text-[10px] text-cyan-400/50">· {pct}%</span>
  </div>
)


/* ────────────────────────  Lobe quick cells (3 stacked)  ─────────── */


const LobeQuickCell = ({
  span, id, onSelect, onToolSelect,
}: {
  span: string
  id: LobeId
  onSelect: (id: LobeId) => void
  onToolSelect: (cid: string) => void
}): React.JSX.Element => {
  const lobe = LOBES[id]
  const tools = TOOLS_BY_LOBE[id].slice(0, 4)
  const accent = id === 'acquire' ? '#22d3ee' : id === 'convert' ? '#a3e635' : '#f97316'
  return (
    <div className={`hud-panel hud-bracket rounded-xl p-3 ${span} flex flex-col`}>
      <span className="br-tl" /><span className="br-tr" /><span className="br-bl" /><span className="br-br" />
      <div className="flex items-center justify-between">
        <span className="hud-mono text-[10px] tracking-[0.3em] uppercase font-bold" style={{ color: accent }}>
          {lobe.label}
        </span>
        <button
          onClick={() => onSelect(id)}
          className="hud-mono text-[10px] tracking-widest uppercase text-cyan-300/70 hover:text-cyan-200 inline-flex items-center gap-1 transition"
        >
          abrir <ChevronRight className="w-3 h-3" />
        </button>
      </div>
      <h3 className="mt-1.5 text-[16px] font-[800] tracking-tight leading-snug text-white">
        {lobe.title}
      </h3>
      <p className="hud-mono text-[10px] text-cyan-400/55 mt-0.5">{TOOLS_BY_LOBE[id].length} módulos activos</p>
      <ul className="mt-2.5 space-y-1">
        {tools.map((t) => (
          <li key={t.id}>
            <button
              type="button"
              onClick={() => onToolSelect(t.componentId)}
              className="w-full flex items-center gap-2 px-2 py-1 rounded text-left hover:bg-cyan-500/[0.06] transition group"
            >
              <span className="w-1 h-1 rounded-full" style={{ background: accent }} />
              <span className="hud-mono text-[11px] text-cyan-100/85 flex-1 truncate">{t.title}</span>
              <ArrowRight className="w-3 h-3 text-cyan-400/40 group-hover:text-cyan-300 group-hover:translate-x-0.5 transition" />
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}


export default HUDDashboard
