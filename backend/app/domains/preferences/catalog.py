"""The option lists the configuration screen offers.

Served to the UI instead of being duplicated in the frontend, so a value the
backend does not accept can never appear in a dropdown.

Two different kinds of knowledge live here and they are kept apart on purpose:

* What a platform CAN DO for the seller is never written down — it is read off
  the connector class at runtime (platform_commerce.capabilities), so it cannot
  claim an integration the code does not have.
* WHERE a platform operates and WHAT it suits is real-world knowledge that no
  amount of introspection can produce. It is declared below as data, deliberately
  coarse, and it is used only to order suggestions — never to promise a result.
"""

from __future__ import annotations

from typing import Any

# ISO 639-1, the ones this product's prompts and channels actually handle.
LANGUAGES: list[dict[str, str]] = [
    {"code": "es", "label": "Español"},
    {"code": "en", "label": "Inglés"},
    {"code": "pt", "label": "Portugués"},
    {"code": "it", "label": "Italiano"},
    {"code": "fr", "label": "Francés"},
    {"code": "de", "label": "Alemán"},
]

# ISO 3166-1 alpha-2. LatAm first because that is where this product's sellers
# are; the rest are the markets its platforms reach without extra setup.
MARKETS: list[dict[str, str]] = [
    {"code": "AR", "label": "Argentina"},
    {"code": "UY", "label": "Uruguay"},
    {"code": "CL", "label": "Chile"},
    {"code": "PY", "label": "Paraguay"},
    {"code": "BO", "label": "Bolivia"},
    {"code": "PE", "label": "Perú"},
    {"code": "BR", "label": "Brasil"},
    {"code": "CO", "label": "Colombia"},
    {"code": "MX", "label": "México"},
    {"code": "EC", "label": "Ecuador"},
    {"code": "US", "label": "Estados Unidos"},
    {"code": "ES", "label": "España"},
    {"code": "IT", "label": "Italia"},
    {"code": "DE", "label": "Alemania"},
    {"code": "FR", "label": "Francia"},
    {"code": "GB", "label": "Reino Unido"},
]

#: platform -> where it operates and what it suits.
#: "markets": [] means "not tied to a country" (a shop or a messenger works
#: wherever the seller does). Categories use the BusinessType values.
PLATFORM_FIT: dict[str, dict[str, Any]] = {
    "mercadolibre": {
        "label": "MercadoLibre",
        "kind": "marketplace",
        "markets": ["AR", "MX", "BR", "CL", "CO", "UY", "PE", "EC", "BO"],
        "suits": ["physical_products", "fashion_beauty", "home_decor", "handcraft", "health_wellness"],
        "note": "El marketplace con más tráfico de compra directa en Latinoamérica.",
    },
    "shopify": {
        "label": "Shopify",
        "kind": "own_store",
        "markets": [],
        "suits": ["physical_products", "digital_products", "fashion_beauty", "home_decor", "handcraft"],
        "note": "Tienda propia: no trae tráfico, pero ninguna plataforma se queda con tu cliente.",
    },
    "woocommerce": {
        "label": "WooCommerce",
        "kind": "own_store",
        "markets": [],
        "suits": ["physical_products", "digital_products", "services", "food_beverage"],
        "note": "Tienda propia sobre WordPress, si ya tenés el sitio.",
    },
    "etsy": {
        "label": "Etsy",
        "kind": "marketplace",
        "markets": ["US", "GB", "DE", "FR", "IT", "ES"],
        "suits": ["handcraft", "home_decor", "fashion_beauty", "digital_products"],
        "note": "Compradores que buscan hecho a mano y diseño, sobre todo en EE.UU. y Europa.",
    },
    "amazon": {
        "label": "Amazon",
        "kind": "marketplace",
        "markets": ["US", "MX", "BR", "ES", "IT", "DE", "FR", "GB"],
        "suits": ["physical_products", "home_decor", "health_wellness"],
        "note": "Volumen alto y competencia alta: conviene con stock y logística resueltos.",
    },
    "hotmart": {
        "label": "Hotmart",
        "kind": "marketplace",
        "markets": ["BR", "MX", "CO", "AR", "ES"],
        "suits": ["digital_products", "consulting", "software"],
        "note": "Cursos e infoproductos, con afiliados que venden por vos.",
    },
    "tiktok_shop": {
        "label": "TikTok Shop",
        "kind": "marketplace",
        "markets": ["US", "GB", "MX", "BR", "ES"],
        "suits": ["fashion_beauty", "physical_products", "health_wellness", "home_decor"],
        "note": "Venta dentro del video: rinde si ya producís contenido.",
    },
    "facebook_marketplace": {
        "label": "Facebook Marketplace",
        "kind": "marketplace",
        "markets": [],
        "suits": ["physical_products", "home_decor", "handcraft", "food_beverage"],
        "note": "Compra-venta local, sin comisión, con mucha consulta por mensaje.",
    },
    "instagram": {
        "label": "Instagram",
        "kind": "social",
        "markets": [],
        "suits": ["fashion_beauty", "food_beverage", "handcraft", "home_decor", "health_wellness", "services"],
        "note": "Donde se descubre el producto y se abre la conversación.",
    },
    "whatsapp": {
        "label": "WhatsApp",
        "kind": "messaging",
        "markets": [],
        "suits": ["services", "consulting", "food_beverage", "physical_products", "health_wellness"],
        "note": "Donde se cierra la venta en Latinoamérica.",
    },
    "telegram": {
        "label": "Telegram",
        "kind": "messaging",
        "markets": [],
        "suits": ["digital_products", "software", "consulting"],
        "note": "Comunidad y soporte, con bots sin costo por mensaje.",
    },
    "messenger": {
        "label": "Messenger",
        "kind": "messaging",
        "markets": [],
        "suits": ["physical_products", "services", "food_beverage"],
        "note": "La bandeja de las páginas de Facebook.",
    },
    "tiktok": {
        "label": "TikTok",
        "kind": "social",
        "markets": [],
        "suits": ["fashion_beauty", "food_beverage", "health_wellness", "handcraft"],
        "note": "Alcance orgánico sin seguidores previos.",
    },
    "linkedin": {
        "label": "LinkedIn",
        "kind": "social",
        "markets": [],
        "suits": ["consulting", "software", "services"],
        "note": "El canal B2B: decisores, no consumidores.",
    },
    "threads": {"label": "Threads", "kind": "social", "markets": [], "suits": ["services", "consulting"], "note": "Conversación de texto ligada a tu Instagram."},
    "twitter": {"label": "X / Twitter", "kind": "social", "markets": [], "suits": ["software", "consulting", "digital_products"], "note": "Nicho técnico y actualidad."},
    "email": {"label": "Email", "kind": "messaging", "markets": [], "suits": ["digital_products", "consulting", "services", "software"], "note": "Lo único que no depende de un algoritmo ajeno."},
    "webchat": {"label": "Chat del sitio", "kind": "messaging", "markets": [], "suits": ["services", "software", "consulting"], "note": "Atiende a quien ya está mirando tu producto."},
}

# The tones the prompt composer really distinguishes.
TONES: list[dict[str, str]] = [
    {"value": "professional", "label": "Profesional", "detail": "Claro y directo, sin exceso de confianza."},
    {"value": "casual", "label": "Cercano", "detail": "Como le hablás a un cliente conocido."},
    {"value": "persuasive", "label": "Persuasivo", "detail": "Orientado a que la conversación termine en compra."},
    {"value": "technical", "label": "Técnico", "detail": "Datos, especificaciones y precisión."},
]

GOALS: list[dict[str, str]] = [
    {"value": "more_sales", "label": "Vender más"},
    {"value": "more_leads", "label": "Conseguir más contactos"},
    {"value": "more_traffic", "label": "Traer más visitas"},
    {"value": "brand_awareness", "label": "Que me conozcan"},
    {"value": "expansion", "label": "Abrir un mercado nuevo"},
]

PRICE_RANGES: list[dict[str, str]] = [
    {"value": "low", "label": "Económico"},
    {"value": "medium", "label": "Medio"},
    {"value": "premium", "label": "Premium"},
    {"value": "luxury", "label": "Lujo"},
]


def business_types() -> list[dict[str, str]]:
    """The niches, read off the enum the database actually stores."""
    from app.domains.business_context.models import BusinessType

    labels = {
        "physical_products": "Productos físicos",
        "digital_products": "Productos digitales",
        "services": "Servicios",
        "consulting": "Consultoría / coaching",
        "software": "Software / SaaS",
        "food_beverage": "Gastronomía",
        "fashion_beauty": "Moda y belleza",
        "health_wellness": "Salud y bienestar",
        "home_decor": "Hogar y decoración",
        "handcraft": "Artesanías",
        "other": "Otro",
    }
    return [{"value": t.value, "label": labels.get(t.value, t.value)} for t in BusinessType]


def sales_models() -> list[dict[str, str]]:
    from app.domains.business_context.models import SalesModel

    labels = {
        "b2c": "Al consumidor final (B2C)",
        "b2b": "A empresas (B2B)",
        "b2b2c": "Mixto (B2B2C)",
        "d2c": "Marca propia directa (D2C)",
        "marketplace": "En marketplaces",
    }
    return [{"value": m.value, "label": labels.get(m.value, m.value)} for m in SalesModel]


def platform_options() -> list[dict[str, Any]]:
    """Every platform the seller can choose, with what it can really do here."""
    from app.domains.platform_commerce import capabilities

    options = []
    for platform, fit in PLATFORM_FIT.items():
        caps = capabilities.capabilities_for(platform)
        options.append({
            "value": platform,
            "label": fit["label"],
            "kind": fit["kind"],
            "note": fit["note"],
            "markets": fit["markets"],
            "suits": fit["suits"],
            "capabilities": [key for key, available in caps.items() if available],
        })
    return sorted(options, key=lambda option: option["label"].lower())


def full_catalog() -> dict[str, Any]:
    return {
        "languages": LANGUAGES,
        "markets": MARKETS,
        "platforms": platform_options(),
        "tones": TONES,
        "goals": GOALS,
        "price_ranges": PRICE_RANGES,
        "business_types": business_types(),
        "sales_models": sales_models(),
    }
