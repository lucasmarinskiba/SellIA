"use client"

import React, { useState, useEffect, useCallback, useRef } from "react"
import { motion, AnimatePresence, useReducedMotion } from "framer-motion"
import { cn } from "@/lib/utils"

export type CelebrationLevel = 1 | 2 | 3

interface CelebrationEvent {
  id: string
  level: CelebrationLevel
  title: string
  message: string
  streakProtected?: boolean
}

interface CelebrationSystemProps {
  className?: string
}

const CONFETTI_COLORS = ["#FF6B35", "#7C3AED", "#00D4AA", "#FBBF24", "#F472B6", "#60A5FA"]

interface ConfettiPiece {
  id: number
  x: number
  color: string
  size: number
  delay: number
  duration: number
  rotation: number
}

function generateConfetti(count: number): ConfettiPiece[] {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    color: CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)],
    size: 6 + Math.random() * 8,
    delay: Math.random() * 0.5,
    duration: 2 + Math.random() * 2,
    rotation: Math.random() * 360,
  }))
}

function CelebrationConfetti({ active }: { active: boolean }) {
  const reducedMotion = useReducedMotion()
  const [confetti, setConfetti] = useState<ConfettiPiece[]>([])

  useEffect(() => {
    if (active && !reducedMotion) {
      setConfetti(generateConfetti(60))
    }
  }, [active, reducedMotion])

  if (reducedMotion || !active) return null

  return (
    <div className="fixed inset-0 pointer-events-none z-[90] overflow-hidden" aria-hidden="true">
      {confetti.map((piece) => (
        <motion.div
          key={piece.id}
          initial={{
            x: `${piece.x}vw`,
            y: -20,
            rotate: 0,
            opacity: 1,
          }}
          animate={{
            y: "110vh",
            rotate: piece.rotation,
            opacity: [1, 1, 0],
          }}
          transition={{
            duration: piece.duration,
            delay: piece.delay,
            ease: "easeIn",
          }}
          style={{
            position: "absolute",
            width: piece.size,
            height: piece.size * 0.6,
            backgroundColor: piece.color,
            borderRadius: 2,
          }}
        />
      ))}
    </div>
  )
}

function ProgressRing({
  progress,
  size = 60,
  strokeWidth = 5,
  className,
}: {
  progress: number
  size?: number
  strokeWidth?: number
  className?: string
}) {
  const reducedMotion = useReducedMotion()
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const [animatedProgress, setAnimatedProgress] = useState(0)

  useEffect(() => {
    if (reducedMotion) {
      setAnimatedProgress(progress)
      return
    }
    const timeout = setTimeout(() => setAnimatedProgress(progress), 100)
    return () => clearTimeout(timeout)
  }, [progress, reducedMotion])

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-muted/30"
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          className="text-primary"
          initial={{ strokeDashoffset: circumference }}
          animate={{
            strokeDashoffset: circumference - (animatedProgress / 100) * circumference,
          }}
          transition={
            reducedMotion
              ? { duration: 0 }
              : { type: "spring", stiffness: 60, damping: 15, duration: 1.5 }
          }
          style={{
            strokeDasharray: circumference,
          }}
        />
      </svg>
      <span className="absolute text-xs font-bold text-foreground">
        {Math.round(animatedProgress)}%
      </span>
    </div>
  )
}

export function triggerCelebration(
  level: CelebrationLevel,
  title?: string,
  message?: string,
  streakProtected?: boolean
): CelebrationEvent {
  return {
    id: Math.random().toString(36).substring(2, 9),
    level,
    title: title || (level === 1 ? "¡Bien hecho!" : level === 2 ? "¡Increíble!" : "¡LEYENDA!"),
    message:
      message ||
      (level === 1
        ? "Cada paso cuenta. Seguí así."
        : level === 2
        ? "¡Estás en racha! No pares ahora."
        : "¡Esto es histórico! Compartilo con el equipo."),
    streakProtected,
  }
}

export function CelebrationSystem({ className }: CelebrationSystemProps) {
  const [events, setEvents] = useState<CelebrationEvent[]>([])
  const reducedMotion = useReducedMotion()
  const activeEvent = events[0]

  const dismissEvent = useCallback((id: string) => {
    setEvents((prev) => prev.filter((e) => e.id !== id))
  }, [])

  // Expose a global function for triggering celebrations
  useEffect(() => {
    const handler = ((e: CustomEvent<CelebrationEvent>) => {
      setEvents((prev) => [...prev, e.detail])
    }) as EventListener

    window.addEventListener("sellia-celebration", handler)
    return () => window.removeEventListener("sellia-celebration", handler)
  }, [])

  // Auto-dismiss events
  useEffect(() => {
    if (!activeEvent) return
    const timer = setTimeout(() => dismissEvent(activeEvent.id), activeEvent.level === 3 ? 6000 : 4000)
    return () => clearTimeout(timer)
  }, [activeEvent, dismissEvent])

  return (
    <div className={className}>
      {/* Confetti layer */}
      <CelebrationConfetti active={!!activeEvent && activeEvent.level >= 2} />

      {/* Celebration modal/toast */}
      <AnimatePresence>
        {activeEvent && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[80] flex items-center justify-center bg-black/40 backdrop-blur-sm"
            role="alertdialog"
            aria-modal="true"
            aria-label="Celebración de logro"
          >
            <motion.div
              initial={reducedMotion ? { opacity: 0 } : { scale: 0.5, opacity: 0, y: 40 }}
              animate={reducedMotion ? { opacity: 1 } : { scale: 1, opacity: 1, y: 0 }}
              exit={reducedMotion ? { opacity: 0 } : { scale: 0.9, opacity: 0, y: 20 }}
              transition={{ type: "spring", stiffness: 300, damping: 24 }}
              className={cn(
                "relative mx-4 p-8 rounded-3xl border shadow-2xl max-w-sm w-full text-center",
                activeEvent.level === 3
                  ? "bg-primary/5 border-primary/20"
                  : activeEvent.level === 2
                  ? "bg-card border-border"
                  : "bg-card border-border"
              )}
            >
              {/* Flash effect for level 3 */}
              {activeEvent.level === 3 && !reducedMotion && (
                <motion.div
                  initial={{ opacity: 0.8 }}
                  animate={{ opacity: 0 }}
                  transition={{ duration: 0.6 }}
                  className="absolute inset-0 rounded-3xl bg-primary/20"
                />
              )}

              {/* Emoji */}
              <motion.div
                animate={reducedMotion ? {} : { rotate: [0, -10, 10, -10, 10, 0], scale: [1, 1.2, 1] }}
                transition={{ duration: 0.8 }}
                className="text-6xl mb-4"
              >
                {activeEvent.streakProtected
                  ? "🔥"
                  : activeEvent.level === 1
                  ? "👏"
                  : activeEvent.level === 2
                  ? "🎉"
                  : "🏆"}
              </motion.div>

              {/* Streak protected badge */}
              {activeEvent.streakProtected && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-500 text-xs font-semibold mb-3"
                >
                  <span>🔥</span> ¡Casi lo perdés! Pero no.
                </motion.div>
              )}

              <h3 className="text-xl font-bold text-foreground mb-2">{activeEvent.title}</h3>
              <p className="text-sm text-muted-foreground mb-6">{activeEvent.message}</p>

              {/* Progress ring demo */}
              {activeEvent.level >= 2 && (
                <div className="flex justify-center mb-6">
                  <ProgressRing
                    progress={activeEvent.level === 3 ? 100 : 75}
                    size={80}
                    strokeWidth={6}
                  />
                </div>
              )}

              {/* Pulse for level 1 */}
              {activeEvent.level === 1 && !reducedMotion && (
                <div className="flex justify-center mb-4">
                  <motion.div
                    animate={{ scale: [1, 1.15, 1], opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center"
                  >
                    <span className="text-2xl">✨</span>
                  </motion.div>
                </div>
              )}

              <button
                onClick={() => dismissEvent(activeEvent.id)}
                className="px-6 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              >
                ¡Genial!
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// Helper to dispatch celebration events from anywhere
export function dispatchCelebration(
  level: CelebrationLevel,
  title?: string,
  message?: string,
  streakProtected?: boolean
) {
  const event = triggerCelebration(level, title, message, streakProtected)
  window.dispatchEvent(new CustomEvent("sellia-celebration", { detail: event }))
}
