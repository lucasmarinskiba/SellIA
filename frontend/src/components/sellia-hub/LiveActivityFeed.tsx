'use client'

/**
 * LIVE ACTIVITY FEED
 *
 * Stream en tiempo real de TODO lo que la IA está haciendo:
 * - Acciones de automatización
 * - Cierres de venta
 * - Mensajes enviados
 * - Fidelización (reorders, NPS, referidos)
 *
 * Filtros por categoría. Las nuevas acciones aparecen arriba con fade-in.
 */

import { useState, useEffect, useMemo } from 'react'
import {
  Activity, MessageCircle, DollarSign, Package, Truck, Star,
  Bot, MousePointer2, Sparkles, Filter, Pause, Play, Zap
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

type ActivityCategory = 'sales' | 'fidelization' | 'cua' | 'communication' | 'admin'

interface ActivityItem {
  id: string
  timestamp: string
  ts: number
  category: ActivityCategory
  emoji: string
  title: string
  detail: string
  amount?: number
  icon: React.ElementType
  color: string
}

const SEED_ACTIVITY: ActivityItem[] = [
  { id: 'a1',  timestamp: 'ahora',    ts: Date.now(),          category: 'cua',           emoji: '🖱',  title: 'Acción automatizada en chat de Juan García', detail: 'WhatsApp Web · paso 17/30',                          icon: MousePointer2, color: T.amber   },
  { id: 'a2',  timestamp: 'hace 12s', ts: Date.now() - 12000,  category: 'sales',         emoji: '✅',  title: 'Cierre completado · Ana Suárez',             detail: '+$980 ARS · Pack Premium',           amount: 980,  icon: DollarSign,   color: '#22c55e' },
  { id: 'a3',  timestamp: 'hace 43s', ts: Date.now() - 43000,  category: 'communication', emoji: '💬',  title: 'Respuesta a objeción de precio',             detail: 'Tomás N. · estrategia de valor activa',              icon: MessageCircle, color: T.cyan   },
  { id: 'a4',  timestamp: 'hace 1m',  ts: Date.now() - 60000,  category: 'fidelization',  emoji: '⭐',  title: 'NPS 10 registrado · Lucía F.',               detail: 'Activando programa de embajadores',                  icon: Star,          color: T.amber  },
  { id: 'a5',  timestamp: 'hace 2m',  ts: Date.now() - 120000, category: 'admin',         emoji: '🧾',  title: 'Factura A generada en AFIP',                 detail: 'CAE 75412988411 · Ana Suárez',                        icon: Bot,           color: '#3b82f6' },
  { id: 'a6',  timestamp: 'hace 3m',  ts: Date.now() - 180000, category: 'fidelization',  emoji: '🔄',  title: 'Reorder automático ejecutado',               detail: 'Pedro K. · 6 productos · $3,200', amount: 3200,  icon: Package,       color: T.violet },
  { id: 'a7',  timestamp: 'hace 4m',  ts: Date.now() - 240000, category: 'sales',         emoji: '🎯',  title: 'Lead calificado · Empresa Beta',             detail: 'Calificación: A · Score IA 87/100',                  icon: Sparkles,      color: '#6366f1' },
  { id: 'a8',  timestamp: 'hace 5m',  ts: Date.now() - 300000, category: 'communication', emoji: '📩',  title: '12 mensajes enviados a leads tibios',        detail: 'Secuencia reactivación 90d · WhatsApp',              icon: MessageCircle, color: T.emerald },
  { id: 'a9',  timestamp: 'hace 7m',  ts: Date.now() - 420000, category: 'fidelization',  emoji: '🚚',  title: 'Envío coordinado · OCA',                     detail: 'Tracking #A2841 enviado a cliente',                  icon: Truck,         color: T.amber  },
  { id: 'a10', timestamp: 'hace 8m',  ts: Date.now() - 480000, category: 'sales',         emoji: '📈',  title: 'Deal movido a Negociación',                  detail: 'Mariana P. · $850 · 78% probabilidad',              icon: Sparkles,      color: '#f97316' },
  { id: 'a11', timestamp: 'hace 10m', ts: Date.now() - 600000, category: 'cua',           emoji: '🌐',  title: 'Sesión iniciada en MercadoLibre',            detail: 'Respondiendo 4 reseñas pendientes',                  icon: Bot,           color: T.amber  },
  { id: 'a12', timestamp: 'hace 12m', ts: Date.now() - 720000, category: 'admin',         emoji: '⚡',  title: 'Stock crítico detectado',                    detail: 'Zapatillas Nike 42 · 2 unidades · auto-orden',       icon: Zap,           color: T.rose   },
]

const CATEGORY_CONFIG: Record<ActivityCategory | 'all', { label: string; color: string; icon: React.ElementType }> = {
  all:           { label: 'Todo',         color: T.textPrim, icon: Activity      },
  sales:         { label: 'Ventas',       color: '#22c55e',  icon: DollarSign    },
  fidelization:  { label: 'Fidelización', color: T.violet,   icon: Star          },
  cua:           { label: 'Auto CUA',     color: T.amber,    icon: MousePointer2 },
  communication: { label: 'Mensajes',     color: T.cyan,     icon: MessageCircle },
  admin:         { label: 'Admin',        color: '#3b82f6',  icon: Bot           },
}

const SIMULATED_ARRIVALS = [
  { category: 'communication' as const, emoji: '💬', title: 'Mensaje enviado a Juan García', detail: 'Técnica de cierre asuntivo · WhatsApp', icon: MessageCircle, color: T.cyan },
  { category: 'cua' as const, emoji: '🖱', title: 'Acción automatizada en portal', detail: 'Mercado Pago · paso 23/30', icon: MousePointer2, color: T.amber },
  { category: 'sales' as const, emoji: '🎯', title: 'Nuevo lead capturado · Instagram', detail: 'DM sobre Pack Premium', icon: Sparkles, color: '#6366f1' },
  { category: 'fidelization' as const, emoji: '🎁', title: 'Cupón de cumpleaños enviado', detail: 'María L. cumple mañana · 20% off', icon: Star, color: T.violet },
  { category: 'admin' as const, emoji: '📊', title: 'Reporte semanal generado', detail: 'Enviado a gerencia por email', icon: Bot, color: '#3b82f6' },
]

export default function LiveActivityFeed() {
  const [activity, setActivity] = useState<ActivityItem[]>(SEED_ACTIVITY)
  const [filter, setFilter] = useState<ActivityCategory | 'all'>('all')
  const [paused, setPaused] = useState(false)

  useEffect(() => {
    if (paused) return
    const id = setInterval(() => {
      const template = SIMULATED_ARRIVALS[Math.floor((Date.now() / 1000) % SIMULATED_ARRIVALS.length)]
      const newItem: ActivityItem = {
        id: `a-${Date.now()}`,
        timestamp: 'ahora',
        ts: Date.now(),
        ...template,
      }
      setActivity(prev => [newItem, ...prev].slice(0, 30))
    }, 8000)
    return () => clearInterval(id)
  }, [paused])

  const filtered = useMemo(
    () => filter === 'all' ? activity : activity.filter(a => a.category === filter),
    [activity, filter]
  )

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: activity.length }
    for (const a of activity) c[a.category] = (c[a.category] ?? 0) + 1
    return c
  }, [activity])

  return (
    <section style={{
      background: T.bgCard, border: `1px solid ${T.border}`, borderRadius: 16, overflow: 'hidden',
      display: 'flex', flexDirection: 'column',
    }}>
      <div style={{ height: 1, background: `linear-gradient(90deg, transparent, ${T.emerald}60, transparent)` }} />

      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ position: 'relative' }}>
            <Activity style={{ width: 16, height: 16, color: T.emerald, filter: `drop-shadow(0 0 6px ${T.emerald}99)` }} />
            {!paused && <div className="animate-ping" style={{ position: 'absolute', top: -4, right: -4, width: 8, height: 8, borderRadius: '50%', background: T.emerald }} />}
          </div>
          <div>
            <h3 style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, letterSpacing: '.08em', textTransform: 'uppercase', margin: 0 }}>Live Activity</h3>
            <p style={{ fontSize: 10, color: T.textSub, margin: 0, marginTop: 2 }}>Stream de acciones IA en tiempo real</p>
          </div>
        </div>
        <button
          onClick={() => setPaused(p => !p)}
          style={{
            padding: 6, borderRadius: 8, cursor: 'pointer',
            background: paused ? `${T.amber}18` : `${T.emerald}18`,
            border: `1px solid ${paused ? T.amber + '40' : T.emerald + '40'}`,
            color: paused ? T.amber : T.emerald,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
          title={paused ? 'Reanudar feed' : 'Pausar feed'}
        >
          {paused ? <Play style={{ width: 14, height: 14 }} /> : <Pause style={{ width: 14, height: 14 }} />}
        </button>
      </div>

      {/* Filter chips */}
      <div style={{ padding: '10px 20px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', gap: 6, overflowX: 'auto' }}>
        <Filter style={{ width: 12, height: 12, color: T.textSub, flexShrink: 0 }} />
        {(Object.keys(CATEGORY_CONFIG) as (ActivityCategory | 'all')[]).map(cat => {
          const cfg = CATEGORY_CONFIG[cat]
          const Icon = cfg.icon
          const active = filter === cat
          const count = counts[cat] ?? 0
          return (
            <button key={cat} onClick={() => setFilter(cat)} style={{
              flexShrink: 0, display: 'flex', alignItems: 'center', gap: 6,
              padding: '4px 10px', borderRadius: 20, fontSize: 10, fontWeight: 600, cursor: 'pointer',
              background: active ? `${cfg.color}20` : 'rgba(255,255,255,0.02)',
              border: `1px solid ${active ? cfg.color + '50' : T.border}`,
              color: active ? cfg.color : T.textSub,
            }}>
              <Icon style={{ width: 10, height: 10 }} />
              {cfg.label}
              {count > 0 && <span style={{ opacity: 0.6 }}>·{count}</span>}
            </button>
          )
        })}
      </div>

      {/* Activity list */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px 12px', display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 480, minHeight: 240 }}>
        {filtered.length === 0 ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '48px 0', fontSize: 12, color: T.textSub }}>
            Sin actividad en esta categoría
          </div>
        ) : (
          filtered.map((item, i) => {
            const Icon = item.icon
            const isLatest = i === 0 && !paused
            return (
              <div key={item.id} style={{
                position: 'relative', display: 'flex', alignItems: 'flex-start', gap: 12,
                padding: 10, borderRadius: 10,
                background: isLatest ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.02)',
                border: `1px solid ${isLatest ? item.color + '30' : T.border}`,
                boxShadow: isLatest ? `0 0 12px ${item.color}12` : 'none',
              }}>
                {isLatest && (
                  <div className="animate-pulse" style={{
                    position: 'absolute', left: -4, top: '50%', transform: 'translateY(-50%)',
                    width: 8, height: 8, borderRadius: '50%', background: item.color,
                    boxShadow: `0 0 8px ${item.color}`,
                  }} />
                )}
                <div style={{ width: 28, height: 28, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, background: `${item.color}18`, border: `1px solid ${item.color}30` }}>
                  <Icon style={{ width: 14, height: 14, color: item.color }} />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
                    <p style={{ fontSize: 12, fontWeight: 500, color: T.textPrim, margin: 0, lineHeight: 1.4 }}>{item.title}</p>
                    {item.amount !== undefined && (
                      <span style={{ fontSize: 11, fontWeight: 700, color: T.emerald, flexShrink: 0, textShadow: '0 0 20px #10B98188' }}>
                        ${item.amount.toLocaleString()}
                      </span>
                    )}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 2 }}>
                    <p style={{ fontSize: 10, color: T.textSub, margin: 0, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.detail}</p>
                    <span style={{ fontSize: 9, color: T.textSub, fontFamily: 'monospace', flexShrink: 0 }}>{item.timestamp}</span>
                  </div>
                </div>
              </div>
            )
          })
        )}
      </div>

      {/* Footer */}
      <div style={{ padding: '10px 20px', borderTop: `1px solid ${T.border}`, background: 'rgba(0,0,0,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 10, color: T.textSub }}>
          <span>{filtered.length} eventos</span>
          <span>·</span>
          <span style={{ color: '#22c55e' }}>{counts.sales ?? 0} ventas</span>
          <span>·</span>
          <span style={{ color: T.violet }}>{counts.fidelization ?? 0} fidelización</span>
        </div>
        {!paused && (
          <span style={{ fontSize: 9, color: T.emerald, fontFamily: 'JetBrains Mono,monospace', textTransform: 'uppercase', letterSpacing: '.06em', display: 'flex', alignItems: 'center', gap: 4 }}>
            <div className="animate-pulse" style={{ width: 4, height: 4, borderRadius: '50%', background: T.emerald }} />
            Streaming
          </span>
        )}
      </div>

      <style>{`
        @keyframes fadeInDown {
          0%   { opacity: 0; transform: translateY(-8px); }
          100% { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </section>
  )
}
