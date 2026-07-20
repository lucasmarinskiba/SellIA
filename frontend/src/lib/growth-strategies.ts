/**
 * Biblioteca de estrategias de crecimiento — conocimiento accionable.
 * Curado en frontend (Vercel-safe), mapeado a las categorías reales del cerebro
 * (backend/app/core/knowledge/library/*.json). Nutre el Motor de Crecimiento.
 */

export type StrategyTopic =
  | 'salir_quiebra' | 'mas_clientes' | 'vender_sin_vender' | 'referente' | 'branding' | 'contenido' | 'ventas'
  | 'finanzas' | 'activos_pasivos' | 'estructura_negocio' | 'emprendimiento'
  | 'posicionamiento_redes' | 'posicionamiento_ventas' | 'productos_ganadores'
  | 'cripto' | 'blockchain' | 'costos_presupuesto' | 'estimacion_presupuestaria'
  | 'bienes_raices' | 'inversiones'

export interface Strategy {
  id: string
  title: string
  topic: StrategyTopic
  principles: string[]
  tactics: string[]
  sourceHint: string
  /** Tags de relevancia: bizType ('producto'|'servicio'|'ambos'), industrias o keywords del producto. */
  applies?: string[]
  /** Ids reales del registry (agentes/automatizaciones/skills) que esta estrategia activa. */
  activates?: string[]
}

export const STRATEGIES: Strategy[] = [
  {
    id: 'salir_quiebra', title: 'Salir de la quiebra', topic: 'salir_quiebra',
    principles: [
      'En crisis, caja primero: cada acción tiene que traer ingreso o ahorro ya.',
      'Concentrá el fuego en lo que más rápido convierte; cortá lo que no.',
      'Vendé lo que ya tenés a quien ya te conoce antes de buscar extraños.',
    ],
    tactics: [
      'Oferta de emergencia con urgencia real a tu lista/clientes viejos',
      'Reactivar leads y carritos abandonados hoy',
      'Pausar todo gasto que no genere retorno medible en 7 días',
      'Pedir referidos y reseñas a clientes felices',
    ],
    sourceHint: 'Estadistas en crisis · Buffett (caja) · venta directa',
  },
  {
    id: 'mas_clientes', title: 'Conseguir más clientes (cada día)', topic: 'mas_clientes',
    principles: [
      'Crecimiento = adquisición sistemática, no golpes de suerte.',
      'Duplicá el canal que ya funciona antes de abrir uno nuevo.',
      'Mejorá 1% por día: medir, iterar, repetir.',
    ],
    tactics: [
      'Identificar el canal con mejor CAC y duplicar presupuesto/tiempo ahí',
      'Cadencia de outbound diaria (DMs/emails) a clientes ideales',
      'Lead magnet que captura contacto antes de vender',
      'Seguimiento de 5 toques: la mayoría cierra después del 5º',
    ],
    sourceHint: 'Embudos · SPIN/Challenger · Cardone (follow-up)',
  },
  {
    id: 'vender_sin_vender', title: 'Vender sin vender (bajar gasto en ads)', topic: 'vender_sin_vender',
    principles: [
      'La mejor venta no parece venta: aportás valor y el cliente pide comprar.',
      'Audiencia propia (email/comunidad) = tráfico gratis y recurrente.',
      'El contenido y el boca a boca bajan el CAC y la dependencia de pauta.',
    ],
    tactics: [
      'Contenido educativo/entretenido que resuelve el problema del cliente',
      'SEO/keywords para tráfico orgánico sostenido',
      'Programa de referidos con incentivo (boca a boca sistemático)',
      'Email/lista propia: secuencias de valor que venden solas',
      'Comunidad/grupo donde el cliente ideal ya está',
    ],
    sourceHint: 'Inbound · Godin (permiso) · Hormozi (give-give-ask)',
  },
  {
    id: 'referente', title: 'Convertirte en referente / autoridad', topic: 'referente',
    principles: [
      'La autoridad se construye enseñando en público, consistentemente.',
      'Ser el primero en una categoría > ser el mejor: creá tu categoría.',
      'La gente compra a quien percibe como experto del tema.',
    ],
    tactics: [
      'Publicar insights y casos propios con frecuencia (thought leadership)',
      'Colaboraciones, podcasts, entrevistas y PR en tu nicho',
      'Documentar resultados y procesos (transparencia = confianza)',
      'Ocupar una palabra/posición en la mente del mercado',
    ],
    sourceHint: 'Ries-Trout (posicionamiento) · Vaynerchuk · branding',
  },
  {
    id: 'branding', title: 'Construcción de marca / branding', topic: 'branding',
    principles: [
      'Posicionamiento: ocupá una casilla clara en la mente del prospecto.',
      'Diferenciate o competís solo por precio.',
      'Consistencia en mensaje y estética construye marca con el tiempo.',
    ],
    tactics: [
      'Definir propuesta y atributo diferenciador en 1 frase',
      'Narrativa de marca con propósito (por qué) e identidad del cliente',
      'Identidad visual y tono consistentes en todos los canales',
      'Foco: una marca fuerte dice una sola cosa con potencia',
    ],
    sourceHint: 'Ries & Trout · Trout & Rivkin · Sinek (Start With Why)',
  },
  {
    id: 'contenido', title: 'Estrategia de contenido', topic: 'contenido',
    principles: [
      'El primer objetivo del contenido es frenar el scroll (gancho en 3-5s).',
      'Adaptá el mensaje al grado de conciencia del prospecto.',
      'Una sola idea + un solo llamado a la acción por pieza.',
    ],
    tactics: [
      'Pilares de contenido: educar, inspirar, vender (regla 3:1)',
      'Calendario consistente > viralidad esporádica',
      'Repurpose: 1 idea → reel, post, carrusel, email',
      'Copy AIDA + prueba social específica (números, testimonios)',
    ],
    sourceHint: 'Schwartz · Ogilvy · Sugarman · AIDA',
  },
  {
    id: 'ventas', title: 'Ser muy bueno vendiendo', topic: 'ventas',
    principles: [
      'El que pregunta controla: descubrí el dolor antes de presentar.',
      'La gente compra la certeza del vendedor (transferencia de certeza).',
      'Las objeciones son pedidos de más certeza, no rechazos.',
    ],
    tactics: [
      'SPIN: situación → problema → implicación → necesidad',
      'Calificar (MEDDIC) antes de invertir tiempo en un trato',
      'Manejo de objeciones por looping (elevar certeza → re-cierre)',
      'Vender valor/ROI, no precio; anclar contra el costo de no actuar',
    ],
    sourceHint: 'Belfort (línea recta) · Rackham (SPIN) · MEDDIC',
  },
  {
    id: 'finanzas', title: 'Finanzas del negocio (no quebrar)', topic: 'finanzas',
    principles: [
      'La caja manda: un negocio rentable puede quebrar por falta de liquidez.',
      'Separá finanzas personales de las del negocio.',
      'Lo que no se mide no se controla: P&L, caja y márgenes al día.',
    ],
    tactics: ['Proyección de flujo de caja y runway', 'Margen real por producto/servicio', 'Reserva de emergencia (colchón)', 'Tablero financiero en vivo'],
    sourceHint: 'Buffett · finanzas para emprendedores',
    applies: ['producto', 'servicio', 'ambos'], activates: ['agent.expert.wealth_strategist', 'skill.tool.cashflow_planner', 'automation.financial_dashboard'],
  },
  {
    id: 'activos_pasivos', title: 'Activos vs pasivos (construir patrimonio)', topic: 'activos_pasivos',
    principles: [
      'Activo = pone dinero en tu bolsillo; pasivo = lo saca. Comprá activos.',
      'Reinvertí utilidades en lo que genera más ingreso.',
      'Deuda buena financia activos productivos; la mala financia consumo.',
    ],
    tactics: ['Clasificar activos/pasivos del negocio', 'Convertir gasto en activo (contenido, marca, sistemas)', 'Plan de reinversión', 'Reducir pasivos improductivos'],
    sourceHint: 'Kiyosaki · Buffett · contabilidad básica',
    applies: ['producto', 'servicio', 'ambos'], activates: ['agent.expert.wealth_strategist', 'skill.tool.asset_liability_tracker'],
  },
  {
    id: 'costos_presupuesto', title: 'Costos y presupuesto', topic: 'costos_presupuesto',
    principles: [
      'Sin conocer tu costo unitario no sabés si ganás o perdés en cada venta.',
      'Fijos vs variables: bajá el punto de equilibrio.',
      'Presupuestá por objetivo, no por inercia.',
    ],
    tactics: ['Costeo unitario y margen', 'Punto de equilibrio (breakeven)', 'Presupuesto por canal/campaña', 'Control de desvíos mensual'],
    sourceHint: 'Costos · pricing · control de gestión',
    applies: ['producto', 'servicio', 'ambos'], activates: ['agent.expert.budget_analyst', 'skill.tool.cost_estimator', 'skill.tool.breakeven_calc', 'automation.budget_costing'],
  },
  {
    id: 'estimacion_presupuestaria', title: 'Estimación y análisis presupuestario', topic: 'estimacion_presupuestaria',
    principles: [
      'Proyectá escenarios (pesimista/base/optimista) antes de gastar.',
      'Compará real vs presupuestado y ajustá rápido.',
      'Asigná capital al canal con mejor retorno.',
    ],
    tactics: ['Forecast de ingresos y egresos', 'Análisis de varianza real vs plan', 'Asignación de presupuesto por ROI', 'Alertas de desvío'],
    sourceHint: 'FP&A · budgeting',
    applies: ['producto', 'servicio', 'ambos'], activates: ['agent.expert.budget_analyst', 'skill.tool.budget_forecaster', 'skill.tool.forecast'],
  },
  {
    id: 'estructura_negocio', title: 'Estructuración del negocio', topic: 'estructura_negocio',
    principles: [
      'Estructura legal/fiscal correcta protege y escala.',
      'Procesos documentados = negocio que no depende de vos.',
      'Separá roles: dueño (visión) vs operador (ejecución).',
    ],
    tactics: ['Elegir figura legal/fiscal adecuada', 'Documentar procesos clave (SOPs)', 'Delegar con la ley del quién', 'Sistemas y automatización'],
    sourceHint: 'Gerber (E-Myth) · estructura societaria',
    applies: ['producto', 'servicio', 'ambos'], activates: ['agent.expert.startup_architect', 'automation.business_structuring', 'skill.computer_use.business_models'],
  },
  {
    id: 'emprendimiento', title: 'Formación de emprendimientos', topic: 'emprendimiento',
    principles: [
      'Validá demanda antes de invertir fuerte (MVP).',
      'Resolvé un problema real y doloroso.',
      'Iterá rápido con feedback del mercado.',
    ],
    tactics: ['MVP y validación con clientes reales', 'Modelo de negocio (canvas)', 'Unit economics desde el día 1', 'Pitch para inversores/aliados'],
    sourceHint: 'Lean Startup · business_models · investor_pitch',
    applies: ['producto', 'servicio', 'ambos'], activates: ['agent.expert.startup_architect', 'agent.expert.investor_pitch', 'skill.computer_use.business_models'],
  },
  {
    id: 'productos_ganadores', title: 'Encontrar productos ganadores', topic: 'productos_ganadores',
    principles: [
      'Vendé lo que el mercado YA quiere comprar (demanda probada).',
      'Margen + demanda + baja competencia = producto ganador.',
      'Validá con datos, no con corazonadas.',
    ],
    tactics: ['Research de tendencias y demanda', 'Análisis de competencia y margen', 'Testear ángulos/creativos antes de stockear', 'Escalar el ganador, matar lo flojo'],
    sourceHint: 'Product research · e-commerce',
    applies: ['producto', 'ambos', 'ecommerce', 'dropshipping', 'indumentaria', 'retail'],
    activates: ['agent.expert.product_scout', 'skill.tool.winning_product_finder', 'automation.research_winning_products'],
  },
  {
    id: 'posicionamiento_ventas', title: 'Posicionarte en plataformas de venta', topic: 'posicionamiento_ventas',
    principles: [
      'En marketplaces, el algoritmo premia conversión y reputación.',
      'Título, fotos y reseñas mueven el ranking.',
      'Precio competitivo + envío rápido = más visibilidad.',
    ],
    tactics: ['Optimizar listing (SEO de marketplace)', 'Conseguir reseñas y rating alto', 'Precio y envío competitivos', 'Responder preguntas al instante'],
    sourceHint: 'Mercado Libre · Amazon · e-commerce',
    applies: ['producto', 'ambos', 'ecommerce', 'retail'],
    activates: ['agent.expert.crm_builder', 'skill.tool.crm_sync', 'automation.inventory_sync', 'automation.review_responder'],
  },
  {
    id: 'posicionamiento_redes', title: 'Posicionarte en redes sociales', topic: 'posicionamiento_redes',
    principles: [
      'Consistencia + valor > viralidad esporádica.',
      'El algoritmo premia retención: gancho en 3s.',
      'Nicho claro = audiencia que compra.',
    ],
    tactics: ['Pilares de contenido y calendario', 'Hooks y formatos que retienen', 'Interacción y comunidad', 'Perfil optimizado a conversión (bio/CTA)'],
    sourceHint: 'Vaynerchuk · creator economy',
    applies: ['producto', 'servicio', 'ambos'],
    activates: ['agent.expert.viral_video', 'skill.tool.copy_gen', 'skill.tool.video_reels', 'automation.social_content'],
  },
  {
    id: 'inversiones', title: 'Inversiones (hacer crecer el capital)', topic: 'inversiones',
    principles: [
      'Margen de seguridad + círculo de competencia (Buffett).',
      'Interés compuesto: tiempo > timing.',
      'Diversificá; no concentres todo en una idea.',
    ],
    tactics: ['Definir perfil de riesgo y horizonte', 'Cartera diversificada', 'Reinversión sistemática', 'Educación financiera continua'],
    sourceHint: 'Buffett · Graham · investing/wealth',
    applies: ['producto', 'servicio', 'ambos', 'finanzas', 'inversión'],
    activates: ['agent.expert.financial_planner', 'agent.expert.wealth_strategist', 'skill.computer_use.financial_markets'],
  },
  {
    id: 'bienes_raices', title: 'Bienes raíces', topic: 'bienes_raices',
    principles: [
      'El inmueble se gana en la compra (precio + ubicación).',
      'Cap rate y flujo > especulación de precio.',
      'Apalancamiento prudente multiplica retorno.',
    ],
    tactics: ['Análisis de cap rate y comparables', 'Evaluar plusvalía y zona', 'Estructura de financiación', 'Alquiler vs flipping según objetivo'],
    sourceHint: 'real_estate · inversión inmobiliaria',
    applies: ['inmobiliaria', 'real estate', 'bienes raices', 'propiedades', 'ambos'],
    activates: ['agent.expert.realestate_analyst', 'skill.tool.property_valuator', 'automation.real_estate_scan', 'skill.computer_use.real_estate'],
  },
  {
    id: 'cripto', title: 'Criptomonedas (educativo)', topic: 'cripto',
    principles: [
      'Sólo invertís lo que podés perder; gestión de riesgo primero.',
      'DYOR: fundamentos on-chain > hype.',
      'Custodia y seguridad son parte del retorno.',
    ],
    tactics: ['Watchlist y métricas on-chain', 'Tesis de inversión y gestión de riesgo', 'Seguridad de wallets/custodia', 'Educación continua (sin ejecutar trades automáticos)'],
    sourceHint: 'crypto · risk_management (sólo lectura)',
    applies: ['cripto', 'crypto', 'fintech', 'blockchain', 'inversión'],
    activates: ['agent.expert.blockchain_analyst', 'skill.tool.crypto_screener', 'automation.crypto_watchlist', 'skill.computer_use.crypto'],
  },
  {
    id: 'blockchain', title: 'Tecnología blockchain', topic: 'blockchain',
    principles: [
      'Blockchain sirve donde hace falta confianza sin intermediario.',
      'No toda solución necesita blockchain: evaluá el caso de uso.',
      'Contratos inteligentes automatizan acuerdos verificables.',
    ],
    tactics: ['Identificar caso de uso real (pagos, trazabilidad, tokenización)', 'Elegir red/stack adecuado', 'Pilotos pequeños antes de escalar', 'Cumplimiento y seguridad'],
    sourceHint: 'blockchain · web3',
    applies: ['blockchain', 'cripto', 'web3', 'fintech', 'software', 'tecnología'],
    activates: ['agent.expert.blockchain_analyst', 'agent.expert.app_builder'],
  },
]

export const STRATEGY_BY_ID: Record<string, Strategy> = Object.fromEntries(STRATEGIES.map(s => [s.id, s]))

export interface RelevanceCtx { bizType: string; industry: string; product: string; goals: string[] }

/** Puntúa la relevancia de una estrategia para el negocio (mayor = más relevante). */
export const scoreStrategy = (s: Strategy, ctx: RelevanceCtx): number => {
  const hay = `${ctx.industry} ${ctx.product}`.toLowerCase()
  let score = 0
  if (!s.applies || s.applies.length === 0) score += 1 // universal
  for (const a of s.applies ?? []) {
    if (a === ctx.bizType) score += 2
    else if (a === 'producto' || a === 'servicio' || a === 'ambos') { if (ctx.bizType === 'ambos') score += 1 }
    else if (hay.includes(a.toLowerCase())) score += 3 // industria/keyword match
  }
  if (hay.includes(s.topic.replace(/_/g, ' '))) score += 1
  return score
}

/** Estrategias ordenadas por relevancia al negocio, con flag `relevant`. */
export const relevantStrategies = (ctx: RelevanceCtx): Array<{ strategy: Strategy; score: number; relevant: boolean }> =>
  STRATEGIES
    .map(s => { const score = scoreStrategy(s, ctx); return { strategy: s, score, relevant: score >= 2 } })
    .sort((a, b) => b.score - a.score)
