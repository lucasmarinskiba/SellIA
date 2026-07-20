'use client'

import { useEffect, useState, useRef } from 'react'
import { motion, useInView, useSpring, useTransform } from 'framer-motion'
import { useAuth } from '@/hooks/useAuth'
import { autopilotApi, OvernightReport } from '@/lib/autopilot'
import { businessApi } from '@/lib/business'
import { dispatchCelebration } from '@/components/gamification/CelebrationSystem'
import { Skeleton } from '@/components/ui/Skeleton'
import {
  Moon, Sun, TrendingUp, MessageSquare, Wrench, Target,
  Sprout, Shield, Rocket, Search, Share2, Star, ArrowRight,
  MessageCircle, Clock, Zap, CheckCircle2
} from 'lucide-react'

function AnimatedCounter({ value, label, icon, delay = 0 }: { value: number; label: string; icon: React.ReactNode; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true })
  const spring = useSpring(0, { duration: 2000 })
  const display = useTransform(spring, (v) => Math.floor(v))
  const [displayValue, setDisplayValue] = useState(0)

  useEffect(() => {
    if (isInView) {
      const timeout = setTimeout(() => spring.set(value), delay)
      return () => clearTimeout(timeout)
    }
  }, [isInView, value, spring, delay])

  useEffect(() => {
    const unsub = display.on('change', (v) => setDisplayValue(v))
    return unsub
  }, [display])

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5, delay: delay / 1000 }}
      className="flex flex-col items-center text-center p-4 rounded-2xl bg-card border border-border"
    >
      <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-2">
        {icon}
      </div>
      <span className="text-3xl font-bold text-foreground">{displayValue.toLocaleString()}</span>
      <span className="text-xs text-muted-foreground mt-1">{label}</span>
    </motion.div>
  )
}

function TrustScoreRing({ score }: { score: number }) {
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true })
  const radius = 50
  const circumference = 2 * Math.PI * radius
  const progress = (score / 100) * circumference

  return (
    <div ref={ref} className="relative w-32 h-32 flex items-center justify-center">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r={radius} fill="none" stroke="currentColor" strokeWidth="8" className="text-muted/20" />
        <motion.circle
          cx="60" cy="60" r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          strokeLinecap="round"
          className={score >= 80 ? 'text-emerald-400' : score >= 60 ? 'text-amber-400' : 'text-red-400'}
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={isInView ? { strokeDashoffset: circumference - progress } : {}}
          transition={{ duration: 1.5, ease: 'easeOut' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-foreground">{score}</span>
        <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Trust</span>
      </div>
    </div>
  )
}

function SectionHeader({ emoji, title, highlight }: { emoji: string; title: string; highlight?: string }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center gap-3">
        <span className="text-2xl">{emoji}</span>
        <h2 className="text-xl font-bold text-foreground">{title}</h2>
      </div>
      {highlight && (
        <span className="text-xs font-medium px-3 py-1 rounded-full bg-primary/10 text-primary border border-primary/20">
          {highlight}
        </span>
      )}
    </div>
  )
}

function SaleCard({ item }: { item: Record<string, any> }) {
  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      className="relative min-w-[240px] p-4 rounded-2xl bg-card border border-border overflow-hidden group"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      <div className="relative">
        <div className="flex items-center gap-3 mb-3">
          {item.seller_avatar ? (
            <img src={item.seller_avatar} alt="" className="w-8 h-8 rounded-full object-cover" />
          ) : (
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xs font-bold">
              {item.seller_name?.[0] || 'S'}
            </div>
          )}
          <div>
            <p className="text-sm font-semibold text-foreground">{item.seller_name}</p>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-muted text-muted-foreground uppercase">
              {item.platform}
            </span>
          </div>
        </div>
        <p className="text-xs text-muted-foreground mb-1">{item.customer_name}</p>
        <div className="flex items-center justify-between">
          <span className="text-lg font-bold text-emerald-400">${item.amount?.toLocaleString?.() || item.amount}</span>
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Clock className="w-3 h-3" /> {item.time}
          </span>
        </div>
      </div>
    </motion.div>
  )
}

function ConversationCard({ item }: { item: Record<string, any> }) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="p-4 rounded-2xl bg-card border border-border"
    >
      <div className="flex items-center gap-2 mb-2">
        <MessageCircle className="w-4 h-4 text-primary" />
        <span className="text-sm font-semibold text-foreground">{item.customer_name}</span>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-muted text-muted-foreground uppercase ml-auto">
          {item.platform}
        </span>
      </div>
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span className="line-through opacity-50">Último mensaje: hace {item.last_inbound_hours}h</span>
        <ArrowRight className="w-3 h-3" />
        <span className="text-emerald-400 font-medium">
          {item.responded ? 'Auto-followup enviado · Respondió' : 'Auto-followup enviado'}
        </span>
      </div>
    </motion.div>
  )
}

function RepairCard({ item }: { item: Record<string, any> }) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="p-4 rounded-2xl bg-card border border-border flex items-center gap-3"
    >
      <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center shrink-0">
        <Wrench className="w-4 h-4 text-amber-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-foreground truncate">{item.description}</p>
        <p className="text-xs text-muted-foreground">{item.time}</p>
      </div>
      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
    </motion.div>
  )
}

function OpportunityCard({ item }: { item: Record<string, any> }) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="p-4 rounded-2xl bg-card border border-border"
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold text-foreground">{item.customer_name}</span>
        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${item.score >= 80 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-primary/10 text-primary'}`}>
          {item.score}%
        </span>
      </div>
      <p className="text-xs text-muted-foreground mb-1">Etapa: {item.stage}</p>
      {item.value > 0 && (
        <p className="text-sm font-bold text-foreground">${item.value?.toLocaleString?.() || item.value}</p>
      )}
    </motion.div>
  )
}

function GrowthCard({ item }: { item: Record<string, any> }) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="p-4 rounded-2xl bg-card border border-border flex items-center gap-3"
    >
      <div className="w-8 h-8 rounded-lg bg-violet-500/10 flex items-center justify-center shrink-0">
        <Sprout className="w-4 h-4 text-violet-400" />
      </div>
      <p className="text-sm text-foreground">{item.description}</p>
    </motion.div>
  )
}

function NarrativeSection({ section, index }: { section: Record<string, any>; index: number }) {
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true, margin: '-80px' })

  const bgGradients = [
    'from-background via-background to-background',
    'from-background via-primary/[0.02] to-background',
    'from-background via-emerald-500/[0.02] to-background',
    'from-background via-amber-500/[0.02] to-background',
    'from-background via-violet-500/[0.02] to-background',
    'from-background via-background to-primary/[0.03]',
  ]

  return (
    <motion.section
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, delay: 0.1 }}
      className={`py-10 px-4 md:px-8 bg-gradient-to-b ${bgGradients[index % bgGradients.length]}`}
    >
      <div className="max-w-5xl mx-auto">
        <SectionHeader
          emoji={section.emoji}
          title={section.title}
          highlight={section.highlight}
        />

        {section.emoji === '💰' && section.items?.length > 0 && (
          <div className="flex gap-4 overflow-x-auto pb-4 -mx-4 px-4 md:mx-0 md:px-0 scrollbar-hide">
            {section.items.map((item: any, i: number) => (
              <SaleCard key={i} item={item} />
            ))}
          </div>
        )}

        {section.emoji === '🤝' && section.items?.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {section.items.map((item: any, i: number) => (
              <ConversationCard key={i} item={item} />
            ))}
          </div>
        )}

        {section.emoji === '🔧' && section.items?.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {section.items.map((item: any, i: number) => (
              <RepairCard key={i} item={item} />
            ))}
          </div>
        )}

        {section.emoji === '🎯' && section.items?.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {section.items.map((item: any, i: number) => (
              <OpportunityCard key={i} item={item} />
            ))}
          </div>
        )}

        {section.emoji === '📈' && section.items?.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {section.items.map((item: any, i: number) => (
              <GrowthCard key={i} item={item} />
            ))}
          </div>
        )}

        {section.emoji === '💤' && (
          <div className="flex flex-col md:flex-row items-center gap-8 p-6 rounded-2xl bg-card border border-border">
            <TrustScoreRing score={section.count || 0} />
            <div className="flex-1 text-center md:text-left">
              <p className="text-lg font-semibold text-foreground mb-1">
                {section.highlight || 'El equipo manejó todo'}
              </p>
              <p className="text-sm text-muted-foreground">
                Mientras dormías, el sistema autónomo ejecutó todas las acciones sin intervención humana.
              </p>
              <div className="flex flex-wrap justify-center md:justify-start gap-4 mt-4">
                {section.items?.map((stat: any, i: number) => (
                  <div key={i} className="text-center">
                    <p className="text-lg font-bold text-foreground">{stat.value}</p>
                    <p className="text-[10px] text-muted-foreground uppercase">{stat.label}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="hidden md:flex items-center gap-1">
              {[...Array(5)].map((_, i) => (
                <motion.div
                  key={i}
                  animate={{ opacity: [0.3, 1, 0.3], y: [0, -4, 0] }}
                  transition={{ duration: 2, repeat: Infinity, delay: i * 0.3 }}
                >
                  <Star className="w-5 h-5 text-amber-400 fill-amber-400" />
                </motion.div>
              ))}
            </div>
          </div>
        )}
      </div>
    </motion.section>
  )
}

export default function MientrasDormiasPage() {
  const { user } = useAuth()
  const [businessId, setBusinessId] = useState<string | null>(null)
  const [report, setReport] = useState<OvernightReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    businessApi.list().then(res => {
      if (res.length > 0) setBusinessId(res[0].id)
    })
  }, [user])

  useEffect(() => {
    if (!businessId) return
    loadReport()
  }, [businessId])

  const loadReport = async () => {
    if (!businessId) return
    setLoading(true)
    try {
      const data = await autopilotApi.getOvernightReport(businessId)
      setReport(data)
      // Confetti burst if great night
      if (data.summary_stats?.sales > 5 || data.summary_stats?.revenue > 1000) {
        setTimeout(() => {
          dispatchCelebration(
            3,
            '¡Gran noche! 🎉',
            `Cerramos ${data.summary_stats.sales} ventas y generamos $${data.summary_stats.revenue?.toLocaleString?.() || data.summary_stats.revenue}`
          )
        }, 1200)
      }
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error cargando el reporte nocturno')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        {/* Hero skeleton */}
        <div className="relative overflow-hidden px-4 md:px-8 pt-16 pb-12">
          <div className="max-w-5xl mx-auto text-center">
            <Skeleton className="h-8 w-48 mx-auto mb-4" />
            <Skeleton className="h-12 w-80 mx-auto mb-4" />
            <Skeleton className="h-6 w-64 mx-auto mb-8" />
            <div className="flex justify-center gap-4">
              <Skeleton className="h-10 w-32 rounded-full" />
              <Skeleton className="h-10 w-40 rounded-full" />
            </div>
          </div>
        </div>
        {/* Stats skeleton */}
        <div className="max-w-5xl mx-auto px-4 md:px-8 mb-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-28 rounded-2xl" />
            ))}
          </div>
        </div>
        {/* Sections skeleton */}
        <div className="max-w-5xl mx-auto px-4 md:px-8 space-y-8 pb-20">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-48 rounded-2xl" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <div className="text-center max-w-md">
          <Moon className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h2 className="text-xl font-bold text-foreground mb-2">No pudimos cargar tu noche</h2>
          <p className="text-sm text-muted-foreground mb-6">{error}</p>
          <button
            onClick={loadReport}
            className="px-6 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 transition-opacity"
          >
            Reintentar
          </button>
        </div>
      </div>
    )
  }

  const stats = report?.summary_stats || {}

  return (
    <div className="min-h-screen bg-background">
      {/* Hero */}
      <section className="relative overflow-hidden px-4 md:px-8 pt-16 pb-12">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/[0.03] via-background to-background" />
        {/* Moon/Sun animation */}
        <div className="absolute top-8 right-8 md:top-12 md:right-20">
          <motion.div
            initial={{ y: 40, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 1.2, ease: 'easeOut' }}
          >
            <motion.div
              animate={{ rotate: [0, 10, -10, 0] }}
              transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
              className="relative"
            >
              <Moon className="w-16 h-16 text-primary/20 absolute -top-4 -left-4" />
              <Sun className="w-12 h-12 text-amber-400" />
            </motion.div>
          </motion.div>
        </div>

        <div className="relative max-w-5xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/10 text-primary text-sm font-medium border border-primary/20 mb-6">
              <Moon className="w-4 h-4" />
              {report?.night_period}
              <Sun className="w-4 h-4" />
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl md:text-6xl font-bold text-foreground mb-4 tracking-tight"
          >
            {report?.greeting || 'Buenos días'}
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-lg md:text-xl text-muted-foreground mb-8"
          >
            Tu equipo trabajó toda la noche
          </motion.p>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="inline-flex items-center gap-3 px-5 py-2.5 rounded-2xl bg-card border border-border"
          >
            <Shield className="w-5 h-5 text-emerald-400" />
            <span className="text-sm text-foreground">
              Dormiste tranquilo <span className="font-bold">{Math.round((report?.trust_score || 0) / 10)}/10</span>
            </span>
          </motion.div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="px-4 md:px-8 mb-8">
        <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4">
          <AnimatedCounter value={stats.sales || 0} label="Ventas" icon={<TrendingUp className="w-5 h-5" />} delay={0} />
          <AnimatedCounter value={stats.messages || 0} label="Mensajes" icon={<MessageSquare className="w-5 h-5" />} delay={100} />
          <AnimatedCounter value={stats.leads || 0} label="Leads" icon={<Zap className="w-5 h-5" />} delay={200} />
          <AnimatedCounter value={stats.problems_fixed || 0} label="Problemas solucionados" icon={<Wrench className="w-5 h-5" />} delay={300} />
        </div>
      </section>

      {/* Top Seller */}
      {report?.top_seller && (
        <section className="px-4 md:px-8 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="max-w-5xl mx-auto flex items-center gap-4 p-4 rounded-2xl bg-gradient-to-r from-amber-500/5 to-background border border-amber-500/10"
          >
            {report.top_seller.avatar ? (
              <img src={report.top_seller.avatar} alt="" className="w-12 h-12 rounded-full object-cover border-2 border-amber-400/30" />
            ) : (
              <div className="w-12 h-12 rounded-full bg-amber-500/10 flex items-center justify-center text-amber-400 font-bold text-lg">
                {report.top_seller.name?.[0] || 'S'}
              </div>
            )}
            <div className="flex-1">
              <p className="text-sm text-muted-foreground">Vendedor estrella de la noche</p>
              <p className="text-lg font-bold text-foreground">
                {report.top_seller.name} · {report.top_seller.sales} ventas · ${(report.top_seller.revenue || 0).toLocaleString()}
              </p>
            </div>
            <Star className="w-6 h-6 text-amber-400 fill-amber-400 hidden md:block" />
          </motion.div>
        </section>
      )}

      {/* Narrative Sections */}
      {report?.sections?.map((section, index) => (
        <NarrativeSection key={index} section={section} index={index} />
      ))}

      {/* Closing Section */}
      <section className="px-4 md:px-8 py-16">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-5xl mx-auto text-center"
        >
          <div className="p-8 md:p-12 rounded-3xl bg-gradient-to-br from-primary/5 via-background to-primary/[0.02] border border-border">
            <h2 className="text-2xl md:text-3xl font-bold text-foreground mb-3">
              {report?.prediction || 'Hoy prevemos cerrar más'}
            </h2>
            <p className="text-muted-foreground mb-8 max-w-lg mx-auto">
              {report?.recommendation}
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-6">
              <button className="w-full sm:w-auto px-8 py-3 rounded-xl bg-primary text-primary-foreground font-semibold hover:opacity-90 transition-opacity flex items-center justify-center gap-2">
                <Rocket className="w-4 h-4" />
                Dejalo correr
              </button>
              <button className="w-full sm:w-auto px-8 py-3 rounded-xl bg-card text-foreground font-semibold border border-border hover:bg-accent transition-colors flex items-center justify-center gap-2">
                <Search className="w-4 h-4" />
                Revisar oportunidades
              </button>
            </div>

            <button
              onClick={() => {
                if (navigator.share) {
                  navigator.share({
                    title: 'Mientras Dormías — SellIA',
                    text: `${report?.greeting}. ${report?.prediction}.`,
                  })
                } else {
                  navigator.clipboard.writeText(`${report?.greeting}. ${report?.prediction}.`)
                }
              }}
              className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <Share2 className="w-4 h-4" />
              Compartir resumen
            </button>
          </div>
        </motion.div>
      </section>

      {/* Spacer */}
      <div className="h-20" />
    </div>
  )
}
