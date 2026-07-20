"use client"

import { useState, useCallback, useEffect } from "react"
import { Button } from "@/components/ui/Button"
import { Play, Pause, SkipBack, SkipForward, ChevronLeft, ChevronRight, X } from "lucide-react"

interface ReplayStep {
  step_number: number
  screenshot_url: string
  action_type: string
  action_params: Record<string, any>
  reason?: string
  execution_result?: string
  execution_ms?: number
  annotations?: Array<{
    id: string
    content: string
    x_coordinate?: number
    y_coordinate?: number
    color: string
  }>
}

interface Props {
  steps: ReplayStep[]
  task_description: string
  onClose: () => void
}

export default function ComputerUseReplay({ steps, task_description, onClose }: Props) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackSpeed, setPlaybackSpeed] = useState(1)

  const currentStep = steps[currentIndex]

  const goTo = useCallback((index: number) => {
    setCurrentIndex(Math.max(0, Math.min(index, steps.length - 1)))
  }, [steps.length])

  const togglePlay = useCallback(() => {
    setIsPlaying(prev => !prev)
  }, [])

  useEffect(() => {
    if (!isPlaying) return
    const interval = setInterval(() => {
      setCurrentIndex(prev => {
        if (prev >= steps.length - 1) {
          setIsPlaying(false)
          return prev
        }
        return prev + 1
      })
    }, 2000 / playbackSpeed)
    return () => clearInterval(interval)
  }, [isPlaying, steps.length, playbackSpeed])

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") goTo(currentIndex + 1)
      if (e.key === "ArrowLeft") goTo(currentIndex - 1)
      if (e.key === " ") { e.preventDefault(); togglePlay() }
      if (e.key === "Escape") onClose()
    }
    window.addEventListener("keydown", handleKey)
    return () => window.removeEventListener("keydown", handleKey)
  }, [currentIndex, goTo, togglePlay, onClose])

  if (!currentStep) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/90 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gray-900 border-b border-gray-800">
        <div>
          <h2 className="text-white font-semibold text-sm">🎬 Replay — {task_description}</h2>
          <p className="text-gray-400 text-xs">Paso {currentIndex + 1} de {steps.length}</p>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose} className="text-white hover:bg-gray-800">
          <X className="w-4 h-4" />
        </Button>
      </div>

      {/* Main viewer */}
      <div className="flex-1 flex overflow-hidden">
        {/* Screenshot */}
        <div className="flex-1 flex items-center justify-center p-4 relative">
          <img
            src={currentStep.screenshot_url}
            alt={`Step ${currentStep.step_number}`}
            className="max-w-full max-h-full rounded-lg border border-gray-700"
          />
          {/* Annotation markers */}
          {currentStep.annotations?.map(ann => (
            ann.x_coordinate !== null && ann.y_coordinate !== null && (
              <div
                key={ann.id}
                className="absolute w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white cursor-pointer animate-pulse"
                style={{
                  left: `${ann.x_coordinate}px`,
                  top: `${ann.y_coordinate}px`,
                  backgroundColor: ann.color,
                }}
                title={ann.content}
              >
                💬
              </div>
            )
          ))}
        </div>

        {/* Sidebar info */}
        <div className="w-80 bg-gray-900 border-l border-gray-800 p-4 overflow-y-auto">
          <div className="space-y-4">
            <div className="bg-gray-800 rounded-lg p-3">
              <span className="text-xs text-gray-400 uppercase tracking-wider">Acción</span>
              <p className="text-white font-mono text-sm mt-1">{currentStep.action_type}</p>
            </div>
            {currentStep.reason && (
              <div className="bg-gray-800 rounded-lg p-3">
                <span className="text-xs text-gray-400 uppercase tracking-wider">Razón</span>
                <p className="text-gray-300 text-sm mt-1">{currentStep.reason}</p>
              </div>
            )}
            {Object.keys(currentStep.action_params).length > 0 && (
              <div className="bg-gray-800 rounded-lg p-3">
                <span className="text-xs text-gray-400 uppercase tracking-wider">Parámetros</span>
                <pre className="text-gray-300 text-xs mt-1 overflow-x-auto">
                  {JSON.stringify(currentStep.action_params, null, 2)}
                </pre>
              </div>
            )}
            {currentStep.execution_result && (
              <div className="bg-gray-800 rounded-lg p-3">
                <span className="text-xs text-gray-400 uppercase tracking-wider">Resultado</span>
                <p className={`text-sm mt-1 ${currentStep.execution_result === "success" ? "text-green-400" : "text-red-400"}`}>
                  {currentStep.execution_result}
                </p>
              </div>
            )}
            {currentStep.annotations && currentStep.annotations.length > 0 && (
              <div className="bg-gray-800 rounded-lg p-3">
                <span className="text-xs text-gray-400 uppercase tracking-wider">Anotaciones</span>
                <div className="space-y-2 mt-2">
                  {currentStep.annotations.map(ann => (
                    <div key={ann.id} className="flex items-start gap-2">
                      <div className="w-3 h-3 rounded-full mt-1 shrink-0" style={{ backgroundColor: ann.color }} />
                      <p className="text-gray-300 text-xs">{ann.content}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-gray-900 border-t border-gray-800 px-4 py-3">
        <div className="flex items-center justify-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => goTo(0)} className="text-gray-400 hover:text-white">
            <SkipBack className="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="sm" onClick={() => goTo(currentIndex - 1)} className="text-gray-400 hover:text-white">
            <ChevronLeft className="w-5 h-5" />
          </Button>
          <Button onClick={togglePlay} className="bg-blue-600 hover:bg-blue-700 text-white px-6">
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </Button>
          <Button variant="ghost" size="sm" onClick={() => goTo(currentIndex + 1)} className="text-gray-400 hover:text-white">
            <ChevronRight className="w-5 h-5" />
          </Button>
          <Button variant="ghost" size="sm" onClick={() => goTo(steps.length - 1)} className="text-gray-400 hover:text-white">
            <SkipForward className="w-4 h-4" />
          </Button>
        </div>
        {/* Progress bar */}
        <div className="mt-3 flex items-center gap-3">
          <span className="text-gray-400 text-xs w-8">{currentIndex + 1}</span>
          <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-300"
              style={{ width: `${((currentIndex + 1) / steps.length) * 100}%` }}
            />
          </div>
          <span className="text-gray-400 text-xs w-8 text-right">{steps.length}</span>
        </div>
        {/* Speed */}
        <div className="mt-2 flex justify-center gap-2">
          {[0.5, 1, 2, 4].map(speed => (
            <button
              key={speed}
              onClick={() => setPlaybackSpeed(speed)}
              className={`text-xs px-2 py-1 rounded ${playbackSpeed === speed ? "bg-blue-600 text-white" : "text-gray-400 hover:text-white"}`}
            >
              {speed}x
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
