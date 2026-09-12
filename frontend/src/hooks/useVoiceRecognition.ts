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
  const { language = 'es-AR', onResult, onEnd } = options
  const [state, setState] = useState<VoiceRecognitionState>({
    isListening: false,
    transcript: '',
    interimTranscript: '',
    error: null,
    isSupported: false,
  })

  const recognitionRef = useRef<any>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)
  // Full utterance accumulated across every `onresult` event in this
  // listening session — `event.resultIndex` only covers the newest chunk,
  // so without this the 2s-pause auto-send fired with just the last
  // fragment of a longer/paused sentence instead of the whole thing.
  const fullFinalRef = useRef('')
  // True while the user wants to keep listening (i.e. hasn't called
  // stopListening) — lets `onend` auto-restart if the browser/OS cuts the
  // session on its own, instead of hands-free just going silent.
  const shouldListenRef = useRef(false)

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (SpeechRecognition) {
      setState(prev => ({ ...prev, isSupported: true }))
    }
  }, [])

  const stopListening = useCallback(() => {
    shouldListenRef.current = false
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

  const startListening = useCallback(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) {
      setState(prev => ({ ...prev, error: 'Speech recognition not supported in this browser' }))
      return
    }

    // Clean up previous instance
    if (recognitionRef.current) {
      try { recognitionRef.current.stop() } catch { /* already stopped */ }
    }

    fullFinalRef.current = ''
    shouldListenRef.current = true

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
      let newFinal = ''
      let interim = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          newFinal += transcript
        } else {
          interim += transcript
        }
      }

      if (newFinal) fullFinalRef.current += newFinal

      setState(prev => ({
        ...prev,
        transcript: prev.transcript + newFinal,
        interimTranscript: interim,
      }))

      // Auto-send the FULL accumulated utterance after a pause in speech —
      // not just this event's fragment, so longer/paused sentences arrive
      // whole instead of truncated to their last few words.
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
      timeoutRef.current = setTimeout(() => {
        const fullText = (fullFinalRef.current || interim).trim()
        if (fullText) {
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
      // A recoverable error (e.g. a transient no-speech timeout) shouldn't
      // kill hands-free if the user is still trying to talk — only stop
      // listening outright on errors that mean the mic itself is unusable.
      const fatal = event.error === 'not-allowed' || event.error === 'audio-capture'
      if (fatal) shouldListenRef.current = false
      setState(prev => ({
        ...prev,
        error: errorMap[event.error] || `Error: ${event.error}`,
        isListening: fatal ? false : prev.isListening,
      }))
    }

    recognition.onend = () => {
      // The browser/OS can end a "continuous" session on its own (silence
      // timeout, tab throttling, etc.). If the user never asked to stop,
      // restart automatically so hands-free doesn't just go quiet.
      if (shouldListenRef.current) {
        try {
          recognition.start()
          return
        } catch {
          // fall through to reporting "not listening" below
        }
      }
      setState(prev => {
        if (prev.isListening) {
          onEnd?.()
        }
        return { ...prev, isListening: false, interimTranscript: '' }
      })
    }

    recognitionRef.current = recognition
    try {
      recognition.start()
    } catch {
      setState(prev => ({ ...prev, error: 'No se pudo iniciar el micrófono. Probá de nuevo.' }))
    }
  }, [language, onResult, onEnd, stopListening])

  const resetTranscript = useCallback(() => {
    fullFinalRef.current = ''
    setState(prev => ({ ...prev, transcript: '', interimTranscript: '', error: null }))
  }, [])

  return {
    ...state,
    startListening,
    stopListening,
    resetTranscript,
  }
}
