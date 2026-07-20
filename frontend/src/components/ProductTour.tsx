"use client"

import React, { useEffect, useState, useRef, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { ArrowLeft, ArrowRight, SkipForward } from "lucide-react"
import { cn } from "@/lib/utils"
import { useProductTour, type TourStep } from "@/hooks/useProductTour"
import { Button } from "@/components/ui/Button"

interface ProductTourProps {
  tourId: string
  children: React.ReactNode
}

function useElementPosition(selector: string) {
  const [rect, setRect] = useState<DOMRect | null>(null)

  const update = useCallback(() => {
    const el = document.querySelector(selector)
    if (el) {
      setRect(el.getBoundingClientRect())
    }
  }, [selector])

  useEffect(() => {
    update()
    window.addEventListener("resize", update)
    window.addEventListener("scroll", update, true)
    const id = setInterval(update, 500)
    return () => {
      window.removeEventListener("resize", update)
      window.removeEventListener("scroll", update, true)
      clearInterval(id)
    }
  }, [update])

  return rect
}

function TourTooltip({
  step,
  stepIndex,
  totalSteps,
  onNext,
  onPrev,
  onSkip,
}: {
  step: TourStep
  stepIndex: number
  totalSteps: number
  onNext: () => void
  onPrev: () => void
  onSkip: () => void
}) {
  const rect = useElementPosition(step.target_selector)
  const tooltipRef = useRef<HTMLDivElement>(null)
  const [placement, setPlacement] = useState<"top" | "bottom" | "left" | "right">(
    step.placement ?? "bottom"
  )
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 })

  useEffect(() => {
    if (!rect) return
    const margin = 12
    const preferred = step.placement ?? "bottom"
    const vw = window.innerWidth
    const vh = window.innerHeight

    // Estimate tooltip size (will refine after mount)
    const tw = tooltipRef.current?.offsetWidth ?? 320
    const th = tooltipRef.current?.offsetHeight ?? 180

    let pos = { x: 0, y: 0 }
    let chosen: typeof placement = preferred

    const candidates: Array<typeof placement> = [preferred, "bottom", "top", "right", "left"]

    for (const p of candidates) {
      chosen = p
      if (p === "bottom") {
        pos.x = rect.left + rect.width / 2 - tw / 2
        pos.y = rect.bottom + margin
      } else if (p === "top") {
        pos.x = rect.left + rect.width / 2 - tw / 2
        pos.y = rect.top - th - margin
      } else if (p === "right") {
        pos.x = rect.right + margin
        pos.y = rect.top + rect.height / 2 - th / 2
      } else {
        pos.x = rect.left - tw - margin
        pos.y = rect.top + rect.height / 2 - th / 2
      }

      // Clamp to viewport
      pos.x = Math.max(8, Math.min(vw - tw - 8, pos.x))
      pos.y = Math.max(8, Math.min(vh - th - 8, pos.y))

      // If preferred fits, use it
      if (p === preferred) break
    }

    setPlacement(chosen)
    setTooltipPos(pos)
  }, [rect, step.placement])

  if (!rect) {
    // Target not found yet; still render tooltip centered so user sees something
    return (
      <div className="fixed inset-0 z-[80] flex items-center justify-center">
        <motion.div
          ref={tooltipRef}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ type: "spring", stiffness: 300, damping: 24 }}
          className={cn(
            "w-80 rounded-2xl border border-white/[0.08] bg-[#0A0E1A] shadow-2xl shadow-black/50 backdrop-blur-xl p-5"
          )}
        >
          <p className="text-white/40 text-sm">Buscando elemento...</p>
        </motion.div>
      </div>
    )
  }

  const isFirst = stepIndex === 0
  const isLast = stepIndex === totalSteps - 1

  return (
    <>
      {/* Spotlight cutout using SVG overlay */}
      <svg className="fixed inset-0 z-[78] pointer-events-none" width="100%" height="100%">
        <defs>
          <mask id="tour-spotlight-mask">
            <rect x="0" y="0" width="100%" height="100%" fill="white" />
            <rect
              x={rect.left - 6}
              y={rect.top - 6}
              width={rect.width + 12}
              height={rect.height + 12}
              rx={12}
              fill="black"
            />
          </mask>
        </defs>
        <rect
          x="0"
          y="0"
          width="100%"
          height="100%"
          fill="rgba(0,0,0,0.65)"
          mask="url(#tour-spotlight-mask)"
          style={{ pointerEvents: "auto" }}
        />
      </svg>

      {/* Highlight ring around target */}
      <motion.div
        className="fixed z-[79] rounded-xl border-2 border-brand-violet/60 pointer-events-none"
        style={{
          left: rect.left - 6,
          top: rect.top - 6,
          width: rect.width + 12,
          height: rect.height + 12,
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      />

      {/* Tooltip */}
      <motion.div
        ref={tooltipRef}
        className="fixed z-[80] w-80 rounded-2xl border border-white/[0.08] bg-[#0A0E1A] shadow-2xl shadow-black/50 backdrop-blur-xl p-5"
        style={{ left: tooltipPos.x, top: tooltipPos.y }}
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        transition={{ type: "spring", stiffness: 300, damping: 24 }}
      >
        {/* Arrow indicator */}
        <div
          className={cn(
            "absolute w-3 h-3 bg-[#0A0E1A] border-white/[0.08] rotate-45",
            placement === "bottom" && "-top-1.5 left-1/2 -translate-x-1/2 border-t border-l",
            placement === "top" && "-bottom-1.5 left-1/2 -translate-x-1/2 border-b border-r",
            placement === "right" && "-left-1.5 top-1/2 -translate-y-1/2 border-t border-l",
            placement === "left" && "-right-1.5 top-1/2 -translate-y-1/2 border-b border-r"
          )}
        />

        <div className="space-y-3">
          <div className="space-y-1">
            <h4 className="text-white font-semibold text-sm">{step.title}</h4>
            <p className="text-white/60 text-sm leading-relaxed">{step.content}</p>
          </div>

          <div className="flex items-center justify-between pt-1">
            <div className="flex items-center gap-1">
              {Array.from({ length: totalSteps }, (_, i) => (
                <div
                  key={i}
                  className={cn(
                    "h-1.5 rounded-full transition-all",
                    i === stepIndex ? "w-4 bg-brand-violet" : "w-1.5 bg-white/10"
                  )}
                />
              ))}
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={onSkip}
                className="text-xs text-white/30 hover:text-white/60 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-white/20 rounded px-1"
              >
                Saltar tour
              </button>
              {!isFirst && (
                <Button variant="ghost" size="sm" onClick={onPrev} className="h-8 px-2">
                  <ArrowLeft className="h-3.5 w-3.5" />
                  Anterior
                </Button>
              )}
              <Button size="sm" onClick={onNext} className="h-8 px-3">
                {isLast ? "Finalizar" : "Siguiente"}
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        </div>
      </motion.div>
    </>
  )
}

export function ProductTour({ tourId, children }: ProductTourProps) {
  const { currentStep, totalSteps, next, prev, skip, isActive, stepIndex } = useProductTour(tourId)

  if (!isActive || !currentStep) {
    return <>{children}</>
  }

  return (
    <>
      {children}
      <AnimatePresence>
        {currentStep && (
          <TourTooltip
            key={currentStep.id}
            step={currentStep}
            stepIndex={stepIndex}
            totalSteps={totalSteps}
            onNext={next}
            onPrev={prev}
            onSkip={skip}
          />
        )}
      </AnimatePresence>
    </>
  )
}
