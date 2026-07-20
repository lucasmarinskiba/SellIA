'use client'

/**
 * PLAYBOOK LIBRARY
 *
 * Workflows de Computer Use pre-construidos que orquestan múltiples plataformas
 * con 1 click. Cada playbook:
 *   - Define una secuencia de pasos en N plataformas
 *   - Tiempo estimado + éxito histórico
 *   - 1-click trigger (IA hace todo el resto)
 *
 * Categorías: Captación · Ventas · Marketing · Operaciones · Post-venta
 */

import { useState, useMemo } from 'react'
import {
  BookOpen, Play, Sparkles, Filter, Clock, Activity, Bot,
  Target, DollarSign, Megaphone, Cog, Heart, ChevronRight,
  Hash, CheckCircle2, Layers, Zap, Search, TrendingUp
} from 'lucide-react'

type Category = 'captacion' | 'ventas' | 'marketing' | 'ops' | 'postventa'

interface PlaybookStep {
  platform: string
  emoji: string
  action: string
}

interface Playbook {
  id: string
  emoji: string
  name: string
  description: string
  category: Category
  platforms: string[]
  steps: PlaybookStep[]
  avgMinutes: number
  successRate: number
  runsThisMonth: number
  lastRun?: string
  difficulty: 'easy' | 'medium' | 'pro'
  popular?: boolean
  outcome: string
}

const PLAYBOOKS: Playbook[] = [
  // ─── CAPTACIÓN ─────────────────────────────────────────────────
  {
    id: 'pb1', emoji: '🎯', name: 'Cold outreach LinkedIn ICP',
    description: 'Buscá 50 prospectos en LinkedIn que matchean tu ICP, mandales connection request personalizada + secuencia 3 toques',
    category: 'captacion',
    platforms: ['💼 LinkedIn', '📧 Email', '🤖 CRM'],
    steps: [
      { platform: 'LinkedIn', emoji: '💼', action: 'Sales Navigator search · filtrar 50 ICP' },
      { platform: 'LinkedIn', emoji: '💼', action: 'Connection request con nota personalizada IA' },
      { platform: 'LinkedIn', emoji: '💼', action: 'Mensaje 1 (valor) a quien acepta · 24h después' },
      { platform: 'Email', emoji: '📧', action: 'Encontrar email vía Apollo · enviar follow-up' },
      { platform: 'CRM', emoji: '🤖', action: 'Crear deal en stage Prospección · stage automático' },
    ],
    avgMinutes: 47, successRate: 68, runsThisMonth: 14, lastRun: 'Hoy 09:23',
    difficulty: 'easy', popular: true,
    outcome: '~12-18 conexiones aceptadas · 4-6 conversaciones · 1-3 deals nuevos',
  },
  {
    id: 'pb2', emoji: '💌', name: 'IG/TikTok DM funnel',
    description: 'Identifica 30 cuentas que comentaron en posts de competidores, mandales DM con hook + bonus + landing',
    category: 'captacion',
    platforms: ['📷 Instagram', '🎵 TikTok', '🌐 Web'],
    steps: [
      { platform: 'Instagram', emoji: '📷', action: 'Scrapping comentarios en 3 cuentas competencia' },
      { platform: 'Instagram', emoji: '📷', action: 'Filtrar 30 cuentas matchean ICP · IA evalúa bio' },
      { platform: 'Instagram', emoji: '📷', action: 'DM con hook personalizado + link bonus gratis' },
      { platform: 'TikTok', emoji: '🎵', action: 'Mismo flow paralelo en TikTok' },
      { platform: 'Web', emoji: '🌐', action: 'Pixel tracking · trigger secuencia email si entran' },
    ],
    avgMinutes: 28, successRate: 41, runsThisMonth: 8, lastRun: 'Ayer',
    difficulty: 'medium',
    outcome: '~8-12 respuestas · 3-5 visitas a landing · 1 venta',
  },
  {
    id: 'pb3', emoji: '🎙', name: 'Webinar funnel completo',
    description: 'Lanzá webinar: copy + landing + Ads multi-plataforma + recordatorios + seguimiento post',
    category: 'captacion',
    platforms: ['🌐 Web', '◼️ Meta Ads', '🎵 TikTok Ads', '📧 Email', '🔍 Google Ads'],
    steps: [
      { platform: 'Web', emoji: '🌐', action: 'Generar landing page con IA (Framer/Webflow)' },
      { platform: 'Meta Ads', emoji: '◼️', action: 'Lanzar campaña Lead Ads · 3 audiencias' },
      { platform: 'Google Ads', emoji: '🔍', action: 'Search + Display retargeting' },
      { platform: 'Email', emoji: '📧', action: 'Secuencia 5 emails recordatorio' },
      { platform: 'TikTok Ads', emoji: '🎵', action: 'Spark Ads desde reel orgánico' },
    ],
    avgMinutes: 124, successRate: 58, runsThisMonth: 2,
    difficulty: 'pro', popular: true,
    outcome: '~120 inscriptos · 60 asisten · 8-12 ventas en pitch',
  },

  // ─── VENTAS ────────────────────────────────────────────────────
  {
    id: 'pb4', emoji: '🚀', name: 'Lanzamiento multi-plataforma 24h',
    description: 'Lanzá un producto nuevo en simultáneo en Amazon, ML, Shopify, IG Shop, TikTok Shop, FB Shops',
    category: 'ventas',
    platforms: ['📦 Amazon', '🟡 ML', '🛍 Shopify', '🌸 IG Shop', '🎵 TT Shop', '🛒 FB Shops'],
    steps: [
      { platform: 'Amazon', emoji: '📦', action: 'Crear listing con título SEO + 7 imágenes + A+ content' },
      { platform: 'ML', emoji: '🟡', action: 'Publicación + ficha técnica · catálogo' },
      { platform: 'Shopify', emoji: '🛍', action: 'Producto + SEO meta + email anuncio a base' },
      { platform: 'IG Shop', emoji: '🌸', action: 'Catálogo sync + 3 reels + story con sticker producto' },
      { platform: 'TT Shop', emoji: '🎵', action: 'Listing + 5 videos showcase · trending sounds' },
      { platform: 'FB Shops', emoji: '🛒', action: 'Catálogo + post pagado · audiencia engaged' },
    ],
    avgMinutes: 187, successRate: 82, runsThisMonth: 1, lastRun: 'Hace 12 días',
    difficulty: 'pro', popular: true,
    outcome: 'Presencia 360° en 24hs · primera venta promedio en 4hs',
  },
  {
    id: 'pb5', emoji: '📺', name: 'Live Shopping TikTok',
    description: 'Setup completo de live shopping: banner, OBS, productos pinneados, modera DM, sincroniza con CRM',
    category: 'ventas',
    platforms: ['🎵 TikTok Shop', '🤖 CRM', '💬 WhatsApp'],
    steps: [
      { platform: 'TikTok Shop', emoji: '🎵', action: 'Schedule live + banner generado IA' },
      { platform: 'TikTok Shop', emoji: '🎵', action: 'Pin productos por orden de prioridad' },
      { platform: 'TikTok Shop', emoji: '🎵', action: 'Modera comentarios + responde objeciones live' },
      { platform: 'CRM', emoji: '🤖', action: 'Cada compra → deal + customer auto-creado' },
      { platform: 'WhatsApp', emoji: '💬', action: 'Mensaje gracias + tracking en 5min post-compra' },
    ],
    avgMinutes: 90, successRate: 71, runsThisMonth: 3, lastRun: 'Anteayer',
    difficulty: 'medium',
    outcome: '~200-500 viewers · 8-15 ventas durante live · ticket avg $89',
  },
  {
    id: 'pb6', emoji: '🛒', name: 'Cart recovery agresivo 5 toques',
    description: 'Recuperá carritos abandonados con secuencia: email → WhatsApp → IG DM → bonus → urgencia',
    category: 'ventas',
    platforms: ['🛍 Shopify', '📧 Email', '💬 WhatsApp', '📷 Instagram'],
    steps: [
      { platform: 'Shopify', emoji: '🛍', action: 'Detectar carrito abandonado >1h' },
      { platform: 'Email', emoji: '📧', action: 'Email recordatorio amable + producto' },
      { platform: 'WhatsApp', emoji: '💬', action: '24h después: WhatsApp con 10% off bonus' },
      { platform: 'Instagram', emoji: '📷', action: '48h: IG DM con UGC + caso éxito' },
      { platform: 'Email', emoji: '📧', action: '72h: último intento + urgencia "stock low"' },
    ],
    avgMinutes: 0, successRate: 47, runsThisMonth: 47,
    difficulty: 'easy', popular: true,
    outcome: '~47% recovery rate · running auto · sin tu intervención',
  },

  // ─── MARKETING ────────────────────────────────────────────────
  {
    id: 'pb7', emoji: '📝', name: 'Content blast 7 plataformas',
    description: 'Un brief = 7 piezas de contenido optimizadas: reel + carrusel + story + tweet + LinkedIn post + blog + email',
    category: 'marketing',
    platforms: ['📷 Instagram', '🎵 TikTok', '👍 Facebook', '💼 LinkedIn', '🌐 Web', '📧 Email'],
    steps: [
      { platform: 'AI Brain', emoji: '🧠', action: 'Procesar brief + investigar topic + 8 hooks' },
      { platform: 'Instagram', emoji: '📷', action: 'Reel 30s con script + edición + thumbnail' },
      { platform: 'TikTok', emoji: '🎵', action: 'Variante TikTok con trending sound' },
      { platform: 'LinkedIn', emoji: '💼', action: 'Post thought leadership + carrusel' },
      { platform: 'Web', emoji: '🌐', action: 'Blog post 1.5k palabras SEO-optimizado' },
      { platform: 'Email', emoji: '📧', action: 'Newsletter con highlight + CTA' },
    ],
    avgMinutes: 38, successRate: 89, runsThisMonth: 21,
    difficulty: 'easy', popular: true,
    outcome: '7 piezas optimizadas por plataforma · publicación programada',
  },
  {
    id: 'pb8', emoji: '🔍', name: 'SEO boost producto',
    description: 'Auditá + optimizá una product page para Top 10 Google: meta, schema, backlinks, contenido relacionado',
    category: 'marketing',
    platforms: ['🌐 Web', '🔍 Google Search Console', '📊 Analytics'],
    steps: [
      { platform: 'Search Console', emoji: '🔍', action: 'Análisis keywords actuales + competidores' },
      { platform: 'Web', emoji: '🌐', action: 'Reescribir meta + title + schema product' },
      { platform: 'Web', emoji: '🌐', action: 'Crear 3 artículos blog interlinked' },
      { platform: 'Web', emoji: '🌐', action: 'Outreach a 12 sitios para backlinks' },
      { platform: 'Analytics', emoji: '📊', action: 'Trackear movement semanal · alerta si baja' },
    ],
    avgMinutes: 67, successRate: 64, runsThisMonth: 4,
    difficulty: 'pro',
    outcome: 'Movement promedio +15 posiciones en 30 días',
  },
  {
    id: 'pb9', emoji: '📊', name: 'Ads optimization sweep',
    description: 'Pasada completa sobre Meta + Google + TikTok Ads: pausa lo malo, escala lo bueno, prueba 5 creatives nuevos',
    category: 'marketing',
    platforms: ['◼️ Meta Ads', '🔍 Google Ads', '🎵 TikTok Ads'],
    steps: [
      { platform: 'Meta', emoji: '◼️', action: 'Pausar campañas ROAS <1 · escalar 30% ROAS >3' },
      { platform: 'Google', emoji: '🔍', action: 'Negative keywords + bid adjustments' },
      { platform: 'TikTok', emoji: '🎵', action: 'Spark Ads desde top 3 reels orgánicos' },
      { platform: 'Meta', emoji: '◼️', action: 'Crear 5 nuevos creatives con UGC' },
      { platform: 'All', emoji: '⚡', action: 'Setup automatic rules para auto-pause low ROAS' },
    ],
    avgMinutes: 42, successRate: 76, runsThisMonth: 8, lastRun: 'Hoy 11:14',
    difficulty: 'medium', popular: true,
    outcome: 'ROAS promedio sube 25-40% · ad fatigue reducido',
  },

  // ─── OPERACIONES ──────────────────────────────────────────────
  {
    id: 'pb10', emoji: '🧾', name: 'Factura AFIP + envío post-venta',
    description: 'Post-pago: genera factura AFIP automática, coordina courier, envía tracking, agenda follow-up',
    category: 'ops',
    platforms: ['🧾 AFIP', '📮 Andreani', '💬 WhatsApp', '📧 Email', '📅 Calendar'],
    steps: [
      { platform: 'AFIP', emoji: '🧾', action: 'Login portal AFIP · emitir Factura A · CAE' },
      { platform: 'Andreani', emoji: '📮', action: 'Generar guía + retiro · agendar' },
      { platform: 'WhatsApp', emoji: '💬', action: 'Enviar factura PDF + tracking al cliente' },
      { platform: 'Email', emoji: '📧', action: 'Email con factura + survey NPS post-entrega' },
      { platform: 'Calendar', emoji: '📅', action: 'Recordatorio en 7d para upsell' },
    ],
    avgMinutes: 0, successRate: 98, runsThisMonth: 87,
    difficulty: 'easy', popular: true,
    outcome: 'Run auto cada venta · 0 fricción cliente · NPS 9.2',
  },
  {
    id: 'pb11', emoji: '🔄', name: 'Reposición automática stock',
    description: 'Detecta stock crítico, evalúa supplier mejor precio, genera orden de compra, agenda recepción',
    category: 'ops',
    platforms: ['📊 Inventory', '📧 Email', '💼 Suppliers'],
    steps: [
      { platform: 'Inventory', emoji: '📊', action: 'Scan diario · detectar SKUs bajo umbral' },
      { platform: 'Suppliers', emoji: '💼', action: 'Comparar 3 proveedores · mejor precio + ETA' },
      { platform: 'Email', emoji: '📧', action: 'Enviar PO al supplier elegido' },
      { platform: 'Calendar', emoji: '📅', action: 'Bloquear día de recepción · alerta' },
    ],
    avgMinutes: 0, successRate: 95, runsThisMonth: 4,
    difficulty: 'easy',
    outcome: 'Run auto · 0 stockouts en últimos 90d',
  },
  {
    id: 'pb12', emoji: '💸', name: 'Reconciliación pagos diaria',
    description: 'Cruza ventas de ML + Shopify + MercadoPago con tu CRM y banco. Detecta discrepancias',
    category: 'ops',
    platforms: ['🟡 ML', '🛍 Shopify', '💳 MercadoPago', '🏦 Banco', '🤖 CRM'],
    steps: [
      { platform: 'ML', emoji: '🟡', action: 'Export ventas día' },
      { platform: 'Shopify', emoji: '🛍', action: 'Export órdenes pagas' },
      { platform: 'MercadoPago', emoji: '💳', action: 'Movimientos día' },
      { platform: 'Banco', emoji: '🏦', action: 'Conciliar con extracto bancario' },
      { platform: 'CRM', emoji: '🤖', action: 'Marcar deals "pagado verified"' },
    ],
    avgMinutes: 0, successRate: 99, runsThisMonth: 22,
    difficulty: 'easy',
    outcome: 'Run auto 23:00 cada día · alerta si discrepancia',
  },

  // ─── POST-VENTA ───────────────────────────────────────────────
  {
    id: 'pb13', emoji: '🎁', name: 'Onboarding kickoff 48hs',
    description: 'Cliente nuevo → bienvenida + tutorial + sesión 1:1 agendada + comunidad Discord/Telegram',
    category: 'postventa',
    platforms: ['📧 Email', '💬 WhatsApp', '📅 Calendly', '🎙 Discord'],
    steps: [
      { platform: 'Email', emoji: '📧', action: 'Welcome email + video onboarding personalizado' },
      { platform: 'WhatsApp', emoji: '💬', action: 'Mensaje + link al tutorial paso a paso' },
      { platform: 'Calendly', emoji: '📅', action: 'Auto-agendar sesión 1:1 según disponibilidad' },
      { platform: 'Discord', emoji: '🎙', action: 'Invitación + assign rol · presentación auto' },
      { platform: 'Email', emoji: '📧', action: 'Check-in 48hs · "¿cómo va?"' },
    ],
    avgMinutes: 0, successRate: 92, runsThisMonth: 12, lastRun: 'Hoy 10:42',
    difficulty: 'easy', popular: true,
    outcome: 'Primera victoria en 48hs · NPS inicial 8.7 · 0% churn primeros 30d',
  },
  {
    id: 'pb14', emoji: '⭐', name: 'NPS survey + testimonio',
    description: 'NPS automático · si responde 9-10 pide testimonio + referido · si 7-8 mejora · si <7 escala a vos',
    category: 'postventa',
    platforms: ['📧 Email', '💬 WhatsApp', '🎬 Video tool'],
    steps: [
      { platform: 'Email', emoji: '📧', action: 'Survey NPS 1 pregunta · día 30 post-venta' },
      { platform: 'WhatsApp', emoji: '💬', action: 'Si NPS 9-10: pedir testimonio en video' },
      { platform: 'Video', emoji: '🎬', action: 'Si acepta: link grabación Loom 60s' },
      { platform: 'WhatsApp', emoji: '💬', action: 'Si 7-8: "¿qué te haría darnos un 10?"' },
      { platform: 'Email', emoji: '📧', action: 'Si <7: escalar a CEO · llamada urgente' },
    ],
    avgMinutes: 0, successRate: 87, runsThisMonth: 23,
    difficulty: 'easy',
    outcome: '~14 testimonios/mes · 8 referidos · churn anticipado salvado',
  },
  {
    id: 'pb15', emoji: '♻️', name: 'Reorder push clientes loyal',
    description: 'Detecta clientes con LTV alto que no recompraron en 60d. IA crea oferta personalizada por canal preferido',
    category: 'postventa',
    platforms: ['🤖 CRM', '💬 WhatsApp', '📧 Email'],
    steps: [
      { platform: 'CRM', emoji: '🤖', action: 'Filtrar Loyal+ tier sin compra 60d' },
      { platform: 'CRM', emoji: '🤖', action: 'IA arma oferta personalizada según histórico' },
      { platform: 'WhatsApp', emoji: '💬', action: 'Mensaje cálido + oferta exclusiva' },
      { platform: 'Email', emoji: '📧', action: 'Backup email si no responde 48hs' },
    ],
    avgMinutes: 0, successRate: 54, runsThisMonth: 6,
    difficulty: 'easy',
    outcome: '~54% recompra dentro de 7 días · revenue easy recovery',
  },
]

const CATEGORY_CONFIG: Record<Category, { label: string; emoji: string; icon: React.ElementType; color: string }> = {
  captacion:  { label: 'Captación',  emoji: '🎯', icon: Target,    color: '#3b82f6' },
  ventas:     { label: 'Ventas',     emoji: '💰', icon: DollarSign,color: '#22c55e' },
  marketing:  { label: 'Marketing',  emoji: '📢', icon: Megaphone, color: '#ec4899' },
  ops:        { label: 'Operaciones',emoji: '⚙️', icon: Cog,       color: '#a855f7' },
  postventa:  { label: 'Post-venta', emoji: '❤️', icon: Heart,     color: '#fbbf24' },
}

const DIFFICULTY_CONFIG = {
  easy:   { label: 'Easy',    color: '#22c55e' },
  medium: { label: 'Medium',  color: '#f59e0b' },
  pro:    { label: 'Pro',     color: '#ef4444' },
} as const

export default function PlaybookLibrary() {
  const [filter, setFilter] = useState<Category | 'all' | 'popular'>('all')
  const [search, setSearch] = useState('')
  const [expandedId, setExpandedId] = useState<string | null>(PLAYBOOKS[0]?.id || null)

  const filtered = useMemo(() => {
    let list = PLAYBOOKS
    if (filter === 'popular') list = list.filter(p => p.popular)
    else if (filter !== 'all') list = list.filter(p => p.category === filter)
    if (search) {
      const q = search.toLowerCase()
      list = list.filter(p =>
        p.name.toLowerCase().includes(q) ||
        p.description.toLowerCase().includes(q) ||
        p.platforms.some(pl => pl.toLowerCase().includes(q))
      )
    }
    return list
  }, [filter, search])

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: PLAYBOOKS.length, popular: PLAYBOOKS.filter(p => p.popular).length }
    for (const p of PLAYBOOKS) c[p.category] = (c[p.category] || 0) + 1
    return c
  }, [])

  const stats = useMemo(() => ({
    totalRuns: PLAYBOOKS.reduce((s, p) => s + p.runsThisMonth, 0),
    avgSuccess: PLAYBOOKS.reduce((s, p) => s + p.successRate, 0) / PLAYBOOKS.length,
    autoRunning: PLAYBOOKS.filter(p => p.avgMinutes === 0).length,
  }), [])

  return (
    <section className="relative rounded-2xl border border-orange-500/20 bg-gradient-to-br from-[#1a0f08]/40 via-[#0a0e1a]/85 to-[#0a0e1a]/95 backdrop-blur overflow-hidden">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-orange-400/80 via-amber-400/60 to-transparent" />

      {/* Header */}
      <div className="px-5 py-4 border-b border-white/[0.06] flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500/25 to-amber-500/15 border border-orange-500/40 flex items-center justify-center">
            <BookOpen className="w-5 h-5 text-orange-400" style={{ filter: 'drop-shadow(0 0 8px rgba(251,146,60,0.7))' }} />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 flex-wrap">
              <span className="bg-gradient-to-r from-orange-400 to-amber-400 bg-clip-text text-transparent">PLAYBOOK LIBRARY</span>
              <span className="text-white/40 font-light normal-case tracking-normal">·  {PLAYBOOKS.length} workflows · 1-click trigger</span>
            </h2>
            <p className="text-[11px] text-white/40 mt-0.5">Recetas pre-construidas. Cada una orquesta Computer Use en múltiples plataformas</p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <div className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/25 flex items-center gap-1.5">
            <Activity className="w-3 h-3 text-emerald-400 animate-pulse" />
            <span className="text-xs text-emerald-400 font-bold">{stats.autoRunning} auto-running</span>
          </div>
          <div className="px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06]">
            <span className="text-[10px] text-white/40">Ejecuciones mes: </span>
            <span className="text-xs text-white font-bold">{stats.totalRuns}</span>
          </div>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 border-b border-white/[0.06]">
        <div className="p-3 border-r border-white/[0.04]">
          <div className="flex items-center gap-1.5 mb-1">
            <Layers className="w-3 h-3 text-orange-400" />
            <p className="text-[9px] uppercase tracking-widest text-white/40 font-bold">Workflows disponibles</p>
          </div>
          <p className="text-xl font-black text-white tabular-nums">{PLAYBOOKS.length}</p>
          <p className="text-[9px] text-white/40">en 5 categorías</p>
        </div>
        <div className="p-3 border-r border-white/[0.04]">
          <div className="flex items-center gap-1.5 mb-1">
            <TrendingUp className="w-3 h-3 text-emerald-400" />
            <p className="text-[9px] uppercase tracking-widest text-white/40 font-bold">Éxito promedio</p>
          </div>
          <p className="text-xl font-black text-emerald-400 tabular-nums">{stats.avgSuccess.toFixed(0)}%</p>
          <p className="text-[9px] text-white/40">histórico</p>
        </div>
        <div className="p-3">
          <div className="flex items-center gap-1.5 mb-1">
            <Zap className="w-3 h-3 text-amber-400" />
            <p className="text-[9px] uppercase tracking-widest text-white/40 font-bold">Plataformas integradas</p>
          </div>
          <p className="text-xl font-black text-amber-400 tabular-nums">23</p>
          <p className="text-[9px] text-white/40">Amazon, ML, IG, TT, Meta, Google, AFIP, ...</p>
        </div>
      </div>

      {/* Filters + search */}
      <div className="px-5 py-3 border-b border-white/[0.06] space-y-2">
        <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
          <Filter className="w-3 h-3 text-white/30 shrink-0" />
          <button
            onClick={() => setFilter('all')}
            className={`shrink-0 px-3 py-1 rounded-full text-[10px] font-bold border transition-all ${
              filter === 'all' ? 'bg-white/10 border-white/20 text-white' : 'bg-white/[0.02] border-white/[0.06] text-white/40'
            }`}
          >
            Todos · {counts.all}
          </button>
          <button
            onClick={() => setFilter('popular')}
            className={`shrink-0 flex items-center gap-1 px-3 py-1 rounded-full text-[10px] font-bold border transition-all ${
              filter === 'popular' ? 'bg-amber-500/20 border-amber-500/50 text-amber-400' : 'bg-white/[0.02] border-white/[0.06] text-white/40'
            }`}
          >
            ⭐ Populares · {counts.popular}
          </button>
          {(Object.keys(CATEGORY_CONFIG) as Category[]).map(cat => {
            const cfg = CATEGORY_CONFIG[cat]
            const Icon = cfg.icon
            const active = filter === cat
            const count = counts[cat] || 0
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
                <Icon className="w-2.5 h-2.5" />
                {cfg.label} · {count}
              </button>
            )
          })}
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3 h-3 text-white/30" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Buscar playbook... ej: 'Amazon', 'WhatsApp', 'recovery'"
            className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06] text-xs text-white placeholder:text-white/20 focus:outline-none focus:border-orange-500/40"
          />
        </div>
      </div>

      {/* Playbooks grid */}
      <div className="p-3 space-y-2">
        {filtered.length === 0 ? (
          <div className="py-12 text-center text-white/30 text-xs">
            Sin playbooks que coincidan
          </div>
        ) : (
          filtered.map(pb => {
            const cfg = CATEGORY_CONFIG[pb.category]
            const diff = DIFFICULTY_CONFIG[pb.difficulty]
            const isExpanded = expandedId === pb.id
            const isAuto = pb.avgMinutes === 0
            return (
              <div key={pb.id} className="rounded-xl border bg-white/[0.02] overflow-hidden transition-all"
                style={{ borderColor: isExpanded ? `${cfg.color}40` : 'rgba(255,255,255,0.06)' }}>
                <button
                  onClick={() => setExpandedId(isExpanded ? null : pb.id)}
                  className="w-full flex items-start gap-3 p-3 text-left hover:bg-white/[0.02] transition-colors"
                >
                  <div className="text-3xl shrink-0 mt-0.5">{pb.emoji}</div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <p className="text-sm font-bold text-white">{pb.name}</p>
                      {pb.popular && (
                        <span className="text-[9px] px-1.5 py-0.5 rounded font-mono uppercase bg-amber-500/15 text-amber-400 border border-amber-500/30">
                          ⭐ POPULAR
                        </span>
                      )}
                      <span className="text-[9px] px-1.5 py-0.5 rounded font-mono uppercase tracking-wider" style={{ background: `${cfg.color}20`, color: cfg.color }}>
                        {cfg.label}
                      </span>
                      <span className="text-[9px] px-1.5 py-0.5 rounded font-mono uppercase" style={{ background: `${diff.color}15`, color: diff.color }}>
                        {diff.label}
                      </span>
                      {isAuto && (
                        <span className="text-[9px] px-1.5 py-0.5 rounded font-mono uppercase bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                          <div className="w-1 h-1 rounded-full bg-emerald-400 animate-pulse" />
                          AUTO
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-white/60 leading-snug mb-1.5 line-clamp-2">{pb.description}</p>

                    {/* Platforms involved */}
                    <div className="flex items-center gap-1 mb-1.5 flex-wrap">
                      {pb.platforms.map((pl, i) => (
                        <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-white/[0.04] border border-white/[0.06] text-white/60">
                          {pl}
                        </span>
                      ))}
                    </div>

                    {/* Bottom stats */}
                    <div className="flex items-center gap-3 text-[10px] text-white/40">
                      <span className="flex items-center gap-1">
                        <Clock className="w-2.5 h-2.5" />
                        {isAuto ? 'Auto-loop' : `~${pb.avgMinutes}min`}
                      </span>
                      <span className="flex items-center gap-1">
                        <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400" />
                        <span className="text-emerald-400 font-bold">{pb.successRate}%</span> éxito
                      </span>
                      <span>·  {pb.runsThisMonth} runs/mes</span>
                      {pb.lastRun && (
                        <span className="hidden md:inline">·  Last: {pb.lastRun}</span>
                      )}
                    </div>
                  </div>

                  {/* Trigger button */}
                  <button
                    onClick={(e) => { e.stopPropagation(); /* trigger logic */ }}
                    className="shrink-0 flex items-center gap-1.5 px-3 py-2 rounded-lg font-bold text-[11px] transition-all hover:scale-105"
                    style={{ background: `${cfg.color}20`, border: `1px solid ${cfg.color}50`, color: cfg.color, boxShadow: `0 0 12px ${cfg.color}20` }}
                  >
                    <Play className="w-3 h-3" />
                    <span>Ejecutar</span>
                  </button>

                  <ChevronRight className={`w-4 h-4 text-white/30 mt-2 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                </button>

                {/* Expanded: full steps + outcome */}
                {isExpanded && (
                  <div className="px-3 pb-3 border-t border-white/[0.04]">
                    {/* Steps */}
                    <p className="text-[9px] uppercase tracking-widest text-white/40 font-bold mt-3 mb-2 flex items-center gap-1">
                      <Bot className="w-2.5 h-2.5" />
                      SECUENCIA COMPUTER USE
                    </p>
                    <div className="space-y-1.5 relative">
                      {/* Vertical connector */}
                      <div className="absolute left-[10px] top-2 bottom-2 w-px" style={{ background: `${cfg.color}30` }} />
                      {pb.steps.map((s, i) => (
                        <div key={i} className="relative flex items-start gap-2 pl-1">
                          <div className="w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold shrink-0 z-10"
                            style={{ background: `${cfg.color}25`, border: `1px solid ${cfg.color}50`, color: cfg.color }}>
                            {i + 1}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-1.5 mb-0.5">
                              <span>{s.emoji}</span>
                              <span className="text-[10px] font-bold uppercase tracking-wider text-white/60">{s.platform}</span>
                            </div>
                            <p className="text-[11px] text-white/85 leading-snug">{s.action}</p>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Outcome */}
                    <div className="mt-3 p-2.5 rounded-lg bg-emerald-500/[0.06] border border-emerald-500/20">
                      <div className="flex items-start gap-2">
                        <Sparkles className="w-3 h-3 text-emerald-400 shrink-0 mt-0.5" />
                        <div>
                          <p className="text-[9px] uppercase tracking-widest text-emerald-400 font-bold mb-0.5">RESULTADO ESPERADO</p>
                          <p className="text-[11px] text-white/85">{pb.outcome}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>

      {/* Footer */}
      <div className="px-5 py-3 border-t border-white/[0.06] bg-purple-500/[0.04] flex items-center gap-3">
        <Sparkles className="w-4 h-4 text-purple-400 shrink-0" />
        <p className="text-[11px] text-white/70 leading-snug">
          <span className="text-purple-400 font-bold">¿No encontrás tu workflow?</span> Decile a SellIA &quot;Hola, creame un playbook para...&quot; y la IA arma la secuencia personalizada para tu negocio.
        </p>
      </div>
    </section>
  )
}
