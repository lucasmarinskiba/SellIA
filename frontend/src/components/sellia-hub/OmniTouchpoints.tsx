'use client'

/**
 * OMNI TOUCHPOINTS
 *
 * Donde vive SellIA en el negocio del usuario. 18 superficies:
 *   Browser ext · Desktop apps · Mobile apps · Smartwatch · Smart speakers ·
 *   Chat bots · POS · IoT · QR · Email · SMS gateway · Voice phone IVR · etc.
 *
 * Cada touchpoint = canal omnipresente · IA visible siempre.
 */

import { useState, useMemo, useEffect } from 'react'
import {
  Globe, Monitor, Smartphone, Watch, Speaker, MessageCircle, ShoppingCart,
  Wifi, QrCode, Mail, MessageSquare, Phone, Tablet, Headphones, Tv2,
  Hash, Activity, CheckCircle2, Filter, Sparkles, Zap
} from 'lucide-react'

// ── Design tokens ──────────────────────────────────────────────────────────────
const T = {
  bgApp:       '#0B0F19',
  bgCard:      '#151B2B',
  border:      '#2A3441',
  textPrim:    '#F3F4F6',
  textSub:     '#9CA3AF',
  cyan:        '#06B6D4',
  emerald:     '#10B981',
  amber:       '#F59E0B',
  pink:        '#ec4899',
  glowCyan:    '0 0 22px rgba(6,182,212,0.50)',
  glowEmerald: '0 0 22px rgba(16,185,129,0.50)',
} as const

type TouchpointCategory = 'browser' | 'desktop' | 'mobile' | 'wearable' | 'voice' | 'chat' | 'pos' | 'iot' | 'physical' | 'comm'

interface Touchpoint {
  id: string
  emoji: string
  name: string
  category: TouchpointCategory
  surface: string
  presence: number
  installations: number
  eventsPerDay: number
  status: 'live' | 'rollout' | 'planned'
  icon: React.ElementType
  color: string
}

const TOUCHPOINTS: Touchpoint[] = [
  { id: 't1',  emoji: '🌐', name: 'Browser Extensions × 8',     category: 'browser',  surface: 'Chrome · Edge · Firefox · Safari · Brave · Opera · Arc · Vivaldi',                 presence: 95, installations: 8467, eventsPerDay: 184_000, status: 'live',   icon: Globe,       color: '#4285F4' },
  { id: 't2',  emoji: '📑', name: 'Browser sidebar PWA',         category: 'browser',  surface: 'Chrome side panel + Edge sidebar',                                                  presence: 78, installations: 2147, eventsPerDay: 47_000,  status: 'live',   icon: Tablet,      color: '#3b82f6' },
  { id: 't3',  emoji: '🖥', name: 'Desktop App · Mac/Win/Linux', category: 'desktop',  surface: 'Tauri native · system tray · global hotkey',                                        presence: 87, installations: 4847, eventsPerDay: 142_000, status: 'live',   icon: Monitor,     color: '#a855f7' },
  { id: 't4',  emoji: '⌨️', name: 'CLI · sellia command',         category: 'desktop',  surface: 'macOS · Linux · Windows PowerShell',                                                presence: 42, installations: 847,  eventsPerDay: 8_400,   status: 'live',   icon: Hash,        color: '#06b6d4' },
  { id: 't5',  emoji: '📱', name: 'Mobile app · iOS + Android',  category: 'mobile',   surface: 'Capacitor · push notifications · widgets',                                          presence: 93, installations: 12847, eventsPerDay: 287_000, status: 'live',   icon: Smartphone,  color: '#10b981' },
  { id: 't6',  emoji: '🏠', name: 'iOS/Android home widget',     category: 'mobile',   surface: 'iOS WidgetKit + Android App Widget',                                                presence: 68, installations: 5847,  eventsPerDay: 47_000,  status: 'live',   icon: Smartphone,  color: '#22c55e' },
  { id: 't7',  emoji: '🔒', name: 'Lock-screen activities',      category: 'mobile',   surface: 'iOS Live Activities · Android Always-On',                                           presence: 56, installations: 3247,  eventsPerDay: 24_000,  status: 'live',   icon: Smartphone,  color: '#0ea5e9' },
  { id: 't8',  emoji: '⌚', name: 'Apple Watch · WatchOS',       category: 'wearable', surface: 'Complications · notifications · Siri',                                              presence: 51, installations: 2147,  eventsPerDay: 18_000,  status: 'live',   icon: Watch,       color: '#06b6d4' },
  { id: 't9',  emoji: '⌚', name: 'WearOS smartwatch',           category: 'wearable', surface: 'Tiles · notifications · Google Assistant',                                          presence: 38, installations: 1247,  eventsPerDay: 9_000,   status: 'rollout',icon: Watch,       color: '#3b82f6' },
  { id: 't10', emoji: '🕶', name: 'Ray-Ban Meta + Apple Vision', category: 'wearable', surface: 'POV alerts · AR overlay precios',                                                   presence: 18, installations: 247,   eventsPerDay: 1_400,   status: 'rollout',icon: Headphones,  color: '#a855f7' },
  { id: 't11', emoji: '🔊', name: 'Smart speakers',              category: 'voice',    surface: 'Alexa Skill · Google Action · Siri Shortcuts',                                      presence: 72, installations: 4847,  eventsPerDay: 67_000,  status: 'live',   icon: Speaker,     color: '#fbbf24' },
  { id: 't12', emoji: '📞', name: 'Voice IVR · llamadas',        category: 'voice',    surface: 'Twilio Voice · receive incoming + outbound calls',                                  presence: 64, installations: 1847,  eventsPerDay: 12_000,  status: 'live',   icon: Phone,       color: '#ef4444' },
  { id: 't13', emoji: '💚', name: 'WhatsApp Business Bot',        category: 'chat',     surface: 'Cloud API · catálogo · listas difusión',                                            presence: 96, installations: 9847,  eventsPerDay: 412_000, status: 'live',   icon: MessageCircle,color: '#25d366' },
  { id: 't14', emoji: '✈️', name: 'Telegram bot · canales',       category: 'chat',     surface: 'Bot API · inline mode · payments',                                                  presence: 67, installations: 2147,  eventsPerDay: 34_000,  status: 'live',   icon: MessageSquare,color: '#0088cc' },
  { id: 't15', emoji: '💬', name: 'Slack + Discord workspace',    category: 'chat',     surface: 'Slack app + Discord bot · notif equipo',                                            presence: 54, installations: 1247,  eventsPerDay: 18_000,  status: 'live',   icon: MessageSquare,color: '#5865f2' },
  { id: 't16', emoji: '💳', name: 'POS terminals',                category: 'pos',      surface: 'Stripe Reader · Square · Clover · MP Point',                                        presence: 47, installations: 847,   eventsPerDay: 9_400,   status: 'rollout',icon: ShoppingCart, color: '#84cc16' },
  { id: 't17', emoji: '📺', name: 'Digital signage / TV',         category: 'pos',      surface: 'Pantallas en local · stock + promos live',                                          presence: 28, installations: 247,   eventsPerDay: 2_400,   status: 'planned',icon: Tv2,          color: '#f97316' },
  { id: 't18', emoji: '📡', name: 'IoT sensores stock',           category: 'iot',      surface: 'Weight sensors + RFID · alerta reposición',                                         presence: 14, installations: 47,    eventsPerDay: 847,     status: 'rollout',icon: Wifi,         color: '#dc2626' },
  { id: 't19', emoji: '📷', name: 'QR codes en productos/local',  category: 'physical', surface: 'Dynamic QR · catálogo · pedidos sin app',                                           presence: 84, installations: 4847,  eventsPerDay: 78_000,  status: 'live',   icon: QrCode,       color: '#10b981' },
  { id: 't20', emoji: '✉️', name: 'Email + signature embed',      category: 'comm',     surface: 'Drips · transactional · cool sigs activos',                                         presence: 89, installations: 12847, eventsPerDay: 247_000, status: 'live',   icon: Mail,         color: '#3b82f6' },
  { id: 't21', emoji: '📱', name: 'SMS gateway · A2P',            category: 'comm',     surface: 'Twilio · Vonage · multi-país compliance',                                           presence: 71, installations: 4147,  eventsPerDay: 48_000,  status: 'live',   icon: MessageSquare,color: '#f59e0b' },
  { id: 't22', emoji: '🔔', name: 'OS Push · desktop+mobile',     category: 'comm',     surface: 'Web Push API · FCM · APNs · windows notif',                                         presence: 92, installations: 8847,  eventsPerDay: 184_000, status: 'live',   icon: Sparkles,     color: '#ec4899' },
]

const CATEGORY_CONFIG: Record<TouchpointCategory, { label: string; color: string; icon: React.ElementType }> = {
  browser:  { label: 'Browser',    color: '#3b82f6', icon: Globe },
  desktop:  { label: 'Desktop',    color: '#a855f7', icon: Monitor },
  mobile:   { label: 'Mobile',     color: '#10b981', icon: Smartphone },
  wearable: { label: 'Wearables',  color: '#06b6d4', icon: Watch },
  voice:    { label: 'Voz',        color: '#fbbf24', icon: Speaker },
  chat:     { label: 'Chat bots',  color: '#25d366', icon: MessageCircle },
  pos:      { label: 'POS · Retail', color: '#84cc16', icon: ShoppingCart },
  iot:      { label: 'IoT',        color: '#dc2626', icon: Wifi },
  physical: { label: 'Físico',     color: '#10b981', icon: QrCode },
  comm:     { label: 'Comms',      color: '#ec4899', icon: Mail },
}

const STATUS_CONFIG = {
  live:    { color: '#22c55e', label: '● LIVE' },
  rollout: { color: '#3b82f6', label: '◌ ROLLOUT' },
  planned: { color: '#fbbf24', label: '○ PLANNED' },
} as const

const card = (extra?: React.CSSProperties): React.CSSProperties => ({
  background: T.bgCard,
  border: `1px solid ${T.border}`,
  borderRadius: 16,
  ...extra,
})

export default function OmniTouchpoints() {
  const [filter, setFilter] = useState<TouchpointCategory | 'all'>('all')
  const [pulse, setPulse] = useState(0)

  useEffect(() => {
    const id = setInterval(() => setPulse(p => (p + 1) % 100), 80)
    return () => clearInterval(id)
  }, [])

  const filtered = useMemo(
    () => filter === 'all' ? TOUCHPOINTS : TOUCHPOINTS.filter(t => t.category === filter),
    [filter]
  )

  const stats = useMemo(() => {
    const liveCount = TOUCHPOINTS.filter(t => t.status === 'live').length
    const totalInstalls = TOUCHPOINTS.reduce((s, t) => s + t.installations, 0)
    const totalEvents = TOUCHPOINTS.reduce((s, t) => s + t.eventsPerDay, 0)
    const avgPresence = Math.round(TOUCHPOINTS.reduce((s, t) => s + t.presence, 0) / TOUCHPOINTS.length)
    return { liveCount, totalInstalls, totalEvents, avgPresence, total: TOUCHPOINTS.length }
  }, [])

  const categoryCounts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const t of TOUCHPOINTS) c[t.category] = (c[t.category] || 0) + 1
    return c
  }, [])

  return (
    <section style={{ background: T.bgApp, border: `1px solid ${T.border}`, borderRadius: 16, overflow: 'hidden', position: 'relative' }}>
      {/* Accent line */}
      <div style={{ height: 2, background: `linear-gradient(90deg, ${T.pink}, ${T.cyan}, transparent)` }} />

      {/* Header */}
      <div style={{ padding: '20px 24px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, background: 'rgba(236,72,153,0.12)', border: '1px solid rgba(236,72,153,0.30)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Hash style={{ width: 20, height: 20, color: T.pink, filter: 'drop-shadow(0 0 8px rgba(236,72,153,0.6))' }} />
          </div>
          <div>
            <h2 style={{ fontSize: 14, fontWeight: 900, color: T.textPrim, textTransform: 'uppercase', letterSpacing: '0.08em', margin: 0 }}>
              OMNI <span style={{ color: T.pink }}>TOUCHPOINTS</span>
              <span style={{ color: T.textSub, fontWeight: 400, fontSize: 11, marginLeft: 8, textTransform: 'none', letterSpacing: 0 }}>· Donde vive SellIA</span>
              <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 999, background: 'rgba(16,185,129,0.15)', color: T.emerald, border: `1px solid rgba(16,185,129,0.30)`, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.1em', marginLeft: 8 }}>
                {stats.liveCount}/{stats.total} LIVE
              </span>
            </h2>
            <p style={{ fontSize: 11, color: T.textSub, margin: '4px 0 0' }}>{stats.total} superficies · <span style={{ color: T.cyan, fontWeight: 700 }}>{(stats.totalEvents / 1_000_000).toFixed(1)}M eventos/día</span> · {(stats.totalInstalls / 1000).toFixed(1)}k instalaciones</p>
          </div>
        </div>
        {/* Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
          {[
            { label: 'Touchpoints', value: stats.total,                                  color: T.pink },
            { label: 'Live',        value: stats.liveCount,                              color: T.emerald },
            { label: 'Eventos/día', value: `${(stats.totalEvents / 1_000_000).toFixed(1)}M`, color: T.cyan },
            { label: 'Presencia avg',value: `${stats.avgPresence}%`,                    color: T.amber },
          ].map(s => (
            <div key={s.label} style={{ textAlign: 'center' }}>
              <p style={{ fontSize: 20, fontWeight: 900, color: s.color, margin: 0, fontVariantNumeric: 'tabular-nums' }}>{s.value}</p>
              <p style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.textSub, fontFamily: 'monospace', margin: '2px 0 0' }}>{s.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Category filter */}
      <div style={{ padding: '12px 24px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', gap: 8, overflowX: 'auto' }}>
        <Filter style={{ width: 12, height: 12, color: T.textSub, flexShrink: 0 }} />
        <button
          onClick={() => setFilter('all')}
          style={{
            flexShrink: 0, padding: '4px 10px', borderRadius: 999, fontSize: 10, fontWeight: 700, cursor: 'pointer',
            background: filter === 'all' ? 'rgba(255,255,255,0.10)' : T.bgCard,
            border: filter === 'all' ? '1px solid rgba(255,255,255,0.20)' : `1px solid ${T.border}`,
            color: filter === 'all' ? T.textPrim : T.textSub,
          }}>
          Todos · {TOUCHPOINTS.length}
        </button>
        {(Object.keys(CATEGORY_CONFIG) as TouchpointCategory[]).map(c => {
          const cfg = CATEGORY_CONFIG[c]
          const Icon = cfg.icon
          const active = filter === c
          return (
            <button
              key={c}
              onClick={() => setFilter(c)}
              style={{
                flexShrink: 0, display: 'flex', alignItems: 'center', gap: 4, padding: '4px 10px', borderRadius: 999, fontSize: 10, fontWeight: 700, cursor: 'pointer',
                background: active ? `${cfg.color}20` : T.bgCard,
                border: active ? `1px solid ${cfg.color}50` : `1px solid ${T.border}`,
                color: active ? cfg.color : T.textSub,
              }}
            >
              <Icon style={{ width: 10, height: 10 }} />
              {cfg.label} · {categoryCounts[c] || 0}
            </button>
          )
        })}
      </div>

      {/* Touchpoints grid */}
      <div style={{ padding: 20, display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
        {filtered.map(t => {
          const Icon = t.icon
          const status = STATUS_CONFIG[t.status]
          return (
            <div key={t.id} style={{ ...card(), overflow: 'hidden', opacity: t.status === 'planned' ? 0.65 : 1 }}>
              <div style={{ height: 2, background: `linear-gradient(90deg, ${t.color}, transparent)` }} />
              <div style={{ padding: '14px 16px' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 10 }}>
                  <div style={{ position: 'relative', width: 36, height: 36, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, background: `${t.color}15`, border: `1px solid ${t.color}30` }}>
                    <Icon style={{ width: 16, height: 16, color: t.color }} />
                    {t.status === 'live' && (
                      <div style={{ position: 'absolute', top: -2, right: -2, width: 8, height: 8, borderRadius: '50%', background: t.color, boxShadow: `0 0 4px ${t.color}`, animation: 'pulse 2s infinite' }} />
                    )}
                  </div>
                  <span style={{ fontSize: 20, flexShrink: 0 }}>{t.emoji}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ fontSize: 12, fontWeight: 700, color: T.textPrim, lineHeight: 1.3, margin: '0 0 4px' }}>{t.name}</p>
                    <span style={{ fontSize: 8, padding: '2px 6px', borderRadius: 5, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.06em', display: 'inline-block', background: `${status.color}18`, color: status.color }}>
                      {status.label}
                    </span>
                  </div>
                </div>

                <p style={{ fontSize: 10, color: T.textSub, lineHeight: 1.4, marginBottom: 10, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>{t.surface}</p>

                {/* Presence bar */}
                <div style={{ marginBottom: 10 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <span style={{ fontSize: 9, color: T.textSub, textTransform: 'uppercase', letterSpacing: '0.08em', fontFamily: 'monospace' }}>Presencia</span>
                    <span style={{ fontSize: 11, fontWeight: 700, fontVariantNumeric: 'tabular-nums', color: t.color }}>{t.presence}%</span>
                  </div>
                  <div style={{ height: 4, background: T.bgApp, borderRadius: 999, overflow: 'hidden' }}>
                    <div style={{ height: '100%', borderRadius: 999, width: `${t.presence}%`, background: t.color, boxShadow: `0 0 4px ${t.color}` }} />
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 10 }}>
                  <span style={{ color: T.textSub, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Activity style={{ width: 10, height: 10 }} />
                    {(t.eventsPerDay / 1000).toFixed(0)}k ev/día
                  </span>
                  <span style={{ color: T.textSub, fontFamily: 'monospace' }}>
                    {t.installations.toLocaleString()} install
                  </span>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Footer */}
      <div style={{ borderTop: `1px solid ${T.border}`, padding: '14px 24px', background: 'rgba(236,72,153,0.03)', textAlign: 'center' }}>
        <p style={{ fontSize: 11, color: T.textSub, margin: 0 }}>
          <Sparkles style={{ width: 12, height: 12, display: 'inline', color: T.pink, marginRight: 6 }} />
          SellIA visible en <span style={{ color: T.pink, fontWeight: 700 }}>{stats.total} superficies</span> del negocio · {(stats.totalEvents / 1_000_000).toFixed(1)}M eventos/día · <span style={{ color: T.textPrim, fontWeight: 700 }}>omnipresente · omnisciente · omnipotente</span>.
        </p>
      </div>
    </section>
  )
}
