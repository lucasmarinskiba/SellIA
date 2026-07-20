'use client'

/**
 * AUTONOMOUS MODE
 *
 * Panel de control del modo autónomo total. El usuario define:
 *   - ON/OFF master switch
 *   - Confidence threshold (60-100%): a partir de qué confianza la IA actúa sola
 *   - Per-action permissions: qué cosas puede hacer sola, qué requiere aprobación
 *
 * Muestra stats de las últimas 24h de operación autónoma.
 */

import { useState } from 'react'
import {
  Power, Shield, Lock, Unlock, AlertTriangle, CheckCircle2,
  Bot, Activity, Eye, EyeOff, Sliders, Crown, Sparkles,
  DollarSign
} from 'lucide-react'

const T = {
  bgApp:       '#0B0F19',
  bgCard:      '#151B2B',
  bgCardHov:   '#1A2235',
  border:      '#2A3441',
  textPrim:    '#F3F4F6',
  textSub:     '#9CA3AF',
  violet:      '#8B5CF6',
  emerald:     '#10B981',
  amber:       '#F59E0B',
  rose:        '#ef4444',
  cyan:        '#06B6D4',
  glowViolet:  '0 0 22px rgba(139,92,246,0.50)',
  glowEmerald: '0 0 22px rgba(16,185,129,0.50)',
  glowAmber:   '0 0 22px rgba(245,158,11,0.45)',
} as const

interface Permission {
  id: string
  emoji: string
  label: string
  description: string
  mode: 'auto' | 'guarded' | 'manual'
  thresholdLabel: string
  todayCount: number
  successRate?: number
}

const PERMISSIONS: Permission[] = [
  { id: 'p1',  emoji: '💬', label: 'Enviar mensajes (WhatsApp/IG/Email)',   description: 'Respuestas, follow-ups, cold outreach',          mode: 'auto',    thresholdLabel: 'Confianza ≥ 70% · sin límite',      todayCount: 142, successRate: 87 },
  { id: 'p2',  emoji: '🎯', label: 'Calificar y mover leads en CRM',       description: 'Scoring IA + transiciones de etapa automáticas',  mode: 'auto',    thresholdLabel: 'Auto-evaluación',                   todayCount: 47,  successRate: 92 },
  { id: 'p3',  emoji: '🤝', label: 'Cerrar deals < $1,000',                description: 'Auto-cierre con protocolo de conversión IA',     mode: 'auto',    thresholdLabel: 'Confianza ≥ 85% · < $1k',           todayCount: 8,   successRate: 78 },
  { id: 'p4',  emoji: '💰', label: 'Aplicar descuentos < 15%',             description: 'Promociones, escasez, cierre',                  mode: 'auto',    thresholdLabel: 'Sin aprobación · < 15%',             todayCount: 12 },
  { id: 'p5',  emoji: '📦', label: 'Auto-orden de reposición de stock',    description: 'Detecta crítico y dispara orden',                mode: 'auto',    thresholdLabel: 'Stock < umbral seguridad',           todayCount: 4  },
  { id: 'p6',  emoji: '🧾', label: 'Facturación AFIP y emisión recibos',   description: 'Automatización sobre portal fiscal',            mode: 'auto',    thresholdLabel: 'Tras confirmación pago',             todayCount: 8  },
  { id: 'p7',  emoji: '🚚', label: 'Coordinar envíos con courier',         description: 'Andreani, OCA, Correo Argentino',               mode: 'auto',    thresholdLabel: 'Tras factura emitida',               todayCount: 6  },
  { id: 'p8',  emoji: '💸', label: 'Cerrar deals > $1,000',                description: 'Deals grandes requieren tu OK',                 mode: 'guarded', thresholdLabel: 'Aprobación 1-click',                 todayCount: 3  },
  { id: 'p9',  emoji: '🎁', label: 'Descuentos 15-30%',                    description: 'Promociones agresivas',                         mode: 'guarded', thresholdLabel: 'Aprobación rápida',                  todayCount: 2  },
  { id: 'p10', emoji: '↩️', label: 'Reembolsos y cancelaciones',           description: 'Toda operación financiera reversible',          mode: 'manual',  thresholdLabel: 'Solo vos podés',                     todayCount: 0  },
  { id: 'p11', emoji: '🔐', label: 'Cambios de plan / billing',            description: 'Suscripciones, upgrades, downgrades',          mode: 'manual',  thresholdLabel: 'Solo vos podés',                     todayCount: 0  },
]

const MODE_CONFIG = {
  auto:    { label: 'Autónomo',   icon: Unlock, color: '#22c55e' },
  guarded: { label: 'Con guarda', icon: Shield, color: T.amber   },
  manual:  { label: 'Manual',     icon: Lock,   color: T.rose    },
} as const

const STATS_24H = [
  { label: 'Decisiones autónomas', value: '187',    sub: 'sin tu intervención',  icon: Bot,           color: T.violet  },
  { label: 'Override rate',         value: '2%',     sub: '4 correcciones tuyas', icon: AlertTriangle, color: T.amber   },
  { label: 'Win rate decisiones',   value: '87%',    sub: 'aciertos IA solo',     icon: CheckCircle2,  color: '#22c55e' },
  { label: 'Revenue autónomo',      value: '$2,847', sub: 'cerrado sin vos',      icon: DollarSign,    color: T.emerald },
]

export default function AutonomousMode() {
  const [enabled, setEnabled] = useState(true)
  const [confidenceThreshold, setConfidenceThreshold] = useState(75)
  const [showSensitive, setShowSensitive] = useState(false)

  const autoCount    = PERMISSIONS.filter(p => p.mode === 'auto').length
  const guardedCount = PERMISSIONS.filter(p => p.mode === 'guarded').length
  const manualCount  = PERMISSIONS.filter(p => p.mode === 'manual').length

  return (
    <section style={{
      background: T.bgCard,
      border: `1px solid ${enabled ? T.emerald + '50' : T.border}`,
      borderRadius: 16,
      overflow: 'hidden',
    }}>
      <div style={{ height: 1, background: `linear-gradient(90deg, transparent, ${enabled ? T.emerald + '80' : 'rgba(255,255,255,0.15)'}, transparent)` }} />

      {/* Header with master ON/OFF */}
      <div style={{ padding: '20px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {/* Power core */}
          <div style={{ position: 'relative', width: 56, height: 56, flexShrink: 0 }}>
            <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }} viewBox="0 0 56 56">
              <defs>
                <linearGradient id="powerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor={enabled ? T.emerald : '#6b7280'} />
                  <stop offset="100%" stopColor={enabled ? '#22c55e' : '#9ca3af'} />
                </linearGradient>
              </defs>
              <circle cx="28" cy="28" r="24" fill="none" stroke="url(#powerGrad)" strokeWidth="2" strokeDasharray="60 90" strokeLinecap="round" opacity={enabled ? 0.9 : 0.3} />
            </svg>
            <div style={{
              position: 'absolute', inset: 8, borderRadius: '50%',
              background: enabled ? `linear-gradient(135deg, ${T.emerald}30, #22c55e20)` : 'rgba(255,255,255,0.04)',
              border: `2px solid ${enabled ? T.emerald + '80' : 'rgba(255,255,255,0.10)'}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Power style={{ width: 20, height: 20, color: enabled ? '#22c55e' : T.textSub, filter: enabled ? 'drop-shadow(0 0 8px rgba(34,197,94,0.8))' : 'none' }} />
            </div>
            {enabled && (
              <div className="animate-pulse" style={{ position: 'absolute', bottom: -4, right: -4, width: 16, height: 16, borderRadius: '50%', background: T.emerald, border: `2px solid ${T.bgCard}` }} />
            )}
          </div>

          <div>
            <h2 style={{ fontSize: 13, fontWeight: 700, letterSpacing: '.08em', textTransform: 'uppercase', margin: 0, display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
              <span style={{ color: enabled ? T.emerald : T.textSub }}>MODO AUTÓNOMO</span>
              {enabled && (
                <span className="animate-pulse" style={{
                  fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase',
                  padding: '2px 8px', borderRadius: 12,
                  background: `${T.emerald}18`, border: `1px solid ${T.emerald}28`, color: T.emerald,
                }}>OPERANDO 24/7</span>
              )}
            </h2>
            <p style={{ fontSize: 11, color: T.textSub, margin: 0, marginTop: 4 }}>
              {enabled
                ? 'La IA toma decisiones sin tu supervisión · vos solo aprobás lo crítico'
                : 'IA esperando tu aprobación en cada paso · más lenta · más manual'}
            </p>
          </div>
        </div>

        {/* Toggle */}
        <button
          onClick={() => setEnabled(e => !e)}
          style={{
            display: 'flex', alignItems: 'center', gap: 12, padding: '4px 4px 4px 16px', borderRadius: 20,
            background: enabled ? `linear-gradient(135deg, ${T.emerald}20, ${T.emerald}10)` : 'rgba(255,255,255,0.04)',
            border: `2px solid ${enabled ? T.emerald + '50' : 'rgba(255,255,255,0.15)'}`,
            boxShadow: enabled ? `0 0 20px ${T.emerald}25` : 'none',
            cursor: 'pointer',
          }}
        >
          <span style={{ fontSize: 14, fontWeight: 700, color: enabled ? T.emerald : T.textSub }}>
            {enabled ? 'ON' : 'OFF'}
          </span>
          <div style={{ position: 'relative', width: 64, height: 32, borderRadius: 16, background: enabled ? `${T.emerald}40` : 'rgba(255,255,255,0.10)' }}>
            <div style={{
              position: 'absolute', top: 2, width: 28, height: 28, borderRadius: '50%',
              left: enabled ? 'calc(100% - 30px)' : '2px',
              background: enabled ? T.emerald : '#374151',
              boxShadow: enabled ? '0 0 12px rgba(34,197,94,0.8)' : '0 0 4px rgba(0,0,0,0.4)',
              transition: 'all 0.3s',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Power style={{ width: 12, height: 12, color: '#fff' }} />
            </div>
          </div>
        </button>
      </div>

      {/* Stats 24h */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', borderBottom: `1px solid ${T.border}` }}>
        {STATS_24H.map((s, i) => {
          const Icon = s.icon
          return (
            <div key={s.label} style={{ padding: 12, borderRight: i < 3 ? `1px solid ${T.border}` : undefined }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                <Icon style={{ width: 12, height: 12, color: s.color }} />
                <p style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, margin: 0, fontWeight: 700 }}>{s.label}</p>
              </div>
              <p style={{ fontSize: 20, fontWeight: 900, color: s.color, margin: 0, textShadow: `0 0 20px ${s.color}88` }}>{s.value}</p>
              <p style={{ fontSize: 9, color: T.textSub, margin: 0, marginTop: 2 }}>{s.sub}</p>
            </div>
          )
        })}
      </div>

      {/* Confidence threshold */}
      <div style={{ padding: '20px', borderBottom: `1px solid ${T.border}` }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10, flexWrap: 'wrap', gap: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Sliders style={{ width: 16, height: 16, color: T.violet }} />
            <p style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.violet, fontWeight: 700, margin: 0 }}>Umbral de confianza</p>
          </div>
          <span style={{ fontSize: 10, color: T.textSub }}>
            IA actúa sola cuando estima ≥ <span style={{ fontWeight: 700, color: T.textPrim, textShadow: '0 0 20px #F3F4F688' }}>{confidenceThreshold}%</span> de éxito
          </span>
        </div>
        <input
          type="range"
          min={60} max={95} step={5}
          value={confidenceThreshold}
          onChange={e => setConfidenceThreshold(Number(e.target.value))}
          disabled={!enabled}
          style={{
            width: '100%', height: 8, borderRadius: 4, appearance: 'none', cursor: enabled ? 'pointer' : 'not-allowed', opacity: enabled ? 1 : 0.5,
            background: `linear-gradient(to right, ${T.rose} 0%, ${T.amber} ${((75 - 60) / (95 - 60)) * 100}%, #22c55e 100%)`,
          }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, fontSize: 9, color: T.textSub, fontFamily: 'monospace' }}>
          <span>60% · Más arriesgada</span>
          <span>75% · Balanceada</span>
          <span>95% · Conservadora</span>
        </div>
      </div>

      {/* Permissions summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', borderBottom: `1px solid ${T.border}` }}>
        {[
          { label: 'Autónomas',   count: autoCount,    icon: Unlock, color: '#22c55e', description: 'IA hace sola' },
          { label: 'Con guarda',  count: guardedCount, icon: Shield, color: T.amber,   description: 'Aprobás 1-click' },
          { label: 'Manuales',    count: manualCount,  icon: Lock,   color: T.rose,    description: 'Solo vos' },
        ].map((s, i) => {
          const Icon = s.icon
          return (
            <div key={s.label} style={{ padding: 12, borderRight: i < 2 ? `1px solid ${T.border}` : undefined }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <div style={{ width: 28, height: 28, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', background: `${s.color}18`, border: `1px solid ${s.color}30` }}>
                  <Icon style={{ width: 14, height: 14, color: s.color }} />
                </div>
                <div>
                  <p style={{ fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, fontWeight: 700, margin: 0 }}>{s.label}</p>
                  <p style={{ fontSize: 18, fontWeight: 900, color: s.color, margin: 0, textShadow: `0 0 20px ${s.color}88` }}>{s.count}</p>
                </div>
              </div>
              <p style={{ fontSize: 10, color: T.textSub, margin: 0 }}>{s.description}</p>
            </div>
          )
        })}
      </div>

      {/* Permissions matrix */}
      <div style={{ padding: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Crown style={{ width: 16, height: 16, color: T.amber }} />
            <h3 style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.amber, fontWeight: 700, margin: 0 }}>Matriz de permisos</h3>
          </div>
          <button
            onClick={() => setShowSensitive(s => !s)}
            style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, color: T.textSub, background: 'none', border: 'none', cursor: 'pointer' }}
          >
            {showSensitive ? <EyeOff style={{ width: 12, height: 12 }} /> : <Eye style={{ width: 12, height: 12 }} />}
            {showSensitive ? 'Ocultar sensibles' : 'Ver sensibles'}
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {PERMISSIONS.filter(p => showSensitive || p.mode !== 'manual').map(perm => {
            const cfg = MODE_CONFIG[perm.mode]
            const Icon = cfg.icon
            return (
              <div key={perm.id} style={{
                display: 'flex', alignItems: 'center', gap: 12, padding: 12, borderRadius: 10,
                background: `${cfg.color}10`, border: `1px solid ${cfg.color}30`,
              }}>
                <span style={{ fontSize: 18, flexShrink: 0 }}>{perm.emoji}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 2 }}>
                    <p style={{ fontSize: 14, fontWeight: 600, color: T.textPrim, margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{perm.label}</p>
                    <span style={{
                      display: 'inline-flex', alignItems: 'center', gap: 4,
                      fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', fontWeight: 700,
                      padding: '2px 6px', borderRadius: 4,
                      background: `${cfg.color}20`, color: cfg.color,
                    }}>
                      <Icon style={{ width: 10, height: 10 }} />{cfg.label}
                    </span>
                  </div>
                  <p style={{ fontSize: 10, color: T.textSub, margin: 0 }}>
                    {perm.description} · <span style={{ fontFamily: 'monospace' }}>{perm.thresholdLabel}</span>
                  </p>
                </div>
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <p style={{ fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, margin: 0 }}>Hoy</p>
                  <p style={{ fontSize: 18, fontWeight: 900, color: T.textPrim, margin: 0, textShadow: `0 0 20px ${cfg.color}88` }}>{perm.todayCount}</p>
                  {perm.successRate !== undefined && (
                    <p style={{ fontSize: 9, fontWeight: 700, color: cfg.color, margin: 0 }}>{perm.successRate}% éxito</p>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Trust footer */}
      <div style={{ padding: '12px 20px', borderTop: `1px solid ${T.border}`, background: `${T.emerald}04`, display: 'flex', alignItems: 'center', gap: 12 }}>
        <Sparkles style={{ width: 16, height: 16, color: T.emerald, flexShrink: 0 }} />
        <p style={{ fontSize: 11, color: T.textSub, margin: 0, lineHeight: 1.6 }}>
          <span style={{ color: T.emerald, fontWeight: 700 }}>Cruzá los brazos.</span> En las últimas 24h, la IA tomó 187 decisiones sin tu intervención — el 87% fueron las correctas. Te notificamos solo cuando algo realmente lo amerita.
        </p>
      </div>

      <style>{`
        input[type="range"]::-webkit-slider-thumb {
          appearance: none;
          width: 18px; height: 18px;
          background: #fff;
          border-radius: 50%;
          box-shadow: 0 0 8px rgba(34,197,94,0.6);
          border: 2px solid #22c55e;
          cursor: pointer;
        }
        input[type="range"]:disabled::-webkit-slider-thumb {
          background: #6b7280;
          border-color: #4b5563;
          box-shadow: none;
        }
      `}</style>
    </section>
  )
}
