"""SellIA Diagnostic Engine

Analiza datos del negocio y detecta problemas que impiden ventas.
Genera diagnósticos con severidad y misiones recomendadas.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .schemas import BusinessDiagnosticCreate
from .playbook_library import PLAYBOOKS


# ─── Benchmarks de referencia ──────────────────────────────────────────────────

BENCHMARKS = {
    "conversion_rate": {"value": 2.5, "unit": "%", "source": "e-commerce promedio global"},
    "cart_abandonment_rate": {"value": 70.0, "unit": "%", "source": "Baymard Institute"},
    "instagram_posts_per_week": {"value": 5, "unit": "posts", "source": "Social Media Examiner"},
    "response_time_minutes": {"value": 15, "unit": "min", "source": "HubSpot"},
    "email_open_rate": {"value": 20.0, "unit": "%", "source": "Mailchimp"},
    "website_load_time": {"value": 3.0, "unit": "s", "source": "Google"},
    "repeat_customer_rate": {"value": 25.0, "unit": "%", "source": "e-commerce promedio"},
    "ads_roas": {"value": 4.0, "unit": "x", "source": "Meta/Google promedio"},
}


# ─── Motor de diagnóstico ──────────────────────────────────────────────────────

class DiagnosticEngine:
    """Genera diagnósticos de negocio basados en métricas y contexto."""

    def __init__(self, business_metrics: Dict[str, Any], business_context: Optional[Dict[str, Any]] = None):
        self.metrics = business_metrics
        self.context = business_context or {}
        self.diagnostics: List[BusinessDiagnosticCreate] = []

    def run_full_diagnostic(self) -> List[BusinessDiagnosticCreate]:
        """Ejecutar diagnóstico completo en todas las categorías."""
        self._diagnose_sales()
        self._diagnose_traffic()
        self._diagnose_seo()
        self._diagnose_ads()
        self._diagnose_branding()
        self._diagnose_logistics()
        self._diagnose_conversion()
        self._diagnose_retention()
        self._diagnose_context_specific()
        return self.diagnostics

    def _diagnose_context_specific(self):
        """Diagnósticos específicos según el tipo de negocio y contexto."""
        ctx = self.context
        if not ctx:
            return

        business_type = ctx.get("business_type")
        reach = ctx.get("geographic_reach")
        channels = ctx.get("channels_configured", {})
        ads = ctx.get("ads_configured", {})
        shipping = ctx.get("shipping_configured", {})
        has_website = ctx.get("website_configured", False)
        has_seo = ctx.get("seo_configured", False)

        # Channel gaps
        critical_channels = {
            "physical_products": ["mercadolibre", "shopify", "instagram"],
            "digital_products": ["shopify", "hotmart", "email"],
            "services": ["calendly", "google_business", "instagram"],
            "consulting": ["linkedin", "calendly", "google_business"],
            "software": ["producthunt", "linkedin", "github"],
            "food_beverage": ["rappi", "google_business", "instagram"],
            "fashion_beauty": ["instagram", "shopify", "mercadolibre"],
            "health_wellness": ["google_business", "instagram", "calendly"],
            "home_decor": ["pinterest", "shopify", "instagram"],
            "handcraft": ["etsy", "mercadolibre", "instagram"],
        }

        required = critical_channels.get(business_type, ["instagram", "google_business"])
        missing = [c for c in required if not channels.get(c, False)]
        if missing:
            self._add(
                "sales",
                "critical",
                f"Faltan canales esenciales para tu tipo de negocio ({business_type}): {', '.join(missing)}",
                recommended_slug="full_automation_setup",
                context={"missing_channels": missing},
            )

        # Website check for non-local businesses
        if not has_website and reach in ("national", "cross_border", "global"):
            self._add(
                "branding",
                "critical",
                "No tenés sitio web propio pero querés vender a nivel nacional/internacional. Necesitás una tienda profesional.",
                recommended_slug="brand_kit_creation",
            )

        # SEO check
        if has_website and not has_seo:
            self._add(
                "seo",
                "warning",
                "Tenés sitio web pero no tenés SEO configurado. Estás perdiendo tráfico orgánico gratuito.",
                recommended_slug="seo_technical_audit",
            )

        # Ads check for scaling
        if reach in ("national", "cross_border", "global") and not any(ads.values()):
            self._add(
                "ads",
                "warning",
                "Querés escalar a nivel nacional/internacional pero no tenés ads activos. El crecimiento orgánico solo no alcanza.",
                recommended_slug="meta_ads_funnel",
            )

        # Shipping check for physical products
        if business_type == "physical_products" and ctx.get("does_delivery", False) and not any(shipping.values()):
            self._add(
                "logistics",
                "critical",
                "Hacés envíos pero no tenés carriers configurados. Los clientes abandonan por falta de opciones de envío.",
                recommended_slug="shipping_carriers_full",
            )

        # Cross-border specific
        if reach == "cross_border" and not shipping.get("dhl") and not shipping.get("fedex"):
            self._add(
                "logistics",
                "warning",
                "Querés vender al exterior pero no tenés carriers internacionales (DHL/FedEx) configurados.",
                recommended_slug="cross_border_shipping",
            )

        # Local SEO for physical presence
        if ctx.get("has_physical_location", False) and not channels.get("google_business"):
            self._add(
                "seo",
                "critical",
                "Tenés local físico pero no tenés Google Business Profile. Perdés clientes que te buscan en Maps.",
                recommended_slug="google_local_seo",
            )

    def _add(self, category: str, severity: str, finding: str, metric_key: Optional[str] = None, recommended_slug: Optional[str] = None, context: Optional[Dict] = None):
        metric_value = None
        benchmark_value = None
        if metric_key and metric_key in self.metrics:
            metric_value = str(self.metrics[metric_key])
        if metric_key and metric_key in BENCHMARKS:
            benchmark_value = f"{BENCHMARKS[metric_key]['value']}{BENCHMARKS[metric_key]['unit']}"

        self.diagnostics.append(
            BusinessDiagnosticCreate(
                category=category,
                severity=severity,
                finding=finding,
                metric_value=metric_value,
                benchmark_value=benchmark_value,
                recommended_mission_slug=recommended_slug,
                context_data=context or {},
            )
        )

    # ─── Sales ─────────────────────────────────────────────────────────────────
    def _diagnose_sales(self):
        sales_30d = self.metrics.get("sales_30d", 0)
        if sales_30d == 0:
            self._add("sales", "critical", "Sin ventas en los últimos 30 días. El negocio está estancado.", recommended_slug="full_automation_setup")
        elif sales_30d < 5:
            self._add("sales", "warning", f"Solo {sales_30d} ventas en 30 días. Por debajo del umbral mínimo de sustentabilidad.", recommended_slug="cart_recovery_sequence")

        avg_order_value = self.metrics.get("avg_order_value", 0)
        if avg_order_value < 5000:
            self._add("sales", "info", f"Ticket promedio bajo (${avg_order_value}). Oportunidad de upsell.", recommended_slug="lead_nurture_sequence")

    # ─── Traffic ───────────────────────────────────────────────────────────────
    def _diagnose_traffic(self):
        traffic_30d = self.metrics.get("traffic_30d", 0)
        if traffic_30d == 0:
            self._add("traffic", "critical", "Sin tráfico web en los últimos 30 días. Nadie está llegando al negocio.", recommended_slug="google_local_seo")
        elif traffic_30d < 100:
            self._add("traffic", "warning", f"Solo {traffic_30d} visitas en 30 días. Tráfico insuficiente para escalar.", recommended_slug="meta_ads_funnel")

        organic_traffic_pct = self.metrics.get("organic_traffic_pct", 0)
        if organic_traffic_pct < 20:
            self._add("traffic", "warning", f"Solo {organic_traffic_pct}% del tráfico es orgánico. Dependencia excesiva de ads pago.", recommended_slug="seo_technical_audit")

        instagram_posts_14d = self.metrics.get("instagram_posts_14d", 0)
        if instagram_posts_14d == 0:
            self._add("traffic", "critical", "0 publicaciones en Instagram en los últimos 14 días. Perdida de alcance orgánico.", recommended_slug="instagram_launch")
        elif instagram_posts_14d < 3:
            self._add("traffic", "warning", f"Solo {instagram_posts_14d} posts en Instagram en 14 días. Frecuencia insuficiente.", recommended_slug="instagram_launch")

        tiktok_posts_14d = self.metrics.get("tiktok_posts_14d", 0)
        if tiktok_posts_14d == 0:
            self._add("traffic", "info", "Sin contenido en TikTok. Oportunidad de captar audiencia joven.", recommended_slug="tiktok_viral_launch")

    # ─── SEO ───────────────────────────────────────────────────────────────────
    def _diagnose_seo(self):
        indexed_pages = self.metrics.get("indexed_pages", 0)
        if indexed_pages == 0:
            self._add("seo", "critical", "El sitio web no está indexado en Google. Es invisible para búsquedas.", recommended_slug="seo_technical_audit")

        page_speed = self.metrics.get("page_speed_seconds", 99)
        if page_speed > 5:
            self._add("seo", "warning", f"Sitio web muy lento ({page_speed}s). Google penaliza y los usuarios abandonan.", metric_key="website_load_time", recommended_slug="seo_technical_audit")

        keywords_ranking = self.metrics.get("keywords_ranking_top10", 0)
        if keywords_ranking == 0:
            self._add("seo", "warning", "0 keywords en top 10 de Google. Sin posicionamiento orgánico.", recommended_slug="seo_technical_audit")

    # ─── Ads ───────────────────────────────────────────────────────────────────
    def _diagnose_ads(self):
        ad_spend_30d = self.metrics.get("ad_spend_30d", 0)
        roas = self.metrics.get("ads_roas", 0)

        if ad_spend_30d > 0 and roas == 0:
            self._add("ads", "critical", "Invirtiendo en ads sin retorno (ROAS 0). Campañas posiblemente mal configuradas.", recommended_slug="meta_ads_funnel")
        elif roas > 0 and roas < 2:
            self._add("ads", "warning", f"ROAS de {roas}x. Por debajo del break-even (3x). Revisar targeting y creativos.", metric_key="ads_roas", recommended_slug="meta_ads_funnel")
        elif roas >= 4:
            self._add("ads", "info", f"ROAS saludable de {roas}x. Oportunidad de escalar presupuesto.", metric_key="ads_roas")

        if ad_spend_30d == 0:
            self._add("ads", "info", "Sin inversión en ads. Oportunidad de acelerar crecimiento con tráfico pago.", recommended_slug="google_ads_search")

    # ─── Branding ──────────────────────────────────────────────────────────────
    def _diagnose_branding(self):
        brand_mentions_30d = self.metrics.get("brand_mentions_30d", 0)
        if brand_mentions_30d == 0:
            self._add("branding", "warning", "0 menciones de marca en 30 días. Sin presencia de marca en redes.", recommended_slug="brand_identity_refresh")

        profile_completeness = self.metrics.get("social_profile_completeness_pct", 0)
        if profile_completeness < 60:
            self._add("branding", "warning", f"Perfiles sociales incompletos ({profile_completeness}%). Perdida de credibilidad.", recommended_slug="brand_identity_refresh")

    # ─── Logistics ─────────────────────────────────────────────────────────────
    def _diagnose_logistics(self):
        avg_shipping_time = self.metrics.get("avg_shipping_days", 99)
        if avg_shipping_time > 7:
            self._add("logistics", "warning", f"Envío promedio de {avg_shipping_time} días. Los clientes esperan <3 días.", recommended_slug="local_delivery_setup")

        shipping_options = self.metrics.get("shipping_options_count", 0)
        if shipping_options < 2:
            self._add("logistics", "info", f"Solo {shipping_options} opción de envío. Múltiples carriers = más conversiones.", recommended_slug="local_delivery_setup")

    # ─── Conversion ────────────────────────────────────────────────────────────
    def _diagnose_conversion(self):
        conversion_rate = self.metrics.get("conversion_rate_pct", 0)
        if conversion_rate == 0:
            self._add("conversion", "critical", "Tasa de conversión 0%. El tráfico llega pero no compra.", recommended_slug="cart_recovery_sequence")
        elif conversion_rate < 1:
            self._add("conversion", "warning", f"Tasa de conversión {conversion_rate}% (benchmark: 2.5%). Funnel roto.", metric_key="conversion_rate", recommended_slug="cart_recovery_sequence")

        cart_abandonment = self.metrics.get("cart_abandonment_rate_pct", 100)
        if cart_abandonment > 85:
            self._add("conversion", "critical", f"{cart_abandonment}% de carritos abandonados. Recuperación urgente.", metric_key="cart_abandonment_rate", recommended_slug="cart_recovery_sequence")
        elif cart_abandonment > 70:
            self._add("conversion", "warning", f"{cart_abandonment}% de carritos abandonados. Por encima del promedio.", metric_key="cart_abandonment_rate", recommended_slug="cart_recovery_sequence")

    # ─── Retention ─────────────────────────────────────────────────────────────
    def _diagnose_retention(self):
        repeat_rate = self.metrics.get("repeat_customer_rate_pct", 0)
        if repeat_rate == 0:
            self._add("retention", "warning", "0% de clientes recurrentes. Sin estrategia de fidelización.", recommended_slug="lead_nurture_sequence")
        elif repeat_rate < 15:
            self._add("retention", "info", f"Solo {repeat_rate}% de clientes vuelven a comprar. Oportunidad de LTV.", metric_key="repeat_customer_rate", recommended_slug="lead_nurture_sequence")

        response_time = self.metrics.get("avg_response_time_minutes", 999)
        if response_time > 60:
            self._add("retention", "warning", f"Tiempo de respuesta promedio: {response_time} min. Clientes se van a la competencia.", metric_key="response_time_minutes", recommended_slug="full_automation_setup")


def run_diagnostic(business_metrics: Dict[str, Any], business_context: Optional[Dict[str, Any]] = None) -> List[BusinessDiagnosticCreate]:
    """Función de conveniencia para ejecutar un diagnóstico completo."""
    engine = DiagnosticEngine(business_metrics, business_context)
    return engine.run_full_diagnostic()
