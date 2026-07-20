'use client'

/**
 * BRAIN FUNNEL MAP
 *
 * Visual hero: organic cortex topology with 3 funnel lobes (Adquisición → Conversión → Retención)
 * plus a Core node anchoring everything. Synapses are animated SVG paths with drifting energy
 * particles that travel between lobes — left to right, simulating lead progression.
 *
 * Click a lobe → scrolls Hub shell to that section.
 */

import { useEffect, useMemo, useRef, useState } from 'react'

import { LOBES, TOOLS_BY_LOBE, type LobeId, type Tool } from './toolIndex'


interface BrainFunnelMapProps {
  onLobeSelect: (lobeId: LobeId) => void
  onToolSelect: (componentId: string) => void
}


export const BrainFunnelMap = ({ onLobeSelect, onToolSelect }: BrainFunnelMapProps): React.JSX.Element => {
  return (
    <section className="relative w-full overflow-hidden">
      {/* Background atmosphere */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[1200px] h-[700px] rounded-full bg-cyan-500/[0.06] blur-[160px]" />
        <div className="absolute top-1/3 left-1/4 w-[500px] h-[500px] rounded-full bg-pink-500/[0.05] blur-[140px]" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] rounded-full bg-emerald-500/[0.05] blur-[140px]" />
        <NoiseLayer />
      </div>

      <div className="relative max-w-7xl mx-auto px-6 pt-32 pb-12">
        <Header />
        <Topology onLobeSelect={onLobeSelect} />
        <StageRail onToolSelect={onToolSelect} />
      </div>
    </section>
  )
}


const Header = (): React.JSX.Element => (
  <div className="text-center mb-10">
    <p className="inline-flex items-center gap-2 text-[10px] font-mono tracking-[0.4em] uppercase text-white/50 px-3 py-1 rounded-full border border-white/10 bg-white/[0.03] mb-6">
      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
      SellIA · cerebro vendedor activo
    </p>
    <h1
      className="text-[clamp(2.4rem,6vw,5rem)] font-light leading-[0.95] text-white mb-4"
      style={{
        fontFamily: '"Cormorant Garamond", "Iowan Old Style", Georgia, serif',
        letterSpacing: '-0.02em',
      }}
    >
      Un cerebro que <em className="italic font-normal bg-gradient-to-r from-cyan-300 via-pink-300 to-emerald-300 bg-clip-text text-transparent">vende solo</em>.
    </h1>
    <p className="max-w-2xl mx-auto text-[14px] text-white/55 leading-relaxed">
      Conseguí prospectos. Convertilos en clientes. Hacelos volver.
      <br className="hidden sm:inline" />
      Cada lóbulo del cerebro opera una etapa del embudo · sin pausa, sin supervisión.
    </p>
  </div>
)


const Topology = ({ onLobeSelect }: { onLobeSelect: (id: LobeId) => void }): React.JSX.Element => {
  const lobes: LobeId[] = ['acquire', 'convert', 'retain', 'core']
  return (
    <div className="relative aspect-[16/8] w-full">
      <svg viewBox="0 0 1000 500" className="absolute inset-0 w-full h-full">
        <defs>
          <linearGradient id="syn-a-c" x1="0%" y1="50%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#ec4899" stopOpacity="0.6" />
          </linearGradient>
          <linearGradient id="syn-c-r" x1="0%" y1="0%" x2="100%" y2="50%">
            <stop offset="0%" stopColor="#ec4899" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#10b981" stopOpacity="0.6" />
          </linearGradient>
          <linearGradient id="syn-r-a" x1="100%" y1="50%" x2="0%" y2="50%">
            <stop offset="0%" stopColor="#10b981" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#22d3ee" stopOpacity="0.35" />
          </linearGradient>
          <radialGradient id="core-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#a855f7" stopOpacity="0.55" />
            <stop offset="100%" stopColor="#a855f7" stopOpacity="0" />
          </radialGradient>
          <filter id="lobe-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="8" />
          </filter>
        </defs>

        {/* Synapse paths · curved */}
        <path d="M 130 250 C 280 100, 380 60, 500 150" stroke="url(#syn-a-c)" strokeWidth="1.5" fill="none" opacity="0.7" />
        <path d="M 500 150 C 620 60, 720 100, 870 250" stroke="url(#syn-c-r)" strokeWidth="1.5" fill="none" opacity="0.7" />
        <path d="M 870 250 C 870 360, 600 460, 500 390" stroke="url(#syn-c-r)" strokeWidth="0.8" fill="none" opacity="0.3" strokeDasharray="4 6" />
        <path d="M 500 390 C 400 460, 130 360, 130 250" stroke="url(#syn-r-a)" strokeWidth="0.8" fill="none" opacity="0.3" strokeDasharray="4 6" />
        <path d="M 130 250 C 250 280, 380 340, 500 390" stroke="#a855f7" strokeWidth="0.6" fill="none" opacity="0.3" strokeDasharray="2 8" />
        <path d="M 870 250 C 740 280, 620 340, 500 390" stroke="#a855f7" strokeWidth="0.6" fill="none" opacity="0.3" strokeDasharray="2 8" />

        {/* Energy particles on main pathway */}
        {Array.from({ length: 6 }).map((_, i) => (
          <g key={i}>
            <circle r="2.5" fill="#22d3ee">
              <animateMotion dur={`${5 + i * 0.4}s`} repeatCount="indefinite" begin={`${i * 0.8}s`}>
                <mpath href="#path-ac" />
              </animateMotion>
            </circle>
            <circle r="2.5" fill="#ec4899">
              <animateMotion dur={`${5 + i * 0.4}s`} repeatCount="indefinite" begin={`${i * 0.8 + 0.3}s`}>
                <mpath href="#path-cr" />
              </animateMotion>
            </circle>
          </g>
        ))}
        <path id="path-ac" d="M 130 250 C 280 100, 380 60, 500 150" fill="none" opacity="0" />
        <path id="path-cr" d="M 500 150 C 620 60, 720 100, 870 250" fill="none" opacity="0" />
      </svg>

      {/* Lobe nodes positioned over SVG */}
      <div className="absolute inset-0">
        {lobes.map((id) => (
          <LobeNode key={id} id={id} onSelect={onLobeSelect} />
        ))}
      </div>
    </div>
  )
}


const LobeNode = ({ id, onSelect }: { id: LobeId; onSelect: (id: LobeId) => void }): React.JSX.Element => {
  const lobe = LOBES[id]
  const tools = TOOLS_BY_LOBE[id]
  const isCore = id === 'core'
  return (
    <button
      type="button"
      onClick={() => onSelect(id)}
      className="absolute group focus:outline-none"
      style={{
        left: `${lobe.position.x}%`,
        top: `${lobe.position.y}%`,
        transform: 'translate(-50%, -50%)',
      }}
    >
      {/* Outer halo */}
      <span
        className="absolute -inset-8 rounded-full opacity-60 group-hover:opacity-90 transition-opacity"
        style={{
          background: `radial-gradient(circle, ${lobe.glow} 0%, transparent 70%)`,
        }}
      />
      {/* Orbital ring */}
      <span
        className="absolute inset-0 rounded-full border opacity-40 animate-[spin_22s_linear_infinite] pointer-events-none"
        style={{
          borderColor: `${lobe.color}66`,
          width: isCore ? 220 : 180,
          height: isCore ? 220 : 180,
          left: isCore ? -110 : -90,
          top: isCore ? -110 : -90,
          borderStyle: 'dashed',
        }}
      />
      {/* Core circle */}
      <span
        className="relative flex items-center justify-center rounded-full border backdrop-blur-md"
        style={{
          width: isCore ? 160 : 140,
          height: isCore ? 160 : 140,
          background: `radial-gradient(circle at 30% 30%, ${lobe.color}22, rgba(8,10,22,0.85) 60%)`,
          borderColor: `${lobe.color}55`,
          boxShadow: `0 0 60px -10px ${lobe.glow}, inset 0 0 30px ${lobe.glow}`,
        }}
      >
        <div className="text-center px-3">
          <div
            className="text-[9px] font-mono tracking-[0.3em] uppercase mb-1"
            style={{ color: lobe.color }}
          >
            {lobe.label}
          </div>
          <div
            className="text-white font-light leading-tight"
            style={{
              fontFamily: '"Cormorant Garamond", Georgia, serif',
              fontSize: isCore ? '16px' : '15px',
            }}
          >
            {lobe.title.split(' ').slice(0, 4).join(' ')}
          </div>
          <div className="text-[10px] text-white/55 mt-1.5 font-mono">
            {tools.length} skills
          </div>
        </div>
      </span>
      {/* Tool count micro-orbs */}
      <span className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center text-[9px] font-bold"
        style={{
          background: lobe.color,
          color: '#03050e',
          boxShadow: `0 0 12px ${lobe.glow}`,
        }}>
        {tools.length}
      </span>
    </button>
  )
}


const StageRail = ({ onToolSelect }: { onToolSelect: (componentId: string) => void }): React.JSX.Element => {
  const order: LobeId[] = ['acquire', 'convert', 'retain']
  return (
    <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
      {order.map((id, idx) => {
        const lobe = LOBES[id]
        const tools = TOOLS_BY_LOBE[id].slice(0, 5)
        return (
          <div
            key={id}
            className="relative rounded-2xl border bg-gradient-to-br from-white/[0.03] to-transparent p-4"
            style={{ borderColor: `${lobe.color}33` }}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-[9px] font-mono tracking-[0.3em] uppercase text-white/40">
                  paso {idx + 1}
                </span>
                <span className="w-1 h-1 rounded-full bg-white/20" />
                <span className="text-[10px] font-mono tracking-widest uppercase" style={{ color: lobe.color }}>
                  {lobe.label}
                </span>
              </div>
              <span className="text-[10px] text-white/40 font-mono">{TOOLS_BY_LOBE[id].length}</span>
            </div>
            <h3
              className="text-white text-[18px] font-light leading-snug mb-1"
              style={{ fontFamily: '"Cormorant Garamond", Georgia, serif' }}
            >
              {lobe.title}
            </h3>
            <p className="text-[11px] text-white/45 leading-relaxed mb-3">{lobe.subtitle}</p>
            <ul className="space-y-1">
              {tools.map((t: Tool) => (
                <li key={t.id}>
                  <button
                    type="button"
                    onClick={() => onToolSelect(t.componentId)}
                    className="w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-left hover:bg-white/[0.04] transition"
                  >
                    <span className="text-[14px]">{t.icon}</span>
                    <span className="text-[12px] text-white/80 flex-1 truncate">{t.title}</span>
                    <span className="text-[9px] text-white/30 font-mono">↳</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )
      })}
    </div>
  )
}


const NoiseLayer = (): React.JSX.Element => (
  <div
    className="absolute inset-0 opacity-[0.04] mix-blend-overlay pointer-events-none"
    style={{
      backgroundImage: `url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>")`,
    }}
  />
)


export default BrainFunnelMap
