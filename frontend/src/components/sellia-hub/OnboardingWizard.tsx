'use client'

/**
 * ONBOARDING WIZARD
 *
 * Flow 5 pasos · user nuevo → vendiendo en <10min.
 * Cada paso = OAuth/setup real para conectar canal + IA + payment.
 */

import { useState } from 'react'
import {
  CheckCircle2, ArrowRight, ArrowLeft, Sparkles, Bot,
  ShoppingBag, CreditCard, Briefcase, MessageCircle, Rocket
} from 'lucide-react'

interface Step {
  id: number
  emoji: string
  title: string
  subtitle: string
  icon: React.ElementType
  color: string
}

const STEPS: Step[] = [
  { id: 1, emoji: '👋', title: 'Tu negocio',         subtitle: 'Contanos qué vendés',              icon: Briefcase,    color: '#3b82f6' },
  { id: 2, emoji: '💬', title: 'Conectá canal',       subtitle: 'WhatsApp · IG · Web · etc.',       icon: MessageCircle, color: '#22c55e' },
  { id: 3, emoji: '🛍', title: 'Conectá tienda',       subtitle: 'Shopify · ML · Amazon · etc.',     icon: ShoppingBag,   color: '#fbbf24' },
  { id: 4, emoji: '💳', title: 'Cobrar pagos',         subtitle: 'Stripe · Mercado Pago',            icon: CreditCard,    color: '#a855f7' },
  { id: 5, emoji: '🚀', title: 'Activar SellIA',       subtitle: 'IA empieza a vender por vos',     icon: Rocket,        color: '#ec4899' },
]

const CHANNELS = [
  { id: 'wa',   emoji: '💚', name: 'WhatsApp Business', color: '#25d366', desc: 'Cloud API · catálogo' },
  { id: 'ig',   emoji: '📷', name: 'Instagram DM',       color: '#E1306C', desc: 'Posts · DMs · Shop' },
  { id: 'fb',   emoji: '👍', name: 'Facebook Messenger', color: '#1877F2', desc: 'Page · Messenger' },
  { id: 'em',   emoji: '✉️', name: 'Email',              color: '#3b82f6', desc: 'Gmail · Outlook' },
  { id: 'web',  emoji: '🌐', name: 'Web chat widget',     color: '#06b6d4', desc: 'Embed JS · webhook' },
  { id: 'li',   emoji: '💼', name: 'LinkedIn',            color: '#0A66C2', desc: 'B2B outreach' },
]

const STORES = [
  { id: 'shopify',  emoji: '🛍', name: 'Shopify',          color: '#95BF47', oauth: 'OAuth · 1-click' },
  { id: 'ml',       emoji: '🟡', name: 'Mercado Libre',    color: '#FFE600', oauth: 'OAuth · ML SDK' },
  { id: 'amazon',   emoji: '📦', name: 'Amazon Seller',     color: '#FF9900', oauth: 'LWA + SP-API' },
  { id: 'woo',      emoji: '🛒', name: 'WooCommerce',       color: '#7B57A2', oauth: 'API key' },
  { id: 'nube',     emoji: '🇦🇷', name: 'Tienda Nube',       color: '#0099FF', oauth: 'OAuth nativo' },
  { id: 'etsy',     emoji: '🧶', name: 'Etsy',              color: '#F1641E', oauth: 'OAuth 2.0' },
  { id: 'hotmart',  emoji: '🔥', name: 'Hotmart',           color: '#EF4E22', oauth: 'API key' },
  { id: 'custom',   emoji: '🌐', name: 'Web propia (custom)',color: '#a855f7', oauth: 'Webhook · API' },
]

const PAYMENTS = [
  { id: 'stripe',  emoji: '🟣', name: 'Stripe',           color: '#635bff', features: 'Tarjetas · BNPL · payouts' },
  { id: 'mp',      emoji: '🟡', name: 'Mercado Pago',      color: '#fbbf24', features: 'Tarjetas · QR · cuotas LATAM' },
  { id: 'pp',      emoji: '🅿️', name: 'PayPal',           color: '#0070ba', features: 'Multi-país · seguro' },
  { id: 'wise',    emoji: '🌎', name: 'Wise Business',     color: '#163300', features: 'Multi-currency · transfers' },
]

export default function OnboardingWizard() {
  const [current, setCurrent] = useState(1)
  const [bizName, setBizName] = useState('')
  const [bizType, setBizType] = useState('')
  const [selectedChannel, setSelectedChannel] = useState<string | null>(null)
  const [selectedStore, setSelectedStore] = useState<string | null>(null)
  const [selectedPayment, setSelectedPayment] = useState<string | null>(null)

  const canProceed =
    (current === 1 && bizName.length > 2 && bizType.length > 0) ||
    (current === 2 && selectedChannel) ||
    (current === 3 && selectedStore) ||
    (current === 4 && selectedPayment) ||
    current === 5

  const progress = (current / STEPS.length) * 100

  return (
    <section className="relative rounded-2xl border border-cyan-500/30 bg-gradient-to-br from-[#081218]/90 via-[#0a0e1a]/93 to-[#08081a]/95 backdrop-blur overflow-hidden">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-cyan-400/80 via-pink-400/60 to-transparent" />

      {/* Header */}
      <div className="px-5 py-4 border-b border-white/[0.06]">
        <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/25 to-pink-500/15 border border-cyan-500/40 flex items-center justify-center">
              <Rocket className="w-5 h-5 text-cyan-400" style={{ filter: 'drop-shadow(0 0 8px rgba(6,182,212,0.7))' }} />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                <span className="bg-gradient-to-r from-cyan-400 via-pink-400 to-cyan-400 bg-clip-text text-transparent">ONBOARDING WIZARD</span>
                <span className="text-white/40 font-light normal-case tracking-normal ml-2">·  Vendiendo en &lt;10min</span>
              </h2>
              <p className="text-[11px] text-white/40 mt-0.5">5 pasos · OAuth nativo · sin código</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-[9px] uppercase tracking-widest text-white/40">Paso</p>
            <p className="text-base font-black text-cyan-400 tabular-nums">{current}/{STEPS.length}</p>
          </div>
        </div>

        {/* Step indicators */}
        <div className="flex items-center gap-1">
          {STEPS.map((s, i) => {
            const done = current > s.id
            const active = current === s.id
            return (
              <div key={s.id} className="flex-1 flex items-center gap-1">
                <div className="flex flex-col items-center flex-1">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm shrink-0 transition-all"
                    style={{
                      background: done ? `${s.color}25` : active ? `${s.color}40` : 'rgba(255,255,255,0.05)',
                      border: `1.5px solid ${done || active ? s.color : 'rgba(255,255,255,0.1)'}`,
                      boxShadow: active ? `0 0 12px ${s.color}50` : 'none',
                    }}>
                    {done ? <CheckCircle2 className="w-4 h-4" style={{ color: s.color }} /> : <span>{s.emoji}</span>}
                  </div>
                  <p className="text-[8px] font-mono uppercase tracking-wider mt-1 text-center" style={{ color: active ? s.color : 'rgba(255,255,255,0.4)' }}>
                    {s.title}
                  </p>
                </div>
                {i < STEPS.length - 1 && (
                  <div className="h-px flex-1" style={{ background: done ? s.color : 'rgba(255,255,255,0.08)' }} />
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Step content */}
      <div className="p-5 min-h-[300px]">
        {/* Step 1 · biz info */}
        {current === 1 && (
          <div className="space-y-4 max-w-md mx-auto">
            <div className="text-center">
              <span className="text-4xl">👋</span>
              <h3 className="text-base font-bold text-white mt-2">¿Cómo se llama tu negocio?</h3>
              <p className="text-[11px] text-white/50">Personalizamos todo desde acá</p>
            </div>
            <div>
              <label className="text-[10px] uppercase tracking-widest text-white/40 font-bold mb-1 block">Nombre del negocio</label>
              <input
                type="text"
                value={bizName}
                onChange={e => setBizName(e.target.value)}
                placeholder="Ej: Café Aurora · Estudio Jurídico Sosa · Clínica Vida"
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-cyan-400/40"
              />
            </div>
            <div>
              <label className="text-[10px] uppercase tracking-widest text-white/40 font-bold mb-1 block">¿Qué vendés?</label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: 'goods', emoji: '🛍', label: 'Productos físicos' },
                  { id: 'digital', emoji: '💾', label: 'Productos digitales' },
                  { id: 'service', emoji: '🩺', label: 'Servicios profesionales' },
                  { id: 'food', emoji: '🍔', label: 'Gastronomía · delivery' },
                  { id: 'events', emoji: '🎉', label: 'Eventos · turismo' },
                  { id: 'edu', emoji: '🎓', label: 'Cursos · coaching' },
                ].map(t => (
                  <button
                    key={t.id}
                    onClick={() => setBizType(t.id)}
                    className="flex items-center gap-2 p-2.5 rounded-lg border transition-all"
                    style={
                      bizType === t.id
                        ? { background: 'rgba(6,182,212,0.15)', borderColor: 'rgba(6,182,212,0.5)' }
                        : { background: 'rgba(255,255,255,0.02)', borderColor: 'rgba(255,255,255,0.08)' }
                    }
                  >
                    <span className="text-xl">{t.emoji}</span>
                    <span className="text-xs text-white/85">{t.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Step 2 · channel */}
        {current === 2 && (
          <div className="space-y-3">
            <div className="text-center mb-3">
              <h3 className="text-base font-bold text-white">¿Por dónde te contactan los clientes?</h3>
              <p className="text-[11px] text-white/50">Conectá UNO ahora · más después</p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {CHANNELS.map(c => (
                <button
                  key={c.id}
                  onClick={() => setSelectedChannel(c.id)}
                  className="text-left p-3 rounded-xl border transition-all"
                  style={
                    selectedChannel === c.id
                      ? { background: `${c.color}15`, borderColor: `${c.color}60`, boxShadow: `0 0 16px ${c.color}25` }
                      : { background: 'rgba(255,255,255,0.02)', borderColor: 'rgba(255,255,255,0.08)' }
                  }
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-2xl">{c.emoji}</span>
                    <p className="text-xs font-bold text-white">{c.name}</p>
                  </div>
                  <p className="text-[10px] text-white/50">{c.desc}</p>
                  {selectedChannel === c.id && (
                    <div className="mt-2 inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-widest" style={{ color: c.color }}>
                      <Sparkles className="w-2.5 h-2.5" /> Seleccionado
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 3 · store */}
        {current === 3 && (
          <div className="space-y-3">
            <div className="text-center mb-3">
              <h3 className="text-base font-bold text-white">¿Dónde tenés tu tienda?</h3>
              <p className="text-[11px] text-white/50">Conectamos OAuth · 1 click</p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {STORES.map(s => (
                <button
                  key={s.id}
                  onClick={() => setSelectedStore(s.id)}
                  className="text-left p-3 rounded-xl border transition-all"
                  style={
                    selectedStore === s.id
                      ? { background: `${s.color}15`, borderColor: `${s.color}60`, boxShadow: `0 0 16px ${s.color}25` }
                      : { background: 'rgba(255,255,255,0.02)', borderColor: 'rgba(255,255,255,0.08)' }
                  }
                >
                  <span className="text-2xl">{s.emoji}</span>
                  <p className="text-xs font-bold text-white mt-1">{s.name}</p>
                  <p className="text-[10px] text-white/50 mt-0.5">{s.oauth}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 4 · payment */}
        {current === 4 && (
          <div className="space-y-3">
            <div className="text-center mb-3">
              <h3 className="text-base font-bold text-white">¿Cómo cobrás?</h3>
              <p className="text-[11px] text-white/50">SellIA cobra y factura por vos</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {PAYMENTS.map(p => (
                <button
                  key={p.id}
                  onClick={() => setSelectedPayment(p.id)}
                  className="text-left p-3 rounded-xl border transition-all"
                  style={
                    selectedPayment === p.id
                      ? { background: `${p.color}15`, borderColor: `${p.color}60`, boxShadow: `0 0 16px ${p.color}25` }
                      : { background: 'rgba(255,255,255,0.02)', borderColor: 'rgba(255,255,255,0.08)' }
                  }
                >
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{p.emoji}</span>
                    <div>
                      <p className="text-sm font-bold text-white">{p.name}</p>
                      <p className="text-[10px] text-white/50">{p.features}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 5 · activate */}
        {current === 5 && (
          <div className="text-center max-w-md mx-auto space-y-4">
            <div className="relative inline-block">
              <div className="absolute inset-0 rounded-full bg-pink-500/30 blur-2xl animate-pulse" />
              <div className="relative w-20 h-20 rounded-full bg-gradient-to-br from-cyan-500 to-pink-500 flex items-center justify-center text-4xl">
                🚀
              </div>
            </div>
            <h3 className="text-xl font-black text-white">¡Todo listo, {bizName || 'Lucas'}!</h3>
            <p className="text-[12px] text-white/60 leading-snug">
              SellIA va a empezar a vender por vos en <span className="text-cyan-300 font-bold">{CHANNELS.find(c => c.id === selectedChannel)?.name || 'tu canal'}</span>,
              conectado a <span className="text-amber-300 font-bold">{STORES.find(s => s.id === selectedStore)?.name || 'tu tienda'}</span>,
              cobrando con <span className="text-purple-300 font-bold">{PAYMENTS.find(p => p.id === selectedPayment)?.name || 'Stripe'}</span>.
            </p>
            <div className="rounded-xl p-4 bg-emerald-500/[0.08] border border-emerald-500/25 text-left space-y-1.5">
              <p className="text-[10px] uppercase tracking-widest text-emerald-400 font-bold flex items-center gap-1">
                <Bot className="w-2.5 h-2.5" /> PRIMEROS 60 MINUTOS · IA AUTOMATIZA:
              </p>
              {[
                'Importa catálogo de tu tienda',
                'Configura skills del vertical',
                'Carga tus 36 leyendas de venta',
                'Sincroniza inventario y precios',
                'Empieza a responder + vender',
              ].map((t, i) => (
                <div key={i} className="flex items-center gap-2">
                  <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                  <span className="text-[11px] text-white/80">{t}</span>
                </div>
              ))}
            </div>
            <button className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-pink-500 text-white font-bold text-sm flex items-center justify-center gap-2 hover:scale-[1.02] transition-all"
              style={{ boxShadow: '0 4px 24px rgba(236,72,153,0.4)' }}>
              <Rocket className="w-4 h-4" />
              Activar SellIA · Empezar trial 14 días
            </button>
            <p className="text-[10px] text-white/40">Sin tarjeta · cancel anytime · soporte 24/7</p>
          </div>
        )}
      </div>

      {/* Footer nav */}
      <div className="border-t border-white/[0.06] px-5 py-3 flex items-center justify-between bg-black/30">
        <button
          onClick={() => setCurrent(c => Math.max(1, c - 1))}
          disabled={current === 1}
          className="flex items-center gap-1.5 text-[11px] text-white/60 disabled:opacity-30 disabled:cursor-not-allowed hover:text-white"
        >
          <ArrowLeft className="w-3 h-3" />
          Atrás
        </button>

        {/* Progress bar */}
        <div className="flex-1 mx-4 max-w-xs">
          <div className="h-1 bg-white/5 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-cyan-400 to-pink-400 rounded-full transition-all" style={{ width: `${progress}%` }} />
          </div>
        </div>

        {current < STEPS.length ? (
          <button
            onClick={() => setCurrent(c => Math.min(STEPS.length, c + 1))}
            disabled={!canProceed}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-[11px] font-bold transition-all"
            style={
              canProceed
                ? { background: 'linear-gradient(135deg, #06b6d4, #ec4899)', color: '#fff', boxShadow: '0 0 12px rgba(236,72,153,0.4)' }
                : { background: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.3)', cursor: 'not-allowed' }
            }
          >
            Siguiente
            <ArrowRight className="w-3 h-3" />
          </button>
        ) : (
          <div className="text-[10px] text-emerald-400 font-bold uppercase tracking-widest flex items-center gap-1">
            <Sparkles className="w-3 h-3" />
            Listo para activar
          </div>
        )}
      </div>
    </section>
  )
}
