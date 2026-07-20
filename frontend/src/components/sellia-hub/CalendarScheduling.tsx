'use client'

/**
 * CALENDAR + SCHEDULING
 *
 * Agenda inteligente con IA. Demos/meetings/follow-ups con:
 *   - Lead info por evento
 *   - Estado de auto-booking
 *   - Tiempos óptimos sugeridos por IA
 *   - Interactividad: click para expandir detalles
 *   - Slots reservables · sync GCal / Outlook
 */

import { useMemo, useState } from 'react'
import {
  Calendar, Clock, Video, Phone, MapPin, Bot, CheckCircle2,
  AlertCircle, Plus, Filter, Sparkles, ChevronDown, ChevronRight,
  Zap, Users, Target
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

type EventKind = 'meeting' | 'demo' | 'followup' | 'delivery' | 'task' | 'reminder'
type EventStatus = 'confirmed' | 'tentative' | 'cancelled'

interface CalEvent {
  id: string
  emoji: string
  title: string
  kind: EventKind
  start: string
  duration: string
  with: string
  channel: 'video' | 'phone' | 'in-person'
  status: EventStatus
  aiHandling?: string
  aiOptimalNote?: string
  reminderSet: boolean
  color: string
  leadScore?: number
  dealValue?: number
}

const EVENTS: CalEvent[] = [
  {
    id: 'e1', emoji: '🎥', title: 'Demo producto · María L.', kind: 'demo',
    start: 'Hoy 14:00', duration: '30min', with: 'María L. · Shopify',
    channel: 'video', status: 'confirmed',
    aiHandling: 'Enviando agenda 15min antes + link Meet auto-generado',
    aiOptimalNote: 'Horario óptimo: mayor tasa de cierre histórica los martes 14-16hs',
    reminderSet: true, color: T.cyan, leadScore: 82, dealValue: 1240,
  },
  {
    id: 'e2', emoji: '📞', title: 'Follow-up Tomás N.', kind: 'followup',
    start: 'Hoy 16:30', duration: '15min', with: 'Tomás N. · WhatsApp',
    channel: 'phone', status: 'confirmed',
    aiHandling: 'Brief auto preparado · últimas 3 conversaciones analizadas · objeción de precio activa',
    reminderSet: true, color: T.violet, leadScore: 68, dealValue: 2400,
  },
  {
    id: 'e3', emoji: '🚚', title: 'Entrega Pack Premium · Ana S.', kind: 'delivery',
    start: 'Hoy 17:00', duration: '—', with: 'Ana Suárez',
    channel: 'in-person', status: 'confirmed',
    aiHandling: 'Tracking OCA actualizado · mensaje de confirmación enviado al cliente',
    reminderSet: true, color: T.emerald, dealValue: 980,
  },
  {
    id: 'e4', emoji: '🤝', title: 'Reunión estrategia Q2', kind: 'meeting',
    start: 'Mañana 10:00', duration: '60min', with: 'Equipo · 4 personas',
    channel: 'video', status: 'tentative',
    aiOptimalNote: 'IA sugiere confirmar hoy · 2 asistentes sin responder',
    reminderSet: true, color: '#ec4899',
  },
  {
    id: 'e5', emoji: '🎥', title: 'Demo Empresa Beta · pitch ejecutivo', kind: 'demo',
    start: 'Mañana 15:00', duration: '45min', with: 'CEO + CFO · LinkedIn',
    channel: 'video', status: 'confirmed',
    aiHandling: 'Análisis competitivo preparado · script de manejo de objeciones listo · materiales de propuesta adjuntos',
    aiOptimalNote: 'Deal de $8.4k · probabilidad 64% · foco en ROI para CFO',
    reminderSet: true, color: T.cyan, leadScore: 91, dealValue: 8400,
  },
  {
    id: 'e6', emoji: '✅', title: 'Pago factura proveedor #2348', kind: 'task',
    start: 'Viernes', duration: '—', with: 'Andreani logística',
    channel: 'in-person', status: 'confirmed', reminderSet: true, color: T.amber,
  },
  {
    id: 'e7', emoji: '📦', title: 'Reposición sneakers Nike', kind: 'reminder',
    start: 'Lunes próx', duration: '—', with: 'Auto · supplier Vendor-X',
    channel: 'in-person', status: 'confirmed',
    aiHandling: 'PO #4821 ya enviada · ETA confirmada para miércoles · stock calculado para 30 días',
    reminderSet: true, color: T.emerald,
  },
  {
    id: 'e8', emoji: '📞', title: 'Llamada cierre · Pedro K.', kind: 'followup',
    start: 'Lunes 11:30', duration: '20min', with: 'Pedro K. · ML',
    channel: 'phone', status: 'tentative',
    aiOptimalNote: 'Sin confirmar · IA envió recordatorio automatico hace 2hs',
    reminderSet: false, color: T.violet, leadScore: 44, dealValue: 1200,
  },
]

const KIND_CONFIG: Record<EventKind, { color: string; label: string }> = {
  meeting:  { color: '#ec4899', label: 'Reunión'      },
  demo:     { color: T.cyan,    label: 'Demo'          },
  followup: { color: T.violet,  label: 'Follow-up'    },
  delivery: { color: '#22c55e', label: 'Entrega'       },
  task:     { color: T.amber,   label: 'Task'          },
  reminder: { color: T.emerald, label: 'Recordatorio' },
}

const CHANNEL_ICON = { video: Video, phone: Phone, 'in-person': MapPin } as const

const SLOTS_AVAILABLE = [
  { day: 'Lun', slots: ['09:00', '11:00', '14:00', '16:00'] },
  { day: 'Mar', slots: ['10:00', '15:00'] },
  { day: 'Mié', slots: ['09:00', '11:30', '15:30', '17:00'] },
  { day: 'Jue', slots: ['14:00', '16:30'] },
  { day: 'Vie', slots: ['10:30', '15:00'] },
]

const AI_SUGGESTIONS = [
  { emoji: '⚡', text: 'Pedro K. · llamar miércoles 10am: máxima apertura según historial', color: T.violet },
  { emoji: '🎯', text: 'Agendar follow-up con Carlos R. hoy: 8 días sin contacto', color: T.rose },
  { emoji: '📅', text: 'Bloquear jueves 15-17hs para cierre Empresa Beta · alto valor', color: T.amber },
]

export default function CalendarScheduling() {
  const [filter, setFilter] = useState<EventKind | 'all'>('all')
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const filtered = useMemo(
    () => filter === 'all' ? EVENTS : EVENTS.filter(e => e.kind === filter),
    [filter]
  )

  const stats = useMemo(() => ({
    today: EVENTS.filter(e => e.start.startsWith('Hoy')).length,
    week: EVENTS.length,
    confirmed: EVENTS.filter(e => e.status === 'confirmed').length,
    aiHandled: EVENTS.filter(e => e.aiHandling).length,
    totalDealValue: EVENTS.filter(e => e.dealValue).reduce((s, e) => s + (e.dealValue ?? 0), 0),
  }), [])

  return (
    <section style={{ background: T.bgCard, border: `1px solid ${T.border}`, borderRadius: 16, overflow: 'hidden' }}>
      <div style={{ height: 1, background: `linear-gradient(90deg, transparent, ${T.violet}80, transparent)` }} />

      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: `${T.violet}22`, border: `1px solid ${T.violet}44`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Calendar style={{ width: 20, height: 20, color: T.violet, filter: `drop-shadow(0 0 8px ${T.violet}b0)` }} />
          </div>
          <div>
            <h2 style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, letterSpacing: '.08em', textTransform: 'uppercase', margin: 0 }}>
              CALENDAR + SCHEDULING
              <span style={{ color: T.textSub, fontWeight: 400, textTransform: 'none', letterSpacing: 'normal', marginLeft: 8 }}>· Slots · GCal sync · recordatorios IA</span>
            </h2>
            <p style={{ fontSize: 11, color: T.textSub, margin: 0, marginTop: 2 }}>
              {stats.today} hoy · {stats.week} esta semana · {stats.aiHandled} con IA en marcha · ${stats.totalDealValue.toLocaleString()} en juego
            </p>
          </div>
        </div>
        <button style={{ padding: '6px 14px', borderRadius: 8, background: `${T.violet}18`, border: `1px solid ${T.violet}40`, color: T.violet, fontSize: 12, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}>
          <Plus style={{ width: 12, height: 12 }} />Nuevo evento
        </button>
      </div>

      {/* Quick stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', borderBottom: `1px solid ${T.border}` }}>
        {[
          { icon: Clock, color: T.violet, label: 'Hoy',          value: stats.today,     sub: 'eventos' },
          { icon: Calendar, color: T.cyan, label: 'Esta semana', value: stats.week,      sub: 'agendados' },
          { icon: CheckCircle2, color: T.emerald, label: 'Confirmados', value: stats.confirmed, sub: 'en verde' },
          { icon: Bot, color: T.violet, label: 'Con IA',        value: stats.aiHandled, sub: 'preparados' },
        ].map((s, i) => {
          const Icon = s.icon
          return (
            <div key={i} style={{ padding: 12, borderRight: i < 3 ? `1px solid ${T.border}` : undefined }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                <Icon style={{ width: 12, height: 12, color: s.color }} />
                <p style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, margin: 0, fontWeight: 700 }}>{s.label}</p>
              </div>
              <p style={{ fontSize: 20, fontWeight: 900, color: T.textPrim, margin: 0, textShadow: `0 0 20px ${s.color}88` }}>{s.value}</p>
              <p style={{ fontSize: 9, color: T.textSub, margin: 0, marginTop: 2 }}>{s.sub}</p>
            </div>
          )
        })}
      </div>

      {/* AI suggestions bar */}
      <div style={{ padding: '10px 16px', borderBottom: `1px solid ${T.border}`, background: `${T.violet}06`, display: 'flex', alignItems: 'flex-start', gap: 8, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
          <Sparkles style={{ width: 12, height: 12, color: T.violet }} />
          <span style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.violet, fontWeight: 700 }}>IA SUGIERE</span>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {AI_SUGGESTIONS.map((s, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '4px 10px', borderRadius: 6, background: `${s.color}12`, border: `1px solid ${s.color}28`, cursor: 'pointer' }}>
              <span style={{ fontSize: 12 }}>{s.emoji}</span>
              <span style={{ fontSize: 11, color: s.color }}>{s.text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Filter bar */}
      <div style={{ padding: '10px 20px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <Filter style={{ width: 12, height: 12, color: T.textSub, flexShrink: 0 }} />
        <button onClick={() => setFilter('all')} style={{
          fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', fontWeight: 700,
          padding: '2px 8px', borderRadius: 4, cursor: 'pointer',
          background: filter === 'all' ? 'rgba(255,255,255,0.10)' : 'rgba(255,255,255,0.02)',
          border: `1px solid ${filter === 'all' ? 'rgba(255,255,255,0.20)' : T.border}`,
          color: filter === 'all' ? T.textPrim : T.textSub,
        }}>Todos · {EVENTS.length}</button>
        {(Object.keys(KIND_CONFIG) as EventKind[]).map(k => {
          const cfg = KIND_CONFIG[k]
          const count = EVENTS.filter(e => e.kind === k).length
          const active = filter === k
          return (
            <button key={k} onClick={() => setFilter(k)} style={{
              fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', fontWeight: 700,
              padding: '2px 8px', borderRadius: 4, cursor: 'pointer',
              background: active ? `${cfg.color}20` : 'rgba(255,255,255,0.02)',
              border: `1px solid ${active ? cfg.color + '50' : T.border}`,
              color: active ? cfg.color : T.textSub,
            }}>{cfg.label} · {count}</button>
          )
        })}
      </div>

      {/* Content grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 260px', gap: 12, padding: 16 }}>
        {/* Events list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 520, overflowY: 'auto' }}>
          {filtered.map(e => {
            const ChannelIcon = CHANNEL_ICON[e.channel]
            const kind = KIND_CONFIG[e.kind]
            const isExpanded = expandedId === e.id
            return (
              <div key={e.id} style={{
                position: 'relative', borderRadius: 12, overflow: 'hidden',
                background: `${e.color}06`,
                border: `1px solid ${e.color}20`,
                opacity: e.status === 'cancelled' ? 0.45 : 1,
              }}>
                {/* Left color bar */}
                <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 3, background: e.color }} />

                <button
                  onClick={() => setExpandedId(isExpanded ? null : e.id)}
                  style={{ width: '100%', display: 'flex', alignItems: 'flex-start', gap: 12, padding: '12px 14px 12px 20px', background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left' }}
                >
                  {/* Time block */}
                  <div style={{ flexShrink: 0, textAlign: 'center', minWidth: 52 }}>
                    <p style={{ fontSize: 13, fontWeight: 900, color: T.textPrim, margin: 0 }}>
                      {e.start.includes(':') ? e.start.split(' ').pop() : e.start}
                    </p>
                    <p style={{ fontSize: 8, color: T.textSub, margin: 0, marginTop: 1, textTransform: 'uppercase', letterSpacing: '.06em' }}>
                      {e.start.startsWith('Hoy') ? 'HOY' : e.start.startsWith('Mañana') ? 'MÑN' : e.start.split(' ')[0]?.toUpperCase() ?? ''}
                    </p>
                    {e.duration !== '—' && <p style={{ fontSize: 8, color: T.textSub, margin: 0, opacity: 0.6 }}>{e.duration}</p>}
                  </div>

                  {/* Emoji badge */}
                  <div style={{ width: 36, height: 36, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, flexShrink: 0, background: `${e.color}12`, border: `1px solid ${e.color}25` }}>
                    {e.emoji}
                  </div>

                  {/* Content */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 4 }}>
                          <p style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, margin: 0 }}>{e.title}</p>
                          <span style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', padding: '2px 6px', borderRadius: 4, background: `${kind.color}18`, border: `1px solid ${kind.color}28`, color: kind.color, fontWeight: 700 }}>{kind.label}</span>
                          {e.dealValue && (
                            <span style={{ fontSize: 10, fontWeight: 700, color: T.emerald, textShadow: '0 0 20px #10B98188' }}>${e.dealValue.toLocaleString()}</span>
                          )}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 10, color: T.textSub, flexWrap: 'wrap' }}>
                          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                            <ChannelIcon style={{ width: 10, height: 10 }} />{e.with}
                          </span>
                          {e.leadScore && (
                            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                              <Target style={{ width: 10, height: 10, color: T.violet }} />
                              <span style={{ color: T.violet }}>Score {e.leadScore}</span>
                            </span>
                          )}
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
                        {e.status === 'confirmed'
                          ? <CheckCircle2 style={{ width: 16, height: 16, color: T.emerald }} />
                          : <AlertCircle style={{ width: 16, height: 16, color: T.amber }} />
                        }
                        {isExpanded
                          ? <ChevronDown style={{ width: 14, height: 14, color: T.textSub }} />
                          : <ChevronRight style={{ width: 14, height: 14, color: T.textSub }} />
                        }
                      </div>
                    </div>

                    {/* AI handling chip — always visible */}
                    {e.aiHandling && (
                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 6, padding: '6px 10px', borderRadius: 8, background: `${T.violet}08`, border: `1px solid ${T.violet}20`, marginTop: 8 }}>
                        <Bot style={{ width: 12, height: 12, color: T.violet, flexShrink: 0, marginTop: 1 }} />
                        <p style={{ fontSize: 10, color: T.violet, margin: 0, lineHeight: 1.5 }}>{e.aiHandling}</p>
                      </div>
                    )}
                  </div>
                </button>

                {/* Expanded detail */}
                {isExpanded && (
                  <div style={{ padding: '0 14px 14px 20px', borderTop: `1px solid ${T.border}`, paddingTop: 12 }}>
                    {e.aiOptimalNote && (
                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 6, padding: '8px 10px', borderRadius: 8, background: `${T.amber}08`, border: `1px solid ${T.amber}20`, marginBottom: 10 }}>
                        <Zap style={{ width: 12, height: 12, color: T.amber, flexShrink: 0, marginTop: 1 }} />
                        <p style={{ fontSize: 11, color: T.amber, margin: 0, lineHeight: 1.4 }}>{e.aiOptimalNote}</p>
                      </div>
                    )}
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      <button style={{ padding: '6px 14px', borderRadius: 8, background: `${e.color}18`, border: `1px solid ${e.color}40`, color: e.color, fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
                        Abrir detalle
                      </button>
                      <button style={{ padding: '6px 14px', borderRadius: 8, background: `${T.violet}18`, border: `1px solid ${T.violet}40`, color: T.violet, fontSize: 12, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Bot style={{ width: 10, height: 10 }} />Preparar brief IA
                      </button>
                      {e.status === 'tentative' && (
                        <button style={{ padding: '6px 14px', borderRadius: 8, background: `${T.emerald}18`, border: `1px solid ${T.emerald}40`, color: T.emerald, fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
                          Confirmar
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Booking slots + summary */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ borderRadius: 12, border: `1px solid ${T.cyan}28`, background: `${T.cyan}04`, padding: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <Sparkles style={{ width: 14, height: 14, color: T.cyan }} />
              <p style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.cyan, fontWeight: 700, margin: 0 }}>SLOTS BOOKABLE</p>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {SLOTS_AVAILABLE.map(d => (
                <div key={d.day}>
                  <p style={{ fontSize: 11, fontWeight: 700, color: T.textPrim, marginBottom: 4 }}>{d.day}</p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {d.slots.map(s => (
                      <span key={s} style={{
                        fontSize: 9, fontFamily: 'JetBrains Mono,monospace', padding: '2px 6px', borderRadius: 4,
                        background: `${T.cyan}18`, border: `1px solid ${T.cyan}30`, color: T.cyan, cursor: 'pointer',
                      }}>{s}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 12, paddingTop: 12, borderTop: `1px solid ${T.border}` }}>
              <p style={{ fontSize: 10, color: T.cyan, fontWeight: 700, marginBottom: 4 }}>📅 PUBLIC BOOKING LINK</p>
              <code style={{ display: 'block', padding: '4px 8px', borderRadius: 6, background: 'rgba(0,0,0,0.4)', fontSize: 9, fontFamily: 'monospace', color: T.textSub, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                sellia.app/book/lucas
              </code>
              <p style={{ fontSize: 10, color: T.textSub, marginTop: 8 }}>IA bloquea automáticamente al agendar · sync GCal · sync Outlook</p>
            </div>
          </div>

          {/* Week at a glance */}
          <div style={{ borderRadius: 12, border: `1px solid ${T.border}`, background: 'rgba(255,255,255,0.02)', padding: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <Users style={{ width: 14, height: 14, color: T.textSub }} />
              <p style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, fontWeight: 700, margin: 0 }}>RESUMEN SEMANA</p>
            </div>
            {[
              { label: 'Demos agendadas', value: EVENTS.filter(e => e.kind === 'demo').length, color: T.cyan },
              { label: 'Follow-ups',      value: EVENTS.filter(e => e.kind === 'followup').length, color: T.violet },
              { label: 'Reuniones',       value: EVENTS.filter(e => e.kind === 'meeting').length, color: '#ec4899' },
              { label: 'Valor en juego',  value: `$${stats.totalDealValue.toLocaleString()}`, color: T.emerald },
            ].map((s, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 0', borderBottom: i < 3 ? `1px solid ${T.border}` : undefined }}>
                <span style={{ fontSize: 11, color: T.textSub }}>{s.label}</span>
                <span style={{ fontSize: 13, fontWeight: 700, color: s.color, textShadow: `0 0 20px ${s.color}88` }}>{s.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
