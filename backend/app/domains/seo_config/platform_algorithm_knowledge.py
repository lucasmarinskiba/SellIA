"""What SellIA knows about how each connected platform ranks and surfaces sellers.

One source of truth, used by: platform-name normalisation (every connector
lookup), the "why does this matter" attached to each recommendation, the
per-platform algorithm guide endpoint, the prioritised action plan, and the
knowledge the AI agents read (library/marketplace_algorithm_mastery.json is
generated from this module, and a test keeps them in sync).

Honesty rules baked into the data:
  - Every factor carries its evidence level. "official" means the platform
    itself documents the mechanism (help center, developer docs, public
    statements by its executives). "community" means seller/agency consensus:
    widely repeated, never published by the platform. No platform publishes
    exact ranking weights, and nothing here pretends otherwise.
  - `not_measurable` lists what SellIA cannot see and why, so a score is never
    mistaken for the platform's own.
  - Platforms not researched yet are `researched=False` with NO factors: an
    empty answer is better than a confident invented one.
"""

import re
from dataclasses import dataclass, field

OFFICIAL = "official"
COMMUNITY = "community"

MEASURED = "measured"  # a connector fetches real ranking signals from the platform's API
WEB_AUDIT = "web_audit"  # own store / generic web: scored by the real on-page audit (web_presence)
GUIDANCE_ONLY = "guidance_only"  # no connector or audit path yet: guidance, not a score


@dataclass(frozen=True)
class RankingFactor:
    name: str
    evidence: str  # OFFICIAL | COMMUNITY
    note: str
    measured_by: tuple[str, ...] = ()  # signal keys SellIA computes for this factor


@dataclass(frozen=True)
class PlatformProfile:
    key: str
    label: str
    kind: str  # marketplace | social | own_store | generic_web
    coverage: str  # MEASURED | WEB_AUDIT | GUIDANCE_ONLY
    summary: str
    disclosure: str  # how much the platform actually publishes about its ranking
    factors: tuple[RankingFactor, ...] = ()
    not_measurable: tuple[str, ...] = ()
    playbook: tuple[str, ...] = ()
    researched: bool = True
    aliases: tuple[str, ...] = field(default_factory=tuple)


_PROFILES: tuple[PlatformProfile, ...] = (
    PlatformProfile(
        key="mercado-libre", label="Mercado Libre", kind="marketplace", coverage=MEASURED,
        aliases=("mercadolibre", "mercado_libre", "meli", "ml"),
        summary=(
            "El orden de búsqueda combina reputación del vendedor, calidad de la ficha, competitividad "
            "(precio/envío) y desempeño de ventas. Para productos de catálogo, compiten los vendedores por una "
            "única oferta destacada (Buy Box)."
        ),
        disclosure=(
            "Mercado Libre nunca publicó los pesos del ranking. Documenta el sistema de reputación, el medidor de "
            "salud por publicación (Reputation Health Gauge) y la mecánica de catálogo; el resto es consenso de vendedores."
        ),
        factors=(
            RankingFactor("Reputación del vendedor", OFFICIAL,
                          "Ventana de 60 días (con 40+ ventas). Reclamos por debajo de 3% (1% para MercadoLíder), "
                          "cancelaciones propias, despachos tarde (más de 10% penaliza) y mediaciones.",
                          ("seller_claims_rate", "seller_cancellation_rate", "seller_reputation_level", "seller_has_unhealthy_items")),
            RankingFactor("Catálogo y Buy Box", OFFICIAL,
                          "En productos de catálogo la ficha la fija Mercado Libre; los vendedores solo compiten en "
                          "precio, cuotas, envío y garantía por la oferta destacada.",
                          ("buy_box_winner",)),
            RankingFactor("Logística (Full / Flex)", OFFICIAL,
                          "Mercado Envíos Full y Flex reciben distintivos de envío preferenciales; el peso exacto en el ranking no está publicado.",
                          ("shipping_tier",)),
            RankingFactor("Calidad de la ficha", COMMUNITY,
                          "Título con palabras clave reales y atributos (sin relleno), categoría correcta, atributos "
                          "requeridos completos y fotos suficientes (se recomiendan 6 o más).",
                          ("listing_completeness_pct", "title_length_score", "photo_count")),
            RankingFactor("Respuesta a preguntas", COMMUNITY,
                          "Responder rápido sube la confianza y la conversión. Los umbrales (más de 90% respondidas, "
                          "promedio menor a 60 min) son buena práctica de vendedores, no un SLA de Mercado Libre.",
                          ("question_response_latency_minutes", "question_answer_rate_pct")),
            RankingFactor("Conversión visitas → ventas", COMMUNITY,
                          "Se la describe como la señal que más rápido mueve el ranking. SellIA mide las ventas con órdenes reales; "
                          "los clics no los expone Mercado Libre a los vendedores."),
        ),
        not_measurable=(
            "Precio frente a la competencia: no hay una fuente de precios de competidores conectada.",
            "Personalización del orden por comprador: Mercado Libre no la especifica.",
            "Pesos exactos del ranking: no son públicos.",
        ),
        playbook=(
            "Mantené los reclamos por debajo de 3% y sin publicaciones marcadas como 'unhealthy': es lo más grave para tu exposición.",
            "Completá todos los atributos requeridos de la categoría: habilita catálogo y mejora la ficha.",
            "Respondé preguntas en menos de 1 hora.",
            "Subí a 6 o más fotos y escribí el título con palabras clave reales, sin repetirlas.",
            "Si podés, usá Full o Flex.",
        ),
    ),
    PlatformProfile(
        key="amazon", label="Amazon", kind="marketplace", coverage=MEASURED,
        aliases=("amazon-seller", "amazon_seller", "amazon-sp-api"),
        summary=(
            "Amazon privilegia listings comprables, con stock y precio competitivo, de vendedores con métricas de "
            "cuenta sanas; el Featured Offer (Buy Box) concentra las ventas."
        ),
        disclosure=(
            "Amazon nunca publicó fórmula ni pesos: 'A9' y 'A10' son apodos de la industria. Sí documenta las métricas "
            "de salud de cuenta con umbrales y los factores generales de elegibilidad del Featured Offer."
        ),
        factors=(
            RankingFactor("Salud de la cuenta (ODR, envíos tardíos, tracking válido)", OFFICIAL,
                          "Order Defect Rate por debajo de 1%, envíos tardíos por debajo de 4% y tracking válido por encima de 95%. "
                          "Perder estándar puede costar el Buy Box hasta 60 días.",
                          ("account_odr_pct", "account_lsr_pct", "account_vtr_pct")),
            RankingFactor("Precio para el Featured Offer", OFFICIAL,
                          "Amazon calcula el precio esperado para ganar el Featured Offer (FOEP). El precio es un factor real, "
                          "pero no el principal: las métricas de cuenta pueden descalificar aunque el precio sea el mejor.",
                          ("price_vs_foep_ratio", "foep_price", "current_price")),
            RankingFactor("Estado del listing", OFFICIAL,
                          "Un listing suprimido o no BUYABLE no puede ganar el Buy Box.",
                          ("listing_buyable", "listing_issues_count")),
            RankingFactor("Stock disponible", OFFICIAL,
                          "Las ofertas sin inventario pierden visibilidad y elegibilidad.", ("in_stock",)),
            RankingFactor("Método de cumplimiento (FBA / FBM)", COMMUNITY,
                          "FBA y Seller-Fulfilled Prime suelen recibir trato preferencial porque Amazon controla la promesa de entrega; no está publicado.",
                          ("fulfillment_method",)),
            RankingFactor("Contenido del catálogo", COMMUNITY,
                          "Título, bullets e imágenes. Amazon indica que A+ Content se asocia a mayor conversión, no a un impulso directo del ranking.",
                          ("catalog_completeness_pct", "bullet_count", "image_count", "title_length")),
            RankingFactor("Ranking de ventas (BSR)", OFFICIAL,
                          "Métrica real de ranking por categoría; sirve como indicador de velocidad de ventas, sin escala absoluta para puntuarla.",
                          ("best_sellers_rank",)),
            RankingFactor("Conversión, velocidad de ventas y reseñas", COMMUNITY,
                          "El consenso los ubica entre los factores más pesados. SellIA no los puntúa hoy."),
        ),
        not_measurable=(
            "Reseñas (calificación, cantidad y velocidad): no se confirmó un endpoint de la API que las entregue.",
            "Relevancia por palabras clave y tráfico externo: Amazon no publica cómo los pondera.",
            "Pesos exactos del ranking: no son públicos.",
        ),
        playbook=(
            "Cuidá ODR por debajo de 1%, envíos tardíos por debajo de 4% y tracking válido por encima de 95%.",
            "Resolvé cualquier supresión o issue del listing: sin estado BUYABLE no hay Buy Box.",
            "Mantené stock y llevá tu precio al FOEP que calcula Amazon.",
            "Completá título, 5 bullets y 7 imágenes (objetivos heurísticos).",
        ),
    ),
    PlatformProfile(
        key="hotmart", label="Hotmart", kind="marketplace", coverage=MEASURED,
        aliases=("hotmart-producer", "hotmart_producer"),
        summary=(
            "El Mercado de Afiliados filtra y ordena por Temperature (desempeño del producto) y exige un Blueprint "
            "mínimo para listarse. Hotmart no expone ninguno de los dos por API."
        ),
        disclosure=(
            "Hotmart documenta Temperature (índice de 0 a 150 según frecuencia y recencia de ventas, tasa de reembolso y "
            "Blueprint) y Blueprint (calificación de calidad; por debajo de 60% el producto no se lista para afiliados). "
            "No publica las fórmulas."
        ),
        factors=(
            RankingFactor("Reembolsos", OFFICIAL,
                          "La tasa de reembolso es uno de los insumos documentados de la Temperature.", ("refund_rate_pct",)),
            RankingFactor("Frecuencia y recencia de ventas", OFFICIAL,
                          "También insumo documentado de la Temperature.", ("sales_velocity",)),
            RankingFactor("Contracargos y disputas", COMMUNITY,
                          "No es un insumo documentado; se los vigila por su efecto en la reputación del productor.", ("chargeback_rate_pct",)),
            RankingFactor("Finalización de la compra", COMMUNITY,
                          "Proxy de fricción del checkout: ventas pagas sobre intentos de compra.", ("approval_rate_pct",)),
            RankingFactor("Blueprint (calidad del producto y su página)", OFFICIAL,
                          "Evalúa nombre, categoría, organización del contenido, página de ventas, relación precio-valor, "
                          "competitividad de la comisión y materiales para afiliados."),
        ),
        not_measurable=(
            "La Temperature y el Blueprint reales: Hotmart no los expone por ninguna API. SellIA calcula proxies con tus transacciones reales.",
            "Calificación 'Most Loved': solo visible en el panel de Hotmart.",
            "EPC (ganancia por clic): no existe en Hotmart, es un concepto de otras redes de afiliados.",
        ),
        playbook=(
            "Bajá los reembolsos: mejorá la promesa de la página de ventas y la entrega.",
            "Revisá que la comisión sea competitiva para afiliados: es parte del Blueprint.",
            "Cuidá los contracargos: dañan tu reputación como productor.",
        ),
    ),
    PlatformProfile(
        key="instagram", label="Instagram", kind="social", coverage=MEASURED,
        aliases=("ig", "instagram-business", "instagram_business"),
        summary=(
            "Instagram pondera cuánto se mira y se comparte el contenido, no cuántos likes junta. Los Reels se rankean por "
            "tiempo de reproducción y repeticiones."
        ),
        disclosure=(
            "Meta, por boca de su responsable de Instagram, nombró las señales principales: tiempo de reproducción, "
            "envíos por DM por alcance y likes por alcance. No publica los pesos exactos."
        ),
        factors=(
            RankingFactor("Envíos por DM por alcance", OFFICIAL,
                          "Meta indicó que los envíos pesan más que los likes para llegar a quienes no te siguen; la magnitud exacta no es oficial.",
                          ("sends_per_reach",)),
            RankingFactor("Tiempo de reproducción y repeticiones (Reels)", OFFICIAL,
                          "Los Reels se ordenan por tiempo total visto y repeticiones, no por cantidad de vistas.",
                          ("watch_time_seconds", "replay_rate_pct")),
            RankingFactor("Likes por alcance", OFFICIAL, "Una de las tres señales principales que Meta nombró.", ("likes_per_reach",)),
            RankingFactor("Guardados y comentarios", COMMUNITY,
                          "Se los trata como señales de calidad; Meta no dio su peso.", ("saves_per_reach", "comments_per_reach")),
            RankingFactor("Palabras clave en descripción, bio y texto alternativo", OFFICIAL,
                          "Meta indicó que hoy impulsan el descubrimiento en la búsqueda; los hashtags perdieron peso.",
                          ("alt_text_present", "hashtag_count")),
            RankingFactor("Regularidad de publicación", COMMUNITY,
                          "Muy repetida por la comunidad; Meta no confirmó su efecto.", ("posting_cadence_days",)),
        ),
        not_measurable=(
            "Cobertura de palabras clave objetivo en la descripción: requiere una lista de palabras clave por negocio que aún no existe.",
            "Pesos exactos de cada señal: no son públicos.",
        ),
        playbook=(
            "Diseñá cada contenido para que se comparta por mensaje directo: es la señal que Meta prioriza.",
            "En Reels cuidá los primeros segundos: mayor tiempo visto y repeticiones.",
            "Escribí descripciones con palabras clave reales y completá el texto alternativo; no dependas de hashtags.",
        ),
    ),
    PlatformProfile(
        key="shopify", label="Shopify", kind="own_store", coverage=WEB_AUDIT,
        aliases=("shopify-store",),
        summary=(
            "Tu tienda vive en tu propio dominio: no hay un ranking de marketplace que compare vendedores. Se posiciona "
            "como cualquier sitio en Google, más la búsqueda interna de la tienda."
        ),
        disclosure=(
            "Shopify documenta que su búsqueda interna admite grupos de sinónimos y refuerzos manuales de productos, "
            "pero no publica la fórmula de relevancia."
        ),
        factors=(
            RankingFactor("SEO del sitio (Google)", OFFICIAL,
                          "Título, meta descripción, H1, texto alternativo, datos estructurados, HTTPS y velocidad; SellIA los mide leyendo tus páginas reales."),
            RankingFactor("Búsqueda interna de la tienda", OFFICIAL,
                          "Sinónimos y refuerzos manuales dentro de tu propia tienda; no afecta el posicionamiento frente a otros vendedores."),
        ),
        not_measurable=("Relevancia interna de la búsqueda de la tienda: la fórmula no es pública.",),
        playbook=(
            "Optimizá título, meta descripción y H1 de cada producto.",
            "Agregá datos estructurados (schema.org) y texto alternativo en imágenes.",
            "Configurá sinónimos en la búsqueda interna.",
        ),
    ),
    PlatformProfile(
        key="tiendanube", label="Tienda Nube", kind="own_store", coverage=WEB_AUDIT,
        aliases=("tienda-nube", "tienda_nube", "nuvemshop"),
        summary="Tienda propia en tu dominio: el posicionamiento es SEO web estándar orientado a Google.",
        disclosure="No se encontró evidencia de un algoritmo propietario de ranking entre vendedores; su propio contenido trata el posicionamiento como SEO web.",
        factors=(
            RankingFactor("SEO del sitio (Google)", COMMUNITY,
                          "Títulos, meta descripciones, velocidad y contenido; SellIA los mide leyendo tus páginas reales."),
        ),
        playbook=(
            "Optimizá título y descripción de cada producto.",
            "Cuidá la velocidad de carga y el uso móvil.",
        ),
    ),
    PlatformProfile(
        key="woocommerce", label="WooCommerce", kind="own_store", coverage=WEB_AUDIT,
        aliases=("woo", "woo-commerce"),
        summary="Tienda propia en tu dominio: el posicionamiento es SEO web estándar orientado a Google.",
        disclosure="Al ser una tienda en tu propio dominio no hay ranking entre vendedores; rige el SEO de Google.",
        factors=(
            RankingFactor("SEO del sitio (Google)", COMMUNITY,
                          "Títulos, meta descripciones, datos estructurados y velocidad; SellIA los mide leyendo tus páginas reales."),
        ),
        playbook=("Optimizá título, meta descripción y datos estructurados de cada producto.",),
    ),
    PlatformProfile(
        key="etsy", label="Etsy", kind="marketplace", coverage=GUIDANCE_ONLY,
        aliases=("etsy-shop",),
        summary="Etsy rankea por relevancia de palabras clave, calidad del listing y experiencia del cliente.",
        disclosure="Etsy divulga oficialmente sus factores de ranking en su página de transparencia, sin pesos.",
        factors=(
            RankingFactor("Relevancia", OFFICIAL, "Coincidencia de palabras clave con la búsqueda; condiciona a los demás factores."),
            RankingFactor("Puntaje de calidad del listing", OFFICIAL, "Aproxima la conversión de vistas a favoritos, carritos y ventas."),
            RankingFactor("Experiencia del cliente y del mercado", OFFICIAL, "Reseñas, envíos, resolución de casos y tiempo de respuesta."),
            RankingFactor("Precio de envío, recencia, personalización y ubicación", OFFICIAL, "Factores adicionales divulgados por Etsy."),
        ),
        not_measurable=("SellIA aún no tiene un conector que traiga estas señales de Etsy: hoy es solo guía, sin puntaje.",),
        playbook=(
            "Usá en el título y las etiquetas las palabras que tu cliente realmente busca.",
            "Mantené buenas reseñas, envíos claros y respuesta rápida.",
        ),
    ),
    PlatformProfile(
        key="custom", label="Sitio web propio (Google)", kind="generic_web", coverage=WEB_AUDIT,
        aliases=("website", "web", "sitio", "otro", "google"),
        summary="Se posiciona con SEO web: contenido útil, sitio rápido y confiable, y datos estructurados.",
        disclosure="Google confirma que Core Web Vitals y E-E-A-T existen como factores, pero no publica sus pesos.",
        factors=(
            RankingFactor("Core Web Vitals", OFFICIAL, "Google publica los umbrales: LCP menor a 2,5 s, INP menor a 200 ms, CLS menor a 0,1."),
            RankingFactor("Experiencia, pericia, autoridad y confianza (E-E-A-T)", OFFICIAL, "Google lo describe como criterio de calidad; el peso no está publicado."),
            RankingFactor("Datos estructurados", OFFICIAL, "No suben la posición por sí solos según Google, pero habilitan resultados enriquecidos que mejoran el clic."),
            RankingFactor("Rastreo e indexación", OFFICIAL, "HTTPS, robots.txt, sitemap y ausencia de bloqueos; SellIA los mide leyendo tus páginas reales."),
            RankingFactor("Enlaces entrantes relevantes", COMMUNITY, "Consenso del sector: cuenta más la relevancia temática que la cantidad."),
        ),
        not_measurable=("Volumen de búsqueda, dificultad de palabras clave y Core Web Vitals de laboratorio requieren APIs pagas que no están conectadas.",),
        playbook=(
            "Corregí primero los hallazgos críticos de la auditoría real de tus páginas.",
            "Sumá datos estructurados y verificá que Google pueda rastrear y indexar.",
        ),
    ),
    # Researched = False: listed so the UI can say "no hay análisis todavía" instead of guessing.
    PlatformProfile(key="tiktok", label="TikTok", kind="social", coverage=GUIDANCE_ONLY, researched=False,
                    summary="Sin investigación verificada todavía.", disclosure="No se muestran factores para no inventarlos.",
                    aliases=("tik-tok", "tiktok-shop", "tiktok_shop")),
    PlatformProfile(key="facebook", label="Facebook", kind="social", coverage=GUIDANCE_ONLY, researched=False,
                    summary="Sin investigación verificada todavía.", disclosure="No se muestran factores para no inventarlos.",
                    aliases=("facebook-marketplace", "facebook_marketplace", "fb", "meta")),
    PlatformProfile(key="youtube", label="YouTube", kind="social", coverage=GUIDANCE_ONLY, researched=False,
                    summary="Sin investigación verificada todavía.", disclosure="No se muestran factores para no inventarlos.",
                    aliases=("yt",)),
    PlatformProfile(key="ebay", label="eBay", kind="marketplace", coverage=GUIDANCE_ONLY, researched=False,
                    summary="Sin investigación verificada todavía.", disclosure="No se muestran factores para no inventarlos."),
)

PROFILES: dict[str, PlatformProfile] = {p.key: p for p in _PROFILES}

_ALIASES: dict[str, str] = {}
for _p in _PROFILES:
    for _name in (_p.key, *_p.aliases):
        _ALIASES[re.sub(r"[^a-z0-9]", "", _name.lower())] = _p.key


def canonical_platform(name: str | None) -> str | None:
    """Any spelling ('mercadolibre', 'Mercado_Libre', 'MELI') -> the key seo_config uses
    ('mercado-libre'). None when the platform is unknown (callers keep the raw name)."""
    return _ALIASES.get(re.sub(r"[^a-z0-9]", "", (name or "").lower()))


def get_profile(name: str | None) -> PlatformProfile | None:
    key = canonical_platform(name)
    return PROFILES.get(key) if key else None


def coverage_for(name: str | None) -> str:
    """How a platform is treated: measured by API, web-audited, or guidance only."""
    profile = get_profile(name)
    return profile.coverage if profile else GUIDANCE_ONLY


def factor_for_signal(platform: str | None, signal_key: str) -> RankingFactor | None:
    """The ranking factor a signal belongs to — the 'why this matters' of a recommendation."""
    profile = get_profile(platform)
    if not profile:
        return None
    return next((f for f in profile.factors if signal_key in f.measured_by), None)


def profile_to_dict(profile: PlatformProfile) -> dict:
    return {
        "platform": profile.key,
        "label": profile.label,
        "kind": profile.kind,
        "coverage": profile.coverage,
        "researched": profile.researched,
        "summary": profile.summary,
        "disclosure": profile.disclosure,
        "factors": [
            {"name": f.name, "evidence": f.evidence, "note": f.note, "measured_by": list(f.measured_by)}
            for f in profile.factors
        ],
        "not_measurable": list(profile.not_measurable),
        "playbook": list(profile.playbook),
    }


def render_library_items() -> list[dict]:
    """The items the AI agents read for the platforms researched in this module.
    Written to library/marketplace_algorithm_mastery.json; a test keeps the file in sync."""
    items = []
    for item_id, keys in (
        ("algo_001", ("mercado-libre",)), ("algo_002", ("amazon",)), ("algo_006", ("hotmart",)),
        ("algo_007", ("instagram",)), ("algo_008", ("etsy",)),
        ("algo_009", ("shopify", "tiendanube", "woocommerce")), ("algo_010", ("custom",)),
    ):
        profiles = [PROFILES[k] for k in keys]
        name = " / ".join(p.label for p in profiles)
        parts = []
        for p in profiles:
            official = [f.name for f in p.factors if f.evidence == OFFICIAL]
            community = [f.name for f in p.factors if f.evidence == COMMUNITY]
            text = f"{p.summary} {p.disclosure}"
            if official:
                text += " Documentado por la plataforma: " + "; ".join(official) + "."
            if community:
                text += " Consenso de vendedores (no oficial): " + "; ".join(community) + "."
            if p.not_measurable:
                text += " Lo que no se puede medir: " + " ".join(p.not_measurable)
            parts.append(text if len(profiles) == 1 else f"[{p.label}] {text}")
        items.append({"id": item_id, "name": f"{name}: cómo posiciona", "tactic": " ".join(parts)})
    return items
