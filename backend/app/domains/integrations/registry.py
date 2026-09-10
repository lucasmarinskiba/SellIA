"""The catalogue of external APIs SellIA can use, per tool.

Why this exists as code and not only as a document: a markdown file listing
"falta configurar PageSpeed" goes stale the moment someone adds the variable in
Railway, and then it is lying in the same way the old hardcoded dashboards were.
This registry is read at runtime against the real environment, so
GET /integrations/status always reports what is actually set on this deployment.
docs/INTEGRACIONES.md is generated from this file (scripts/gen_integrations_doc.py).

`impact` is deliberately blunt about what the product does TODAY without the
integration -- in every case the answer is "says it cannot measure it", never
"shows an estimate", and that is the behaviour these keys would replace with
real data.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

FREE = "gratis"
FREEMIUM = "free tier + pago"
PAID = "pago"


@dataclass
class Integration:
    key: str
    name: str
    provider: str
    #: SellIA tool this unlocks, matching the dashboard page names.
    tool: str
    #: All of these must be present for the integration to be usable.
    required_env: list[str]
    optional_env: list[str] = field(default_factory=list)
    cost: str = FREE
    docs_url: str = ""
    unlocks: str = ""
    #: What the product does today, without it.
    today_instead: str = ""
    #: Rough ordering for the user: 1 = do this first.
    priority: int = 3

    def configured(self) -> bool:
        return all(bool(os.getenv(name)) for name in self.required_env)

    def missing(self) -> list[str]:
        return [name for name in self.required_env if not os.getenv(name)]

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "provider": self.provider,
            "tool": self.tool,
            "required_env": self.required_env,
            "optional_env": self.optional_env,
            "cost": self.cost,
            "docs_url": self.docs_url,
            "unlocks": self.unlocks,
            "today_instead": self.today_instead,
            "priority": self.priority,
            "configured": self.configured(),
            "missing_env": self.missing(),
        }


INTEGRATIONS: list[Integration] = [
    # ── SEO ────────────────────────────────────────────────────────────────
    Integration(
        key="google_search_console",
        name="Google Search Console API",
        provider="Google",
        tool="SEO",
        required_env=["GOOGLE_OAUTH_CLIENT_ID", "GOOGLE_OAUTH_CLIENT_SECRET"],
        cost=FREE,
        docs_url="https://developers.google.com/webmaster-tools/v1/getting_started",
        unlocks="Posiciones, impresiones, clics y CTR reales por keyword y por página, "
                "sacados de las búsquedas que de verdad mostraron el sitio del usuario. "
                "Es la única fuente de posiciones reales y no cuesta nada.",
        today_instead="La herramienta mide la página pero no puede decir en qué puesto sale "
                      "ni por qué términos la encuentran.",
        priority=1,
    ),
    Integration(
        key="pagespeed",
        name="PageSpeed Insights API",
        provider="Google",
        tool="SEO",
        required_env=["GOOGLE_PAGESPEED_API_KEY"],
        cost=FREE,
        docs_url="https://developers.google.com/speed/docs/insights/v5/get-started",
        unlocks="Core Web Vitals reales (LCP, CLS, INP) de laboratorio y de campo (CrUX), "
                "que hoy se declaran explícitamente como no medibles.",
        today_instead="Sólo se mide el tiempo de respuesta del servidor, que es real pero es "
                      "una parte chica de la experiencia.",
        priority=1,
    ),
    Integration(
        key="keyword_data",
        name="Volumen y dificultad de keywords",
        provider="DataForSEO (barato) · SemRush · Ahrefs · Moz",
        tool="SEO",
        required_env=["KEYWORD_API_PROVIDER", "KEYWORD_API_KEY"],
        optional_env=["KEYWORD_API_LOGIN"],
        cost=PAID,
        docs_url="https://docs.dataforseo.com/v3/keywords_data/overview/",
        unlocks="Cuánta gente busca cada término y qué tan difícil es rankear. Convierte el "
                "perfil de términos actual (qué dice tu página) en decisiones de qué escribir.",
        today_instead="Se muestra qué términos usa realmente la página, sin volumen ni "
                      "dificultad, y se aclara que eso requiere API paga.",
        priority=2,
    ),
    Integration(
        key="backlinks",
        name="Índice de backlinks",
        provider="Ahrefs · Majestic · Moz · DataForSEO",
        tool="SEO / Construya Autoridad",
        required_env=["BACKLINK_API_PROVIDER", "BACKLINK_API_KEY"],
        cost=PAID,
        docs_url="https://docs.dataforseo.com/v3/backlinks/overview/",
        unlocks="Quién enlaza al sitio del usuario desde afuera: el otro 50% de la autoridad. "
                "Hoy sólo se verifica el enlazado entre las propiedades del propio usuario.",
        today_instead="Se mide la red interna de marca (web ↔ redes ↔ tienda), que es real y "
                      "accionable, pero no ve enlaces de terceros.",
        priority=3,
    ),
    Integration(
        key="bing_webmaster",
        name="Bing Webmaster Tools API",
        provider="Microsoft",
        tool="SEO",
        required_env=["BING_WEBMASTER_API_KEY"],
        cost=FREE,
        docs_url="https://learn.microsoft.com/en-us/bingwebmaster/getting-access",
        unlocks="Posiciones en Bing y envío instantáneo de URLs a indexar (IndexNow). "
                "Gratis y con menos competencia que Google.",
        today_instead="No se consulta Bing.",
        priority=3,
    ),
    # ── Analytics ──────────────────────────────────────────────────────────
    Integration(
        key="ga4",
        name="Google Analytics 4 Data API",
        provider="Google",
        tool="Analytics",
        required_env=["GOOGLE_OAUTH_CLIENT_ID", "GOOGLE_OAUTH_CLIENT_SECRET", "GA4_PROPERTY_ID"],
        cost=FREE,
        docs_url="https://developers.google.com/analytics/devguides/reporting/data/v1",
        unlocks="Visitas, origen del tráfico y conversiones del sitio del usuario, para cruzar "
                "tráfico con las conversaciones que sí medimos hoy.",
        today_instead="Analytics sólo lee conversaciones, mensajes y órdenes propias: no sabe "
                      "cuánta gente visitó la web sin escribir.",
        priority=2,
    ),
    Integration(
        key="meta_insights",
        name="Meta Marketing API (insights)",
        provider="Meta",
        tool="Analytics",
        required_env=["META_APP_ID", "META_APP_SECRET"],
        optional_env=["META_AD_ACCOUNT_ID"],
        cost=FREE,
        docs_url="https://developers.facebook.com/docs/marketing-api/insights",
        unlocks="Inversión publicitaria y resultados reales para poder calcular ROAS. Sin gasto "
                "real, cualquier ROI sería inventado.",
        today_instead="No se muestra ROI ni ROAS en ninguna pantalla, justamente por eso.",
        priority=3,
    ),
    # ── Vendedor Multiplataforma ───────────────────────────────────────────
    Integration(
        key="meta_platform_app",
        name="App de Meta (WhatsApp / Instagram / Messenger)",
        provider="Meta",
        tool="Vendedor Multiplataforma",
        required_env=["META_APP_ID", "META_APP_SECRET"],
        optional_env=["META_WEBHOOK_VERIFY_TOKEN"],
        cost=FREE,
        docs_url="https://developers.facebook.com/docs/whatsapp/cloud-api/get-started",
        unlocks="Botón 'Autorizar' con OAuth: hoy cada usuario tiene que pegar a mano un token "
                "que sacó por su cuenta del panel de Meta.",
        today_instead="El usuario carga sus credenciales manualmente en el formulario y se "
                      "validan de verdad contra la plataforma.",
        priority=1,
    ),
    Integration(
        key="mercadolibre_app",
        name="Aplicación de MercadoLibre",
        provider="MercadoLibre",
        tool="Vendedor Multiplataforma",
        required_env=["MERCADO_LIBRE_CLIENT_ID", "MERCADO_LIBRE_CLIENT_SECRET"],
        optional_env=["MERCADO_LIBRE_REDIRECT_URI"],
        cost=FREE,
        docs_url="https://developers.mercadolibre.com.ar/es_ar/registra-tu-aplicacion",
        unlocks="Conexión con un clic y renovación automática del token, para que la IA "
                "responda preguntas de publicaciones sin que se corte cada 6 horas.",
        today_instead="Cada usuario tiene que crear su propia app en ML y pegar client_id y "
                      "client_secret.",
        priority=1,
    ),
    Integration(
        key="amazon_spapi",
        name="Amazon Selling Partner API",
        provider="Amazon",
        tool="Vendedor Multiplataforma",
        required_env=["AMAZON_CLIENT_ID", "AMAZON_CLIENT_SECRET"],
        cost=FREE,
        docs_url="https://developer-docs.amazon.com/sp-api/docs/registering-your-application",
        unlocks="Órdenes, listings y mensajes de Amazon en el mismo inbox. Requiere aprobación "
                "de Amazon, que tarda.",
        today_instead="El usuario carga sus propias credenciales SP-API si ya tiene una app "
                      "aprobada.",
        priority=3,
    ),
    Integration(
        key="hotmart_app",
        name="Aplicación de Hotmart",
        provider="Hotmart",
        tool="Vendedor Multiplataforma",
        required_env=["HOTMART_CLIENT_ID", "HOTMART_CLIENT_SECRET"],
        optional_env=["HOTMART_REDIRECT_URI"],
        cost=FREE,
        docs_url="https://developers.hotmart.com/docs/en/start/app-auth/",
        unlocks="Ventas y suscripciones de infoproductos sincronizadas.",
        today_instead="Credenciales manuales por usuario.",
        priority=3,
    ),
    Integration(
        key="google_business",
        name="Google Business Profile API",
        provider="Google",
        tool="Construya Autoridad",
        required_env=["GOOGLE_OAUTH_CLIENT_ID", "GOOGLE_OAUTH_CLIENT_SECRET"],
        cost=FREE,
        docs_url="https://developers.google.com/my-business/content/prereqs",
        unlocks="Reseñas reales de Google, respuesta automática a reseñas y ficha local: la "
                "señal de autoridad más fuerte para un negocio con local físico.",
        today_instead="Sólo se cuentan reseñas cargadas manualmente en SellIA.",
        priority=2,
    ),
    # ── IA / conversaciones ────────────────────────────────────────────────
    Integration(
        key="anthropic",
        name="Anthropic (Claude)",
        provider="Anthropic",
        tool="Agentes IA",
        required_env=["ANTHROPIC_API_KEY"],
        cost=PAID,
        docs_url="https://docs.anthropic.com/en/api/getting-started",
        unlocks="Respuestas generadas por el agente en conversaciones y análisis.",
        today_instead="Sin clave, el sistema cae a respuestas de plantilla.",
        priority=1,
    ),
    Integration(
        key="openai",
        name="OpenAI",
        provider="OpenAI",
        tool="Agentes IA",
        required_env=["OPENAI_API_KEY"],
        cost=PAID,
        docs_url="https://platform.openai.com/docs/quickstart",
        unlocks="Proveedor alternativo y embeddings para búsqueda semántica del catálogo.",
        today_instead="Se usa sólo Anthropic; si falla, no hay segundo proveedor.",
        priority=3,
    ),
    # ── Comunicaciones ─────────────────────────────────────────────────────
    Integration(
        key="twilio",
        name="Twilio",
        provider="Twilio",
        tool="Notificaciones",
        required_env=["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"],
        cost=PAID,
        docs_url="https://www.twilio.com/docs/messaging/quickstart",
        unlocks="SMS de aviso al vendedor cuando entra una consulta caliente fuera de la app.",
        today_instead="Las notificaciones viven dentro de la app y por email.",
        priority=3,
    ),
    Integration(
        key="sentry",
        name="Sentry",
        provider="Sentry",
        tool="Operación",
        required_env=["SENTRY_DSN"],
        cost=FREEMIUM,
        docs_url="https://docs.sentry.io/platforms/python/integrations/fastapi/",
        unlocks="Errores de producción con stack trace en vez de tener que leer logs de Railway "
                "a mano. Free tier alcanza de sobra para este volumen.",
        today_instead="Los errores se ven sólo en los logs del deploy.",
        priority=2,
    ),
    Integration(
        key="mercadopago",
        name="MercadoPago",
        provider="MercadoPago",
        tool="Pagos",
        required_env=["MERCADOPAGO_ACCESS_TOKEN"],
        optional_env=["MERCADOPAGO_PUBLIC_KEY", "MERCADOPAGO_WEBHOOK_SECRET"],
        cost=PAID,
        docs_url="https://www.mercadopago.com.ar/developers/es/docs",
        unlocks="Checkout y cobros en Argentina y Latam.",
        today_instead="Ya está configurado y en uso.",
        priority=1,
    ),
    Integration(
        key="resend",
        name="Resend",
        provider="Resend",
        tool="Notificaciones",
        required_env=["RESEND_API_KEY"],
        optional_env=["RESEND_WEBHOOK_SECRET"],
        cost=FREEMIUM,
        docs_url="https://resend.com/docs/introduction",
        unlocks="Envío de emails transaccionales y seguimiento de aperturas.",
        today_instead="Ya está configurado y en uso.",
        priority=1,
    ),
    Integration(
        key="stripe",
        name="Stripe",
        provider="Stripe",
        tool="Pagos",
        required_env=["STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"],
        optional_env=["STRIPE_PUBLISHABLE_KEY"],
        cost=PAID,
        docs_url="https://docs.stripe.com/keys",
        unlocks="Cobro internacional con tarjeta, además de MercadoPago que ya está andando.",
        today_instead="Sólo MercadoPago (configurado).",
        priority=3,
    ),
]


def status() -> dict[str, Any]:
    """Real configuration state of this deployment. Never returns a value --
    only whether each variable is present."""
    items = [i.as_dict() for i in INTEGRATIONS]
    by_tool: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        by_tool.setdefault(item["tool"], []).append(item)

    return {
        "configured_count": sum(1 for i in items if i["configured"]),
        "total": len(items),
        "by_tool": [
            {
                "tool": tool,
                "integrations": sorted(entries, key=lambda i: (i["configured"], i["priority"])),
            }
            for tool, entries in by_tool.items()
        ],
        "next_steps": sorted(
            [i for i in items if not i["configured"]],
            key=lambda i: i["priority"],
        )[:5],
    }
