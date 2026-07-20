/**
 * Catálogo de herramientas funcionales del Motor de Crecimiento.
 * Cada herramienta está anexada a su plataforma/red pertinente (vía los links
 * del perfil) y arma una indicación concreta para Computer Use / automatización.
 */

import type { BusinessProfile } from '@/lib/business-profile'

export interface ToolInput { key: string; label: string; placeholder: string; type?: 'text' | 'textarea' }

export interface GrowthTool {
  id: string
  name: string
  kind: 'automation' | 'tool' | 'agent'
  /** ids de plataforma del perfil a los que se anexa (salesPlatforms/adPlatforms/socialLinks/channels). */
  platforms: string[]
  platformLabel: string
  desc: string
  capabilities: string[]
  inputs: ToolInput[]
  buildInstruction: (p: BusinessProfile, v: Record<string, string>, accountUrl: string) => string
  /** UX especial del Tool Studio. create_confirm = pregunta "¿creo por vos?"; advisory = estrategia + aviso de no-ejecución. */
  studioMode?: 'create_confirm' | 'advisory'
  /** Estrategias seleccionables (advisory). */
  strategies?: Array<{ id: string; label: string; desc: string }>
  /** Aviso de seguridad mostrado en el studio. */
  safetyNote?: string
  // ── excelencia: categoría, métrica, checklist, conocimiento, guardrails ──
  category?: ToolCategory
  /** KPI / métrica de éxito de la herramienta. */
  kpi?: string
  /** Criterios de "hecho" / qué vas a obtener. */
  checklist?: string[]
  /** Estrategia del cerebro que la respalda (growth-strategies id). */
  strategyRef?: string
  /** Nivel de riesgo → drive de confirmación supervisada. */
  risk?: 'safe' | 'medium' | 'high'
  /** Guardrail responsable. */
  guardrail?: { supervised?: boolean; note: string }
  /** Prefill inteligente de inputs desde el perfil. */
  smartDefaults?: (p: BusinessProfile) => Record<string, string>
}

export type ToolCategory = 'ventas' | 'contenido' | 'ads' | 'finanzas' | 'diseño' | 'chat' | 'crm'

export const CATEGORY_COLOR: Record<ToolCategory, string> = {
  ventas: '#10B981', contenido: '#8B5CF6', ads: '#F59E0B', finanzas: '#EAB308',
  diseño: '#EC4899', chat: '#3B82F6', crm: '#14B8A6',
}

/** Metadata de excelencia por herramienta (category/kpi/checklist/strategyRef/guardrail/smartDefaults). */
const META: Record<string, Partial<GrowthTool>> = {
  wa_bot_247: {
    category: 'chat', kpi: 'Tasa de respuesta <1 min · +30% conversión de chat', strategyRef: 'ventas', risk: 'medium',
    checklist: ['Responde el 100% de consultas', 'Califica y registra cada lead', 'Deriva a humano en casos sensibles'],
    guardrail: { supervised: true, note: 'Pide confirmación antes de enviar promesas de precio/stock o cerrar pagos.' },
    smartDefaults: (p) => ({ tono: p.bizType === 'servicio' ? 'profesional' : 'cercano', bienvenida: `¡Hola! ¿Te ayudo con ${p.productDesc || 'lo que buscás'}?` }),
  },
  inventory_sync: {
    category: 'ventas', kpi: '0 quiebres de stock · 0 sobreventa', strategyRef: 'posicionamiento_ventas', risk: 'medium',
    checklist: ['Stock unificado entre canales', 'Alerta de reposición activa', 'Sin ventas sobre stock 0'],
    guardrail: { supervised: true, note: 'Confirma antes de cambiar precios o pausar publicaciones.' },
    smartDefaults: () => ({ minimo: '5' }),
  },
  review_responder: {
    category: 'ventas', kpi: 'Respuesta <5 min · rating 4.8★+', strategyRef: 'referente', risk: 'medium',
    checklist: ['Responde toda reseña nueva', 'Escala quejas graves', 'Pide reseña a clientes felices'],
    guardrail: { supervised: false, note: 'NUNCA inventa reseñas ni reviews falsas; solo responde las reales.' },
    smartDefaults: (p) => ({ firma: `Equipo de ${p.industry || 'la marca'}` }),
  },
  meta_ads_optimizer: {
    category: 'ads', kpi: 'ROAS objetivo ≥3x · CPA en baja', strategyRef: 'mas_clientes', risk: 'high',
    checklist: ['Campaña creada con audiencias', 'Retargeting activo', 'Pausa de lo flojo a 3-5 días'],
    guardrail: { supervised: true, note: 'Respeta el tope de presupuesto; confirma antes de subir gasto o publicar anuncios.' },
    smartDefaults: () => ({ presupuesto: '$20', objetivo: 'ventas' }),
  },
  google_ads_optimizer: {
    category: 'ads', kpi: 'CPC bajo · conversiones en alza', strategyRef: 'mas_clientes', risk: 'high',
    checklist: ['Search + display activos', 'Keywords actualizadas', 'Pausa de términos sin retorno'],
    guardrail: { supervised: true, note: 'Respeta el tope diario; confirma antes de aumentar puja/presupuesto.' },
    smartDefaults: (p) => ({ presupuesto: '$25', keywords: `comprar ${p.productDesc || 'producto'}` }),
  },
  tiktok_ads_optimizer: {
    category: 'ads', kpi: 'CPA bajo en público joven', strategyRef: 'posicionamiento_redes', risk: 'high',
    checklist: ['Campaña TikTok activa', 'Creativos verticales testeados', 'Escala del ganador'],
    guardrail: { supervised: true, note: 'Respeta el tope; confirma antes de subir presupuesto.' },
    smartDefaults: () => ({ presupuesto: '$20' }),
  },
  tiktok_promo: {
    category: 'contenido', kpi: 'Views + saves + seguidores en alza', strategyRef: 'posicionamiento_redes', risk: 'medium',
    checklist: ['Publica con gancho de 3s', 'Usa tendencias/sonidos', 'Responde comentarios'],
    guardrail: { supervised: true, note: 'Confirma antes de publicar contenido a tu cuenta.' },
    smartDefaults: () => ({ angulo: 'antes/después o tutorial rápido' }),
  },
  social_content: {
    category: 'contenido', kpi: '+3x alcance orgánico', strategyRef: 'contenido', risk: 'medium',
    checklist: ['Calendario activo', 'Posts/reels/stories publicados', 'Repurpose 1→varios'],
    guardrail: { supervised: true, note: 'Confirma antes de publicar a tus redes.' },
    smartDefaults: () => ({ frecuencia: 'diaria' }),
  },
  cart_recovery: {
    category: 'ventas', kpi: '+12-18% carritos recuperados', strategyRef: 'mas_clientes', risk: 'medium',
    checklist: ['Detecta abandono', 'Secuencia WA+email', 'Oferta a las 24h'],
    guardrail: { supervised: false, note: 'Mensajes con valor; respeta la baja/opt-out del cliente.' },
    smartDefaults: (p) => ({ incentivo: p.offer || '10% off' }),
  },
  crm_sync: {
    category: 'crm', kpi: '0 leads perdidos · pipeline al día', strategyRef: 'ventas', risk: 'safe',
    checklist: ['Contactos/deals cargados', 'Etapas y seguimiento', 'Lead scoring activo'],
    guardrail: { supervised: false, note: 'Solo organiza datos; no envía mensajes sin tu OK.' },
    smartDefaults: () => ({ etapas: 'nuevo → contactado → propuesta → cierre' }),
  },
  copy_gen: {
    category: 'contenido', kpi: '+CTR · variantes para A/B', strategyRef: 'contenido', risk: 'safe',
    checklist: ['Titular + variantes', 'AIDA aplicado', 'Adaptado al canal'],
    guardrail: { supervised: false, note: 'Genera borradores; vos elegís y publicás.' },
    smartDefaults: () => ({ canal: 'anuncio', angulo: 'beneficio principal' }),
  },
  canva_create: {
    category: 'diseño', kpi: 'Piezas listas para publicar', strategyRef: 'branding', risk: 'safe',
    checklist: ['Borradores con tu identidad', 'Revisión antes de exportar', 'Export listo para canal'],
    guardrail: { supervised: false, note: 'Muestra borradores antes de exportar; no publica sin tu OK.' },
    smartDefaults: () => ({ pieza: 'post promo' }),
  },
  portfolio_manager: {
    category: 'finanzas', kpi: 'Señales + gestión de riesgo (no ejecuta)', strategyRef: 'inversiones', risk: 'high',
    checklist: ['Watchlist + niveles', 'Stop-loss sugerido', 'Alertas; vos confirmás cada operación'],
    guardrail: { supervised: true, note: 'NUNCA ejecuta compras/ventas ni transferencias; solo señales que vos confirmás.' },
    smartDefaults: () => ({ riesgo: 'moderado', strategy: 'swing' }),
  },
  manychat_qualify: {
    category: 'chat', kpi: '−60% leads malos · +40% calidad de pipeline', strategyRef: 'ventas', risk: 'medium',
    checklist: ['Flujo de calificación activo en ManyChat', 'Reglas de descarte (no-interesado, sin presupuesto, fuera de zona)', 'Solo leads CALIENTES llegan al vendedor'],
    guardrail: { supervised: true, note: 'No descarta sin trazabilidad: cada "lead malo" queda registrado con motivo. Confirma antes de bloquear contactos.' },
    smartDefaults: (p) => ({
      tipoOferta: p.bizType === 'servicio' ? 'servicio' : 'bien',
      criterios: p.bizType === 'servicio'
        ? 'necesidad real + presupuesto + plazo + decisor'
        : 'intención de compra + zona/envío + presupuesto + uso real',
      bienvenida: `¡Hola! Antes de pasarte con un asesor, contame qué buscás con ${p.productDesc || 'nuestro servicio'} 👇`,
    }),
  },
  lead_capture: {
    category: 'crm', kpi: '+3x captura de leads · scoring automático', strategyRef: 'mas_clientes', risk: 'medium',
    checklist: ['Lead magnet activo (descargable/diagnóstico/demo)', 'Formulario + ManyChat + WhatsApp como entrada', 'Scoring (frío/tibio/caliente) y derivación automática'],
    guardrail: { supervised: false, note: 'Pide consentimiento explícito de datos (LGPD/GDPR/Ley 25.326). No comparte datos con terceros.' },
    smartDefaults: (p) => ({
      magnet: p.bizType === 'servicio' ? 'Diagnóstico/auditoría gratis' : 'Guía/cupón de bienvenida',
      canales: 'IG DM + WhatsApp + Landing',
      scoring: 'frío(0-3) → tibio(4-7) → caliente(8-10)',
    }),
  },
  brief_to_campaign: {
    category: 'ads', kpi: 'Brief → campaña 360° lista en horas', strategyRef: 'mas_clientes', risk: 'medium',
    checklist: ['Estrategia (objetivo, audiencias, canales, presupuesto, KPI)', 'Copys + creativos + landing', 'Plan de medición y optimización'],
    guardrail: { supervised: true, note: 'Genera plan + creativos; confirma antes de lanzar pauta o publicar en cuentas reales.' },
    smartDefaults: (p) => ({
      objetivo: p.goals?.[0] || 'ventas',
      publico: p.industry || 'tu público objetivo',
      presupuesto: '$300/mes',
      canales: 'Meta Ads + Google + orgánico',
    }),
  },
  master_seller_agent: {
    category: 'ventas', kpi: 'Script maestro para CUALQUIER bien/servicio', strategyRef: 'ventas', risk: 'safe',
    checklist: [
      'Contexto: qué vendo, a quién, momento del cierre',
      'Script maestro: 5 pasos (Rapport → Diagnóstico → Reframe → Oferta → Cierre)',
      'Tonalidad calibrada por paso',
      '7 objeciones probables con respuesta maestra',
      'Cierre + Garantía + Escasez real',
      'Seguimiento (próximos 48h)',
    ],
    guardrail: { supervised: false, note: 'Agente maestro. Integra Belfort+SPIN+Hormozi+Vaynerchuk+Cialdini. Responde como mejor vendedor del mundo. Honesto: si no hay caso de venta, lo dice.' },
    smartDefaults: (p) => ({
      producto: p.productDesc || 'mi producto/servicio',
      tipo: p.bizType === 'servicio' ? 'servicio' : 'bien',
      audiencia: p.audience || 'mi cliente ideal',
      etapa: 'primer_contacto',
    }),
  },
  sales_system_builder: {
    category: 'ventas', kpi: 'Método óptimo por escenario · roadmap de 30/60/90 días', strategyRef: 'ventas', risk: 'safe',
    checklist: [
      'Diagnóstico: ticket · decisores · ciclo esperado',
      'Método recomendado (transaccional vs consultativa)',
      'Roadmap de venta: fase 1/2/3 con acciones concretas',
      '7 objeciones probables + respuesta calibrada para cada una',
      'Métricas de seguimiento (tasa de avance, conversión por fase)',
    ],
    guardrail: { supervised: false, note: 'Recomienda métodos probados (Belfort, SPIN, MEDDIC, etc.). No inventa tácticas; cita framework + origen. Honesto sobre cuándo cada método falla.' },
    smartDefaults: (p) => ({
      producto: p.productDesc || 'mi producto',
      ticket: '~$5,000',
      decisores: 'uno/dos',
      cicloEsperado: '30-60 días',
    }),
  },
  impossible_sale: {
    category: 'ventas', kpi: 'Pitch + 5 ángulos para vender lo "invendible"', strategyRef: 'ventas', risk: 'medium',
    checklist: [
      '5 reframes de significado del producto',
      '5 palancas (audiencia/categoría/propósito/tiempo/packaging) exploradas',
      'Oferta irresistible (sueño/prueba/tiempo/esfuerzo + bonos + garantía)',
      'Manejo de la objeción "no lo necesito"',
      'Pitch final en 1 párrafo + script de cierre',
    ],
    guardrail: { supervised: false, note: 'Genera ángulos honestos: no inventa atributos falsos ni promete lo que el producto no cumple. Marca claramente cuándo un ángulo requiere certificación/prueba real.' },
    smartDefaults: (p) => ({
      producto: p.productDesc || 'mi producto',
      contexto: `mercado donde el producto parece innecesario o saturado`,
      audiencia: p.audience || 'a definir',
    }),
  },
  lead_scoring: {
    category: 'crm', kpi: 'Leads calificados automáticamente · priorización clara', strategyRef: 'mas_clientes', risk: 'safe',
    checklist: [
      'Scoring automático (frío/tibio/caliente)',
      'Derivación por temperatura',
      'Alertas de leads calientes',
      'Historial de scoring',
    ],
    guardrail: { supervised: false, note: 'Lead scoring basado en comportamiento observable (respuestas, engagement). No discriminatorio.' },
    smartDefaults: () => ({
      criteria: 'respuesta_rapida + engagement + budget_indicios',
      frioMax: 3,
      tibioMax: 7,
      calienteMin: 8,
    }),
  },
  brand_identity: {
    category: 'diseño', kpi: 'Identidad coherente · brand kit completo', strategyRef: 'branding', risk: 'safe',
    checklist: ['Propuesta de valor + tono de voz', 'Naming/eslogan + paleta + tipografía + logo (opciones)', 'Brand kit exportable (Canva/Figma)'],
    guardrail: { supervised: false, note: 'Genera propuestas; vos elegís. No registra marca: te indica los pasos si querés hacerlo.' },
    smartDefaults: (p) => ({
      vibe: p.bizType === 'servicio' ? 'confiable y experto' : 'cercano y aspiracional',
      publico: p.industry || 'tu público objetivo',
      valores: 'claridad, resultados, cercanía',
    }),
  },
}

const prod = (p: BusinessProfile): string => p.productDesc || 'mi producto/servicio'

export const TOOLS: GrowthTool[] = [
  {
    id: 'wa_bot_247', name: 'Bot WhatsApp 24/7', kind: 'automation',
    platforms: ['whatsapp'], platformLabel: 'WhatsApp',
    desc: 'Atiende, califica, envía catálogo y cierra ventas por WhatsApp las 24h.',
    capabilities: ['Responde consultas al instante', 'Califica leads (necesidad/presupuesto)', 'Envía catálogo y precios', 'Agenda y cierra; deriva a humano si hace falta'],
    inputs: [
      { key: 'tono', label: 'Tono', placeholder: 'cercano / profesional / vendedor' },
      { key: 'bienvenida', label: 'Mensaje de bienvenida', placeholder: '¡Hola! ¿En qué te ayudo con…?', type: 'textarea' },
    ],
    buildInstruction: (p, v) => `Operá el WhatsApp Business como bot 24/7 para ${prod(p)}. Tono ${v.tono || 'cercano'}. Bienvenida: "${v.bienvenida || 'Hola, ¿en qué te ayudo?'}". Respondé consultas, calificá (necesidad/presupuesto), enviá catálogo${p.offer ? ` y la oferta: ${p.offer}` : ''} y avanzá al cierre; derivá a humano si es necesario.`,
  },
  {
    id: 'inventory_sync', name: 'Sincronía de inventario', kind: 'automation',
    platforms: ['mercadolibre', 'amazon', 'shopify', 'tiendanube', 'woocommerce'], platformLabel: 'tu tienda/marketplace',
    desc: 'Mantiene el stock unificado en todos tus canales y alerta reposición.',
    capabilities: ['Sincroniza stock entre canales', 'Alerta al llegar al mínimo', 'Sugiere orden de reposición', 'Evita sobreventa'],
    inputs: [{ key: 'minimo', label: 'Stock mínimo de alerta', placeholder: 'ej: 5' }],
    buildInstruction: (p, v, url) => `Sincronizá el inventario de ${prod(p)} en ${url || 'tus canales de venta'}. Alertá cuando una variante llegue a ${v.minimo || '5'} unidades y sugerí reposición. Evitá sobreventa entre canales.`,
  },
  {
    id: 'review_responder', name: 'Gestor de reseñas', kind: 'automation',
    platforms: ['mercadolibre', 'amazon', 'google_business'], platformLabel: 'Mercado Libre / Google',
    desc: 'Responde reseñas en <5 min y protege tu reputación (rating 4.8★+).',
    capabilities: ['Monitorea reseñas nuevas', 'Responde con empatía en minutos', 'Escala quejas críticas', 'Pide reseña a clientes felices'],
    inputs: [{ key: 'firma', label: 'Firma', placeholder: 'Equipo de [marca]' }],
    buildInstruction: (p, v, url) => `Monitoreá y respondé reseñas de ${prod(p)} en ${url || 'el marketplace'} en menos de 5 minutos, con tono empático, firma "${v.firma || 'el equipo'}". Escalá quejas graves y pedí reseña a compradores satisfechos.`,
  },
  {
    id: 'meta_ads_optimizer', name: 'Optimizador Meta Ads', kind: 'automation',
    platforms: ['meta_ads'], platformLabel: 'Meta Ads (FB/IG)',
    desc: 'Crea, monitorea, escala y pausa campañas en Meta según ROAS.',
    capabilities: ['Crea campañas + audiencias', 'Monitorea ROAS en vivo', 'Escala lo ganador, pausa lo flojo a 3-5 días', 'Retargeting de visitantes'],
    inputs: [
      { key: 'presupuesto', label: 'Presupuesto diario', placeholder: 'ej: $20' },
      { key: 'objetivo', label: 'Objetivo', placeholder: 'ventas / leads / mensajes' },
    ],
    buildInstruction: (p, v, url) => `En Meta Ads (${url || 'tu cuenta'}) creá y optimizá campañas para ${prod(p)}. Presupuesto diario ${v.presupuesto || '$20'}, objetivo ${v.objetivo || 'ventas'}. Monitoreá ROAS, escalá lo ganador y pausá lo flojo a los 3-5 días. Sumá retargeting de visitantes.`,
  },
  {
    id: 'google_ads_optimizer', name: 'Optimizador Google Ads', kind: 'automation',
    platforms: ['google_ads'], platformLabel: 'Google Ads',
    desc: 'Campañas search + display con keywords y puja automática.',
    capabilities: ['Search + display', 'Keywords actualizadas semanal', 'Puja automática a conversión', 'Pausa términos que no rinden'],
    inputs: [
      { key: 'presupuesto', label: 'Presupuesto diario', placeholder: 'ej: $25' },
      { key: 'keywords', label: 'Palabras clave', placeholder: 'comprar zapatillas…' },
    ],
    buildInstruction: (p, v, url) => `En Google Ads (${url || 'tu cuenta'}) creá campañas search+display para ${prod(p)}. Presupuesto ${v.presupuesto || '$25'}/día, keywords: ${v.keywords || 'según producto'}. Puja automática a conversión; pausá términos sin retorno.`,
  },
  {
    id: 'tiktok_ads_optimizer', name: 'Optimizador TikTok Ads', kind: 'automation',
    platforms: ['tiktok_ads'], platformLabel: 'TikTok Ads',
    desc: 'Crea y optimiza pauta en TikTok para audiencia joven.',
    capabilities: ['Crea campañas TikTok For Business', 'Creativos verticales que convierten', 'Optimiza CPA/ROAS', 'Escala lo ganador'],
    inputs: [{ key: 'presupuesto', label: 'Presupuesto diario', placeholder: 'ej: $20' }],
    buildInstruction: (p, v, url) => `En TikTok Ads (${url || 'tu cuenta'}) creá y optimizá campañas para ${prod(p)} con creativos verticales. Presupuesto ${v.presupuesto || '$20'}/día. Optimizá CPA/ROAS y escalá lo ganador.`,
  },
  {
    id: 'tiktok_promo', name: 'Promocionar en TikTok', kind: 'tool',
    platforms: ['tiktok'], platformLabel: 'TikTok',
    desc: 'Contenido orgánico viral (rompefilas) para crecer sin pagar ads.',
    capabilities: ['Ideas y guiones con gancho de 3s', 'Tendencias y sonidos del momento', 'Publica y responde comentarios', 'Mide qué formato funciona'],
    inputs: [{ key: 'angulo', label: 'Ángulo/idea', placeholder: 'antes/después, tutorial, detrás de escena…' }],
    buildInstruction: (p, v, url) => `Creá y publicá contenido orgánico viral de ${prod(p)} en TikTok (${url || 'tu perfil'}). Ángulo: ${v.angulo || 'gancho fuerte en 3s'}. Usá tendencias/sonidos, publicá y respondé comentarios.`,
  },
  {
    id: 'social_content', name: 'Contenido social diario', kind: 'automation',
    platforms: ['instagram', 'tiktok', 'facebook'], platformLabel: 'tus redes',
    desc: 'Genera y publica posts/reels/stories todos los días con calendario.',
    capabilities: ['Calendario editorial automático', 'Posts/reels/stories', 'Hashtags y horarios óptimos', 'Repurpose 1 idea → varios formatos'],
    inputs: [{ key: 'frecuencia', label: 'Frecuencia', placeholder: 'diaria / 3x semana' }],
    buildInstruction: (p, v, url) => `Generá y publicá contenido (${v.frecuencia || 'diario'}) de ${prod(p)} en ${url || 'tus redes'}: posts, reels y stories con hashtags y horarios óptimos. Reutilizá cada idea en varios formatos.`,
  },
  {
    id: 'cart_recovery', name: 'Recuperación de carritos', kind: 'automation',
    platforms: ['whatsapp', 'email', 'shopify'], platformLabel: 'WhatsApp/Email',
    desc: 'Persigue cada carrito abandonado con secuencia multicanal.',
    capabilities: ['Detecta carrito abandonado', 'WhatsApp a los 30 min', 'Email a la hora', 'Oferta especial a las 24h'],
    inputs: [{ key: 'incentivo', label: 'Incentivo', placeholder: '10% off / envío gratis' }],
    buildInstruction: (p, v) => `Activá la recuperación de carritos abandonados de ${prod(p)}: WhatsApp a los 30 min, email a la hora y oferta (${v.incentivo || '10% off'}) a las 24h.`,
  },
  {
    id: 'crm_sync', name: 'CRM + pipeline', kind: 'tool',
    platforms: ['hubspot', 'salesforce'], platformLabel: 'tu CRM',
    desc: 'Ordena contactos y deals en un pipeline; nada se pierde.',
    capabilities: ['Crea/actualiza contactos y deals', 'Etapas y seguimiento automático', 'Lead scoring', 'Reportes de pipeline'],
    inputs: [{ key: 'etapas', label: 'Etapas del pipeline', placeholder: 'nuevo → contactado → propuesta → cierre' }],
    buildInstruction: (p, v, url) => `Estructurá el CRM/pipeline (${url || 'tu CRM'}) de ${prod(p)} con etapas: ${v.etapas || 'nuevo → contactado → propuesta → cierre'}. Cargá contactos/deals, automatizá seguimiento y aplicá lead scoring.`,
  },
  {
    id: 'copy_gen', name: 'Generador de copy', kind: 'tool',
    platforms: ['meta_ads', 'instagram', 'email'], platformLabel: 'ads/posts/email',
    desc: 'Copys de venta y anuncios con fórmula AIDA, listos para publicar.',
    capabilities: ['Titulares de alto CTR', 'Variantes para A/B', 'AIDA: atención→interés→deseo→acción', 'Adapta a cada canal'],
    inputs: [
      { key: 'canal', label: 'Canal', placeholder: 'anuncio / reel / email' },
      { key: 'angulo', label: 'Ángulo', placeholder: 'beneficio principal / objeción' },
    ],
    buildInstruction: (p, v) => `Generá copy ${v.canal || 'multicanal'} para ${prod(p)} con AIDA, ángulo "${v.angulo || 'beneficio principal'}"${p.offer ? `, oferta: ${p.offer}` : ''}. Entregá titular + variantes para A/B.`,
  },
  {
    id: 'canva_create', name: 'Crea con Canva', kind: 'tool',
    platforms: ['canva'], platformLabel: 'Canva',
    desc: 'Acceso directo a tu Canva vinculado para crear piezas de tu marca.',
    capabilities: ['Abre tu cuenta Canva', 'Diseña posts, reels, historias, flyers, logos', 'Usa tu identidad de marca', 'Exporta listo para publicar'],
    inputs: [{ key: 'pieza', label: 'Qué crear', placeholder: 'post promo, flyer, story, logo…' }],
    studioMode: 'create_confirm',
    buildInstruction: (p, v, url) => v.create === 'no'
      ? `Abrí Canva (${url || 'canva.com'}) para que el usuario diseñe ${v.pieza || 'sus piezas'} de ${prod(p)}.`
      : `En Canva (${url || 'canva.com'}) creá ${v.pieza || 'piezas de marca'} para ${prod(p)} con su identidad${p.offer ? ` y la oferta "${p.offer}"` : ''}, listas para publicar. Mostrá borradores al usuario antes de exportar.`,
  },
  {
    id: 'portfolio_manager', name: 'Gestionar Cartera/Portafolio', kind: 'agent',
    platforms: ['binance', 'coinbase', 'kraken', 'mercadolibre'], platformLabel: 'tu plataforma de inversión',
    desc: 'Acceso a tu plataforma de inversión + bots de estrategia (señales). NO ejecuta operaciones: propone, vos confirmás.',
    capabilities: [
      'Bot DCA: compra periódica para promediar costo',
      'Bot Grid: compra en bajas, vende en subas dentro de un rango',
      'Bot Swing/Holding: comprar barato, vender caro, recomprar en baja y vender en suba',
      'Watchlist + alertas de precio y señales',
      'Gestión de riesgo (stop-loss sugerido, tamaño de posición)',
    ],
    inputs: [
      { key: 'activos', label: 'Activos a seguir', placeholder: 'BTC, ETH, acciones…' },
      { key: 'riesgo', label: 'Perfil de riesgo', placeholder: 'conservador / moderado / agresivo' },
      { key: 'capital', label: 'Capital asignado (opcional)', placeholder: 'ej: $500' },
    ],
    studioMode: 'advisory',
    strategies: [
      { id: 'dca', label: 'DCA', desc: 'Compra periódica fija para promediar costo (menos timing, más disciplina).' },
      { id: 'grid', label: 'Grid', desc: 'Órdenes escalonadas: compra en cada baja, vende en cada suba dentro de un rango.' },
      { id: 'swing', label: 'Swing/Holding', desc: 'Comprar barato, vender caro; recomprar cuando baja y vender cuando sube, con confirmación.' },
    ],
    safetyNote: 'SellIA NUNCA ejecuta compras/ventas ni transferencias por su cuenta. Genera señales, alertas y la estrategia; cada operación la confirmás y ejecutás vos.',
    buildInstruction: (p, v, url) => `Gestión de cartera (sólo señales, NO ejecutar operaciones) en ${url || 'tu plataforma'}. Estrategia ${v.strategy || 'swing'}, activos: ${v.activos || 'BTC/ETH'}, riesgo ${v.riesgo || 'moderado'}${v.capital ? `, capital ${v.capital}` : ''}. Generá watchlist, niveles de compra/venta, stop-loss sugerido y alertas; proponé operaciones para que el usuario confirme.`,
  },
  {
    id: 'manychat_qualify', name: 'ManyChat: filtrar leads malos', kind: 'automation',
    platforms: ['manychat', 'instagram', 'facebook', 'whatsapp'], platformLabel: 'ManyChat (IG/FB/WA)',
    desc: 'Flujo en ManyChat que califica cada lead y descarta a los que nunca van a comprar — adaptado a si vendés bienes o servicios.',
    capabilities: [
      'Pregunta clave en 3 mensajes (necesidad/presupuesto/plazo)',
      'Descarta automático: sin presupuesto, fuera de zona, no-interesado',
      'Etiqueta y deriva SOLO leads calientes al vendedor',
      'Adapta el guion según el tipo de oferta (bien o servicio)',
    ],
    inputs: [
      { key: 'tipoOferta', label: 'Tipo de oferta', placeholder: 'bien / servicio' },
      { key: 'criterios', label: 'Criterios de calificación', placeholder: 'presupuesto, zona, decisor…', type: 'textarea' },
      { key: 'bienvenida', label: 'Bienvenida del bot', placeholder: '¡Hola! Antes de pasarte con un asesor…', type: 'textarea' },
    ],
    buildInstruction: (p, v, url) => `En ManyChat (${url || 'manychat.com'}) configurá un flujo de calificación de leads para ${prod(p)} (oferta: ${v.tipoOferta || (p.bizType === 'servicio' ? 'servicio' : 'bien')}). Bienvenida: "${v.bienvenida || 'Contame qué buscás 👇'}". Hacé 3-4 preguntas para evaluar: ${v.criterios || 'necesidad + presupuesto + plazo + decisor'}. Etiquetá: descartado / frío / tibio / caliente. Descartados reciben respuesta cordial (con motivo registrado) y NO van al vendedor. Solo CALIENTES se derivan a humano por WhatsApp${p.offer ? ` (mencionar oferta: ${p.offer})` : ''}.`,
  },
  {
    id: 'lead_capture', name: 'Captación inteligente de leads', kind: 'automation',
    platforms: ['manychat', 'instagram', 'whatsapp', 'meta_ads', 'google_ads'], platformLabel: 'tus canales',
    desc: 'Captura leads desde todos tus canales con lead magnet + scoring automático.',
    capabilities: [
      'Lead magnet activo (descargable, diagnóstico, demo o cupón)',
      'Captura desde IG DM, WhatsApp, ads y landing',
      'Scoring automático: frío / tibio / caliente',
      'Derivación: caliente → vendedor, tibio → nutrición, frío → contenido',
    ],
    inputs: [
      { key: 'magnet', label: 'Lead magnet', placeholder: 'guía, cupón, diagnóstico, demo…' },
      { key: 'canales', label: 'Canales de captura', placeholder: 'IG + WhatsApp + Landing' },
      { key: 'scoring', label: 'Criterios de scoring', placeholder: 'frío(0-3) tibio(4-7) caliente(8-10)' },
    ],
    buildInstruction: (p, v) => `Activá la captación de leads para ${prod(p)} con lead magnet "${v.magnet || 'guía gratis'}" en ${v.canales || 'IG + WhatsApp + Landing'}. Cada lead recibe scoring (${v.scoring || 'frío/tibio/caliente'}) según intención, presupuesto y momento. Calientes → vendedor; tibios → secuencia de nutrición; fríos → contenido de valor. Pedí consentimiento explícito de datos.`,
  },
  {
    id: 'brief_to_campaign', name: 'Brief → Campaña de marketing', kind: 'agent',
    platforms: ['meta_ads', 'google_ads', 'tiktok_ads', 'instagram'], platformLabel: 'tus cuentas de pauta',
    desc: 'Convierte un brief simple en una campaña 360° completa: estrategia + copys + creativos + landing + medición.',
    capabilities: [
      'Estrategia: objetivo, audiencias, canales, presupuesto, KPI',
      'Copys y guiones (AIDA) por canal',
      'Briefs de creativos (imágenes/video) listos para diseño',
      'Plan de medición + roadmap de optimización',
    ],
    inputs: [
      { key: 'objetivo', label: 'Objetivo de la campaña', placeholder: 'ventas / leads / awareness' },
      { key: 'publico', label: 'Público objetivo', placeholder: 'mujeres 25-40, GBA, interés fitness' },
      { key: 'presupuesto', label: 'Presupuesto total', placeholder: '$300 / $1.000 / $5.000' },
      { key: 'canales', label: 'Canales', placeholder: 'Meta + Google + orgánico' },
      { key: 'brief', label: 'Brief del usuario', placeholder: 'Qué querés lograr, plazos, oferta, restricciones…', type: 'textarea' },
    ],
    buildInstruction: (p, v) => `Convertí este brief en una campaña 360° para ${prod(p)}.
Objetivo: ${v.objetivo || 'ventas'} · Público: ${v.publico || 'definir'} · Presupuesto: ${v.presupuesto || '$300'} · Canales: ${v.canales || 'Meta + Google'}
${p.offer ? `Oferta: ${p.offer}` : ''}
Brief: "${v.brief || 'Sin detalles adicionales'}"

Entregá:
1) Estrategia (objetivo, audiencias, embudo, KPI principal y secundarios).
2) Copys por canal (titular + cuerpo + CTA, variantes A/B con AIDA).
3) Briefs de creativos (imagen/video/reel) — qué mostrar, gancho 3s, formato.
4) Landing/mensaje de conversión.
5) Plan de medición (UTM, eventos, dashboard) + roadmap de optimización a 7/14/30 días.

NO lances pauta sin confirmación explícita.`,
  },
  {
    id: 'master_seller_agent', name: 'Agente Vendedor Maestro', kind: 'agent',
    platforms: ['whatsapp', 'email', 'meta_ads', 'instagram', 'linkedin'], platformLabel: 'cualquier canal',
    desc: 'Agente maestro de ventas: responde como el mejor vendedor del mundo. Integra Belfort+SPIN+Hormozi+Vaynerchuk+Cialdini. Script + objeciones + cierre para CUALQUIER bien/servicio.',
    capabilities: [
      'Script maestro en 5 pasos (Rapport → Diagnóstico → Reframe → Oferta → Cierre)',
      'Tonalidad calibrada por etapa (curiosidad, comprensión, autoridad, entusiasmo, decisión)',
      'Manejo de 7 objeciones con respuesta maestra (sin presión)',
      'Oferta irresistible: sueño+prueba−tiempo−esfuerzo+bonos+garantía+escasez',
      'Cierre progresivo: pequeños síes → firma',
      'Seguimiento 48h post-cierre',
    ],
    inputs: [
      { key: 'producto', label: 'Qué vendés', placeholder: 'SaaS, coaching, producto físico, consultoría…' },
      { key: 'tipo', label: 'Tipo', placeholder: 'bien / servicio' },
      { key: 'audiencia', label: 'A quién le vendés', placeholder: 'PMEs, startups, consumidor final…' },
      { key: 'etapa', label: 'Etapa del cierre', placeholder: 'primer contacto / diagnóstico / oferta / cierre final' },
      { key: 'contexto', label: 'Contexto del cliente', placeholder: 'quién es, qué teme, qué desea, dinámicas…', type: 'textarea' },
    ],
    buildInstruction: (p, v) => `SOS el AGENTE VENDEDOR MAESTRO. Tu objetivo: generar un script de venta irresistible para ${v.producto || prod(p)}.

Contexto:
- Producto: ${v.producto || prod(p)} (tipo: ${v.tipo || p.bizType || 'bien/servicio'})
- Audiencia: ${v.audiencia || p.audience || 'a definir'}
- Etapa: ${v.etapa || 'primer_contacto'}
- Cliente: "${v.contexto || 'cliente estándar sin detalles'}"

TU IDENTIDAD: Mejor vendedor del mundo. Integras:
- Belfort: líneas rectas, 3 certezas, tonalidad, ritmo
- SPIN: descubrimiento profundo sin presión (situación → problema → implicación → payoff)
- Hormozi: oferta irresistible (sueño×probabilidad ÷ tiempo×esfuerzo)
- Vaynerchuk: deuda social, confianza genuina, múltiples toques
- Cialdini: 6 principios (reciprocidad, prueba social, autoridad, escasez, compromiso, empatía)
- Voss: calibración de tonalidad, empatía táctica, silencio estratégico

ENTREGÁ:

1) SCRIPT MAESTRO (5 pasos + tonalidad):
   PASO 1 — RAPPORT (tonalidad: curiosidad cálida): Apertura, genuino interés, sin agenda visible. 1-2 min.
   PASO 2 — DIAGNÓSTICO (tonalidad: comprensión empática): Preguntas SPIN, silencio largo (5 seg), escucha 70%. 5-10 min.
   PASO 3 — REFRAME (tonalidad: autoridad relajada): "Lo que no ves es…" Reencuadrá el problema. Cita caso similar. 2-3 min.
   PASO 4 — OFERTA (tonalidad: entusiasmo sincero): Sueño + Prueba + Tiempo − Esfuerzo + Bono + Garantía + Escasez. 2-3 min.
   PASO 5 — CIERRE (tonalidad: decisión clara): "¿Cuándo empezamos?" + Fecha exacta + Próximo paso. 1 min.

2) TONALIDAD (por paso, describe voz/ritmo/pausa):
   - Paso 1: Cálido, intrigado, sin prisa
   - Paso 2: Atento, validador, silencios largos
   - Paso 3: Seguro pero no arrogante, basado en datos
   - Paso 4: Ilusionado, honesto, con convicción
   - Paso 5: Directo, decidido, sin dudas

3) 7 OBJECIONES PROBABLES + RESPUESTA MAESTRA:
   Por cada objeción: [objeción] → [validación] → [diagnóstico de tipo: real/falsa/oculta] → [respuesta maestra] → [confirma: "¿eso resuelve?"]
   Ejemplo: "Es caro" → "Entiendo" → "Real (presupuesto limitado)" → "No es gasto, es inversión que recupera en [X meses]. Mira el caso de [cliente similar]" → "¿eso cambia?"

4) CIERRE + GARANTÍA + ESCASEZ:
   - Cierre: "Entonces, ¿cuándo empezamos? [fecha específica]"
   - Garantía real: 30/60/90 días dinero de vuelta O por resultado
   - Escasez honesta: cupo real / plazo real / bono que vence

5) SEGUIMIENTO (próximas 48h):
   - Mensajes de toque 1/2/3 si dice "me lo pienso"
   - Cada toque con razón nueva + valor nuevo

6) DIAGNÓSTICO DE VENTA:
   - ¿Es el caso de venta? (sí/no/depende → explica)
   - Si es sí: confianza de conversión ___% y por qué
   - Si es no: qué cambiaría el resultado

Sé honesto. Si el producto no encaja, lo decís. Si hay objeción sin solución, lo decís. Si falta contexto, preguntá.

COMIENZA AHORA.`,
  },
  {
    id: 'sales_system_builder', name: 'Constructor de Sistema de Venta', kind: 'tool',
    platforms: ['whatsapp', 'email', 'meta_ads'], platformLabel: 'tu método',
    desc: 'Elige el método óptimo (Belfort/SPIN/MEDDIC/Cardone/etc) según ticket, ciclo y decisores. Arma roadmap de venta 30/60/90 días.',
    capabilities: [
      'Diagnóstico de escenario: ticket · decisores · ciclo esperado',
      'Recomendación de método (15 frameworks: transaccional, consultativa, enterprise)',
      'Roadmap de 3 fases con acciones concretas por semana',
      '7 objeciones probables + scripts calibrados',
      'Métricas de seguimiento (tasa de avance, conversión por fase)',
    ],
    inputs: [
      { key: 'producto', label: 'Producto/servicio a vender', placeholder: 'CRM, consultoría, SaaS, coaching…' },
      { key: 'ticket', label: 'Ticket promedio', placeholder: 'USD 500 / $5.000 / $50.000+' },
      { key: 'decisores', label: 'Cuántos decisores esperados', placeholder: '1 / 2-3 / 5+' },
      { key: 'ciclo', label: 'Ciclo de venta esperado', placeholder: '7 días / 30 días / 90 días' },
      { key: 'tipo', label: 'Tipo de cliente', placeholder: 'PYME / Startup / Empresa / Consumidor final' },
    ],
    buildInstruction: (p, v) => `Diseñá el sistema de venta óptimo para ${v.producto || prod(p)}.

Escenario:
- Ticket: ${v.ticket || '$5k'}
- Decisores: ${v.decisores || '1-2'}
- Ciclo: ${v.ciclo || '30-60 días'}
- Tipo cliente: ${v.tipo || 'PYME/Startup'}

Entregá:
1) Diagnóstico: ¿transaccional o consultativa? ¿por qué?
2) Método recomendado (de 15 opciones: Belfort, SPIN, MEDDIC, Sandler, Cardone, Vaynerchuk, consultativa, etc.) + por qué es óptimo para este escenario.
3) Roadmap de 3 fases:
   - Fase 1 (semanas 1-2): prospección + toma de contacto + diagnóstico inicial
   - Fase 2 (semanas 3-6): profundización + propuesta + manejo de objeciones
   - Fase 3 (semanas 7+): cierre + negociación + firma
   Por cada semana: acciones concretas, canales, tono.
4) 7 objeciones probables en este escenario + script calibrado para cada una (no presión, honesto).
5) Métricas de seguimiento:
   - % que pasan de fase 1 a 2 (tasa de avance)
   - % que avanzan de 2 a 3 (calificación)
   - % cierre final (conversión)
   - Semanas promedio de ciclo real vs esperado
6) Banderas rojas: cuándo deberías dejar ir / pivotar / escalar a otro vendedor.

Frameworks disponibles (cita exacto): Straight Line (Belfort), Submarine (Sandler), SPIN, MEDDIC, 10X (Cardone), Debt Social (Vaynerchuk), PNL, Consultativa, Relationship-First, Objection Handling, Takeaway Close, Social Proof, Price Anchoring, Risk Reversal.`,
  },
  {
    id: 'impossible_sale', name: 'Vender lo invendible', kind: 'agent',
    platforms: ['whatsapp', 'instagram', 'meta_ads', 'email'], platformLabel: 'cualquier canal',
    desc: 'Genera ángulos para vender productos donde parecen innecesarios: arena al Sahara, agua al Amazonas, hielo a un esquimal. Usa reframe + identidad + ritual + storytelling.',
    capabilities: [
      '5 reframes de significado (ritual/estatus/recuerdo/arte/salud)',
      '5 palancas creativas (audiencia/categoría/propósito/tiempo/packaging)',
      'Oferta irresistible (Hormozi) + manejo de objeción "no lo necesito"',
      'Pitch final + script de cierre + casos reales análogos',
    ],
    inputs: [
      { key: 'producto', label: 'Producto a vender', placeholder: 'arena, agua, hielo, X…' },
      { key: 'contexto', label: 'Contexto del comprador (por qué parece invendible)', placeholder: 'vive en el desierto y ya tiene arena de sobra', type: 'textarea' },
      { key: 'audiencia', label: 'Audiencia (si querés cambiarla)', placeholder: 'turistas, peregrinos, conocedores, exportar a…' },
      { key: 'restricciones', label: 'Restricciones (qué no podés prometer)', placeholder: 'no certifico orgánico, sin envío internacional…', type: 'textarea' },
    ],
    buildInstruction: (p, v) => `Vendé "${v.producto || prod(p)}" a un comprador que "${v.contexto || 'aparentemente no lo necesita'}". Audiencia objetivo: ${v.audiencia || 'replanteable'}.
Restricciones REALES (no prometer fuera de esto): ${v.restricciones || 'sin restricciones declaradas'}.

Entregá:
1) Diagnóstico: ¿por qué "parece" invendible aquí? (1 frase).
2) 5 RE-FRAMES de significado del producto (ritual/estatus/recuerdo/arte/salud/regalo/identidad).
3) 5 PALANCAS aplicadas: audiencia / categoría / propósito / tiempo / packaging — con la opción más prometedora elegida y por qué.
4) Diferenciación extrema honesta: atributo único + historia contable (sin inventar lo que el producto no tiene).
5) Oferta irresistible (Hormozi): + sueño, + prueba, − tiempo, − esfuerzo, + bonos, + garantía, + escasez real.
6) Manejo de la OBJECIÓN "no lo necesito": reframe + prueba social del nuevo uso.
7) Pitch final en 1 párrafo (≤ 80 palabras).
8) Script de cierre WhatsApp/DM (3 mensajes).
9) 2-3 casos reales análogos que lo validan (Liquid Death, Svalbarði, Pet Rock, etc.).

Reglas: honestidad total. Si un ángulo requiere certificación/prueba que el producto no tiene, marcalo como "REQUIERE PROBAR". No inventes atributos.`,
  },
  {
    id: 'brand_identity', name: 'Generador de identidad de marca', kind: 'agent',
    platforms: ['canva', 'instagram'], platformLabel: 'Canva / tus redes',
    desc: 'Genera identidad de marca completa: propósito, tono, naming, paleta, tipografía, logo y brand kit.',
    capabilities: [
      'Propuesta de valor + propósito + tono de voz',
      'Naming/eslogan (opciones)',
      'Paleta de color + tipografía + estilo visual',
      'Brief de logo (opciones para Canva/diseñador)',
      'Brand kit exportable',
    ],
    inputs: [
      { key: 'vibe', label: 'Personalidad de marca', placeholder: 'confiable, aspiracional, divertida, premium…' },
      { key: 'publico', label: 'Público objetivo', placeholder: 'a quién le hablás' },
      { key: 'valores', label: 'Valores', placeholder: 'claridad, resultados, cercanía…' },
      { key: 'referencias', label: 'Referencias (marcas que te gustan)', placeholder: 'Apple por simpleza, Nike por energía…', type: 'textarea' },
    ],
    buildInstruction: (p, v) => `Generá la identidad de marca completa para ${prod(p)} (industria: ${p.industry || 'sin especificar'}).
Vibe: ${v.vibe || 'confiable y cercana'} · Público: ${v.publico || 'a definir'} · Valores: ${v.valores || 'claridad, resultados'}
Referencias: ${v.referencias || 'sin referencias'}

Entregá:
1) Propósito + propuesta de valor única (1 frase).
2) Tono de voz (3 do's y 3 dont's con ejemplos).
3) Naming + 3-5 opciones de eslogan.
4) Paleta de color (4-6 colores con códigos HEX y uso).
5) Tipografía (títulos + cuerpo).
6) Estilo visual (mood + 3 referencias).
7) Brief de logo (3 conceptos para que el usuario pida en Canva o a un diseñador).
8) Brand kit (resumen exportable).

Mostrá las opciones para que el usuario elija; no registres marca.`,
  },
]

// Mezcla la metadata de excelencia en cada herramienta.
for (const t of TOOLS) Object.assign(t, META[t.id] ?? {})

export const TOOL_BY_ID: Record<string, GrowthTool> = Object.fromEntries(TOOLS.map(t => [t.id, t]))

/** Resuelve la URL/cuenta del perfil anexada a una herramienta (primera plataforma con link). */
export const accountUrlFor = (tool: GrowthTool, p: BusinessProfile | null): string => {
  if (!p) return ''
  const presets = [...p.salesPlatforms, ...p.adPlatforms, ...p.socialLinks]
  // 1) match exacto por id de preset
  for (const pid of tool.platforms) {
    const m = presets.find(l => l.enabled && l.url && l.id === pid)
    if (m) return m.url
  }
  // 2) custom links: match por dominio que contenga el id de plataforma (ej. binance.com)
  for (const l of (p.customLinks ?? [])) {
    if (!l.enabled || !l.url) continue
    const host = l.url.toLowerCase()
    if (tool.platforms.some(pid => host.includes(pid))) return l.url
  }
  return ''
}
