"use client"

import React, { useState, useEffect, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { X, Send } from "lucide-react"
import { cn } from "@/lib/utils"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/Button"
import { Textarea } from "@/components/ui/Textarea"
import { Label } from "@/components/ui/Label"

const DISMISSAL_KEY = "nps-dismissed-until"
const DISMISSAL_DAYS = 30

function getDismissalExpiry(): number | null {
  if (typeof window === "undefined") return null
  const raw = localStorage.getItem(DISMISSAL_KEY)
  if (!raw) return null
  const until = parseInt(raw, 10)
  if (isNaN(until)) return null
  return until
}

function isDismissed(): boolean {
  const until = getDismissalExpiry()
  if (!until) return false
  return Date.now() < until
}

function dismissForDays(days: number) {
  if (typeof window === "undefined") return
  const ms = days * 24 * 60 * 60 * 1000
  localStorage.setItem(DISMISSAL_KEY, String(Date.now() + ms))
}

function getScoreColor(score: number): string {
  if (score <= 6) return "bg-red-500 hover:bg-red-400 text-white shadow-red-500/20"
  if (score <= 8) return "bg-amber-500 hover:bg-amber-400 text-white shadow-amber-500/20"
  return "bg-emerald-500 hover:bg-emerald-400 text-white shadow-emerald-500/20"
}

function getScoreLabel(score: number): string {
  if (score <= 6) return "Detractor"
  if (score <= 8) return "Neutral"
  return "Promotor"
}

export function NpsWidget() {
  const [visible, setVisible] = useState(false)
  const [score, setScore] = useState<number | null>(null)
  const [comment, setComment] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => {
      if (!isDismissed()) {
        setVisible(true)
      }
    }, 3000)
    return () => clearTimeout(timer)
  }, [])

  const handleDismiss = useCallback(() => {
    setVisible(false)
    dismissForDays(DISMISSAL_DAYS)
  }, [])

  const handleSubmit = async () => {
    if (score === null) return
    setSubmitting(true)
    try {
      await api.post("/nps", { score, comment: comment.trim() || undefined })
      setSubmitted(true)
      setTimeout(() => {
        setVisible(false)
      }, 2000)
    } catch {
      setSubmitted(true)
      setTimeout(() => setVisible(false), 2000)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ type: "spring", stiffness: 300, damping: 24 }}
          className="fixed top-0 left-0 right-0 z-[55]"
        >
          <div className="mx-auto max-w-3xl px-4 pt-4">
            <div className="relative rounded-2xl border border-white/[0.06] bg-[#060812] shadow-2xl shadow-black/50 backdrop-blur-xl overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-brand-violet via-brand-violet-light to-brand-violet" />

              <div className="p-6">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 space-y-4">
                    {submitted ? (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="flex items-center gap-3 py-2"
                      >
                        <div className="h-10 w-10 rounded-full bg-emerald-500/10 flex items-center justify-center">
                          <svg className="h-5 w-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                          </svg>
                        </div>
                        <div>
                          <p className="text-white font-medium">¡Gracias por tu respuesta!</p>
                          <p className="text-white/40 text-sm">Nos ayuda mucho a seguir mejorando.</p>
                        </div>
                      </motion.div>
                    ) : (
                      <>
                        <div className="space-y-1">
                          <h3 className="text-white font-semibold text-base">
                            ¿Qué tan probable es que recomiendes SellIA a un colega?
                          </h3>
                          <p className="text-white/40 text-sm">Del 0 (nada probable) al 10 (muy probable)</p>
                        </div>

                        <div className="flex items-center gap-1.5 flex-wrap">
                          {Array.from({ length: 11 }, (_, i) => (
                            <button
                              key={i}
                              onClick={() => setScore(i)}
                              className={cn(
                                "h-9 w-9 rounded-lg text-sm font-bold transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-white/20",
                                score === i
                                  ? getScoreColor(i)
                                  : "bg-white/[0.03] border border-white/[0.06] text-white/60 hover:bg-white/[0.06] hover:text-white"
                              )}
                              aria-label={`Puntuación ${i}`}
                            >
                              {i}
                            </button>
                          ))}
                        </div>

                        {score !== null && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: "auto" }}
                            className="space-y-3 overflow-hidden"
                          >
                            <div className="flex items-center gap-2">
                              <span className={cn(
                                "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
                                score <= 6 ? "bg-red-500/10 text-red-400" :
                                score <= 8 ? "bg-amber-500/10 text-amber-400" :
                                "bg-emerald-500/10 text-emerald-400"
                              )}>
                                {getScoreLabel(score)}
                              </span>
                            </div>

                            <div className="space-y-2">
                              <Label htmlFor="nps-comment" className="text-white/60 normal-case tracking-normal text-sm">
                                ¿Por qué? <span className="text-white/30">(opcional)</span>
                              </Label>
                              <Textarea
                                id="nps-comment"
                                placeholder="Contanos más sobre tu experiencia..."
                                value={comment}
                                onChange={(e) => setComment(e.target.value)}
                                rows={3}
                                className="resize-none"
                              />
                            </div>

                            <Button
                              onClick={handleSubmit}
                              disabled={submitting}
                              isLoading={submitting}
                              className="w-full sm:w-auto"
                              leftIcon={<Send className="h-4 w-4" />}
                            >
                              Enviar respuesta
                            </Button>
                          </motion.div>
                        )}
                      </>
                    )}
                  </div>

                  {!submitted && (
                    <button
                      onClick={handleDismiss}
                      className="flex-shrink-0 p-1.5 rounded-lg text-white/30 hover:text-white/60 hover:bg-white/5 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-white/20"
                      aria-label="Cerrar encuesta NPS"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default NpsWidget
