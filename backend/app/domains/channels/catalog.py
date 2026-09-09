"""What each platform actually needs in order to be connected.

The connectors read specific keys out of ChannelConnection.credentials
(mercadolibre reads client_id/client_secret/access_token/seller_id, whatsapp
reads api_token/phone_number_id/…), but nothing ever declared those keys to the
UI. So "conectar una plataforma" had no honest form to render: the dashboard
could show a platform as available while the account had no way to supply what
the connector needs.

This registry is derived from what the connector code really reads --
`required` are the keys without which the connector cannot send or receive at
all, `optional` the ones that unlock extra capability. Keep it in sync when a
connector starts reading a new key.
"""

from __future__ import annotations

from typing import Any

#: platform -> spec. `oauth` means app/api/v1/channels.py's auth-url route can
#: complete the connection after the app credentials are saved.
CONNECTOR_CATALOG: dict[str, dict[str, Any]] = {
    "whatsapp": {
        "label": "WhatsApp Business",
        "group": "mensajeria",
        "oauth": True,
        "required": [
            {"key": "api_token", "label": "Token de acceso permanente", "secret": True},
            {"key": "phone_number_id", "label": "Phone Number ID", "secret": False},
        ],
        "optional": [
            {"key": "business_account_id", "label": "WhatsApp Business Account ID", "secret": False},
        ],
        "help": "Se obtienen en Meta for Developers → tu app → WhatsApp → Configuración de la API.",
        "docs_url": "https://developers.facebook.com/docs/whatsapp/cloud-api/get-started",
    },
    "instagram": {
        "label": "Instagram",
        "group": "redes",
        "oauth": True,
        "required": [
            {"key": "api_token", "label": "Token de página (Page Access Token)", "secret": True},
            {"key": "instagram_account_id", "label": "Instagram Business Account ID", "secret": False},
        ],
        "optional": [{"key": "page_id", "label": "Facebook Page ID", "secret": False}],
        "help": "Tu cuenta de Instagram tiene que ser Profesional y estar vinculada a una página de Facebook.",
        "docs_url": "https://developers.facebook.com/docs/instagram-api/getting-started",
    },
    "messenger": {
        "label": "Facebook Messenger",
        "group": "mensajeria",
        "oauth": True,
        "required": [
            {"key": "api_token", "label": "Page Access Token", "secret": True},
            {"key": "page_id", "label": "Page ID", "secret": False},
        ],
        "optional": [],
        "help": "Se generan en Meta for Developers con los permisos pages_messaging.",
        "docs_url": "https://developers.facebook.com/docs/messenger-platform/getting-started",
    },
    "telegram": {
        "label": "Telegram",
        "group": "mensajeria",
        "oauth": False,
        "required": [{"key": "bot_token", "label": "Token del bot", "secret": True}],
        "optional": [{"key": "webhook_secret", "label": "Secreto del webhook", "secret": True}],
        "help": "Creá el bot con @BotFather en Telegram y pegá el token que te da.",
        "docs_url": "https://core.telegram.org/bots#how-do-i-create-a-bot",
    },
    "mercadolibre": {
        "label": "MercadoLibre",
        "group": "marketplace",
        "oauth": True,
        "required": [
            {"key": "client_id", "label": "App ID", "secret": False},
            {"key": "client_secret", "label": "Secret Key", "secret": True},
        ],
        "optional": [
            {"key": "seller_id", "label": "ID de vendedor", "secret": False},
            {"key": "access_token", "label": "Access token (lo completa la autorización)", "secret": True},
        ],
        "help": "Creá una aplicación en MercadoLibre Developers; después usá 'Autorizar' para que ML "
                "te devuelva el token. Con esto la IA responde también las preguntas de tus publicaciones.",
        "docs_url": "https://developers.mercadolibre.com.ar/es_ar/registra-tu-aplicacion",
    },
    "amazon": {
        "label": "Amazon",
        "group": "marketplace",
        "oauth": False,
        "required": [
            {"key": "lwa_app_id", "label": "LWA App ID", "secret": False},
            {"key": "lwa_client_secret", "label": "LWA Client Secret", "secret": True},
            {"key": "refresh_token", "label": "Refresh token", "secret": True},
            {"key": "marketplace_id", "label": "Marketplace ID", "secret": False},
        ],
        "optional": [
            {"key": "seller_id", "label": "Seller ID", "secret": False},
            {"key": "aws_access_key", "label": "AWS Access Key", "secret": True},
            {"key": "aws_secret_key", "label": "AWS Secret Key", "secret": True},
            {"key": "role_arn", "label": "Role ARN", "secret": False},
        ],
        "help": "Necesitás una app en Amazon Selling Partner API (SP-API) aprobada para tu cuenta de vendedor.",
        "docs_url": "https://developer-docs.amazon.com/sp-api/docs/registering-your-application",
    },
    "shopify": {
        "label": "Shopify",
        "group": "ecommerce",
        "oauth": False,
        "required": [
            {"key": "shop_domain", "label": "Dominio de la tienda (mitienda.myshopify.com)", "secret": False},
            {"key": "admin_api_token", "label": "Admin API access token", "secret": True},
        ],
        "optional": [
            {"key": "api_key", "label": "API key", "secret": False},
            {"key": "api_secret", "label": "API secret", "secret": True},
            {"key": "webhook_secret", "label": "Webhook secret", "secret": True},
        ],
        "help": "En tu admin de Shopify: Configuración → Apps y canales de venta → Desarrollar apps.",
        "docs_url": "https://shopify.dev/docs/apps/auth/admin-app-access-tokens",
    },
    "woocommerce": {
        "label": "WooCommerce",
        "group": "ecommerce",
        "oauth": False,
        "required": [
            {"key": "site_url", "label": "URL de tu tienda", "secret": False},
            {"key": "consumer_key", "label": "Consumer key", "secret": False},
            {"key": "consumer_secret", "label": "Consumer secret", "secret": True},
        ],
        "optional": [{"key": "webhook_secret", "label": "Webhook secret", "secret": True}],
        "help": "WooCommerce → Ajustes → Avanzado → REST API → Añadir clave (permisos de lectura/escritura).",
        "docs_url": "https://woocommerce.github.io/woocommerce-rest-api-docs/#authentication",
    },
    "tiktok_shop": {
        "label": "TikTok Shop",
        "group": "marketplace",
        "oauth": False,
        "required": [
            {"key": "client_id", "label": "App key", "secret": False},
            {"key": "client_secret", "label": "App secret", "secret": True},
            {"key": "access_token", "label": "Access token", "secret": True},
            {"key": "shop_id", "label": "Shop ID", "secret": False},
        ],
        "optional": [
            {"key": "shop_cipher", "label": "Shop cipher", "secret": False},
            {"key": "refresh_token", "label": "Refresh token", "secret": True},
        ],
        "help": "Se generan en TikTok Shop Partner Center al crear tu app.",
        "docs_url": "https://partner.tiktokshop.com/docv2/page/getting-started",
    },
    "etsy": {
        "label": "Etsy",
        "group": "marketplace",
        "oauth": False,
        "required": [
            {"key": "api_keystring", "label": "API keystring", "secret": True},
            {"key": "access_token", "label": "Access token", "secret": True},
            {"key": "shop_id", "label": "Shop ID", "secret": False},
        ],
        "optional": [{"key": "shared_secret", "label": "Shared secret", "secret": True}],
        "help": "Registrá una app en Etsy Developers y autorizala sobre tu tienda.",
        "docs_url": "https://developers.etsy.com/documentation/essentials/authentication",
    },
    "hotmart": {
        "label": "Hotmart",
        "group": "marketplace",
        "oauth": False,
        "required": [
            {"key": "client_id", "label": "Client ID", "secret": False},
            {"key": "client_secret", "label": "Client secret", "secret": True},
            {"key": "basic_token", "label": "Basic token", "secret": True},
        ],
        "optional": [{"key": "hottok", "label": "Hottok (validación de webhooks)", "secret": True}],
        "help": "Hotmart → Herramientas → Credenciales de API.",
        "docs_url": "https://developers.hotmart.com/docs/en/start/app-auth/",
    },
    "email": {
        "label": "Email (SMTP)",
        "group": "mensajeria",
        "oauth": False,
        "required": [
            {"key": "smtp_host", "label": "Servidor SMTP", "secret": False},
            {"key": "smtp_port", "label": "Puerto", "secret": False},
            {"key": "smtp_user", "label": "Usuario", "secret": False},
            {"key": "smtp_password", "label": "Contraseña", "secret": True},
            {"key": "from_address", "label": "Dirección remitente", "secret": False},
        ],
        "optional": [],
        "help": "Si usás Gmail o Outlook con 2FA, generá una contraseña de aplicación en lugar de la tuya.",
        "docs_url": "",
    },
    "webchat": {
        "label": "Chat en tu web",
        "group": "redes",
        "oauth": False,
        "required": [{"key": "widget_id", "label": "ID del widget", "secret": False}],
        "optional": [],
        "help": "El widget se pega en tu sitio y las consultas entran al mismo inbox que el resto.",
        "docs_url": "",
    },
    "manychat": {
        "label": "ManyChat",
        "group": "mensajeria",
        "oauth": False,
        "required": [{"key": "api_token", "label": "API token", "secret": True}],
        "optional": [],
        "help": "ManyChat → Settings → API.",
        "docs_url": "https://api.manychat.com/",
    },
    "linkedin": {
        "label": "LinkedIn",
        "group": "redes",
        "oauth": False,
        "required": [
            {"key": "access_token", "label": "Access token", "secret": True},
            {"key": "sender_urn", "label": "URN del remitente", "secret": False},
        ],
        "optional": [],
        "help": "Requiere una app aprobada en LinkedIn Developers con permisos de mensajería.",
        "docs_url": "https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow",
    },
}

#: Platforms whose credentials the UI must never echo back once saved.
SECRET_KEYS = {
    field["key"]
    for spec in CONNECTOR_CATALOG.values()
    for field in (*spec.get("required", []), *spec.get("optional", []))
    if field.get("secret")
}


def catalog_entries() -> list[dict[str, Any]]:
    return [{"platform": platform, **spec} for platform, spec in CONNECTOR_CATALOG.items()]


def mask_credentials(credentials: dict[str, Any] | None) -> dict[str, Any]:
    """Never return a stored secret to the browser -- only whether it is set."""
    if not credentials:
        return {}
    return {
        key: ("configurado" if key in SECRET_KEYS and value else value)
        for key, value in credentials.items()
    }


def missing_required(platform: str, credentials: dict[str, Any] | None) -> list[str]:
    """Which required keys this connection still lacks, by the connector's own
    definition of required. Drives the honest 'falta configurar X' state."""
    spec = CONNECTOR_CATALOG.get(platform)
    if not spec:
        return []
    creds = credentials or {}
    return [
        field["label"]
        for field in spec.get("required", [])
        if not creds.get(field["key"])
    ]
