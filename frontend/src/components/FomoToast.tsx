"use client"

import React, { useState, useEffect, useCallback, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { X, Zap } from "lucide-react"
import { cn } from "@/lib/utils"
import { api } from "@/lib/api"

interface FomoEvent {
  id: string
  user: string
  action: string
  item: string
  timeAgo: string
}

interface FomoToastItem extends FomoEvent {
  visible: boolean
}

const SAMPLE_EVENTS: FomoEvent[] = [
  { id: "f1", user: "María", action: "compró", item: "Plantilla de Ventas Pro", timeAgo: "hace 2 min" },
  { id: "f2", user: "Carlos", action: "suscribió", item: "Plan Growth", timeAgo: "hace 5 min" },
  { id: "f3", user: "Ana", action: "activó", item: "Autopilot IA", timeAgo: "hace 8 min" },
  { id: "f4", user: "Luis", action: "compró", item: "Pack de Embudos", timeAgo: "hace 12 min" },
  { id: "f5", user: "Sofía", action: "upgradeó a", item: "Plan Pro", timeAgo: "hace 15 min" },
]

const MAX_VISIBLE = 3
const AUTO_DISMISS_MS = 5000
const POLL_INTERVAL_MS = 30000

function getRandomEvent(): FomoEvent {
  return SAMPLE_EVENTS[Math.floor(Math.random() * SAMPLE_EVENTS.length)]
}

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

async function fetchFomoEvents(): Promise<FomoEvent[]> {
  try {
    const res = await api.get("/fomo/events")
    if (Array.isArray(res.data)) {
      return res.data.map((e: FomoEvent) => ({ ...e, id: e.id || generateId() }))
    }
  } catch {
    // Fallback to sample data
  }
  return [getRandomEvent()]
}

export function FomoToast({ className }: { className?: string }) {
  const [toasts, setToasts] = useState<FomoToastItem[]>([])
  const queueRef = useRef<FomoEvent[]>([])
  const timeoutsRef = useRef<Record<string, NodeJS.Timeout>>({})

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
    if (timeoutsRef.current[id]) {
      clearTimeout(timeoutsRef.current[id])
      delete timeoutsRef.current[id]
    }
  }, [])

  const addToast = useCallback((event: FomoEvent) => {
    const id = generateId()
    const toast: FomoToastItem = { ...event, id, visible: true }

    setToasts((prev) => {
      const next = [...prev, toast]
      if (next.length > MAX_VISIBLE) {
        const [first, ...rest] = next
        removeToast(first.id)
        return rest
      }
      return next
    })

    timeoutsRef.current[id] = setTimeout(() => {
      removeToast(id)
    }, AUTO_DISMISS_MS)
  }, [removeToast])

  const processQueue = useCallback(() => {
    if (queueRef.current.length === 0) return
    const event = queueRef.current.shift()
    if (event) addToast(event)
  }, [addToast])

  const pollEvents = useCallback(async () => {
    const events = await fetchFomoEvents()
    queueRef.current.push(...events)
    processQueue()
  }, [processQueue])

  useEffect(() => {
    const initialTimer = setTimeout(() => {
      pollEvents()
    }, 4000)

    const interval = setInterval(() => {
      pollEvents()
    }, POLL_INTERVAL_MS)

    const queueInterval = setInterval(() => {
      processQueue()
    }, 3500)

    return () => {
      clearTimeout(initialTimer)
      clearInterval(interval)
      clearInterval(queueInterval)
      Object.values(timeoutsRef.current).forEach(clearTimeout)
    }
  }, [pollEvents, processQueue])

  return (
    <div className={cn("fixed bottom-6 left-6 z-[65] flex flex-col gap-3", className)}>
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            layout
            initial={{ opacity: 0, x: -60, scale: 0.95 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: -40, scale: 0.95 }}
            transition={{ type: "spring", stiffness: 350, damping: 25 }}
            className={cn(
              "flex items-center gap-3 rounded-2xl border px-4 py-3 shadow-xl backdrop-blur-md",
              "bg-white/[0.03] border-white/[0.06]",
              "max-w-sm"
            )}
            role="status"
            aria-live="polite"
          >
            <div className="flex-shrink-0 h-10 w-10 rounded-xl bg-brand-violet/10 border border-brand-violet/20 flex items-center justify-center">
              <Zap className="h-5 w-5 text-brand-violet-light" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-white leading-snug">
                <span className="font-semibold">{toast.user}</span>{" "}
                <span className="text-white/60">{toast.action}</span>{" "}
                <span className="font-medium text-brand-violet-light">{toast.item}</span>{" "}
                <span className="text-white/30 text-xs">{toast.timeAgo}</span>
              </p>
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="flex-shrink-0 p-1 rounded-lg text-white/20 hover:text-white/50 hover:bg-white/5 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-white/20"
              aria-label="Cerrar notificación"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}

export default FomoToast
