'use client'

/**
 * SELLIA · landing CRO 2026.
 *
 * Direction: high-conversion landing inspired by the world's best (Linear, Stripe, Webflow, Framer).
 *   - LIGHT theme (slate-50 surface, slate-900 ink) · contrasts with dark HUD product.
 *   - Single objective per screen, single CTA color: emerald-500.
 *   - Zero top navigation menu (only logo) · "single-purpose page" pattern.
 *   - Mobile-first · sticky bottom CTA bar · big tap targets.
 *   - Benefits (life impact), not features (specs).
 *   - Stylized HUD product screenshot in hero (mini-dashboard React) shows system live.
 *   - Social proof: trust counter live tick + brand strip + testimonials grid + ratings.
 *   - FAQ collapsible at bottom · email-only short form.
 *   - Microcopy: action-oriented, urgency without sleaze.
 */

import Link from 'next/link'
import { useEffect, useRef, useState, type FormEvent } from 'react'
import { motion, useScroll, useSpring, useTransform, type Variants } from 'framer-motion'
import {
  ArrowRight, Sparkles, Check, ChevronDown, Plus, Star, Zap, Brain, Bot, Clock,
  ShieldCheck, TrendingUp, MessageSquare, Lock, MonitorCheck, Mic, Globe2,
} from 'lucide-react'


/* ────────────────────────────  fonts + theme  ───────────────────────── */


const Theme = (): React.JSX.Element => (
  <>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
    <link
      rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap"
    />
    <style>{`
      html, body { font-family: "Inter", ui-sans-serif, system-ui, -apple-system, sans-serif; background: #f8fafc; color: #0f172a; }
      .mono { font-family: "JetBrains Mono", ui-monospace, monospace; }
      .display { font-weight: 800; letter-spacing: -0.025em; }
      @keyframes ticker { 0%{transform:translateX(0)} 100%{transform:translateX(-50%)} }
      @keyframes pulse-dot { 0%,100%{opacity:.55} 50%{opacity:1} }
      @keyframes shine { 0%{transform:translateX(-120%)} 100%{transform:translateX(220%)} }
      @keyframes blink { 0%,49%{opacity:1} 50%,100%{opacity:0} }
    `}</style>
  </>
)


/* ────────────────────────────  helpers  ───────────────────────── */


const useCountUp = (target: number, duration = 1600): number => {
  const [v, setV] = useState<number>(0)
  const started = useRef<boolean>(false)
  useEffect(() => {
    if (started.current) return
    started.current = true
    const start = performance.now()
    let raf = 0
    const tick = (t: number): void => {
      const p = Math.min((t - start) / duration, 1)
      setV(target * (1 - Math.pow(1 - p, 3)))
      if (p < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [target, duration])
  return v
}


const StaggerContainer: Variants = { hidden: {}, visible: { transition: { staggerChildren: 0.06 } } }
const StaggerItem: Variants = {
  hidden: { opacity: 0, y: 18 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.16, 1, 0.3, 1] } },
}


/* ────────────────────────────  page  ───────────────────────── */


export default function HomePage(): React.JSX.Element {
  const { scrollYProgress } = useScroll()
  const progress = useSpring(scrollYProgress, { stiffness: 80, damping: 20 })
  const progressWidth = useTransform(progress, [0, 1], ['0%', '100%'])

  return (
    <div className="min-h-screen relative overflow-x-hidden bg-slate-50 text-slate-900">
      <Theme />

      <motion.div className="fixed top-0 inset-x-0 z-[60] h-[2px] origin-left bg-emerald-500" style={{ width: progressWidth }} />

      <MinimalHeader />
      <Hero />
      <SocialProofStrip />
      <BenefitsGrid />
      <ProductPreview />
      <NumbersBlock />
      <Testimonials />
      <SecurityBanner />
      <Pricing />
      <FAQ />
      <FinalCTA />
      <Footer />
      <MobileBottomCTA />
    </div>
  )
}


/* ────────────────────────────  minimal header  ───────────────────────── */


const MinimalHeader = (): React.JSX.Element => (
  <header className="sticky top-0 z-40 bg-white/85 backdrop-blur-xl border-b border-slate-200/70">
    <div className="max-w-6xl mx-auto px-5 sm:px-6 h-[60px] flex items-center">
      <Link href="/" className="flex items-center gap-2.5">
        <Logomark />
        <span className="text-[16px] font-extrabold tracking-tight">SellIA</span>
      </Link>
      <a
        href="#signup"
        className="ml-auto inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-[13px] font-bold shadow-lg shadow-emerald-500/30 hover:scale-105 transition active:scale-100"
      >
        Comenzar gratis <ArrowRight className="w-3.5 h-3.5" />
      </a>
    </div>
  </header>
)


const Logomark = (): React.JSX.Element => (
  <span className="relative w-[32px] h-[32px] rounded-lg bg-slate-900 flex items-center justify-center"
    style={{ boxShadow: '0 6px 20px -6px rgba(16,185,129,0.45)' }}
  >
    <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="#10b981" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 17 L9 11 L13 15 L21 7" />
      <circle cx="21" cy="7" r="1.6" fill="#10b981" />
    </svg>
  </span>
)


/* ────────────────────────────  hero  ───────────────────────── */


const Hero = (): React.JSX.Element => {
  const [email, setEmail] = useState<string>('')
  const [sent, setSent] = useState<boolean>(false)
  const onSubmit = (e: FormEvent): void => {
    e.preventDefault()
    if (!email.trim()) return
    setSent(true)
    window.setTimeout(() => {
      window.location.assign(`/sellia-signup?email=${encodeURIComponent(email)}`)
    }, 600)
  }
  return (
    <section className="relative pt-16 sm:pt-24 pb-12 px-5 sm:px-6">
      {/* soft mesh background */}
      <div className="absolute inset-0 pointer-events-none -z-10">
        <div className="absolute -top-32 left-1/2 -translate-x-1/2 w-[1200px] h-[600px] rounded-full blur-[140px] bg-emerald-300/30" />
        <div className="absolute top-40 right-0 w-[500px] h-[500px] rounded-full blur-[140px] bg-blue-200/40" />
        <div className="absolute inset-0 opacity-[0.5]" style={{
          backgroundImage: 'radial-gradient(circle, rgba(15,23,42,0.05) 1px, transparent 1px)',
          backgroundSize: '28px 28px',
          maskImage: 'radial-gradient(circle at 50% 30%, black, transparent 70%)',
        }} />
      </div>

      <div className="max-w-6xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white border border-slate-200 shadow-sm mb-7"
        >
          <span className="flex">
            {Array.from({ length: 5 }).map((_, i) => (
              <Star key={i} className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
            ))}
          </span>
          <span className="text-[12.5px] font-medium text-slate-700">4.9/5 · 1,847 negocios activos esta semana</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.05 }}
          className="display text-[clamp(2.4rem,6.5vw,5.2rem)] leading-[1.02] tracking-tight max-w-4xl mx-auto"
          style={{ textWrap: 'balance' as React.CSSProperties['textWrap'] }}
        >
          Tu nuevo vendedor IA cierra ventas{' '}
          <span className="bg-gradient-to-r from-emerald-500 via-emerald-600 to-blue-600 bg-clip-text text-transparent">
            mientras dormís.
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55, delay: 0.15 }}
          className="mt-6 text-[16px] sm:text-[18px] text-slate-600 max-w-2xl mx-auto leading-relaxed"
        >
          SellIA responde, cualifica, factura y fideliza por vos en 14 canales y 12 idiomas. Sin codear, sin contratar, sin pausa.{' '}
          <strong className="text-slate-900">Conectás en 5 minutos. Vende esta misma noche.</strong>
        </motion.p>

        {/* email signup */}
        <motion.form
          onSubmit={onSubmit}
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55, delay: 0.25 }}
          id="signup"
          className="mt-9 max-w-[480px] mx-auto"
        >
          <div className="relative flex items-stretch gap-2 rounded-2xl bg-white border border-slate-200 shadow-xl shadow-emerald-500/5 p-2">
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="tu@correo.com"
              className="flex-1 bg-transparent outline-none px-3 py-2 text-[14px] sm:text-[15px] placeholder:text-slate-400"
            />
            <button
              type="submit"
              disabled={sent}
              className="inline-flex items-center gap-1.5 px-4 sm:px-5 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-[13.5px] font-bold shadow-lg shadow-emerald-500/30 hover:scale-105 transition active:scale-100 disabled:opacity-70"
            >
              {sent ? 'Llevándote…' : 'Comenzar gratis'}
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="mt-3 flex items-center justify-center gap-1.5 text-[12px] text-slate-500">
            <Check className="w-3.5 h-3.5 text-emerald-500" />
            Sin tarjeta · sin compromiso · cancelás cuando quieras
          </div>
        </motion.form>

        {/* small badges */}
        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5, delay: 0.4 }}
          className="mt-7 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-[12px] text-slate-500"
        >
          <span className="inline-flex items-center gap-1.5"><ShieldCheck className="w-3.5 h-3.5 text-emerald-500" /> SOC2-ready</span>
          <span className="inline-flex items-center gap-1.5"><Lock className="w-3.5 h-3.5 text-emerald-500" /> Datos cifrados</span>
          <span className="inline-flex items-center gap-1.5"><Clock className="w-3.5 h-3.5 text-emerald-500" /> Setup en 5 min</span>
          <span className="inline-flex items-center gap-1.5"><Globe2 className="w-3.5 h-3.5 text-emerald-500" /> 12 idiomas</span>
        </motion.div>

        {/* hero preview · stylized HUD */}
        <motion.div
          initial={{ opacity: 0, y: 28 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.5 }}
          className="relative mt-16 max-w-5xl mx-auto"
        >
          <HUDPreview />
          {/* arrow pointing to CTA */}
          <svg
            className="hidden md:block absolute -top-10 -right-2 lg:right-12 w-32 h-20 text-emerald-500/80"
            viewBox="0 0 200 100" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          >
            <path d="M180 10 C 120 20, 80 30, 40 70" strokeDasharray="3 4" />
            <path d="M40 70 L 55 60 M40 70 L 50 78" />
          </svg>
        </motion.div>
      </div>
    </section>
  )
}


/* ────────────────────────────  HUD preview window  ───────────────────────── */


const HUDPreview = (): React.JSX.Element => {
  const [tick, setTick] = useState<number>(0)
  useEffect(() => {
    const id = window.setInterval(() => setTick((t) => t + 1), 1500)
    return () => window.clearInterval(id)
  }, [])
  const tokensPerMin = 184_000 + ((tick * 137) % 4_500)
  const leads = 1284 + ((tick * 17) % 30)
  return (
    <div
      className="relative rounded-2xl bg-slate-950 border border-slate-800 overflow-hidden text-left"
      style={{
        boxShadow:
          '0 80px 200px -40px rgba(2,6,23,0.45), 0 30px 60px -30px rgba(16,185,129,0.18), 0 0 0 1px rgba(255,255,255,0.04)',
      }}
    >
      {/* window chrome */}
      <div className="flex items-center gap-2 px-3.5 py-2.5 border-b border-slate-800 bg-slate-900/80">
        <span className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
        <span className="w-2.5 h-2.5 rounded-full bg-[#febc2e]" />
        <span className="w-2.5 h-2.5 rounded-full bg-[#28c840]" />
        <div className="mx-auto inline-flex items-center gap-2 px-2 py-0.5 rounded mono text-[10px] tracking-widest uppercase text-slate-400 bg-slate-950 border border-slate-800">
          sellia · mission control
        </div>
        <span className="w-5" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[170px_1fr] min-h-[420px]">
        <aside className="border-r border-slate-800 py-3 hidden md:block">
          {[
            ['overview', true],
            ['pipeline', false],
            ['computer use', false],
            ['voz', false],
            ['agentes', false],
            ['compliance', false],
          ].map(([name, active]) => (
            <div key={name as string} className={`px-3.5 py-1.5 mono text-[12px] ${active ? 'text-emerald-400' : 'text-slate-400'}`}>
              {active ? '› ' : '  '}{name}
            </div>
          ))}
          <div className="px-3.5 mt-4 mono text-[9px] tracking-[0.3em] uppercase text-slate-500">streams</div>
          {['leads', 'deals', 'revenue'].map((s) => (
            <div key={s} className="px-3.5 py-1.5 mono text-[12px] text-slate-500">  · {s}</div>
          ))}
        </aside>

        <div className="p-4 space-y-3">
          <div className="grid grid-cols-3 gap-2">
            <HudKpi label="leads/24h" value={leads.toString()} />
            <HudKpi label="win rate"  value="42.6%" emphasize />
            <HudKpi label="mrr"       value="$47.3k" />
          </div>

          <div className="border border-slate-800 rounded-lg overflow-hidden">
            <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-800">
              <span className="mono text-[10px] tracking-[0.3em] uppercase text-slate-500">activity · live</span>
              <span className="mono text-[10px] text-emerald-400 inline-flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" style={{ animation: 'pulse-dot 1.6s infinite' }} />
                streaming
              </span>
            </div>
            <ul className="divide-y divide-slate-800">
              {LIVE_ROWS.map((r, i) => (
                <li key={i} className="grid grid-cols-[12px_60px_1fr_60px] items-center gap-2 px-3 py-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${r.win ? 'bg-emerald-400' : 'bg-slate-500'}`} />
                  <span className="mono text-[10px] text-slate-500">{r.t}</span>
                  <span className="text-[12px] text-slate-300 truncate">{r.text}</span>
                  <span className="mono text-[10px] text-right text-slate-500">{r.tag}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="border border-slate-800 rounded-lg p-2.5 flex items-center gap-2">
            <span className="w-6 h-6 rounded-md bg-emerald-500 flex items-center justify-center">
              <Brain className="w-3.5 h-3.5 text-slate-950" />
            </span>
            <span className="text-[12.5px] text-slate-300 truncate">
              recuperá los carritos abandonados de hoy y mandales WhatsApp
              <span className="inline-block w-2 h-3 align-middle ml-0.5 bg-emerald-400" style={{ animation: 'blink 1s steps(2) infinite' }} />
            </span>
            <span className="ml-auto mono text-[10px] text-slate-500 tracking-widest">↵</span>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <HudQuick icon={MonitorCheck} label="Computer Use" />
            <HudQuick icon={Mic}          label="Manos libres" />
            <HudQuick icon={MessageSquare} label="Inbox 14" />
          </div>
        </div>
      </div>

      <div className="border-t border-slate-800 px-3.5 py-2 flex items-center justify-between mono text-[10px] tracking-widest uppercase text-slate-500">
        <span>cpu · {(tokensPerMin / 1000).toFixed(1)}k tok/min</span>
        <span>latencia · 297ms</span>
        <span>uptime · 99.97%</span>
      </div>

      {/* shine overlay */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden rounded-2xl">
        <span
          className="absolute top-0 bottom-0 w-1/3"
          style={{
            background: 'linear-gradient(90deg, transparent, rgba(16,185,129,0.06), transparent)',
            animation: 'shine 6s linear infinite',
          }}
        />
      </div>
    </div>
  )
}


const LIVE_ROWS = [
  { t: '14:02:11', text: 'agent · cerró deal · Acme · $4.8k',                            tag: 'WIN',  win: true  },
  { t: '14:02:09', text: 'cua · sandbox-2 · publicó listing #7 en Mercado Libre',         tag: 'CUA',  win: false },
  { t: '14:02:02', text: 'recovery · 3 carritos · WhatsApp enviado',                      tag: 'RCVR', win: false },
  { t: '14:01:48', text: 'factura E · CAE 75123091 emitida · destino BR',                 tag: 'ARCA', win: true  },
  { t: '14:01:30', text: 'manos libres · "agendá demo martes 11hs" · OK',                 tag: 'VOZ',  win: false },
]


const HudKpi = ({ label, value, emphasize }: { label: string; value: string; emphasize?: boolean }): React.JSX.Element => (
  <div className={`border rounded-md px-3 py-2 ${emphasize ? 'border-emerald-500/40 bg-emerald-500/[0.08]' : 'border-slate-800 bg-slate-900/50'}`}>
    <div className={`text-[18px] font-[700] tabular-nums leading-none ${emphasize ? 'text-emerald-300' : 'text-slate-100'}`}>{value}</div>
    <div className="mono text-[9px] tracking-[0.25em] uppercase text-slate-500 mt-1">{label}</div>
  </div>
)


const HudQuick = ({ icon: Icon, label }: { icon: React.ComponentType<{ className?: string }>; label: string }): React.JSX.Element => (
  <button type="button" className="border border-slate-800 rounded-md px-3 py-2 flex items-center gap-2 hover:bg-slate-900 transition text-left bg-slate-900/40">
    <Icon className="w-3.5 h-3.5 text-slate-400" />
    <span className="text-[11.5px] text-slate-300 truncate">{label}</span>
    <ArrowRight className="w-3 h-3 text-slate-500 ml-auto" />
  </button>
)


/* ────────────────────────────  social proof strip  ───────────────────────── */


const PARTNERS = [
  'WhatsApp Cloud', 'Stripe', 'Shopify', 'Mercado Libre', 'Anthropic', 'Vercel',
  'Cloudflare', 'Twilio', 'Resend', 'Groq', 'Hotmart', 'TikTok Shop',
]


const SocialProofStrip = (): React.JSX.Element => (
  <section className="border-y border-slate-200 bg-white py-8">
    <p className="text-center mono text-[10.5px] tracking-[0.4em] uppercase text-slate-500 mb-5">
      compatible · integrado · funcionando con
    </p>
    <div className="relative overflow-hidden">
      <div className="flex gap-10 whitespace-nowrap" style={{ animation: 'ticker 38s linear infinite', width: '200%' }}>
        {[...PARTNERS, ...PARTNERS].map((p, i) => (
          <span key={`${p}-${i}`} className="mono text-[14px] text-slate-400 hover:text-slate-700 transition shrink-0 inline-flex items-center gap-1.5">
            <span className="w-1 h-1 rounded-full bg-slate-300" /> {p}
          </span>
        ))}
      </div>
      <div className="absolute inset-y-0 left-0 w-24 bg-gradient-to-r from-white to-transparent" />
      <div className="absolute inset-y-0 right-0 w-24 bg-gradient-to-l from-white to-transparent" />
    </div>
  </section>
)


/* ────────────────────────────  benefits  ───────────────────────── */


const BENEFITS = [
  {
    title: 'Ahorrá 10 horas por semana',
    body: 'SellIA responde, agenda y factura mientras vos atendés lo importante. No más copiar y pegar mensajes.',
    icon: Clock,
  },
  {
    title: 'Vendé 24/7 sin contratar',
    body: 'Trabaja a las 3 AM cuando tu cliente está mirando WhatsApp. Cero salario, cero ausentismo.',
    icon: TrendingUp,
  },
  {
    title: 'Cerrá deals que se enfriaban',
    body: 'El recovery lab persigue cada lead, recupera carritos abandonados y suma 18% al revenue mensual avg.',
    icon: Zap,
  },
  {
    title: 'Tranquilidad fiscal real',
    body: 'Factura A/B/C/E ARCA · SAT · DIAN · OSS automático. Compliance multi-país sin estudio contable extra.',
    icon: ShieldCheck,
  },
]


const BenefitsGrid = (): React.JSX.Element => (
  <section className="py-24 px-5 sm:px-6">
    <div className="max-w-5xl mx-auto">
      <SectionTitle kicker="por qué SellIA" title="No es otra herramienta más." sub="Es 10 horas de vuelta a tu semana. Y un vendedor que nunca se rinde." />
      <motion.div
        initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-60px' }} variants={StaggerContainer}
        className="grid grid-cols-1 md:grid-cols-2 gap-4"
      >
        {BENEFITS.map((b) => (
          <motion.article key={b.title} variants={StaggerItem}
            className="rounded-2xl bg-white border border-slate-200 p-7 hover:border-emerald-300 hover:shadow-lg hover:shadow-emerald-500/5 transition"
          >
            <span className="inline-flex w-11 h-11 rounded-xl bg-emerald-50 text-emerald-600 items-center justify-center">
              <b.icon className="w-5 h-5" />
            </span>
            <h3 className="mt-5 text-[20px] font-extrabold tracking-tight text-slate-900">{b.title}</h3>
            <p className="mt-2 text-[14px] text-slate-600 leading-relaxed">{b.body}</p>
          </motion.article>
        ))}
      </motion.div>
    </div>
  </section>
)


/* ────────────────────────────  product preview  ───────────────────────── */


const ProductPreview = (): React.JSX.Element => (
  <section className="py-24 px-5 sm:px-6 bg-white border-y border-slate-200">
    <div className="max-w-5xl mx-auto">
      <SectionTitle kicker="cómo opera" title="Una conversación. Un agente. Una venta." sub="SellIA entiende intención, hace las preguntas correctas y agenda · 24/7 en cualquier canal." />
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.1fr] gap-10 items-center">
        <ul className="space-y-3">
          {[
            { t: 'Memoria persistente por cliente',     d: 'Recuerda cada conversación. Nunca empieza de cero.' },
            { t: 'Detección de intención + objeciones', d: 'Sabe cuándo es un curioso, un buscador o un comprador caliente.' },
            { t: 'Hand-off humano solo cuando hace falta', d: 'Saltás cuando importa. El resto del tiempo, ganás tiempo.' },
            { t: 'Métricas claras y exportables',        d: 'Pipeline, conversión, CAC, MRR. Sin BIs externos.' },
          ].map((b) => (
            <li key={b.t} className="flex items-start gap-3 p-3.5 rounded-xl hover:bg-slate-50 transition">
              <span className="mt-0.5 inline-flex w-6 h-6 rounded-full bg-emerald-500 text-white items-center justify-center shrink-0">
                <Check className="w-3.5 h-3.5" />
              </span>
              <div>
                <p className="text-[14px] font-semibold text-slate-900">{b.t}</p>
                <p className="text-[13px] text-slate-600">{b.d}</p>
              </div>
            </li>
          ))}
        </ul>

        <ChatPreview />
      </div>

      <div className="mt-12 flex justify-center">
        <a href="#signup" className="inline-flex items-center gap-2 px-6 py-3.5 rounded-2xl bg-emerald-500 hover:bg-emerald-600 text-white text-[14px] font-bold shadow-xl shadow-emerald-500/30 hover:scale-105 transition active:scale-100">
          Probar gratis ahora <ArrowRight className="w-4 h-4" />
        </a>
      </div>
    </div>
  </section>
)


const ChatPreview = (): React.JSX.Element => {
  const [step, setStep] = useState<number>(0)
  useEffect(() => {
    const id = window.setInterval(() => setStep((s) => (s + 1) % DEMO_MSGS.length), 1900)
    return () => window.clearInterval(id)
  }, [])
  return (
    <div className="rounded-2xl bg-white border border-slate-200 shadow-xl shadow-slate-900/5 overflow-hidden">
      <div className="flex items-center gap-2 px-3.5 py-2.5 bg-slate-50 border-b border-slate-200">
        <span className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]/70" />
        <span className="w-2.5 h-2.5 rounded-full bg-[#febc2e]/70" />
        <span className="w-2.5 h-2.5 rounded-full bg-[#28c840]/70" />
        <div className="mx-auto mono text-[10px] tracking-widest uppercase text-slate-500">
          whatsapp business · live
        </div>
        <span className="relative w-2 h-2 ml-auto">
          <span className="absolute inset-0 rounded-full bg-emerald-400 animate-ping" />
          <span className="absolute inset-0 rounded-full bg-emerald-500" />
        </span>
      </div>
      <div className="p-4 space-y-3 min-h-[340px] bg-slate-50/50">
        {DEMO_MSGS.slice(0, step + 1).map((m, i) => <Bubble key={i} {...m} />)}
        {step < DEMO_MSGS.length - 1 && (
          <div className="flex gap-2 items-center">
            <span className="w-7 h-7 rounded-full bg-emerald-500 text-white flex items-center justify-center text-[10px] font-bold">SA</span>
            <span className="px-3 py-2 rounded-2xl rounded-tl-sm bg-white border border-slate-200 inline-flex gap-1">
              <Dot delay="0s" /><Dot delay="0.15s" /><Dot delay="0.3s" />
            </span>
          </div>
        )}
      </div>
    </div>
  )
}


const DEMO_MSGS: Array<{ from: 'user' | 'bot'; text: string }> = [
  { from: 'user', text: '¿Hacen cursos para consultoras?' },
  { from: 'bot',  text: 'Sí, hay 3 programas: Acelerador (4 sem), Mastermind (12 sem) y 1-on-1. ¿Cuál es tu objetivo principal este trimestre?' },
  { from: 'user', text: 'Necesito más leads orgánicos.' },
  { from: 'bot',  text: 'Acelerador es ideal. Arranca el 5 de junio · USD 890 · 8 sesiones + comunidad. ¿Te agendo 15 min con un asesor mañana 11hs?' },
  { from: 'user', text: '✅ Dale.' },
]


const Bubble = ({ from, text }: { from: 'user' | 'bot'; text: string }): React.JSX.Element => (
  <div className={`flex gap-2 ${from === 'bot' ? '' : 'justify-end'}`}>
    {from === 'bot' && <span className="w-7 h-7 rounded-full bg-emerald-500 text-white flex items-center justify-center text-[10px] font-bold">SA</span>}
    <span className={`px-3.5 py-2 rounded-2xl text-[12.5px] max-w-[78%] leading-relaxed ${
      from === 'bot' ? 'bg-white border border-slate-200 text-slate-800 rounded-tl-sm shadow-sm' : 'bg-blue-600 text-white rounded-tr-sm shadow'
    }`}>
      {text}
    </span>
    {from === 'user' && <span className="w-7 h-7 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center text-[10px] font-bold">U</span>}
  </div>
)


const Dot = ({ delay }: { delay: string }): React.JSX.Element => (
  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 inline-block" style={{ animation: 'pulse-dot 1.2s ease-in-out infinite', animationDelay: delay }} />
)


/* ────────────────────────────  numbers (animated counters)  ───────────────────────── */


const NUMS = [
  { v: 1847, suf: '+',  label: 'negocios usando SellIA' },
  { v: 24,   suf: '/7', label: 'agentes despiertos' },
  { v: 42,   suf: '%',  label: 'conversión avg' },
  { v: 18,   suf: '%',  label: 'revenue recuperado' },
]


const NumbersBlock = (): React.JSX.Element => (
  <section className="py-20 px-5 sm:px-6">
    <div className="max-w-5xl mx-auto grid grid-cols-2 lg:grid-cols-4 gap-px rounded-2xl overflow-hidden border border-slate-200 bg-slate-200/70">
      {NUMS.map((n, i) => <NumberCell key={n.label} n={n} highlight={i === 0} />)}
    </div>
  </section>
)


const NumberCell = ({ n, highlight }: { n: typeof NUMS[number]; highlight?: boolean }): React.JSX.Element => {
  const cur = useCountUp(n.v, 1600)
  return (
    <div className={`px-6 py-10 text-center bg-white ${highlight ? 'bg-emerald-50/60' : ''}`}>
      <div className={`text-[44px] sm:text-[54px] font-extrabold leading-none tracking-tight ${highlight ? 'text-emerald-600' : 'text-slate-900'}`}>
        {Math.round(cur).toLocaleString('es-AR')}{n.suf}
      </div>
      <div className="mt-3 mono text-[10px] tracking-[0.3em] uppercase text-slate-500">{n.label}</div>
    </div>
  )
}


/* ────────────────────────────  testimonials grid  ───────────────────────── */


const TESTIMONIALS = [
  {
    name: 'Martín Ruiz',     role: 'CEO · Agencia Digital',     avatar: 'MR', color: 'bg-emerald-500',
    q: 'Pasamos de 200 mensajes por día a un agente que cualifica solo. Conversión +40% en 6 semanas.',
  },
  {
    name: 'Lucía Gómez',     role: 'Fundadora · E-commerce',    avatar: 'LG', color: 'bg-blue-600',
    q: 'El recovery lab nos trajo USD 15.000 en carritos abandonados el primer mes. Pagué el Pro 30 veces.',
  },
  {
    name: 'Diego Saavedra',  role: 'Consultor de ventas',       avatar: 'DS', color: 'bg-orange-500',
    q: 'Consulto con Hormozi AI antes de cada propuesta. Como tener al mentor en el bolsillo.',
  },
  {
    name: 'Sofía Paz',       role: 'Owner · Veterinaria',       avatar: 'SP', color: 'bg-rose-500',
    q: 'Manos libres mientras atiendo. SellIA agenda turnos por WhatsApp y yo ni toco el teléfono.',
  },
  {
    name: 'Javier López',    role: 'Founder · SaaS B2B',        avatar: 'JL', color: 'bg-purple-600',
    q: 'Bajé el CAC un 38%. El sistema responde leads en 12 segundos. Ya no pierdo tickets calientes.',
  },
  {
    name: 'Camila Torres',   role: 'Owner · Restaurante',       avatar: 'CT', color: 'bg-amber-500',
    q: 'Reservas por WhatsApp, agenda automática, facturación CAE. Despedí el "gestor administrativo".',
  },
]


const Testimonials = (): React.JSX.Element => (
  <section className="py-24 px-5 sm:px-6 bg-white border-y border-slate-200">
    <div className="max-w-6xl mx-auto">
      <SectionTitle kicker="historias reales" title="Vendedores que ahora trabajan menos." sub="Lo que dicen los que ya cobraron con SellIA esta semana." />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {TESTIMONIALS.map((t, i) => (
          <motion.article
            key={t.name}
            initial={{ opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.5, delay: i * 0.05 }}
            className="rounded-2xl bg-slate-50 border border-slate-200 p-6 flex flex-col hover:shadow-lg hover:scale-[1.01] transition"
          >
            <div className="flex gap-0.5 mb-4">
              {Array.from({ length: 5 }).map((_, j) => <Star key={j} className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />)}
            </div>
            <p className="text-[14.5px] leading-relaxed text-slate-800 flex-1">"{t.q}"</p>
            <div className="mt-5 pt-4 border-t border-slate-200 flex items-center gap-3">
              <span className={`w-10 h-10 rounded-full ${t.color} text-white flex items-center justify-center font-bold text-[13px]`}>{t.avatar}</span>
              <div className="leading-tight">
                <div className="text-[13px] font-semibold text-slate-900">{t.name}</div>
                <div className="text-[11.5px] text-slate-500">{t.role}</div>
              </div>
            </div>
          </motion.article>
        ))}
      </div>
    </div>
  </section>
)


/* ────────────────────────────  security banner  ───────────────────────── */


const SecurityBanner = (): React.JSX.Element => (
  <section className="py-16 px-5 sm:px-6">
    <div className="max-w-5xl mx-auto rounded-2xl bg-slate-900 text-white p-8 sm:p-12 flex flex-col md:flex-row items-center gap-8 shadow-2xl shadow-slate-900/10 overflow-hidden relative">
      <div className="absolute -top-20 -right-20 w-72 h-72 rounded-full bg-emerald-500/20 blur-3xl pointer-events-none" />
      <div className="relative shrink-0 inline-flex w-16 h-16 rounded-2xl bg-emerald-500/15 border border-emerald-500/30 items-center justify-center">
        <ShieldCheck className="w-7 h-7 text-emerald-400" />
      </div>
      <div className="relative flex-1">
        <h3 className="text-[24px] font-extrabold tracking-tight">Tus datos están blindados.</h3>
        <p className="mt-1.5 text-[14px] text-slate-300 leading-relaxed">
          Multi-tenant aislado con Postgres Row-Level Security · JWT bcrypt · Fernet encryption · audit logs inmutables · SOC2-ready · GDPR-aligned.
        </p>
      </div>
      <a href="#signup" className="relative inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-[13px] font-bold shadow-lg shadow-emerald-500/40 hover:scale-105 transition active:scale-100">
        Empezar protegido <ArrowRight className="w-3.5 h-3.5" />
      </a>
    </div>
  </section>
)


/* ────────────────────────────  pricing  ───────────────────────── */


const PLANS = [
  { name: 'Free',       price: '$0',     cad: '/mes', desc: 'Probar', popular: false,
    feats: ['1 agente', '1 canal', '50 conv/mes', 'Soporte email'] },
  { name: 'Pro',        price: '$49',    cad: '/mes', desc: 'Emprendedores y PyMEs', popular: true,
    feats: ['5 agentes', '14 canales', 'Conv ilimitadas', 'Computer Use · 3 sandboxes', 'Manos libres · 12 idiomas', 'Workflows + automatizaciones', 'Soporte prioritario'] },
  { name: 'Enterprise', price: 'Custom', cad: '',     desc: 'Equipos · operaciones grandes', popular: false,
    feats: ['Agentes ilimitados', 'API · SLA', 'Onboarding dedicado', 'Multi-tenant + RBAC', 'Custom integrations', 'Audit · SSO'] },
]


const Pricing = (): React.JSX.Element => (
  <section className="py-24 px-5 sm:px-6">
    <div className="max-w-5xl mx-auto">
      <SectionTitle kicker="precios honestos" title="Gratis para arrancar. Justo cuando escalás." sub="Sin tarjeta de crédito para empezar. Sin sorpresas." />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {PLANS.map((p) => (
          <motion.article
            key={p.name}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.5 }}
            className={`relative rounded-2xl p-7 flex flex-col bg-white border ${p.popular ? 'border-emerald-400 shadow-2xl shadow-emerald-500/15 scale-[1.02]' : 'border-slate-200'}`}
          >
            {p.popular && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full text-[10px] mono tracking-[0.3em] uppercase text-white bg-emerald-500 shadow-lg shadow-emerald-500/30">
                el más elegido
              </span>
            )}
            <div className="flex items-baseline justify-between">
              <span className="mono text-[10px] tracking-[0.3em] uppercase text-slate-500">{p.name}</span>
              <span className="text-[11px] mono tracking-widest uppercase text-slate-400">{p.desc}</span>
            </div>
            <div className="mt-3 text-[48px] font-extrabold leading-none tracking-tight text-slate-900">
              {p.price}<span className="text-[14px] text-slate-400 font-normal">{p.cad}</span>
            </div>
            <ul className="mt-6 space-y-2 flex-1">
              {p.feats.map((f) => (
                <li key={f} className="flex items-center gap-2 text-[13.5px] text-slate-700">
                  <Check className="w-4 h-4 text-emerald-500 shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
            <a
              href="#signup"
              className={`mt-6 inline-flex items-center justify-center gap-1.5 px-4 py-3 rounded-xl text-[13px] font-bold transition active:scale-100 ${
                p.popular
                  ? 'bg-emerald-500 hover:bg-emerald-600 text-white shadow-lg shadow-emerald-500/30 hover:scale-105'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-900 hover:scale-105'
              }`}
            >
              {p.popular ? 'Empezar Pro' : p.name === 'Free' ? 'Probar gratis' : 'Contactar ventas'}
              <ArrowRight className="w-3.5 h-3.5" />
            </a>
          </motion.article>
        ))}
      </div>
    </div>
  </section>
)


/* ────────────────────────────  FAQ collapsible  ───────────────────────── */


const QUESTIONS = [
  { q: '¿Necesito saber programar?',
    a: 'No. Tenemos presets por industria + onboarding asistido en 5 min. Si querés extender, hay API REST.' },
  { q: '¿Qué pasa con mis datos?',
    a: 'Multi-tenant aislado con Postgres Row-Level Security. JWT bcrypt cost 12, secrets cifrados con Fernet, audit logs inmutables. SOC2-ready, GDPR-aligned.' },
  { q: '¿En cuánto tiempo veo resultados?',
    a: 'Primer mensaje atendido por SellIA en menos de 1 hora. Conversiones medibles en 7–14 días. Recovery lab activo desde el día 1.' },
  { q: '¿Puede operar mi navegador?',
    a: 'Sí. Anthropic Computer Use (claude-sonnet-4-5, beta computer-use-2025-01-24) en sandbox aislado. 3 sandboxes simultáneos en Pro.' },
  { q: '¿Cómo cancelo?',
    a: 'Un click desde tu panel. Exportás todo tu historial. Cero lock-in. Sin preguntas, sin retención forzada.' },
  { q: '¿Funciona con mis herramientas?',
    a: 'WhatsApp Cloud, Instagram, TikTok, LinkedIn, Email, Stripe, Mercado Pago, Shopify, Mercado Libre, Amazon, Hotmart, AFIP/ARCA, SAT, DIAN y más.' },
  { q: '¿Cobra facturación AFIP automáticamente?',
    a: 'Sí. ARCA: Factura A/B/C/E, padrón, monotributo, libro IVA, COVE, DJVE, certificado de origen MERCOSUR/ALADI/SGP/CAN.' },
  { q: '¿Hay soporte humano?',
    a: 'Sí. Email en Free. Prioritario (1h) en Pro. Onboarding dedicado en Enterprise.' },
]


const FAQ = (): React.JSX.Element => {
  const [open, setOpen] = useState<number | null>(0)
  return (
    <section className="py-24 px-5 sm:px-6 bg-white border-t border-slate-200">
      <div className="max-w-3xl mx-auto">
        <SectionTitle kicker="preguntas frecuentes" title="Las dudas que todos tienen antes de empezar." />
        <div className="space-y-2">
          {QUESTIONS.map((qa, i) => {
            const isOpen = open === i
            return (
              <div
                key={qa.q}
                className={`rounded-xl border transition ${isOpen ? 'border-emerald-400 bg-emerald-50/50 shadow-md' : 'border-slate-200 bg-slate-50 hover:border-slate-300'}`}
              >
                <button
                  type="button"
                  onClick={() => setOpen(isOpen ? null : i)}
                  className="w-full flex items-center justify-between gap-4 px-5 py-4 text-left"
                  aria-expanded={isOpen}
                >
                  <span className="text-[14.5px] font-semibold text-slate-900">{qa.q}</span>
                  <span className={`w-8 h-8 rounded-full flex items-center justify-center transition ${isOpen ? 'bg-emerald-500 text-white' : 'bg-white border border-slate-200 text-slate-500'}`}>
                    <Plus className={`w-3.5 h-3.5 transition-transform ${isOpen ? 'rotate-45' : ''}`} />
                  </span>
                </button>
                <div className="overflow-hidden transition-all" style={{ maxHeight: isOpen ? '260px' : '0px' }}>
                  <p className="px-5 pb-5 text-[13.5px] text-slate-600 leading-relaxed">{qa.a}</p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}


/* ────────────────────────────  final CTA  ───────────────────────── */


const FinalCTA = (): React.JSX.Element => (
  <section className="py-24 px-5 sm:px-6">
    <div className="max-w-4xl mx-auto relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 to-slate-800 text-white p-10 sm:p-16 text-center shadow-2xl">
      <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-emerald-500/30 blur-[100px] pointer-events-none" />
      <div className="absolute inset-0 opacity-[0.04]" style={{
        backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.6) 1px, transparent 1px)',
        backgroundSize: '20px 20px',
      }} />
      <div className="relative">
        <Sparkles className="w-5 h-5 text-emerald-400 mx-auto mb-3" />
        <h2 className="display text-[clamp(2rem,5vw,3.6rem)] leading-tight">
          Empezá a vender mientras{' '}
          <span className="text-emerald-400">leés esto.</span>
        </h2>
        <p className="mt-5 text-[15px] text-slate-300 max-w-xl mx-auto leading-relaxed">
          5 minutos para configurar. Sin tarjeta. 1,847 negocios ya están vendiendo con SellIA esta semana.
        </p>
        <a
          href="#signup"
          className="mt-8 inline-flex items-center gap-2 px-7 py-4 rounded-2xl bg-emerald-500 hover:bg-emerald-600 text-white text-[15px] font-bold shadow-2xl shadow-emerald-500/40 hover:scale-105 transition active:scale-100"
        >
          Comenzar gratis ahora <ArrowRight className="w-4 h-4" />
        </a>
        <p className="mt-4 text-[11.5px] text-slate-400">Sin tarjeta · sin compromiso · cancelás cuando quieras</p>
      </div>
    </div>
  </section>
)


/* ────────────────────────────  footer  ───────────────────────── */


const Footer = (): React.JSX.Element => (
  <footer className="border-t border-slate-200 bg-white px-5 sm:px-6 py-10 mt-8">
    <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
      <div className="flex items-center gap-2.5">
        <Logomark />
        <span className="font-extrabold tracking-tight text-slate-900">SellIA</span>
        <span className="text-[12px] text-slate-500">· Revenue OS · LATAM</span>
      </div>
      <p className="mono text-[10.5px] tracking-[0.3em] uppercase text-slate-400">
        © {new Date().getFullYear()} sellia · all rights reserved
      </p>
    </div>
  </footer>
)


/* ────────────────────────────  mobile bottom CTA  ───────────────────────── */


const MobileBottomCTA = (): React.JSX.Element => (
  <div className="fixed bottom-3 left-3 right-3 z-40 md:hidden">
    <a
      href="#signup"
      className="flex items-center justify-center gap-2 w-full px-5 py-4 rounded-2xl bg-emerald-500 text-white text-[14.5px] font-bold shadow-2xl shadow-emerald-500/40 hover:scale-105 transition active:scale-100"
    >
      Comenzar gratis <ArrowRight className="w-4 h-4" />
    </a>
  </div>
)


/* ────────────────────────────  section title helper  ───────────────────────── */


const SectionTitle = ({
  kicker, title, sub,
}: { kicker: string; title: string; sub?: string }): React.JSX.Element => (
  <div className="text-center mb-12 max-w-3xl mx-auto">
    <div className="mono text-[10.5px] tracking-[0.4em] uppercase text-emerald-600 mb-3">{kicker}</div>
    <h2 className="display text-[clamp(1.9rem,4.2vw,3.3rem)] leading-[1.05] text-slate-900">{title}</h2>
    {sub && <p className="mt-4 text-[15.5px] text-slate-600 leading-relaxed">{sub}</p>}
  </div>
)
