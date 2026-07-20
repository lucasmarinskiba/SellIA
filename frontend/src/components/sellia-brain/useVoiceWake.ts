'use client'

/**
 * useVoiceWake — Web Speech API wake-word hook
 *
 * 1. Requests microphone permission (getUserMedia)
 * 2. Starts SpeechRecognition in continuous mode
 * 3. Fires onWake() when any wake phrase is detected
 *
 * Browser support: Chrome/Edge/Safari. Firefox = unsupported (graceful fallback).
 */

import { useCallback, useEffect, useRef, useState } from 'react'

// ── Wake phrases (lowercase, accents stripped) ─────────────────────────────────
const DEFAULT_WAKE_PHRASES = [
  'hola sellia', 'hola sellía', 'ok sellia', 'hey sellia',
  'oye sellia', 'sellia escucha', 'sellia activate',
]

// Minimal speech-recognition shape (cross-browser)
interface SpeechResult { 0: { transcript: string }; isFinal: boolean }
interface SpeechResultEvent extends Event { results: ArrayLike<SpeechResult>; resultIndex: number }
interface SpeechErrorEvent extends Event { error: string }

interface SpeechRecognitionLike extends EventTarget {
  continuous: boolean
  interimResults: boolean
  lang: string
  start: () => void
  stop: () => void
  onresult: ((e: SpeechResultEvent) => void) | null
  onerror:  ((e: SpeechErrorEvent) => void) | null
  onend:    (() => void)            | null
  onstart:  (() => void)            | null
}

type SpeechRecognitionCtor = new () => SpeechRecognitionLike

const getSpeechRecognition = (): SpeechRecognitionCtor | null => {
  if (typeof window === 'undefined') return null
  const w = window as unknown as { SpeechRecognition?: SpeechRecognitionCtor; webkitSpeechRecognition?: SpeechRecognitionCtor }
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null
}

const norm = (s: string): string =>
  s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').trim()

export type VoiceState = 'idle' | 'requesting' | 'listening' | 'denied' | 'unsupported' | 'error'

interface UseVoiceWakeOpts {
  onWake?: (transcript: string) => void
  wakePhrases?: string[]
  lang?: string
}

interface UseVoiceWakeResult {
  state:       VoiceState
  transcript:  string
  lastWake:    string | null
  errorMsg:    string | null
  start:       () => Promise<void>
  stop:        () => void
  toggle:      () => void
  isListening: boolean
}

export const useVoiceWake = ({ onWake, wakePhrases, lang = 'es-AR' }: UseVoiceWakeOpts = {}): UseVoiceWakeResult => {
  const [state, setState]            = useState<VoiceState>('idle')
  const [transcript, setTranscript]  = useState('')
  const [lastWake, setLastWake]      = useState<string | null>(null)
  const [errorMsg, setErrorMsg]      = useState<string | null>(null)
  const recogRef                     = useRef<SpeechRecognitionLike | null>(null)
  const restartRef                   = useRef(true)
  const phrases = wakePhrases ?? DEFAULT_WAKE_PHRASES

  const detectWake = useCallback((text: string): boolean => {
    const n = norm(text)
    return phrases.some(p => n.includes(norm(p)))
  }, [phrases])

  const start = useCallback(async (): Promise<void> => {
    const Ctor = getSpeechRecognition()
    if (!Ctor) { setState('unsupported'); setErrorMsg('Tu navegador no soporta reconocimiento de voz'); return }

    // Request mic permission first (no audio kept — recognition handles its own stream)
    setState('requesting')
    setErrorMsg(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      // Stop stream immediately — only needed for permission grant
      stream.getTracks().forEach(t => t.stop())
    } catch (e) {
      setState('denied')
      setErrorMsg('Permiso de micrófono denegado')
      return
    }

    // Start recognition
    const recog = new Ctor()
    recog.continuous = true
    recog.interimResults = true
    recog.lang = lang

    recog.onstart = (): void => { setState('listening') }

    recog.onresult = (e: SpeechResultEvent): void => {
      let interim = ''
      let finalText = ''
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const r = e.results[i]
        const txt = r[0].transcript
        if (r.isFinal) finalText += txt
        else interim += txt
      }
      const combined = (finalText + ' ' + interim).trim()
      setTranscript(combined)
      if (detectWake(combined)) {
        setLastWake(combined)
        if (onWake) onWake(combined)
      }
    }

    recog.onerror = (e): void => {
      const ev = e as SpeechErrorEvent
      if (ev.error === 'not-allowed' || ev.error === 'service-not-allowed') {
        setState('denied')
        setErrorMsg('Permiso de micrófono denegado')
        restartRef.current = false
      } else if (ev.error === 'no-speech' || ev.error === 'aborted') {
        // benign — let onend restart
      } else {
        setState('error')
        setErrorMsg(`Error: ${ev.error}`)
      }
    }

    recog.onend = (): void => {
      // Auto-restart for continuous wake listening (browser stops after ~60s by default)
      if (restartRef.current) {
        try { recog.start() } catch { /* already started */ }
      } else {
        setState('idle')
      }
    }

    recogRef.current = recog
    restartRef.current = true
    try {
      recog.start()
    } catch {
      // Already started — ignore
    }
  }, [detectWake, lang, onWake])

  const stop = useCallback((): void => {
    restartRef.current = false
    if (recogRef.current) {
      try { recogRef.current.stop() } catch { /* noop */ }
      recogRef.current = null
    }
    setState('idle')
    setTranscript('')
  }, [])

  const toggle = useCallback((): void => {
    if (state === 'listening' || state === 'requesting') stop()
    else void start()
  }, [state, start, stop])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      restartRef.current = false
      if (recogRef.current) {
        try { recogRef.current.stop() } catch { /* noop */ }
      }
    }
  }, [])

  return {
    state,
    transcript,
    lastWake,
    errorMsg,
    start,
    stop,
    toggle,
    isListening: state === 'listening',
  }
}
