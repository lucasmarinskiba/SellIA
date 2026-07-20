'use client'

/**
 * COMPUTER USE LAUNCHER
 *
 * Floating bottom-right dock + full-page launcher modal.
 *
 * Dock:
 *   - Pulsing green dot when ≥1 CUA session running
 *   - Click → open modal listing live sessions + scenarios
 *
 * Modal:
 *   - Live sessions list (mock data)
 *   - "Lanzar nuevo escenario" cards (sales-focused presets · checkout, ML listing, IG ads)
 *   - CTA: open ComputerUseMainStage anchor in the shell
 */

import { useEffect, useState } from 'react'
import { MonitorCheck, X, Play, Sparkles, Workflow, ShoppingCart, Megaphone, Briefcase, ArrowRight } from 'lucide-react'


interface ComputerUseLauncherProps {
  open: boolean
  onClose: () => void
  onJump: (componentId: string) => void
}


interface CUSession {
  id: string
  scenario: string
  step: string
  progress: number
  color: string
}


const MOCK_SESSIONS: CUSession[] = [
  { id: 'cua-1', scenario: 'Publicar 12 listings en ML',          step: 'completando ficha #7',         progress: 58, color: '#22d3ee' },
  { id: 'cua-2', scenario: 'Recuperar carritos · Shopify',         step: 'enviando WhatsApp a 4 leads',  progress: 78, color: '#10b981' },
  { id: 'cua-3', scenario: 'Conciliar pagos · banco + Mercado Pago', step: 'matching transactions',     progress: 33, color: '#a855f7' },
]


const SCENARIOS: Array<{
  id: string
  title: string
  subtitle: string
  icon: React.ComponentType<{ className?: string }>
  color: string
}> = [
  { id: 'checkout-amazon',      title: 'Checkout Amazon',          subtitle: 'Completar compra + tracking + factura', icon: ShoppingCart, color: '#f59e0b' },
  { id: 'list-mercadolibre',    title: 'Listar Mercado Libre',     subtitle: 'Foto, copy, precio, categorías',         icon: Workflow,     color: '#22d3ee' },
  { id: 'launch-meta-ad',       title: 'Lanzar Ad en Meta',        subtitle: 'Audiencia · creativo · presupuesto',     icon: Megaphone,    color: '#ec4899' },
  { id: 'linkedin-outbound',    title: 'Prospectar LinkedIn',      subtitle: 'Connect requests · followup secuencia',  icon: Briefcase,    color: '#10b981' },
]


export const ComputerUseLauncher = ({ open, onClose, onJump }: ComputerUseLauncherProps): React.JSX.Element | null => {
  const [tab, setTab] = useState<'live' | 'new'>('live')

  useEffect(() => {
    if (open) setTab('live')
  }, [open])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-[115] flex items-center justify-center px-4"
      onClick={onClose}
    >
      <div className="absolute inset-0 bg-black/65 backdrop-blur-md" />

      <div
        onClick={(e) => e.stopPropagation()}
        className="relative w-full max-w-3xl rounded-xl border overflow-hidden"
        style={{
          borderColor: 'rgba(211,255,58,0.3)',
          background: 'linear-gradient(180deg, #0f1219 0%, #0a0c11 100%)',
          boxShadow: '0 80px 200px -50px rgba(0,0,0,0.95), inset 0 1px 0 rgba(255,255,255,0.04), 0 0 0 1px rgba(211,255,58,0.08)',
        }}
      >
        <header className="flex items-center justify-between px-5 py-4 border-b border-white/10">
          <div className="flex items-center gap-2.5">
            <span className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#d3ff3a] to-[#d3ff3a] flex items-center justify-center shadow-[0_0_24px_-4px_rgba(34,211,238,0.6)]">
              <MonitorCheck className="w-4 h-4 text-[#03050e]" />
            </span>
            <div className="flex flex-col leading-tight">
              <h3 className="text-white text-[14px] font-bold tracking-wider uppercase" style={{ fontFamily: 'Manrope, ui-sans-serif' }}>
                Computer Use
              </h3>
              <span className="text-[10px] font-mono" style={{ color: 'rgba(211,255,58,0.7)' }}>agente operando navegador · sandbox aislado</span>
            </div>
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-full border border-white/15 bg-white/[0.04] hover:bg-white/[0.1] flex items-center justify-center text-white/70" aria-label="Cerrar">
            <X className="w-4 h-4" />
          </button>
        </header>

        <div className="flex gap-1 px-5 pt-3">
          <TabButton active={tab === 'live'} onClick={() => setTab('live')} label={`En vivo · ${MOCK_SESSIONS.length}`} color="#22d3ee" />
          <TabButton active={tab === 'new'} onClick={() => setTab('new')} label="Lanzar nuevo" color="#ec4899" />
        </div>

        <div className="px-5 py-4 max-h-[60vh] overflow-y-auto">
          {tab === 'live' && (
            <div className="space-y-2">
              {MOCK_SESSIONS.map((s) => (
                <SessionRow key={s.id} session={s} onView={() => { onJump('lobe-convert-cua-main'); onClose() }} />
              ))}
              <button
                type="button"
                onClick={() => { onJump('lobe-convert-cua-main'); onClose() }}
                className="w-full mt-3 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border transition text-[12px] font-bold tracking-widest uppercase"
                style={{ borderColor: 'rgba(211,255,58,0.4)', background: 'rgba(211,255,58,0.08)', color: '#d3ff3a' }}
              >
                Ir a la mesa principal de Computer Use <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
          {tab === 'new' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {SCENARIOS.map((sc) => (
                <ScenarioCard key={sc.id} {...sc} onLaunch={() => { onJump('lobe-convert-cua-main'); onClose() }} />
              ))}
              <div className="sm:col-span-2 rounded-xl border border-dashed border-white/15 bg-white/[0.02] p-4 flex items-center gap-3">
                <Sparkles className="w-4 h-4 text-amber-300" />
                <span className="text-[11.5px] text-white/65">
                  ¿No ves tu escenario? Escribilo en la barra de búsqueda · SellIA arma el plan y lanza el sandbox.
                </span>
              </div>
            </div>
          )}
        </div>

        <footer className="px-5 py-3 border-t border-white/10 bg-black/30 flex items-center justify-between text-[10px] font-mono text-white/45">
          <span>Anthropic Claude · `computer-use-2025-01-24` beta · sandbox E2B/Browserbase</span>
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            sandboxes saludables
          </span>
        </footer>
      </div>
    </div>
  )
}


const TabButton = ({
  active, onClick, label, color,
}: { active: boolean; onClick: () => void; label: string; color: string }): React.JSX.Element => (
  <button
    type="button"
    onClick={onClick}
    className={`text-[10px] font-mono tracking-[0.25em] uppercase px-3 py-1.5 rounded-md border ${
      active ? 'text-white' : 'text-white/45 hover:text-white/70'
    }`}
    style={{
      borderColor: active ? `${color}88` : 'rgba(255,255,255,0.1)',
      background: active ? `${color}1a` : 'transparent',
    }}
  >
    {label}
  </button>
)


const SessionRow = ({ session, onView }: { session: CUSession; onView: () => void }): React.JSX.Element => (
  <div className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 flex items-center gap-3">
    <span className="relative inline-flex w-2.5 h-2.5">
      <span className="absolute inset-0 rounded-full animate-ping" style={{ background: session.color, opacity: 0.5 }} />
      <span className="relative w-2.5 h-2.5 rounded-full" style={{ background: session.color, boxShadow: `0 0 10px ${session.color}` }} />
    </span>
    <div className="flex-1 min-w-0">
      <div className="text-[12.5px] font-semibold text-white truncate">{session.scenario}</div>
      <div className="text-[10.5px] text-white/45 truncate">{session.step}</div>
      <div className="mt-1.5 h-1 rounded-full bg-white/8 overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${session.progress}%`, background: `linear-gradient(90deg, ${session.color}, white)` }}
        />
      </div>
    </div>
    <button
      type="button"
      onClick={onView}
      className="px-2.5 py-1.5 rounded-md text-[10px] font-bold tracking-widest uppercase border border-white/15 hover:bg-white/[0.08] text-white/75 inline-flex items-center gap-1"
    >
      ver <ArrowRight className="w-3 h-3" />
    </button>
  </div>
)


const ScenarioCard = ({
  id, title, subtitle, icon: Icon, color, onLaunch,
}: typeof SCENARIOS[number] & { onLaunch: () => void }): React.JSX.Element => (
  <button
    type="button"
    onClick={onLaunch}
    className="group rounded-xl border bg-gradient-to-br from-white/[0.04] to-transparent p-4 text-left transition hover:translate-y-[-2px]"
    style={{ borderColor: `${color}55` }}
    aria-label={`Lanzar escenario ${title}`}
  >
    <div className="flex items-center justify-between mb-2">
      <span
        className="w-9 h-9 rounded-lg flex items-center justify-center"
        style={{ background: `${color}22`, border: `1px solid ${color}55`, color }}
      >
        <Icon className="w-4 h-4" />
      </span>
      <Play className="w-3.5 h-3.5 text-white/40 group-hover:text-white/80" />
    </div>
    <div className="text-[13px] font-bold text-white leading-tight">{title}</div>
    <div className="text-[10.5px] text-white/45 leading-snug mt-0.5">{subtitle}</div>
    <div className="text-[9px] font-mono tracking-widest uppercase mt-2 inline-flex items-center gap-1" style={{ color }}>
      lanzar sandbox <ArrowRight className="w-3 h-3" />
    </div>
  </button>
)


/* ─────────────────────  floating dock button  ───────────────── */


export const ComputerUseDock = (
  { liveCount, onClick }: { liveCount: number; onClick: () => void },
): React.JSX.Element => (
  <button
    type="button"
    onClick={onClick}
    className="fixed bottom-6 right-6 z-40 group flex items-center gap-3 rounded-lg border px-4 py-3"
    style={{ borderColor: 'rgba(211,255,58,0.4)', background: 'rgba(8,9,12,0.85)', backdropFilter: 'blur(20px)', boxShadow: '0 30px 80px -20px rgba(211,255,58,0.35)' }}
    aria-label="Abrir Computer Use"
  >
    <span className="relative inline-flex w-9 h-9 rounded-xl items-center justify-center bg-gradient-to-br from-[#d3ff3a] to-[#d3ff3a]">
      <MonitorCheck className="w-4 h-4 text-[#03050e]" />
      {liveCount > 0 && (
        <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-emerald-400 text-[#03050e] text-[9px] font-bold flex items-center justify-center">
          {liveCount}
        </span>
      )}
    </span>
    <span className="hidden md:flex flex-col leading-tight">
      <span className="text-[11px] font-bold tracking-wider uppercase" style={{ color: '#d3ff3a' }}>Computer Use</span>
      <span className="text-[9px] font-mono" style={{ color: 'rgba(211,255,58,0.7)' }}>
        {liveCount > 0 ? `${liveCount} sandbox vivo · ver` : 'lanzar nuevo agente'}
      </span>
    </span>
  </button>
)


export default ComputerUseLauncher
