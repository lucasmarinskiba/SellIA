"use client"

import React, { useState, useEffect, useCallback } from "react"
import { motion, AnimatePresence, useReducedMotion } from "framer-motion"
import { cn } from "@/lib/utils"

interface CompanionWidgetProps {
  className?: string
}

type CompanionMood = "happy" | "worried" | "celebrating" | "sleeping" | "neutral"

interface TipItem {
  text: string
  type: "tip" | "joke" | "encouragement"
}

const TIPS: TipItem[] = [
  { text: "💡 Tip: Respondé en los primeros 5 minutos para aumentar conversiones un 391%.", type: "tip" },
  { text: "😄 ¿Sabías que el 70% de las ventas se cierran en el seguimiento? ¡Nunca dejes de seguir!", type: "tip" },
  { text: "🧠 Tu cerebro trabaja mejor con descansos. Hacé una pausa cada 90 minutos.", type: "tip" },
  { text: "🚀 La confianza se transmite: si creés en tu producto, el cliente también lo hará.", type: "encouragement" },
  { text: "☕ El café potencia tu focus... ¡pero el agua mantiene tu energía todo el día!", type: "tip" },
  { text: "🎯 Objetivo del día: una venta más que ayer. Eso es progreso.", type: "encouragement" },
  { text: "😂 ¿Por qué el vendedor llevó una escalera? ¡Para alcanzar sus metas!", type: "joke" },
  { text: "🔥 La constancia vence al talento cuando el talento no es constante.", type: "encouragement" },
  { text: "💤 Dormir bien mejora tu toma de decisiones un 30%. ¡Descansá hoy para vender mañana!", type: "tip" },
  { text: "🌱 Cada 'no' te acerca un paso más al 'sí' correcto.", type: "encouragement" },
]

const MOOD_CONFIG: Record<CompanionMood, { emoji: string; message: string; color: string }> = {
  happy: {
    emoji: "🦊",
    message: "¡Vamos! Estás a 2 ventas de subir de rango 🚀",
    color: "text-amber-500",
  },
  worried: {
    emoji: "🐱",
    message: "No hay ventas en 3 días... ¿necesitás ayuda con campañas?",
    color: "text-sky-500",
  },
  celebrating: {
    emoji: "🎉",
    message: "¡VENTA! ¡Sos una máquina! 🔥🔥🔥",
    color: "text-emerald-500",
  },
  sleeping: {
    emoji: "💤",
    message: "Descansá bien, mañana vendemos más 🌙",
    color: "text-violet-400",
  },
  neutral: {
    emoji: "🐶",
    message: "¡Hola! Tu autopiloto está trabajando por vos 🤖",
    color: "text-brand-orange",
  },
}

function getMoodFromContext(): CompanionMood {
  const hour = new Date().getHours()
  if (hour >= 23 || hour < 6) return "sleeping"
  // In a real app, we'd check sales data, streaks, etc.
  // For now, we'll randomize between happy and neutral with occasional celebration
  const rand = Math.random()
  if (rand > 0.92) return "celebrating"
  if (rand > 0.7) return "happy"
  if (rand < 0.05) return "worried"
  return "neutral"
}

export function CompanionWidget({ className }: CompanionWidgetProps) {
  const [mood, setMood] = useState<CompanionMood>("neutral")
  const [isWaving, setIsWaving] = useState(false)
  const [activeTip, setActiveTip] = useState<TipItem | null>(null)
  const [showTip, setShowTip] = useState(false)
  const reducedMotion = useReducedMotion()

  useEffect(() => {
    setMood(getMoodFromContext())
    const interval = setInterval(() => {
      setMood(getMoodFromContext())
    }, 60000) // Check mood every minute
    return () => clearInterval(interval)
  }, [])

  const handleClick = useCallback(() => {
    setIsWaving(true)
    const randomTip = TIPS[Math.floor(Math.random() * TIPS.length)]
    setActiveTip(randomTip)
    setShowTip(true)
    setTimeout(() => setIsWaving(false), 1200)
    setTimeout(() => setShowTip(false), 6000)
  }, [])

  const config = MOOD_CONFIG[mood]

  return (
    <div
      className={cn(
        "relative flex flex-col items-center gap-3 p-4 rounded-2xl border border-border bg-card",
        className
      )}
      role="region"
      aria-label="Compañero virtual SellIA"
    >
      {/* Companion Avatar */}
      <motion.button
        onClick={handleClick}
        className={cn(
          "relative w-14 h-14 rounded-full bg-secondary flex items-center justify-center text-3xl cursor-pointer select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
          config.color
        )}
        animate={
          reducedMotion
            ? {}
            : isWaving
            ? {
                rotate: [0, -15, 15, -15, 15, 0],
                scale: [1, 1.1, 1.1, 1.1, 1.1, 1],
              }
            : mood === "sleeping"
            ? { scale: [1, 0.95, 1] }
            : mood === "celebrating"
            ? { scale: [1, 1.2, 1], rotate: [0, 10, -10, 0] }
            : { y: [0, -4, 0] }
        }
        transition={
          isWaving
            ? { duration: 0.8, ease: "easeInOut" }
            : mood === "sleeping"
            ? { duration: 3, repeat: Infinity, ease: "easeInOut" }
            : mood === "celebrating"
            ? { duration: 0.6, repeat: 2 }
            : { duration: 2.5, repeat: Infinity, ease: "easeInOut" }
        }
        whileHover={reducedMotion ? {} : { scale: 1.08 }}
        whileTap={{ scale: 0.95 }}
        aria-label="Compañero virtual. Hacé clic para ver un consejo."
      >
        {config.emoji}
        {!reducedMotion && mood === "celebrating" && (
          <>
            <span className="absolute -top-1 -right-1 text-sm animate-bounce">✨</span>
            <span className="absolute -bottom-1 -left-1 text-sm animate-bounce delay-100">🎊</span>
          </>
        )}
      </motion.button>

      {/* Message */}
      <div className="text-center">
        <p className="text-xs font-medium text-muted-foreground leading-relaxed">
          {config.message}
        </p>
      </div>

      {/* Tip Bubble */}
      <AnimatePresence>
        {showTip && activeTip && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.9 }}
            transition={{ type: "spring", stiffness: 300, damping: 24 }}
            className="absolute -top-2 left-1/2 -translate-x-1/2 -translate-y-full w-56 p-3 rounded-xl bg-popover border border-border shadow-lg z-50"
            role="status"
            aria-live="polite"
          >
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 rotate-45 w-3 h-3 bg-popover border-r border-b border-border" />
            <p className="text-xs text-popover-foreground leading-relaxed relative">
              {activeTip.text}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
