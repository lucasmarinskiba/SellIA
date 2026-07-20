'use client'

/**
 * BRAIN CORTEX HERO · 2026 OS aesthetic.
 *
 * Monochrome surface (charcoal #08090c) · single signal color: ACID LIME #d3ff3a.
 * Type-driven, OS-window-chrome cards, technical density.
 *
 *  - Mega headline · Geist 800/900 · tracking-tight.
 *  - Funnel as 4-node flat graph w/ animated wire pulses (no organic anatomy).
 *  - Each node = OS-style window card w/ live KPIs.
 *  - Bottom: pipeline manifold strip + scenario chips.
 *  - One accent color · zero rainbow gradient.
 */

import { useEffect, useMemo, useRef, useState } from 'react'
import { ArrowRight, Search, Cpu, ChevronRight, TrendingUp, TrendingDown, Sparkles } from 'lucide-react'

import { LOBES, TOOLS_BY_LOBE, TOOLS, fuzzyMatch, type LobeId, type Tool } from './toolIndex'
import { KPICell, LOBE_KPIS } from './LiveKPITicker'


interface BrainCortexHeroProps {
  onLobeSelect: (id: LobeId) => void
  onToolSelect: (componentId: string) => void
  onCommand: (q: string) => void
}


export const BrainCortexHero = ({ onLobeSelect, onToolSelect, onCommand }: BrainCortexHeroProps): React.JSX.Element => (
  <section className="relative">
    <div className="relative max-w-[1400px] mx-auto px-5 sm:px-7 pt-12 pb-10">
      <Eyebrow />
      <Headline />
      <CommandRow onCommand={onCommand} onToolSelect={onToolSelect} />
      <FunnelGraph onLobeSelect={onLobeSelect} onToolSelect={onToolSelect} />
      <PipelineStrip />
    </div>
  </section>
)


/* ───────────────────────  eyebrow  ─────────────────────── */


const Eyebrow = (): React.JSX.Element => (
  <div className="flex items-center justify-center gap-3 mb-5">
    <span className="font-[var(--font-mono,_Geist_Mono)] text-[10px] tracking-[0.5em] uppercase text-white/40">
      revenue-os · live
    </span>
    <span className="w-px h-3 bg-white/15" />
    <span className="font-[var(--font-mono,_Geist_Mono)] text-[10px] tracking-widest uppercase inline-flex items-center gap-1.5"
      style={{ color: '#d3ff3a' }}
    >
      <span className="relative w-1.5 h-1.5">
        <span className="absolute inset-0 rounded-full animate-ping" style={{ background: '#d3ff3a' }} />
        <span className="absolute inset-0 rounded-full" style={{ background: '#d3ff3a' }} />
      </span>
      cerebro operativo
    </span>
  </div>
)


/* ───────────────────────  headline  ─────────────────────── */


const Headline = (): React.JSX.Element => (
  <div className="text-center max-w-[1100px] mx-auto">
    <h1
      className="text-[clamp(2.8rem,8vw,6.5rem)] font-[900] tracking-[-0.04em] leading-[0.86] text-white"
      style={{ textWrap: 'balance' as React.CSSProperties['textWrap'] }}
    >
      Captar.{' '}
      <span style={{ color: '#d3ff3a' }}>Cerrar.</span>{' '}
      Volver.
    </h1>
    <p className="mt-5 text-[14px] sm:text-[15px] text-white/55 leading-relaxed max-w-[640px] mx-auto">
      Tres etapas, cuatro lóbulos, un solo cerebro. Cada nodo opera 24/7 — vos lo gobernás desde la barra de comando.
    </p>
  </div>
)


/* ───────────────────────  inline command + chips  ─────────────────── */


const CommandRow = (
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
    <div className="mt-10 mx-auto w-[min(820px,calc(100%-1rem))]">
      <div className="rounded-xl border bg-[rgba(8,9,12,0.78)] backdrop-blur-xl overflow-hidden"
        style={{ borderColor: focused ? 'rgba(211,255,58,0.4)' : 'rgba(255,255,255,0.08)' }}
      >
        <div className="flex items-center gap-2.5 px-4 py-3">
          <span className="w-7 h-7 rounded-md flex items-center justify-center" style={{ background: '#d3ff3a' }}>
            <Cpu className="w-3.5 h-3.5 text-[#08090c]" />
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
            placeholder='"recuperá los carritos abandonados de hoy"  ·  "abrí Computer Use"  ·  "emití factura E a Brasil"'
            className="flex-1 bg-transparent text-white placeholder:text-white/30 outline-none text-[14px]"
            style={{ fontFamily: 'Geist, ui-sans-serif, system-ui' }}
          />
          <span className="hidden md:inline mono-tag">⌘ K</span>
          <button
            type="button"
            disabled={!q.trim()}
            onClick={() => results[0] ? onToolSelect(results[0].componentId) : onCommand(q.trim())}
            className="px-3 py-1.5 rounded-md text-[11px] font-bold disabled:opacity-30 transition"
            style={{ background: '#d3ff3a', color: '#08090c' }}
          >
            ENTER ↵
          </button>
        </div>
        {focused && results.length > 0 && (
          <div className="border-t border-white/8 max-h-72 overflow-y-auto">
            {results.map((t) => (
              <button
                key={t.id}
                type="button"
                onMouseDown={(e) => { e.preventDefault(); onToolSelect(t.componentId) }}
                className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-white/[0.04] text-left"
              >
                <span className="text-[13px] font-semibold text-white truncate flex-1">{t.title}</span>
                <span className="text-[11px] text-white/45 hidden sm:inline truncate max-w-[300px]">{t.subtitle}</span>
                <span className="font-mono text-[9px] uppercase tracking-widest px-1.5 py-0.5 rounded border border-white/10 text-white/55">
                  {LOBES[t.lobe].label}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* chips */}
      <div className="mt-3 flex flex-wrap justify-center gap-1.5">
        {QUICK_CHIPS.map((c) => (
          <button
            key={c.label}
            onClick={() => onToolSelect(c.componentId)}
            className="px-2.5 py-1 rounded-md border border-white/10 bg-white/[0.03] text-[11px] text-white/75 hover:border-white/25 hover:bg-white/[0.07] transition mono-shortcut"
          >
            {c.label}
          </button>
        ))}
      </div>

      <style>{`
        .mono-tag { font-family: "Geist Mono", ui-monospace, monospace; font-size: 10px; letter-spacing: 0.15em; color: rgba(255,255,255,0.45); border: 1px solid rgba(255,255,255,0.12); padding: 2px 6px; border-radius: 4px; }
        .mono-shortcut { font-family: "Geist Mono", ui-monospace, monospace; letter-spacing: 0.02em; }
      `}</style>
    </div>
  )
}


const QUICK_CHIPS: Array<{ label: string; componentId: string }> = [
  { label: 'lanzar ads',          componentId: 'lobe-acquire-ads' },
  { label: 'captar omnicanal',    componentId: 'lobe-acquire-omni' },
  { label: 'desbloquear deal',    componentId: 'lobe-convert-doctor' },
  { label: 'modo autónomo',       componentId: 'lobe-convert-autonomous' },
  { label: 'computer use',        componentId: 'lobe-convert-cua-main' },
  { label: 'recuperar carrito',   componentId: 'lobe-retain-recovery' },
  { label: 'fidelizar cliente',   componentId: 'lobe-retain-fidel' },
  { label: 'facturar ARCA',       componentId: 'lobe-retain-arca' },
]


/* ───────────────────────  funnel graph (flat OS-style)  ─────────────────── */


const NODE_ORDER: LobeId[] = ['acquire', 'convert', 'retain']


const FunnelGraph = (
  { onLobeSelect, onToolSelect }: { onLobeSelect: (id: LobeId) => void; onToolSelect: (cid: string) => void },
): React.JSX.Element => (
  <div className="relative mt-14">
    {/* connecting line */}
    <div className="hidden lg:block absolute top-[44px] left-[10%] right-[10%] h-px bg-white/8" />
    <div
      className="hidden lg:block absolute top-[44px] left-[10%] h-px"
      style={{
        width: '80%',
        background: 'linear-gradient(90deg, transparent, #d3ff3a, transparent)',
        opacity: 0.35,
        animation: 'wire-pulse 6s linear infinite',
      }}
    />
    <style>{`
      @keyframes wire-pulse {
        0%   { transform: translateX(-50%); opacity: 0; }
        20%  { opacity: 0.55; }
        100% { transform: translateX(50%); opacity: 0; }
      }
    `}</style>
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
      {NODE_ORDER.map((id, i) => (
        <LobeNode key={id} id={id} index={i + 1} onSelect={onLobeSelect} onToolSelect={onToolSelect} />
      ))}
    </div>
    <CoreNode onSelect={onLobeSelect} />
  </div>
)


const LobeNode = (
  { id, index, onSelect, onToolSelect }: {
    id: LobeId
    index: number
    onSelect: (id: LobeId) => void
    onToolSelect: (cid: string) => void
  },
): React.JSX.Element => {
  const lobe = LOBES[id]
  const tools = TOOLS_BY_LOBE[id].slice(0, 4)
  const kpis = LOBE_KPIS[id]
  return (
    <article
      className="relative rounded-xl border border-white/8 bg-[#11141b] overflow-hidden hover:border-white/18 transition"
      style={{ boxShadow: '0 0 0 1px rgba(255,255,255,0.02), 0 50px 120px -50px rgba(0,0,0,0.9), inset 0 1px 0 rgba(255,255,255,0.04)' }}
    >
      {/* window chrome bar */}
      <header className="flex items-center gap-2 px-3.5 py-2.5 border-b border-white/8">
        <span className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
        <span className="w-2.5 h-2.5 rounded-full bg-[#febc2e]" />
        <span className="w-2.5 h-2.5 rounded-full bg-[#28c840]" />
        <div className="ml-3 inline-flex items-center gap-2 px-2 py-0.5 rounded font-mono text-[9.5px] tracking-[0.3em] uppercase text-white/50 border border-white/8 bg-black/30">
          <span>node.</span>
          <span style={{ color: '#d3ff3a' }}>{index.toString().padStart(2, '0')}</span>
          <span>·</span>
          <span>{lobe.label}</span>
        </div>
        <span className="ml-auto font-mono text-[9.5px] tracking-widest uppercase text-white/35">
          {TOOLS_BY_LOBE[id].length} tools
        </span>
      </header>

      {/* body */}
      <button
        type="button"
        onClick={() => onSelect(id)}
        className="w-full text-left px-5 py-4 hover:bg-white/[0.02] transition"
      >
        <div className="flex items-baseline justify-between gap-2">
          <h3 className="text-[22px] font-[800] tracking-tight leading-snug text-white">
            {lobe.title}
          </h3>
          <span className="text-[40px] font-[900] leading-none text-white/8 select-none">
            {index.toString().padStart(2, '0')}
          </span>
        </div>
        <p className="mt-1.5 text-[12.5px] text-white/55 leading-relaxed">{lobe.subtitle}</p>
      </button>

      {/* KPIs row */}
      <div className="px-5 pb-4 grid grid-cols-3 gap-3">
        {kpis.map((k) => (
          <div key={k.label} className="border-l border-white/8 pl-3">
            <KPICell kpi={{ ...k, color: '#d3ff3a' }} />
          </div>
        ))}
      </div>

      {/* tools list */}
      <ul className="border-t border-white/8 divide-y divide-white/8">
        {tools.map((t) => (
          <li key={t.id}>
            <button
              type="button"
              onClick={() => onToolSelect(t.componentId)}
              className="w-full flex items-center gap-3 px-5 py-2.5 text-left hover:bg-white/[0.04] transition group"
            >
              <span className="text-[12.5px] font-medium text-white flex-1 truncate">{t.title}</span>
              <span className="text-[11px] text-white/40 hidden sm:inline truncate max-w-[180px]">{t.subtitle}</span>
              <ArrowRight className="w-3 h-3 text-white/30 group-hover:text-[#d3ff3a] group-hover:translate-x-0.5 transition" />
            </button>
          </li>
        ))}
      </ul>
    </article>
  )
}


const CoreNode = ({ onSelect }: { onSelect: (id: LobeId) => void }): React.JSX.Element => (
  <button
    type="button"
    onClick={() => onSelect('core')}
    className="mt-6 w-full rounded-xl border border-white/8 bg-[#11141b] px-5 py-4 flex flex-wrap items-center gap-4 hover:border-white/18 transition text-left"
    style={{ boxShadow: '0 0 0 1px rgba(255,255,255,0.02), 0 30px 80px -40px rgba(0,0,0,0.85)' }}
  >
    <span className="inline-flex items-center gap-2 font-mono text-[10px] tracking-[0.3em] uppercase text-white/45">
      <span>core</span>
      <span>·</span>
      <span style={{ color: '#d3ff3a' }}>cerebro · infra · gobierno</span>
    </span>
    <span className="flex-1 text-[13px] text-white/70">
      Router IA tier-cascade · {TOOLS_BY_LOBE.core.length} módulos de infra: tokens infinitos, audit logs, admin, voice palette, onboarding.
    </span>
    <span className="inline-flex items-center gap-1 font-mono text-[11px] tracking-widest uppercase" style={{ color: '#d3ff3a' }}>
      abrir core <ChevronRight className="w-3.5 h-3.5" />
    </span>
  </button>
)


/* ───────────────────────  pipeline manifold strip  ─────────────────── */


const PipelineStrip = (): React.JSX.Element => (
  <div className="mt-10 rounded-xl border border-white/8 bg-[#11141b] overflow-hidden"
    style={{ boxShadow: '0 0 0 1px rgba(255,255,255,0.02), 0 30px 80px -40px rgba(0,0,0,0.85)' }}
  >
    <div className="flex items-center justify-between px-5 py-3 border-b border-white/8">
      <span className="font-mono text-[10px] tracking-[0.3em] uppercase text-white/50">flujo · últimas 24h</span>
      <span className="font-mono text-[10px] tracking-widest uppercase inline-flex items-center gap-1.5" style={{ color: '#d3ff3a' }}>
        <span className="w-1.5 h-1.5 rounded-full" style={{ background: '#d3ff3a', animation: 'pulse-soft 1.6s infinite' }} />
        stream live
      </span>
    </div>
    <div className="grid grid-cols-3 divide-x divide-white/8">
      <FlowCell tag="ADQ" count={1284} pct={100} label="leads captados" />
      <FlowCell tag="CON" count={547}  pct={42}  label="cerraron" />
      <FlowCell tag="RET" count={361}  pct={28}  label="volvieron" emphasize />
    </div>
    <div className="relative h-px bg-white/8 overflow-hidden">
      <span
        className="absolute inset-y-0 w-1/4"
        style={{
          background: 'linear-gradient(90deg, transparent, #d3ff3a, transparent)',
          animation: 'wire-pulse 5s linear infinite',
        }}
      />
    </div>
  </div>
)


const FlowCell = (
  { tag, count, pct, label, emphasize }: { tag: string; count: number; pct: number; label: string; emphasize?: boolean },
): React.JSX.Element => (
  <div className="px-5 py-4 flex items-baseline gap-3" style={{ background: emphasize ? 'rgba(211,255,58,0.04)' : 'transparent' }}>
    <span className="font-mono text-[10px] tracking-[0.3em] uppercase text-white/45">{tag}</span>
    <span className={`text-[28px] font-[800] leading-none tabular-nums ${emphasize ? '' : 'text-white'}`} style={{ color: emphasize ? '#d3ff3a' : undefined }}>
      {count.toLocaleString('es-AR')}
    </span>
    <span className="text-[11px] text-white/45">· {pct}% top</span>
    <span className="ml-auto text-[11px] text-white/55 hidden sm:inline">{label}</span>
  </div>
)


export default BrainCortexHero
