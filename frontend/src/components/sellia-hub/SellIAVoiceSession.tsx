'use client'

/**
 * SELLIA VOICE SESSION — CORE lobe — FULL RICH REWRITE
 *
 * Large mic button with pulse, waveform SVG, transcript panel, quick command chips, status indicator, language selector.
 */

import { useState, useCallback, useEffect, useRef } from 'react'
import { Mic, MicOff, X, Globe, Zap } from 'lucide-react'

const T = {
  bgApp:       '#0B0F19',
  bgCard:      '#151B2B',
  bgCardHov:   '#1A2235',
  border:      '#2A3441',
  textPrim:    '#F3F4F6',
  textSub:     '#9CA3AF',
  violet:      '#a855f7',
  cyan:        '#06B6D4',
  emerald:     '#10B981',
  amber:       '#F59E0B',
  rose:        '#ef4444',
  glowViolet:  '0 0 22px rgba(168,85,247,0.50)',
  glowCyan:    '0 0 22px rgba(6,182,212,0.50)',
  glowEmerald: '0 0 22px rgba(16,185,129,0.50)',
} as const

type VoiceStatus = 'idle' | 'escuchando' | 'procesando' | 'respondiendo'

interface LangOption { code: string; flag: string; label: string }

const LANGUAGES: LangOption[] = [
  { code: 'es-AR', flag: '🇦🇷', label: 'Español (AR)' },
  { code: 'es-ES', flag: '🇪🇸', label: 'Español (ES)' },
  { code: 'en-US', flag: '🇺🇸', label: 'English (US)' },
  { code: 'pt-BR', flag: '🇧🇷', label: 'Português (BR)' },
  { code: 'fr-FR', flag: '🇫🇷', label: 'Français' },
  { code: 'it-IT', flag: '🇮🇹', label: 'Italiano' },
  { code: 'de-DE', flag: '🇩🇪', label: 'Deutsch' },
  { code: 'ja-JP', flag: '🇯🇵', label: '日本語' },
  { code: 'zh-CN', flag: '🇨🇳', label: '中文' },
  { code: 'ar-SA', flag: '🇸🇦', label: 'العربية' },
  { code: 'hi-IN', flag: '🇮🇳', label: 'हिन्दी' },
  { code: 'ko-KR', flag: '🇰🇷', label: '한국어' },
]

const QUICK_COMMANDS = [
  { label: 'Ver deals', color: T.emerald },
  { label: 'Crear cotización', color: T.cyan },
  { label: 'Siguiente tarea', color: T.violet },
  { label: 'Responder mensajes', color: T.amber },
  { label: 'Ver analytics', color: '#06B6D4' },
  { label: 'Lanzar campaña', color: '#ec4899' },
]

const DEMO_TRANSCRIPT: { who: 'user' | 'sellia'; text: string }[] = [
  { who: 'user',   text: 'Hola SellIA, ¿cuántos deals tengo abiertos?' },
  { who: 'sellia', text: 'Tenés 14 deals abiertos. Los 3 más urgentes son: Empresa Beta ($2,400), Moda Joven ($1,200) y Tech Solutions ($800). ¿Querés que los contacte ahora?' },
  { who: 'user',   text: 'Sí, contactá al de Empresa Beta.' },
  { who: 'sellia', text: 'Enviando mensaje a Empresa Beta por WhatsApp. Redacté una propuesta de cierre basada en el historial. Confirmá si querés que la envíe.' },
  { who: 'user',   text: 'Perfecto, enviala.' },
]

const STATUS_CONFIG: Record<VoiceStatus, { label: string; color: string; dot: string }> = {
  idle:        { label: 'Inactiva',    color: T.textSub, dot: T.border  },
  escuchando:  { label: 'Escuchando', color: T.emerald, dot: T.emerald },
  procesando:  { label: 'Procesando', color: T.amber,   dot: T.amber   },
  respondiendo:{ label: 'Respondiendo',color: T.violet,  dot: T.violet  },
}

interface SellIAVoiceSessionProps {
  userName?: string
  enabled?: boolean
  onStartWorking?: () => void
  onStopWorking?: () => void
}

export default function SellIAVoiceSession({
  userName = 'Usuario',
  enabled = true,
  onStartWorking,
  onStopWorking,
}: SellIAVoiceSessionProps) {
  const [status, setStatus] = useState<VoiceStatus>('idle')
  const [lang, setLang] = useState('es-AR')
  const [waveTick, setWaveTick] = useState(0)
  const waveRef = useRef(0)
  const cycleRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Animate waveform
  useEffect(() => {
    if (status === 'idle') return
    const id = setInterval(() => {
      waveRef.current = (waveRef.current + 1) % 1000
      setWaveTick(waveRef.current)
    }, 80)
    return () => clearInterval(id)
  }, [status])

  const waveBars = Array.from({ length: 40 }, (_, i) => {
    if (status === 'idle') return 4
    const base = ((Math.sin((waveTick + i * 6) * 0.18) + 1) / 2) * 100
    const active = status === 'escuchando' ? 0.8 : status === 'procesando' ? 0.5 : 0.65
    return Math.round(6 + base * active)
  })

  const handleMicClick = useCallback(() => {
    if (status === 'idle') {
      setStatus('escuchando')
      onStartWorking?.()
      // Demo cycle
      cycleRef.current = setTimeout(() => setStatus('procesando'), 2500)
      cycleRef.current = setTimeout(() => setStatus('respondiendo'), 4500)
      cycleRef.current = setTimeout(() => setStatus('idle'), 7000)
    } else {
      setStatus('idle')
      onStopWorking?.()
    }
  }, [status, onStartWorking, onStopWorking])

  const selectedLang = LANGUAGES.find(l => l.code === lang) ?? LANGUAGES[0]
  const st = STATUS_CONFIG[status]

  const micGlowColor =
    status === 'escuchando' ? T.emerald :
    status === 'procesando' ? T.amber :
    status === 'respondiendo' ? T.violet :
    T.border

  return (
    <section style={{ background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 16, overflow: 'hidden' }}>
      <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, #a855f780, transparent)' }} />

      {/* Header */}
      <div style={{ padding: '14px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Mic style={{ width: 16, height: 16, color: T.violet }} />
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, letterSpacing: '.06em', textTransform: 'uppercase' }}>
              Hola SellIA
              <span style={{ fontSize: 11, color: T.textSub, fontWeight: 400, textTransform: 'none', marginLeft: 8, letterSpacing: 0 }}>· sesión de voz</span>
            </div>
            <div style={{ fontSize: 11, color: T.textSub, marginTop: 2 }}>12 idiomas · hands-free · activación por voz</div>
          </div>
        </div>
        {/* Lang selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Globe style={{ width: 13, height: 13, color: T.textSub }} />
          <select value={lang} onChange={e => setLang(e.target.value)}
            style={{ background: T.bgApp, border: '1px solid ' + T.border, borderRadius: 6, padding: '5px 10px', fontSize: 11, color: T.textPrim, outline: 'none', fontFamily: 'inherit', cursor: 'pointer' }}>
            {LANGUAGES.map(l => (
              <option key={l.code} value={l.code} style={{ background: T.bgApp }}>{l.flag} {l.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Center area: mic + waveform */}
      <div style={{ padding: '28px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 20, background: T.bgApp }}>
        {/* Status indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: st.dot, boxShadow: status !== 'idle' ? '0 0 8px ' + st.dot : 'none' }} className={status !== 'idle' ? 'animate-pulse' : ''} />
          <span style={{ fontSize: 12, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: st.color }}>{st.label}</span>
        </div>

        {/* Large mic button */}
        <button onClick={enabled ? handleMicClick : undefined}
          style={{ width: 88, height: 88, borderRadius: '50%', border: '2px solid ' + micGlowColor, background: status !== 'idle' ? micGlowColor + '22' : T.bgCard, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: enabled ? 'pointer' : 'not-allowed', transition: 'all .2s', boxShadow: status !== 'idle' ? '0 0 28px ' + micGlowColor + '55, 0 0 64px ' + micGlowColor + '22' : 'none', position: 'relative', flexShrink: 0 }}>
          {status !== 'idle'
            ? <Mic style={{ width: 36, height: 36, color: micGlowColor, filter: 'drop-shadow(0 0 8px ' + micGlowColor + ')' }} className="animate-pulse" />
            : <MicOff style={{ width: 34, height: 34, color: T.textSub }} />}
          {/* outer ring pulse when listening */}
          {status === 'escuchando' && (
            <div className="animate-ping" style={{ position: 'absolute', width: 88, height: 88, borderRadius: '50%', border: '1px solid ' + T.emerald + '44' }} />
          )}
        </button>

        {/* Waveform SVG */}
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'center', gap: 2, height: 48, width: '100%', maxWidth: 320 }}>
          {waveBars.map((h, i) => {
            const color =
              status === 'escuchando' ? T.emerald :
              status === 'procesando' ? T.amber :
              status === 'respondiendo' ? T.violet :
              T.border
            return (
              <div key={i} style={{ width: 4, height: h + 'px', borderRadius: 3, background: status !== 'idle' ? `linear-gradient(180deg, ${color}, ${color}88)` : T.border + '66', boxShadow: status !== 'idle' ? '0 0 4px ' + color + '66' : 'none', transition: 'height .08s ease, background .3s' }} />
            )
          })}
        </div>

        <div style={{ fontSize: 11, color: T.textSub, textAlign: 'center' }}>
          {status === 'idle'
            ? <span>Decí <span style={{ color: T.violet, fontFamily: 'JetBrains Mono,monospace', fontWeight: 700 }}>"Hola SellIA"</span> · {selectedLang.flag} {selectedLang.label}</span>
            : status === 'escuchando'
            ? <span style={{ color: T.emerald }}>Escuchando, {userName}… ¿qué necesitás?</span>
            : status === 'procesando'
            ? <span style={{ color: T.amber }}>Procesando tu solicitud…</span>
            : <span style={{ color: T.violet }}>SellIA está respondiendo…</span>}
        </div>
      </div>

      {/* Quick command chips */}
      <div style={{ padding: '12px 20px', borderTop: '1px solid ' + T.border, borderBottom: '1px solid ' + T.border }}>
        <div style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
          <Zap style={{ width: 11, height: 11 }} /> Comandos rápidos
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {QUICK_COMMANDS.map((cmd) => (
            <button key={cmd.label}
              style={{ padding: '5px 12px', borderRadius: 20, fontSize: 11, fontWeight: 600, cursor: 'pointer', background: cmd.color + '18', border: '1px solid ' + cmd.color + '40', color: cmd.color, transition: 'all .15s' }}>
              {cmd.label}
            </button>
          ))}
        </div>
      </div>

      {/* Transcript panel */}
      <div style={{ padding: '12px 20px' }}>
        <div style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, marginBottom: 10 }}>Últimas 5 interacciones</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 200, overflowY: 'auto' }}>
          {DEMO_TRANSCRIPT.map((entry, i) => {
            const isUser = entry.who === 'user'
            return (
              <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', flexDirection: isUser ? 'row' : 'row-reverse' }}>
                <div style={{ width: 24, height: 24, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700, flexShrink: 0, background: isUser ? T.violet + '22' : T.emerald + '22', border: '1px solid ' + (isUser ? T.violet + '44' : T.emerald + '44'), color: isUser ? T.violet : T.emerald }}>
                  {isUser ? 'U' : 'IA'}
                </div>
                <div style={{ maxWidth: '75%', padding: '7px 11px', borderRadius: isUser ? '0 10px 10px 10px' : '10px 0 10px 10px', background: isUser ? T.violet + '12' : T.emerald + '0A', border: '1px solid ' + (isUser ? T.violet + '28' : T.emerald + '20') }}>
                  <div style={{ fontSize: 11, color: T.textPrim, lineHeight: 1.5 }}>{entry.text}</div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
