"""Computer Use — Knowledge Base / Skills.

Conocimiento de dominio inyectado en el contexto del agente de visión para
que actúe como vendedor experto: estrategias de venta, copywriting/creador
de contenido, manejo de redes sociales, ads y plataformas de venta.

El brief se construye en tiempo de ejecución a partir de la tarea y la URL
actual, manteniéndolo compacto (los modelos de visión tienen presupuesto de
tokens limitado). Es aditivo: no rompe ningún provider existente.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.parse import urlparse


@dataclass(frozen=True)
class SkillDomain:
    """Un área de competencia del agente."""

    key: str
    title: str
    keywords: List[str]            # disparadores en la tarea/URL
    principles: List[str]          # reglas accionables, una línea cada una
    platforms: List[str] = field(default_factory=list)


# ── Estrategias de venta ────────────────────────────────────────────────
SALES_STRATEGY = SkillDomain(
    key="sales_strategy",
    title="Estrategia de Ventas",
    keywords=[
        "venta", "vender", "lead", "prospecto", "cliente", "cierre", "deal",
        "objecion", "objeción", "seguimiento", "follow", "crm", "pipeline",
        "cotizacion", "cotización", "presupuesto", "negocio",
    ],
    principles=[
        "Califica con BANT: Budget, Authority, Need, Timeline antes de invertir esfuerzo.",
        "Estructura el mensaje con AIDA: Atención, Interés, Deseo, Acción.",
        "Usa SPIN en descubrimiento: Situación, Problema, Implicación, Necesidad-beneficio.",
        "Vende el resultado y el ROI, no las características.",
        "Ante objeciones aplica sentir-sintieron-descubrieron y reencuadra el valor.",
        "Cierra con un único CTA claro y crea urgencia legítima (stock, cupo, fecha).",
        "Haz seguimiento en cadencia: día 1, 3, 7, 14; nunca dejes un lead sin próximo paso.",
        "Personaliza con el nombre, la empresa y el dolor específico del prospecto.",
    ],
)

# ── Creador de contenido / copywriting ──────────────────────────────────
CONTENT_CREATOR = SkillDomain(
    key="content_creator",
    title="Creación de Contenido",
    keywords=[
        "post", "publicacion", "publicación", "contenido", "copy", "caption",
        "reel", "story", "historia", "video", "guion", "guión", "creativo",
        "banner", "diseño", "diseno", "carrusel", "hashtag", "blog", "articulo",
        "artículo", "email", "newsletter",
    ],
    principles=[
        "Engancha en los primeros 3 segundos / primera línea o pierdes al lector.",
        "Fórmulas de gancho: pregunta provocadora, dato sorprendente, dolor + promesa.",
        "Estructura: Hook → Valor → Prueba (social/caso) → CTA único.",
        "Una sola idea por pieza; claridad sobre creatividad.",
        "CTA explícito: comenta, guarda, escribe 'INFO', visita el link.",
        "3-5 hashtags relevantes y de nicho superan a 30 genéricos.",
        "Escribe para escaneo: frases cortas, saltos de línea, emojis con moderación.",
        "Adapta tono y formato a la plataforma; no recicles el mismo copy en todas.",
    ],
)

# ── Manejo de redes sociales ────────────────────────────────────────────
SOCIAL_MEDIA = SkillDomain(
    key="social_media",
    title="Gestión de Redes Sociales",
    keywords=[
        "instagram", "facebook", "tiktok", "social", "red social", "perfil",
        "seguidores", "dm", "mensaje directo", "comentario", "engagement",
        "programar", "calendario", "comunidad",
    ],
    principles=[
        "Optimiza el perfil primero: foto, bio con propuesta de valor y link.",
        "Responde DMs y comentarios rápido; la velocidad sube el alcance.",
        "Publica en horarios de mayor actividad de la audiencia.",
        "Mezcla formatos: reels para alcance, carruseles para valor, stories para cercanía.",
        "Convierte engagement en conversación y la conversación en venta por DM.",
        "Nunca uses credenciales reales sin confirmación; si pide login, detente y avisa.",
    ],
    platforms=["instagram", "facebook", "tiktok"],
)

# ── Manejo de ads / paid media ──────────────────────────────────────────
ADS_MANAGEMENT = SkillDomain(
    key="ads_management",
    title="Gestión de Publicidad (Ads)",
    keywords=[
        "ads", "anuncio", "anuncios", "campaña", "campana", "publicidad",
        "meta ads", "google ads", "tiktok ads", "presupuesto diario", "puja",
        "roas", "cpa", "cpc", "ctr", "conversion", "conversión", "pixel",
        "audiencia", "segmentacion", "segmentación", "retargeting",
    ],
    principles=[
        "Define el objetivo de campaña antes de crear: tráfico, leads o ventas.",
        "Empieza con presupuesto de prueba; escala solo lo que da ROAS positivo.",
        "Estructura cuenta: Campaña (objetivo) → Conjunto (audiencia/budget) → Anuncio (creativo).",
        "Prueba 3-5 creativos por conjunto y deja que el algoritmo aprenda 3-7 días.",
        "Verifica que el pixel/conversión esté activo antes de gastar.",
        "Optimiza por CPA/ROAS, no por CTR; el clic barato no paga las cuentas.",
        "Usa retargeting de visitantes y lookalikes de compradores para escalar.",
        "Nunca aumentes presupuesto sin confirmación del usuario: gasta dinero real.",
    ],
    platforms=["google_ads", "meta_ads", "tiktok_ads"],
)

# ── Plataformas de venta / e-commerce ───────────────────────────────────
SALES_PLATFORMS = SkillDomain(
    key="sales_platforms",
    title="Plataformas de Venta / E-commerce",
    keywords=[
        "shopify", "mercadolibre", "mercado libre", "amazon", "hotmart",
        "tienda", "producto", "catalogo", "catálogo", "publicacion",
        "stock", "inventario", "precio", "envio", "envío", "checkout",
        "orden", "pedido", "marketplace",
    ],
    principles=[
        "Título con keyword + beneficio; las primeras palabras pesan en el buscador.",
        "Fotos claras, fondo limpio, múltiples ángulos; la imagen vende primero.",
        "Descripción con beneficios, especificaciones y respuestas a dudas frecuentes.",
        "Precio competitivo verificado contra la competencia visible en la plataforma.",
        "Completa stock, variantes y envío para no perder el buy box / posición.",
        "Responde preguntas de compradores rápido; impacta la reputación y el ranking.",
        "Nunca confirmes compras, cobros o cambios de precio masivos sin aprobación.",
    ],
    platforms=["shopify", "mercadolibre", "amazon", "hotmart"],
)

# ── Manejo de herramientas (genérico web) ───────────────────────────────
TOOL_HANDLING = SkillDomain(
    key="tool_handling",
    title="Manejo de Herramientas Web",
    keywords=[
        "canva", "formulario", "form", "dashboard", "panel", "exportar",
        "descargar", "subir", "configurar", "ajustes", "integrar", "conectar",
        "automatizar", "automatizacion", "automatización",
    ],
    principles=[
        "Prefiere acciones DOM-precisas (click_selector/click_text/fill) a adivinar píxeles.",
        "Espera a que el elemento exista (wait_for_selector) antes de interactuar.",
        "Cierra primero popups, cookies y banners; luego ejecuta la tarea.",
        "Tras una acción, espera a que la página se estabilice antes del próximo paso.",
        "Si te trabas en el mismo estado, cambia de enfoque en vez de repetir.",
        "No descargues ejecutables ni archivos desconocidos.",
    ],
)


# ── Prospección / SDR (generación de leads) ─────────────────────────────
PROSPECTING = SkillDomain(
    key="prospecting",
    title="Prospección / SDR",
    keywords=[
        "prospectar", "prospeccion", "prospección", "buscar clientes",
        "generar leads", "lead gen", "sdr", "lista de", "directorio",
        "linkedin", "scraping de contactos", "base de datos de clientes",
        "nicho", "buyer persona", "publico objetivo", "público objetivo",
    ],
    principles=[
        "Define el ICP (perfil de cliente ideal) antes de prospectar: sector, tamaño, dolor.",
        "Prioriza leads por fit + señales de intención (crecimiento, vacantes, posts).",
        "Multicanal: combina LinkedIn, web, marketplaces y referidos.",
        "Registra cada lead con fuente, contacto y motivo de calce para trazabilidad.",
        "No recopiles datos sensibles ni imágenes faciales; respeta privacidad.",
        "Calidad sobre cantidad: 20 leads bien calificados rinden más que 200 fríos.",
    ],
)

# ── Outreach en frío (email / DM) ───────────────────────────────────────
OUTREACH = SkillDomain(
    key="outreach",
    title="Outreach en Frío",
    keywords=[
        "outreach", "cold email", "correo en frio", "correo en frío",
        "mensaje en frio", "mensaje en frío", "primer contacto", "secuencia",
        "cadencia", "plantilla de mensaje", "asunto", "subject", "dm frio",
        "dm frío", "invitacion", "invitación", "networking",
    ],
    principles=[
        "Asunto corto y curioso; decide si abren o no (4-7 palabras).",
        "Primera línea sobre EL prospecto, no sobre vos; personaliza con un detalle real.",
        "Un solo CTA suave: pedí 15 min o una respuesta de sí/no.",
        "Mensaje breve (50-90 palabras); el muro de texto mata la respuesta.",
        "Secuencia de 3-4 toques con valor nuevo en cada uno, no 'solo haciendo seguimiento'.",
        "Nunca envíes a granel sin confirmación; respeta opt-out y anti-spam.",
    ],
)

# ── Negociación / cierre / pricing ──────────────────────────────────────
NEGOTIATION = SkillDomain(
    key="negotiation",
    title="Negociación y Cierre",
    keywords=[
        "negociar", "negociacion", "negociación", "descuento", "precio",
        "pricing", "propuesta", "cotizar", "cotizacion", "cotización",
        "cerrar", "cierre", "contrato", "objecion de precio", "regateo",
        "condiciones", "terminos", "términos",
    ],
    principles=[
        "Ancla alto: presenta primero el valor y el precio lista, luego ajustá.",
        "No bajes precio sin contrapartida (volumen, plazo, testimonio, pago anticipado).",
        "Vendé el costo de NO actuar; cuantificá la pérdida de seguir igual.",
        "Ofrecé 3 opciones (bueno/mejor/premium); el ancla del medio suele ganar.",
        "Aislá la objeción real: '¿si resolvemos esto, avanzamos?' antes de ceder.",
        "Cerrá con próximo paso concreto y fecha; el silencio mata el deal.",
        "Compromisos de pago/contrato siempre requieren confirmación del usuario.",
    ],
)

# ── Customer Success / retención / upsell ───────────────────────────────
CUSTOMER_SUCCESS = SkillDomain(
    key="customer_success",
    title="Customer Success / Retención",
    keywords=[
        "retencion", "retención", "fidelizar", "fidelizacion", "fidelización",
        "postventa", "post venta", "soporte", "onboarding", "upsell",
        "cross sell", "cross-sell", "renovacion", "renovación", "churn",
        "reseña", "review", "testimonio", "nps", "recompra",
    ],
    principles=[
        "El primer valor rápido (quick win) define si el cliente se queda.",
        "Seguimiento proactivo: contactá antes de que aparezca el problema.",
        "Detectá señales de churn (uso bajo, quejas) y actuá temprano.",
        "Upsell cuando el cliente ya tuvo éxito, no antes; ofrecé el siguiente nivel.",
        "Pedí reseñas y testimonios en el pico de satisfacción.",
        "Un cliente retenido cuesta menos que uno nuevo; prioriza la base existente.",
    ],
)

# ── Inteligencia competitiva / market research ──────────────────────────
MARKET_INTEL = SkillDomain(
    key="market_intel",
    title="Inteligencia de Mercado",
    keywords=[
        "competencia", "competidor", "competidores", "benchmark", "mercado",
        "research", "investigacion", "investigación", "analisis de mercado",
        "análisis de mercado", "precios de la competencia", "tendencia",
        "tendencias", "demanda", "comparar", "espionaje",
    ],
    principles=[
        "Mapeá 3-5 competidores: oferta, precio, propuesta de valor, reseñas.",
        "Buscá los huecos: qué prometen y no cumplen según sus reseñas.",
        "Compară precios visibles para posicionar el tuyo con criterio.",
        "Detectá tendencias de demanda (búsquedas, hashtags, más vendidos).",
        "Sintetizá hallazgos en oportunidades accionables, no en datos sueltos.",
        "Usá solo información pública; no accedas a fuentes restringidas.",
    ],
)

# ── SEO / marketing de contenidos ───────────────────────────────────────
SEO_MARKETING = SkillDomain(
    key="seo_marketing",
    title="SEO y Marketing de Contenidos",
    keywords=[
        "seo", "posicionamiento", "keyword", "palabra clave", "ranking",
        "google", "blog", "trafico organico", "tráfico orgánico",
        "meta description", "backlink", "indexar", "serp", "contenido evergreen",
    ],
    principles=[
        "Una keyword principal por página, alineada con la intención de búsqueda.",
        "Keyword en título, H1, primer párrafo y URL; sin sobrecargar (no keyword stuffing).",
        "Responde la intención del usuario mejor que el top 3 actual.",
        "Title y meta description atractivos suben el CTR en resultados.",
        "Contenido útil y actualizado gana a la cantidad; calidad escala el orgánico.",
        "Enlaza interno hacia páginas de conversión.",
    ],
)

# ── Analítica / reporting / KPIs ────────────────────────────────────────
ANALYTICS = SkillDomain(
    key="analytics",
    title="Analítica y Reporting",
    keywords=[
        "reporte", "reporting", "informe", "metrica", "métrica", "metricas",
        "métricas", "kpi", "dashboard de ventas", "conversion", "conversión",
        "embudo", "funnel", "analytics", "estadistica", "estadística",
        "resultados", "performance", "roi",
    ],
    principles=[
        "Define la métrica norte (revenue/leads) y mide todo contra ella.",
        "Sigue el embudo completo: impresiones → clics → leads → ventas.",
        "Compará contra período anterior y meta; el número solo no dice nada.",
        "Aísla la palanca con mayor impacto antes de optimizar lo menor.",
        "Reporte accionable: insight + recomendación, no solo gráficos.",
        "Verifica que el tracking (pixel/eventos) esté activo antes de confiar en los datos.",
    ],
)

# ── CRM / data ops / higiene de datos ───────────────────────────────────
CRM_OPS = SkillDomain(
    key="crm_ops",
    title="CRM / Operaciones de Datos",
    keywords=[
        "crm", "cargar datos", "actualizar registro", "pipeline", "etapa",
        "estado del lead", "data entry", "planilla", "spreadsheet", "hoja de calculo",
        "hoja de cálculo", "importar", "exportar contactos", "limpiar datos",
        "deduplicar", "etiquetar", "tag",
    ],
    principles=[
        "Datos limpios = decisiones limpias; deduplica y normaliza al cargar.",
        "Cada lead con etapa, próximo paso y fecha; sin huérfanos en el pipeline.",
        "Registra la interacción inmediatamente; la memoria no escala.",
        "Mové las etapas según criterios objetivos, no optimismo.",
        "Usa campos consistentes (estado, fuente, valor) para poder reportar.",
        "No cargues datos sensibles (tarjetas, documentos) en campos de texto libre.",
    ],
)


# ── Criptomonedas / blockchain (educativo) ──────────────────────────────
CRYPTO = SkillDomain(
    key="crypto",
    title="Criptomonedas / Blockchain",
    keywords=[
        "cripto", "crypto", "bitcoin", "btc", "ethereum", "eth", "blockchain",
        "altcoin", "stablecoin", "defi", "wallet", "billetera", "exchange",
        "binance", "coinbase", "on-chain", "onchain", "staking", "token",
        "nft", "web3",
    ],
    principles=[
        "Educa, no asesores: explica conceptos; nunca des recomendaciones personalizadas de compra/venta.",
        "Custodia: 'not your keys, not your coins'; explica hot vs cold wallet y riesgo de exchange.",
        "Volatilidad extrema: el capital puede perderse por completo; siempre advierte el riesgo.",
        "DCA (Dollar-Cost Averaging) reduce el riesgo de timing frente a la entrada única.",
        "Diferencia capa 1/capa 2, PoW/PoS y el caso de uso real del token.",
        "Verifica contratos y fuentes; el espacio cripto está lleno de scams y rug-pulls.",
        "NUNCA ejecutes trades, transferencias ni ingreses seed phrases/credenciales: detente y avisa al usuario.",
    ],
)

# ── Bolsa de valores / acciones (educativo) ─────────────────────────────
STOCK_MARKET = SkillDomain(
    key="stock_market",
    title="Bolsa de Valores / Acciones",
    keywords=[
        "accion", "acción", "acciones", "bolsa", "stock", "equity", "etf",
        "indice", "índice", "sp500", "s&p", "nasdaq", "dividendo", "broker",
        "merval", "cedear", "ipo", "ticker", "portafolio", "cartera",
    ],
    principles=[
        "Educa sobre instrumentos (acción, ETF, índice); no des consejos de inversión personalizados.",
        "Diversificación: no concentres; reduce riesgo idiosincrático del portafolio.",
        "Horizonte largo + interés compuesto suele superar al trading frecuente para el inversor común.",
        "Distingue tipos de orden (market, limit, stop) y su efecto en ejecución y slippage.",
        "Costos importan: comisiones, spread e impuestos erosionan el retorno neto.",
        "Rendimiento pasado no garantiza resultados futuros; siempre advierte el riesgo de pérdida.",
        "NUNCA ejecutes órdenes ni ingreses credenciales de broker: presenta info y deriva al usuario.",
    ],
)

# ── Estilos de análisis (técnico/fundamental/cuant/macro/sentimiento) ───
MARKET_ANALYSIS = SkillDomain(
    key="market_analysis",
    title="Estilos de Análisis de Mercado",
    keywords=[
        "analisis tecnico", "análisis técnico", "analisis fundamental",
        "análisis fundamental", "velas", "candlestick", "soporte", "resistencia",
        "tendencia", "rsi", "macd", "media movil", "media móvil", "fibonacci",
        "valuacion", "valuación", "per", "pe ratio", "flujo de caja", "dcf",
        "sentimiento", "cuantitativo", "quant", "macro", "on-chain",
    ],
    principles=[
        "Análisis técnico: precio/volumen, tendencias, soportes/resistencias, indicadores (RSI, MACD, medias).",
        "Análisis fundamental: valor intrínseco vía ingresos, márgenes, deuda, flujo de caja (DCF), múltiplos (PER).",
        "Análisis cuantitativo: modelos estadísticos, backtesting, factores; cuidado con overfitting.",
        "Análisis de sentimiento: noticias, redes y miedo/codicia como señales contrarias.",
        "Macro: tasas, inflación, ciclo económico y liquidez mueven todos los mercados.",
        "On-chain (cripto): flujos de exchange, holders, actividad de red.",
        "Ningún estilo es infalible: combínalos, gestiona riesgo y nunca prometas rendimientos.",
    ],
)

# ── Mercados financieros (forex, bonos, commodities, tasas) ─────────────
FINANCIAL_MARKETS = SkillDomain(
    key="financial_markets",
    title="Mercados Financieros",
    keywords=[
        "forex", "divisa", "divisas", "fx", "bono", "bonos", "renta fija",
        "commodity", "commodities", "materias primas", "oro", "petroleo",
        "petróleo", "tasa de interes", "tasa de interés", "inflacion",
        "inflación", "tipo de cambio", "futuros", "derivados", "liquidez",
    ],
    principles=[
        "Clases de activo: renta variable, renta fija, divisas, commodities y derivados — perfiles de riesgo distintos.",
        "Tasas de interés suben → bonos existentes bajan de precio (relación inversa).",
        "Divisas: el tipo de cambio refleja tasas, inflación y balanza; alto apalancamiento = alto riesgo.",
        "Commodities cubren inflación pero son cíclicos y sensibles a oferta/demanda global.",
        "Correlaciones cambian en crisis; la diversificación puede fallar cuando más se necesita.",
        "Derivados amplifican ganancias y pérdidas; explica el riesgo antes que la oportunidad.",
        "Solo información educativa; no asesores ni ejecutes operaciones apalancadas.",
    ],
)

# ── Mercado inmobiliario ────────────────────────────────────────────────
REAL_ESTATE = SkillDomain(
    key="real_estate",
    title="Mercado Inmobiliario",
    keywords=[
        "inmueble", "inmobiliario", "propiedad", "propiedades", "real estate",
        "alquiler", "renta", "departamento", "casa", "terreno", "hipoteca",
        "tasacion", "tasación", "valuacion inmueble", "cap rate", "roi inmobiliario",
        "flipping", "metro cuadrado", "m2", "plusvalia", "plusvalía",
    ],
    principles=[
        "Ubicación manda: zona, servicios y desarrollo futuro pesan más que el inmueble en sí.",
        "Mide el retorno: cap rate = ingreso neto anual / valor; compara contra alternativas.",
        "ROI con apalancamiento (hipoteca) amplifica retorno y riesgo; modela escenarios.",
        "Costos ocultos: impuestos, mantenimiento, vacancia, gestión y comisiones.",
        "Comparables (comps) de ventas recientes en la zona anclan la valuación.",
        "Flujo de caja positivo > especular con plusvalía; la liquidez inmobiliaria es baja.",
        "Educativo: no firmes ofertas, reservas ni pagos; deriva la decisión al usuario.",
    ],
)

# ── Manejo de plataformas de trading (Binance, brokers) — read-only ─────
TRADING_PLATFORMS = SkillDomain(
    key="trading_platforms",
    title="Plataformas de Trading / Inversión",
    keywords=[
        "binance", "coinbase", "kraken", "tradingview", "metatrader",
        "interactive brokers", "etoro", "broker", "exchange cripto",
        "panel de trading", "orderbook", "libro de ordenes", "libro de órdenes",
        "grafico de precios", "gráfico de precios",
    ],
    principles=[
        "Modo SOLO LECTURA: navega, lee precios, gráficos y datos públicos; reporta al usuario.",
        "NUNCA ingreses credenciales, claves API, 2FA ni seed phrases en la plataforma.",
        "NUNCA coloques, modifiques o canceles órdenes, ni muevas/retires fondos.",
        "Si la tarea exige operar o autenticarse, DETENTE y pide que el usuario lo haga.",
        "Extrae métricas (precio, volumen, variación) para análisis, no para ejecutar.",
        "Respeta CAPTCHAs y verificaciones; no las eludas.",
    ],
)

# ── Gestión de riesgo / money management ────────────────────────────────
RISK_MANAGEMENT = SkillDomain(
    key="risk_management",
    title="Gestión de Riesgo de Trading",
    keywords=[
        "gestion de riesgo", "gestión de riesgo", "money management", "stop loss",
        "stop-loss", "take profit", "take-profit", "tamaño de posicion",
        "tamaño de posición", "position sizing", "drawdown", "ratio riesgo beneficio",
        "risk reward", "r multiple", "apalancamiento", "diversificar", "kelly",
    ],
    principles=[
        "Define el riesgo por operación antes de entrar; regla común: no arriesgar más del 1-2% del capital.",
        "Todo trade lleva stop-loss; sin stop no hay plan, hay apuesta.",
        "Busca ratio riesgo/beneficio (R-multiple) ≥ 1:2; el target debe pagar el riesgo.",
        "Dimensiona la posición según la distancia al stop, no por corazonada.",
        "Controla el drawdown máximo; recuperar un -50% exige un +100%.",
        "El apalancamiento amplifica pérdidas igual que ganancias; úsalo con extrema cautela.",
        "Diversifica entre activos y correlaciones; no concentres todo en una idea.",
        "El agente solo propone parámetros de riesgo; la ejecución y el capital son del usuario.",
    ],
)

# ── Modelos de negocio ──────────────────────────────────────────────────
BUSINESS_MODELS = SkillDomain(
    key="business_models",
    title="Modelos de Negocio",
    keywords=[
        "modelo de negocio", "business model", "saas", "suscripcion",
        "suscripción", "marketplace", "dropshipping", "franquicia",
        "ecommerce", "afiliados", "freemium", "membresia", "membresía",
        "unit economics", "ltv", "cac", "mrr", "arr", "monetizar", "monetizacion",
        "monetización", "escalar negocio",
    ],
    principles=[
        "Elige el modelo según margen, recurrencia y costo de adquisición: SaaS, marketplace, e-commerce, afiliados, franquicia.",
        "Unit economics primero: LTV debe superar a CAC (idealmente 3:1) o el modelo no escala.",
        "Recurrencia (suscripción/MRR) da previsibilidad; reduce el churn antes de escalar adquisición.",
        "Marketplace: resuelve primero el lado escaso de la oferta/demanda (chicken-and-egg).",
        "Freemium funciona si el free convierte y el costo de servir al free es bajo.",
        "Valida con ingresos reales antes de invertir en escala; la tracción manda.",
        "Modela escenarios financieros; no prometas retornos garantizados.",
    ],
)


SKILL_DOMAINS: Dict[str, SkillDomain] = {
    d.key: d
    for d in (
        SALES_STRATEGY,
        PROSPECTING,
        OUTREACH,
        NEGOTIATION,
        CUSTOMER_SUCCESS,
        CONTENT_CREATOR,
        SOCIAL_MEDIA,
        ADS_MANAGEMENT,
        SALES_PLATFORMS,
        SEO_MARKETING,
        MARKET_INTEL,
        ANALYTICS,
        CRM_OPS,
        CRYPTO,
        STOCK_MARKET,
        MARKET_ANALYSIS,
        FINANCIAL_MARKETS,
        REAL_ESTATE,
        TRADING_PLATFORMS,
        RISK_MANAGEMENT,
        BUSINESS_MODELS,
        TOOL_HANDLING,
    )
}

# Rol de equipo de ventas que cada skill reemplaza (introspección/marketing).
SALES_TEAM_ROLES: Dict[str, str] = {
    "prospecting": "SDR / Generador de leads",
    "outreach": "Representante de desarrollo (cold outreach)",
    "sales_strategy": "Ejecutivo de cuenta",
    "negotiation": "Closer / Especialista en cierre",
    "customer_success": "Customer Success Manager",
    "content_creator": "Creador de contenido / Copywriter",
    "social_media": "Community Manager",
    "ads_management": "Media Buyer / Performance",
    "sales_platforms": "E-commerce Manager",
    "seo_marketing": "Especialista SEO",
    "market_intel": "Analista de mercado",
    "analytics": "Analista de datos / RevOps",
    "crm_ops": "Operaciones de ventas (Sales Ops)",
    "crypto": "Analista de criptomonedas (educativo)",
    "stock_market": "Analista de renta variable (educativo)",
    "market_analysis": "Analista técnico/fundamental",
    "financial_markets": "Analista de mercados financieros",
    "real_estate": "Analista inmobiliario",
    "trading_platforms": "Operador de plataformas (solo lectura)",
    "risk_management": "Gestor de riesgo / money manager",
    "business_models": "Estratega de modelos de negocio",
    "tool_handling": "Asistente de operaciones",
}

# Mapa dominio-URL → skill de plataforma (para activar por la URL actual).
_DOMAIN_HINTS: Dict[str, str] = {
    "instagram.com": "social_media",
    "facebook.com": "social_media",
    "tiktok.com": "social_media",
    "ads.google.com": "ads_management",
    "business.facebook.com": "ads_management",
    "shopify.com": "sales_platforms",
    "myshopify.com": "sales_platforms",
    "mercadolibre.com": "sales_platforms",
    "amazon.com": "sales_platforms",
    "hotmart.com": "sales_platforms",
    "canva.com": "content_creator",
    "linkedin.com": "prospecting",
    "search.google.com": "seo_marketing",
    "analytics.google.com": "analytics",
    "docs.google.com": "crm_ops",
    "sheets.google.com": "crm_ops",
    "airtable.com": "crm_ops",
    "hubspot.com": "crm_ops",
    "salesforce.com": "crm_ops",
    "binance.com": "trading_platforms",
    "coinbase.com": "trading_platforms",
    "kraken.com": "trading_platforms",
    "tradingview.com": "market_analysis",
    "metatrader": "trading_platforms",
    "etoro.com": "trading_platforms",
    "zillow.com": "real_estate",
    "zonaprop.com": "real_estate",
    "argenprop.com": "real_estate",
    "investing.com": "financial_markets",
    "yahoo.com/finance": "stock_market",
    "finance.yahoo.com": "stock_market",
}


def _domain_of(url: Optional[str]) -> str:
    if not url:
        return ""
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def detect_skill_domains(task: str, url: Optional[str] = None) -> List[SkillDomain]:
    """Selecciona los dominios de skill relevantes para la tarea + URL.

    Siempre incluye Estrategia de Ventas (es un agente vendedor) y los
    dominios cuyos keywords aparecen en la tarea o que coinciden con la URL.
    """
    text = (task or "").lower()
    selected: List[str] = ["sales_strategy"]

    for key, domain in SKILL_DOMAINS.items():
        if key in selected:
            continue
        if any(kw in text for kw in domain.keywords):
            selected.append(key)

    host = _domain_of(url)
    if host:
        for hint_host, skill_key in _DOMAIN_HINTS.items():
            if hint_host in host and skill_key not in selected:
                selected.append(skill_key)

    # Manejo de herramientas siempre útil como base operativa.
    if "tool_handling" not in selected:
        selected.append("tool_handling")

    return [SKILL_DOMAINS[k] for k in selected]


def build_skill_brief(
    task: str,
    url: Optional[str] = None,
    max_domains: int = 5,
    principles_per_domain: int = 4,
) -> str:
    """Construye un brief compacto de conocimiento para inyectar al prompt.

    Devuelve string vacío si no hay nada relevante (defensivo).
    """
    domains = detect_skill_domains(task, url)
    if not domains:
        return ""

    domains = domains[:max_domains]
    lines: List[str] = ["Expert sales-agent knowledge (apply where relevant):"]
    for d in domains:
        lines.append(f"[{d.title}]")
        for p in d.principles[:principles_per_domain]:
            lines.append(f"- {p}")
    return "\n".join(lines)


def list_platform_skills() -> Dict[str, List[str]]:
    """Lista las plataformas cubiertas por cada dominio de skill (introspección)."""
    return {
        key: list(domain.platforms)
        for key, domain in SKILL_DOMAINS.items()
        if domain.platforms
    }


def list_sales_team_roles() -> List[Dict[str, object]]:
    """Lista las skills como roles de un equipo de ventas (introspección/UI).

    Devuelve, por cada dominio, el rol humano equivalente y cuántos
    principios/competencias incluye. Sirve para mostrar "este agente
    reemplaza a un equipo completo".
    """
    return [
        {
            "key": key,
            "role": SALES_TEAM_ROLES.get(key, "Especialista"),
            "title": domain.title,
            "competencies": len(domain.principles),
            "platforms": list(domain.platforms),
        }
        for key, domain in SKILL_DOMAINS.items()
    ]
