'use client'

/**
 * NEURAL BRAIN
 *
 * Visualización viva del cerebro de SellIA — una red neuronal real donde:
 *   - Entradas: canales de venta (WhatsApp, IG, Email, ML, Web, Phone)
 *   - Capa Captación: agentes que capturan y califican leads
 *   - Capa Ventas: experts (Voss, Belfort, Hormozi, Ziglar)
 *   - Capa Fidelización: onboarder, retainer, champion-builder
 *   - Salidas: lead, deal cerrado, cliente fiel, embajador
 *
 * Las conexiones "disparan" (firing) en tiempo real con packets de datos
 * viajando entre nodos. Hover en cualquier nodo muestra su estado.
 *
 * Es la metáfora visual del sistema autónomo trabajando sin supervisión.
 */

import { useState, useEffect, useMemo } from 'react'
import {
  Brain, MessageCircle, Camera as Instagram, Mail, ShoppingBag, Globe, Phone,
  Target, Search, Handshake, CheckCircle2, Rocket, Heart, Crown, Megaphone,
  Activity, Zap, Sparkles, Bot, MousePointer2, FileText, CalendarClock, CreditCard,
  Smartphone, Tv2, Briefcase, Hash, Music2, Video, Headphones
} from 'lucide-react'

type LayerId = 'input' | 'capture' | 'sales' | 'cua' | 'fidelize' | 'output'

interface BrainNode {
  id: string
  layer: LayerId
  label: string
  shortLabel: string
  icon: React.ElementType
  color: string
  x: number // percentage 0-100
  y: number // percentage 0-100
  metric?: string
}

interface NeuralEdge {
  from: string
  to: string
}

// ─── Network topology ──────────────────────────────────────────────────────────

const NODES: BrainNode[] = [
  // ─── INPUT LAYER · 14 canales (col x=3) ───
  { id: 'wa',  layer: 'input',  label: 'WhatsApp',     shortLabel: 'WA',   icon: MessageCircle, color: '#25d366', x: 3, y:  6, metric: '47 chats' },
  { id: 'ig',  layer: 'input',  label: 'Instagram',    shortLabel: 'IG',   icon: Instagram,      color: '#ec4899', x: 3, y: 13, metric: '12 DMs' },
  { id: 'tt',  layer: 'input',  label: 'TikTok',       shortLabel: 'TT',   icon: Music2,         color: '#FF0050', x: 3, y: 20, metric: '847k views' },
  { id: 'yt',  layer: 'input',  label: 'YouTube',      shortLabel: 'YT',   icon: Video,          color: '#FF0000', x: 3, y: 27, metric: '23 leads' },
  { id: 'fb',  layer: 'input',  label: 'Facebook',     shortLabel: 'FB',   icon: Hash,           color: '#1877F2', x: 3, y: 34, metric: '8.2k fans' },
  { id: 'li',  layer: 'input',  label: 'LinkedIn',     shortLabel: 'LI',   icon: Briefcase,      color: '#0A66C2', x: 3, y: 41, metric: '47 conexiones' },
  { id: 'em',  layer: 'input',  label: 'Email',        shortLabel: 'EM',   icon: Mail,           color: '#3b82f6', x: 3, y: 48, metric: '8 sec activas' },
  { id: 'ml',  layer: 'input',  label: 'MercadoLibre', shortLabel: 'ML',   icon: ShoppingBag,    color: '#fbbf24', x: 3, y: 55, metric: '23 preg' },
  { id: 'am',  layer: 'input',  label: 'Amazon',       shortLabel: 'AMZ',  icon: ShoppingBag,    color: '#FF9900', x: 3, y: 62, metric: '14 órdenes' },
  { id: 'sh',  layer: 'input',  label: 'Shopify',      shortLabel: 'SH',   icon: ShoppingBag,    color: '#95BF47', x: 3, y: 69, metric: '847 sesiones' },
  { id: 'ht',  layer: 'input',  label: 'Hotmart',      shortLabel: 'HM',   icon: ShoppingBag,    color: '#EF4E22', x: 3, y: 76, metric: '5 ventas' },
  { id: 'web', layer: 'input',  label: 'Web propia',   shortLabel: 'WEB',  icon: Globe,          color: '#06b6d4', x: 3, y: 83, metric: '4.2k sesiones' },
  { id: 'tel', layer: 'input',  label: 'Llamada',      shortLabel: 'TEL',  icon: Phone,          color: '#a855f7', x: 3, y: 90, metric: '2 calls' },
  { id: 'pod', layer: 'input',  label: 'Podcast/Voz',  shortLabel: 'POD',  icon: Headphones,     color: '#8b5cf6', x: 3, y: 97, metric: '1.2k listens' },

  // ─── CAPTURE LAYER · 5 agentes (col x=18) ───
  { id: 'gv',  layer: 'capture', label: 'Captador · Multi-canal',      shortLabel: 'CAPT',  icon: Target,       color: '#3b82f6', x: 18, y: 12, metric: '47 prospect' },
  { id: 'bm',  layer: 'capture', label: 'Cualificador IA',             shortLabel: 'QUAL',  icon: Search,       color: '#6366f1', x: 18, y: 30, metric: '28 calif' },
  { id: 'sp',  layer: 'capture', label: 'Diagnosticador (SPIN)',       shortLabel: 'DIAG',  icon: Sparkles,     color: '#06b6d4', x: 18, y: 48, metric: '15 discovery' },
  { id: 'ls',  layer: 'capture', label: 'Listener (sentiment)',        shortLabel: 'LSTN',  icon: Activity,     color: '#14b8a6', x: 18, y: 66, metric: 'mood real-time' },
  { id: 'sg',  layer: 'capture', label: 'Segmenter (RFM/cohorts)',     shortLabel: 'SEGM',  icon: Brain,        color: '#0ea5e9', x: 18, y: 84, metric: '12 segments' },

  // ─── SALES LAYER · 7 experts (col x=37) ───
  { id: 'vs',  layer: 'sales',   label: 'Empatía Táctica',               shortLabel: 'EMP',   icon: Brain,    color: '#ef4444', x: 37, y:  8 },
  { id: 'hz',  layer: 'sales',   label: 'Grand Slam Offer',              shortLabel: 'GSO',   icon: Sparkles, color: '#f59e0b', x: 37, y: 21 },
  { id: 'bf',  layer: 'sales',   label: 'Straight Line Close',           shortLabel: 'SL',    icon: Zap,      color: '#f97316', x: 37, y: 34 },
  { id: 'zg',  layer: 'sales',   label: 'Cierre Asuntivo',               shortLabel: 'ASM',   icon: Handshake,color: '#22c55e', x: 37, y: 47 },
  { id: 'cd',  layer: 'sales',   label: '10X Close',                     shortLabel: '10X',   icon: Activity, color: '#10b981', x: 37, y: 60 },
  { id: 'gi',  layer: 'sales',   label: 'Ley de los 250',                shortLabel: 'L250',  icon: Target,   color: '#dc2626', x: 37, y: 73 },
  { id: 'fb2', layer: 'sales',   label: 'Story-sell',                    shortLabel: 'STRY',  icon: FileText, color: '#3b82f6', x: 37, y: 86 },

  // ─── CUA LAYER · 6 Computer Use bots (col x=55) ───
  { id: 'cua-br', layer: 'cua', label: 'Browser-Bot · Chrome/FF/WebKit',  shortLabel: 'BRWS', icon: Globe,         color: '#fbbf24', x: 55, y: 10, metric: '17 sesiones' },
  { id: 'cua-mo', layer: 'cua', label: 'Mobile-Bot · iOS/Android emu',    shortLabel: 'MOBL', icon: Smartphone,    color: '#06b6d4', x: 55, y: 26, metric: '4 emu activos' },
  { id: 'cua-ff', layer: 'cua', label: 'Form-Filler · checkout/forms',    shortLabel: 'FORM', icon: FileText,      color: '#a855f7', x: 55, y: 42, metric: '23 forms/h' },
  { id: 'cua-cl', layer: 'cua', label: 'Click-Bot · UI navigator',        shortLabel: 'CLCK', icon: MousePointer2, color: '#ec4899', x: 55, y: 58, metric: '847 clicks' },
  { id: 'cua-ca', layer: 'cua', label: 'Calendar-Bot · meetings',         shortLabel: 'CAL',  icon: CalendarClock, color: '#0ea5e9', x: 55, y: 74, metric: '12 booked' },
  { id: 'cua-py', layer: 'cua', label: 'Payment-Bot · Stripe/MP/AFIP',    shortLabel: 'PAY',  icon: CreditCard,    color: '#84cc16', x: 55, y: 90, metric: '$3.2k procesado' },

  // ─── FIDELIZE LAYER · 5 (col x=73) ───
  { id: 'bz',  layer: 'fidelize', label: 'Onboarder · CX Premium',      shortLabel: 'ONBD', icon: Rocket,    color: '#10b981', x: 73, y: 14 },
  { id: 'rt',  layer: 'fidelize', label: 'Engager (RFM/LTV)',           shortLabel: 'ENG',  icon: Heart,     color: '#ec4899', x: 73, y: 32 },
  { id: 'rc',  layer: 'fidelize', label: 'Recovery Lab',                shortLabel: 'RECV', icon: Activity,  color: '#06b6d4', x: 73, y: 50 },
  { id: 'cb',  layer: 'fidelize', label: 'Champion-Builder',            shortLabel: 'CHMP', icon: Crown,     color: '#fbbf24', x: 73, y: 68 },
  { id: 'ev',  layer: 'fidelize', label: 'Evangelist activator',        shortLabel: 'EVNG', icon: Megaphone, color: '#dc2626', x: 73, y: 86 },

  // ─── OUTPUT LAYER · 7 outcomes (col x=92) ───
  { id: 'lead',  layer: 'output', label: 'Lead nuevo',         shortLabel: 'LEAD', icon: Target,        color: '#3b82f6', x: 92, y:  8, metric: '+47 hoy' },
  { id: 'qual',  layer: 'output', label: 'Lead calificado',    shortLabel: 'QUAL', icon: Search,        color: '#6366f1', x: 92, y: 22, metric: '+28 hoy' },
  { id: 'demo',  layer: 'output', label: 'Demo agendado',      shortLabel: 'DEMO', icon: CalendarClock, color: '#06b6d4', x: 92, y: 36, metric: '+12 hoy' },
  { id: 'deal',  layer: 'output', label: 'Deal cerrado',       shortLabel: 'WON',  icon: CheckCircle2,  color: '#22c55e', x: 92, y: 50, metric: '+12 hoy' },
  { id: 'cust',  layer: 'output', label: 'Cliente fiel',       shortLabel: 'LOYAL',icon: Heart,         color: '#a855f7', x: 92, y: 64, metric: '34 activos' },
  { id: 'adv',   layer: 'output', label: 'Embajador',          shortLabel: 'ADV',  icon: Megaphone,     color: '#fbbf24', x: 92, y: 78, metric: '+2 sem' },
  { id: 'evg',   layer: 'output', label: 'Evangelist (viral)', shortLabel: 'EVG',  icon: Crown,         color: '#dc2626', x: 92, y: 92, metric: '3 evangelistas' },
]

// Build edges across 6 layers: input → capture → sales → cua → fidelize → output (mesh)
const buildEdges = (): NeuralEdge[] => {
  const edges: NeuralEdge[] = []
  const inputs   = NODES.filter(n => n.layer === 'input')
  const captures = NODES.filter(n => n.layer === 'capture')
  const sales    = NODES.filter(n => n.layer === 'sales')
  const cuas     = NODES.filter(n => n.layer === 'cua')
  const fidels   = NODES.filter(n => n.layer === 'fidelize')
  const outputs  = NODES.filter(n => n.layer === 'output')

  // input → capture: every input connects 2 nearest captures
  inputs.forEach((inp, i) => {
    edges.push({ from: inp.id, to: captures[i % captures.length].id })
    edges.push({ from: inp.id, to: captures[(i + 1) % captures.length].id })
    if (i % 3 === 0) edges.push({ from: inp.id, to: captures[(i + 2) % captures.length].id })
  })
  // capture → sales: dense mesh
  captures.forEach((cap, i) => {
    sales.forEach((s, j) => {
      if ((i + j) % 2 === 0) edges.push({ from: cap.id, to: s.id })
    })
  })
  // sales → cua: each sales agent invokes 2-3 CUA bots
  sales.forEach((s, i) => {
    edges.push({ from: s.id, to: cuas[i % cuas.length].id })
    edges.push({ from: s.id, to: cuas[(i + 1) % cuas.length].id })
    if (i % 2 === 0) edges.push({ from: s.id, to: cuas[(i + 2) % cuas.length].id })
  })
  // cua → fidelize: action results feed fidelization
  cuas.forEach((c, i) => {
    edges.push({ from: c.id, to: fidels[i % fidels.length].id })
    if (i % 2 === 0) edges.push({ from: c.id, to: fidels[(i + 1) % fidels.length].id })
  })
  // cua → output direct shortcuts (close happens via CUA)
  edges.push({ from: 'cua-py', to: 'deal' })
  edges.push({ from: 'cua-ca', to: 'demo' })
  edges.push({ from: 'cua-ff', to: 'qual' })
  edges.push({ from: 'cua-cl', to: 'lead' })
  // fidelize → output
  fidels.forEach(f => {
    if (f.id === 'bz') { edges.push({ from: f.id, to: 'deal' }); edges.push({ from: f.id, to: 'cust' }) }
    if (f.id === 'rt') { edges.push({ from: f.id, to: 'cust' }); edges.push({ from: f.id, to: 'adv' }) }
    if (f.id === 'rc') { edges.push({ from: f.id, to: 'deal' }); edges.push({ from: f.id, to: 'cust' }) }
    if (f.id === 'cb') { edges.push({ from: f.id, to: 'adv' });  edges.push({ from: f.id, to: 'evg' }) }
    if (f.id === 'ev') { edges.push({ from: f.id, to: 'evg' });  edges.push({ from: f.id, to: 'adv' }) }
  })
  // input → lead direct
  inputs.forEach(i => edges.push({ from: i.id, to: 'lead' }))
  return edges
}

const EDGES = buildEdges()

// Pre-defined "firing paths" — sample journeys through the 6-layer brain
const FIRING_PATHS: string[][] = [
  // WhatsApp lead → Voss → Browser-Bot → Onboarder → Deal
  ['wa',  'gv',  'vs', 'cua-br', 'bz', 'deal'],
  // Instagram → Hormozi → Form-Filler → Engager → Cliente fiel
  ['ig',  'bm',  'hz', 'cua-ff', 'rt', 'cust'],
  // TikTok viral → Captador → Belfort → Click-Bot → Champion-Builder → Embajador
  ['tt',  'sp',  'bf', 'cua-cl', 'cb', 'adv'],
  // YouTube → Diag → Ziglar → Calendar-Bot → Demo agendado
  ['yt',  'sp',  'zg', 'cua-ca', 'demo'],
  // Amazon → Qual → Cardone → Payment-Bot → Deal
  ['am',  'bm',  'cd', 'cua-py', 'bz', 'deal'],
  // Mercado Libre → Listener → Girard → Mobile-Bot → Recovery Lab → Cliente fiel
  ['ml',  'ls',  'gi', 'cua-mo', 'rc', 'cust'],
  // Shopify → Segmenter → Feldman → Payment-Bot → Onboarder → Deal
  ['sh',  'sg',  'fb2','cua-py', 'bz', 'deal'],
  // LinkedIn → Qual → Voss → Browser-Bot → Engager → Cliente fiel
  ['li',  'bm',  'vs', 'cua-br', 'rt', 'cust'],
  // Hotmart → Segm → Hormozi → Form-Filler → Onboarder → Deal
  ['ht',  'sg',  'hz', 'cua-ff', 'bz', 'deal'],
  // Web form → Captador → Ziglar → Calendar-Bot → Demo
  ['web', 'gv',  'zg', 'cua-ca', 'demo'],
  // Llamada → Diag → Cardone → Click-Bot → Engager → Embajador
  ['tel', 'sp',  'cd', 'cua-cl', 'rt', 'adv'],
  // Email → Qual → Belfort → Browser-Bot → Recovery → Deal
  ['em',  'bm',  'bf', 'cua-br', 'rc', 'deal'],
  // Facebook → Listener → Girard → Mobile-Bot → Champion → Evangelist
  ['fb',  'ls',  'gi', 'cua-mo', 'cb', 'evg'],
  // Podcast → Captador → Feldman → Browser-Bot → Engager → Embajador
  ['pod', 'gv',  'fb2','cua-br', 'rt', 'adv'],
  // Instagram → Segm → Voss → Payment-Bot → Evangelist activator → Evangelist
  ['ig',  'sg',  'vs', 'cua-py', 'ev', 'evg'],
]

const PARALLEL_PATHS = 3 // simultaneous firing paths

export default function NeuralBrain() {
  const [pathOffset, setPathOffset] = useState(0)
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)
  const [tickGlobal, setTickGlobal] = useState(0)

  // Cycle: advance offset slowly so paths rotate through library
  useEffect(() => {
    const id = setInterval(() => {
      setPathOffset(i => (i + 1) % FIRING_PATHS.length)
    }, 3000)
    return () => clearInterval(id)
  }, [])

  // Global animation tick (continuous packet movement)
  useEffect(() => {
    const id = setInterval(() => setTickGlobal(t => (t + 1) % 1000), 40)
    return () => clearInterval(id)
  }, [])

  // N active paths at once (interleaved)
  const activePaths = useMemo(() => {
    const paths: string[][] = []
    for (let i = 0; i < PARALLEL_PATHS; i++) {
      paths.push(FIRING_PATHS[(pathOffset + i * 5) % FIRING_PATHS.length])
    }
    return paths
  }, [pathOffset])

  const activeNodes = useMemo(() => {
    const s = new Set<string>()
    for (const p of activePaths) for (const n of p) s.add(n)
    return s
  }, [activePaths])

  const activeEdges = useMemo(() => {
    const set = new Set<string>()
    for (const p of activePaths) {
      for (let i = 0; i < p.length - 1; i++) set.add(`${p[i]}->${p[i + 1]}`)
    }
    return set
  }, [activePaths])

  const hoveredData = hoveredNode ? NODES.find(n => n.id === hoveredNode) : null
  const W = 1000
  const H = 500

  return (
    <section className="relative rounded-2xl border border-purple-500/20 bg-gradient-to-br from-[#0c0a1a]/95 via-[#0a0e1a]/90 to-[#0a0e1a]/95 backdrop-blur overflow-hidden">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-purple-400/80 to-transparent" />
      <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-purple-400/40 to-transparent" />

      {/* Header */}
      <div className="relative px-5 py-4 border-b border-white/[0.06] flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="relative w-11 h-11 rounded-xl bg-gradient-to-br from-purple-500/30 to-pink-500/20 border border-purple-500/50 flex items-center justify-center">
            <Brain className="w-5 h-5 text-purple-400" style={{ filter: 'drop-shadow(0 0 10px rgba(168,85,247,0.8))' }} />
            <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-emerald-400 border-2 border-[#0a0e1a] animate-pulse" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 flex-wrap">
              <span className="bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent">NEURAL BRAIN</span>
              <span className="text-white/40 font-light normal-case tracking-normal">·  Red neuronal viva</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-mono uppercase tracking-widest">
                ● {EDGES.length} sinapsis
              </span>
            </h2>
            <p className="text-[11px] text-white/40 mt-0.5">Canales → Captura → Ventas → <span className="text-amber-400 font-bold">Computer Use</span> → Fidelización → Outcomes · {NODES.length} nodos · {PARALLEL_PATHS} paths en paralelo</p>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1 text-[9px] text-white/40 max-w-md">
          {activePaths.map((p, i) => (
            <span key={i} className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: ['#a855f7','#ec4899','#fbbf24'][i] }} />
              <span className="font-mono font-bold truncate" style={{ color: ['#c084fc','#f472b6','#fbbf24'][i] }}>
                {p.map(id => NODES.find(n => n.id === id)?.shortLabel).join(' → ')}
              </span>
            </span>
          ))}
        </div>
      </div>

      {/* Layer labels · 6 columns */}
      <div className="px-5 pt-3 grid grid-cols-6 gap-2 text-center">
        {[
          { label: 'CANALES (14)',     color: '#3b82f6' },
          { label: 'CAPTURA (5)',       color: '#6366f1' },
          { label: 'VENTAS · 7 EXPERTS',color: '#ef4444' },
          { label: 'COMPUTER USE (6)',  color: '#fbbf24' },
          { label: 'FIDELIZACIÓN (5)',  color: '#ec4899' },
          { label: 'OUTCOMES (7)',      color: '#22c55e' },
        ].map(l => (
          <span key={l.label} className="text-[9px] font-mono uppercase tracking-widest" style={{ color: `${l.color}cc` }}>{l.label}</span>
        ))}
      </div>

      {/* Neural canvas */}
      <div className="relative px-5 py-4">
        <div className="relative rounded-xl bg-black/30 border border-purple-500/15 overflow-hidden" style={{ aspectRatio: '2.2 / 1', minHeight: 360 }}>
          {/* Grid background */}
          <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{
            backgroundImage: 'linear-gradient(rgba(168,85,247,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(168,85,247,0.5) 1px, transparent 1px)',
            backgroundSize: '40px 40px',
          }} />

          {/* SVG canvas with edges + packets */}
          <svg viewBox={`0 0 ${W} ${H}`} className="absolute inset-0 w-full h-full" preserveAspectRatio="none">
            <defs>
              {NODES.map(n => (
                <filter key={`g-${n.id}`} id={`glow-${n.id}`}>
                  <feGaussianBlur stdDeviation="4" result="b" />
                  <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
                </filter>
              ))}
              <linearGradient id="edgeActive" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#a855f7" stopOpacity="0.9" />
                <stop offset="100%" stopColor="#ec4899" stopOpacity="0.9" />
              </linearGradient>
            </defs>

            {/* Edges */}
            {EDGES.map((edge, i) => {
              const from = NODES.find(n => n.id === edge.from)!
              const to = NODES.find(n => n.id === edge.to)!
              const isActive = activeEdges.has(`${edge.from}->${edge.to}`)
              const x1 = (from.x / 100) * W
              const y1 = (from.y / 100) * H
              const x2 = (to.x / 100) * W
              const y2 = (to.y / 100) * H
              return (
                <line
                  key={i}
                  x1={x1} y1={y1} x2={x2} y2={y2}
                  stroke={isActive ? 'url(#edgeActive)' : 'rgba(168,85,247,0.08)'}
                  strokeWidth={isActive ? 1.8 : 0.6}
                  style={isActive ? { filter: 'drop-shadow(0 0 4px rgba(168,85,247,0.5))' } : {}}
                />
              )
            })}

            {/* Multi-packet rendering · 1 per active path, phase-offset */}
            {activePaths.map((path, pIdx) => {
              if (path.length <= 1) return null
              const totalSegments = path.length - 1
              // Each path packet phase-offset to spread visually
              const phase = (tickGlobal + pIdx * 35) % 100
              const progressPct = phase / 100
              const currentSeg = Math.min(Math.floor(progressPct * totalSegments), totalSegments - 1)
              const segProgress = (progressPct * totalSegments) - currentSeg
              const fromNode = NODES.find(n => n.id === path[currentSeg])
              const toNode = NODES.find(n => n.id === path[currentSeg + 1])
              if (!fromNode || !toNode) return null
              const x = (fromNode.x + (toNode.x - fromNode.x) * segProgress) / 100 * W
              const y = (fromNode.y + (toNode.y - fromNode.y) * segProgress) / 100 * H
              const packetColor = ['#fbbf24', '#ec4899', '#a855f7'][pIdx % 3]
              return (
                <g key={`pkt-${pIdx}`}>
                  <circle cx={x} cy={y} r="8" fill={packetColor} opacity="0.25" />
                  <circle cx={x} cy={y} r="5" fill={packetColor} opacity="0.6" />
                  <circle cx={x} cy={y} r="2.5" fill="#fff" />
                </g>
              )
            })}

            {/* Nodes (rendered on top) */}
            {NODES.map(n => {
              const cx = (n.x / 100) * W
              const cy = (n.y / 100) * H
              const isActive = activeNodes.has(n.id)
              const isHover = hoveredNode === n.id
              return (
                <g
                  key={n.id}
                  onMouseEnter={() => setHoveredNode(n.id)}
                  onMouseLeave={() => setHoveredNode(null)}
                  style={{ cursor: 'pointer' }}
                >
                  {/* Outer ring */}
                  <circle cx={cx} cy={cy} r={isActive ? 22 : 16} fill={`${n.color}10`} stroke={n.color} strokeOpacity={isActive ? 0.9 : 0.35} strokeWidth={isActive ? 2 : 1} />
                  {/* Glow ring when active */}
                  {isActive && (
                    <circle cx={cx} cy={cy} r="30" fill="none" stroke={n.color} strokeOpacity="0.3" strokeWidth="1.5" style={{ filter: `drop-shadow(0 0 10px ${n.color})`, animation: 'pulse 1.5s ease-in-out infinite' }} />
                  )}
                  {/* Inner dot */}
                  <circle cx={cx} cy={cy} r={isActive ? 7 : 5} fill={n.color} style={{ filter: `drop-shadow(0 0 ${isActive ? 8 : 3}px ${n.color})` }} />
                  {/* Label */}
                  <text x={cx} y={cy + 30} textAnchor="middle" fontSize="9" fill={isActive ? n.color : 'rgba(255,255,255,0.4)'} fontFamily="monospace" fontWeight={isActive ? 'bold' : 'normal'}>
                    {n.shortLabel}
                  </text>
                  {/* Hover halo */}
                  {isHover && (
                    <circle cx={cx} cy={cy} r="34" fill="none" stroke="#fff" strokeOpacity="0.4" strokeDasharray="3 3" />
                  )}
                </g>
              )
            })}
          </svg>

          {/* Hover info card */}
          {hoveredData && (
            <div className="absolute bottom-2 left-2 right-2 sm:left-auto sm:right-2 sm:max-w-xs rounded-xl bg-black/85 border backdrop-blur p-3 pointer-events-none"
              style={{ borderColor: `${hoveredData.color}40`, boxShadow: `0 0 20px ${hoveredData.color}20` }}>
              <div className="flex items-center gap-2 mb-1">
                <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: `${hoveredData.color}20`, border: `1px solid ${hoveredData.color}40` }}>
                  <hoveredData.icon className="w-3.5 h-3.5" style={{ color: hoveredData.color }} />
                </div>
                <div>
                  <p className="text-xs font-bold text-white">{hoveredData.label}</p>
                  <p className="text-[9px] uppercase tracking-widest" style={{ color: hoveredData.color }}>{hoveredData.layer}</p>
                </div>
              </div>
              {hoveredData.metric && (
                <p className="text-[10px] text-white/60 font-mono mt-1">{hoveredData.metric}</p>
              )}
            </div>
          )}

          {/* Live firing badge */}
          <div className="absolute top-2 left-2 px-2.5 py-1 rounded-md bg-black/70 border border-purple-500/30 backdrop-blur flex items-center gap-1.5">
            <Activity className="w-3 h-3 text-purple-400 animate-pulse" />
            <span className="text-[9px] text-purple-400 font-mono uppercase tracking-widest">SYNAPSE FIRING</span>
          </div>
        </div>
      </div>

      {/* Stats below */}
      <div className="grid grid-cols-2 md:grid-cols-5 border-t border-white/[0.06]">
        {[
          { label: 'Canales activos', value: '14/14', color: '#3b82f6', icon: Globe },
          { label: 'Agentes online', value: '23/23', color: '#a855f7', icon: Brain },
          { label: 'Decisiones/min', value: '23', color: '#ec4899', icon: Zap },
          { label: 'Latencia avg', value: '180ms', color: '#06b6d4', icon: Activity },
          { label: 'Uptime', value: '99.97%', color: '#22c55e', icon: CheckCircle2 },
        ].map((s, i) => {
          const Icon = s.icon
          return (
            <div key={s.label} className="p-3 border-r border-white/[0.04] last:border-r-0">
              <div className="flex items-center gap-1.5 mb-1">
                <Icon className="w-3 h-3" style={{ color: s.color }} />
                <p className="text-[9px] uppercase tracking-widest text-white/40 font-bold truncate">{s.label}</p>
              </div>
              <p className="text-lg font-black text-white tabular-nums">{s.value}</p>
            </div>
          )
        })}
      </div>

      <style jsx>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.3; }
          50% { opacity: 0.7; }
        }
      `}</style>
    </section>
  )
}
