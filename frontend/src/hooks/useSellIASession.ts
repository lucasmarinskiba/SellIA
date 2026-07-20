'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import { useTextToSpeech } from './useTextToSpeech'
import { useVoiceRecognition } from './useVoiceRecognition'

export type SellIASessionState =
  | 'idle'
  | 'greeting'
  | 'awaiting_confirmation'
  | 'thinking'
  | 'working'
  | 'speaking'

interface UseSellIASessionOptions {
  userName?: string
  onStartWorking?: () => void
  onStopWorking?: () => void
}

const CONFIRMATION_WORDS = ['sí', 'si', 'dale', 'empecemos', 'empezemos', 'vamos', 'activa', 'activar', 'sí dale', 'sí vamos']
const NEGATION_WORDS = ['no', 'cancelar', 'detener', 'pará', 'para', 'stop', 'no ahora']

export function useSellIASession(options: UseSellIASessionOptions = {}) {
  const { userName = 'Usuario', onStartWorking, onStopWorking } = options
  const [sessionState, setSessionState] = useState<SellIASessionState>('idle')
  const [lastGreetingAt, setLastGreetingAt] = useState<number>(0)
  const confirmationTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const { isSpeaking, speak, stop: stopTTS } = useTextToSpeech()

  const onStartWorkingRef = useRef(onStartWorking)
  const onStopWorkingRef = useRef(onStopWorking)
  onStartWorkingRef.current = onStartWorking
  onStopWorkingRef.current = onStopWorking

  const handleVoiceResult = useCallback((transcript: string) => {
    const normalized = transcript.toLowerCase().trim()

    setSessionState(prev => {
      if (prev !== 'awaiting_confirmation') return prev

      const confirmed = CONFIRMATION_WORDS.some(w => normalized.includes(w))
      const negated = NEGATION_WORDS.some(w => normalized.includes(w))

      if (confirmed) {
        if (confirmationTimeoutRef.current) clearTimeout(confirmationTimeoutRef.current)
        speak('Perfecto. Activando el cerebro de ventas.', () => {
          setSessionState('working')
          onStartWorkingRef.current?.()
        })
        return 'speaking'
      } else if (negated) {
        if (confirmationTimeoutRef.current) clearTimeout(confirmationTimeoutRef.current)
        speak('De acuerdo. Estoy aquí cuando me necesites.', () => {
          setSessionState('idle')
          onStopWorkingRef.current?.()
        })
        return 'speaking'
      }
      return prev
    })
  }, [speak])

  const {
    isListening,
    isSupported: voiceSupported,
    startListening,
    stopListening,
    interimTranscript,
    error: voiceError,
    resetTranscript,
  } = useVoiceRecognition({
    language: 'es-ES',
    onResult: handleVoiceResult,
  })

  const triggerGreeting = useCallback(() => {
    if (sessionState !== 'idle' && sessionState !== 'working') return

    setLastGreetingAt(Date.now())
    setSessionState('greeting')

    // Pequeña pausa antes de hablar
    setTimeout(() => {
      setSessionState('speaking')
      const greeting = `Hola ${userName}. ¿Empezamos a vender?`
      speak(greeting, () => {
        setSessionState('awaiting_confirmation')
        resetTranscript()
        startListening()

        // Timeout de 8 segundos para confirmación
        confirmationTimeoutRef.current = setTimeout(() => {
          setSessionState('idle')
          stopListening()
        }, 8000)
      })
    }, 300)
  }, [sessionState, userName, speak, startListening, stopListening, resetTranscript])

  const stopSession = useCallback(() => {
    if (confirmationTimeoutRef.current) clearTimeout(confirmationTimeoutRef.current)
    stopTTS()
    stopListening()
    setSessionState('idle')
    onStopWorking?.()
  }, [stopTTS, stopListening, onStopWorking])

  const setWorking = useCallback(() => {
    setSessionState('working')
    onStartWorking?.()
  }, [onStartWorking])

  const setIdle = useCallback(() => {
    setSessionState('idle')
    onStopWorking?.()
  }, [onStopWorking])

  // Cleanup
  useEffect(() => {
    return () => {
      if (confirmationTimeoutRef.current) clearTimeout(confirmationTimeoutRef.current)
      stopTTS()
      stopListening()
    }
  }, [stopTTS, stopListening])

  return {
    sessionState,
    isListening,
    voiceSupported,
    voiceError,
    interimTranscript,
    lastGreetingAt,
    triggerGreeting,
    stopSession,
    setWorking,
    setIdle,
  }
}
