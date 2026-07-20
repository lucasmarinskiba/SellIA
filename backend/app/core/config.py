import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from functools import lru_cache


class Settings(BaseSettings):
    # Database - MUST be set via environment variable, no hardcoded defaults
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    # SECRET_KEY - MUST be set via environment variable, enforced in validation
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    KIMI_API_KEY: str | None = None  # Moonshot AI (Kimi K2.5) — OpenAI-compatible API
    GROQ_API_KEY: str | None = None  # Groq — free/ultra-fast Llama/Mixtral inference (OpenAI-compatible)
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    OLLAMA_BASE_URL: str = "http://localhost:11434"  # Ollama local LLM server

    # AI Content Generation APIs
    STABILITY_API_KEY: str | None = None  # Stable Diffusion / Stability AI
    REPLICATE_API_KEY: str | None = None  # Replicate (Runway, Flux, etc.)
    RUNWAY_API_KEY: str | None = None     # Runway Gen-4 video
    MIDJOURNEY_API_KEY: str | None = None  # Midjourney (via API proxy)
    ELEVENLABS_API_KEY: str | None = None  # ElevenLabs voice/AI audio
    FAL_KEY: str | None = None            # fal.ai (Seedance 2.0, Flux, etc.)

    # Additional Content Generation APIs
    LEONARDO_API_KEY: str | None = None       # Leonardo.ai image generation
    PHOTOROOM_API_KEY: str | None = None      # Photoroom product photos
    IDEOGRAM_API_KEY: str | None = None       # Ideogram 2.0 text-in-image
    HEYGEN_API_KEY: str | None = None         # HeyGen AI avatars
    PIKA_API_KEY: str | None = None           # Pika Labs video
    OPUSCLIP_API_KEY: str | None = None       # Opus Clip video repurposing
    COPYAI_API_KEY: str | None = None         # Copy.ai marketing copy
    JASPER_API_KEY: str | None = None         # Jasper long-form copy
    BEAUTIFULAI_API_KEY: str | None = None    # Beautiful.ai presentations
    GAMMA_API_KEY: str | None = None          # Gamma docs/presentations
    SUNO_API_KEY: str | None = None           # Suno AI music
    MUREKA_API_KEY: str | None = None         # Mureka AI music
    KLING_API_KEY: str | None = None          # Kling AI video
    MINIMAX_API_KEY: str | None = None        # Minimax AI video
    LUMA_API_KEY: str | None = None           # Luma Dream Machine 3D video
    ADCREATIVE_API_KEY: str | None = None     # AdCreative.ai ad banners
    WRITESONIC_API_KEY: str | None = None     # Writesonic SEO + ads
    CANVA_API_KEY: str | None = None          # Canva design API
    CAPCUT_API_KEY: str | None = None         # CapCut video editing

    # Seguridad
    ENVIRONMENT: str = "development"  # development | production
    ENABLE_OPENAPI: bool = True
    SIDECAR_SHARED_SECRET: str = ""

    # Database SSL (production)
    DB_SSL_MODE: str = "prefer"  # disable | allow | prefer | require | verify-ca | verify-full
    DB_SSL_CA: str | None = None  # path to CA certificate for verify-ca / verify-full

    # Cloudflare Turnstile
    TURNSTILE_SECRET_KEY: str | None = None

    # Email Tracking
    TRACKING_BASE_URL: str | None = None  # e.g. https://app.sellia.com

    # Frontend URL (for redirects and webhooks)
    FRONTEND_URL: str | None = None  # e.g. https://app.sellia.com

    # MercadoPago
    MERCADOPAGO_ACCESS_TOKEN: str | None = None

    # Payoneer (International USD payments)
    PAYONEER_PROGRAM_ID: str | None = None
    PAYONEER_CLIENT_ID: str | None = None
    PAYONEER_CLIENT_SECRET: str | None = None
    PAYONEER_WEBHOOK_SECRET: str | None = None

    # Crypto (USDT)
    CREATOR_USDT_TRC20_ADDRESS: str | None = None
    CREATOR_USDT_BEP20_ADDRESS: str | None = None
    TRONGRID_API_KEY: str | None = None
    BSCSCAN_API_KEY: str | None = None

    # Creator billing / fiscal information
    CREATOR_MP_ALIAS: str | None = None           # MercadoPago alias
    CREATOR_COCO_ALIAS: str | None = None         # Coco alias (transfers)
    CREATOR_CBU: str | None = None                # Bank CBU
    CREATOR_CUIT: str | None = None               # Argentinian tax ID
    CREATOR_FULL_NAME: str | None = None          # Legal name for invoices
    CREATOR_BUSINESS_NAME: str | None = None      # Razón social
    CREATOR_BILLING_ADDRESS: str | None = None    # Fiscal address
    CREATOR_IVA_CONDITION: str | None = None      # Monotributo / RI / Exento

    # ReAct Orchestrator
    USE_REACT_ORCHESTRATOR: bool = True

    # Computer Use Agents
    COMPUTER_USE_ENABLED: bool = True
    COMPUTER_USE_MAX_STEPS: int = 30
    COMPUTER_USE_TIMEOUT_SECONDS: int = 300
    COMPUTER_USE_SCREENSHOT_QUALITY: int = 75
    COMPUTER_USE_MAX_SCREENSHOT_WIDTH: int = 1280
    # Performance / precision tuning
    COMPUTER_USE_BLOCK_RESOURCES: bool = True       # block heavy images/media/fonts/ads → faster loads
    COMPUTER_USE_NAV_TIMEOUT_MS: int = 30000        # navigation hard timeout
    COMPUTER_USE_SETTLE_TIMEOUT_MS: int = 4000      # max wait for network/DOM settle after action
    COMPUTER_USE_ACTION_SETTLE_MS: int = 250        # short post-action settle floor
    COMPUTER_USE_TYPE_DELAY_MS: int = 6             # per-char keystroke delay
    COMPUTER_USE_DEVICE_SCALE: float = 1.0          # device scale factor (lower = smaller screenshots)
    COMPUTER_USE_URL_WHITELIST: list[str] = [
        # Diseño / Presentaciones
        "canva.com",
        "gamma.app",
        "beautiful.ai",
        "figma.com",
        "framer.com",
        "invideo.io",
        "capcut.com",
        # Google Workspace
        "docs.google.com",
        "sheets.google.com",
        "drive.google.com",
        "slides.google.com",
        "mail.google.com",
        "google.com",
        # Redes Sociales
        "linkedin.com",
        "twitter.com",
        "x.com",
        "instagram.com",
        "facebook.com",
        "meta.com",
        "youtube.com",
        "tiktok.com",
        "threads.net",
        # E-commerce & Marketplaces
        "mercadolibre.com",
        "mercadolibre.com.ar",
        "mercadolibre.com.br",
        "mercadolibre.com.mx",
        "mercadolibre.com.co",
        "mercadolibre.com.uy",
        "mercadolibre.com.cl",
        "mercadolibre.com.pe",
        "shopify.com",
        "myshopify.com",
        "woocommerce.com",
        "amazon.com",
        "amazon.com.mx",
        "amazon.com.br",
        "sellercentral.amazon.com",
        "vendorcentral.amazon.com",
        "hotmart.com",
        "hotmart.market",
        "app.hotmart.com",
        "beacons.ai",
        "beacons.page",
        "linktr.ee",
        # TikTok Shop & Business
        "seller.tiktok.com",
        "affiliate.tiktok.com",
        "business.tiktok.com",
        "tiktok.com/business",
        # Meta Business
        "business.facebook.com",
        "facebook.com/business",
        "business.instagram.com",
        " creators.instagram.com",
        # Publicidad
        "ads.google.com",
        "adwords.google.com",
        "ads.facebook.com",
        "adsmanager.facebook.com",
        "business.facebook.com/adsmanager",
        # SEO & Analytics
        "search.google.com",
        "pagespeed.web.dev",
        "analytics.google.com",
        "searchconsole.google.com",
        "trends.google.com",
        "keywordtool.io",
        "ubersuggest.com",
        "answerthepublic.com",
        # Web / CMS
        "wordpress.com",
        "webflow.com",
        "wix.com",
        "squarespace.com",
        "godaddy.com",
        "namecheap.com",
        # Productividad & CRM
        "notion.so",
        "trello.com",
        "asana.com",
        "hubspot.com",
        "salesforce.com",
        "zoho.com",
        "calendly.com",
        "typeform.com",
        "jotform.com",
        # Email Marketing
        "mailchimp.com",
        "convertkit.com",
        "activecampaign.com",
        "mailerlite.com",
        "sendinblue.com",
        "brevo.com",
        # Scheduling Social
        "later.com",
        "buffer.com",
        "hootsuite.com",
        "sproutsocial.com",
        "metricool.com",
        "creatorstudio.facebook.com",
        # Pagos
        "stripe.com",
        "paypal.com",
        "wise.com",
        "mercadopago.com.ar",
        "mercadopago.com.br",
        "mercadopago.com.mx",
        "payoneer.com",
        "payu.com",
        # Logística
        "andreani.com",
        "andreani.com.ar",
        "dhl.com",
        "dhlexpress.com",
        "fedex.com",
        "ups.com",
        "correoargentino.com.ar",
        "oca.com.ar",
        "shipstation.com",
        "shipbob.com",
        "aftership.com",
        # Print on Demand
        "printful.com",
        "printify.com",
        # Video / Reuniones
        "zoom.us",
        "meet.google.com",
        # Búsqueda
        "bing.com",
        "duckduckgo.com",
        "yahoo.com",
        # Marketplaces adicionales
        "etsy.com",
        "aliexpress.com",
        "shopee.com",
        "shopee.com.br",
        "shopee.com.mx",
        "shopee.com.ar",
        # Delivery Apps
        "rappi.com",
        "rappi.com.ar",
        "pedidosya.com",
        "pedidosya.com.ar",
        "ubereats.com",
        "ifood.com.br",
        # Product Hunt / Tech
        "producthunt.com",
        "github.com",
        "gitlab.com",
        "vercel.com",
        "netlify.com",
        # App Stores
        "play.google.com",
        "apps.apple.com",
        "appstoreconnect.apple.com",
        # Pinterest
        "pinterest.com",
        "pinterest.com.ar",
        "pinterest.es",
        # WhatsApp / Telegram
        "web.whatsapp.com",
        "whatsapp.com",
        "web.telegram.org",
        "telegram.org",
        # Google Business Profile
        "business.google.com",
        "google.com/business",
        # Semrush / Ahrefs / SEO tools
        "semrush.com",
        "ahrefs.com",
        "moz.com",
        "screamingfrog.co.uk",
        "gtmetrix.com",
        # Facebook Shops
        "facebook.com/commerce",
        "instagram.com/shopping",
        # Additional Meta
        "meta.com/business",
        "facebook.com/business",
        # TikTok Ads
        "ads.tiktok.com",
        "business.tiktok.com",
        # Additional Google
        "ads.google.com/home",
        "adwords.google.com",
        "google.com/retail",
        "merchants.google.com",
        # Cloudflare
        "cloudflare.com",
        "dash.cloudflare.com",
        # Additional payment
        "komoju.com",
        "rapyd.net",
        "dlocal.com",
        "ebanx.com",
        # Additional shipping
        "moova.com.ar",
        "envio.pack",
        "caba-envios",
        "loggi.com",
        "loggi.com.br",
    ]
    COMPUTER_USE_URL_BLACKLIST: list[str] = [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
        "192.168.",
        "10.0.",
        "172.16.",
        "bank",
        "banco",
        "santander",
        "galicia",
        "bbva",
        "itau",
        "nacion",
        "provincia",
        "icbc",
        "macro",
        "brubank",
        "rebanking",
        "naranja",
        "mercadopago.com/mla",
        "mercadopago.com/money",
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def normalize_database_url(self):
        """Normaliza DATABASE_URL al driver async.

        Proveedores como Render/Heroku entregan `postgres://` o
        `postgresql://` (driver sync). La app usa asyncpg, así que reescribimos
        el scheme a `postgresql+asyncpg://` para que funcione sin tocar el panel.
        """
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = "postgresql+asyncpg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+asyncpg://" + url[len("postgresql://"):]
        if url != self.DATABASE_URL:
            self.DATABASE_URL = url
        return self

    @model_validator(mode="after")
    def validate_security(self):
        # P0: DATABASE_URL is always required - no defaults allowed
        if not self.DATABASE_URL:
            raise ValueError(
                "DATABASE_URL es requerido en todos los entornos. "
                "Configure la variable de entorno DATABASE_URL con credentials seguros."
            )
        if "devpassword123" in self.DATABASE_URL or "password" in self.DATABASE_URL.lower() and "postgres://" in self.DATABASE_URL:
            # Check for common insecure patterns
            if any(weak in self.DATABASE_URL.lower() for weak in ["devpassword", "password123", "postgres://user:password@"]):
                raise ValueError(
                    "DATABASE_URL contiene credenciales débiles o por defecto. "
                    "Use contraseñas seguras (mínimo 16 caracteres alfanuméricos + símbolos)."
                )

        # P0: SECRET_KEY is always required - NEVER auto-assign even in dev
        if not self.SECRET_KEY:
            raise ValueError(
                "SECRET_KEY es requerido en TODOS los entornos. "
                "Genérese con: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )

        # Validate SECRET_KEY strength
        insecure_defaults = [
            "cambia_esta_clave_en_produccion_minimo_32_caracteres",
            "supersecretkeychangethisinproduction",
            "devpassword123",
            "dev-only-not-secure-32-chars-long-1234567890",
            "supersecretkey",
        ]

        if self.SECRET_KEY.lower() in [d.lower() for d in insecure_defaults]:
            raise ValueError(
                "SECRET_KEY está usando un valor por defecto inseguro. "
                "Genérese con: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )

        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY debe tener al menos 32 caracteres.")

        # Production-specific checks
        if self.ENVIRONMENT == "production":
            if not self.SIDECAR_SHARED_SECRET:
                raise ValueError(
                    "SIDECAR_SHARED_SECRET es requerido en producción cuando se usa Envoy sidecar."
                )

        # Validate FERNET_SECRET if defined
        fernet_secret = os.environ.get("FERNET_SECRET")
        if fernet_secret and len(fernet_secret) < 32:
            raise ValueError(
                "FERNET_SECRET debe tener al menos 32 caracteres. "
                "Use: openssl rand -base64 32"
            )
        return self


@lru_cache()
def get_settings() -> Settings:
    return Settings()
