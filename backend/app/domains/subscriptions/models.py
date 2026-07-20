import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Numeric, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base
import enum


class PaymentProvider(str, enum.Enum):
    MERCADOPAGO = "mercadopago"
    STRIPE = "stripe"
    CRYPTO = "crypto"
    MANUAL = "manual"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class InvoiceType(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    INTL = "INTL"


class InvoiceStatus(str, enum.Enum):
    PENDING = "pending"
    EMITTED = "emitted"
    CANCELLED = "cancelled"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    INACTIVE = "inactive"


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    price_monthly_ars = Column(Numeric(10, 2), nullable=True)
    price_yearly_ars = Column(Numeric(10, 2), nullable=True)
    price_monthly_usd = Column(Numeric(10, 2), nullable=True)
    price_yearly_usd = Column(Numeric(10, 2), nullable=True)
    price_monthly_latam_usd = Column(Numeric(10, 2), nullable=True)
    price_yearly_latam_usd = Column(Numeric(10, 2), nullable=True)
    limits = Column(JSONB, default=dict, nullable=False)
    features = Column(JSONB, default=list, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    billing_cycle_options = Column(JSONB, default=list, nullable=False)
    target_regions = Column(JSONB, default=list, nullable=False)
    trial_days = Column(Integer, default=14, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    subscriptions = relationship("Subscription", back_populates="plan", foreign_keys="Subscription.plan_id")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.TRIALING, nullable=False)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)
    stripe_customer_id = Column(String(100), nullable=True)
    stripe_subscription_id = Column(String(100), nullable=True)
    mercadopago_preference_id = Column(String(100), nullable=True)
    mercadopago_payment_id = Column(String(100), nullable=True)
    mercadopago_preapproval_id = Column(String(100), nullable=True)
    billing_cycle = Column(String(10), default="monthly", nullable=False)
    payment_provider = Column(String(20), nullable=True)
    payment_method_id = Column(String(100), nullable=True)
    crypto_network = Column(String(20), nullable=True)
    crypto_wallet_address = Column(String(100), nullable=True)
    next_billing_date = Column(DateTime(timezone=True), nullable=True)
    grace_period_end = Column(DateTime(timezone=True), nullable=True)
    auto_renew = Column(Boolean, default=True, nullable=False)
    invoice_data = Column(JSONB, default=dict, nullable=False)
    downgrade_to_plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id", ondelete="SET NULL"), nullable=True)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="subscription")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions", foreign_keys="[Subscription.plan_id]")


class UserAPIKey(Base):
    __tablename__ = "user_api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)
    encrypted_key = Column(Text, nullable=False)  # bcrypt hash (legacy)
    api_key_fernet = Column(Text, nullable=True)  # Fernet encrypted (reversible)
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class UsageTracking(Base):
    __tablename__ = "usage_tracking"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True)
    metric_type = Column(String(50), nullable=False, index=True)
    quantity = Column(Integer, default=0, nullable=False)
    period_month = Column(String(7), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# Default limits per plan
DEFAULT_PLAN_LIMITS = {
    "free": {
        "conversations_per_month": 100,
        "channels": 2,
        "products": 20,
        "agents": 1,
        "storage_mb": 500,
        "ai_tokens_monthly": 5000,
        "automations": 2,
        "email_sequences": 1,
        "shipments_per_month": 0,
        "appointments_per_month": 10,
        "team_members": 1,
        "api_calls_per_minute": 10,
        "custom_webhooks": 0,
        "custom_domains": 0,
        "multi_business": False,
        "advanced_integrations": False,
        "white_label": False,
        # Content Generation
        "content_generations_monthly": 15,
        "content_max_video_duration": 5,
        "content_max_image_resolution": "1024x1024",
        "content_daily_budget_usd": 1.0,
        "content_supports_4k": False,
        "content_supports_custom_models": False,
    },
    "starter": {
        "conversations_per_month": 2000,
        "channels": 5,
        "products": 100,
        "agents": 3,
        "storage_mb": 5120,
        "ai_tokens_monthly": 25000,
        "automations": 10,
        "email_sequences": 5,
        "shipments_per_month": 50,
        "appointments_per_month": 100,
        "team_members": 2,
        "api_calls_per_minute": 60,
        "custom_webhooks": 0,
        "custom_domains": 0,
        "multi_business": False,
        "advanced_integrations": False,
        "white_label": False,
        # Content Generation
        "content_generations_monthly": 100,
        "content_max_video_duration": 15,
        "content_max_image_resolution": "1792x1024",
        "content_daily_budget_usd": 5.0,
        "content_supports_4k": False,
        "content_supports_custom_models": False,
    },
    "pro": {
        "conversations_per_month": -1,
        "channels": 15,
        "products": 1000,
        "agents": 5,
        "storage_mb": 51200,
        "ai_tokens_monthly": 100000,
        "automations": 50,
        "email_sequences": 20,
        "shipments_per_month": 500,
        "appointments_per_month": 1000,
        "team_members": 5,
        "api_calls_per_minute": 300,
        "custom_webhooks": 5,
        "custom_domains": 1,
        "multi_business": True,
        "advanced_integrations": True,
        "white_label": False,
        # Content Generation
        "content_generations_monthly": 500,
        "content_max_video_duration": 30,
        "content_max_image_resolution": "2048x2048",
        "content_daily_budget_usd": 20.0,
        "content_supports_4k": True,
        "content_supports_custom_models": False,
    },
    "enterprise": {
        "conversations_per_month": -1,
        "channels": -1,
        "products": -1,
        "agents": -1,
        "storage_mb": -1,
        "ai_tokens_monthly": -1,
        "automations": -1,
        "email_sequences": -1,
        "shipments_per_month": -1,
        "appointments_per_month": -1,
        "team_members": -1,
        "api_calls_per_minute": 1000,
        "custom_webhooks": -1,
        "custom_domains": -1,
        "multi_business": True,
        "advanced_integrations": True,
        "white_label": True,
        # Content Generation
        "content_generations_monthly": -1,
        "content_max_video_duration": 60,
        "content_max_image_resolution": "4K",
        "content_daily_budget_usd": 100.0,
        "content_supports_4k": True,
        "content_supports_custom_models": True,
    },
}

DEFAULT_PLAN_FEATURES = {
    "free": [
        "basic_agent", "community_support",
        # Content tools (Free tier)
        "chatgpt", "canva", "capcut", "ideogram",
        "replicate_flux_schnell", "fal_flux_pro", "gpt_image_mini",
    ],
    "starter": [
        "basic_agent", "advanced_agents", "email_support", "own_api_key",
        # Content tools (Starter tier)
        "chatgpt", "canva", "capcut", "ideogram",
        "replicate_flux_schnell", "fal_flux_pro", "gpt_image_mini",
        "dalle3", "leonardo", "photoroom", "opusclip",
        "copyai", "jasper", "beautifulai",
    ],
    "pro": [
        "basic_agent", "advanced_agents", "custom_agents", "chat_support",
        "own_api_key", "multi_business", "advanced_integrations",
        # Content tools (Pro tier)
        "chatgpt", "canva", "capcut", "ideogram",
        "replicate_flux_schnell", "fal_flux_pro", "gpt_image_mini",
        "dalle3", "leonardo", "photoroom", "opusclip",
        "copyai", "jasper", "beautifulai",
        "midjourney", "runway", "heygen", "pika",
        "elevenlabs", "gamma",
    ],
    "enterprise": [
        "basic_agent", "advanced_agents", "custom_agents", "dedicated_support",
        "own_api_key", "multi_business", "advanced_integrations", "white_label", "custom_api",
        # Content tools (Enterprise tier)
        "chatgpt", "canva", "capcut", "ideogram",
        "replicate_flux_schnell", "fal_flux_pro", "gpt_image_mini",
        "dalle3", "leonardo", "photoroom", "opusclip",
        "copyai", "jasper", "beautifulai",
        "midjourney", "runway", "heygen", "pika",
        "elevenlabs", "gamma",
        "seedance", "kling", "sora", "sd35",
        "adcreative", "writesonic", "luma", "custom_api",
    ],
}


# =============================================================================
# NEW MODELS: PaymentTransaction, Invoice, UsageAlert
# =============================================================================

class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=True)

    amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(3), nullable=False)  # ARS | USD
    provider = Column(String(20), nullable=False)  # mercadopago | stripe | crypto | manual
    provider_transaction_id = Column(String(100), nullable=True, index=True)
    status = Column(String(20), default=PaymentStatus.PENDING.value, nullable=False)

    # Crypto-specific
    crypto_network = Column(String(20), nullable=True)  # trc20 | bep20
    crypto_from_address = Column(String(100), nullable=True)
    crypto_tx_hash = Column(String(100), nullable=True, index=True)
    crypto_confirmations = Column(Integer, default=0)

    # Billing
    billing_cycle = Column(String(10), nullable=True)  # monthly | yearly
    extra_data = Column(JSONB, default=dict, nullable=False)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("payment_transactions.id"), nullable=True, index=True)

    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    invoice_type = Column(String(10), default=InvoiceType.C.value, nullable=False)  # A | B | C | INTL

    amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    tax_amount = Column(Numeric(14, 2), default=0)
    total_amount = Column(Numeric(14, 2), nullable=False)

    plan_name = Column(String(100), nullable=True)
    billing_period_start = Column(DateTime(timezone=True), nullable=True)
    billing_period_end = Column(DateTime(timezone=True), nullable=True)

    status = Column(String(20), default=InvoiceStatus.PENDING.value, nullable=False)
    afip_cae = Column(String(20), nullable=True)
    afip_barcode = Column(Text, nullable=True)

    pdf_url = Column(Text, nullable=True)
    extra_data = Column(JSONB, default=dict, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    emitted_at = Column(DateTime(timezone=True), nullable=True)


class UsageAlert(Base):
    __tablename__ = "usage_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)
    threshold_percent = Column(Integer, nullable=False)  # 80, 100
    sent_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    acknowledged = Column(Boolean, default=False, nullable=False)


# =============================================================================
# Bank Transfer Payment (Cocos Capital / Manual transfers)
# =============================================================================

class BankTransferStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class BankTransferPayment(Base):
    __tablename__ = "bank_transfer_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=True)

    amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(3), nullable=False)  # ARS | USD

    # Order details
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    alias = Column(String(100), nullable=True)
    cbu = Column(String(50), nullable=True)
    account_holder = Column(String(255), nullable=True)
    instructions = Column(Text, nullable=True)

    # Status
    status = Column(String(20), default=BankTransferStatus.PENDING.value, nullable=False)
    proof_image_url = Column(Text, nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_by_admin_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_by_admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


# =============================================================================
# Cancellation Feedback
# =============================================================================

class CancellationFeedback(Base):
    __tablename__ = "cancellation_feedbacks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True)

    reason_category = Column(String(50), nullable=False)
    reason_text = Column(Text, nullable=True)
    competitor_name = Column(Text, nullable=True)
    improvement_suggestion = Column(Text, nullable=True)
    rating_nps = Column(Integer, nullable=True)  # 0-10

    cancelled_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
