'use client'

import { useState, useCallback, useRef, useEffect } from 'react'

export type WakeWordState = 'inactive' | 'listening' | 'detected' | 'error'

interface UseSellIAWakeWordOptions {
  onWake?: () => void
  enabled?: boolean
}

const WAKE_PHRASES = [
  'hola sellia',
  'hey sellia',
  'ok sellia',
  'okey sellia',
  'sellia',
  'hola selia',
  'hey selia',
]

export function useSellIAWakeWord(options: UseSellIAWakeWordOptions = {}) {
  const { onWake, enabled = true } = options
  const [state, setState] = useState<WakeWordState>('inactive')
  const [lastDetectedAt, setLastDetectedAt] = useState<number>(0)
  const recognitionRef = useRef<any>(null)
  const cooldownRef = useRef(false)
  const restartTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const onWakeRef = useRef(onWake)
  onWakeRef.current = onWake

  const COOLDOWN_MS = 3000 // Evitar doble-trigger

  const isSupported = typeof window !== 'undefined' &&
    !!((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition)

  const stopListening = useCallback(() => {
    if (restartTimeoutRef.current) {
      clearTimeout(restartTimeoutRef.current)
      restartTimeoutRef.current = null
    }
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop()
      } catch {
        // ignore
      }
      recognitionRef.current = null
    }
    setState(prev => prev === 'detected' ? prev : 'inactive')
  }, [])

  const startListening = useCallback(() => {
    if (!isSupported || !enabled) return

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) return

    // Stop previous
    if (recognitionRef.current) {
      try { recognitionRef.current.stop() } catch {}
    }

    const recognition = new SpeechRecognition()
    recognition.lang = 'es-ES'
    recognition.continuous = true
    recognition.interimResults = true
    recognition.maxAlternatives = 1

    recognition.onstart = () => {
      setState('listening')
    }

    recognition.onresult = (event: any) => {
      let fullTranscript = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        fullTranscript += event.results[i][0].transcript
      }

      const normalized = fullTranscript.toLowerCase().trim()

      const matched = WAKE_PHRASES.some(phrase => normalized.includes(phrase))

      if (matched && !cooldownRef.current) {
        cooldownRef.current = true
        setState('detected')
        setLastDetectedAt(Date.now())
        onWakeRef.current?.()

        // Cooldown para evitar múltiples triggers
        setTimeout(() => {
          cooldownRef.current = false
        }, COOLDOWN_MS)
      }
    }

    recognition.onerror = (event: any) => {
      if (event.error === 'not-allowed') {
        setState('error')
        return
      }
      // Auto-restart en errores no críticos
      if (enabled && event.error !== 'aborted') {
        restartTimeoutRef.current = setTimeout(() => {
          startListening()
        }, 500)
      }
    }

    recognition.onend = () => {
      if (enabled) {
        restartTimeoutRef.current = setTimeout(() => {
          startListening()
        }, 200)
      } else {
        setState('inactive')
      }
    }

    recognitionRef.current = recognition
    try {
      recognition.start()
    } catch {
      // ignore
    }
  }, [isSupported, enabled])

  useEffect(() => {
    if (enabled) {
      startListening()
    } else {
      stopListening()
    }
    return () => {
      stopListening()
    }
  }, [enabled, startListening, stopListening])

  return {
    state,
    isSupported,
    isListening: state === 'listening',
    lastDetectedAt,
    startListening,
    stopListening,
  }
}
