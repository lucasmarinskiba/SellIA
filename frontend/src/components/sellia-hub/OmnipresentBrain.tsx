'use client'

/**
 * OMNIPRESENT BRAIN
 *
 * Interfaz "set it and forget it" — usuario no maneja la plataforma.
 * SellIA explica en lenguaje plano qué está haciendo, cómo consigue clientes,
 * qué estrategias usa, y dispara notificaciones (PC + móvil) en cada win.
 *
 * Lo MÁS importante visible:
 *   - SellIA está vendiendo en X plataformas ahora mismo
 *   - Cuántos clientes le consiguió hoy
 *   - Ventas cerradas con técnica usada
 *   - Notificaciones que dispara
 */

import { useState, useEffect, useMemo } from 'react'
import {
  Brain, Sparkles, Activity, MessageCircle, DollarSign, Bell, Smartphone,
  Monitor, Watch, ShoppingBag, TrendingUp, Bot, Heart, Zap, Eye, Globe
} from 'lucide-react'

interface PlainAction {
  emoji: string
  text: string
  technique: string
  platform: string
  ts: string
  color: string
}

interface Strategy {
  emoji: string
  name: string
  why: string
  platform: string
  active: boolean
  metric: string
  color: string
}

interface ClosedSale {
  emoji: string
  customer: string
  amount: number
  platform: string
  technique: string
  ts: string
}

interface NotifChannel {
  id: string
  icon: React.ElementType
  label: string
  delivered: number
  unreadByUser: number
  online: boolean
}

const ACTIONS_LIVE: PlainAction[] = [
  { emoji: '💬', text: 'Estoy respondiendo a Juan en WhatsApp sobre el Pack Premium', technique: 'Empatía táctica activa', platform: 'WhatsApp', ts: 'ahora', color: '#25d366' },
  { emoji: '📸', text: 'Publiqué un reel con hook viral probado', technique: 'Hook 3-seg + trending audio', platform: 'Instagram', ts: 'hace 4min', color: '#ec4899' },
  { emoji: '🛒', text: 'Le estoy ofreciendo a María un upgrade Premium', technique: 'Stack de valor · oferta irresistible', platform: 'Shopify', ts: 'hace 7min', color: '#95BF47' },
  { emoji: '📞', text: 'Llamé en frío a 12 prospects en LinkedIn ICP B2B', technique: 'Persistencia sistemática · 10X contactos', platform: 'LinkedIn', ts: 'hace 12min', color: '#0A66C2' },
  { emoji: '⭐', text: 'Pedí review a Ana post-compra · NPS 10', technique: 'Reconocimiento post-venta · activación NPS', platform: 'Email', ts: 'hace 18min', color: '#3b82f6' },
  { emoji: '🎯', text: 'Lancé campaña Meta Ads · presupuesto $50/día', technique: 'Lookalike 1% audience', platform: 'Meta Ads', ts: 'hace 23min', color: '#1877F2' },
  { emoji: '🧾', text: 'Generé factura A automática · cerró deal $1,200', technique: 'Computer Use AFIP', platform: 'AFIP', ts: 'hace 31min', color: '#fbbf24' },
  { emoji: '🚚', text: 'Coordiné envío con OCA · tracking enviado al cliente', technique: 'Payment-Bot + Calendar-Bot', platform: 'OCA', ts: 'hace 38min', color: '#f59e0b' },
]

const STRATEGIES: Strategy[] = [
  { emoji: '🎯', name: 'Captación orgánica multi-canal', why: 'Genero tráfico sin gastar en ads', platform: '14 canales', active: true, metric: '+47 leads/día', color: '#22c55e' },
  { emoji: '💬', name: 'Respuesta < 30 segundos', why: 'Quien responde primero gana 78% del lead', platform: 'WhatsApp/IG/Email', active: true, metric: 'avg 18seg', color: '#06b6d4' },
  { emoji: '🛡', name: 'Recovery de leads fríos · 90 días', why: 'El 51% de "perdidos" se pueden recuperar', platform: 'Email + WA', active: true, metric: '38 recuperados/mes', color: '#0ea5e9' },
  { emoji: '⭐', name: 'NPS · referidos virales', why: 'Embajadores generan ventas sin invertir un peso', platform: 'Email + IG', active: true, metric: '+9 referidos/sem', color: '#fbbf24' },
  { emoji: '💰', name: 'Pricing dinámico cross-platform', why: 'Ajusto precios según demanda · margin +12%', platform: 'Amazon/ML/Shopify', active: true, metric: '+$2.3k/mes margin', color: '#10b981' },
  { emoji: '🤖', name: 'Computer Use 24/7 · sin parar', why: 'Vendo mientras dormís · sin descanso', platform: 'Todas', active: true, metric: '187 acciones/día', color: '#a855f7' },
  { emoji: '🎨', name: 'Content batch · 12 piezas/sem', why: 'Atención = moneda · creo contenido continuo', platform: 'IG + TikTok + YouTube', active: true, metric: '847k views/sem', color: '#ec4899' },
  { emoji: '🔥', name: 'Drop strategy + urgency', why: 'Scarcity convierte al 3.2× más', platform: 'Shopify + TikTok Shop', active: false, metric: 'preparando próximo drop', color: '#ef4444' },
]

const CLOSED_TODAY: ClosedSale[] = [
  { emoji: '✅', customer: 'Ana Suárez',         amount: 980,  platform: 'WhatsApp', technique: 'Cierre asuntivo', ts: '17:32' },
  { emoji: '✅', customer: 'Pedro K.',           amount: 320,  platform: 'Mercado Libre', technique: 'Venta del beneficio clave', ts: '16:18' },
  { emoji: '✅', customer: 'Empresa Beta SRL',   amount: 1847, platform: 'Email + Call', technique: 'Pregunta calibrada de cierre', ts: '14:47' },
  { emoji: '✅', customer: 'Mariana Pérez',      amount: 850,  platform: 'Instagram DM', technique: 'Oferta de alto valor', ts: '13:09' },
  { emoji: '✅', customer: 'Lautaro M.',         amount: 420,  platform: 'Shopify', technique: 'Línea directa de cierre', ts: '11:42' },
  { emoji: '✅', customer: 'Lucía F.',           amount: 1240, platform: 'TikTok Shop', technique: 'Demo en vivo + oferta', ts: '10:23' },
  { emoji: '✅', customer: 'Tomás N. (upgrade)', amount: 2400, platform: 'WhatsApp + Stripe', technique: 'Cierre de alta convicción', ts: '09:51' },
  { emoji: '✅', customer: 'Carlos R.',          amount: 680,  platform: 'LinkedIn', technique: 'Venta consultiva SPIN', ts: '09:14' },
]

const NOTIF_CHANNELS: NotifChannel[] = [
  { id: 'pc',     icon: Monitor,    label: 'PC Desktop',       delivered: 47, unreadByUser: 12, online: true },
  { id: 'mobile', icon: Smartphone, label: 'Móvil (push)',     delivered: 47, unreadByUser: 8,  online: true },
  { id: 'watch',  icon: Watch,      label: 'Smartwatch',       delivered: 12, unreadByUser: 0,  online: true },
  { id: 'email',  icon: MessageCircle, label: 'Email digest',  delivered: 3,  unreadByUser: 1,  online: true },
]

export default function OmnipresentBrain() {
  const [pulse, setPulse] = useState(0)
  const [actionIdx, setActionIdx] = useState(0)

  // Pulse animation tick
  useEffect(() => {
    const id = setInterval(() => setPulse(p => (p + 1) % 100), 80)
    return () => clearInterval(id)
  }, [])

  // Rotate latest action highlight
  useEffect(() => {
    const id = setInterval(() => setActionIdx(i => (i + 1) % ACTIONS_LIVE.length), 4000)
    return () => clearInterval(id)
  }, [])

  const todayTotal = useMemo(() => CLOSED_TODAY.reduce((s, c) => s + c.amount, 0), [])
  const activeStrats = STRATEGIES.filter(s => s.active).length

  return (
    <section className="relative rounded-2xl border border-purple-500/30 bg-gradient-to-br from-[#0a0820]/95 via-[#0a0e1a]/92 to-[#0a0820]/95 backdrop-blur overflow-hidden">
      {/* Multi-color top edge: omnipresent vibe */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-cyan-400 via-purple-400 via-pink-400 via-amber-400 to-emerald-400" />

      {/* Ambient pulsing orbs background */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden opacity-40">
        <div className="absolute top-10 left-20 w-32 h-32 rounded-full bg-purple-500/20 blur-[60px] animate-pulse" style={{ animationDuration: '4s' }} />
        <div className="absolute top-1/2 right-20 w-40 h-40 rounded-full bg-cyan-500/20 blur-[80px] animate-pulse" style={{ animationDuration: '6s', animationDelay: '1s' }} />
        <div className="absolute bottom-10 left-1/2 w-36 h-36 rounded-full bg-pink-500/20 blur-[70px] animate-pulse" style={{ animationDuration: '5s', animationDelay: '2s' }} />
      </div>

      {/* Hero: omnipresent brain banner */}
      <div className="relative px-5 py-6 border-b border-white/[0.06]">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            {/* Pulsing orb */}
            <div className="relative w-16 h-16 shrink-0">
              <div
                className="absolute inset-0 rounded-full bg-gradient-to-br from-purple-500 to-cyan-500"
                style={{
                  transform: `scale(${1 + Math.sin(pulse * 0.1) * 0.08})`,
                  boxShadow: '0 0 40px rgba(168,85,247,0.6), 0 0 80px rgba(6,182,212,0.3)',
                }}
              />
              <div className="absolute inset-2 rounded-full bg-[#0a0e1a] flex items-center justify-center">
                <Brain className="w-7 h-7 text-purple-300" style={{ filter: 'drop-shadow(0 0 12px rgba(168,85,247,1))' }} />
              </div>
              <div className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-emerald-400 border-2 border-[#0a0e1a] animate-ping" />
              <div className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-emerald-400 border-2 border-[#0a0e1a]" />
            </div>

            <div>
              <h2 className="text-base font-black text-white tracking-tight mb-0.5">
                <span className="bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text text-transparent uppercase tracking-widest">SELLIA</span>
                <span className="text-white/80 ml-2 text-sm font-light">está vendiendo por vos</span>
              </h2>
              <p className="text-[12px] text-white/60">
                Omnipresente · omnipotente · omnisciente · <span className="text-emerald-400 font-bold">conectado a 14 plataformas</span> · {activeStrats} estrategias activas
              </p>
            </div>
          </div>

          {/* Big numbers */}
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-[9px] uppercase tracking-widest text-white/40">Cerrado hoy</p>
              <p className="text-3xl font-black text-emerald-400 tabular-nums">${(todayTotal / 1000).toFixed(1)}k</p>
            </div>
            <div className="w-px h-12 bg-white/10" />
            <div className="text-right">
              <p className="text-[9px] uppercase tracking-widest text-white/40">Ventas</p>
              <p className="text-3xl font-black text-white tabular-nums">{CLOSED_TODAY.length}</p>
            </div>
            <div className="w-px h-12 bg-white/10" />
            <div className="text-right">
              <p className="text-[9px] uppercase tracking-widest text-white/40">Leads nuevos</p>
              <p className="text-3xl font-black text-cyan-400 tabular-nums">47</p>
            </div>
          </div>
        </div>

        {/* Latest action highlight */}
        <div className="mt-4 rounded-xl p-3 bg-white/[0.04] border border-white/[0.08] flex items-center gap-3">
          <div className="relative">
            <div className="absolute inset-0 rounded-full animate-ping bg-emerald-400/30" />
            <div className="relative w-2 h-2 rounded-full bg-emerald-400" />
          </div>
          <span className="text-2xl shrink-0">{ACTIONS_LIVE[actionIdx].emoji}</span>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-white font-medium leading-tight">{ACTIONS_LIVE[actionIdx].text}</p>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-purple-500/15 text-purple-300 font-mono">
                <Bot className="w-2.5 h-2.5 inline mr-0.5" />
                {ACTIONS_LIVE[actionIdx].technique}
              </span>
              <span className="text-[10px] text-white/40 font-mono">· {ACTIONS_LIVE[actionIdx].platform} · {ACTIONS_LIVE[actionIdx].ts}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Body: 3-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 p-5">
        {/* COL 1 · Strategies running */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-400" />
            <h3 className="text-[11px] uppercase tracking-widest font-bold text-amber-400">ESTRATEGIAS CORRIENDO</h3>
            <span className="text-[10px] text-white/30 ml-auto">{activeStrats}/{STRATEGIES.length}</span>
          </div>
          <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">
            {STRATEGIES.map((s, i) => (
              <div key={i} className="rounded-xl border p-3 transition-all"
                style={{
                  background: s.active ? `${s.color}08` : 'rgba(255,255,255,0.02)',
                  borderColor: s.active ? `${s.color}30` : 'rgba(255,255,255,0.06)',
                  opacity: s.active ? 1 : 0.6,
                }}>
                <div className="flex items-start gap-2.5">
                  <span className="text-xl shrink-0">{s.emoji}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <p className="text-xs font-bold text-white leading-tight">{s.name}</p>
                      {s.active && (
                        <div className="w-1.5 h-1.5 rounded-full animate-pulse shrink-0" style={{ background: s.color }} />
                      )}
                    </div>
                    <p className="text-[10px] italic text-white/55 leading-snug mb-1">"{s.why}"</p>
                    <div className="flex items-center justify-between gap-2 mt-1">
                      <span className="text-[9px] text-white/40 font-mono truncate">{s.platform}</span>
                      <span className="text-[10px] font-bold shrink-0" style={{ color: s.color }}>{s.metric}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* COL 2 · Live action log */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400 animate-pulse" />
            <h3 className="text-[11px] uppercase tracking-widest font-bold text-emerald-400">QUÉ ESTOY HACIENDO AHORA</h3>
            <span className="text-[10px] text-emerald-400/70 ml-auto font-mono">● LIVE</span>
          </div>
          <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">
            {ACTIONS_LIVE.map((a, i) => (
              <div key={i} className={`rounded-xl border p-3 transition-all ${i === actionIdx ? 'bg-white/[0.06] border-white/20' : 'bg-white/[0.02] border-white/[0.05]'}`}>
                <div className="flex items-start gap-2.5">
                  <span className="text-lg shrink-0">{a.emoji}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-[12px] text-white/90 leading-snug">{a.text}</p>
                    <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                      <span className="text-[9px] px-1.5 py-0.5 rounded font-mono" style={{ background: `${a.color}18`, color: a.color }}>
                        {a.platform}
                      </span>
                      <span className="text-[9px] text-white/30 font-mono">{a.ts}</span>
                    </div>
                    <p className="text-[9px] text-purple-300/70 mt-1 italic">
                      <Bot className="w-2 h-2 inline mr-0.5" /> {a.technique}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* COL 3 · Closed today + notif channels */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-emerald-400" />
            <h3 className="text-[11px] uppercase tracking-widest font-bold text-emerald-400">VENTAS CERRADAS HOY</h3>
            <span className="text-[10px] text-white/30 ml-auto">${todayTotal.toLocaleString()}</span>
          </div>
          <div className="space-y-1.5 max-h-[260px] overflow-y-auto pr-1">
            {CLOSED_TODAY.map((sale, i) => (
              <div key={i} className="rounded-lg p-2.5 bg-emerald-500/[0.04] border border-emerald-500/15">
                <div className="flex items-center justify-between gap-2 mb-0.5">
                  <span className="text-xs font-bold text-white truncate">{sale.customer}</span>
                  <span className="text-sm font-black text-emerald-400 tabular-nums shrink-0">${sale.amount}</span>
                </div>
                <div className="flex items-center justify-between gap-2">
                  <p className="text-[9px] text-purple-300 italic truncate">{sale.technique}</p>
                  <span className="text-[9px] text-white/40 font-mono shrink-0">{sale.ts}</span>
                </div>
                <p className="text-[9px] text-white/40 font-mono mt-0.5">vía {sale.platform}</p>
              </div>
            ))}
          </div>

          {/* Notification channels */}
          <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/[0.04] p-3">
            <div className="flex items-center gap-2 mb-2">
              <Bell className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
              <h3 className="text-[10px] uppercase tracking-widest font-bold text-cyan-400">NOTIFICACIONES ACTIVAS</h3>
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {NOTIF_CHANNELS.map(n => {
                const Icon = n.icon
                return (
                  <div key={n.id} className="flex items-center gap-2 p-1.5 rounded-md bg-white/[0.03] border border-white/[0.05]">
                    <Icon className="w-3 h-3 shrink-0" style={{ color: n.online ? '#22c55e' : '#6b7280' }} />
                    <div className="flex-1 min-w-0">
                      <p className="text-[10px] font-bold text-white truncate">{n.label}</p>
                      <p className="text-[8px] text-white/40 font-mono">{n.delivered} enviadas</p>
                    </div>
                    {n.unreadByUser > 0 && (
                      <span className="text-[8px] px-1 py-0.5 rounded-full bg-red-500/30 text-red-300 font-mono font-bold shrink-0">{n.unreadByUser}</span>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom: omni-platform connector strip */}
      <div className="border-t border-white/[0.06] bg-black/30 px-5 py-3">
        <div className="flex items-center gap-3 mb-2">
          <Globe className="w-3.5 h-3.5 text-purple-400" />
          <p className="text-[10px] uppercase tracking-widest font-bold text-purple-300">VENDIENDO SIMULTÁNEAMENTE EN</p>
          <div className="flex-1 h-px bg-gradient-to-r from-purple-400/30 to-transparent" />
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          {[
            { e: '🟢', n: 'WhatsApp' },
            { e: '📷', n: 'Instagram' },
            { e: '🎵', n: 'TikTok' },
            { e: '🛍', n: 'Shopify' },
            { e: '🟡', n: 'Mercado Libre' },
            { e: '📦', n: 'Amazon' },
            { e: '🔥', n: 'Hotmart' },
            { e: '💼', n: 'LinkedIn' },
            { e: '👍', n: 'Facebook' },
            { e: '📧', n: 'Email' },
            { e: '🌐', n: 'Web propia' },
            { e: '🔍', n: 'Google Ads' },
            { e: '◼️', n: 'Meta Ads' },
            { e: '📅', n: 'Google Calendar' },
          ].map(p => (
            <span key={p.n} className="text-[10px] px-2 py-1 rounded-md bg-white/[0.04] border border-white/[0.06] text-white/70 flex items-center gap-1">
              <span>{p.e}</span> {p.n}
            </span>
          ))}
        </div>
        <p className="text-center text-[10px] text-white/40 mt-3 italic">
          <Heart className="w-3 h-3 inline text-pink-400 mr-1" />
          Vos descansás. SellIA vende, cierra, factura, cobra, envía, y fideliza. <span className="text-white/70">24/7. Sin descanso.</span>
        </p>
      </div>
    </section>
  )
}
