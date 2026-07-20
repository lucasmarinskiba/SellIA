'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { ThumbsUp, ThumbsDown, Crown, AlertTriangle, CheckCircle2 } from 'lucide-react'

export interface PendingAction {
  id: string
  action: string
  reason: string
  confidence: number
  impact: number
  type: 'discount' | 'upgrade' | 'refund' | 'general'
  icon?: string
}

interface SellIAActionQueueProps {
  actions: PendingAction[]
  onApprove?: (id: string) => void
  onReject?: (id: string) => void
}

const TYPE_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  discount: { label: 'Descuento', color: '#f59e0b', bg: 'bg-amber-500/10 border-amber-500/20' },
  upgrade: { label: 'Upgrade', color: '#3b82f6', bg: 'bg-blue-500/10 border-blue-500/20' },
  refund: { label: 'Reembolso', color: '#ef4444', bg: 'bg-red-500/10 border-red-500/20' },
  general: { label: 'Acción', color: '#a855f7', bg: 'bg-purple-500/10 border-purple-500/20' },
}

export default function SellIAActionQueue({ actions, onApprove, onReject }: SellIAActionQueueProps) {
  if (actions.length === 0) {
    return (
      <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl p-5 text-center">
        <CheckCircle2 className="w-6 h-6 text-emerald-400/40 mx-auto mb-2" />
        <p className="text-xs text-white/30">No hay acciones pendientes de aprobación</p>
      </div>
    )
  }

  return (
    <div className="bg-gradient-to-br from-amber-500/[0.04] to-transparent border border-amber-500/20 rounded-2xl overflow-hidden">
      <div className="px-5 py-4 border-b border-amber-500/15 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center">
            <Crown className="w-4 h-4 text-amber-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">La IA necesita tu aprobación</h3>
            <p className="text-[11px] text-white/40">Decisiones de alto impacto escaladas</p>
          </div>
        </div>
        <span className="text-[10px] px-2 py-1 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30 font-medium">
          {actions.length} pendientes
        </span>
      </div>

      <div className="p-4 space-y-2.5 max-h-[300px] overflow-y-auto">
        <AnimatePresence>
          {actions.map((action) => {
            const cfg = TYPE_CONFIG[action.type] || TYPE_CONFIG.general

            return (
              <motion.div
                key={action.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.05] transition-colors"
              >
                <div className="text-2xl shrink-0">{action.icon || '💡'}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <p className="text-sm text-white/90 font-medium truncate">{action.action}</p>
                    <span
                      className="text-[9px] px-1.5 py-0.5 rounded-md font-medium shrink-0"
                      style={{ background: `${cfg.color}20`, color: cfg.color }}
                    >
                      {cfg.label}
                    </span>
                  </div>
                  <p className="text-xs text-white/40 mt-0.5">{action.reason}</p>
                  <div className="flex items-center gap-3 mt-1.5">
                    <span className="text-[10px] text-white/50">
                      Confianza: <span className="text-white/80 font-semibold">{action.confidence}%</span>
                    </span>
                    <span className={`text-[10px] font-semibold ${action.impact > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      Impacto: {action.impact > 0 ? '+' : ''}${Math.abs(action.impact).toLocaleString()}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  <button
                    onClick={() => onApprove?.(action.id)}
                    className="w-9 h-9 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/25 flex items-center justify-center transition-all active:scale-95"
                  >
                    <ThumbsUp className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => onReject?.(action.id)}
                    className="w-9 h-9 rounded-xl bg-red-500/15 border border-red-500/30 text-red-400 hover:bg-red-500/25 flex items-center justify-center transition-all active:scale-95"
                  >
                    <ThumbsDown className="w-4 h-4" />
                  </button>
                </div>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>
    </div>
  )
}
