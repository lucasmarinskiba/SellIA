'use client'

import { Loader2, PauseCircle, PlayCircle, CheckCircle2, XCircle, StopCircle } from 'lucide-react'

interface ComputerUseStatusProps {
  status: string
  step: number
  totalSteps: number
  task: string
  url?: string
}

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: any }> = {
  pending: { label: 'Iniciando', color: 'text-white/40', icon: Loader2 },
  running: { label: 'Ejecutando', color: 'text-brand-teal', icon: PlayCircle },
  paused: { label: 'Pausado', color: 'text-amber-400', icon: PauseCircle },
  completed: { label: 'Completado', color: 'text-green-400', icon: CheckCircle2 },
  failed: { label: 'Fallido', color: 'text-red-400', icon: XCircle },
  stopped: { label: 'Detenido', color: 'text-white/40', icon: StopCircle },
}

export default function ComputerUseStatus({ status, step, totalSteps, task, url }: ComputerUseStatusProps) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending
  const Icon = config.icon

  return (
    <div className="bg-[#0A0E1A] rounded-2xl border border-white/[0.08] p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className={`w-4 h-4 ${config.color} ${status === 'pending' || status === 'running' ? 'animate-spin' : ''}`} />
          <span className={`text-sm font-medium ${config.color}`}>{config.label}</span>
        </div>
        <span className="text-xs text-white/30 font-mono">
          {step} / {totalSteps}
        </span>
      </div>

      {/* Progress bar */}
      <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            status === 'completed'
              ? 'bg-green-500'
              : status === 'failed'
              ? 'bg-red-500'
              : status === 'paused'
              ? 'bg-amber-500'
              : 'bg-brand-teal'
          }`}
          style={{ width: `${Math.min((step / totalSteps) * 100, 100)}%` }}
        />
      </div>

      <div className="space-y-1">
        <p className="text-xs text-white/50">
          <span className="text-white/30">Tarea:</span> {task}
        </p>
        {url && (
          <p className="text-xs text-white/30 truncate font-mono">
            {url}
          </p>
        )}
      </div>
    </div>
  )
}
