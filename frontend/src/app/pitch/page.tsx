'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import Logo from '@/components/Logo'
import {
  Bot, Zap, Shield, Globe, MessageCircle, TrendingUp,
  ArrowRight, Check, X, Sparkles, BarChart3,
  Layers, Star, Cpu, Phone, Mail, Camera as Instagram, ShoppingBag,
  Lock, Headphones, Clock, ChevronDown, Workflow, Palette,
  Smartphone, Rocket, Award, HeartHandshake, BrainCircuit,
  Menu
} from 'lucide-react'

/* ============================================================
   PITCH — SellIA Presentation (Lovable-grade UX/UI)
   ============================================================ */

const plans = [
  {
    name: 'Free',
    emoji: '🌱',
    tag: 'Para empezar',
    desc: 'Ideal para probar el potencial de la IA en tus ventas sin gastar un centavo.',
    monthly: 0,
    yearly: 0,
    features: [
      { text: '100 conversaciones/mes', included: true },
      { text: '2 canales', included: true },
      { text: '20 productos en catálogo', included: true },
      { text: '1 agente IA', included: true },
      { text: '500MB almacenamiento', included: true },
      { text: '5.000 tokens IA/mes', included: true },
      { text: 'Dashboard de métricas', included: true },
      { text: 'Soporte por email', included: false },
      { text: 'API propia', included: false },
      { text: 'Agentes personalizados', included: false },
    ],
    cta: 'Empezar gratis',
    popular: false,
    color: 'from-emerald-500/20 to-teal-500/20',
    accent: 'text-emerald-400',
  },
  {
    name: 'Starter',
    emoji: '🚀',
    tag: 'Más popular',
    desc: 'Perfecto para emprendedores y pequeños negocios que quieren vender sin límites.',
    monthly: 15,
    yearly: 12,
    features: [
      { text: '1.000 conversaciones/mes', included: true },
      { text: '5 canales', included: true },
      { text: '100 productos en catálogo', included: true },
      { text: '2 agentes IA', included: true },
      { text: '2GB almacenamiento', included: true },
      { text: '50.000 tokens IA/mes', included: true },
      { text: 'Dashboard avanzado', included: true },
      { text: 'Soporte prioritario', included: true },
      { text: 'API propia', included: false },
      { text: 'Agentes personalizados', included: false },
    ],
    cta: 'Elegir Starter',
    popular: true,
    color: 'from-brand-orange/20 to-amber-500/20',
    accent: 'text-brand-orange',
  },
  {
    name: 'Pro',
    emoji: '💎',
    tag: 'Para escalar',
    desc: 'Diseñado para negocios en crecimiento que necesitan potencia y flexibilidad total.',
    monthly: 49,
    yearly: 39,
    features: [
      { text: '5.000 conversaciones/mes', included: true },
      { text: 'Canales ilimitados', included: true },
      { text: 'Productos ilimitados', included: true },
      { text: '4 agentes IA', included: true },
      { text: '10GB almacenamiento', included: true },
      { text: '200.000 tokens IA/mes', included: true },
      { text: 'Dashboard + reportes', included: true },
      { text: 'Soporte 24/7', included: true },
      { text: 'API propia', included: true },
      { text: 'Agentes personalizados', included: false },
    ],
    cta: 'Elegir Pro',
    popular: false,
    color: 'from-brand-violet/20 to-fuchsia-500/20',
    accent: 'text-brand-violet',
  },
  {
    name: 'Enterprise',
    emoji: '🏢',
    tag: 'A tu medida',
    desc: 'Para empresas que necesitan control total, white-label y soporte dedicado.',
    monthly: 199,
    yearly: 159,
    features: [
      { text: 'Conversaciones ilimitadas', included: true },
      { text: 'Canales ilimitados', included: true },
      { text: 'Productos ilimitados', included: true },
      { text: 'Agentes personalizados', included: true },
      { text: 'Almacenamiento ilimitado', included: true },
      { text: 'Tokens ilimitados', included: true },
      { text: 'Reportes ejecutivos', included: true },
      { text: 'Soporte dedicado', included: true },
      { text: 'API + Webhooks', included: true },
      { text: 'White-label completo', included: true },
    ],
    cta: 'Contactar ventas',
    popular: false,
    color: 'from-blue-500/20 to-cyan-500/20',
    accent: 'text-blue-400',
  },
]

const bentoFeatures = [
  {
    icon: Bot,
    emoji: '🤖',
    title: '4 Agentes Especializados',
    desc: 'Un equipo de IA completo que trabaja en cadena: Captador, Cualificador, Vendedor y Post-Venta. Cada uno con personalidad y prompts adaptados a tu negocio.',
    size: 'large',
    color: 'from-brand-orange/15 to-brand-violet/15',
    iconBg: 'bg-brand-orange/20',
    iconColor: 'text-brand-orange',
  },
  {
    icon: Globe,
    emoji: '🌐',
    title: 'Multi-Plataforma',
    desc: 'WhatsApp, Instagram, Email, MercadoLibre, Amazon, LinkedIn y más. Un solo inbox para dominarlos a todos.',
    size: 'small',
    color: 'from-brand-teal/15 to-emerald-500/15',
    iconBg: 'bg-brand-teal/20',
    iconColor: 'text-brand-teal',
  },
  {
    icon: Zap,
    emoji: '⚡',
    title: 'Respuesta < 2 min',
    desc: 'Tus clientes nunca esperan. La IA responde al instante, las 24 horas, los 7 días de la semana.',
    size: 'small',
    color: 'from-amber-500/15 to-orange-500/15',
    iconBg: 'bg-amber-500/20',
    iconColor: 'text-amber-400',
  },
  {
    icon: BarChart3,
    emoji: '📊',
    title: 'Métricas que Importan',
    desc: 'Conversiones, ingresos, canales más rentables, tasa de respuesta y ROI. Todo en un dashboard intuitivo que entendés de un vistazo. Exportá reportes en PDF para tus reuniones.',
    size: 'large',
    color: 'from-brand-violet/15 to-fuchsia-500/15',
    iconBg: 'bg-brand-violet/20',
    iconColor: 'text-brand-violet',
  },
  {
    icon: Shield,
    emoji: '🔒',
    title: 'Seguro por Diseño',
    desc: 'Encriptación end-to-end. Tus datos nunca entrenan modelos de terceros. Cumplimos con GDPR.',
    size: 'small',
    color: 'from-blue-500/15 to-cyan-500/15',
    iconBg: 'bg-blue-500/20',
    iconColor: 'text-blue-400',
  },
  {
    icon: BrainCircuit,
    emoji: '🧠',
    title: 'Tu Propia API Key',
    desc: 'Conectá tu OpenAI o Anthropic y mantené el control total de los costos y la calidad de las respuestas. Sin intermediarios.',
    size: 'small',
    color: 'from-rose-500/15 to-pink-500/15',
    iconBg: 'bg-rose-500/20',
    iconColor: 'text-rose-400',
  },
]

const channels = [
  { icon: Phone, name: 'WhatsApp', emoji: '💬', color: 'bg-green-500/20 text-green-400' },
  { icon: Mail, name: 'Email', emoji: '📧', color: 'bg-blue-500/20 text-blue-400' },
  { icon: Instagram, name: 'Instagram', emoji: '📸', color: 'bg-pink-500/20 text-pink-400' },
  { icon: ShoppingBag, name: 'MercadoLibre', emoji: '🛒', color: 'bg-yellow-500/20 text-yellow-400' },
  { icon: Globe, name: 'Web Chat', emoji: '💻', color: 'bg-brand-orange/20 text-brand-orange' },
  { icon: Smartphone, name: 'SMS', emoji: '📱', color: 'bg-brand-violet/20 text-brand-violet' },
]

const testimonials = [
  {
    name: 'María González',
    role: 'Dueña de tienda de ropa',
    text: 'Pasé de responder manualmente 80 mensajes diarios a que la IA lo haga sola. Mis ventas subieron un 40% en el primer mes. ¡Increíble!',
    avatar: 'M',
    color: 'from-brand-orange to-rose-500',
  },
  {
    name: 'Carlos Rodríguez',
    role: 'CEO de agencia de marketing',
    text: 'Le ofrecemos SellIA a nuestros clientes como valor agregado. El white-label es perfecto para nuestra marca. El soporte es excepcional.',
    avatar: 'C',
    color: 'from-brand-violet to-indigo-500',
  },
  {
    name: 'Lucía Martínez',
    role: 'Consultora de servicios',
    text: 'El agente cualifica leads antes de que yo intervenga. Solo hablo con clientes que realmente van a comprar. Me ahorra horas todos los días.',
    avatar: 'L',
    color: 'from-brand-teal to-emerald-500',
  },
]

const faqs = [
  {
    q: '¿Necesito saber de programación para usar SellIA?',
    a: '¡Para nada! SellIA está diseñado para emprendedores, no para desarrolladores. Configurás tu negocio con clicks, conectás tus canales en segundos y los agentes empiezan a vender solos.',
  },
  {
    q: '¿Puedo usar mi propia API key de OpenAI?',
    a: 'Sí, y te lo recomendamos. Podés conectar tu API key de OpenAI o Anthropic y pagar directamente a ellos por el uso. SellIA solo cobra por la plataforma, no por los tokens de IA.',
  },
  {
    q: '¿Qué pasa si supero los límites de mi plan?',
    a: 'Te avisamos con anticipación cuando te acerques a los límites. Nunca cortamos tu servicio de golpe. Podés upgradear en un click o esperar al siguiente ciclo.',
  },
  {
    q: '¿Funciona para cualquier tipo de negocio?',
    a: 'Sí. SellIA soporta servicios, bienes físicos, productos digitales y negocios mixtos. Cada tipo tiene flujos de conversación adaptados específicamente.',
  },
  {
    q: '¿Puedo cancelar cuando quiera?',
    a: 'Por supuesto. Sin contratos de permanencia, sin letra chica. Cancelás cuando querés y conservás tus datos.',
  },
]

/* ---- Components ---- */

function Orb({ x, y, size, color, delay }: { x: string; y: string; size: number; color: string; delay: number }) {
  return (
    <div
      className="absolute rounded-full blur-[120px] pointer-events-none animate-float"
      style={{
        left: x, top: y, width: size, height: size,
        background: color, opacity: 0.3,
        animationDelay: `${delay}s`, animationDuration: `${12 + delay * 4}s`,
      }}
    />
  )
}

function SectionReveal({ children, className = '', delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) { setVisible(true); obs.disconnect() }
    }, { threshold: 0.1 })
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  return (
    <div
      ref={ref}
      className={`transition-all duration-700 ${className}`}
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0) scale(1)' : 'translateY(32px) scale(0.98)',
        transitionDelay: `${delay}ms`,
        transitionTimingFunction: 'cubic-bezier(0.16, 1, 0.3, 1)',
      }}
    >
      {children}
    </div>
  )
}

function PricingToggle({ yearly, onChange }: { yearly: boolean; onChange: (v: boolean) => void }) {
  return (
    <div className="inline-flex items-center gap-1 p-1.5 bg-white/5 backdrop-blur-sm rounded-full border border-white/10">
      <button
        onClick={() => onChange(false)}
        className={`px-5 py-2.5 rounded-full text-sm font-medium transition-all duration-300 ${
          !yearly ? 'bg-white/10 text-white shadow-sm' : 'text-white/30 hover:text-white/60'
        }`}
      >
        Mensual
      </button>
      <button
        onClick={() => onChange(true)}
        className={`px-5 py-2.5 rounded-full text-sm font-medium transition-all duration-300 flex items-center gap-2 ${
          yearly ? 'bg-white/10 text-white shadow-sm' : 'text-white/30 hover:text-white/60'
        }`}
      >
        Anual
        <span className="text-[10px] font-bold bg-brand-teal/20 text-brand-teal px-2 py-0.5 rounded-full border border-brand-teal/20">-20%</span>
      </button>
    </div>
  )
}

function FAQItem({ q, a, i }: { q: string; a: string; i: number }) {
  const [open, setOpen] = useState(false)
  const contentRef = useRef<HTMLDivElement>(null)
  const [height, setHeight] = useState(0)

  useEffect(() => {
    if (contentRef.current) {
      setHeight(contentRef.current.scrollHeight)
    }
  }, [a])

  return (
    <SectionReveal delay={i * 80}>
      <div className="rounded-2xl bg-white/[0.03] border border-white/[0.06] overflow-hidden hover:border-white/10 transition-colors">
        <button
          onClick={() => setOpen(!open)}
          className="w-full flex items-center justify-between p-6 text-left"
        >
          <span className="text-sm font-medium text-white/90 pr-4">{q}</span>
          <ChevronDown className={`w-5 h-5 text-white/40 shrink-0 transition-transform duration-300 ${open ? 'rotate-180' : ''}`} />
        </button>
        <div 
          className="overflow-hidden transition-all duration-300 ease-out"
          style={{ maxHeight: open ? height : 0 }}
        >
          <div ref={contentRef} className="px-6 pb-6">
            <p className="text-sm text-white/50 leading-relaxed">{a}</p>
          </div>
        </div>
      </div>
    </SectionReveal>
  )
}

export default function PitchPage() {
  const [yearly, setYearly] = useState(true)
  const [mounted, setMounted] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => { setMounted(true) }, [])

  return (
    <div className="min-h-screen bg-[#060812] text-white relative overflow-x-hidden">
      {/* ===== Background ===== */}
      <Orb x="-10%" y="-10%" size={600} color="radial-gradient(circle, #FF6B35, transparent)" delay={0} />
      <Orb x="70%" y="40%" size={700} color="radial-gradient(circle, #7C3AED, transparent)" delay={2} />
      <Orb x="30%" y="80%" size={500} color="radial-gradient(circle, #00D4AA, transparent)" delay={4} />
      <Orb x="85%" y="-5%" size={400} color="radial-gradient(circle, #FF6B35, transparent)" delay={1} />

      <div className="absolute inset-0 pointer-events-none opacity-[0.015]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat', backgroundSize: '128px',
        }}
      />

      {/* ===== Header ===== */}
      <header className="fixed top-0 left-0 right-0 z-50">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mt-4 flex items-center justify-between h-14 px-6 rounded-2xl bg-white/5 backdrop-blur-xl border border-white/10">
            <Logo size={32} showText={true} />
            
            {/* Desktop nav */}
            <div className="hidden sm:flex items-center gap-4">
              <a href="#features" className="text-sm text-white/50 hover:text-white transition-colors">Features</a>
              <a href="#pricing" className="text-sm text-white/50 hover:text-white transition-colors">Planes</a>
              <Link href="/login" className="text-sm text-white/70 hover:text-white transition-colors font-medium">Iniciar sesión</Link>
              <Link href="/register" className="inline-flex items-center gap-2 px-4 py-2 bg-white text-brand-night text-sm font-semibold rounded-xl hover:bg-white/90 transition-all active:scale-[0.98]">
                Empezar gratis
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="sm:hidden p-2 rounded-xl hover:bg-white/5 text-white/50 hover:text-white transition-colors"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>

          {/* Mobile menu */}
          {mobileMenuOpen && (
            <div className="sm:hidden mt-2 bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-4 space-y-2 animate-fade-in">
              <a href="#features" onClick={() => setMobileMenuOpen(false)} className="block text-sm text-white/60 hover:text-white py-2 px-3 rounded-xl hover:bg-white/5">Features</a>
              <a href="#pricing" onClick={() => setMobileMenuOpen(false)} className="block text-sm text-white/60 hover:text-white py-2 px-3 rounded-xl hover:bg-white/5">Planes</a>
              <Link href="/login" onClick={() => setMobileMenuOpen(false)} className="block text-sm text-white/60 hover:text-white py-2 px-3 rounded-xl hover:bg-white/5">Iniciar sesión</Link>
              <Link href="/register" onClick={() => setMobileMenuOpen(false)} className="block text-center px-4 py-2.5 bg-brand-orange text-white text-sm font-semibold rounded-xl hover:bg-brand-orange-dark transition-all">
                Empezar gratis
              </Link>
            </div>
          )}
        </div>
      </header>

      {/* ===== HERO ===== */}
      <section className="relative pt-36 pb-20 px-6">
        <div className="max-w-5xl mx-auto text-center">
          <div className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-white/5 border border-white/10 text-sm font-medium text-white/80 mb-8 transition-all duration-700 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
            <Sparkles className="w-4 h-4 text-brand-orange" />
            🤖 Agentes de IA que venden por vos
          </div>

          <h1 className={`heading-xl mb-6 transition-all duration-1000 delay-100 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
            Vende más,
            <br />
            <span className="gradient-text">duerme mejor.</span> 💤
          </h1>

          <p className={`body-lg max-w-2xl mx-auto mb-10 transition-all duration-1000 delay-200 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
            Automatizá todo tu proceso de ventas con un equipo de <strong className="text-white/80">4 agentes de IA</strong> especializados.
            Desde captar el lead hasta coordinar la entrega. Funciona para servicios, bienes y productos digitales. ✨
          </p>

          <div className={`flex items-center justify-center gap-4 mb-16 transition-all duration-1000 delay-300 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
            <Link href="/register" className="inline-flex items-center gap-2 px-8 py-4 bg-brand-orange text-white text-base font-semibold rounded-2xl hover:bg-brand-orange-dark transition-all active:scale-[0.98] shadow-lg shadow-brand-orange/25">
              Crear cuenta gratis 🚀
            </Link>
            <Link href="/login" className="inline-flex items-center gap-2 px-8 py-4 bg-white/5 text-white text-base font-semibold rounded-2xl border border-white/10 hover:bg-white/10 transition-all">
              Ya tengo cuenta
            </Link>
          </div>

          {/* Dashboard mockup */}
          <div className={`relative max-w-5xl mx-auto transition-all duration-1000 delay-500 ${mounted ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-12 scale-95'}`}>
            <div className="relative rounded-[28px] border border-white/10 bg-gradient-to-b from-white/10 to-white/[0.02] backdrop-blur-sm p-2 shadow-2xl shadow-black/50">
              <div className="rounded-[24px] bg-[#0B0F1A] overflow-hidden">
                <div className="flex items-center gap-2 px-6 py-3.5 border-b border-white/5">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-400/70" />
                    <div className="w-3 h-3 rounded-full bg-amber-400/70" />
                    <div className="w-3 h-3 rounded-full bg-green-400/70" />
                  </div>
                  <div className="flex-1 text-center"><span className="text-[11px] text-white/25 font-mono">sellia.app/dashboard</span></div>
                </div>
                <div className="p-6 grid grid-cols-3 gap-4">
                  <div className="col-span-2 space-y-4">
                    <div className="flex gap-3">
                      {[
                        { label: '💬 Conversaciones', val: '1,247', sub: '+12% este mes', color: 'text-brand-orange', bg: 'bg-brand-orange/10' },
                        { label: '📈 Conversión', val: '24.8%', sub: '+3.2% vs mes pasado', color: 'text-brand-teal', bg: 'bg-brand-teal/10' },
                        { label: '💰 Ingresos', val: '$8,420', sub: 'Meta: $10k', color: 'text-brand-violet', bg: 'bg-brand-violet/10' },
                      ].map((s) => (
                        <div key={s.label} className="flex-1 rounded-2xl bg-white/[0.03] border border-white/[0.05] p-4">
                          <p className="text-[10px] text-white/30 mb-1">{s.label}</p>
                          <p className={`text-xl font-bold ${s.color}`}>{s.val}</p>
                          <p className="text-[10px] text-white/25 mt-1">{s.sub}</p>
                        </div>
                      ))}
                    </div>
                    <div className="rounded-2xl bg-white/[0.03] border border-white/[0.05] p-4 h-32 flex items-end gap-1.5">
                      {[40,65,45,80,55,92,70,85,60,95,75,88,72,98].map((h,i) => (
                        <div key={i} className="flex-1 rounded-t-md bg-gradient-to-t from-brand-orange/50 to-brand-orange/10" style={{ height: `${h}%` }} />
                      ))}
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="rounded-2xl bg-white/[0.03] border border-white/[0.05] p-4">
                      <p className="text-[10px] text-white/30 mb-3">🟢 Chat en vivo</p>
                      <div className="space-y-2.5">
                        <div className="flex gap-2">
                          <div className="w-6 h-6 rounded-full bg-brand-orange/20 flex items-center justify-center text-[9px] text-brand-orange font-bold">IA</div>
                          <div className="flex-1 rounded-xl bg-white/5 px-3 py-2"><p className="text-[10px] text-white/50">¡Hola! 👋 ¿En qué puedo ayudarte?</p></div>
                        </div>
                        <div className="flex gap-2 justify-end">
                          <div className="flex-1 rounded-xl bg-brand-orange/10 px-3 py-2"><p className="text-[10px] text-brand-orange/80">Quiero el plan Pro</p></div>
                        </div>
                        <div className="flex gap-2">
                          <div className="w-6 h-6 rounded-full bg-brand-orange/20 flex items-center justify-center text-[9px] text-brand-orange font-bold">IA</div>
                          <div className="flex-1 rounded-xl bg-white/5 px-3 py-2"><p className="text-[10px] text-white/50">¡Perfecto! Te muestro las opciones 🎯</p></div>
                        </div>
                      </div>
                    </div>
                    <div className="rounded-2xl bg-white/[0.03] border border-white/[0.05] p-4">
                      <p className="text-[10px] text-white/30 mb-2">🤖 Agentes activos</p>
                      <div className="flex gap-1.5 flex-wrap">
                        {['Captador','Cualificador','Vendedor','Post-Venta'].map(a => (
                          <span key={a} className="text-[9px] px-2 py-1 rounded-lg bg-brand-teal/10 text-brand-teal border border-brand-teal/20">{a}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 w-2/3 h-20 bg-brand-orange/20 blur-3xl rounded-full pointer-events-none" />
          </div>
        </div>
      </section>

      {/* ===== TRUST BADGES ===== */}
      <section className="py-10 px-6 border-y border-white/5 bg-white/[0.015]">
        <div className="max-w-5xl mx-auto text-center">
          <p className="text-xs text-white/25 uppercase tracking-widest mb-6">Confían en nosotros emprendedores de todo el mundo 🌍</p>
          <div className="flex items-center justify-center gap-10 flex-wrap opacity-30">
            {['Shopify','MercadoLibre','WhatsApp','Stripe','Notion','Slack'].map((brand) => (
              <span key={brand} className="text-sm font-semibold text-white/60">{brand}</span>
            ))}
          </div>
        </div>
      </section>

      {/* ===== STATS ===== */}
      <section className="py-16 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { value: '24/7', label: 'Disponibilidad', emoji: '⏰' },
              { value: '3×', label: 'Más conversión', emoji: '📈' },
              { value: '<2 min', label: 'Tiempo de respuesta', emoji: '⚡' },
              { value: '10+', label: 'Canales integrados', emoji: '🔗' },
            ].map((stat, i) => (
              <SectionReveal key={stat.label} delay={i * 100}>
                <div className="text-center p-6 rounded-3xl bg-white/[0.02] border border-white/[0.05] hover:border-white/10 transition-all">
                  <p className="text-2xl mb-1">{stat.emoji}</p>
                  <p className="text-3xl font-bold text-white">{stat.value}</p>
                  <p className="text-sm text-white/40 mt-1">{stat.label}</p>
                </div>
              </SectionReveal>
            ))}
          </div>
        </div>
      </section>

      {/* ===== FEATURES BENTO ===== */}
      <section id="features" className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <SectionReveal>
            <div className="text-center mb-16">
              <p className="section-title">✨ Características</p>
              <h2 className="heading-lg text-white mb-4">Todo en uno. Nada de más.</h2>
              <p className="body-lg max-w-xl mx-auto">
                Un sistema diseñado para vender, no para configurar. Cada feature está pensada para que ganes más tiempo y dinero.
              </p>
            </div>
          </SectionReveal>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {bentoFeatures.map((f, i) => {
              const Icon = f.icon
              return (
                <SectionReveal key={f.title} delay={i * 100} className={f.size === 'large' ? 'md:col-span-2' : ''}>
                  <div className={`group h-full rounded-[28px] bg-gradient-to-br ${f.color} border border-white/[0.06] p-8 transition-all duration-500 hover:border-white/[0.12] hover:scale-[1.01]`}>
                    <div className="flex items-center gap-3 mb-5">
                      <div className={`w-11 h-11 ${f.iconBg} rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}>
                        <Icon className={`w-5 h-5 ${f.iconColor}`} />
                      </div>
                      <span className="text-lg">{f.emoji}</span>
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-2">{f.title}</h3>
                    <p className="text-sm text-white/45 leading-relaxed">{f.desc}</p>
                  </div>
                </SectionReveal>
              )
            })}
          </div>
        </div>
      </section>

      {/* ===== CHANNELS ===== */}
      <section className="py-20 px-6 border-y border-white/5">
        <div className="max-w-4xl mx-auto">
          <SectionReveal>
            <div className="text-center mb-12">
              <p className="section-title">🔗 Conectá Todo</p>
              <h2 className="heading-lg text-white mb-4">Un solo inbox. Todos tus canales.</h2>
              <p className="body-lg max-w-lg mx-auto">
                Tus clientes te escriben donde quieren. Vos respondés desde un solo lugar. La IA nunca pierde el hilo de la conversación.
              </p>
            </div>
          </SectionReveal>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
            {channels.map((ch, i) => {
              const Icon = ch.icon
              return (
                <SectionReveal key={ch.name} delay={i * 80}>
                  <div className="flex flex-col items-center gap-3 p-6 rounded-2xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.05] hover:border-white/10 transition-all group">
                    <div className={`w-12 h-12 rounded-2xl ${ch.color} flex items-center justify-center group-hover:scale-110 transition-transform`}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <span className="text-lg">{ch.emoji}</span>
                    <span className="text-xs font-medium text-white/60">{ch.name}</span>
                  </div>
                </SectionReveal>
              )
            })}
          </div>
        </div>
      </section>

      {/* ===== HOW IT WORKS ===== */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto">
          <SectionReveal>
            <div className="text-center mb-16">
              <p className="section-title">🛠️ Cómo Funciona</p>
              <h2 className="heading-lg text-white mb-4">Configurá una vez. Vendé para siempre.</h2>
            </div>
          </SectionReveal>

          <div className="space-y-6">
            {[
              { step: '01', emoji: '🏗️', title: 'Creá tu negocio', desc: 'Definí si vendés servicios, bienes físicos o productos digitales. Configurá opciones de entrega, horarios y zonas en minutos. La IA se adapta automáticamente a tu modelo.', icon: Layers },
              { step: '02', emoji: '🔌', title: 'Conectá tus canales', desc: 'WhatsApp, Email, Instagram, MercadoLibre y más. Un solo clic por canal. En menos de 5 minutos todos tus clientes pueden escribirte y la IA responde al instante.', icon: Workflow },
              { step: '03', emoji: '🚀', title: 'Los agentes venden por vos', desc: 'Captan leads, cualifican intereses, cierran ventas y coordinan entregas. Vos solo intervenís cuando querés. El sistema aprende de cada conversación para vender mejor.', icon: Rocket },
            ].map((item, i) => {
              const Icon = item.icon
              return (
                <SectionReveal key={item.step} delay={i * 150}>
                  <div className="flex gap-5 items-start p-7 rounded-3xl bg-white/[0.02] border border-white/[0.05] hover:border-white/10 transition-all">
                    <div className="flex flex-col items-center gap-2">
                      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-orange/20 to-brand-violet/20 flex items-center justify-center shrink-0">
                        <Icon className="w-6 h-6 text-brand-orange" />
                      </div>
                      {i < 2 && <div className="w-px h-8 bg-white/10 hidden sm:block" />}
                    </div>
                    <div className="pt-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs font-mono text-white/20">PASO {item.step}</span>
                        <span className="text-lg">{item.emoji}</span>
                      </div>
                      <h3 className="text-xl font-semibold text-white mb-2">{item.title}</h3>
                      <p className="text-sm text-white/45 leading-relaxed">{item.desc}</p>
                    </div>
                  </div>
                </SectionReveal>
              )
            })}
          </div>
        </div>
      </section>

      {/* ===== AGENTS SHOWCASE ===== */}
      <section className="py-24 px-6 border-y border-white/5 bg-white/[0.01]">
        <div className="max-w-5xl mx-auto">
          <SectionReveal>
            <div className="text-center mb-16">
              <p className="section-title">🤖 Tu Equipo de IA</p>
              <h2 className="heading-lg text-white mb-4">4 agentes. Un solo objetivo: vender.</h2>
              <p className="body-lg max-w-xl mx-auto">
                Cada agente tiene una personalidad y un propósito específico. Trabajan en equipo como los mejores vendedores del mundo.
              </p>
            </div>
          </SectionReveal>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {[
              { emoji: '🎣', name: 'Captador', color: 'from-blue-500/20 to-cyan-500/20', iconColor: 'text-blue-400', desc: 'Atrae leads de todos los canales y los da la bienvenida con personalidad.' },
              { emoji: '🎯', name: 'Cualificador', color: 'from-brand-violet/20 to-fuchsia-500/20', iconColor: 'text-brand-violet', desc: 'Pregunta, entiende y clasifica. Solo pasa adelante a los que realmente compran.' },
              { emoji: '💰', name: 'Vendedor', color: 'from-brand-orange/20 to-amber-500/20', iconColor: 'text-brand-orange', desc: 'Cierra ventas, maneja objeciones y procesa pagos sin intervención humana.' },
              { emoji: '🤝', name: 'Post-Venta', color: 'from-brand-teal/20 to-emerald-500/20', iconColor: 'text-brand-teal', desc: 'Coordina entregas, pide reviews y fideliza para que vuelvan a comprar.' },
            ].map((agent, i) => (
              <SectionReveal key={agent.name} delay={i * 100}>
                <div className={`h-full rounded-3xl bg-gradient-to-b ${agent.color} border border-white/[0.06] p-7 hover:border-white/10 transition-all group`}>
                  <div className="text-4xl mb-4">{agent.emoji}</div>
                  <h3 className={`text-lg font-bold ${agent.iconColor} mb-2`}>{agent.name}</h3>
                  <p className="text-sm text-white/45 leading-relaxed">{agent.desc}</p>
                </div>
              </SectionReveal>
            ))}
          </div>
        </div>
      </section>

      {/* ===== TESTIMONIALS ===== */}
      <section className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <SectionReveal>
            <div className="text-center mb-16">
              <p className="section-title">❤️ Testimonios</p>
              <h2 className="heading-lg text-white mb-4">Lo que dicen quienes ya venden con IA</h2>
            </div>
          </SectionReveal>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {testimonials.map((t, i) => (
              <SectionReveal key={t.name} delay={i * 100}>
                <div className="h-full rounded-3xl bg-white/[0.03] border border-white/[0.06] p-7 hover:bg-white/[0.05] transition-all">
                  <div className="flex gap-1 mb-4">
                    {[1,2,3,4,5].map(s => <Star key={s} className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />)}
                  </div>
                  <p className="text-sm text-white/55 leading-relaxed mb-6">&ldquo;{t.text}&rdquo;</p>
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${t.color} flex items-center justify-center text-sm font-bold text-white`}>
                      {t.avatar}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white">{t.name}</p>
                      <p className="text-xs text-white/35">{t.role}</p>
                    </div>
                  </div>
                </div>
              </SectionReveal>
            ))}
          </div>
        </div>
      </section>

      {/* ===== PRICING ===== */}
      <section id="pricing" className="py-24 px-6 border-y border-white/5 bg-white/[0.01]">
        <div className="max-w-6xl mx-auto">
          <SectionReveal>
            <div className="text-center mb-6">
              <p className="section-title">💳 Planes</p>
              <h2 className="heading-lg text-white mb-4">Elegí el que se ajuste a tu crecimiento</h2>
              <p className="body-lg max-w-lg mx-auto mb-8">
                Empezá gratis. Escalá cuando lo necesites. Sin contratos ni sorpresas.
              </p>
              <PricingToggle yearly={yearly} onChange={setYearly} />
            </div>
          </SectionReveal>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mt-12">
            {plans.map((plan, i) => (
              <SectionReveal key={plan.name} delay={i * 100}>
                <div className={`relative h-full rounded-3xl p-7 transition-all duration-300 ${
                  plan.popular
                    ? `bg-gradient-to-b ${plan.color} border-2 border-brand-orange/30 scale-[1.02]`
                    : 'bg-white/[0.02] border border-white/[0.06] hover:border-white/10'
                }`}>
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3.5 py-1 bg-brand-orange text-white text-[10px] font-bold uppercase tracking-wider rounded-full">
                      ⭐ Más elegido
                    </div>
                  )}

                  <div className="mb-5">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-2xl">{plan.emoji}</span>
                      <span className="text-xs font-medium text-white/40 uppercase tracking-wider">{plan.tag}</span>
                    </div>
                    <h3 className="text-xl font-bold text-white">{plan.name}</h3>
                    <p className="text-xs text-white/35 mt-1.5 leading-relaxed">{plan.desc}</p>
                  </div>

                  <div className="mb-6">
                    <div className="flex items-baseline gap-1">
                      <span className="text-4xl font-bold text-white">${yearly ? plan.yearly : plan.monthly}</span>
                      <span className="text-sm text-white/35">/mes</span>
                    </div>
                    {yearly && plan.monthly > 0 && (
                      <p className="text-xs text-brand-teal mt-1 font-medium">
                        💚 Ahorrás ${(plan.monthly - plan.yearly) * 12}/año
                      </p>
                    )}
                  </div>

                  <ul className="space-y-2.5 mb-8">
                    {plan.features.map(feat => (
                      <li key={feat.text} className="flex items-start gap-2.5">
                        {feat.included ? (
                          <Check className="w-4 h-4 text-brand-teal shrink-0 mt-0.5" />
                        ) : (
                          <X className="w-4 h-4 text-white/15 shrink-0 mt-0.5" />
                        )}
                        <span className={`text-xs ${feat.included ? 'text-white/60' : 'text-white/20'}`}>{feat.text}</span>
                      </li>
                    ))}
                  </ul>

                  <Link href="/register" className={`block w-full text-center py-3 rounded-xl text-sm font-semibold transition-all active:scale-[0.98] ${
                    plan.popular
                      ? 'bg-brand-orange text-white hover:bg-brand-orange-dark shadow-lg shadow-brand-orange/20'
                      : 'bg-white/5 text-white border border-white/10 hover:bg-white/10'
                  }`}>
                    {plan.cta}
                  </Link>
                </div>
              </SectionReveal>
            ))}
          </div>

          <SectionReveal delay={200}>
            <div className="mt-10 text-center">
              <p className="text-sm text-white/25">
                💡 Todos los precios en USD. Podés usar tu propia API key de OpenAI/Anthropic sin costo extra.
              </p>
            </div>
          </SectionReveal>
        </div>
      </section>

      {/* ===== FAQ ===== */}
      <section className="py-24 px-6">
        <div className="max-w-3xl mx-auto">
          <SectionReveal>
            <div className="text-center mb-12">
              <p className="section-title">❓ Preguntas Frecuentes</p>
              <h2 className="heading-lg text-white mb-4">Todo lo que necesitás saber</h2>
            </div>
          </SectionReveal>

          <div className="space-y-3">
            {faqs.map((faq, i) => (
              <FAQItem key={i} q={faq.q} a={faq.a} i={i} />
            ))}
          </div>
        </div>
      </section>

      {/* ===== FINAL CTA ===== */}
      <section className="py-24 px-6 border-t border-white/5">
        <div className="max-w-3xl mx-auto text-center">
          <SectionReveal>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-sm text-white/60 mb-6">
              <HeartHandshake className="w-4 h-4 text-brand-orange" />
              +2,500 emprendedores ya venden con SellIA
            </div>
            <h2 className="text-4xl sm:text-5xl font-bold text-white mb-6 leading-tight">
              ¿Listo para dejar de{' '}
              <span className="gradient-text">perder ventas?</span> 🚀
            </h2>
            <p className="body-lg max-w-lg mx-auto mb-10">
              Creá tu cuenta en menos de 2 minutos. No necesitás tarjeta de crédito para empezar.
            </p>
            <div className="flex items-center justify-center gap-4">
              <Link href="/register" className="inline-flex items-center gap-2 px-8 py-4 bg-brand-orange text-white text-base font-semibold rounded-2xl hover:bg-brand-orange-dark transition-all active:scale-[0.98] shadow-xl shadow-brand-orange/20 animate-pulse-glow">
                Empezar gratis ahora
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <p className="text-xs text-white/20 mt-6">
              ⚡ Configuración en 2 minutos · Sin tarjeta · Cancelá cuando quieras
            </p>
          </SectionReveal>
        </div>
      </section>

      {/* ===== Mobile Sticky CTA ===== */}
      <div className="fixed bottom-0 left-0 right-0 z-40 p-4 bg-gradient-to-t from-[#060812] via-[#060812] to-transparent sm:hidden">
        <Link href="/register" className="flex items-center justify-center gap-2 w-full px-6 py-3.5 bg-brand-orange text-white text-sm font-bold rounded-2xl hover:bg-brand-orange-dark transition-all active:scale-[0.98] shadow-lg shadow-brand-orange/25">
          Empezar gratis ahora
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* ===== FOOTER ===== */}
      <footer className="py-10 px-6 border-t border-white/5 pb-28 sm:pb-10">
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <Logo size={28} showText={true} />
          <div className="flex items-center gap-6">
            <Link href="/pitch" className="text-sm text-white/30 hover:text-white/60 transition-colors">Pitch</Link>
            <Link href="/login" className="text-sm text-white/30 hover:text-white/60 transition-colors">Login</Link>
            <Link href="/register" className="text-sm text-white/30 hover:text-white/60 transition-colors">Registro</Link>
          </div>
          <p className="text-xs text-white/20">© {new Date().getFullYear()} SellIA 🧡</p>
        </div>
      </footer>
    </div>
  )
}
