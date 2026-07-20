'use client'

import { useState, useCallback, useRef } from 'react'

interface UseTextToSpeechReturn {
  isSpeaking: boolean
  isSupported: boolean
  speak: (text: string, onEnd?: () => void) => void
  stop: () => void
}

export function useTextToSpeech(): UseTextToSpeechReturn {
  const [isSpeaking, setIsSpeaking] = useState(false)
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null)

  const isSupported = typeof window !== 'undefined' && 'speechSynthesis' in window

  const speak = useCallback((text: string, onEnd?: () => void) => {
    if (!isSupported) return

    // Stop any current speech
    window.speechSynthesis.cancel()

    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'es-ES'
    utterance.rate = 1.0
    utterance.pitch = 1.0

    // Try to find a Spanish voice
    const voices = window.speechSynthesis.getVoices()
    const spanishVoice = voices.find(
      v => v.lang.startsWith('es') || v.name.toLowerCase().includes('spanish') || v.name.toLowerCase().includes('español')
    )
    if (spanishVoice) {
      utterance.voice = spanishVoice
    }

    utterance.onstart = () => setIsSpeaking(true)
    utterance.onend = () => {
      setIsSpeaking(false)
      onEnd?.()
    }
    utterance.onerror = () => {
      setIsSpeaking(false)
      onEnd?.()
    }

    utteranceRef.current = utterance
    window.speechSynthesis.speak(utterance)
  }, [isSupported])

  const stop = useCallback(() => {
    if (!isSupported) return
    window.speechSynthesis.cancel()
    setIsSpeaking(false)
  }, [isSupported])

  return { isSpeaking, isSupported, speak, stop }
}
