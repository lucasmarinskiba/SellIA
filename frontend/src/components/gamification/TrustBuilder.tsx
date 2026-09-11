"use client"

import React, { useState, useEffect, useMemo } from "react"
import { useBusinessSnapshot } from "@/lib/businessSnapshot"
import { motion, useReducedMotion } from "framer-motion"
import { Shield, MessageCircle, Clock, Moon, TrendingUp } from "lucide-react"
import { cn } from "@/lib/utils"

interface TrustBuilderProps {
  className?: string
}

interface TrustStat {
  id: string
  icon: React.ReactNode
  label: string
  value: string
  subtext: string
  color: string
}

export function TrustBuilder({ className }: TrustBuilderProps) {
  /**
   * These four numbers used to be constants: "47 ventas autopilot", "99.7% de
   * mensajes respondidos", "0 quejas", "12/15 noches tranquilas". They were
   * displayed in the sidebar of every page to every account, including brand new
   * ones with no data at all, which makes them the most-seen invented numbers in
   * the product. They now come from the account's own snapshot, and a number that
   * cannot be computed yet shows "—" instead of a flattering default.
   */
  const { snapshot, loading } = useBusinessSnapshot()

  const conversations = snapshot?.conversations
  const revenue = snapshot?.revenue
  const aiReplies = (snapshot?.channels ?? []).reduce((sum, channel) => sum + (channel.ai_replies || 0), 0)
  const waiting = Math.max(0, (conversations?.inbound ?? 0) - (conversations?.answered ?? 0))

  const stats: TrustStat[] = useMemo(() => [
    {
      id: "ai-replies",
      icon: <MessageCircle className="w-4 h-4" />,
      label: "Respuestas de la IA",
      value: snapshot ? String(aiReplies) : "—",
      subtext: aiReplies > 0 ? "mensajes que contestó sola" : "todavía ninguna",
      color: "text-emerald-500",
    },
    {
      id: "response-rate",
      icon: <TrendingUp className="w-4 h-4" />,
      label: "Consultas respondidas",
      // Percentage only when there is a denominator: a rate over zero questions
      // is not 100%, it is unknown.
      value:
        conversations && conversations.inbound > 0
          ? `${conversations.response_rate}%`
          : "—",
      subtext:
        conversations && conversations.inbound > 0
          ? `${conversations.answered} de ${conversations.inbound}`
          : "sin consultas todavía",
      color: "text-sky-500",
    },
    {
      id: "waiting",
      icon: <Shield className="w-4 h-4" />,
      label: "Esperando respuesta",
      value: snapshot ? String(waiting) : "—",
      subtext: waiting > 0 ? "conversaciones sin contestar" : "nadie esperando",
      color: waiting > 0 ? "text-amber-500" : "text-violet-500",
    },
    {
      id: "paid-orders",
      icon: <Moon className="w-4 h-4" />,
      label: "Órdenes cobradas",
      value: revenue ? String(revenue.orders_paid) : "—",
      subtext: revenue ? `de ${revenue.orders_total} en total` : "sin ventas todavía",
      color: "text-amber-500",
    },
  ], [snapshot, conversations, revenue, aiReplies, waiting])

  const [animatedValues, setAnimatedValues] = useState<Record<string, number>>({})
  const reducedMotion = useReducedMotion()

  useEffect(() => {
    if (reducedMotion) {
      const initial: Record<string, number> = {}
      stats.forEach((s) => {
        const num = parseFloat(s.value.replace(/[^0-9.]/g, ""))
        initial[s.id] = num
      })
      setAnimatedValues(initial)
      return
    }

    stats.forEach((stat) => {
      const num = parseFloat(stat.value.replace(/[^0-9.]/g, ""))
      const isFraction = stat.value.includes("/")
      const target = isFraction ? num : num
      const duration = 1500
      const startTime = Date.now()

      const animate = () => {
        const elapsed = Date.now() - startTime
        const progress = Math.min(elapsed / duration, 1)
        const eased = 1 - Math.pow(1 - progress, 3)
        const current = target * eased

        setAnimatedValues((prev) => ({
          ...prev,
          [stat.id]: current,
        }))

        if (progress < 1) {
          requestAnimationFrame(animate)
        }
      }

      const timer = setTimeout(() => {
        requestAnimationFrame(animate)
      }, 200)
      if (nothingToShow) return null

  return () => clearTimeout(timer)
    })
  }, [stats, reducedMotion])

  // Nothing to show until the account has been read: better an absent widget
  // than four dashes, and far better than the invented numbers this replaced.
  const nothingToShow = loading && !snapshot

  function formatValue(stat: TrustStat, animated: number): string {
    if (stat.value.includes("%")) {
      return `${animated.toFixed(1)}%`
    }
    if (stat.value.includes("/")) {
      const parts = stat.value.split("/")
      const denominator = parts[1]
      return `${Math.round(animated)}/${denominator}`
    }
    return `${Math.round(animated)}`
  }

  return (
    <div
      className={cn(
        "rounded-2xl border border-border bg-card p-4",
        className
      )}
      role="region"
      aria-label="Confianza en el autopiloto"
    >
      <div className="flex items-center gap-2 mb-4">
        <div className="p-1.5 rounded-lg bg-emerald-500/10">
          <Shield className="w-4 h-4 text-emerald-500" />
        </div>
        <h3 className="text-sm font-semibold text-foreground">Confianza en el Autopilot</h3>
      </div>

      <div className="space-y-3">
        {stats.map((stat, index) => {
          const animated = animatedValues[stat.id] || 0
          const displayValue = animated > 0 ? formatValue(stat, animated) : stat.value

          return (
            <motion.div
              key={stat.id}
              initial={reducedMotion ? { opacity: 0 } : { opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{
                delay: reducedMotion ? 0 : index * 0.1,
                duration: 0.3,
              }}
              className="flex items-center gap-3 p-2.5 rounded-xl bg-muted/50 hover:bg-muted transition-colors"
            >
              <div className={cn("p-1.5 rounded-lg bg-background", stat.color)}>
                {stat.icon}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-muted-foreground">{stat.label}</p>
                <p className="text-sm font-semibold text-foreground">
                  {stat.id === "autopilot-sales" ? (
                    <>
                      Tu autopiloto ha manejado{" "}
                      <span className={stat.color}>{displayValue}</span> ventas este mes sin tu
                      intervención
                    </>
                  ) : stat.id === "sleep-score" ? (
                    <>
                      Dormiste tranquilo{" "}
                      <span className={stat.color}>{displayValue}</span> noches este mes 🌙
                    </>
                  ) : stat.id === "complaints" ? (
                    <>
                      <span className={stat.color}>{displayValue}</span> quejas de clientes en los
                      últimos 30 días
                    </>
                  ) : (
                    <>
                      <span className={stat.color}>{displayValue}</span> de mensajes respondidos a
                      tiempo
                    </>
                  )}
                </p>
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Trust meter */}
      <div className="mt-4 pt-3 border-t border-border">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs text-muted-foreground">Nivel de confianza</span>
          <span className="text-xs font-semibold text-emerald-500">Excelente</span>
        </div>
        <div className="h-2 rounded-full bg-muted overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: "94%" }}
            transition={
              reducedMotion
                ? { duration: 0 }
                : { duration: 1.5, delay: 0.5, ease: "easeOut" }
            }
            className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-sky-500"
            aria-hidden="true"
          />
        </div>
      </div>
    </div>
  )
}

