'use client'

/**
 * HANDS-FREE OVERLAY · voz funcional
 *
 * Captura voz real (Web Speech API vía useVoiceRecognition), transcribe en vivo,
 * resuelve la orden con `onCommand` (el shell ejecuta la tarea: navegar, abrir
 * Computer Use, etc.) y responde por voz (speechSynthesis). Si el navegador no
 * soporta reconocimiento, muestra fallback claro.
 */

import { useCallback, useEffect, useState } from 'react'
import { X, Mic, MicOff, Sparkles, MessageSquare, Loader2 } from 'lucide-react'
import { useVoiceRecognition } from '@/hooks/useVoiceRecognition'


interface HandsFreeOverlayProps {
  open: boolean
  onClose: () => void
  /** Resuelve y ejecuta la orden hablada; retorna la respuesta a decir en voz alta. */
  onCommand?: (text: string) => string
}


const PHRASES = [
  '"Hola SellIA, mostrá el pipeline de ventas."',
  '"Mostrá el cerebro neuronal."',
  '"Abrí Computer Use."',
  '"Mostrá las métricas."',
  '"Activá el piloto automático."',
]

const LANGS = ['ES', 'EN', 'PT', 'FR', 'IT', 'DE', 'JA', 'ZH', 'AR', 'HI', 'KO', 'RU']

const speak = (text: string): void => {
  try {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return
    window.speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(text)
    u.lang = 'es-ES'
    u.rate = 1.05
    window.speechSynthesis.speak(u)
  } catch { /* ignore */ }
}


export const HandsFreeOverlay = ({ open, onClose, onCommand }: HandsFreeOverlayProps): React.JSX.Element | null => {
  const [phraseIdx, setPhraseIdx] = useState(0)
  const [lastCommand, setLastCommand] = useState('')
  const [reply, setReply] = useState('')

  const handleResult = useCallback((text: string): void => {
    const clean = text.trim()
    if (!clean) return
    setLastCommand(clean)
    const r = onCommand?.(clean) ?? 'No hay handler de comandos conectado.'
    setReply(r)
    speak(r)
  }, [onCommand])

  const {
    isListening, transcript, interimTranscript, error, isSupported,
    startListening, stopListening, resetTranscript,
  } = useVoiceRecognition({ language: 'es-ES', onResult: handleResult })

  // rotación de sugerencias (sólo cuando no escucha)
  useEffect(() => {
    if (!open || isListening) return
    const id = window.setInterval(() => setPhraseIdx(i => (i + 1) % PHRASES.length), 3500)
    return () => window.clearInterval(id)
  }, [open, isListening])

  // limpiar al cerrar
  useEffect(() => {
    if (!open) { stopListening(); window.speechSynthesis?.cancel?.() }
  }, [open, stopListening])

  if (!open) return null

  const live = (interimTranscript || transcript).trim()

  return (
    <div className="fixed inset-0 z-[120] flex items-center justify-center">
      <div
        className="absolute inset-0"
        style={{
          background: 'radial-gradient(circle at 50% 50%, rgba(236,72,153,0.18), rgba(3,5,14,0.92) 65%)',
          backdropFilter: 'blur(18px)', WebkitBackdropFilter: 'blur(18px)',
        }}
      />

      <button
        type="button"
        onClick={onClose}
        className="absolute top-6 right-6 w-10 h-10 rounded-full border border-white/15 bg-white/[0.04] hover:bg-white/[0.1] flex items-center justify-center text-white/65 z-10"
        aria-label="Cerrar manos libres"
      >
        <X className="w-4 h-4" />
      </button>

      <div className="relative z-10 text-center max-w-2xl px-6">
        <OrbVisualizer active={isListening} />

        <p className="mt-10 text-[10px] font-mono tracking-[0.5em] uppercase text-pink-200/80">
          {isListening ? 'escuchando…' : 'manos libres · listo'}
        </p>

        <h2
          className="mt-4 text-[clamp(1.8rem,4.2vw,3.2rem)] font-light text-white leading-tight"
          style={{ fontFamily: '"Cormorant Garamond", Georgia, serif', letterSpacing: '-0.015em' }}
        >
          {isListening
            ? <>Te <em className="italic font-normal bg-gradient-to-r from-pink-300 to-purple-300 bg-clip-text text-transparent">escucho</em>. Dame una orden.</>
            : <>Tocá el <em className="italic font-normal bg-gradient-to-r from-pink-300 to-purple-300 bg-clip-text text-transparent">micrófono</em> y hablá.</>}
        </h2>

        {/* transcript en vivo */}
        {live && (
          <p className="mt-4 text-[15px] text-white/85" style={{ fontFamily: 'Manrope, ui-sans-serif' }}>
            “{live}”
          </p>
        )}

        {/* última orden + respuesta */}
        {!live && reply && (
          <div className="mt-4 text-[13px] text-white/70" style={{ fontFamily: 'Manrope, ui-sans-serif' }}>
            <div className="text-white/50">vos: “{lastCommand}”</div>
            <div className="mt-1 inline-flex items-center gap-1.5 text-pink-200">
              <MessageSquare className="w-3.5 h-3.5" /> {reply}
            </div>
          </div>
        )}

        {/* sugerencia rotante cuando idle y sin reply */}
        {!live && !reply && (
          <p className="mt-4 text-[14px] text-white/55 min-h-[24px]" key={phraseIdx} style={{ fontFamily: 'Manrope, ui-sans-serif' }}>
            {PHRASES[phraseIdx]}
          </p>
        )}

        {/* error / no soporte */}
        {error && <p className="mt-3 text-[12px] text-amber-300">{error}</p>}
        {!isSupported && (
          <p className="mt-3 text-[12px] text-amber-300">
            Tu navegador no soporta reconocimiento de voz. Usá Chrome/Edge.
          </p>
        )}

        {/* botón mic — start/stop */}
        <div className="mt-8 flex items-center justify-center gap-3">
          <button
            type="button"
            disabled={!isSupported}
            onClick={() => { if (isListening) { stopListening() } else { resetTranscript(); setReply(''); startListening() } }}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-2xl text-[14px] font-bold transition disabled:opacity-40"
            style={{
              background: isListening ? 'rgba(236,72,153,0.18)' : 'rgba(236,72,153,0.9)',
              border: '1px solid rgba(236,72,153,0.5)',
              color: isListening ? '#f9a8d4' : '#0a0512',
            }}
          >
            {isListening ? <><Loader2 className="w-4 h-4 animate-spin" /> Detener</> : <><Mic className="w-4 h-4" /> Hablar</>}
          </button>
          {isListening && (
            <span className="inline-flex items-center gap-1.5 text-[11px] font-mono text-white/45">
              <MicOff className="w-3.5 h-3.5" /> auto-envía tras pausa
            </span>
          )}
        </div>

        <div className="mt-6 flex flex-wrap justify-center gap-1.5">
          {LANGS.map((l) => (
            <span key={l} className="text-[9px] font-mono tracking-widest px-2 py-1 rounded-full border border-white/10 bg-white/[0.04] text-white/55">
              {l}
            </span>
          ))}
        </div>

        <div className="mt-6 flex items-center justify-center gap-2 text-[10px] font-mono text-white/45">
          <Sparkles className="w-3 h-3" />
          responde por voz · ejecuta la tarea · audio en device
        </div>
      </div>
    </div>
  )
}


const OrbVisualizer = ({ active }: { active: boolean }): React.JSX.Element => (
  <div className="relative w-44 h-44 mx-auto">
    <span
      className="absolute -inset-12 rounded-full"
      style={{
        background: 'radial-gradient(circle, rgba(236,72,153,0.35), transparent 65%)',
        animation: `brain-pulse ${active ? 1200 : 2200}ms ease-in-out infinite`,
      }}
    />
    {[0, 1, 2].map((i) => (
      <span
        key={i}
        className="absolute inset-0 rounded-full border"
        style={{
          borderColor: `rgba(236,72,153,${0.55 - i * 0.15})`,
          animation: `mic-ring ${active ? 1.8 : 2.6}s ease-out infinite`,
          animationDelay: `${i * 0.4}s`,
        }}
      />
    ))}
    <span
      className="absolute inset-6 rounded-full flex items-center justify-center"
      style={{
        background: 'radial-gradient(circle at 30% 30%, rgba(236,72,153,0.75), rgba(168,85,247,0.4) 60%, rgba(3,5,14,0.95) 100%)',
        boxShadow: '0 0 80px -10px rgba(236,72,153,0.65), inset 0 0 50px rgba(168,85,247,0.45)',
      }}
    >
      <Mic className="w-10 h-10 text-pink-100 drop-shadow-[0_0_12px_rgba(236,72,153,0.6)]" />
    </span>

    <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 flex items-end gap-1 h-8">
      {Array.from({ length: 21 }).map((_, i) => (
        <span
          key={i}
          className="w-1 rounded-full"
          style={{
            background: 'linear-gradient(to top, rgba(236,72,153,0.85), rgba(168,85,247,0.85))',
            animation: `eq-bar ${0.6 + (i % 5) * 0.12}s ease-in-out infinite alternate`,
            animationDelay: `${i * 0.04}s`,
            height: active ? `${20 + ((i * 7) % 60)}%` : '18%',
            opacity: active ? 0.9 : 0.3,
          }}
        />
      ))}
    </div>
    <Sparkles className="absolute -top-2 -right-2 w-5 h-5 text-pink-200/70" />

    <style>{`
      @keyframes mic-ring { 0% { transform: scale(0.85); opacity: 0.8; } 100% { transform: scale(1.55); opacity: 0; } }
      @keyframes eq-bar { 0% { transform: scaleY(0.4); } 100% { transform: scaleY(1.4); } }
    `}</style>
  </div>
)


export default HandsFreeOverlay
