"use client"

import React, { useState, useEffect, useCallback } from "react"
import { motion, AnimatePresence, useReducedMotion } from "framer-motion"
import { X } from "lucide-react"
import { cn } from "@/lib/utils"

interface MotivationalToastProps {
  className?: string
}

interface ToastMessage {
  id: string
  text: string
  icon: string
  type: "login" | "logout" | "slump" | "friday" | "milestone" | "streak"
}

const TOAST_MESSAGES: Record<string, ToastMessage[]> = {
  login: [
    { id: "login-1", text: "¡Hola! Tu autopiloto cerró 3 ventas mientras dormías 🌙", icon: "🌙", type: "login" },
    { id: "login-2", text: "¡Bienvenido de vuelta! Tenés 12 mensajes nuevos esperando 💬", icon: "💬", type: "login" },
    { id: "login-3", text: "Tu IA respondió 47 consultas anoche. Dormiste, ella no. 🤖", icon: "🤖", type: "login" },
  ],
  logout: [
    { id: "logout-1", text: "Hoy vendiste más que ayer. Eso es crecimiento. 📈", icon: "📈", type: "logout" },
    { id: "logout-2", text: "Cerraste el día con 5 ventas. Descansá tranquilo. 😴", icon: "😴", type: "logout" },
    { id: "logout-3", text: "Mañana será mejor. Siempre lo es cuando hay constancia. ✨", icon: "✨", type: "logout" },
  ],
  slump: [
    { id: "slump-1", text: "Café + una venta más = día perfecto ☕", icon: "☕", type: "slump" },
    { id: "slump-2", text: "El 80% de las ventas se cierran después del 5to contacto. ¡Seguí! 📞", icon: "📞", type: "slump" },
    { id: "slump-3", text: "Una pausa de 5 minutos recarga tu foco. Respirá. 🧘", icon: "🧘", type: "slump" },
  ],
  friday: [
    { id: "friday-1", text: "Cerrá la semana con una más. Podés. 💪", icon: "💪", type: "friday" },
    { id: "friday-2", text: "Viernes = oportunidad. Muchos compran antes del finde. 🛒", icon: "🛒", type: "friday" },
    { id: "friday-3", text: "Esta semana diste todo. Disfrutá el descanso merecido. 🏖️", icon: "🏖️", type: "friday" },
  ],
}

function getOptimalMomentType(): string | null {
  const hour = new Date().getHours()
  const day = new Date().getDay() // 0 = Sunday, 5 = Friday

  // Login moment - first 5 minutes after login (simulated)
  // We'll use random chance to simulate login moment
  if (Math.random() < 0.3) return "login"

  // 3 PM slump
  if (hour === 15 || hour === 16) return "slump"

  // Friday motivation
  if (day === 5 && hour < 18) return "friday"

  // Logout moment (simulated with random)
  if (hour >= 18 && Math.random() < 0.2) return "logout"

  return null
}

export function MotivationalToast({ className }: MotivationalToastProps) {
  const [activeToast, setActiveToast] = useState<ToastMessage | null>(null)
  const [isVisible, setIsVisible] = useState(false)
  const reducedMotion = useReducedMotion()

  const showToast = useCallback(() => {
    const momentType = getOptimalMomentType()
    if (!momentType) return

    const messages = TOAST_MESSAGES[momentType]
    const randomMessage = messages[Math.floor(Math.random() * messages.length)]
    setActiveToast(randomMessage)
    setIsVisible(true)
  }, [])

  const dismissToast = useCallback(() => {
    setIsVisible(false)
    setTimeout(() => setActiveToast(null), 300)
  }, [])

  useEffect(() => {
    // Show first toast after a delay
    const initialTimer = setTimeout(() => {
      showToast()
    }, 3000)

    // Periodic check for new moments
    const interval = setInterval(() => {
      if (!isVisible && Math.random() < 0.15) {
        showToast()
      }
    }, 60000) // Check every minute

    return () => {
      clearTimeout(initialTimer)
      clearInterval(interval)
    }
  }, [showToast, isVisible])

  // Auto-dismiss
  useEffect(() => {
    if (!isVisible) return
    const timer = setTimeout(() => {
      dismissToast()
    }, 7000)
    return () => clearTimeout(timer)
  }, [isVisible, dismissToast])

  return (
    <div className={cn("fixed bottom-6 right-6 z-[70]", className)}>
      <AnimatePresence>
        {isVisible && activeToast && (
          <motion.div
            initial={reducedMotion ? { opacity: 0 } : { opacity: 0, y: 30, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={reducedMotion ? { opacity: 0 } : { opacity: 0, y: 20, scale: 0.9 }}
            transition={{ type: "spring", stiffness: 300, damping: 24 }}
            className="flex items-start gap-3 p-4 rounded-2xl border border-border bg-card shadow-lg max-w-xs"
            role="status"
            aria-live="polite"
            aria-label="Mensaje motivacional"
          >
            <span className="text-2xl flex-shrink-0" aria-hidden="true">
              {activeToast.icon}
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-foreground leading-relaxed">{activeToast.text}</p>
            </div>
            <button
              onClick={dismissToast}
              className="flex-shrink-0 p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-label="Cerrar mensaje"
            >
              <X className="w-4 h-4" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
