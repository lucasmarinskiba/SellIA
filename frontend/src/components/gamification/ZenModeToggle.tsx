"use client"

import React, { useState, useEffect, createContext, useContext, useCallback } from "react"
import { motion, useReducedMotion, AnimatePresence } from "framer-motion"
import { Leaf, X } from "lucide-react"
import { cn } from "@/lib/utils"

interface ZenModeContextType {
  isZenMode: boolean
  toggleZenMode: () => void
}

const ZenModeContext = createContext<ZenModeContextType>({
  isZenMode: false,
  toggleZenMode: () => {},
})

export function useZenMode() {
  return useContext(ZenModeContext)
}

interface ZenModeProviderProps {
  children: React.ReactNode
}

export function ZenModeProvider({ children }: ZenModeProviderProps) {
  const [isZenMode, setIsZenMode] = useState(false)

  const toggleZenMode = useCallback(() => {
    setIsZenMode((prev) => !prev)
  }, [])

  return (
    <ZenModeContext.Provider value={{ isZenMode, toggleZenMode }}>
      {children}
    </ZenModeContext.Provider>
  )
}

interface ZenModeToggleProps {
  className?: string
}

export function ZenModeToggle({ className }: ZenModeToggleProps) {
  const { isZenMode, toggleZenMode } = useZenMode()
  const reducedMotion = useReducedMotion()

  return (
    <button
      onClick={toggleZenMode}
      className={cn(
        "inline-flex h-10 w-10 items-center justify-center rounded-xl border transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
        isZenMode
          ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-500"
          : "border-border bg-card text-card-foreground hover:bg-accent hover:text-accent-foreground",
        className
      )}
      aria-label={isZenMode ? "Desactivar modo zen" : "Activar modo zen"}
      title={isZenMode ? "Modo zen activado" : "Modo zen"}
    >
      <Leaf className="h-5 w-5" />
    </button>
  )
}

interface ZenOverlayProps {
  className?: string
}

export function ZenOverlay({ className }: ZenOverlayProps) {
  const { isZenMode, toggleZenMode } = useZenMode()
  const reducedMotion = useReducedMotion()
  const [breathPhase, setBreathPhase] = useState<"inhale" | "hold" | "exhale">("inhale")

  useEffect(() => {
    if (!isZenMode) return
    const cycle = () => {
      setBreathPhase("inhale")
      setTimeout(() => setBreathPhase("hold"), 4000)
      setTimeout(() => setBreathPhase("exhale"), 5500)
    }
    cycle()
    const interval = setInterval(cycle, 10000)
    return () => clearInterval(interval)
  }, [isZenMode])

  if (!isZenMode) return null

  const breathScale = breathPhase === "inhale" ? 1.6 : breathPhase === "hold" ? 1.6 : 1
  const breathOpacity = breathPhase === "inhale" ? 0.5 : breathPhase === "hold" ? 0.6 : 0.25

  return (
    <AnimatePresence>
      {isZenMode && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: reducedMotion ? 0 : 0.5 }}
          className={cn(
            "fixed inset-0 z-[100] flex flex-col items-center justify-center bg-background/95 backdrop-blur-md",
            className
          )}
          role="dialog"
          aria-modal="true"
          aria-label="Modo Zen"
        >
          <button
            onClick={toggleZenMode}
            className="absolute top-6 right-6 p-2 rounded-xl text-muted-foreground hover:text-foreground hover:bg-accent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="Cerrar modo zen"
          >
            <X className="w-6 h-6" />
          </button>

          <div className="flex flex-col items-center gap-8">
            {/* Breathing Circle */}
            <div className="relative w-48 h-48 flex items-center justify-center">
              {!reducedMotion && (
                <motion.div
                  animate={{
                    scale: breathScale,
                    opacity: breathOpacity,
                  }}
                  transition={{
                    duration: breathPhase === "inhale" ? 4 : breathPhase === "exhale" ? 4 : 1.5,
                    ease: "easeInOut",
                  }}
                  className="absolute inset-0 rounded-full bg-primary"
                />
              )}
              <div className="relative z-10 w-32 h-32 rounded-full bg-card border border-border flex items-center justify-center">
                <span className="text-4xl">🧘</span>
              </div>
            </div>

            {/* Breathing Text */}
            <div className="text-center space-y-2">
              <p className="text-lg font-medium text-foreground">
                {breathPhase === "inhale" && "Inhalá profundo..."}
                {breathPhase === "hold" && "Mantené..."}
                {breathPhase === "exhale" && "Exhalá suavemente..."}
              </p>
              <p className="text-sm text-muted-foreground max-w-xs">
                Tu autopiloto está trabajando. Respirá.
              </p>
            </div>

            {/* Hidden stats - minimal */}
            <div className="flex gap-6 text-center">
              <div>
                <p className="text-2xl font-bold text-foreground">3</p>
                <p className="text-xs text-muted-foreground">ventas hoy</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">12</p>
                <p className="text-xs text-muted-foreground">mensajes auto</p>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
