'use client'

import { motion } from 'framer-motion'
import { Play, Pause, Clock, Plus, ExternalLink } from 'lucide-react'
import { CUSessionStatus } from '@/hooks/useComputerUseWebSocket'

export interface CUSessionMini {
  id: string
  task: string
  browser: string
  steps: number
  status: CUSessionStatus
  url?: string
  color?: string
}

interface ComputerUseSessionCarouselProps {
  sessions: CUSessionMini[]
  activeSessionId: string | null
  onSelectSession: (id: string) => void
  onCreateSession?: () => void
}

const STATUS_CONFIG: Record<CUSessionStatus, { label: string; dot: string; bg: string }> = {
  running: { label: 'En vivo', dot: 'bg-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
  paused: { label: 'Pausada', dot: 'bg-amber-400', bg: 'bg-amber-500/10 border-amber-500/20' },
  pending: { label: 'Pendiente', dot: 'bg-white/30', bg: 'bg-white/5 border-white/10' },
  completed: { label: 'Completada', dot: 'bg-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' },
  failed: { label: 'Fallida', dot: 'bg-red-400', bg: 'bg-red-500/10 border-red-500/20' },
  stopped: { label: 'Detenida', dot: 'bg-white/20', bg: 'bg-white/5 border-white/10' },
}

const BROWSER_COLORS: Record<string, string> = {
  Chromium: '#3b82f6',
  Firefox: '#ec4899',
  WebKit: '#f59e0b',
}

export default function ComputerUseSessionCarousel({
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateSession,
}: ComputerUseSessionCarouselProps) {
  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-white">Sesiones paralelas</h3>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/25 font-medium">
            {sessions.filter(s => s.status === 'running').length} corriendo
          </span>
        </div>
        <button
          onClick={onCreateSession}
          className="text-xs text-brand-orange hover:text-brand-orange/80 flex items-center gap-1 transition-colors"
        >
          <Plus className="w-3.5 h-3.5" /> Nueva sesión
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {sessions.map((s, i) => {
          const cfg = STATUS_CONFIG[s.status]
          const isActive = activeSessionId === s.id
          const browserColor = BROWSER_COLORS[s.browser] || '#a855f7'

          return (
            <motion.button
              key={s.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              onClick={() => onSelectSession(s.id)}
              className={`text-left rounded-2xl border overflow-hidden transition-all ${
                isActive ? 'ring-1 ring-brand-orange/50' : ''
              } ${cfg.bg}`}
            >
              {/* Mini browser bar */}
              <div className="flex items-center gap-1.5 px-3 py-2 bg-white/[0.02] border-b border-white/[0.06]">
                <div className="flex gap-1">
                  <div className="w-2 h-2 rounded-full bg-red-500/60" />
                  <div className="w-2 h-2 rounded-full bg-yellow-500/60" />
                  <div className="w-2 h-2 rounded-full bg-emerald-500/60" />
                </div>
                <span className="text-[9px] text-white/40 truncate flex-1 font-mono">{s.url || s.browser}</span>
              </div>

              {/* Mock viewport */}
              <div className="relative aspect-video bg-gradient-to-br from-[#0F1729] to-[#0A0E1A] p-2 overflow-hidden">
                <div className="space-y-1">
                  {[0, 1, 2, 3].map(i => (
                    <div
                      key={i}
                      className="h-2 rounded-sm"
                      style={{
                        background: `${browserColor}${15 - i * 3}`,
                        width: `${85 - i * 10}%`,
                      }}
                    />
                  ))}
                </div>
                <div className="absolute bottom-2 right-2">
                  {s.status === 'running' && (
                    <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: browserColor }} />
                  )}
                  {s.status === 'paused' && <Pause className="w-3 h-3 text-amber-400" />}
                  {s.status === 'pending' && <Clock className="w-3 h-3 text-white/40" />}
                </div>
                {isActive && (
                  <div className="absolute inset-0 bg-brand-orange/5 border-2 border-brand-orange/20 rounded-none" />
                )}
              </div>

              {/* Info */}
              <div className="p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-mono text-white/40">{s.id.slice(0, 8)}</span>
                  <span
                    className="text-[9px] px-1.5 py-0.5 rounded-md bg-white/5 text-white/40"
                    style={{ color: browserColor }}
                  >
                    {s.browser}
                  </span>
                </div>
                <p className="text-xs text-white/85 leading-snug line-clamp-2 mb-2">{s.task}</p>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-white/30">{s.steps} pasos</span>
                  <span className="text-[10px] font-medium flex items-center gap-1" style={{ color: browserColor }}>
                    <span className={`w-1 h-1 rounded-full ${cfg.dot}`} />
                    {cfg.label}
                  </span>
                </div>
              </div>
            </motion.button>
          )
        })}

        {/* Create new placeholder */}
        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: sessions.length * 0.05 }}
          onClick={onCreateSession}
          className="rounded-2xl border border-dashed border-white/10 bg-white/[0.02] hover:bg-white/[0.04] hover:border-brand-orange/30 transition-all flex flex-col items-center justify-center gap-2 aspect-[4/3] min-h-[160px]"
        >
          <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center">
            <Plus className="w-5 h-5 text-white/30" />
          </div>
          <span className="text-xs text-white/40">Nueva sesión</span>
        </motion.button>
      </div>
    </div>
  )
}
