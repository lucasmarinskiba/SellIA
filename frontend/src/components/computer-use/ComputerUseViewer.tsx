'use client'

import { useState, useEffect } from 'react'
import { Monitor, Crosshair } from 'lucide-react'

interface ComputerUseViewerProps {
  imageBase64: string | null
  step: number
  url: string
  lastAction?: {
    action_type: string
    params: Record<string, any>
    reason: string
    step: number
  } | null
}

export default function ComputerUseViewer({ imageBase64, step, url, lastAction }: ComputerUseViewerProps) {
  const [cursorPos, setCursorPos] = useState<{ x: number; y: number } | null>(null)
  const [showCursor, setShowCursor] = useState(false)

  useEffect(() => {
    if (lastAction && (lastAction.action_type === 'click' || lastAction.action_type === 'double_click' || lastAction.action_type === 'right_click')) {
      const x = lastAction.params.x
      const y = lastAction.params.y
      if (typeof x === 'number' && typeof y === 'number') {
        setCursorPos({ x, y })
        setShowCursor(true)
        const timer = setTimeout(() => setShowCursor(false), 1500)
        return () => clearTimeout(timer)
      }
    }
  }, [lastAction])

  return (
    <div className="flex flex-col h-full bg-[#0A0E1A] rounded-2xl border border-white/[0.08] overflow-hidden">
      {/* URL Bar */}
      <div className="flex items-center gap-3 px-4 py-2.5 bg-[#070a14] border-b border-white/[0.06]">
        <Monitor className="w-4 h-4 text-white/30 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-xs text-white/40 truncate font-mono">{url || 'about:blank'}</p>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-green-500/80" />
          <span className="text-[10px] text-white/30">Paso {step}</span>
        </div>
      </div>

      {/* Screenshot */}
      <div className="flex-1 relative overflow-hidden bg-[#05070d]">
        {imageBase64 ? (
          <div className="relative w-full h-full flex items-center justify-center p-4">
            <img
              src={`data:image/jpeg;base64,${imageBase64}`}
              alt={`Screenshot paso ${step}`}
              className="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
              style={{ imageRendering: 'auto' }}
            />
            {/* Cursor overlay */}
            {showCursor && cursorPos && (
              <div
                className="absolute pointer-events-none transition-all duration-300"
                style={{
                  left: `${cursorPos.x}px`,
                  top: `${cursorPos.y}px`,
                  transform: 'translate(-50%, -50%)',
                }}
              >
                <Crosshair className="w-6 h-6 text-brand-orange drop-shadow-lg animate-pulse" />
                <div className="absolute -bottom-5 left-1/2 -translate-x-1/2 whitespace-nowrap">
                  <span className="text-[9px] px-1.5 py-0.5 bg-brand-orange/90 text-white rounded">
                    {lastAction?.action_type}
                  </span>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center gap-3">
            <Monitor className="w-12 h-12 text-white/10" />
            <p className="text-sm text-white/20">Esperando screenshot...</p>
          </div>
        )}
      </div>
    </div>
  )
}
