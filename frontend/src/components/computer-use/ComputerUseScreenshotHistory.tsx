'use client'

import { useState, useEffect } from 'react'
import { Camera, X, ChevronLeft, ChevronRight, Layers } from 'lucide-react'

interface ScreenshotItem {
  step_number: number
  screenshot_path: string | null
  action_type: string
  reason?: string
}

interface ComputerUseScreenshotHistoryProps {
  sessionId: string
  steps: ScreenshotItem[]
  currentStep: number
  onSelectStep: (step: number) => void
}

export default function ComputerUseScreenshotHistory({
  sessionId,
  steps,
  currentStep,
  onSelectStep,
}: ComputerUseScreenshotHistoryProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(0)

  const stepsWithScreenshots = steps.filter((s) => s.screenshot_path)

  useEffect(() => {
    // Auto-scroll to current step when it changes
    if (isOpen && currentStep > 0) {
      const idx = stepsWithScreenshots.findIndex((s) => s.step_number === currentStep)
      if (idx >= 0) setSelectedIndex(idx)
    }
  }, [currentStep, isOpen, stepsWithScreenshots])

  if (stepsWithScreenshots.length === 0) return null

  const selected = stepsWithScreenshots[selectedIndex]
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
  const imageUrl = selected?.screenshot_path
    ? `${apiUrl}/api/v1/computer-use/sessions/${sessionId}/screenshots/${selected.step_number}`
    : null

  return (
    <>
      {/* Toggle button */}
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-2 px-3 py-2 bg-[#0A0E1A] hover:bg-white/[0.05] text-white/50 hover:text-white/70 rounded-xl border border-white/[0.08] transition-all text-xs"
      >
        <Layers className="w-3.5 h-3.5" />
        <span>Historial ({stepsWithScreenshots.length})</span>
      </button>

      {/* Drawer overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-end justify-center">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setIsOpen(false)}
          />
          <div className="relative w-full max-w-4xl mx-4 mb-4 bg-[#0A0E1A] border border-white/[0.08] rounded-2xl shadow-2xl overflow-hidden animate-in slide-in-from-bottom-4 duration-300">
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-3 border-b border-white/[0.06]">
              <div className="flex items-center gap-2">
                <Camera className="w-4 h-4 text-white/40" />
                <h3 className="text-sm font-semibold text-white/70">Historial de Screenshots</h3>
                <span className="text-xs text-white/30 ml-2">
                  {selectedIndex + 1} / {stepsWithScreenshots.length}
                </span>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 hover:bg-white/5 rounded-lg transition-colors"
              >
                <X className="w-4 h-4 text-white/30" />
              </button>
            </div>

            {/* Main viewer */}
            <div className="flex items-center justify-center p-4 bg-[#05070d] min-h-[300px]">
              {imageUrl ? (
                <div className="relative">
                  <img
                    src={imageUrl}
                    alt={`Paso ${selected?.step_number}`}
                    className="max-h-[50vh] rounded-lg shadow-lg object-contain"
                  />
                  <div className="absolute top-2 left-2 px-2 py-1 bg-black/60 rounded text-[10px] text-white/80 font-mono">
                    Paso {selected?.step_number}
                  </div>
                  <div className="absolute bottom-2 left-2 right-2 px-2 py-1.5 bg-black/60 rounded text-[10px] text-white/60 truncate">
                    {selected?.reason || selected?.action_type}
                  </div>
                </div>
              ) : (
                <p className="text-sm text-white/20">No hay screenshot</p>
              )}

              {/* Navigation arrows */}
              {stepsWithScreenshots.length > 1 && (
                <>
                  <button
                    onClick={() => setSelectedIndex(Math.max(0, selectedIndex - 1))}
                    disabled={selectedIndex === 0}
                    className="absolute left-4 p-2 bg-black/40 hover:bg-black/60 text-white/70 rounded-full transition-all disabled:opacity-20"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => setSelectedIndex(Math.min(stepsWithScreenshots.length - 1, selectedIndex + 1))}
                    disabled={selectedIndex === stepsWithScreenshots.length - 1}
                    className="absolute right-4 p-2 bg-black/40 hover:bg-black/60 text-white/70 rounded-full transition-all disabled:opacity-20"
                  >
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </>
              )}
            </div>

            {/* Thumbnails strip */}
            <div className="flex gap-2 p-3 overflow-x-auto no-scrollbar border-t border-white/[0.06]">
              {stepsWithScreenshots.map((step, idx) => (
                <button
                  key={step.step_number}
                  onClick={() => {
                    setSelectedIndex(idx)
                    onSelectStep(step.step_number)
                  }}
                  className={`relative shrink-0 w-20 h-14 rounded-lg overflow-hidden border-2 transition-all ${
                    idx === selectedIndex
                      ? 'border-brand-orange'
                      : 'border-transparent hover:border-white/20'
                  }`}
                >
                  <img
                    src={`${apiUrl}/api/v1/computer-use/sessions/${sessionId}/screenshots/${step.step_number}`}
                    alt={`Paso ${step.step_number}`}
                    className="w-full h-full object-cover"
                    loading="lazy"
                  />
                  <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                    <span className="text-[9px] text-white/80 font-mono">#{step.step_number}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
