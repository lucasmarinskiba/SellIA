from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Any
import enum

from app.domains.subscriptions.models import SubscriptionStatus


class SubscriptionPlanBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=50)
    description: str | None = None


class SubscriptionPlanCreate(SubscriptionPlanBase):
    price_monthly_ars: float | None = None
    price_yearly_ars: float | None = None
    price_monthly_usd: float | None = None
    price_yearly_usd: float | None = None
    price_monthly_latam_usd: float | None = None
    price_yearly_latam_usd: float | None = None
    limits: dict[str, Any] | None = None
    features: list[str] | None = None
    display_order: int = 0
    billing_cycle_options: list[str] = ["monthly", "yearly"]
    target_regions: list[str] = ["AR", "LATAM", "INTL"]
    trial_days: int = 14


class SubscriptionPlanResponse(SubscriptionPlanBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    price_monthly_ars: float | None
    price_yearly_ars: float | None
    price_monthly_usd: float | None
    price_yearly_usd: float | None
    price_monthly_latam_usd: float | None
    price_yearly_latam_usd: float | None
    limits: dict[str, Any]
    features: list[str]
    is_active: bool
    display_order: int
    billing_cycle_options: list[str]
    target_regions: list[str]
    trial_days: int
    created_at: datetime
    updated_at: datetime


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    plan_id: UUID
    status: SubscriptionStatus
    current_period_start: datetime | None
    current_period_end: datetime | None
    cancel_at_period_end: bool
    billing_cycle: str = "monthly"
    payment_provider: str | None = None
    next_billing_date: datetime | None = None
    auto_renew: bool = True
    trial_ends_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SubscriptionWithPlanResponse(SubscriptionResponse):
    plan: SubscriptionPlanResponse


class UserAPIKeyBase(BaseModel):
    provider: str


class UserAPIKeyCreate(UserAPIKeyBase):
    api_key: str


class UserAPIKeyResponse(UserAPIKeyBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    is_active: bool
    last_used_at: datetime | None
    created_at: datetime
    updated_at: datetime


class UsageTrackingCreate(BaseModel):
    metric_type: str
    quantity: int = 1
    business_id: UUID | None = None


class UsageTrackingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    business_id: UUID | None
    metric_type: str
    quantity: int
    period_month: str
    created_at: datetime


class CheckLimitResponse(BaseModel):
    metric: str
    used: int
    limit: int
    remaining: int
    has_limit: bool
    allowed: bool


# =============================================================================
# PaymentTransaction Schemas
# =============================================================================

class PaymentTransactionBase(BaseModel):
    amount: float
    currency: str
    provider: str
    provider_transaction_id: str | None = None
    status: str = "pending"
    billing_cycle: str | None = None


class PaymentTransactionCreate(PaymentTransactionBase):
    subscription_id: UUID | None = None
    plan_id: UUID | None = None
    crypto_network: str | None = None
    metadata: dict[str, Any] | None = None


class PaymentTransactionResponse(PaymentTransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    subscription_id: UUID | None = None
    plan_id: UUID | None = None
    crypto_network: str | None = None
    crypto_from_address: str | None = None
    crypto_tx_hash: str | None = None
    crypto_confirmations: int = 0
    metadata: dict[str, Any]
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


# =============================================================================
# Invoice Schemas
# =============================================================================

class InvoiceBase(BaseModel):
    invoice_number: str
    invoice_type: str = "C"
    amount: float
    currency: str
    tax_amount: float = 0
    total_amount: float
    plan_name: str | None = None
    billing_period_start: datetime | None = None
    billing_period_end: datetime | None = None


class InvoiceResponse(InvoiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    transaction_id: UUID | None = None
    status: str
    afip_cae: str | None = None
    afip_barcode: str | None = None
    pdf_url: str | None = None
    metadata: dict[str, Any]
    created_at: datetime
    emitted_at: datetime | None = None


# =============================================================================
# Checkout Schemas
# =============================================================================

class CheckoutRequest(BaseModel):
    plan_slug: str
    billing_cycle: str = "monthly"  # monthly | yearly
    payment_provider: str  # mercadopago | stripe | crypto
    crypto_network: str | None = None  # trc20 | bep20


class CheckoutResponse(BaseModel):
    preference_id: str | None = None
    init_point: str | None = None
    sandbox_init_point: str | None = None
    client_secret: str | None = None
    public_key: str | None = None
    session_id: str | None = None


class CryptoPaymentRequest(BaseModel):
    plan_slug: str
    billing_cycle: str = "monthly"
    crypto_network: str  # trc20 | bep20


class CryptoPaymentResponse(BaseModel):
    transaction_id: UUID
    wallet_address: str
    amount_usdt: float
    network: str
    qr_code_url: str | None = None
    expires_at: datetime
    status: str = "pending"


class CryptoPaymentStatusResponse(BaseModel):
    transaction_id: UUID
    status: str
    confirmations: int = 0
    tx_hash: str | None = None
    completed_at: datetime | None = None
    amount_received: float | None = None


# =============================================================================
# Region Detection Schemas
# =============================================================================

class RegionDetectResponse(BaseModel):
    detected_country: str | None = None
    detected_region: str  # AR | LATAM | INTL
    suggested_currency: str  # ARS | USD


class UserRegionUpdate(BaseModel):
    country_code: str
    preferred_currency: str
    timezone: str | None = None


# =============================================================================
# Billing Details Schemas
# =============================================================================

class BillingDetailsUpdate(BaseModel):
    tax_id: str | None = None
    billing_address: dict[str, Any] | None = None
    full_name: str | None = None


class BillingDetailsResponse(BaseModel):
    tax_id: str | None = None
    billing_address: dict[str, Any]
    full_name: str | None = None
    country_code: str
    preferred_currency: str


# =============================================================================
# Usage Alert Schemas
# =============================================================================

class UsageAlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    metric_type: str
    threshold_percent: int
    sent_at: datetime
    acknowledged: bool


# =============================================================================
# Bank Transfer Payment Schemas
# =============================================================================

class BankTransferOrderCreate(BaseModel):
    plan_slug: str
    billing_cycle: str = "monthly"
    currency: str = "ARS"


class BankTransferOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    order_number: str
    amount: float
    currency: str
    alias: str | None = None
    cbu: str | None = None
    account_holder: str | None = None
    instructions: str | None = None
    status: str
    expires_at: datetime
    created_at: datetime


class BankTransferConfirmRequest(BaseModel):
    proof_image_url: str | None = None


class BankTransferConfirmResponse(BaseModel):
    status: str
    message: str


class BankTransferAdminApproveRequest(BaseModel):
    approved: bool = True
    notes: str | None = None


# =============================================================================
# Cancellation Feedback Schemas
# =============================================================================

class CancellationReason(str, enum.Enum):
    PRICE = "price"
    COMPETITOR = "competitor"
    NO_USAGE = "no_usage"
    BUGS = "bugs"
    MISSING_FEATURE = "missing_feature"
    SUPPORT = "support"
    TRIAL = "trial"
    OTHER = "other"


class CancellationRequest(BaseModel):
    reason_category: CancellationReason
    reason_text: str | None = None
    competitor_name: str | None = None
    improvement_suggestion: str | None = None
    rating_nps: int | None = Field(None, ge=0, le=10)


class CancellationFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    reason_category: str
    reason_text: str | None = None
    competitor_name: str | None = None
    improvement_suggestion: str | None = None
    rating_nps: int | None = None
    cancelled_at: datetime


# =============================================================================
# Retention Dashboard Schemas
# =============================================================================

class RetentionSummary(BaseModel):
    total_cancellations: int
    cancellations_this_month: int
    churn_rate_percent: float
    avg_nps: float | None = None
    top_reasons: list[dict[str, Any]]
    top_competitors: list[dict[str, Any]]


# =============================================================================
# MercadoPago Preapproval Schemas
# =============================================================================

class PreapprovalCreateRequest(BaseModel):
    plan_slug: str
    billing_cycle: str = "monthly"  # monthly | yearly


class PreapprovalResponse(BaseModel):
    preapproval_id: str | None = None
    init_point: str | None = None
    sandbox_init_point: str | None = None
    status: str = "pending"


class PreapprovalStatusResponse(BaseModel):
    preapproval_id: str
    status: str  # authorized | paused | cancelled
    plan_slug: str
    billing_cycle: str
    next_payment_date: datetime | None = None



# =============================================================================
# Admin Dashboard Schemas
# =============================================================================

class RevenueSummary(BaseModel):
    mrr: float
    arr: float
    revenue_this_month: float
    revenue_by_provider: dict[str, float]
    pending_transfers_count: int
    active_subscriptions_count: int


class AdminSubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    user_email: str | None = None
    user_full_name: str | None = None
    plan_id: UUID
    plan_name: str
    plan_slug: str
    status: str
    billing_cycle: str
    payment_provider: str | None = None
    next_billing_date: datetime | None = None
    current_period_end: datetime | None = None
    auto_renew: bool
    created_at: datetime


class AdminBankTransferFilter(BaseModel):
    status: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    page: int = 1
    limit: int = 50
