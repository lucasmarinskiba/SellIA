"use client"

import React, { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { MessageSquare, Bug, Lightbulb, ThumbsUp, Send, ImagePlus, CheckCircle2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { api } from "@/lib/api"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/Sheet"
import { Button } from "@/components/ui/Button"
import { Textarea } from "@/components/ui/Textarea"
import { Label } from "@/components/ui/Label"

type FeedbackType = "bug" | "feature" | "praise"

interface FeedbackOption {
  value: FeedbackType
  label: string
  icon: React.ReactNode
  color: string
}

const FEEDBACK_TYPES: FeedbackOption[] = [
  { value: "bug", label: "Bug", icon: <Bug className="w-4 h-4" />, color: "bg-red-500/10 text-red-400 border-red-500/20 hover:bg-red-500/20" },
  { value: "feature", label: "Feature", icon: <Lightbulb className="w-4 h-4" />, color: "bg-amber-500/10 text-amber-400 border-amber-500/20 hover:bg-amber-500/20" },
  { value: "praise", label: "Praise", icon: <ThumbsUp className="w-4 h-4" />, color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20" },
]

export function FeedbackWidget() {
  const [open, setOpen] = useState(false)
  const [type, setType] = useState<FeedbackType | null>(null)
  const [message, setMessage] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async () => {
    if (!type || !message.trim()) return
    setSubmitting(true)
    try {
      await api.post("/feedback", { type, message: message.trim() })
      setSuccess(true)
      setTimeout(() => {
        setOpen(false)
        setTimeout(() => {
          setSuccess(false)
          setType(null)
          setMessage("")
        }, 300)
      }, 1500)
    } catch {
      // Silently fail - feedback should never block the user
    } finally {
      setSubmitting(false)
    }
  }

  const handleOpenChange = (isOpen: boolean) => {
    setOpen(isOpen)
    if (!isOpen) {
      setTimeout(() => {
        setSuccess(false)
        setType(null)
        setMessage("")
      }, 300)
    }
  }

  return (
    <>
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-[60] flex h-12 w-12 items-center justify-center rounded-full bg-brand-violet text-white shadow-lg shadow-brand-violet/30 hover:bg-brand-violet-light transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-violet/50"
        aria-label="Enviar feedback"
      >
        <MessageSquare className="h-5 w-5" />
      </motion.button>

      <Sheet open={open} onOpenChange={handleOpenChange}>
        <SheetContent side="right" className="w-full sm:max-w-md bg-[#060812] border-white/[0.06]">
          <SheetHeader className="space-y-2">
            <SheetTitle className="text-white">Enviar feedback</SheetTitle>
            <SheetDescription className="text-white/40">
              Tu opinión nos ayuda a mejorar SellIA.
            </SheetDescription>
          </SheetHeader>

          <div className="mt-6 space-y-6">
            <AnimatePresence mode="wait">
              {success ? (
                <motion.div
                  key="success"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="flex flex-col items-center justify-center py-12 space-y-4"
                >
                  <div className="h-16 w-16 rounded-full bg-emerald-500/10 flex items-center justify-center">
                    <CheckCircle2 className="h-8 w-8 text-emerald-400" />
                  </div>
                  <p className="text-white font-medium">¡Gracias por tu feedback!</p>
                  <p className="text-white/40 text-sm text-center">Lo tendremos en cuenta para futuras mejoras.</p>
                </motion.div>
              ) : (
                <motion.div
                  key="form"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="space-y-6"
                >
                  <div className="space-y-3">
                    <Label>Tipo de feedback</Label>
                    <div className="flex gap-2">
                      {FEEDBACK_TYPES.map((option) => (
                        <button
                          key={option.value}
                          onClick={() => setType(option.value)}
                          className={cn(
                            "flex-1 flex items-center justify-center gap-2 rounded-xl border px-3 py-2.5 text-sm font-medium transition-all",
                            option.color,
                            type === option.value
                              ? "ring-2 ring-white/20 bg-white/[0.06]"
                              : "bg-white/[0.03] border-white/[0.06] text-white/70 hover:text-white"
                          )}
                        >
                          {option.icon}
                          {option.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <Label htmlFor="feedback-message">Mensaje</Label>
                    <Textarea
                      id="feedback-message"
                      placeholder="Contanos qué pensás..."
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      rows={5}
                    />
                  </div>

                  <div className="flex items-center gap-2 rounded-xl border border-dashed border-white/[0.08] bg-white/[0.02] px-4 py-3 text-sm text-white/40">
                    <ImagePlus className="h-4 w-4 flex-shrink-0" />
                    <span>Podés adjuntar capturas de pantalla arrastrándolas aquí (próximamente)</span>
                  </div>

                  <Button
                    onClick={handleSubmit}
                    disabled={!type || !message.trim() || submitting}
                    isLoading={submitting}
                    className="w-full"
                    leftIcon={<Send className="h-4 w-4" />}
                  >
                    Enviar feedback
                  </Button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </SheetContent>
      </Sheet>
    </>
  )
}

export default FeedbackWidget
