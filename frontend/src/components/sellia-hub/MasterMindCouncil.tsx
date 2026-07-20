'use client'

/**
 * MASTERMIND COUNCIL
 *
 * Consejo de IA inspirado en los mejores del mundo de los negocios.
 * Cada "miembro" es un agente con un cuerpo de conocimiento específico que
 * la IA invoca cuando la situación lo amerita.
 *
 * Categorías: Empresarios, Vendedores, Brokers/Inversores, Marketers,
 * Innovadores, Negociadores, Branding.
 */

import { useState, useMemo } from 'react'
import {
  Crown, Sparkles, Users, Quote, Activity, Brain, Filter,
  TrendingUp, MessageCircle, ChevronRight, Bot, Star
} from 'lucide-react'

type MentorCategory = 'entrepreneur' | 'seller' | 'broker' | 'marketer' | 'innovator' | 'negotiator' | 'branding'

interface Mentor {
  id: string
  name: string
  emoji: string
  role: string
  category: MentorCategory
  contribution: string
  signatureQuote: string
  activatedToday: number
  color: string
}

const MENTORS: Mentor[] = [
  // Empresarios
  { id: 'jb', name: 'Jeff Bezos',         emoji: '🚀', role: 'Customer obsession · Long-term',     category: 'entrepreneur', contribution: 'Customer-centric ops, two-pizza teams, Day 1 mindset', signatureQuote: '"Tu marca es lo que la gente dice de vos cuando no estás."', activatedToday: 18, color: '#FF9900' },
  { id: 'em', name: 'Elon Musk',          emoji: '🛰',  role: 'First principles · Vertical integration', category: 'entrepreneur', contribution: 'Cuestiona supuestos, escala 10x con primeros principios', signatureQuote: '"Razoná desde primeros principios, no por analogía."', activatedToday: 12, color: '#E31E37' },
  { id: 'sj', name: 'Steve Jobs',         emoji: '🍎', role: 'Product taste · Demo mastery',       category: 'entrepreneur', contribution: 'Reduce a la esencia, demo masterclass, attention to detail', signatureQuote: '"Diseño no es cómo se ve, es cómo funciona."', activatedToday: 23, color: '#A1A1A1' },
  { id: 'np', name: 'Naval Ravikant',     emoji: '🧘', role: 'Leverage · Specific knowledge',      category: 'entrepreneur', contribution: 'Apalancamiento (código, media, capital), wealth via skills', signatureQuote: '"Buscá apalancamiento, no horas."', activatedToday: 8, color: '#06b6d4' },
  { id: 'pg', name: 'Paul Graham',        emoji: '🌱', role: 'Startup growth · Do things that don\'t scale', category: 'entrepreneur', contribution: 'Talk to users, build MVP, growth obsession', signatureQuote: '"Hacé cosas que no escalan al principio."', activatedToday: 6, color: '#fbbf24' },

  // Vendedores
  { id: 'gc', name: 'Grant Cardone',      emoji: '🔥', role: 'Sales obsession · 10X follow-up',    category: 'seller', contribution: 'Persistencia implacable, 12+ toques sin desistir', signatureQuote: '"Si no estás conmigo, estás contra mí."', activatedToday: 47, color: '#ef4444' },
  { id: 'jb2',name: 'Jordan Belfort',     emoji: '🐺', role: 'Straight Line · Objection mastery',  category: 'seller', contribution: 'Manejo de objeciones, certainty, tonality, lenguaje', signatureQuote: '"Vender es transferencia de certeza."', activatedToday: 31, color: '#f97316' },
  { id: 'zz', name: 'Zig Ziglar',         emoji: '🤝', role: 'Asumptive close · Relationship',     category: 'seller', contribution: 'Cierre por presupuesto, relación de largo plazo', signatureQuote: '"Vas a tener todo lo que quieras si ayudás a otros."', activatedToday: 24, color: '#22c55e' },
  { id: 'ar', name: 'Aaron Ross',         emoji: '📞', role: 'Predictable Revenue · Outbound',     category: 'seller', contribution: 'Cold email frameworks, SDR/AE split, predictable pipeline', signatureQuote: '"Outbound es ciencia, no arte."', activatedToday: 14, color: '#3b82f6' },
  { id: 'sw', name: 'Sandler · Wenschlag', emoji: '⚓', role: 'Pain funnel · Up-front contracts',  category: 'seller', contribution: 'Pain-based discovery, contratos previos, no chasing', signatureQuote: '"El sufrimiento financiero es el verdadero motor."', activatedToday: 9, color: '#a855f7' },

  // Brokers / Inversores
  { id: 'wb', name: 'Warren Buffett',     emoji: '💎', role: 'Value investing · Margin of safety', category: 'broker', contribution: 'Análisis de moats, valuation, pricing power', signatureQuote: '"El precio es lo que pagás, el valor es lo que recibís."', activatedToday: 4, color: '#fbbf24' },
  { id: 'cm', name: 'Charlie Munger',     emoji: '🦉', role: 'Mental models · Inversión',          category: 'broker', contribution: 'Modelos mentales múltiples, inversión de problemas', signatureQuote: '"Invertí el problema. Siempre invertí."', activatedToday: 3, color: '#84cc16' },
  { id: 'rd', name: 'Ray Dalio',          emoji: '🌐', role: 'Macro · Principles',                 category: 'broker', contribution: 'Ciclos económicos, all-weather portfolio, radical transparency', signatureQuote: '"El dolor + reflexión = progreso."', activatedToday: 5, color: '#06b6d4' },
  { id: 'pt', name: 'Peter Thiel',        emoji: '🦄', role: 'Monopolies · Zero to One',           category: 'broker', contribution: 'Monopolios, contrarianismo, 10x improvement', signatureQuote: '"La competencia es para perdedores."', activatedToday: 2, color: '#a855f7' },

  // Marketers
  { id: 'gv', name: 'Gary Vee',           emoji: '⚡', role: 'Attention economy · Content',        category: 'marketer', contribution: 'Day-trading attention, jab-jab-right-hook, document don\'t create', signatureQuote: '"La atención es la única moneda real."', activatedToday: 89, color: '#FF6B35' },
  { id: 'ah', name: 'Alex Hormozi',       emoji: '💰', role: 'Grand Slam Offer · Value Equation',  category: 'marketer', contribution: 'Offer mechanics, value stack, guarantees, $100M Offers', signatureQuote: '"Hacé ofertas tan buenas que se sienta estúpido decir no."', activatedToday: 42, color: '#10b981' },
  { id: 'sg', name: 'Seth Godin',         emoji: '💜', role: 'Permission marketing · Tribes',       category: 'marketer', contribution: 'Purple Cow, permission, tribes, remarkable product', signatureQuote: '"Si no es sobre la audiencia, no funciona."', activatedToday: 18, color: '#8b5cf6' },
  { id: 'rb', name: 'Russell Brunson',    emoji: '🌀', role: 'Funnels · ClickFunnels',             category: 'marketer', contribution: 'Sales funnels, hook-story-offer, secrets trilogy', signatureQuote: '"Cada negocio es un funnel disfrazado."', activatedToday: 22, color: '#ec4899' },
  { id: 'nb', name: 'Neil Patel',         emoji: '🔍', role: 'SEO · Content scaling',              category: 'marketer', contribution: 'SEO, content velocity, AdWords + organic combo', signatureQuote: '"Volume + Quality + Distribution = ganás."', activatedToday: 26, color: '#3b82f6' },

  // Innovadores
  { id: 'cc', name: 'Clay Christensen',   emoji: '🔧', role: 'Disruption · Jobs-to-be-done',       category: 'innovator', contribution: 'Innovator\'s Dilemma, JTBD framework, low-end disruption', signatureQuote: '"La gente no compra productos, contrata empleos."', activatedToday: 7, color: '#06b6d4' },
  { id: 'wb2', name: 'W. Chan Kim',       emoji: '🐳', role: 'Blue Ocean Strategy',                category: 'innovator', contribution: 'Crear espacio no disputado, eliminar/reducir/elevar/crear', signatureQuote: '"Hacé que la competencia sea irrelevante."', activatedToday: 4, color: '#0ea5e9' },
  { id: 'gs', name: 'Geoffrey Moore',     emoji: '🌉', role: 'Crossing the Chasm',                 category: 'innovator', contribution: 'Early adopters vs early majority, bowling pin', signatureQuote: '"El chasm mata más startups que la competencia."', activatedToday: 3, color: '#a855f7' },

  // Negociadores
  { id: 'cv', name: 'Chris Voss',         emoji: '🎯', role: 'Tactical Empathy · FBI',             category: 'negotiator', contribution: 'Mirroring, labeling, calibrated questions, accusation audit', signatureQuote: '"Nunca dividas la diferencia."', activatedToday: 67, color: '#ef4444' },
  { id: 'rf', name: 'Roger Fisher',       emoji: '🏛', role: 'Getting to Yes · Harvard',            category: 'negotiator', contribution: 'BATNA, intereses vs posiciones, criterios objetivos', signatureQuote: '"Separá las personas del problema."', activatedToday: 19, color: '#3b82f6' },
  { id: 'wu', name: 'William Ury',        emoji: '🌉', role: 'Getting Past No · Golden Bridge',    category: 'negotiator', contribution: 'Construí puente dorado para que digan sí con dignidad', signatureQuote: '"Ir al balcón antes de reaccionar."', activatedToday: 11, color: '#8b5cf6' },
  { id: 'hc', name: 'Herb Cohen',         emoji: '⚡', role: 'Power Negotiation · Time pressure',   category: 'negotiator', contribution: 'Tiempo, información y poder percibido como armas', signatureQuote: '"Todo en la vida es negociable."', activatedToday: 8, color: '#f59e0b' },

  // Branding
  { id: 'ar2', name: 'Al Ries',           emoji: '🎯', role: 'Positioning · 22 Immutable Laws',     category: 'branding', contribution: 'Categoría primero, mind share, focused brand', signatureQuote: '"Es mejor ser primero que ser mejor."', activatedToday: 13, color: '#fbbf24' },
  { id: 'da', name: 'David Aaker',        emoji: '🌟', role: 'Brand Equity · Identity prism',       category: 'branding', contribution: 'Awareness, loyalty, perceived quality, associations', signatureQuote: '"La marca es un activo financiero medible."', activatedToday: 9, color: '#a855f7' },
  { id: 'mn', name: 'Marty Neumeier',     emoji: '🎨', role: 'Brand Gap · Visual systems',         category: 'branding', contribution: 'Brand essence, voice, sistema visual coherente', signatureQuote: '"Una marca no es un logo. Es un sentimiento gut."', activatedToday: 7, color: '#ec4899' },
]

const CATEGORY_CONFIG: Record<MentorCategory, { label: string; emoji: string; color: string }> = {
  entrepreneur: { label: 'Empresarios',     emoji: '🚀', color: '#FF9900' },
  seller:       { label: 'Vendedores',      emoji: '🔥', color: '#ef4444' },
  broker:       { label: 'Brokers/Invest.', emoji: '💎', color: '#fbbf24' },
  marketer:     { label: 'Marketers',       emoji: '⚡', color: '#FF6B35' },
  innovator:    { label: 'Innovadores',     emoji: '🌀', color: '#06b6d4' },
  negotiator:   { label: 'Negociadores',    emoji: '🎯', color: '#3b82f6' },
  branding:     { label: 'Branding',        emoji: '🎨', color: '#ec4899' },
}

export default function MasterMindCouncil() {
  const [filter, setFilter] = useState<MentorCategory | 'all'>('all')
  const [selectedId, setSelectedId] = useState<string | null>(MENTORS[0]?.id || null)

  const filtered = useMemo(
    () => filter === 'all' ? MENTORS : MENTORS.filter(m => m.category === filter),
    [filter]
  )

  const stats = useMemo(() => {
    const totalActivations = MENTORS.reduce((s, m) => s + m.activatedToday, 0)
    const topMentor = [...MENTORS].sort((a, b) => b.activatedToday - a.activatedToday)[0]
    return { total: MENTORS.length, totalActivations, topMentor }
  }, [])

  const categoryCounts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const m of MENTORS) c[m.category] = (c[m.category] || 0) + 1
    return c
  }, [])

  const selected = selectedId ? MENTORS.find(m => m.id === selectedId) : null

  return (
    <section className="relative rounded-2xl border border-amber-500/20 bg-gradient-to-br from-[#1a1308]/40 via-[#0a0e1a]/85 to-[#0a0e1a]/95 backdrop-blur overflow-hidden">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-amber-400/80 to-transparent" />

      {/* Header */}
      <div className="px-5 py-4 border-b border-white/[0.06] flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500/25 to-orange-500/15 border border-amber-500/40 flex items-center justify-center">
            <Crown className="w-5 h-5 text-amber-400" style={{ filter: 'drop-shadow(0 0 8px rgba(251,191,36,0.7))' }} />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 flex-wrap">
              <span className="bg-gradient-to-r from-amber-400 via-orange-400 to-amber-400 bg-clip-text text-transparent">MASTERMIND COUNCIL</span>
              <span className="text-white/40 font-light normal-case tracking-normal">·  {stats.total} mentes detrás de la IA</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-mono uppercase tracking-widest">
                {stats.totalActivations} activaciones hoy
              </span>
            </h2>
            <p className="text-[11px] text-white/40 mt-0.5">Cada decisión IA se nutre del cuerpo de conocimiento de estos referentes</p>
          </div>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/25">
          <Star className="w-3 h-3 text-amber-400" />
          <span className="text-[10px] text-amber-300">Top hoy: <span className="font-bold">{stats.topMentor.name}</span></span>
        </div>
      </div>

      {/* Category filter */}
      <div className="px-5 py-3 border-b border-white/[0.06] flex items-center gap-2 overflow-x-auto no-scrollbar">
        <Filter className="w-3 h-3 text-white/30 shrink-0" />
        <button
          onClick={() => setFilter('all')}
          className={`shrink-0 px-3 py-1 rounded-full text-[10px] font-bold border transition-all ${
            filter === 'all' ? 'bg-white/10 border-white/20 text-white' : 'bg-white/[0.02] border-white/[0.06] text-white/40'
          }`}
        >
          Todos · {MENTORS.length}
        </button>
        {(Object.keys(CATEGORY_CONFIG) as MentorCategory[]).map(cat => {
          const cfg = CATEGORY_CONFIG[cat]
          const active = filter === cat
          return (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className="shrink-0 flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold border transition-all"
              style={
                active
                  ? { background: `${cfg.color}20`, borderColor: `${cfg.color}50`, color: cfg.color }
                  : { background: 'rgba(255,255,255,0.02)', borderColor: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.4)' }
              }
            >
              <span>{cfg.emoji}</span>
              {cfg.label} · {categoryCounts[cat] || 0}
            </button>
          )
        })}
      </div>

      {/* Grid + selected */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 p-4">
        {/* List */}
        <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-[520px] overflow-y-auto">
          {filtered.map(m => {
            const cat = CATEGORY_CONFIG[m.category]
            const isSelected = selectedId === m.id
            return (
              <button
                key={m.id}
                onClick={() => setSelectedId(m.id)}
                className="text-left rounded-xl border bg-white/[0.02] hover:bg-white/[0.04] transition-all p-3 group"
                style={{
                  borderColor: isSelected ? `${m.color}60` : 'rgba(255,255,255,0.06)',
                  boxShadow: isSelected ? `0 0 16px ${m.color}15` : 'none',
                }}
              >
                <div className="flex items-start gap-2.5">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl shrink-0" style={{
                    background: `${m.color}15`,
                    border: `1px solid ${m.color}30`,
                  }}>
                    {m.emoji}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <p className="text-xs font-bold text-white truncate">{m.name}</p>
                      {m.activatedToday > 30 && (
                        <span className="text-[8px] px-1 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono">🔥</span>
                      )}
                    </div>
                    <p className="text-[10px] text-white/50 truncate">{m.role}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[9px] px-1.5 py-0.5 rounded font-mono uppercase" style={{ background: `${cat.color}18`, color: cat.color }}>
                        {cat.label}
                      </span>
                      <span className="text-[9px] text-white/40 flex items-center gap-0.5">
                        <Activity className="w-2 h-2" />
                        {m.activatedToday}
                      </span>
                    </div>
                  </div>
                </div>
              </button>
            )
          })}
        </div>

        {/* Selected detail */}
        {selected && (
          <div className="rounded-xl border p-4 self-start sticky top-4"
            style={{ background: `${selected.color}08`, borderColor: `${selected.color}30`, boxShadow: `0 0 24px ${selected.color}10` }}>
            <div className="text-center mb-3">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl text-4xl mb-2" style={{
                background: `${selected.color}18`,
                border: `2px solid ${selected.color}40`,
                boxShadow: `0 0 16px ${selected.color}25`,
              }}>
                {selected.emoji}
              </div>
              <h3 className="text-base font-bold text-white">{selected.name}</h3>
              <p className="text-[11px] text-white/50">{selected.role}</p>
            </div>

            <div className="rounded-lg p-3 bg-black/30 border border-white/[0.06] mb-3">
              <div className="flex items-start gap-2">
                <Quote className="w-3 h-3 shrink-0 mt-0.5" style={{ color: selected.color }} />
                <p className="text-[11px] text-white/85 italic leading-snug">{selected.signatureQuote}</p>
              </div>
            </div>

            <div className="mb-3">
              <p className="text-[9px] uppercase tracking-widest text-white/40 font-bold mb-1.5 flex items-center gap-1">
                <Brain className="w-2.5 h-2.5" />
                CONTRIBUCIÓN AL CEREBRO
              </p>
              <p className="text-[11px] text-white/70 leading-snug">{selected.contribution}</p>
            </div>

            <div className="rounded-lg p-2.5 bg-emerald-500/[0.06] border border-emerald-500/20">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-emerald-300">Activado hoy</span>
                <span className="text-base font-black tabular-nums" style={{ color: selected.color }}>{selected.activatedToday}×</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
