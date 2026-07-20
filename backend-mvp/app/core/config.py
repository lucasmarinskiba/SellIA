"""App settings · loaded from env vars."""
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    ENV: str = "dev"  # dev | staging | prod
    SECRET_KEY: str
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:56621"]

    # Database
    DATABASE_URL: str  # postgresql+asyncpg://user:pass@host:5432/sellia
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str  # redis://localhost:6379/0

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MIN: int = 60 * 24 * 7  # 7 days

    # Anthropic
    ANTHROPIC_API_KEY: str | None = None

    # Groq (cheap+fast cloud LLM)
    GROQ_API_KEY: str | None = None

    # Ollama (fallback local)
    OLLAMA_URL: str = "http://localhost:11434"

    # Stripe
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None

    # WhatsApp Cloud API
    WA_VERIFY_TOKEN: str | None = None
    WA_APP_SECRET: str | None = None
    WA_PHONE_NUMBER_ID: str | None = None
    WA_ACCESS_TOKEN: str | None = None

    # Meta App (for WhatsApp Embedded Signup OAuth)
    META_APP_ID: str | None = None
    META_APP_SECRET: str | None = None

    # Email (Resend)
    RESEND_API_KEY: str | None = None
    EMAIL_FROM: str = "SellIA <no-reply@sellia.app>"

    # Browser extension OAuth
    EXTENSION_VERIFY_BASE: str = "https://app.sellia.app"

    # Observability
    SENTRY_DSN: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
