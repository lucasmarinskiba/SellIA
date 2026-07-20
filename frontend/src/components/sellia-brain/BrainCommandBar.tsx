'use client'

/**
 * BRAIN COMMAND BAR
 * Sticky floating palette at top-center · ⌘K / Ctrl+K to summon globally.
 * Fuzzy search across 70+ tools · keyboard nav · scroll-to-component on select.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Search, Command, ArrowRight, Sparkles } from 'lucide-react'

import { LOBES, TOOLS, TOOLS_BY_LOBE, fuzzyMatch, type LobeId, type Tool } from './toolIndex'


interface BrainCommandBarProps {
  onJump: (componentId: string) => void
}


export const BrainCommandBar = ({ onJump }: BrainCommandBarProps): React.JSX.Element => {
  const [open, setOpen] = useState<boolean>(false)
  const [query, setQuery] = useState<string>('')
  const [cursor, setCursor] = useState<number>(0)
  const inputRef = useRef<HTMLInputElement | null>(null)
  const listRef = useRef<HTMLDivElement | null>(null)

  const results = useMemo<Tool[]>(() => {
    if (!query.trim()) return []
    return TOOLS
      .map((t) => ({ tool: t, score: fuzzyMatch(query, t) }))
      .filter((x) => x.score > 0)
      .sort((a, b) => b.score - a.score || b.tool.weight - a.tool.weight)
      .slice(0, 24)
      .map((x) => x.tool)
  }, [query])

  const showSuggestions = !query.trim()

  // Global ⌘K / Ctrl+K
  useEffect(() => {
    const handler = (e: KeyboardEvent): void => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setOpen((v) => !v)
      } else if (e.key === 'Escape' && open) {
        setOpen(false)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open])

  useEffect(() => {
    if (open && inputRef.current) inputRef.current.focus()
    if (open) setCursor(0)
  }, [open, query])

  const handleSelect = useCallback((tool: Tool): void => {
    setOpen(false)
    setQuery('')
    onJump(tool.componentId)
  }, [onJump])

  const handleKey = useCallback((e: React.KeyboardEvent<HTMLInputElement>): void => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setCursor((c) => Math.min(c + 1, Math.max(results.length - 1, 0)))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setCursor((c) => Math.max(c - 1, 0))
    } else if (e.key === 'Enter' && results[cursor]) {
      e.preventDefault()
      handleSelect(results[cursor])
    }
  }, [results, cursor, handleSelect])

  return (
    <>
      {/* Bar · always rendered floating */}
      <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 w-[min(720px,calc(100vw-2rem))]">
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="group w-full flex items-center gap-3 rounded-full border border-white/10 bg-[rgba(8,10,22,0.78)] backdrop-blur-xl px-5 py-2.5 shadow-[0_20px_60px_-20px_rgba(0,0,0,0.6),inset_0_1px_0_rgba(255,255,255,0.06)] hover:border-white/20 transition"
          style={{
            boxShadow:
              '0 30px 80px -30px rgba(0,0,0,0.7), inset 0 1px 0 rgba(255,255,255,0.06), 0 0 0 1px rgba(34,211,238,0.05)',
          }}
        >
          <span
            className="relative inline-flex w-6 h-6 rounded-full items-center justify-center"
            style={{
              background:
                'conic-gradient(from 200deg, #22d3ee, #ec4899, #10b981, #facc15, #22d3ee)',
            }}
          >
            <span className="absolute inset-0.5 rounded-full bg-[#070b16]" />
            <Search className="relative w-3 h-3 text-white/80" />
          </span>
          <span className="flex-1 text-left text-[13px] text-white/55 font-[450] tracking-wide truncate">
            <span className="text-white/85 font-semibold">Pensá una herramienta…</span>{' '}
            <span className="hidden sm:inline">leads, deals, factura E, fidelización, recuperar carrito…</span>
          </span>
          <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-md border border-white/10 bg-white/[0.04] text-[10px] font-mono text-white/55">
            <Command className="w-3 h-3" />K
          </kbd>
        </button>
      </div>

      {/* Palette overlay */}
      {open && (
        <div
          className="fixed inset-0 z-[100] flex items-start justify-center pt-[7vh] px-4"
          onClick={() => setOpen(false)}
        >
          <div className="absolute inset-0 bg-black/60 backdrop-blur-md" />
          <div
            role="dialog"
            aria-modal="true"
            onClick={(e) => e.stopPropagation()}
            className="relative w-full max-w-2xl rounded-2xl border border-white/10 bg-gradient-to-br from-[#0a0d1c]/95 to-[#100515]/95 shadow-2xl overflow-hidden"
            style={{
              boxShadow:
                '0 60px 160px -40px rgba(0,0,0,0.9), inset 0 1px 0 rgba(255,255,255,0.07)',
            }}
          >
            <div className="flex items-center gap-3 px-5 py-4 border-b border-white/8">
              <Search className="w-4 h-4 text-cyan-300" />
              <input
                ref={inputRef}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKey}
                placeholder="Buscá una herramienta del cerebro vendedor…"
                className="flex-1 bg-transparent text-white placeholder:text-white/30 text-[15px] outline-none font-[450]"
                style={{ letterSpacing: '0.005em' }}
              />
              <span className="text-[10px] text-white/35 font-mono">esc</span>
            </div>

            <div ref={listRef} className="max-h-[60vh] overflow-y-auto py-2">
              {showSuggestions && (
                <SuggestionGroups onSelect={handleSelect} />
              )}
              {!showSuggestions && results.length === 0 && (
                <div className="py-12 text-center text-[12px] text-white/40">
                  <Sparkles className="w-4 h-4 mx-auto mb-2 opacity-50" />
                  Nada coincide con &ldquo;{query}&rdquo;. Probá: <em>leads</em>, <em>factura</em>, <em>retención</em>, <em>cua</em>.
                </div>
              )}
              {!showSuggestions && results.length > 0 && (
                <div className="px-2">
                  <div className="px-3 py-2 text-[9px] font-mono tracking-[0.25em] text-white/35 uppercase">
                    Resultados · {results.length}
                  </div>
                  {results.map((tool, idx) => (
                    <ResultRow
                      key={tool.id}
                      tool={tool}
                      active={cursor === idx}
                      onSelect={handleSelect}
                      onHover={() => setCursor(idx)}
                    />
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center justify-between px-4 py-2.5 border-t border-white/8 bg-black/30 text-[10px] text-white/40 font-mono">
              <span>↑↓ navegar · ↵ ir · esc salir</span>
              <span>{TOOLS.length} herramientas indexadas</span>
            </div>
          </div>
        </div>
      )}
    </>
  )
}


const SuggestionGroups = ({ onSelect }: { onSelect: (t: Tool) => void }): React.JSX.Element => (
  <div className="px-2">
    {(['acquire', 'convert', 'retain', 'core'] as LobeId[]).map((lobeId) => {
      const lobe = LOBES[lobeId]
      const items = TOOLS_BY_LOBE[lobeId].slice(0, 4)
      return (
        <div key={lobeId} className="mb-2">
          <div className="flex items-center gap-2 px-3 py-2">
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: lobe.color, boxShadow: `0 0 8px ${lobe.glow}` }} />
            <span className="text-[9px] font-mono tracking-[0.25em] uppercase" style={{ color: lobe.color }}>
              {lobe.label}
            </span>
            <span className="text-[10px] text-white/30 italic">{lobe.title}</span>
          </div>
          {items.map((t) => (
            <ResultRow key={t.id} tool={t} active={false} onSelect={onSelect} onHover={() => undefined} />
          ))}
        </div>
      )
    })}
  </div>
)


const ResultRow = ({
  tool, active, onSelect, onHover,
}: {
  tool: Tool
  active: boolean
  onSelect: (t: Tool) => void
  onHover: () => void
}): React.JSX.Element => {
  const lobe = LOBES[tool.lobe]
  return (
    <button
      type="button"
      onMouseEnter={onHover}
      onClick={() => onSelect(tool)}
      className={`group w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition ${
        active ? 'bg-white/[0.06]' : 'hover:bg-white/[0.04]'
      }`}
    >
      <span
        className="w-9 h-9 rounded-lg flex items-center justify-center text-[18px] shrink-0"
        style={{
          background: `linear-gradient(135deg, ${lobe.color}33, transparent)`,
          border: `1px solid ${lobe.color}44`,
        }}
      >
        {tool.icon}
      </span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-[13px] font-semibold text-white truncate">{tool.title}</span>
          <span
            className="text-[8px] font-mono px-1.5 py-0.5 rounded uppercase tracking-widest"
            style={{ color: lobe.color, background: `${lobe.color}15`, border: `1px solid ${lobe.color}30` }}
          >
            {lobe.label}
          </span>
        </div>
        <div className="text-[11px] text-white/45 truncate">{tool.subtitle}</div>
      </div>
      <ArrowRight className={`w-3.5 h-3.5 transition ${active ? 'text-white/85 translate-x-0.5' : 'text-white/30'}`} />
    </button>
  )
}


export default BrainCommandBar
