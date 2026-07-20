/**
 * Perfil de negocio del usuario — qué vende, dónde vende, dónde se anuncia,
 * dónde sube contenido (+ links reales). Alimenta el cerebro, el mapa de
 * interacciones y Computer Use para que SellIA opere sobre las plataformas
 * reales del usuario.
 *
 * Persistencia: localStorage (cliente) + opcional backend (Business.config JSONB).
 */

import { type Strategy, relevantStrategies } from '@/lib/growth-strategies'
import { TOOL_BY_ID, accountUrlFor } from '@/lib/tools-catalog'

export interface LinkEntry { id: string; label: string; url: string; enabled: boolean }
export type CustomLinkType = 'venta' | 'perfil' | 'web'
export interface CustomLink { id: string; label: string; url: string; type: CustomLinkType; enabled: boolean }

export interface BusinessProfile {
  // qué vende
  bizType: 'producto' | 'servicio' | 'ambos' | ''
  productDesc: string
  industry: string
  ticket: string            // rango de ticket promedio
  audience: string
  // qué ofrece
  offer: string
  valueProp: string
  goals: string[]           // leads | ventas | branding | retencion | contenido | escalar
  // dónde
  salesPlatforms: LinkEntry[]   // ML, Amazon, Shopify, web…
  adPlatforms: LinkEntry[]      // Meta Ads, Google Ads…
  socialLinks: LinkEntry[]      // TikTok, IG, FB, X…
  customLinks: CustomLink[]     // cualquier link: venta/perfil/web (Beacons, Linktree, Lovable, Vercel…)
  channels: string[]            // whatsapp, email, telegram, webchat
  updatedAt?: string
}

export const SALES_PLATFORMS: Array<{ id: string; label: string }> = [
  { id: 'mercadolibre', label: 'Mercado Libre' },
  { id: 'amazon', label: 'Amazon' },
  { id: 'shopify', label: 'Shopify' },
  { id: 'tiendanube', label: 'Tienda Nube' },
  { id: 'woocommerce', label: 'WooCommerce' },
  { id: 'hotmart', label: 'Hotmart' },
  { id: 'web', label: 'Web propia' },
]

export const AD_PLATFORMS: Array<{ id: string; label: string }> = [
  { id: 'meta_ads', label: 'Meta Ads (FB/IG)' },
  { id: 'google_ads', label: 'Google Ads' },
  { id: 'tiktok_ads', label: 'TikTok Ads' },
  { id: 'linkedin_ads', label: 'LinkedIn Ads' },
]

export const SOCIAL_PLATFORMS: Array<{ id: string; label: string; host?: string }> = [
  { id: 'tiktok', label: 'TikTok', host: 'tiktok.com' },
  { id: 'instagram', label: 'Instagram', host: 'instagram.com' },
  { id: 'facebook', label: 'Facebook', host: 'facebook.com' },
  { id: 'twitter', label: 'X (Twitter)', host: 'x.com' },
  { id: 'youtube', label: 'YouTube', host: 'youtube.com' },
  { id: 'linkedin', label: 'LinkedIn', host: 'linkedin.com' },
  { id: 'pinterest', label: 'Pinterest', host: 'pinterest.com' },
  { id: 'threads', label: 'Threads', host: 'threads.net' },
  { id: 'github', label: 'GitHub', host: 'github.com' },
  { id: 'linktree', label: 'Linktree', host: 'linktr.ee' },
  { id: 'beacons', label: 'Beacons', host: 'beacons.ai' },
  { id: 'canva', label: 'Canva', host: 'canva.com' },
  { id: 'manychat', label: 'ManyChat', host: 'manychat.com' },
]

export const CHANNELS: Array<{ id: string; label: string }> = [
  { id: 'whatsapp', label: 'WhatsApp' },
  { id: 'email', label: 'Email' },
  { id: 'telegram', label: 'Telegram' },
  { id: 'webchat', label: 'Chat web' },
]

export const GOALS: Array<{ id: string; label: string }> = [
  { id: 'leads', label: 'Generar leads' },
  { id: 'ventas', label: 'Más ventas' },
  { id: 'retencion', label: 'Retención/recompra' },
  { id: 'branding', label: 'Marca/posicionamiento' },
  { id: 'contenido', label: 'Contenido/redes' },
  { id: 'escalar', label: 'Escalar/automatizar' },
]

const KEY = 'sellia_business_profile_v1'

export const emptyProfile = (): BusinessProfile => ({
  bizType: '', productDesc: '', industry: '', ticket: '', audience: '',
  offer: '', valueProp: '', goals: [],
  salesPlatforms: SALES_PLATFORMS.map(p => ({ id: p.id, label: p.label, url: '', enabled: false })),
  adPlatforms: AD_PLATFORMS.map(p => ({ id: p.id, label: p.label, url: '', enabled: false })),
  socialLinks: SOCIAL_PLATFORMS.map(p => ({ id: p.id, label: p.label, url: '', enabled: false })),
  customLinks: [],
  channels: [],
})

const VENTA_HOSTS = ['mercadolibre', 'amazon', 'hotmart', 'shopify', 'tiendanube', 'etsy', 'ebay', 'woocommerce', 'gumroad', 'tienda']
const PERFIL_HOSTS = ['instagram', 'tiktok', 'x.com', 'twitter', 'facebook', 'youtube', 'linkedin', 'threads.net', 'pinterest']

/** Autodetecta el tipo de un link por su dominio. */
export const detectLinkType = (url: string): CustomLinkType => {
  const h = (() => { try { return new URL(url.startsWith('http') ? url : `https://${url}`).hostname.toLowerCase() } catch { return '' } })()
  if (VENTA_HOSTS.some(k => h.includes(k))) return 'venta'
  if (PERFIL_HOSTS.some(k => h.includes(k))) return 'perfil'
  return 'web' // linktr.ee, beacons.ai, *.vercel.app, lovable, sitio propio, etc.
}

/** Sugiere un label legible desde el host. */
export const labelFromUrl = (url: string): string => {
  try { return new URL(url.startsWith('http') ? url : `https://${url}`).hostname.replace(/^www\./, '') } catch { return 'Link' }
}

export const loadProfile = (): BusinessProfile | null => {
  try {
    const s = typeof window !== 'undefined' ? localStorage.getItem(KEY) : null
    return s ? (JSON.parse(s) as BusinessProfile) : null
  } catch { return null }
}

export const saveProfile = (p: BusinessProfile): void => {
  try {
    localStorage.setItem(KEY, JSON.stringify({ ...p, updatedAt: new Date().toISOString() }))
  } catch { /* ignore */ }
}

/** Mínimo para considerar el perfil "completo": qué vende + 1 objetivo + 1 plataforma o red con link. */
export const isComplete = (p: BusinessProfile | null): boolean => {
  if (!p) return false
  const hasWhat = !!p.bizType && p.productDesc.trim().length > 3
  const hasGoal = p.goals.length > 0
  const anyLink = [...p.salesPlatforms, ...p.adPlatforms, ...p.socialLinks, ...(p.customLinks ?? [])]
    .some(l => l.enabled && validateLink(l.url).ok)
  return hasWhat && hasGoal && anyLink
}

export interface LinkCheck { ok: boolean; reason: string }

export const validateLink = (url: string, host?: string): LinkCheck => {
  const u = (url || '').trim()
  if (!u) return { ok: false, reason: 'vacío' }
  let parsed: URL
  try { parsed = new URL(u.startsWith('http') ? u : `https://${u}`) }
  catch { return { ok: false, reason: 'URL inválida' } }
  if (!/^https?:$/.test(parsed.protocol)) return { ok: false, reason: 'protocolo inválido' }
  if (host && !parsed.hostname.toLowerCase().includes(host)) {
    return { ok: false, reason: `se esperaba ${host}` }
  }
  return { ok: true, reason: 'OK' }
}

export interface Recommendation {
  id: string
  title: string
  kind: 'automation' | 'tool' | 'agent'
  reason: string
}

/** Recomienda flujos/herramientas/agentes según el perfil (reusa la lógica de buildTaskPlan). */
export const recommendFlows = (p: BusinessProfile | null): Recommendation[] => {
  if (!p) return []
  const out: Recommendation[] = []
  const has = (arr: LinkEntry[], id: string): boolean => arr.some(l => l.id === id && l.enabled)
  const anySocial = p.socialLinks.some(l => l.enabled)
  const anySales = p.salesPlatforms.some(l => l.enabled)
  const goal = (g: string): boolean => p.goals.includes(g)

  if (p.channels.includes('whatsapp'))
    out.push({ id: 'wa_bot_247', title: 'Bot WhatsApp 24/7', kind: 'automation', reason: 'Tenés WhatsApp como canal.' })
  if (anySales)
    out.push({ id: 'inventory_sync', title: 'Sincronía de inventario', kind: 'automation', reason: 'Vendés en marketplaces/tienda.' })
  if (has(p.salesPlatforms, 'mercadolibre') || has(p.salesPlatforms, 'amazon'))
    out.push({ id: 'review_responder', title: 'Gestor de reseñas', kind: 'automation', reason: 'Marketplace cargado.' })
  if (has(p.adPlatforms, 'meta_ads'))
    out.push({ id: 'meta_ads_optimizer', title: 'Optimizador Meta Ads', kind: 'automation', reason: 'Te anunciás en Meta.' })
  if (has(p.adPlatforms, 'google_ads'))
    out.push({ id: 'google_ads_optimizer', title: 'Optimizador Google Ads', kind: 'automation', reason: 'Te anunciás en Google.' })
  if (has(p.adPlatforms, 'tiktok_ads'))
    out.push({ id: 'tiktok_ads_optimizer', title: 'Optimizador TikTok Ads', kind: 'automation', reason: 'Te anunciás en TikTok.' })
  if (p.socialLinks.some(l => l.id === 'tiktok' && l.enabled))
    out.push({ id: 'tiktok_promo', title: 'Promocionar en TikTok', kind: 'tool', reason: 'Tenés perfil de TikTok.' })
  if (anySocial || goal('contenido') || goal('branding'))
    out.push({ id: 'social_content', title: 'Contenido social diario', kind: 'automation', reason: 'Subís contenido a redes.' })
  if (goal('leads'))
    out.push({ id: 'lead_scoring', title: 'Lead scoring', kind: 'tool', reason: 'Objetivo: generar leads.' })
  if (goal('retencion') || anySales)
    out.push({ id: 'cart_recovery', title: 'Recuperación de carritos', kind: 'automation', reason: 'Retención / ventas online.' })
  if (goal('escalar') || goal('ventas'))
    out.push({ id: 'crm_sync', title: 'CRM + pipeline', kind: 'tool', reason: 'Escalar y ordenar ventas.' })
  if (anySocial)
    out.push({ id: 'copy_gen', title: 'Generador de copy', kind: 'tool', reason: 'Producir posts/anuncios.' })
  if (anySocial || goal('contenido') || goal('branding') || p.socialLinks.some(l => l.id === 'canva' && l.enabled))
    out.push({ id: 'canva_create', title: 'Crea con Canva', kind: 'tool', reason: 'Diseñá piezas de tu marca.' })
  // ManyChat: filtrar leads malos (si hay IG/FB/WA o ManyChat conectado, o objetivo de leads/ventas)
  if (p.socialLinks.some(l => ['manychat', 'instagram', 'facebook'].includes(l.id) && l.enabled) || p.channels.includes('whatsapp') || goal('leads') || goal('ventas'))
    out.push({ id: 'manychat_qualify', title: 'ManyChat: filtrar leads malos', kind: 'automation', reason: 'Filtrá leads que nunca van a comprar.' })
  // Captación inteligente: siempre que el objetivo sea leads/ventas/escalar
  if (goal('leads') || goal('ventas') || goal('escalar'))
    out.push({ id: 'lead_capture', title: 'Captación inteligente de leads', kind: 'automation', reason: 'Capturá y calificá leads desde todos tus canales.' })
  // Brief → campaña: si te anunciás o querés leads/ventas
  if (p.adPlatforms.some(l => l.enabled) || goal('leads') || goal('ventas') || goal('branding'))
    out.push({ id: 'brief_to_campaign', title: 'Brief → Campaña de marketing', kind: 'agent', reason: 'Brief simple → campaña 360°.' })
  // Identidad de marca: si el objetivo es branding o no hay marca clara aún
  if (goal('branding') || goal('contenido') || !p.valueProp)
    out.push({ id: 'brand_identity', title: 'Generador de identidad de marca', kind: 'agent', reason: 'Construí tu identidad de marca.' })
  // Vender lo invendible: siempre disponible — mercado saturado, producto difícil, ventas estancadas
  if (goal('ventas') || goal('leads') || goal('escalar') || true)
    out.push({ id: 'impossible_sale', title: 'Vender lo invendible', kind: 'agent', reason: 'Reframes y ángulos para vender hasta lo que parece imposible.' })
  // Agente Vendedor Maestro: SIEMPRE recomendado (la arma final)
  out.push({ id: 'master_seller_agent', title: 'Agente Vendedor Maestro', kind: 'agent', reason: 'Script de venta irresistible como el mejor vendedor del mundo.' })
  // Sistema de venta: siempre recomendado (transaccional vs consultativa, roadmap)
  if (goal('ventas') || goal('leads') || goal('escalar') || true)
    out.push({ id: 'sales_system_builder', title: 'Constructor de Sistema de Venta', kind: 'tool', reason: 'Método óptimo por escenario · roadmap 30/60/90.' })
  {
    const finHay = `${p.industry} ${p.productDesc}`.toLowerCase()
    const finBiz = /cripto|crypto|inversi|fintech|trading|bolsa|acciones|finan/.test(finHay)
    const hasExchange = (p.customLinks ?? []).some(l => l.enabled && /binance|coinbase|kraken|bybit|broker|invertir|trading/.test(l.url.toLowerCase()))
    if (finBiz || hasExchange || goal('escalar'))
      out.push({ id: 'portfolio_manager', title: 'Gestionar Cartera/Portafolio', kind: 'agent', reason: 'Bots de estrategia (señales, no ejecuta).' })
  }

  // dedupe por id
  const seen = new Set<string>()
  return out.filter(r => (seen.has(r.id) ? false : (seen.add(r.id), true)))
}

/** Plataformas reales (slugs) que el usuario marcó — para resaltar en el mapa. */
export const activePlatformSlugs = (p: BusinessProfile | null): string[] => {
  if (!p) return []
  return [...p.salesPlatforms, ...p.adPlatforms, ...p.socialLinks]
    .filter(l => l.enabled)
    .map(l => l.id)
}

// ── Computer Use product-aware por cuenta ──────────────────────────────────
type AccountCategory = 'content' | 'sales' | 'ads' | 'linkbio' | 'pro' | 'dev'

const CATEGORY_OF: Record<string, AccountCategory> = {
  tiktok: 'content', instagram: 'content', facebook: 'content', twitter: 'content',
  youtube: 'content', threads: 'content', pinterest: 'content',
  mercadolibre: 'sales', amazon: 'sales', shopify: 'sales', tiendanube: 'sales',
  woocommerce: 'sales', hotmart: 'sales',
  meta_ads: 'ads', google_ads: 'ads', tiktok_ads: 'ads', linkedin_ads: 'ads',
  linktree: 'linkbio', beacons: 'linkbio', web: 'linkbio',
  linkedin: 'pro', github: 'dev',
}

const AGENT_OF: Record<AccountCategory, string> = {
  content: 'Creador de contenido', sales: 'E-commerce Manager', ads: 'Media Buyer',
  linkbio: 'Especialista de conversión', pro: 'SDR / Outbound', dev: 'Dev Rel',
}

const actionsFor = (cat: AccountCategory, label: string, product: string, isService: boolean): string[] => {
  switch (cat) {
    case 'content':
      return [`Crear contenido de ${product}`, `Publicar en ${label}`, 'Responder comentarios y DMs']
    case 'sales':
      return [`${isService ? 'Publicar/ajustar oferta' : 'Crear/optimizar listing'} de ${product}`, 'Responder preguntas', 'Ajustar precio y stock']
    case 'ads':
      return [`Crear campaña para ${product}`, 'Optimizar ROAS y pausar lo flojo']
    case 'linkbio':
      return [`Actualizar links y CTA hacia ${product}`, 'Ordenar destacados']
    case 'pro':
      return [`Prospectar y outreach B2B de ${product}`, 'Agendar reuniones']
    case 'dev':
      return [`Actualizar README/release y docs de ${product}`, 'Responder issues']
    default:
      return [`Operar ${label} para ${product}`]
  }
}

/** Texto de indicación preciso para una cuenta (para el dispatch real). */
export const buildAccountInstruction = (link: LinkEntry, p: BusinessProfile): string => {
  const cat = CATEGORY_OF[link.id] ?? 'content'
  const product = p.productDesc || 'mi producto/servicio'
  const isService = p.bizType === 'servicio'
  const acts = actionsFor(cat, link.label, product, isService)
  return `En ${link.label} (${link.url}): ${acts.join('; ')}. Vendo ${p.bizType}: ${product}.${p.offer ? ` Oferta: ${p.offer}.` : ''}`
}

export interface PlannedFlow {
  id: string; name: string; kind: 'cua'; group?: string; mode?: string; status?: string
  instruction?: string
  steps: Array<{ id: string; label: string; kind: string; group?: string; col: number }>
  edges: Array<{ source: string; target: string; rel: string }>
}

const GROUP_OF_CAT: Record<AccountCategory, string> = {
  content: 'publicacion', sales: 'ventas', ads: 'anuncios', linkbio: 'web', pro: 'publicacion', dev: 'web',
}

/** Un flujo n8n por cuenta enlazada, con acciones product-aware sobre la cuenta real. */
const CUSTOM_CAT: Record<CustomLinkType, AccountCategory> = { venta: 'sales', perfil: 'content', web: 'linkbio' }

export const planAccountFlows = (p: BusinessProfile | null): PlannedFlow[] => {
  if (!p) return []
  const product = p.productDesc || 'mi producto'
  const isService = p.bizType === 'servicio'
  const presets = [...p.salesPlatforms, ...p.adPlatforms, ...p.socialLinks]
    .filter(l => l.enabled && validateLink(l.url).ok)
    .map(l => ({ id: l.id, label: l.label, url: l.url, cat: CATEGORY_OF[l.id] ?? 'content' as AccountCategory }))
  const customs = (p.customLinks ?? [])
    .filter(l => l.enabled && validateLink(l.url).ok)
    .map(l => ({ id: l.id, label: l.label || labelFromUrl(l.url), url: l.url, cat: CUSTOM_CAT[l.type] }))
  const links = [...presets, ...customs]
  return links.map((l, i) => {
    const cat = l.cat
    const group = GROUP_OF_CAT[cat]
    const acts = actionsFor(cat, l.label, product, isService)
    const steps: PlannedFlow['steps'] = []
    const edges: PlannedFlow['edges'] = []
    const trig = `pf${i}.trigger`
    steps.push({ id: trig, label: product.slice(0, 22), kind: 'cua', col: 0 })
    const ag = `pf${i}.agent`
    steps.push({ id: ag, label: AGENT_OF[cat], kind: 'agent', group: 'experto', col: 1 })
    edges.push({ source: trig, target: ag, rel: 'planifica' })
    let last = ag
    acts.forEach((a, j) => {
      const tid = `pf${i}.act${j}`
      steps.push({ id: tid, label: a, kind: 'skill', group, col: 2 })
      edges.push({ source: ag, target: tid, rel: 'usa' })
      last = tid
    })
    const pid = `pf${i}.platform`
    steps.push({ id: pid, label: l.label, kind: 'platform', group, col: 3 })
    edges.push({ source: last, target: pid, rel: 'ejecuta' })
    const instruction = `En ${l.label} (${l.url}): ${acts.join('; ')}. Vendo ${p.bizType}: ${product}.${p.offer ? ` Oferta: ${p.offer}.` : ''}`
    return {
      id: `plan.${l.id}.${i}`, name: `${l.label} · ${product.slice(0, 30)}`,
      kind: 'cua', group, mode: 'supervised', status: 'planned',
      instruction, steps, edges,
    }
  })
}

// ── MODO RESCATE — sin clientes / sin ventas → estrategia de adquisición ────
export interface RescueSituation {
  noSales: boolean        // no vende / nadie compra
  hasSocial: boolean      // está en redes
  hasAds: boolean         // paga anuncios
  hasPhysical: boolean    // local físico
  lowTraffic: boolean     // poco tráfico/alcance
}

export interface RescuePhase { id: string; title: string; why: string; tactics: string[] }
export interface RescuePlan { diagnosis: string; phases: RescuePhase[]; flows: PlannedFlow[] }

const has = (arr: LinkEntry[], id: string): boolean => arr.some(l => l.id === id && l.enabled)

const flowFrom = (idx: number, name: string, group: string, agent: string, acts: string[], platformLabel: string, instruction: string): PlannedFlow => {
  const steps: PlannedFlow['steps'] = []
  const edges: PlannedFlow['edges'] = []
  const trig = `rsc${idx}.t`; steps.push({ id: trig, label: 'Rescate', kind: 'cua', col: 0 })
  const ag = `rsc${idx}.a`; steps.push({ id: ag, label: agent, kind: 'agent', group: 'experto', col: 1 })
  edges.push({ source: trig, target: ag, rel: 'planifica' })
  let last = ag
  acts.forEach((a, j) => { const t = `rsc${idx}.s${j}`; steps.push({ id: t, label: a, kind: 'skill', group, col: 2 }); edges.push({ source: ag, target: t, rel: 'usa' }); last = t })
  const pid = `rsc${idx}.p`; steps.push({ id: pid, label: platformLabel, kind: 'platform', group, col: 3 })
  edges.push({ source: last, target: pid, rel: 'ejecuta' })
  return { id: `rescue.${idx}`, name, kind: 'cua', group, mode: 'supervised', status: 'planned', instruction, steps, edges }
}

/**
 * Plan de rescate: diagnostica por qué no entran clientes y arma tácticas
 * agresivas de adquisición (outbound, oferta irresistible, contenido rompefilas,
 * retargeting, reactivación, referidos, local) usando agentes/skills/cuentas reales.
 */
export const rescuePlan = (p: BusinessProfile | null, s: RescueSituation): RescuePlan => {
  if (!p) return { diagnosis: 'Completá tu negocio primero.', phases: [], flows: [] }
  const product = p.productDesc || 'tu producto/servicio'
  const isService = p.bizType === 'servicio'

  // diagnóstico del cuello de botella
  let diagnosis: string
  if (s.hasAds && s.noSales) diagnosis = 'Tenés tráfico pago pero no convierte → problema de OFERTA/embudo. Hay que reformular la propuesta de valor, la oferta y el camino a la compra (menos fricción).'
  else if (s.hasSocial && s.lowTraffic) diagnosis = 'Estás en redes pero con poco alcance → problema de DISTRIBUCIÓN. Hay que romper la burbuja con contenido + outbound directo.'
  else if (s.hasPhysical && s.noSales) diagnosis = 'Local físico sin demanda → falta PRESENCIA DIGITAL LOCAL y captación activa (Google Business, reseñas, WhatsApp, barrio).'
  else diagnosis = 'Sin clientes a pesar de estar presente → falta ADQUISICIÓN ACTIVA. Dejar de esperar y salir a buscar clientes: outbound + oferta irresistible + prueba social.'

  const phases: RescuePhase[] = [
    { id: 'oferta', title: '1. Oferta irresistible', why: 'Sin una oferta clara y urgente, nada convierte.', tactics: [
      `Reformular la oferta de ${product} (bono + garantía + urgencia real)`,
      'Definir propuesta de valor en 1 frase', 'Eliminar fricción del camino a la compra (a WhatsApp/checkout directo)',
    ]},
    { id: 'outbound', title: '2. Adquisición activa (outbound)', why: 'Salir a buscar clientes, no esperarlos.', tactics: [
      isService ? 'Prospectar y mandar DMs/emails B2B a clientes ideales' : 'DMs a quienes interactuaron + lookalike de compradores',
      'Secuencia de seguimiento (5 toques)', 'Calificar y agendar demos/cierres',
    ]},
    { id: 'contenido', title: '3. Contenido rompefilas + prueba social', why: 'Atención barata + confianza.', tactics: [
      `Contenido viral de ${product} (gancho en 3s)`, 'Testimonios y casos', 'Responder comentarios/DMs al instante',
    ]},
    { id: 'reactivar', title: '4. Reactivar + referidos', why: 'Lo más barato: los que ya te conocen.', tactics: [
      'Reactivar leads/carritos/contactos viejos', 'Programa de referidos con incentivo', 'Pedir reseñas a clientes felices',
    ]},
  ]
  if (s.hasAds) phases.push({ id: 'ads', title: '5. Pauta quirúrgica', why: 'Recién con oferta validada, escalar pago.', tactics: [
    'Retargeting a quienes ya te vieron (72h)', 'Campaña de oferta irresistible', 'Pausar lo que no rinde a los 3-5 días',
  ]})
  if (s.hasPhysical) phases.push({ id: 'local', title: '6. Guerrilla local', why: 'Capturar demanda del barrio.', tactics: [
    'Optimizar Google Business + reseñas', 'WhatsApp catálogo + promo local', 'Contenido geolocalizado',
  ]})

  // flows ejecutables (usa cuentas reales si existen; si no, propone el canal)
  const flows: PlannedFlow[] = []
  let i = 0
  // outbound
  if (has(p.socialLinks, 'instagram') || has(p.socialLinks, 'linkedin') || isService)
    flows.push(flowFrom(i++, 'Outbound: DMs a clientes ideales', 'publicacion', 'SDR / Outbound',
      ['Definir ICP', `Mensaje de apertura sobre ${product}`, 'Enviar DMs + seguimiento'],
      has(p.socialLinks, 'linkedin') ? 'LinkedIn' : 'Instagram',
      `Prospectá y contactá clientes ideales para ${product} por DM/inMail con oferta y CTA a WhatsApp.`))
  // contenido rompefilas
  const contentLink = p.socialLinks.find(l => l.enabled && ['tiktok', 'instagram', 'youtube', 'facebook'].includes(l.id))
  if (contentLink)
    flows.push(flowFrom(i++, `Contenido rompefilas en ${contentLink.label}`, 'publicacion', 'Creador de contenido',
      [`Gancho de 3s sobre ${product}`, 'Publicar reel/post', 'Responder comentarios y DMs'],
      contentLink.label, `Creá y publicá contenido rompefilas de ${product} en ${contentLink.label} (${contentLink.url}) y respondé interacciones.`))
  // reactivación
  if (p.channels.includes('whatsapp') || p.channels.includes('email'))
    flows.push(flowFrom(i++, 'Reactivar contactos + referidos', 'mensajeria', 'Customer Success',
      ['Listar contactos/leads viejos', 'Mensaje de reactivación con oferta', 'Pedir referido/reseña'],
      p.channels.includes('whatsapp') ? 'WhatsApp' : 'Email',
      `Reactivá leads y clientes viejos con una oferta de ${product} y pedí referidos/reseñas.`))
  // ads retargeting
  const adLink = p.adPlatforms.find(l => l.enabled)
  if (adLink)
    flows.push(flowFrom(i++, `Retargeting en ${adLink.label}`, 'anuncios', 'Media Buyer',
      ['Audiencia: visitantes/engagers', `Anuncio de oferta de ${product}`, 'Optimizar y pausar lo flojo'],
      adLink.label, `Lanzá retargeting de 72h en ${adLink.label} con la oferta irresistible de ${product}.`))
  // marketplace si vende productos
  const saleLink = p.salesPlatforms.find(l => l.enabled)
  if (saleLink)
    flows.push(flowFrom(i++, `Optimizar venta en ${saleLink.label}`, 'ventas', 'E-commerce Manager',
      [`Optimizar listing/oferta de ${product}`, 'Responder preguntas', 'Ajustar precio competitivo'],
      saleLink.label, `Optimizá el listing y la oferta de ${product} en ${saleLink.label} (${saleLink.url}).`))

  return { diagnosis, phases, flows }
}

// ── MOTOR DE CRECIMIENTO — 3 modos (rescate / crecer / escalar) ─────────────
export type GrowthMode = 'rescate' | 'crecer' | 'escalar' | 'cimientos'

export interface GrowthPlan extends RescuePlan { mode: GrowthMode; strategies: Strategy[] }

const MODE_TOPICS: Record<GrowthMode, string[]> = {
  rescate: ['salir_quiebra', 'ventas', 'mas_clientes', 'contenido'],
  crecer: ['mas_clientes', 'vender_sin_vender', 'contenido', 'ventas', 'posicionamiento_redes', 'posicionamiento_ventas', 'productos_ganadores'],
  escalar: ['referente', 'branding', 'vender_sin_vender', 'estructura_negocio', 'inversiones'],
  cimientos: ['finanzas', 'activos_pasivos', 'costos_presupuesto', 'estimacion_presupuestaria', 'estructura_negocio', 'emprendimiento', 'inversiones', 'productos_ganadores', 'bienes_raices', 'cripto', 'blockchain'],
}

const MODE_DIAGNOSIS: Record<GrowthMode, string> = {
  rescate: 'Modo supervivencia: sin clientes/ventas. Hay que generar caja YA — oferta irresistible + adquisición activa + reactivar lo que ya tenés.',
  crecer: 'Tenés tracción: el objetivo es superarte cada día. Duplicar lo que funciona, sistematizar adquisición y bajar el CAC vendiendo sin vender (orgánico).',
  escalar: 'Etapa de autoridad: convertirte en referente y construir marca para que te compren por reputación, con menos esfuerzo de venta directa.',
  cimientos: 'Base sólida para no quebrar y construir patrimonio: finanzas (activos/pasivos/caja), costos y presupuesto, estructura del negocio, e inversión (mercado/cripto/bienes raíces) según tu producto.',
}

/**
 * Plan del Motor de Crecimiento según el modo. Combina la biblioteca de
 * estrategias (conocimiento) con flujos ejecutables sobre las cuentas reales.
 */
const relevanceCtx = (p: BusinessProfile) => ({ bizType: p.bizType, industry: p.industry, product: p.productDesc, goals: p.goals })

export const growthPlan = (p: BusinessProfile | null, mode: GrowthMode, s: RescueSituation): GrowthPlan => {
  if (!p) return { mode, diagnosis: 'Completá tu negocio primero.', phases: [], flows: [], strategies: [] }
  // estrategias del modo, ordenadas por relevancia al producto/servicio
  const ctx = relevanceCtx(p)
  const inMode = (id: string): boolean => MODE_TOPICS[mode].includes(id)
  const strategies = relevantStrategies(ctx)
    .filter(r => inMode(r.strategy.id))
    .map(r => r.strategy)
  const phases: RescuePhase[] = strategies.map((st, i) => ({
    id: st.id, title: `${i + 1}. ${st.title}`, why: st.principles[0] ?? '', tactics: st.tactics,
  }))
  // flows ejecutables: rescate=plan agresivo; crecer/escalar=acciones por cuenta; cimientos=asesoría (sin CU)
  const flows = mode === 'rescate' ? rescuePlan(p, s).flows
    : mode === 'cimientos' ? []
    : planAccountFlows(p)
  return { mode, diagnosis: MODE_DIAGNOSIS[mode], phases, flows, strategies }
}

/** Plan multi-herramienta (escalable): 1 flujo por herramienta, con smart-defaults
 *  y guardrails. Reusado por "Plan completo" del toolkit y por el Motor. */
export const buildToolPlan = (p: BusinessProfile | null, toolIds: string[]): PlannedFlow[] => {
  if (!p) return []
  const out: PlannedFlow[] = []
  toolIds.forEach((tid, i) => {
    const tool = TOOL_BY_ID[tid]
    if (!tool) return
    const v = tool.smartDefaults ? tool.smartDefaults(p) : {}
    const url = accountUrlFor(tool, p)
    let instruction = tool.buildInstruction(p, v, url)
    const supervised = !!tool.guardrail?.supervised
    if (supervised) instruction = `[SUPERVISADO — pedí confirmación antes de acciones irreversibles] ${instruction}`
    const group = ({ ventas: 'ventas', contenido: 'publicacion', ads: 'anuncios', finanzas: 'finanzas', diseño: 'creatividad', chat: 'mensajeria', crm: 'crm' } as Record<string, string>)[tool.category ?? 'chat'] ?? 'web'
    const steps: PlannedFlow['steps'] = []
    const edges: PlannedFlow['edges'] = []
    const trig = `tp${i}.t`; steps.push({ id: trig, label: tool.name, kind: 'cua', col: 0 })
    const ag = `tp${i}.a`; steps.push({ id: ag, label: 'Agente ejecutor', kind: 'agent', group: 'experto', col: 1 })
    edges.push({ source: trig, target: ag, rel: 'planifica' })
    let last = ag
    tool.capabilities.slice(0, 4).forEach((c, j) => { const id = `tp${i}.s${j}`; steps.push({ id, label: c, kind: 'skill', group, col: 2 }); edges.push({ source: ag, target: id, rel: 'usa' }); last = id })
    const pid = `tp${i}.p`; steps.push({ id: pid, label: tool.platformLabel, kind: 'platform', group, col: 3 })
    edges.push({ source: last, target: pid, rel: 'ejecuta' })
    out.push({ id: `toolplan.${tid}.${i}`, name: tool.name, kind: 'cua', group, mode: supervised ? 'supervised' : 'auto', status: 'planned', instruction, steps, edges })
  })
  return out
}
