"""
Platform Models — Facebook Shop, Instagram Shop, TikTok Shop, Calendly, Slack, Telegram.

Database models para todas plataformas con:
- Orders / Products sync
- Webhooks log
- Platform metadata
- Rate limiting / quotas
- Analytics tracking

Setup:
  pip install sqlalchemy psycopg2-binary

Migrations:
  alembic revision --autogenerate -m "Add platform models"
  alembic upgrade head
"""

from sqlalchemy import (
    create_engine, Column, String, Float, Integer, DateTime, Boolean, JSON, Text,
    ForeignKey, Enum, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import enum

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/sellia")

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class PlatformType(enum.Enum):
    """Supported platforms."""
    FACEBOOK_SHOP = "facebook_shop"
    INSTAGRAM_SHOP = "instagram_shop"
    TIKTOK_SHOP = "tiktok_shop"
    CALENDLY = "calendly"
    SLACK = "slack"
    TELEGRAM = "telegram"


class OrderStatus(enum.Enum):
    """Order lifecycle states."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(enum.Enum):
    """Payment states."""
    PENDING = "pending"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"


# ============= FACEBOOK SHOP MODELS =============

class FacebookShop(Base):
    """Facebook Shop account integration."""

    __tablename__ = "facebook_shops"

    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.id"), index=True)
    shop_id = Column(String, unique=True, index=True)
    access_token = Column(String)  # Encrypted
    page_id = Column(String)
    catalog_id = Column(String)
    webhook_url = Column(String)
    webhook_verify_token = Column(String)  # Encrypted
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime)
    metadata = Column(JSON, default=dict)  # settings, features, etc
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = relationship("FacebookOrder", back_populates="shop")
    products = relationship("FacebookProduct", back_populates="shop")


class FacebookProduct(Base):
    """Facebook Shop product catalog."""

    __tablename__ = "facebook_products"
    __table_args__ = (
        Index('idx_shop_sku', 'shop_id', 'sku'),
        UniqueConstraint('shop_id', 'facebook_product_id', name='uq_shop_fb_product'),
    )

    id = Column(String, primary_key=True)
    shop_id = Column(String, ForeignKey("facebook_shops.id"), index=True)
    facebook_product_id = Column(String, index=True)
    name = Column(String)
    description = Column(Text)
    price_usd = Column(Float)
    currency = Column(String, default="USD")
    sku = Column(String)
    stock = Column(Integer, default=0)
    images = Column(JSON, default=list)
    url = Column(String)
    category = Column(String)
    metadata = Column(JSON, default=dict)
    synced_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    shop = relationship("FacebookShop", back_populates="products")


class FacebookOrder(Base):
    """Facebook Shop orders."""

    __tablename__ = "facebook_orders"
    __table_args__ = (
        Index('idx_shop_status', 'shop_id', 'status'),
        UniqueConstraint('shop_id', 'facebook_order_id', name='uq_shop_fb_order'),
    )

    id = Column(String, primary_key=True)
    shop_id = Column(String, ForeignKey("facebook_shops.id"), index=True)
    facebook_order_id = Column(String, index=True)
    customer_name = Column(String)
    customer_email = Column(String, index=True)
    customer_phone = Column(String)
    total_amount = Column(Float)
    currency = Column(String, default="USD")
    items = Column(JSON)  # [{product_id, qty, price}]
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, index=True)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    shipping_address = Column(JSON)
    tracking_number = Column(String)
    notes = Column(Text)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    shop = relationship("FacebookShop", back_populates="orders")


# ============= INSTAGRAM SHOP MODELS =============

class InstagramShop(Base):
    """Instagram Shop account integration."""

    __tablename__ = "instagram_shops"

    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.id"), index=True)
    instagram_account_id = Column(String, unique=True, index=True)
    access_token = Column(String)  # Encrypted
    webhook_url = Column(String)
    webhook_verify_token = Column(String)  # Encrypted
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime)
    analytics = Column(JSON, default=dict)  # profile_views, website_clicks, etc
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = relationship("InstagramOrder", back_populates="shop")
    products = relationship("InstagramProduct", back_populates="shop")


class InstagramProduct(Base):
    """Instagram Shop product catalog."""

    __tablename__ = "instagram_products"
    __table_args__ = (
        Index('idx_shop_sku', 'shop_id', 'sku'),
        UniqueConstraint('shop_id', 'instagram_product_id', name='uq_shop_ig_product'),
    )

    id = Column(String, primary_key=True)
    shop_id = Column(String, ForeignKey("instagram_shops.id"), index=True)
    instagram_product_id = Column(String, index=True)
    name = Column(String)
    description = Column(Text)
    price_usd = Column(Float)
    currency = Column(String, default="USD")
    sku = Column(String)
    stock = Column(Integer, default=0)
    images = Column(JSON, default=list)
    category = Column(String)
    linked_post_id = Column(String)  # Instagram post/reel
    metadata = Column(JSON, default=dict)
    synced_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    shop = relationship("InstagramShop", back_populates="products")


class InstagramOrder(Base):
    """Instagram Shop Checkout orders."""

    __tablename__ = "instagram_orders"
    __table_args__ = (
        Index('idx_shop_status', 'shop_id', 'status'),
        UniqueConstraint('shop_id', 'instagram_order_id', name='uq_shop_ig_order'),
    )

    id = Column(String, primary_key=True)
    shop_id = Column(String, ForeignKey("instagram_shops.id"), index=True)
    instagram_order_id = Column(String, index=True)
    customer_name = Column(String)
    customer_email = Column(String, index=True)
    customer_phone = Column(String)
    total_amount = Column(Float)
    currency = Column(String, default="USD")
    items = Column(JSON)  # [{product_id, qty, price}]
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, index=True)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    checkout_url = Column(String)
    shipping_address = Column(JSON)
    tracking_number = Column(String)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    shop = relationship("InstagramShop", back_populates="orders")


# ============= TIKTOK SHOP MODELS =============

class TikTokShop(Base):
    """TikTok Shop account integration."""

    __tablename__ = "tiktok_shops"

    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.id"), index=True)
    shop_id = Column(String, unique=True, index=True)
    shop_cipher = Column(String)  # Encrypted shop ID for API
    access_token = Column(String)  # Encrypted
    refresh_token = Column(String)  # Encrypted
    webhook_url = Column(String)
    webhook_verify_token = Column(String)  # Encrypted
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime)
    quota_reset_at = Column(DateTime)  # For rate limit tracking
    quota_used = Column(Integer, default=0)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = relationship("TikTokOrder", back_populates="shop")
    products = relationship("TikTokProduct", back_populates="shop")


class TikTokProduct(Base):
    """TikTok Shop product catalog."""

    __tablename__ = "tiktok_products"
    __table_args__ = (
        Index('idx_shop_sku', 'shop_id', 'sku'),
        UniqueConstraint('shop_id', 'tiktok_product_id', name='uq_shop_tt_product'),
    )

    id = Column(String, primary_key=True)
    shop_id = Column(String, ForeignKey("tiktok_shops.id"), index=True)
    tiktok_product_id = Column(String, index=True)
    name = Column(String)
    description = Column(Text)
    price_usd = Column(Float)
    currency = Column(String, default="USD")
    sku = Column(String)
    stock = Column(Integer, default=0)
    images = Column(JSON, default=list)
    videos = Column(JSON, default=list)  # TikTok video product links
    category = Column(String)
    metadata = Column(JSON, default=dict)
    synced_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    shop = relationship("TikTokShop", back_populates="products")


class TikTokOrder(Base):
    """TikTok Shop orders."""

    __tablename__ = "tiktok_orders"
    __table_args__ = (
        Index('idx_shop_status', 'shop_id', 'status'),
        UniqueConstraint('shop_id', 'tiktok_order_id', name='uq_shop_tt_order'),
    )

    id = Column(String, primary_key=True)
    shop_id = Column(String, ForeignKey("tiktok_shops.id"), index=True)
    tiktok_order_id = Column(String, index=True)
    customer_name = Column(String)
    customer_email = Column(String, index=True)
    customer_phone = Column(String)
    total_amount = Column(Float)
    currency = Column(String, default="USD")
    items = Column(JSON)  # [{product_id, qty, price}]
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, index=True)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    fulfillment_type = Column(String)  # "seller_fulfillment", "tiktok_shop_fulfillment"
    shipping_address = Column(JSON)
    tracking_number = Column(String)
    tracking_provider = Column(String)
    estimated_delivery = Column(DateTime)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    shop = relationship("TikTokShop", back_populates="orders")


# ============= CALENDLY MODELS =============

class CalendlyAccount(Base):
    """Calendly account integration."""

    __tablename__ = "calendly_accounts"

    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.id"), index=True)
    calendly_user_uri = Column(String, unique=True, index=True)
    access_token = Column(String)  # Encrypted
    refresh_token = Column(String)  # Encrypted
    webhook_url = Column(String)
    webhook_uuid = Column(String)  # Calendly webhook subscription ID
    is_active = Column(Boolean, default=True)
    sync_with_google = Column(Boolean, default=True)
    sync_with_outlook = Column(Boolean, default=False)
    auto_reminders = Column(Boolean, default=True)
    reminder_minutes_before = Column(Integer, default=15)
    timezone = Column(String, default="UTC")
    last_sync = Column(DateTime)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    events = relationship("CalendlyEvent", back_populates="account")


class CalendlyEvent(Base):
    """Calendly scheduled events."""

    __tablename__ = "calendly_events"
    __table_args__ = (
        Index('idx_account_status', 'account_id', 'status'),
        UniqueConstraint('account_id', 'calendly_event_uri', name='uq_account_event'),
    )

    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("calendly_accounts.id"), index=True)
    calendly_event_uri = Column(String, index=True)
    event_title = Column(String)
    invitee_name = Column(String)
    invitee_email = Column(String, index=True)
    invitee_phone = Column(String)
    start_time = Column(DateTime, index=True)
    end_time = Column(DateTime)
    duration_minutes = Column(Integer)
    status = Column(String, default="scheduled")  # scheduled, cancelled
    location = Column(String)  # Zoom URL, phone, physical address
    notes = Column(Text)
    synced_to_google = Column(Boolean, default=False)
    google_calendar_event_id = Column(String)
    reminder_sent = Column(Boolean, default=False)
    cancellation_reason = Column(String)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    account = relationship("CalendlyAccount", back_populates="events")


# ============= SLACK MODELS =============

class SlackWorkspace(Base):
    """Slack workspace integration."""

    __tablename__ = "slack_workspaces"

    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.id"), index=True)
    team_id = Column(String, unique=True, index=True)
    team_name = Column(String)
    bot_user_id = Column(String)
    bot_access_token = Column(String)  # Encrypted
    webhook_url = Column(String)  # Incoming webhook for bot
    installed_by = Column(String)  # user_id
    is_active = Column(Boolean, default=True)
    scopes = Column(JSON, default=list)  # OAuth scopes granted
    features_enabled = Column(JSON, default=dict)  # {orders: true, analytics: true, ...}
    notification_channel = Column(String)  # Default channel for alerts
    last_sync = Column(DateTime)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    commands = relationship("SlackCommand", back_populates="workspace")
    messages = relationship("SlackMessage", back_populates="workspace")


class SlackCommand(Base):
    """Slack slash commands usage log."""

    __tablename__ = "slack_commands"

    id = Column(String, primary_key=True)
    workspace_id = Column(String, ForeignKey("slack_workspaces.id"), index=True)
    command = Column(String)  # /status, /analytics, /orders
    user_id = Column(String)
    user_name = Column(String)
    text_input = Column(String)
    response = Column(Text)
    status_code = Column(Integer)
    executed_at = Column(DateTime, default=datetime.utcnow, index=True)

    workspace = relationship("SlackWorkspace", back_populates="commands")


class SlackMessage(Base):
    """Slack messages sent by bot."""

    __tablename__ = "slack_messages"

    id = Column(String, primary_key=True)
    workspace_id = Column(String, ForeignKey("slack_workspaces.id"), index=True)
    channel_id = Column(String)
    message_type = Column(String)  # alert, report, notification
    title = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("SlackWorkspace", back_populates="messages")


# ============= TELEGRAM MODELS =============

class TelegramBot(Base):
    """Telegram bot integration."""

    __tablename__ = "telegram_bots"

    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.id"), index=True)
    bot_token = Column(String, unique=True)  # Encrypted
    bot_username = Column(String, unique=True, index=True)
    bot_name = Column(String)
    webhook_url = Column(String)
    webhook_secret = Column(String)  # Encrypted
    is_active = Column(Boolean, default=True)
    is_webhook_active = Column(Boolean, default=False)
    features_enabled = Column(JSON, default=dict)  # {orders: true, support: true, ...}
    commands_enabled = Column(JSON, default=list)  # [/start, /status, /orders]
    deep_link_enabled = Column(Boolean, default=False)
    last_update_id = Column(Integer, default=0)  # For polling fallback
    last_sync = Column(DateTime)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = relationship("TelegramUser", back_populates="bot")
    messages = relationship("TelegramMessage", back_populates="bot")


class TelegramUser(Base):
    """Telegram users interacting with bot."""

    __tablename__ = "telegram_users"
    __table_args__ = (
        UniqueConstraint('bot_id', 'telegram_user_id', name='uq_bot_user'),
    )

    id = Column(String, primary_key=True)
    bot_id = Column(String, ForeignKey("telegram_bots.id"), index=True)
    telegram_user_id = Column(Integer, index=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    phone_number = Column(String)
    language_code = Column(String, default="en")
    is_bot = Column(Boolean, default=False)
    status = Column(String, default="active")  # active, blocked, inactive
    notifications_enabled = Column(Boolean, default=True)
    first_interaction = Column(DateTime)
    last_interaction = Column(DateTime)
    conversation_state = Column(JSON, default=dict)  # For maintaining context
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    bot = relationship("TelegramBot", back_populates="users")
    messages = relationship("TelegramMessage", back_populates="user")


class TelegramMessage(Base):
    """Telegram messages log."""

    __tablename__ = "telegram_messages"

    id = Column(String, primary_key=True)
    bot_id = Column(String, ForeignKey("telegram_bots.id"), index=True)
    user_id = Column(String, ForeignKey("telegram_users.id"), index=True)
    message_id = Column(Integer)
    chat_id = Column(Integer)
    text = Column(Text)
    message_type = Column(String)  # text, command, notification, alert
    response_text = Column(Text)
    response_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)

    bot = relationship("TelegramBot", back_populates="messages")
    user = relationship("TelegramUser", back_populates="messages")


# ============= WEBHOOK EVENT LOG (ALL PLATFORMS) =============

class PlatformWebhookEvent(Base):
    """Unified webhook event log for all platforms."""

    __tablename__ = "platform_webhook_events"
    __table_args__ = (
        Index('idx_platform_type', 'platform_type'),
        Index('idx_account_platform', 'account_id', 'platform_type'),
        Index('idx_processed', 'processed'),
        Index('idx_created', 'created_at'),
    )

    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.id"), index=True)
    platform_type = Column(Enum(PlatformType), index=True)
    event_type = Column(String)  # order.created, payment.completed, etc
    external_id = Column(String)  # Event ID from platform
    payload = Column(JSON)
    signature = Column(String)  # Webhook signature for verification
    processed = Column(Boolean, default=False, index=True)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)


# ============= PLATFORM CREDENTIALS (ENCRYPTED) =============

class PlatformCredential(Base):
    """Securely store platform API credentials."""

    __tablename__ = "platform_credentials"
    __table_args__ = (
        UniqueConstraint('account_id', 'platform_type', name='uq_account_platform_cred'),
    )

    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.id"), index=True)
    platform_type = Column(Enum(PlatformType), index=True)
    credential_type = Column(String)  # api_key, oauth_token, webhook_secret
    credential_value = Column(String)  # Encrypted
    expires_at = Column(DateTime)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============= RATE LIMIT TRACKING =============

class PlatformRateLimit(Base):
    """Track rate limits for each platform."""

    __tablename__ = "platform_rate_limits"
    __table_args__ = (
        UniqueConstraint('account_id', 'platform_type', 'endpoint', name='uq_account_endpoint'),
    )

    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.id"), index=True)
    platform_type = Column(Enum(PlatformType), index=True)
    endpoint = Column(String)  # API endpoint path
    requests_made = Column(Integer, default=0)
    requests_limit = Column(Integer)
    reset_at = Column(DateTime, index=True)
    last_request_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============= SYNC STATUS =============

class PlatformSyncStatus(Base):
    """Track sync status for each platform."""

    __tablename__ = "platform_sync_status"
    __table_args__ = (
        UniqueConstraint('account_id', 'platform_type', name='uq_account_platform_sync'),
    )

    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.id"), index=True)
    platform_type = Column(Enum(PlatformType), index=True)
    sync_type = Column(String)  # products, orders, events
    last_sync_at = Column(DateTime)
    next_sync_at = Column(DateTime)
    items_synced = Column(Integer, default=0)
    status = Column(String, default="idle")  # idle, syncing, error
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============= DATABASE INIT =============

def init_db() -> None:
    """Create all tables in database."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for obtaining DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
