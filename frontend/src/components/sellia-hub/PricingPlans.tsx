'use client'

/**
 * PRICING PLANS — CORE lobe — style migration.
 * 4 tiers Stripe-ready. Plan cards kept. Glow added on prices.
 */

import { useState } from 'react'
import {
  CreditCard, Sparkles, CheckCircle2, ArrowRight, Star, X
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

interface Plan {
  id: string
  emoji: string
  name: string
  tagline: string
  priceMonthly: number
  priceAnnual: number
  highlight?: boolean
  features: { text: string; included: boolean; bold?: boolean }[]
  cta: string
  badge?: string
  color: string
}

const PLANS: Plan[] = [
  {
    id: 'free', emoji: '🌱', name: 'Trial', tagline: '14 días gratis · sin tarjeta',
    priceMonthly: 0, priceAnnual: 0, color: T.emerald, cta: 'Empezar gratis',
    features: [
      { text: '1 canal conectado (WA o IG)', included: true },
      { text: '50 conversaciones IA / mes', included: true },
      { text: '5 ventas cerradas máx', included: true },
      { text: 'Computer Use: 10 sesiones', included: true },
      { text: 'Skills básicas (20)', included: true },
      { text: 'Soporte por email', included: true },
      { text: 'Browser extensions', included: false },
      { text: 'Custom branding', included: false },
    ],
  },
  {
    id: 'starter', emoji: '⚡', name: 'Starter', tagline: 'Para autónomos · 1 negocio',
    priceMonthly: 49, priceAnnual: 39, color: T.cyan, cta: 'Empezar Starter',
    features: [
      { text: '3 canales conectados', included: true, bold: true },
      { text: '500 conversaciones IA / mes', included: true },
      { text: 'Ventas ilimitadas', included: true, bold: true },
      { text: 'Computer Use: 100 sesiones/mes', included: true },
      { text: 'Todos los skills (167)', included: true },
      { text: 'Browser extensions × 8', included: true },
      { text: '1 vertical pre-configurado', included: true },
      { text: 'Soporte chat <24h', included: true },
      { text: 'API access', included: false },
      { text: 'Multi-tenant (sub-cuentas)', included: false },
    ],
  },
  {
    id: 'pro', emoji: '🚀', name: 'Pro', tagline: 'PyMEs · varios canales',
    priceMonthly: 149, priceAnnual: 119, color: T.violet, cta: 'Empezar Pro',
    highlight: true, badge: 'MÁS POPULAR',
    features: [
      { text: '10 canales + plataformas', included: true, bold: true },
      { text: '5,000 conversaciones IA / mes', included: true },
      { text: 'Computer Use ilimitado', included: true, bold: true },
      { text: 'Todos los skills + Skill-Creator', included: true },
      { text: 'Ollama local opcional ($0 extra)', included: true, bold: true },
      { text: 'Voice IA (12 idiomas)', included: true },
      { text: 'Custom branding', included: true },
      { text: 'API access + webhooks', included: true },
      { text: 'Onboarding 1:1 (1h)', included: true },
      { text: 'Soporte priority <2h', included: true },
      { text: 'Multi-tenant', included: false },
    ],
  },
  {
    id: 'scale', emoji: '🏢', name: 'Scale', tagline: 'Empresas · agencias',
    priceMonthly: 499, priceAnnual: 399, color: '#ec4899', cta: 'Hablar con sales',
    features: [
      { text: 'Canales ilimitados', included: true, bold: true },
      { text: 'Conversaciones ilimitadas', included: true, bold: true },
      { text: 'Computer Use ilimitado', included: true },
      { text: 'Multi-tenant (sub-cuentas)', included: true, bold: true },
      { text: 'White-label opcional', included: true },
      { text: 'Cluster Ollama dedicado', included: true },
      { text: 'SLA 99.99% · DPA + GDPR', included: true },
      { text: 'API rate-limit personalizado', included: true },
      { text: 'CSM dedicado', included: true },
      { text: 'Onboarding equipo (4h)', included: true },
      { text: 'Soporte 24/7', included: true },
    ],
  },
]

const ADD_ONS = [
  { emoji: '🤖', name: 'Computer Use sessions extra', price: '$0.15', unit: 'por sesión sobre límite' },
  { emoji: '💬', name: 'Conversaciones IA extra',     price: '$0.02', unit: 'por conversación' },
  { emoji: '🎓', name: 'Skill personalizado',         price: '$499',  unit: 'one-time setup' },
  { emoji: '📞', name: 'Soporte phone',               price: '$199',  unit: 'por mes (Pro+)' },
  { emoji: '🏷', name: 'White-label completo',        price: '$1,499',unit: 'por mes' },
  { emoji: '🎯', name: 'Vertical custom',             price: '$2,499',unit: 'one-time build' },
]

export default function PricingPlans() {
  const [billing, setBilling] = useState<'monthly' | 'annual'>('annual')

  return (
    <section style={{ background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 16, overflow: 'hidden' }}>
      <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, #a855f780, #06B6D480, transparent)' }} />

      {/* Header */}
      <div style={{ padding: '20px', borderBottom: '1px solid ' + T.border, textAlign: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginBottom: 6 }}>
          <CreditCard style={{ width: 18, height: 18, color: T.emerald }} />
          <div style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, letterSpacing: '.06em', textTransform: 'uppercase' }}>
            PRICING · COBRA DESDE DÍA 1
          </div>
        </div>
        <div style={{ fontSize: 11, color: T.textSub, marginBottom: 14 }}>4 tiers · Stripe Subscriptions · cancel anytime</div>

        {/* Billing toggle */}
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: 4, borderRadius: 10, background: T.bgApp, border: '1px solid ' + T.border }}>
          {(['monthly', 'annual'] as const).map(b => (
            <button key={b} onClick={() => setBilling(b)}
              style={{ padding: '5px 18px', borderRadius: 8, fontSize: 11, fontWeight: 700, cursor: 'pointer', transition: 'all .15s', background: billing === b ? (b === 'annual' ? T.emerald + '22' : T.bgCardHov) : 'transparent', border: '1px solid ' + (billing === b ? (b === 'annual' ? T.emerald + '44' : T.border) : 'transparent'), color: billing === b ? (b === 'annual' ? T.emerald : T.textPrim) : T.textSub, display: 'flex', alignItems: 'center', gap: 6 }}>
              {b === 'monthly' ? 'Mensual' : <><span>Anual</span><span style={{ fontSize: 9, padding: '1px 6px', borderRadius: 4, background: T.emerald + '30', color: T.emerald }}>-20%</span></>}
            </button>
          ))}
        </div>
      </div>

      {/* Plans grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, padding: 20 }}>
        {PLANS.map(plan => {
          const price = billing === 'monthly' ? plan.priceMonthly : plan.priceAnnual
          return (
            <div key={plan.id} style={{ position: 'relative', borderRadius: 14, border: '1px solid ' + (plan.highlight ? plan.color + '70' : T.border), background: plan.highlight ? plan.color + '0E' : T.bgApp, padding: 16, display: 'flex', flexDirection: 'column', boxShadow: plan.highlight ? '0 0 32px ' + plan.color + '25' : 'none' }}>
              {plan.badge && (
                <div style={{ position: 'absolute', top: -12, left: '50%', transform: 'translateX(-50%)', padding: '2px 12px', borderRadius: 20, fontSize: 9, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.06em', background: plan.color, color: '#fff', boxShadow: '0 0 12px ' + plan.color + '80', whiteSpace: 'nowrap' }}>
                  ⭐ {plan.badge}
                </div>
              )}

              <div style={{ textAlign: 'center', marginBottom: 12 }}>
                <span style={{ fontSize: 28 }}>{plan.emoji}</span>
                <div style={{ fontSize: 15, fontWeight: 800, color: plan.color, marginTop: 4 }}>{plan.name}</div>
                <div style={{ fontSize: 10, color: T.textSub, marginTop: 2 }}>{plan.tagline}</div>
              </div>

              <div style={{ textAlign: 'center', marginBottom: 14 }}>
                {price === 0 ? (
                  <div style={{ fontSize: 28, fontWeight: 800, color: T.textPrim, textShadow: '0 0 20px ' + plan.color + '88' }}>GRATIS</div>
                ) : (
                  <>
                    <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'center', gap: 3 }}>
                      <span style={{ fontSize: 11, color: T.textSub }}>USD</span>
                      <span style={{ fontSize: 30, fontWeight: 800, color: T.textPrim, textShadow: '0 0 20px ' + plan.color + '88' }}>${price}</span>
                      <span style={{ fontSize: 11, color: T.textSub }}>/mes</span>
                    </div>
                    {billing === 'annual' && (
                      <div style={{ fontSize: 10, color: T.emerald, marginTop: 2 }}>facturado ${price * 12}/año</div>
                    )}
                  </>
                )}
              </div>

              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 14 }}>
                {plan.features.map((f, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 6 }}>
                    {f.included
                      ? <CheckCircle2 style={{ width: 12, height: 12, color: plan.color, flexShrink: 0, marginTop: 1 }} />
                      : <X style={{ width: 12, height: 12, color: T.textSub + '44', flexShrink: 0, marginTop: 1 }} />}
                    <span style={{ fontSize: 10, lineHeight: 1.4, color: f.included ? (f.bold ? T.textPrim : T.textSub + 'dd') : T.textSub + '44', fontWeight: f.bold ? 700 : 400, textDecoration: f.included ? 'none' : 'line-through' }}>
                      {f.text}
                    </span>
                  </div>
                ))}
              </div>

              <button style={{ width: '100%', padding: '9px 0', borderRadius: 10, fontSize: 11, fontWeight: 700, cursor: 'pointer', transition: 'all .15s', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, background: plan.highlight ? plan.color : plan.color + '20', border: '1px solid ' + (plan.highlight ? 'transparent' : plan.color + '44'), color: plan.highlight ? '#fff' : plan.color, boxShadow: plan.highlight ? '0 4px 16px ' + plan.color + '44' : 'none' }}>
                {plan.cta} <ArrowRight style={{ width: 12, height: 12 }} />
              </button>
            </div>
          )
        })}
      </div>

      {/* Add-ons */}
      <div style={{ padding: '0 20px 20px' }}>
        <div style={{ background: T.bgApp, border: '1px solid ' + T.border, borderRadius: 12, padding: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <Sparkles style={{ width: 14, height: 14, color: T.amber }} />
            <div style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.amber }}>ADD-ONS · USAGE BASED</div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
            {ADD_ONS.map(a => (
              <div key={a.name} style={{ background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 8, padding: '10px 12px', display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <span style={{ fontSize: 18, flexShrink: 0 }}>{a.emoji}</span>
                <div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: T.textPrim }}>{a.name}</div>
                  <div style={{ fontSize: 12, fontWeight: 800, color: T.amber, textShadow: '0 0 20px ' + T.amber + '88' }}>{a.price}</div>
                  <div style={{ fontSize: 10, color: T.textSub }}>{a.unit}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{ borderTop: '1px solid ' + T.border, padding: '10px 20px', textAlign: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, fontSize: 11, color: T.textSub }}>
          <Star style={{ width: 12, height: 12, color: T.emerald }} />
          Stripe Subscriptions ready · checkout en 60 seg · prorate · dunning · taxes auto · refund cancel anytime.
        </div>
      </div>
    </section>
  )
}
