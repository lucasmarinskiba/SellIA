"""SellIA Missions — Ad Spend Assistant

Módulo de lógica pura para recomendaciones de inversión publicitaria,
asignación de presupuesto, pasos de configuración de campañas y benchmarks CPA.
"""

from typing import List, Dict, Any, Optional


# ─── Benchmarks CPA por país y plataforma (ARS, aproximados) ───────────────────

CPA_BENCHMARKS = {
    "AR": {
        "meta": {"low": 800, "median": 2500, "high": 6000},
        "google": {"low": 1200, "median": 3500, "high": 9000},
        "tiktok": {"low": 600, "median": 2000, "high": 5000},
    },
    "BR": {
        "meta": {"low": 1500, "median": 4500, "high": 12000},
        "google": {"low": 2000, "median": 6000, "high": 15000},
        "tiktok": {"low": 1200, "median": 3500, "high": 9000},
    },
    "MX": {
        "meta": {"low": 2000, "median": 5000, "high": 12000},
        "google": {"low": 2500, "median": 7000, "high": 18000},
        "tiktok": {"low": 1500, "median": 4000, "high": 10000},
    },
    "CL": {
        "meta": {"low": 2000, "median": 5500, "high": 14000},
        "google": {"low": 2500, "median": 7000, "high": 16000},
        "tiktok": {"low": 1500, "median": 4500, "high": 11000},
    },
    "UY": {
        "meta": {"low": 1800, "median": 5000, "high": 12000},
        "google": {"low": 2200, "median": 6000, "high": 14000},
        "tiktok": {"low": 1400, "median": 4000, "high": 10000},
    },
    "US": {
        "meta": {"low": 15, "median": 45, "high": 120},
        "google": {"low": 25, "median": 60, "high": 150},
        "tiktok": {"low": 12, "median": 35, "high": 90},
    },
    "ES": {
        "meta": {"low": 12, "median": 35, "high": 90},
        "google": {"low": 18, "median": 50, "high": 120},
        "tiktok": {"low": 10, "median": 30, "high": 80},
    },
}

CURRENCY_BY_COUNTRY = {
    "AR": "ARS",
    "BR": "BRL",
    "MX": "MXN",
    "CL": "CLP",
    "UY": "UYU",
    "US": "USD",
    "ES": "EUR",
}

# ─── Perfiles de plataforma por tipo de negocio ────────────────────────────────

PLATFORM_PROFILES = {
    "ecommerce": {
        "meta": {"score": 10, "reasons": ["Alto volumen de usuarios", "Shopping tags", "Retargeting potente"]},
        "google": {"score": 9, "reasons": ["Intención de compra alta", "Shopping Ads", "Search demand"]},
        "tiktok": {"score": 7, "reasons": ["Descubrimiento de productos", "Audiencia joven"]},
    },
    "saas": {
        "meta": {"score": 7, "reasons": ["Lead gen con forms", "Lookalike audiences"]},
        "google": {"score": 10, "reasons": ["Búsqueda de soluciones B2B", "LinkedIn no disponible pero Search sí"]},
        "tiktok": {"score": 5, "reasons": ["Menor conversión B2B", "Brand awareness"]},
    },
    "local_service": {
        "meta": {"score": 6, "reasons": ["Audiencia local", "Reviews sociales"]},
        "google": {"score": 10, "reasons": ["Google Local Ads", "Intención de compra inmediata"]},
        "tiktok": {"score": 4, "reasons": ["Menor relevancia para servicios locales"]},
    },
    "fashion": {
        "meta": {"score": 9, "reasons": ["Visual-first", "Influencer integration"]},
        "google": {"score": 6, "reasons": ["Shopping Ads", "Menor impacto visual"]},
        "tiktok": {"score": 10, "reasons": ["Viral potential", "TikTok Shop", "Gen Z target"]},
    },
    "b2b": {
        "meta": {"score": 5, "reasons": ["Lead gen limitado"]},
        "google": {"score": 10, "reasons": ["Search intent B2B", "LinkedIn Ads complementario"]},
        "tiktok": {"score": 3, "reasons": ["No es canal B2B por defecto"]},
    },
    "education": {
        "meta": {"score": 7, "reasons": ["Audiencia de padres/estudiantes"]},
        "google": {"score": 9, "reasons": ["Búsqueda de cursos/carreras"]},
        "tiktok": {"score": 8, "reasons": ["Contenido educativo viral", "Cursos online"]},
    },
}

# ─── Alocación de presupuesto por objetivo ─────────────────────────────────────

BUDGET_ALLOCATION = {
    "awareness": {
        "meta": {"top_of_funnel": 70, "mid_funnel": 20, "bottom_funnel": 10},
        "google": {"top_of_funnel": 60, "mid_funnel": 25, "bottom_funnel": 15},
        "tiktok": {"top_of_funnel": 80, "mid_funnel": 15, "bottom_funnel": 5},
    },
    "conversions": {
        "meta": {"top_of_funnel": 20, "mid_funnel": 30, "bottom_funnel": 50},
        "google": {"top_of_funnel": 15, "mid_funnel": 25, "bottom_funnel": 60},
        "tiktok": {"top_of_funnel": 25, "mid_funnel": 35, "bottom_funnel": 40},
    },
    "lead_generation": {
        "meta": {"top_of_funnel": 30, "mid_funnel": 40, "bottom_funnel": 30},
        "google": {"top_of_funnel": 20, "mid_funnel": 35, "bottom_funnel": 45},
        "tiktok": {"top_of_funnel": 35, "mid_funnel": 40, "bottom_funnel": 25},
    },
    "retention": {
        "meta": {"top_of_funnel": 5, "mid_funnel": 25, "bottom_funnel": 70},
        "google": {"top_of_funnel": 5, "mid_funnel": 20, "bottom_funnel": 75},
        "tiktok": {"top_of_funnel": 10, "mid_funnel": 30, "bottom_funnel": 60},
    },
}

# ─── Pasos de configuración de campañas ────────────────────────────────────────

CAMPAIGN_SETUP_STEPS = {
    "meta": {
        "awareness": [
            {"step": 1, "title": "Crear campaña de Alcance", "description": "Objetivo: Awareness/Reach. Seleccionar optimización para impresiones.", "estimated_minutes": 15},
            {"step": 2, "title": "Definir audiencia", "description": "Intereses amplios + lookalike 1-3% de clientes actuales.", "estimated_minutes": 20},
            {"step": 3, "title": "Configurar presupuesto", "description": "CBO activado, presupuesto diario según funnel top.", "estimated_minutes": 10},
            {"step": 4, "title": "Diseñar creativo", "description": "Video corto (15s) o carrusel con hook visual fuerte.", "estimated_minutes": 30},
            {"step": 5, "title": "Configurar placements", "description": "Automático (Feed, Reels, Stories, Audience Network).", "estimated_minutes": 10},
            {"step": 6, "title": "Revisar y publicar", "description": "Verificar políticas, UTM tags y lanzar.", "estimated_minutes": 10},
        ],
        "conversions": [
            {"step": 1, "title": "Crear campaña de Ventas", "description": "Objetivo: Sales/Conversions. Seleccionar evento de compra.", "estimated_minutes": 15},
            {"step": 2, "title": "Configurar Pixel/CAPI", "description": "Verificar eventos Purchase, AddToCart, InitiateCheckout.", "estimated_minutes": 20},
            {"step": 3, "title": "Definir audiencia de retargeting", "description": "AddToCart 7d, Website visitors 30d, Video viewers 50% 14d.", "estimated_minutes": 20},
            {"step": 4, "title": "Configurar presupuesto", "description": "CBO, CPA target si hay datos históricos.", "estimated_minutes": 10},
            {"step": 5, "title": "Diseñar creativo de conversión", "description": "Testimonio + oferta + CTA claro ('Comprar ahora').", "estimated_minutes": 30},
            {"step": 6, "title": "Revisar y publicar", "description": "UTM tags, landing page mobile-friendly, lanzar.", "estimated_minutes": 10},
        ],
        "lead_generation": [
            {"step": 1, "title": "Crear campaña de Leads", "description": "Objetivo: Leads. Usar Lead Forms instantáneas o landing.", "estimated_minutes": 15},
            {"step": 2, "title": "Configurar formulario", "description": "Nombre, email, teléfono. Mensaje de agradecimiento + CTA WhatsApp.", "estimated_minutes": 20},
            {"step": 3, "title": "Definir audiencia", "description": "Intereses + lookalike de leads calificados.", "estimated_minutes": 20},
            {"step": 4, "title": "Configurar presupuesto", "description": "CBO con cost per lead target.", "estimated_minutes": 10},
            {"step": 5, "title": "Diseñar creativo", "description": "Problema-solución + social proof + CTA al formulario.", "estimated_minutes": 30},
            {"step": 6, "title": "Integrar CRM", "description": "Conectar leads automáticamente a CRM/Excel/WhatsApp.", "estimated_minutes": 15},
        ],
        "retention": [
            {"step": 1, "title": "Crear campaña de Retención", "description": "Objetivo: Engagement o Sales a lista de clientes.", "estimated_minutes": 15},
            {"step": 2, "title": "Subir lista de clientes", "description": "Custom audience con emails/teléfonos de compradores.", "estimated_minutes": 15},
            {"step": 3, "title": "Definir oferta", "description": "Descuento exclusivo, early access, o cross-sell.", "estimated_minutes": 15},
            {"step": 4, "title": "Diseñar creativo", "description": "Mensaje personalizado: 'Gracias por tu compra, tenemos esto para vos'.", "estimated_minutes": 25},
            {"step": 5, "title": "Configurar frecuency cap", "description": "Máximo 1 impresión cada 3 días para no saturar.", "estimated_minutes": 10},
        ],
    },
    "google": {
        "awareness": [
            {"step": 1, "title": "Crear campaña de Display", "description": "Objetivo: Awareness. Red de Display o YouTube bumper ads.", "estimated_minutes": 20},
            {"step": 2, "title": "Definir audiencia", "description": "Intereses in-market + affinity audiences + custom segments.", "estimated_minutes": 20},
            {"step": 3, "title": "Configurar presupuesto", "description": "CPM bidding, presupuesto diario para reach masivo.", "estimated_minutes": 10},
            {"step": 4, "title": "Diseñar banners/video", "description": "Adaptar a todos los tamaños de Display o video 6s.", "estimated_minutes": 35},
            {"step": 5, "title": "Revisar y publicar", "description": "Verificar políticas de imagen y lanzar.", "estimated_minutes": 10},
        ],
        "conversions": [
            {"step": 1, "title": "Crear campaña de Búsqueda", "description": "Objetivo: Ventas/Leads. Keywords de alto intento de compra.", "estimated_minutes": 20},
            {"step": 2, "title": "Investigar keywords", "description": "Keyword Planner + competitor analysis + negative keywords.", "estimated_minutes": 30},
            {"step": 3, "title": "Configurar conversion tracking", "description": "GA4 + Google Ads conversion tag + enhanced conversions.", "estimated_minutes": 25},
            {"step": 4, "title": "Crear ad groups", "description": "3-5 ad groups temáticos con 3-5 ads responsive cada uno.", "estimated_minutes": 30},
            {"step": 5, "title": "Configurar pujas", "description": "Maximize conversions o Target CPA si hay datos.", "estimated_minutes": 15},
            {"step": 6, "title": "Revisar y publicar", "description": "Extensions (sitelinks, callouts, structured snippets), UTM.", "estimated_minutes": 15},
        ],
        "lead_generation": [
            {"step": 1, "title": "Crear campaña de Búsqueda/Display", "description": "Objetivo: Leads. Keywords + remarketing Display.", "estimated_minutes": 20},
            {"step": 2, "title": "Configurar landing page", "description": "LP optimizada con formulario corto, social proof, speed <3s.", "estimated_minutes": 40},
            {"step": 3, "title": "Definir audiencia", "description": "In-market + remarketing + similar audiences.", "estimated_minutes": 20},
            {"step": 4, "title": "Configurar conversion tracking", "description": "Tag de conversión por submit de formulario.", "estimated_minutes": 20},
            {"step": 5, "title": "Diseñar anuncios", "description": "Responsive search ads con headlines de valor y CTAs claros.", "estimated_minutes": 25},
        ],
        "retention": [
            {"step": 1, "title": "Crear campaña RLSA/Remarketing", "description": "Objetivo: Re-engagement. Lista de clientes + remarketing.", "estimated_minutes": 15},
            {"step": 2, "title": "Subir lista de clientes", "description": "Customer match con emails para Search y Display.", "estimated_minutes": 15},
            {"step": 3, "title": "Definir oferta", "description": "Cross-sell, upsell o descuento de fidelidad.", "estimated_minutes": 15},
            {"step": 4, "title": "Configurar frecuency cap", "description": "3 impresiones por día máximo en Display.", "estimated_minutes": 10},
            {"step": 5, "title": "Diseñar creativos", "description": "Anuncios personalizados por categoría de compra previa.", "estimated_minutes": 25},
        ],
    },
    "tiktok": {
        "awareness": [
            {"step": 1, "title": "Crear campaña de Reach", "description": "Objetivo: Reach. Optimización por impresiones.", "estimated_minutes": 15},
            {"step": 2, "title": "Definir audiencia", "description": "Intereses + comportamientos + lookalike.", "estimated_minutes": 20},
            {"step": 3, "title": "Configurar presupuesto", "description": "CBO, presupuesto diario mínimo según país.", "estimated_minutes": 10},
            {"step": 4, "title": "Producir video nativo", "description": "Video vertical 9:16, hook en 0-3s, música trending.", "estimated_minutes": 40},
            {"step": 5, "title": "Revisar y publicar", "description": "Verificar políticas de contenido, UTM, lanzar.", "estimated_minutes": 10},
        ],
        "conversions": [
            {"step": 1, "title": "Crear campaña de Conversiones", "description": "Objetivo: Website Conversions o TikTok Shop.", "estimated_minutes": 15},
            {"step": 2, "title": "Instalar TikTok Pixel", "description": "Verificar eventos ViewContent, AddToCart, Purchase.", "estimated_minutes": 25},
            {"step": 3, "title": "Definir audiencia", "description": "Retargeting: video viewers 50% 7d, website visitors 14d.", "estimated_minutes": 20},
            {"step": 4, "title": "Configurar presupuesto", "description": "CBO con target CPA o lowest cost.", "estimated_minutes": 10},
            {"step": 5, "title": "Producir video de conversión", "description": "UGC-style, demo de producto, CTA claro.", "estimated_minutes": 40},
            {"step": 6, "title": "Revisar y publicar", "description": "UTM, landing mobile-first, lanzar.", "estimated_minutes": 10},
        ],
        "lead_generation": [
            {"step": 1, "title": "Crear campaña de Leads", "description": "Objetivo: Lead Generation con formulario instantáneo.", "estimated_minutes": 15},
            {"step": 2, "title": "Configurar formulario", "description": "Campos: nombre, email, teléfono. CTA WhatsApp.", "estimated_minutes": 20},
            {"step": 3, "title": "Definir audiencia", "description": "Intereses relevantes + lookalike de leads.", "estimated_minutes": 20},
            {"step": 4, "title": "Configurar presupuesto", "description": "CBO, mínimo diario según mercado.", "estimated_minutes": 10},
            {"step": 5, "title": "Producir video", "description": "Hook de problema + solución + testimonio.", "estimated_minutes": 35},
        ],
        "retention": [
            {"step": 1, "title": "Crear campaña de Retención", "description": "Objetivo: Engagement o Conversions a custom audience.", "estimated_minutes": 15},
            {"step": 2, "title": "Subir lista de clientes", "description": "Customer file: emails o teléfonos.", "estimated_minutes": 15},
            {"step": 3, "title": "Definir oferta", "description": "Descuento de fidelidad o early access.", "estimated_minutes": 15},
            {"step": 4, "title": "Producir video exclusivo", "description": "Mensaje directo a la cámara: 'Para nuestros clientes...'.", "estimated_minutes": 30},
            {"step": 5, "title": "Configurar frecuency cap", "description": "Máximo 2 impresiones cada 5 días.", "estimated_minutes": 10},
        ],
    },
}

# ─── Recomendaciones de creativos ──────────────────────────────────────────────

CREATIVE_RECOMMENDATIONS = {
    "meta": {
        "ecommerce": ["Carrusel de productos", "Video UGC 15-30s", "Reels con hook visual", "Stories con sticker de encuesta"],
        "saas": ["Video demo 60s", "Testimonio de cliente", "Carrusel de features", "Infografía de ROI"],
        "local_service": ["Video de detrás de escena", "Testimonio local", "Imagen before/after", "Reels de proceso de trabajo"],
        "fashion": ["Reels con transiciones", "UGC styling", "Carrusel lookbook", "Stories con link sticker"],
        "b2b": ["Video webinar clip", "Case study PDF", "Infografía de proceso", "Testimonio ejecutivo"],
        "education": ["Video de clase corta", "Testimonio de alumno", "Carrusel de tips", "Reels de logros"],
    },
    "google": {
        "ecommerce": ["Shopping Ads con imágenes limpias", "Responsive Search Ads con ofertas", "Display banners de producto"],
        "saas": ["Search Ads con keywords de solución", "Display remarketing con testimonio", "YouTube demo 60s"],
        "local_service": ["Local Service Ads", "Search Ads con keywords locales", "Display geolocalizado"],
        "fashion": ["Shopping Ads con modelos", "Responsive Search Ads de temporada", "Display banners visuales"],
        "b2b": ["Search Ads de intención B2B", "LinkedIn complementario (no Google)", "YouTube thought leadership"],
        "education": ["Search Ads de cursos", "Display remarketing a visitantes", "YouTube video educativo"],
    },
    "tiktok": {
        "ecommerce": ["Video UGC con demo rápida", "TikTok Shop live", "Duet con influencer", "Trending sound + producto"],
        "saas": ["Video 'day in the life' usando el producto", "Tip rápido con producto", "Behind the scenes del equipo"],
        "local_service": ["Video de transformación rápida", "Trending sound + servicio", "Before/after 15s"],
        "fashion": ["Get-ready-with-me", "Outfit transition", "Styling challenge", "TikTok Shop haul"],
        "b2b": ["Video 'unpopular opinion' del sector", "Tips ejecutivos en 30s", "Behind the empresa"],
        "education": ["Micro-clase 60s", "Study tips", "Transformación del alumno", "Trending sound + dato educativo"],
    },
}


class AdSpendAssistant:
    """Asistente de recomendaciones de inversión publicitaria."""

    def get_platform_recommendations(self, context: Dict[str, Any], budget: float) -> List[Dict[str, Any]]:
        """Recomendar plataformas según tipo de negocio y presupuesto.

        Args:
            context: dict con keys como business_type (str), country (str), audience_age (str).
            budget: presupuesto mensual estimado en moneda local.
        """
        business_type = context.get("business_type", "ecommerce")
        country = context.get("country", "AR").upper()
        audience_age = context.get("audience_age", "mixed")  # young | adult | mixed

        profiles = PLATFORM_PROFILES.get(business_type, PLATFORM_PROFILES["ecommerce"])
        recommendations = []

        for platform, data in profiles.items():
            score = data["score"]
            reasons = list(data["reasons"])

            # Ajuste por presupuesto
            if budget < 50000 and platform == "google":
                score -= 1
                reasons.append("Google requiere presupuesto mínimo para learning phase")
            elif budget < 30000 and platform == "tiktok":
                score -= 1
                reasons.append("TikTok necesita testing budget para encontrar audiencia")

            # Ajuste por audiencia joven
            if audience_age == "young" and platform == "tiktok":
                score += 2
                reasons.append("Audiencia joven altamente activa en TikTok")
            elif audience_age == "adult" and platform == "meta":
                score += 1
                reasons.append("Audiencia adulta madura en Meta")

            # Ajuste por país no LATAM → Google más fuerte
            if country not in ("AR", "BR", "MX", "CL", "UY") and platform == "google":
                score += 1
                reasons.append("Mercado maduro: Search demand alta")

            recommendations.append({
                "platform": platform,
                "score": max(0, score),
                "reasons": reasons,
                "suggested_minimum_budget": self._suggested_minimum_budget(platform, country),
            })

        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations

    def generate_budget_allocation(
        self,
        monthly_budget: float,
        business_type: str,
        goal: str,
    ) -> Dict[str, Any]:
        """Generar asignación de presupuesto por plataforma y etapa de funnel.

        Args:
            monthly_budget: presupuesto mensual total.
            business_type: tipo de negocio.
            goal: objetivo de campaña (awareness | conversions | lead_generation | retention).
        """
        goal = goal.lower()
        allocation_template = BUDGET_ALLOCATION.get(goal, BUDGET_ALLOCATION["conversions"])
        platform_scores = PLATFORM_PROFILES.get(business_type, PLATFORM_PROFILES["ecommerce"])

        # Ordenar plataformas por score descendente
        sorted_platforms = sorted(
            platform_scores.keys(),
            key=lambda p: platform_scores[p]["score"],
            reverse=True,
        )

        # Distribución base: 50/30/20 entre top 3 plataformas
        platform_weights = [0.5, 0.3, 0.2]
        platform_allocation = []
        for i, platform in enumerate(sorted_platforms[:3]):
            weight = platform_weights[i] if i < len(platform_weights) else 0.0
            platform_budget = monthly_budget * weight
            funnel = allocation_template.get(platform, allocation_template["meta"])
            platform_allocation.append({
                "platform": platform,
                "monthly_budget": round(platform_budget, 2),
                "percentage_of_total": round(weight * 100, 1),
                "funnel_allocation": {
                    "top_of_funnel": {
                        "percentage": funnel["top_of_funnel"],
                        "budget": round(platform_budget * (funnel["top_of_funnel"] / 100), 2),
                    },
                    "mid_funnel": {
                        "percentage": funnel["mid_funnel"],
                        "budget": round(platform_budget * (funnel["mid_funnel"] / 100), 2),
                    },
                    "bottom_funnel": {
                        "percentage": funnel["bottom_funnel"],
                        "budget": round(platform_budget * (funnel["bottom_funnel"] / 100), 2),
                    },
                },
            })

        return {
            "monthly_budget": monthly_budget,
            "business_type": business_type,
            "goal": goal,
            "platform_allocation": platform_allocation,
        }

    def get_campaign_setup_steps(self, platform: str, objective: str) -> Dict[str, Any]:
        """Devolver paso a paso para crear una campaña.

        Args:
            platform: meta | google | tiktok.
            objective: awareness | conversions | lead_generation | retention.
        """
        platform = platform.lower()
        objective = objective.lower()

        platform_steps = CAMPAIGN_SETUP_STEPS.get(platform, {})
        steps = platform_steps.get(objective, [])

        if not steps:
            return {
                "platform": platform,
                "objective": objective,
                "status": "error",
                "message": f"No hay pasos definidos para {platform} + {objective}.",
                "steps": [],
                "total_estimated_minutes": 0,
            }

        total_minutes = sum(s["estimated_minutes"] for s in steps)
        return {
            "platform": platform,
            "objective": objective,
            "status": "ok",
            "steps": steps,
            "total_estimated_minutes": total_minutes,
        }

    def estimate_cpa(self, business_type: str, platform: str, country: str) -> Dict[str, Any]:
        """Estimar costo por adquisición según benchmarks.

        Args:
            business_type: tipo de negocio.
            platform: meta | google | tiktok.
            country: código ISO de 2 letras.
        """
        platform = platform.lower()
        country = country.upper()
        benchmarks = CPA_BENCHMARKS.get(country, CPA_BENCHMARKS["AR"])
        platform_bench = benchmarks.get(platform, benchmarks["meta"])
        currency = CURRENCY_BY_COUNTRY.get(country, "ARS")

        # Ajustes por tipo de negocio
        low, median, high = platform_bench["low"], platform_bench["median"], platform_bench["high"]
        if business_type == "saas":
            low *= 1.5
            median *= 1.5
            high *= 1.5
        elif business_type == "b2b":
            low *= 2.0
            median *= 2.0
            high *= 2.0
        elif business_type == "fashion":
            low *= 0.8
            median *= 0.8
            high *= 0.8

        return {
            "business_type": business_type,
            "platform": platform,
            "country": country,
            "currency": currency,
            "estimated_cpa": {
                "low": round(low, 2),
                "median": round(median, 2),
                "high": round(high, 2),
            },
            "note": "Estimaciones basadas en benchmarks de mercado. CPA real depende de creativos, targeting y temporada.",
        }

    def get_ad_creatives_recommendations(self, platform: str, business_type: str) -> Dict[str, Any]:
        """Recomendar tipos de creativos según plataforma y negocio.

        Args:
            platform: meta | google | tiktok.
            business_type: ecommerce | saas | local_service | fashion | b2b | education.
        """
        platform = platform.lower()
        business_type = business_type.lower()

        recs = CREATIVE_RECOMMENDATIONS.get(platform, {})
        creatives = recs.get(business_type, ["Video genérico", "Imagen de producto", "Testimonio"])

        best_practices = []
        if platform == "meta":
            best_practices = [
                "Usar videos de 15-30s para feed/Reels",
                "Incluir captions/texto en video (80% sin sonido)",
                "Carrusel con storytelling secuencial",
                "A/B test de thumbnails",
            ]
        elif platform == "google":
            best_practices = [
                "Responsive Search Ads: mínimo 8 headlines y 4 descriptions",
                "Shopping Ads: fondo blanco, imagen nítida, sin texto superpuesto",
                "Display: banners en todos los tamaños estándar",
            ]
        elif platform == "tiktok":
            best_practices = [
                "Video vertical 9:16, mínimo 720p",
                "Hook en los primeros 3 segundos",
                "Usar trending sounds o audio nativo",
                "Evitar aspecto de 'publicidad tradicional'",
            ]

        return {
            "platform": platform,
            "business_type": business_type,
            "recommended_creatives": creatives,
            "best_practices": best_practices,
        }

    def _suggested_minimum_budget(self, platform: str, country: str) -> int:
        """Presupuesto mínimo mensual sugerido según plataforma y país."""
        base = {
            "meta": 30000,
            "google": 40000,
            "tiktok": 25000,
        }.get(platform, 30000)

        if country in ("US", "ES", "GB", "DE"):
            base = int(base * 0.05)  # Aproximación a divisas fuertes
        return base
