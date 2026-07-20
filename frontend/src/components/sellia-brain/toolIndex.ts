/**
 * SellIA Brain Tool Index
 * Frontend-visible tools only. Internal AI agents, mentors, reasoning engines
 * and automation infrastructure stay backend — the magician never reveals his tricks.
 *
 * Funnel lobes:
 *   ACQUIRE   · capta señales · construye pipeline de leads
 *   CONVERT   · cierra ventas · transforma interés en cliente
 *   RETAIN    · fideliza · cliente habitual · revenue recurrente
 *   CORE      · configuración · gobierno · asistente
 */

export type LobeId = 'acquire' | 'convert' | 'retain' | 'core'


export interface Tool {
  id: string
  title: string
  subtitle: string
  lobe: LobeId
  componentId: string   // anchor id used to scroll to mounted component
  keywords: string[]
  icon: string          // single emoji glyph
  weight: number        // 1-5 · higher = more prominent in lobe
}


export const LOBES: Record<LobeId, {
  id: LobeId
  label: string
  title: string
  subtitle: string
  color: string
  glow: string
  position: { x: number; y: number }
}> = {
  acquire: {
    id: 'acquire',
    label: 'Adquisición',
    title: 'Capta y atrae clientes',
    subtitle: 'Audiencia, leads, canales, marketplace.',
    color: '#22d3ee',
    glow: 'rgba(34,211,238,0.45)',
    position: { x: 12, y: 50 },
  },
  convert: {
    id: 'convert',
    label: 'Conversión',
    title: 'Transformá interés en venta',
    subtitle: 'Diagnóstico, cierre, automatización, facturación.',
    color: '#ec4899',
    glow: 'rgba(236,72,153,0.45)',
    position: { x: 50, y: 30 },
  },
  retain: {
    id: 'retain',
    label: 'Retención',
    title: 'Hacé cliente habitual',
    subtitle: 'Pago, soporte, recompra, reputación, reportes.',
    color: '#10b981',
    glow: 'rgba(16,185,129,0.45)',
    position: { x: 88, y: 50 },
  },
  core: {
    id: 'core',
    label: 'Control',
    title: 'Configuración & asistente',
    subtitle: 'Panel, auditoría, voz, planes.',
    color: '#a855f7',
    glow: 'rgba(168,85,247,0.45)',
    position: { x: 50, y: 78 },
  },
}


export const TOOLS: Tool[] = [

  // ── ACQUIRE — 8 herramientas visibles ─────────────────────────────────
  {
    id: 'ads-cockpit',
    title: 'Ads Cockpit',
    subtitle: 'Meta · Google · TikTok · ROAS unificado',
    lobe: 'acquire', componentId: 'lobe-acquire-ads',
    keywords: ['ads','publicidad','meta','google','tiktok','roas','paid'],
    icon: '🎯', weight: 5,
  },
  {
    id: 'growth-engine',
    title: 'Growth Engine',
    subtitle: 'Loops virales · referidos · waitlists · orgánico',
    lobe: 'acquire', componentId: 'lobe-acquire-growth',
    keywords: ['growth','viral','referidos','waitlist','organic'],
    icon: '🚀', weight: 5,
  },
  {
    id: 'marketplace-center',
    title: 'Marketplace Center',
    subtitle: 'Amazon · ML · Shopify · Hotmart · Tienda Nube',
    lobe: 'acquire', componentId: 'lobe-acquire-marketplace',
    keywords: ['marketplace','amazon','mercadolibre','shopify','hotmart','tiendanube','listings'],
    icon: '🏬', weight: 4,
  },
  {
    id: 'canales-digitales',
    title: 'Canales Digitales',
    subtitle: 'WhatsApp · IG · LinkedIn · Email · TikTok · Telegram · Web',
    lobe: 'acquire', componentId: 'lobe-acquire-omni',
    keywords: ['canales','whatsapp','instagram','linkedin','email','tiktok','telegram','web'],
    icon: '📡', weight: 5,
  },
  {
    id: 'pages-forms',
    title: 'Páginas & Formularios',
    subtitle: 'Landings · formularios · A/B · captura de leads',
    lobe: 'acquire', componentId: 'lobe-acquire-forms',
    keywords: ['landing','formularios','captura','ab','split test','pagina'],
    icon: '📝', weight: 3,
  },
  {
    id: 'knowledge-base',
    title: 'Base de Conocimiento',
    subtitle: 'Docs · sitios · PDFs · entrenamiento de la IA',
    lobe: 'acquire', componentId: 'lobe-acquire-kb',
    keywords: ['kb','rag','docs','pdf','training','knowledge','base','conocimiento'],
    icon: '📚', weight: 3,
  },
  {
    id: 'mi-industria',
    title: 'Mi Industria',
    subtitle: '58 verticales pre-configuradas · templates por nicho',
    lobe: 'acquire', componentId: 'lobe-acquire-verticals',
    keywords: ['vertical','industria','nicho','presets','sector'],
    icon: '🏛️', weight: 3,
  },
  {
    id: 'reach-shipping',
    title: 'Cobertura & Envíos',
    subtitle: 'Cobertura geo · carriers · zonas de entrega',
    lobe: 'acquire', componentId: 'lobe-acquire-reach',
    keywords: ['cobertura','envio','shipping','geo','zonas','logistica'],
    icon: '🛰️', weight: 2,
  },

  // ── CONVERT — 6 herramientas visibles ─────────────────────────────────
  {
    id: 'deal-doctor',
    title: 'Deal Doctor',
    subtitle: 'Diagnóstico y destrabe de negociaciones estancadas',
    lobe: 'convert', componentId: 'lobe-convert-doctor',
    keywords: ['deal','diagnostico','stuck','pipeline','negociacion'],
    icon: '🩺', weight: 5,
  },
  {
    id: 'sala-ejecutiva',
    title: 'Sala Ejecutiva',
    subtitle: 'Piloto automático · agente navegador · flujos · voz · actividad',
    lobe: 'convert', componentId: 'lobe-convert-sala',
    keywords: ['autonomous','autopilot','cua','computer use','workflow','flujos','voz','voice','feed','actividad'],
    icon: '🎬', weight: 5,
  },
  {
    id: 'conversion-guarantee',
    title: 'Garantía de Conversión',
    subtitle: 'Cierre garantizado · análisis de objeciones · SLA',
    lobe: 'convert', componentId: 'lobe-convert-guarantee',
    keywords: ['garantia','cierre','convert','sla','objeciones'],
    icon: '🏆', weight: 5,
  },
  {
    id: 'champion-builder',
    title: 'Champion Builder',
    subtitle: 'Identifica y desarrolla aliados internos en B2B',
    lobe: 'convert', componentId: 'lobe-convert-champion',
    keywords: ['champion','aliado','interno','enterprise','b2b'],
    icon: '🛡️', weight: 4,
  },
  {
    id: 'calendar-scheduling',
    title: 'Agenda & Reuniones',
    subtitle: 'Demos · meetings · auto-book · recordatorios',
    lobe: 'convert', componentId: 'lobe-convert-calendar',
    keywords: ['calendario','demos','meetings','book','calendly','agenda','cita'],
    icon: '📅', weight: 3,
  },
  {
    id: 'invoicing-quotes',
    title: 'Cotizaciones & Facturas',
    subtitle: 'Presupuestos · facturación · CAE · AFIP · ARCA',
    lobe: 'convert', componentId: 'lobe-convert-invoice',
    keywords: ['factura','quote','cotizacion','cae','afip','arca','presupuesto'],
    icon: '🧾', weight: 4,
  },

  // ── RETAIN — 10 herramientas visibles ─────────────────────────────────
  {
    id: 'customer-360',
    title: 'Customer 360',
    subtitle: 'Ficha unificada · historial · segmentación inteligente',
    lobe: 'retain', componentId: 'lobe-retain-360',
    keywords: ['customer','cliente','360','crm','perfil','historial'],
    icon: '🌐', weight: 5,
  },
  {
    id: 'recovery-lab',
    title: 'Recovery Lab',
    subtitle: 'Carritos abandonados · win-back · dunning automático',
    lobe: 'retain', componentId: 'lobe-retain-recovery',
    keywords: ['recovery','carrito','abandonado','winback','dunning'],
    icon: '🧪', weight: 5,
  },
  {
    id: 'fidelization-flow',
    title: 'Fidelización & Lealtad',
    subtitle: 'Onboarding post-venta · NPS · loyalty · referidos',
    lobe: 'retain', componentId: 'lobe-retain-fidel',
    keywords: ['fidelizacion','loyalty','nps','postventa','referidos'],
    icon: '💎', weight: 5,
  },
  {
    id: 'order-lifecycle',
    title: 'Ciclo de Pedidos',
    subtitle: 'Tracking · entrega · notificaciones · post-compra',
    lobe: 'retain', componentId: 'lobe-retain-orders',
    keywords: ['order','pedido','tracking','envio','lifecycle','entrega'],
    icon: '📦', weight: 4,
  },
  {
    id: 'reputation',
    title: 'Reputación & Reseñas',
    subtitle: 'Google · Trustpilot · IA responde · devoluciones · RMA',
    lobe: 'retain', componentId: 'lobe-retain-reputation',
    keywords: ['reviews','reseñas','rating','google','trustpilot','rma','devolucion'],
    icon: '⭐', weight: 4,
  },
  {
    id: 'email-campaigns',
    title: 'Email Marketing',
    subtitle: 'Newsletter · drip · re-engagement · campañas',
    lobe: 'retain', componentId: 'lobe-retain-email',
    keywords: ['email','newsletter','campaña','drip','marketing'],
    icon: '✉️', weight: 3,
  },
  {
    id: 'inventory',
    title: 'Inventario',
    subtitle: 'Stock · reposición automática · alertas · multi-canal',
    lobe: 'retain', componentId: 'lobe-retain-inventory',
    keywords: ['stock','inventory','reorder','almacen','inventario'],
    icon: '📦', weight: 3,
  },
  {
    id: 'analytics-reports',
    title: 'Analytics & Reportes',
    subtitle: 'KPIs · funnels · retención · P&L · exports',
    lobe: 'retain', componentId: 'lobe-retain-analytics',
    keywords: ['analytics','kpi','funnel','retention','dashboard','report','pnl','cohort'],
    icon: '📊', weight: 4,
  },
  {
    id: 'arca-compliance',
    title: 'ARCA Compliance',
    subtitle: 'Padrón · factura electrónica · monotributo · responsable',
    lobe: 'retain', componentId: 'lobe-retain-arca',
    keywords: ['arca','afip','padron','factura','monotributo'],
    icon: '🇦🇷', weight: 4,
  },
  {
    id: 'tax-customs',
    title: 'Impuestos & Aduana',
    subtitle: 'AR · MX · CO · PE · BR · USA · EU · COVE · DJVE',
    lobe: 'retain', componentId: 'lobe-retain-tax',
    keywords: ['tax','iva','afip','sat','dian','sunat','aduana','cove','djve','export'],
    icon: '🧮', weight: 3,
  },

  // ── CORE — 5 herramientas visibles ────────────────────────────────────
  {
    id: 'panel-config',
    title: 'Panel de Control',
    subtitle: 'Usuarios · roles · permisos · configuración guiada',
    lobe: 'core', componentId: 'lobe-core-config',
    keywords: ['admin','users','roles','rbac','configuracion','setup','onboarding'],
    icon: '⚙️', weight: 5,
  },
  {
    id: 'audit-logs',
    title: 'Historial & Auditoría',
    subtitle: 'Trazabilidad completa · compliance · logs',
    lobe: 'core', componentId: 'lobe-core-audit',
    keywords: ['audit','logs','compliance','trazabilidad','historial'],
    icon: '📜', weight: 3,
  },
  {
    id: 'pricing-plans',
    title: 'Planes & Facturación',
    subtitle: 'Tiers · upgrades · paywall · suscripción',
    lobe: 'core', componentId: 'lobe-core-pricing',
    keywords: ['pricing','plans','tiers','paywall','suscripcion'],
    icon: '💳', weight: 3,
  },
  {
    id: 'asistente-voz',
    title: 'Asistente de Voz',
    subtitle: '"Hola SellIA" · narración en vivo · 12 idiomas',
    lobe: 'core', componentId: 'lobe-core-voz',
    keywords: ['voice','hola sellia','palette','idiomas','narration','voz','tts'],
    icon: '🗣️', weight: 3,
  },
  {
    id: 'sellia-avatar',
    title: 'SellIA Avatar',
    subtitle: 'Cara visible del asistente · personalidad de marca',
    lobe: 'core', componentId: 'lobe-core-avatar',
    keywords: ['avatar','face','identity','marca','personalidad'],
    icon: '🤳', weight: 2,
  },
]


export const TOOLS_BY_LOBE: Record<LobeId, Tool[]> = {
  acquire: TOOLS.filter((t) => t.lobe === 'acquire').sort((a, b) => b.weight - a.weight),
  convert: TOOLS.filter((t) => t.lobe === 'convert').sort((a, b) => b.weight - a.weight),
  retain:  TOOLS.filter((t) => t.lobe === 'retain').sort((a, b) => b.weight - a.weight),
  core:    TOOLS.filter((t) => t.lobe === 'core').sort((a, b) => b.weight - a.weight),
}


export const fuzzyMatch = (query: string, tool: Tool): number => {
  const q = query.toLowerCase().trim()
  if (!q) return 1
  const hay = `${tool.title} ${tool.subtitle} ${tool.keywords.join(' ')}`.toLowerCase()
  if (hay.startsWith(q)) return 100
  if (hay.includes(` ${q}`) || hay.includes(`-${q}`)) return 80
  if (hay.includes(q)) return 60
  let i = 0
  for (const ch of hay) {
    if (ch === q[i]) i += 1
    if (i === q.length) return 25
  }
  return 0
}
