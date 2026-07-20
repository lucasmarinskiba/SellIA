'use client'

/**
 * VOICE COMMAND PALETTE — CORE lobe — style migration.
 * Wake-word detection, waveform, command palette, 12 idiomas.
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import {
  Mic, MicOff, Volume2, Globe, Sparkles, X, ChevronRight,
  TrendingUp, MessageCircle, DollarSign, Megaphone, Activity, Brain
} from 'lucide-react'

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

interface LangConfig {
  code: string
  flag: string
  label: string
  wakeWords: string[]
  voiceLocale: string
  greeting: string
  prompt: string
}

const LANGUAGES: LangConfig[] = [
  { code: 'es',    flag: '🇦🇷', label: 'Español (LATAM)', wakeWords: ['hola sellia', 'hey sellia', 'ok sellia', 'sellia'],       voiceLocale: 'es-AR', greeting: '¡Hola! ¿En qué te ayudo?',      prompt: 'Decí "Hola SellIA" para activar' },
  { code: 'es-es', flag: '🇪🇸', label: 'Español (España)', wakeWords: ['hola sellia', 'oye sellia', 'venga sellia'],              voiceLocale: 'es-ES', greeting: '¡Hola! ¿En qué te ayudo?',      prompt: 'Dí "Hola SellIA" para activar' },
  { code: 'en',    flag: '🇺🇸', label: 'English',         wakeWords: ['hey sellia', 'hi sellia', 'ok sellia', 'sellia'],          voiceLocale: 'en-US', greeting: 'Hi! How can I help?',           prompt: 'Say "Hey SellIA" to activate' },
  { code: 'pt',    flag: '🇧🇷', label: 'Português (BR)',   wakeWords: ['oi sellia', 'olá sellia', 'sellia'],                      voiceLocale: 'pt-BR', greeting: 'Oi! Como posso ajudar?',        prompt: 'Diga "Oi SellIA" para ativar' },
  { code: 'fr',    flag: '🇫🇷', label: 'Français',        wakeWords: ['salut sellia', 'bonjour sellia', 'eh sellia'],             voiceLocale: 'fr-FR', greeting: 'Salut! Comment puis-je aider?', prompt: 'Dis "Salut SellIA" pour activer' },
  { code: 'it',    flag: '🇮🇹', label: 'Italiano',        wakeWords: ['ciao sellia', 'ehi sellia', 'sellia'],                    voiceLocale: 'it-IT', greeting: 'Ciao! Come posso aiutare?',     prompt: 'Di\' "Ciao SellIA" per attivare' },
  { code: 'de',    flag: '🇩🇪', label: 'Deutsch',         wakeWords: ['hallo sellia', 'hey sellia', 'sellia'],                   voiceLocale: 'de-DE', greeting: 'Hallo! Wie kann ich helfen?',   prompt: 'Sag "Hallo SellIA" zum Aktivieren' },
  { code: 'ja',    flag: '🇯🇵', label: '日本語',          wakeWords: ['こんにちは sellia', 'sellia', 'ねえ sellia'],              voiceLocale: 'ja-JP', greeting: 'お手伝いします。何ですか?',   prompt: '「こんにちは SellIA」と言ってください' },
  { code: 'zh',    flag: '🇨🇳', label: '中文',            wakeWords: ['你好 sellia', 'sellia', '嘿 sellia'],                     voiceLocale: 'zh-CN', greeting: '你好! 需要什么帮助?',          prompt: '说"你好 SellIA"激活' },
  { code: 'ar',    flag: '🇸🇦', label: 'العربية',         wakeWords: ['مرحبا sellia', 'يا sellia', 'sellia'],                   voiceLocale: 'ar-SA', greeting: 'مرحبا! كيف أساعدك؟',          prompt: 'قل "مرحبا SellIA" للتفعيل' },
  { code: 'hi',    flag: '🇮🇳', label: 'हिन्दी',          wakeWords: ['namaste sellia', 'arre sellia', 'sellia'],                voiceLocale: 'hi-IN', greeting: 'नमस्ते! कैसे मदद करूं?',       prompt: '"Namaste SellIA" कहें' },
  { code: 'ko',    flag: '🇰🇷', label: '한국어',          wakeWords: ['안녕 sellia', 'sellia', '헤이 sellia'],                  voiceLocale: 'ko-KR', greeting: '안녕! 어떻게 도와드릴까요?',  prompt: '"안녕 SellIA"라고 말하세요' },
]

interface Command {
  id: string
  icon: React.ElementType
  emoji: string
  label: string
  example: string
  color: string
}

const COMMANDS: Command[] = [
  { id: 'cmd1', icon: TrendingUp,    emoji: '📈', label: 'Hacé crecer la cuenta',       example: '"SellIA, ayúdame a crecer la cuenta"',          color: T.emerald },
  { id: 'cmd2', icon: DollarSign,    emoji: '💰', label: 'Cerrá ventas pendientes',     example: '"SellIA, cerrá los deals abiertos"',            color: '#10B981' },
  { id: 'cmd3', icon: MessageCircle, emoji: '💬', label: 'Respondé mensajes',           example: '"SellIA, contestá WhatsApp e Instagram"',       color: T.cyan    },
  { id: 'cmd4', icon: Megaphone,     emoji: '📣', label: 'Lanzá una campaña',           example: '"SellIA, lanzá ads en Meta y TikTok"',          color: '#ec4899' },
  { id: 'cmd5', icon: Sparkles,      emoji: '✨', label: 'Creá contenido viral',        example: '"SellIA, hacé 3 reels para esta semana"',       color: T.amber   },
  { id: 'cmd6', icon: Activity,      emoji: '🩺', label: 'Diagnóstico del negocio',     example: '"SellIA, decime qué está mal y solucionalo"',   color: T.rose    },
  { id: 'cmd7', icon: Brain,         emoji: '🧠', label: 'Consultá al consejo',         example: '"SellIA, qué estrategia aplicarías aquí?"',     color: T.violet  },
  { id: 'cmd8', icon: Globe,         emoji: '🌐', label: 'Posicioná la marca',          example: '"SellIA, posicioná mi marca en mi ciudad"',     color: '#3b82f6' },
]

interface VoiceCommandPaletteProps {
  userName?: string
}

export default function VoiceCommandPalette({ userName = 'Lucas' }: VoiceCommandPaletteProps) {
  const [lang, setLang] = useState<LangConfig>(LANGUAGES[0])
  const [listening, setListening] = useState(true)
  const [activated, setActivated] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [waveTick, setWaveTick] = useState(0)
  const wavRef = useRef<number>(0)

  useEffect(() => {
    if (!listening && !activated) return
    const id = setInterval(() => {
      wavRef.current = (wavRef.current + 1) % 1000
      setWaveTick(wavRef.current)
    }, 80)
    return () => clearInterval(id)
  }, [listening, activated])

  const handleDemoWake = useCallback(() => {
    setSpeaking(true)
    setActivated(true)
    setTimeout(() => setSpeaking(false), 2400)
  }, [])

  const handleDeactivate = useCallback(() => {
    setActivated(false)
    setSpeaking(false)
  }, [])

  const waveBars = Array.from({ length: 32 }, (_, i) => {
    const base = ((Math.sin((waveTick + i * 7) * 0.15) + 1) / 2) * 100
    return Math.round(20 + base * 0.6)
  })

  return (
    <section style={{ background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 16, overflow: 'hidden' }}>
      <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, #06B6D480, transparent)' }} />

      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ position: 'relative', width: 40, height: 40, borderRadius: 10, background: T.cyan + '22', border: '1px solid ' + T.cyan + '44', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Mic style={{ width: 20, height: 20, color: T.cyan, filter: 'drop-shadow(0 0 8px rgba(6,182,212,0.7))' }} className={listening ? 'animate-pulse' : ''} />
            {listening && (
              <div className="animate-ping" style={{ position: 'absolute', top: -4, right: -4, width: 12, height: 12, borderRadius: '50%', background: T.emerald, border: '2px solid ' + T.bgCard }} />
            )}
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, letterSpacing: '.06em', textTransform: 'uppercase' }}>VOICE COMMAND</div>
              <span style={{ fontSize: 11, color: T.textSub, fontWeight: 400, textTransform: 'none' }}>· 12 idiomas · hands-free</span>
              <span style={{ padding: '2px 8px', borderRadius: 20, fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', background: T.emerald + '18', border: '1px solid ' + T.emerald + '40', color: T.emerald }}>
                {listening ? '● ESCUCHANDO' : '○ INACTIVO'}
              </span>
            </div>
            <div style={{ fontSize: 11, color: T.textSub, marginTop: 2 }}>
              Decí <span style={{ color: T.cyan, fontFamily: 'JetBrains Mono,monospace', fontWeight: 700 }}>"{lang.wakeWords[0]}"</span> + lo que querés
            </div>
          </div>
        </div>

        {/* Lang selector */}
        <select value={lang.code} onChange={e => { const next = LANGUAGES.find(l => l.code === e.target.value); if (next) setLang(next) }}
          style={{ background: T.bgApp, border: '1px solid ' + T.border, borderRadius: 8, padding: '6px 12px', fontSize: 11, color: T.textPrim, outline: 'none', fontFamily: 'inherit', cursor: 'pointer' }}>
          {LANGUAGES.map(l => (
            <option key={l.code} value={l.code} style={{ background: T.bgApp }}>{l.flag} {l.label}</option>
          ))}
        </select>
      </div>

      {/* Waveform area */}
      <div style={{ padding: '24px 20px', background: T.bgApp, position: 'relative' }}>
        {/* Bars */}
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'center', gap: 3, height: 80 }}>
          {waveBars.map((h, i) => (
            <div key={i} style={{ width: 4, borderRadius: 3, height: (listening || activated ? h : 6) + 'px', background: activated ? `linear-gradient(180deg, ${T.cyan}, #3b82f6)` : listening ? `linear-gradient(180deg, ${T.cyan}bb, ${T.cyan}44)` : T.border + '44', boxShadow: (activated || listening) ? '0 0 5px ' + (activated ? T.cyan : T.cyan + '55') : 'none', transition: 'height .08s ease' }} />
          ))}
        </div>

        {/* Transcript / prompt */}
        <div style={{ textAlign: 'center', marginTop: 14, minHeight: 48 }}>
          {activated ? (
            <>
              <div style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.cyan, marginBottom: 6 }}>
                {speaking ? '🔊 SellIA hablando' : '🎙 Escuchando comando…'}
              </div>
              <div style={{ fontSize: 13, color: T.textPrim, fontStyle: speaking ? 'italic' : 'normal' }}>
                {speaking ? <span style={{ color: T.cyan }}>"{lang.greeting}"</span> : <span style={{ color: T.textSub + 'aa' }}>Esperando indicación…</span>}
              </div>
            </>
          ) : (
            <>
              <div style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, marginBottom: 8 }}>{lang.prompt}</div>
              <button onClick={handleDemoWake}
                style={{ padding: '6px 18px', borderRadius: 8, fontSize: 11, cursor: 'pointer', background: T.cyan + '18', border: '1px solid ' + T.cyan + '40', color: T.cyan, transition: 'all .15s' }}>
                ▶ Simular activación
              </button>
            </>
          )}
        </div>

        {activated && (
          <button onClick={handleDeactivate}
            style={{ position: 'absolute', top: 10, right: 10, width: 28, height: 28, borderRadius: '50%', background: T.bgCard, border: '1px solid ' + T.border, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}>
            <X style={{ width: 14, height: 14, color: T.textSub }} />
          </button>
        )}
      </div>

      {/* Wake words */}
      <div style={{ padding: '10px 20px', borderTop: '1px solid ' + T.border, borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub }}>Wake words {lang.flag}:</span>
        {lang.wakeWords.map(w => (
          <span key={w} style={{ padding: '2px 8px', borderRadius: 4, fontSize: 10, fontFamily: 'JetBrains Mono,monospace', background: T.cyan + '14', border: '1px solid ' + T.cyan + '30', color: T.cyan }}>"{w}"</span>
        ))}
      </div>

      {/* Command palette */}
      <div style={{ padding: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
          <Sparkles style={{ width: 11, height: 11, color: T.textSub }} />
          <div style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub }}>COMANDOS HANDS-FREE</div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          {COMMANDS.map(cmd => {
            const Icon = cmd.icon
            return (
              <div key={cmd.id} style={{ background: cmd.color + '06', border: '1px solid ' + cmd.color + '22', borderRadius: 10, overflow: 'hidden', cursor: 'pointer', transition: 'background .15s' }}>
                <div style={{ height: 2, background: `linear-gradient(90deg, ${cmd.color}cc, transparent)` }} />
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: '10px 12px' }}>
                  <div style={{ width: 38, height: 38, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, background: cmd.color + '18', border: '1px solid ' + cmd.color + '30' }}>
                    <Icon style={{ width: 16, height: 16, color: cmd.color }} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                      <span style={{ fontSize: 14 }}>{cmd.emoji}</span>
                      <div style={{ fontSize: 12, fontWeight: 700, color: T.textPrim }}>{cmd.label}</div>
                    </div>
                    <div style={{ fontSize: 11, color: T.textSub, fontStyle: 'italic' }}>{cmd.example}</div>
                  </div>
                  <ChevronRight style={{ width: 12, height: 12, color: T.textSub + '55', flexShrink: 0, alignSelf: 'center' }} />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Voice config footer */}
      <div style={{ borderTop: '1px solid ' + T.border, padding: '12px 20px', background: T.cyan + '06', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: T.textSub }}>
          <Volume2 style={{ width: 12, height: 12, color: T.cyan }} />
          <span>Voz: <span style={{ color: T.cyan, fontWeight: 700 }}>Sofia ES-AR · neural</span></span>
          <span style={{ color: T.border }}>·</span>
          <span style={{ fontFamily: 'JetBrains Mono,monospace' }}>{lang.voiceLocale}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button style={{ padding: '5px 12px', borderRadius: 8, fontSize: 11, cursor: 'pointer', background: T.bgApp, border: '1px solid ' + T.border, color: T.textSub }}>
            Probar voz
          </button>
          <button onClick={() => setListening(l => !l)}
            style={{ padding: '5px 12px', borderRadius: 8, fontSize: 11, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, background: listening ? T.emerald + '18' : T.bgApp, border: '1px solid ' + (listening ? T.emerald + '44' : T.border), color: listening ? T.emerald : T.textSub }}>
            {listening ? <><Mic style={{ width: 12, height: 12 }} /> Always-on</> : <><MicOff style={{ width: 12, height: 12 }} /> Activar mic</>}
          </button>
        </div>
      </div>
    </section>
  )
}
