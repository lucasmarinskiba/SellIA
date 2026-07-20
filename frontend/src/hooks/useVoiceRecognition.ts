'use client'

import { useState, useCallback, useRef, useEffect } from 'react'

interface VoiceRecognitionState {
  isListening: boolean
  transcript: string
  interimTranscript: string
  error: string | null
  isSupported: boolean
}

interface UseVoiceRecognitionOptions {
  language?: string
  onResult?: (transcript: string) => void
  onEnd?: () => void
}

export function useVoiceRecognition(options: UseVoiceRecognitionOptions = {}) {
  const { language = 'es-ES', onResult, onEnd } = options
  const [state, setState] = useState<VoiceRecognitionState>({
    isListening: false,
    transcript: '',
    interimTranscript: '',
    error: null,
    isSupported: false,
  })

  const recognitionRef = useRef<any>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (SpeechRecognition) {
      setState(prev => ({ ...prev, isSupported: true }))
    }
  }, [])

  const startListening = useCallback(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) {
      setState(prev => ({ ...prev, error: 'Speech recognition not supported in this browser' }))
      return
    }

    // Clean up previous instance
    if (recognitionRef.current) {
      recognitionRef.current.stop()
    }

    const recognition = new SpeechRecognition()
    recognition.lang = language
    recognition.continuous = true
    recognition.interimResults = true
    recognition.maxAlternatives = 1

    recognition.onstart = () => {
      setState(prev => ({
        ...prev,
        isListening: true,
        transcript: '',
        interimTranscript: '',
        error: null,
      }))
    }

    recognition.onresult = (event: any) => {
      let finalTranscript = ''
      let interim = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalTranscript += transcript
        } else {
          interim += transcript
        }
      }

      setState(prev => ({
        ...prev,
        transcript: prev.transcript + finalTranscript,
        interimTranscript: interim,
      }))

      // Auto-send after pause in speech
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
      timeoutRef.current = setTimeout(() => {
        if (finalTranscript || interim) {
          const fullText = finalTranscript || interim
          onResult?.(fullText)
          stopListening()
        }
      }, 2000)
    }

    recognition.onerror = (event: any) => {
      const errorMap: Record<string, string> = {
        'no-speech': 'No se detectó voz. Probá de nuevo.',
        'audio-capture': 'No se pudo acceder al micrófono.',
        'not-allowed': 'Permiso de micrófono denegado.',
        'network': 'Error de red. Verificá tu conexión.',
        'aborted': 'Reconocimiento cancelado.',
      }
      setState(prev => ({
        ...prev,
        error: errorMap[event.error] || `Error: ${event.error}`,
        isListening: false,
      }))
    }

    recognition.onend = () => {
      setState(prev => {
        if (prev.isListening) {
          onEnd?.()
        }
        return { ...prev, isListening: false, interimTranscript: '' }
      })
    }

    recognitionRef.current = recognition
    recognition.start()
  }, [language, onResult, onEnd])

  const stopListening = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
    if (recognitionRef.current) {
      recognitionRef.current.stop()
      recognitionRef.current = null
    }
    setState(prev => ({ ...prev, isListening: false, interimTranscript: '' }))
  }, [])

  const resetTranscript = useCallback(() => {
    setState(prev => ({ ...prev, transcript: '', interimTranscript: '', error: null }))
  }, [])

  return {
    ...state,
    startListening,
    stopListening,
    resetTranscript,
  }
}
