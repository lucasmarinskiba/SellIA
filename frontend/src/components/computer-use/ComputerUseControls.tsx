'use client'

import { Play, Pause, Square, Loader2 } from 'lucide-react'

interface ComputerUseControlsProps {
  status: string
  onPause: () => void
  onResume: () => void
  onStop: () => void
}

export default function ComputerUseControls({ status, onPause, onResume, onStop }: ComputerUseControlsProps) {
  const isRunning = status === 'running'
  const isPaused = status === 'paused'
  const isActive = isRunning || isPaused

  return (
    <div className="flex items-center gap-2">
      {isRunning ? (
        <button
          onClick={onPause}
          className="flex items-center gap-2 px-4 py-2.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 rounded-xl border border-amber-500/20 transition-all text-sm font-medium"
        >
          <Pause className="w-4 h-4" />
          Pausar
        </button>
      ) : isPaused ? (
        <button
          onClick={onResume}
          className="flex items-center gap-2 px-4 py-2.5 bg-green-500/10 hover:bg-green-500/20 text-green-400 rounded-xl border border-green-500/20 transition-all text-sm font-medium"
        >
          <Play className="w-4 h-4" />
          Reanudar
        </button>
      ) : (
        <div className="flex items-center gap-2 px-4 py-2.5 bg-white/5 text-white/30 rounded-xl border border-white/10 text-sm font-medium">
          <Loader2 className="w-4 h-4 animate-spin" />
          {status === 'pending' ? 'Iniciando...' : status === 'completed' ? 'Completado' : status === 'failed' ? 'Fallido' : 'Detenido'}
        </div>
      )}

      {isActive && (
        <button
          onClick={onStop}
          className="flex items-center gap-2 px-4 py-2.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-xl border border-red-500/20 transition-all text-sm font-medium"
        >
          <Square className="w-4 h-4" />
          Detener
        </button>
      )}
    </div>
  )
}
