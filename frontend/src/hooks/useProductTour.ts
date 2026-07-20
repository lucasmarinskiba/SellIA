"use client"

import { useState, useEffect, useCallback } from "react"
import { api } from "@/lib/api"

export interface TourStep {
  id: string
  order: number
  target_selector: string
  title: string
  content: string
  placement?: "top" | "bottom" | "left" | "right"
}

export interface TourProgress {
  current_step: number
  completed: boolean
}

export interface UseProductTourReturn {
  currentStep: TourStep | null
  totalSteps: number
  next: () => Promise<void>
  prev: () => void
  skip: () => Promise<void>
  isActive: boolean
  loading: boolean
  stepIndex: number
}

export function useProductTour(tourId: string): UseProductTourReturn {
  const [steps, setSteps] = useState<TourStep[]>([])
  const [stepIndex, setStepIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [completed, setCompleted] = useState(false)

  useEffect(() => {
    let cancelled = false

    async function loadTour() {
      setLoading(true)
      try {
        const [stepsRes, progressRes] = await Promise.all([
          api.get(`/tours/${tourId}/steps`),
          api.get("/my-progress").catch(() => ({ data: null })),
        ])

        if (cancelled) return

        const loadedSteps: TourStep[] = Array.isArray(stepsRes.data)
          ? stepsRes.data.sort((a: TourStep, b: TourStep) => a.order - b.order)
          : []

        setSteps(loadedSteps)

        // Determine starting step from progress
        const progress: TourProgress | null = progressRes.data
        if (progress && !progress.completed && typeof progress.current_step === "number") {
          const startIdx = Math.min(Math.max(0, progress.current_step), loadedSteps.length - 1)
          setStepIndex(startIdx)
        } else if (progress?.completed) {
          setCompleted(true)
        }
      } catch {
        // If API fails, just keep empty steps (inactive tour)
        setSteps([])
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    loadTour()
    return () => { cancelled = true }
  }, [tourId])

  const next = useCallback(async () => {
    const nextIndex = stepIndex + 1
    if (nextIndex >= steps.length) {
      // Mark as completed
      try {
        await api.post(`/tours/${tourId}/progress`, { step: steps.length, completed: true })
      } catch {
        // Best-effort
      }
      setCompleted(true)
      return
    }

    try {
      await api.post(`/tours/${tourId}/progress`, { step: nextIndex })
    } catch {
      // Best-effort
    }
    setStepIndex(nextIndex)
  }, [stepIndex, steps.length, tourId])

  const prev = useCallback(() => {
    setStepIndex((idx) => Math.max(0, idx - 1))
  }, [])

  const skip = useCallback(async () => {
    try {
      await api.post(`/tours/${tourId}/progress`, { step: steps.length, completed: true })
    } catch {
      // Best-effort
    }
    setCompleted(true)
  }, [steps.length, tourId])

  const isActive = steps.length > 0 && !completed && !loading
  const currentStep = isActive ? steps[stepIndex] ?? null : null

  return {
    currentStep,
    totalSteps: steps.length,
    next,
    prev,
    skip,
    isActive,
    loading,
    stepIndex,
  }
}
