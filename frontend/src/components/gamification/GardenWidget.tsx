"use client"

import React, { useState, useEffect } from "react"
import { motion, useReducedMotion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"

interface GardenWidgetProps {
  className?: string
}

interface Plant {
  id: string
  type: "sprout" | "flower" | "tree" | "starflower"
  x: number
  y: number
  color: string
  scale: number
}

const PLANT_CONFIG = {
  sprout: {
    svg: (
      <svg viewBox="0 0 40 40" className="w-full h-full">
        <path d="M20 35 Q20 25 15 20 Q10 15 8 10 Q15 12 20 18 Q25 12 32 10 Q30 15 25 20 Q20 25 20 35" fill="currentColor" />
        <circle cx="20" cy="35" r="3" fill="#8B6914" />
      </svg>
    ),
    colors: ["text-emerald-400", "text-teal-400", "text-green-400"],
  },
  flower: {
    svg: (
      <svg viewBox="0 0 40 40" className="w-full h-full">
        <circle cx="20" cy="20" r="6" fill="#FBBF24" />
        <circle cx="20" cy="10" r="5" fill="currentColor" />
        <circle cx="20" cy="30" r="5" fill="currentColor" />
        <circle cx="10" cy="20" r="5" fill="currentColor" />
        <circle cx="30" cy="20" r="5" fill="currentColor" />
        <path d="M20 35 Q20 30 18 28 Q20 30 22 28 Q20 30 20 35" fill="#8B6914" />
      </svg>
    ),
    colors: ["text-pink-400", "text-violet-400", "text-rose-400", "text-sky-400"],
  },
  tree: {
    svg: (
      <svg viewBox="0 0 40 50" className="w-full h-full">
        <rect x="17" y="35" width="6" height="12" rx="2" fill="#8B6914" />
        <circle cx="20" cy="22" r="14" fill="currentColor" opacity="0.9" />
        <circle cx="14" cy="28" r="10" fill="currentColor" opacity="0.7" />
        <circle cx="26" cy="28" r="10" fill="currentColor" opacity="0.7" />
        <circle cx="20" cy="14" r="8" fill="currentColor" opacity="0.8" />
      </svg>
    ),
    colors: ["text-emerald-500", "text-teal-500", "text-green-500"],
  },
  starflower: {
    svg: (
      <svg viewBox="0 0 40 40" className="w-full h-full">
        <path d="M20 5 L23 15 L33 15 L25 21 L28 31 L20 25 L12 31 L15 21 L7 15 L17 15 Z" fill="currentColor" />
        <circle cx="20" cy="20" r="4" fill="#FBBF24" />
        <path d="M20 38 Q20 34 18 32 Q20 34 22 32 Q20 34 20 38" fill="#8B6914" />
      </svg>
    ),
    colors: ["text-amber-400", "text-orange-400", "text-yellow-400"],
  },
}

function generateGarden(salesCount: number, streakDays: number): Plant[] {
  const plants: Plant[] = []
  const totalPlants = Math.min(salesCount, 24)

  for (let i = 0; i < totalPlants; i++) {
    const type: Plant["type"] =
      i % 12 === 0 ? "starflower" : i % 5 === 0 ? "tree" : i % 2 === 0 ? "flower" : "sprout"
    const config = PLANT_CONFIG[type]
    plants.push({
      id: `plant-${i}`,
      type,
      x: 8 + (i % 6) * 16 + Math.random() * 6 - 3,
      y: 55 + Math.floor(i / 6) * 18 + Math.random() * 4 - 2,
      color: config.colors[Math.floor(Math.random() * config.colors.length)],
      scale: 0.7 + Math.random() * 0.4,
    })
  }

  return plants
}

function WaterDrop({ x, y, delay }: { x: number; y: number; delay: number }) {
  const reducedMotion = useReducedMotion()

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={reducedMotion ? { opacity: 1 } : { opacity: [0, 1, 0], y: [-10, 5, 15] }}
      transition={{
        duration: 1.5,
        delay,
        repeat: Infinity,
        repeatDelay: 2,
      }}
      className="absolute text-sky-400 text-xs"
      style={{ left: `${x}%`, top: `${y}%` }}
      aria-hidden="true"
    >
      💧
    </motion.div>
  )
}

export function GardenWidget({ className }: GardenWidgetProps) {
  const [salesCount, setSalesCount] = useState(8)
  const [streakDays, setStreakDays] = useState(3)
  const [plants, setPlants] = useState<Plant[]>([])
  const [hoveredPlant, setHoveredPlant] = useState<string | null>(null)
  const reducedMotion = useReducedMotion()

  useEffect(() => {
    setPlants(generateGarden(salesCount, streakDays))
  }, [salesCount, streakDays])

  return (
    <div
      className={cn(
        "relative rounded-2xl border border-border bg-card p-4 overflow-hidden",
        className
      )}
      role="region"
      aria-label="Jardín de progreso"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-foreground">Tu Jardín 🌱</h3>
          <p className="text-xs text-muted-foreground">
            {salesCount} ventas = {plants.length} plantas
          </p>
        </div>
        {streakDays > 0 && (
          <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-500 text-xs font-medium">
            <span>💧</span> Racha {streakDays} días
          </div>
        )}
      </div>

      {/* Garden canvas */}
      <div className="relative h-40 rounded-xl bg-gradient-to-b from-sky-50/50 to-emerald-50/30 dark:from-sky-950/20 dark:to-emerald-950/10 border border-border overflow-hidden">
        {/* Sun / Moon */}
        <div className="absolute top-2 right-2 text-lg" aria-hidden="true">
          ☀️
        </div>

        {/* Ground */}
        <div className="absolute bottom-0 left-0 right-0 h-4 bg-gradient-to-t from-emerald-800/20 to-transparent dark:from-emerald-900/30" />

        {/* Water drops animation for streak */}
        {streakDays > 0 &&
          Array.from({ length: Math.min(streakDays, 5) }).map((_, i) => (
            <WaterDrop
              key={`drop-${i}`}
              x={15 + i * 18}
              y={20 + (i % 2) * 10}
              delay={i * 0.4}
            />
          ))}

        {/* Plants */}
        <AnimatePresence>
          {plants.map((plant, index) => (
            <motion.div
              key={plant.id}
              initial={reducedMotion ? { opacity: 0 } : { opacity: 0, scale: 0, y: 10 }}
              animate={{
                opacity: 1,
                scale: hoveredPlant === plant.id ? plant.scale * 1.2 : plant.scale,
                y: 0,
              }}
              exit={{ opacity: 0, scale: 0 }}
              transition={
                reducedMotion
                  ? { duration: 0 }
                  : {
                      type: "spring",
                      stiffness: 200,
                      damping: 15,
                      delay: index * 0.05,
                    }
              }
              className={cn("absolute w-8 h-8 cursor-pointer", plant.color)}
              style={{
                left: `${plant.x}%`,
                top: `${plant.y}%`,
              }}
              onMouseEnter={() => setHoveredPlant(plant.id)}
              onMouseLeave={() => setHoveredPlant(null)}
              role="img"
              aria-label={`Planta ${plant.type} número ${index + 1}`}
            >
              {PLANT_CONFIG[plant.type].svg}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Empty state */}
        {plants.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-xs text-muted-foreground text-center px-4">
              Tu primer venta plantará la primera semilla 🌱
            </p>
          </div>
        )}
      </div>

      {/* Message */}
      <p className="mt-3 text-xs text-muted-foreground text-center">
        Tu jardín crece con cada venta. 🌱
      </p>
    </div>
  )
}
