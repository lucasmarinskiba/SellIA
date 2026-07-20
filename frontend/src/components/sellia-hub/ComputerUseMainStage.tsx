'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Play, Pause, Square, Eye, Maximize2, MousePointer2, Bot, Loader2 } from 'lucide-react'
import { useComputerUseWebSocket, CUSessionStatus } from '@/hooks/useComputerUseWebSocket'
import Image from 'next/image'

interface ComputerUseMainStageProps {
  sessionId: string | null
  onSessionStatusChange?: (status: CUSessionStatus) => void
}

export default function ComputerUseMainStage({ sessionId, onSessionStatusChange }: ComputerUseMainStageProps) {
  const { isConnected, status, lastScreenshot, steps, sendCommand } = useComputerUseWebSocket({
    sessionId,
    onStatusChange: onSessionStatusChange,
  })

  const [isFullscreen, setIsFullscreen] = useState(false)
  const lastStep = steps[steps.length - 1]

  const handleControl = (cmd: 'pause' | 'resume' | 'stop') => {
    sendCommand(cmd)
  }

  return (
    <motion.div
      layout
      className={`relative bg-[#0A0E1A] border border-white/[0.08] rounded-2xl overflow-hidden transition-all ${
        isFullscreen ? 'fixed inset-4 z-50' : ''
      }`}
    >
      {/* Browser chrome */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-white/[0.02] border-b border-white/[0.06]">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500/60" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
            <div className="w-3 h-3 rounded-full bg-emerald-500/60" />
          </div>
          <span className="text-xs text-white/40 ml-2 font-mono">
            {sessionId ? `Chrome — SellIA CUA · ${sessionId.slice(0, 8)}` : 'Sin sesión activa'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <ConnectionBadge connected={isConnected} />
          <button
            onClick={() => setIsFullscreen(f => !f)}
            className="p-1 hover:bg-white/5 rounded transition-colors"
          >
            <Maximize2 className="w-3.5 h-3.5 text-white/30 hover:text-white/60" />
          </button>
        </div>
      </div>

      {/* Viewport */}
      <div className="relative aspect-[16/9] bg-gradient-to-br from-[#0F1729] to-[#0A0E1A] overflow-hidden">
        {/* Grid background */}
        <div
          className="absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage:
              'linear-gradient(rgba(255,107,53,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,107,53,0.5) 1px, transparent 1px)',
            backgroundSize: '40px 40px',
          }}
        />

        {/* Scanline effect */}
        <div
          className="absolute inset-0 pointer-events-none opacity-[0.03]"
          style={{
            backgroundImage: 'linear-gradient(transparent 50%, rgba(0,0,0,0.5) 50%)',
            backgroundSize: '100% 4px',
          }}
        />

        {/* Screenshot */}
        {lastScreenshot ? (
          <div className="absolute inset-0 p-3">
            <div className="relative w-full h-full rounded-xl overflow-hidden border border-white/[0.06]">
              <img
                src={lastScreenshot}
                alt="Computer Use Screenshot"
                className="w-full h-full object-contain bg-black"
              />
              {/* Overlay when paused/stopped */}
              {status !== 'running' && (
                <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center">
                  <div className="text-center">
                    {status === 'paused' && <Pause className="w-10 h-10 text-amber-400 mx-auto mb-2" />}
                    {status === 'completed' && <Square className="w-10 h-10 text-emerald-400 mx-auto mb-2" />}
                    {status === 'failed' && <Square className="w-10 h-10 text-red-400 mx-auto mb-2" />}
                    <p className="text-sm text-white font-medium capitalize">{status}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              {sessionId ? (
                <>
                  <Loader2 className="w-8 h-8 text-brand-orange animate-spin mx-auto mb-3" />
                  <p className="text-sm text-white/40">Conectando a sesión...</p>
                </>
              ) : (
                <>
                  <Bot className="w-10 h-10 text-white/10 mx-auto mb-3" />
                  <p className="text-sm text-white/30">Seleccioná una sesión para ver en vivo</p>
                </>
              )}
            </div>
          </div>
        )}

        {/* Animated virtual cursor */}
        <AnimatePresence>
          {status === 'running' && lastStep?.action_params?.x !== undefined && (
            <motion.div
              className="absolute z-20 pointer-events-none"
              initial={{ opacity: 0 }}
              animate={{
                opacity: 1,
                left: `${lastStep.action_params.x}%`,
                top: `${lastStep.action_params.y}%`,
              }}
              transition={{ type: 'spring', damping: 20, stiffness: 100 }}
            >
              <MousePointer2 className="w-5 h-5 text-amber-400 drop-shadow-lg" fill="currentColor" />
              <div className="absolute -top-1 -left-1 w-7 h-7 rounded-full bg-amber-400/20 animate-ping" />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Controls */}
      {sessionId && (
        <div className="flex items-center justify-between px-4 py-2.5 bg-white/[0.02] border-t border-white/[0.06]">
          <div className="flex items-center gap-2">
            {status === 'running' ? (
              <button
                onClick={() => handleControl('pause')}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/15 border border-amber-500/30 text-amber-400 text-xs font-medium hover:bg-amber-500/20 transition-all"
              >
                <Pause className="w-3.5 h-3.5" /> Pausar
              </button>
            ) : (
              <button
                onClick={() => handleControl('resume')}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-xs font-medium hover:bg-emerald-500/20 transition-all"
              >
                <Play className="w-3.5 h-3.5" /> Reanudar
              </button>
            )}
            <button
              onClick={() => handleControl('stop')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-white/60 text-xs font-medium hover:bg-red-500/10 hover:text-red-400 hover:border-red-500/30 transition-all"
            >
              <Square className="w-3.5 h-3.5" /> Detener
            </button>
          </div>
          <div className="text-[10px] text-white/30 font-mono">
            {steps.length} pasos · {status}
          </div>
        </div>
      )}
    </motion.div>
  )
}

function ConnectionBadge({ connected }: { connected: boolean }) {
  return (
    <div className="flex items-center gap-1.5">
      <div className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'}`} />
      <span className="text-[10px] text-white/40">{connected ? 'En vivo' : 'Desconectado'}</span>
    </div>
  )
}
