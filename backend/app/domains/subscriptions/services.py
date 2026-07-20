from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Any

from app.domains.subscriptions.models import (
    Subscription, SubscriptionPlan, SubscriptionStatus, UsageTracking, Invoice,
    DEFAULT_PLAN_LIMITS, DEFAULT_PLAN_FEATURES
)


async def get_or_create_subscription(db: AsyncSession, user_id: Any, plan_slug: str = "free") -> Subscription:
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    sub = result.scalar_one_or_none()
    if sub:
        return sub

    # Create new subscription with free plan
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.slug == plan_slug)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        plan = await create_default_plans(db)
        result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.slug == plan_slug)
        )
        plan = result.scalar_one()

    sub = Subscription(
        user_id=user_id,
        plan_id=plan.id,
        status=SubscriptionStatus.ACTIVE,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


async def create_default_plans(db: AsyncSession) -> SubscriptionPlan:
    plans_data = [
        {
            "name": "Free",
            "slug": "free",
            "description": "Para probar SellIA",
            "price_monthly_ars": 0,
            "price_yearly_ars": 0,
            "price_monthly_usd": 0,
            "price_yearly_usd": 0,
            "price_monthly_latam_usd": 0,
            "price_yearly_latam_usd": 0,
            "limits": DEFAULT_PLAN_LIMITS["free"],
            "features": DEFAULT_PLAN_FEATURES["free"],
            "display_order": 0,
            "billing_cycle_options": ["monthly"],
            "target_regions": ["AR", "LATAM", "INTL"],
            "trial_days": 0,
        },
        {
            "name": "Starter",
            "slug": "starter",
            "description": "Para emprendedores",
            "price_monthly_ars": 4500,
            "price_yearly_ars": 45000,
            "price_monthly_usd": 15,
            "price_yearly_usd": 150,
            "price_monthly_latam_usd": 12,
            "price_yearly_latam_usd": 120,
            "limits": DEFAULT_PLAN_LIMITS["starter"],
            "features": DEFAULT_PLAN_FEATURES["starter"],
            "display_order": 1,
            "billing_cycle_options": ["monthly", "yearly"],
            "target_regions": ["AR", "LATAM", "INTL"],
            "trial_days": 14,
        },
        {
            "name": "Pro",
            "slug": "pro",
            "description": "Para negocios en crecimiento",
            "price_monthly_ars": 14900,
            "price_yearly_ars": 149000,
            "price_monthly_usd": 49,
            "price_yearly_usd": 490,
            "price_monthly_latam_usd": 39,
            "price_yearly_latam_usd": 390,
            "limits": DEFAULT_PLAN_LIMITS["pro"],
            "features": DEFAULT_PLAN_FEATURES["pro"],
            "display_order": 2,
            "billing_cycle_options": ["monthly", "yearly"],
            "target_regions": ["AR", "LATAM", "INTL"],
            "trial_days": 14,
        },
        {
            "name": "Enterprise",
            "slug": "enterprise",
            "description": "Para equipos y agencias",
            "price_monthly_ars": 59900,
            "price_yearly_ars": 599000,
            "price_monthly_usd": 199,
            "price_yearly_usd": 1990,
            "price_monthly_latam_usd": 159,
            "price_yearly_latam_usd": 1590,
            "limits": DEFAULT_PLAN_LIMITS["enterprise"],
            "features": DEFAULT_PLAN_FEATURES["enterprise"],
            "display_order": 3,
            "billing_cycle_options": ["monthly", "yearly"],
            "target_regions": ["AR", "LATAM", "INTL"],
            "trial_days": 14,
        },
    ]

    for plan_data in plans_data:
        plan = SubscriptionPlan(**plan_data)
        db.add(plan)
    await db.commit()

    result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.slug == "free"))
    return result.scalar_one()


async def check_subscription_limit(
    db: AsyncSession,
    user_id: Any,
    metric_type: str,
    quantity: int = 1,
) -> dict[str, Any]:
    result = await db.execute(
        select(Subscription, SubscriptionPlan)
        .join(SubscriptionPlan)
        .where(Subscription.user_id == user_id)
    )
    row = result.first()
    if not row:
        return {"metric": metric_type, "used": 0, "limit": 0, "remaining": 0, "has_limit": True, "allowed": False}

    sub, plan = row
    limits = plan.limits or {}
    limit = limits.get(metric_type, 0)

    # Unlimited (-1 means no limit)
    if limit == -1:
        return {"metric": metric_type, "used": 0, "limit": -1, "remaining": -1, "has_limit": False, "allowed": True}

    # Superusers bypass all limits
    from app.domains.users.models import User
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user and user.is_superuser:
        return {"metric": metric_type, "used": 0, "limit": -1, "remaining": -1, "has_limit": False, "allowed": True}

    # Get current usage for this month
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    result = await db.execute(
        select(func.coalesce(func.sum(UsageTracking.quantity), 0))
        .where(
            UsageTracking.user_id == user_id,
            UsageTracking.metric_type == metric_type,
            UsageTracking.period_month == current_month,
        )
    )
    used = result.scalar() or 0
    remaining = max(0, limit - used)
    allowed = remaining >= quantity

    return {
        "metric": metric_type,
        "used": used,
        "limit": limit,
        "remaining": remaining,
        "has_limit": True,
        "allowed": allowed,
    }


async def track_usage(
    db: AsyncSession,
    user_id: Any,
    metric_type: str,
    quantity: int = 1,
    business_id: Any = None,
) -> None:
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    tracking = UsageTracking(
        user_id=user_id,
        business_id=business_id,
        metric_type=metric_type,
        quantity=quantity,
        period_month=current_month,
    )
    db.add(tracking)
    await db.commit()


# =============================================================================
# Region-based pricing helpers
# =============================================================================

REGION_MAP = {
    "AR": "AR",
    "CL": "LATAM", "UY": "LATAM", "PY": "LATAM", "BO": "LATAM",
    "PE": "LATAM", "EC": "LATAM", "CO": "LATAM", "VE": "LATAM",
    "BR": "LATAM", "MX": "LATAM", "GT": "LATAM", "SV": "LATAM",
    "HN": "LATAM", "NI": "LATAM", "CR": "LATAM", "PA": "LATAM",
    "DO": "LATAM", "CU": "LATAM", "PR": "LATAM",
}


def get_region_from_country(country_code: str | None) -> str:
    """Map country code to pricing region."""
    if not country_code:
        return "INTL"
    return REGION_MAP.get(country_code.upper(), "INTL")


def get_plan_price(plan: SubscriptionPlan, region: str, billing_cycle: str) -> tuple[float, str]:
    """Get price and currency for a plan based on region and billing cycle.
    
    Returns:
        tuple of (price, currency)
    """
    if billing_cycle not in ("monthly", "yearly"):
        billing_cycle = "monthly"
    
    if region == "AR":
        price = plan.price_monthly_ars if billing_cycle == "monthly" else plan.price_yearly_ars
        return float(price or 0), "ARS"
    elif region == "LATAM":
        price = plan.price_monthly_latam_usd if billing_cycle == "monthly" else plan.price_yearly_latam_usd
        return float(price or 0), "USD"
    else:
        price = plan.price_monthly_usd if billing_cycle == "monthly" else plan.price_yearly_usd
        return float(price or 0), "USD"


# =============================================================================
# Invoice helpers
# =============================================================================

async def generate_invoice_number(db: AsyncSession) -> str:
    """Generate a unique invoice number (SELL-YYYY-XXXXX format)."""
    from sqlalchemy import func
    current_year = datetime.now(timezone.utc).year
    prefix = f"SELL-{current_year}"
    
    result = await db.execute(
        select(func.count(Invoice.id)).where(Invoice.invoice_number.like(f"{prefix}-%"))
    )
    count = result.scalar() or 0
    return f"{prefix}-{count + 1:05d}"


async def create_invoice(
    db: AsyncSession,
    user_id: Any,
    transaction_id: Any | None,
    plan: SubscriptionPlan,
    amount: float,
    currency: str,
    billing_cycle: str,
    region: str,
) -> Invoice:
    """Create an invoice for a payment."""
    invoice_number = await generate_invoice_number(db)
    
    # Determine invoice type based on region and user tax status
    invoice_type = "INTL"
    if region == "AR":
        # Will be determined by AFIP integration (A, B, or C)
        invoice_type = "C"  # Default to consumidor final
    
    period_days = 30 if billing_cycle == "monthly" else 365
    period_start = datetime.now(timezone.utc)
    period_end = period_start + timedelta(days=period_days)
    
    invoice = Invoice(
        user_id=user_id,
        transaction_id=transaction_id,
        invoice_number=invoice_number,
        invoice_type=invoice_type,
        amount=amount,
        currency=currency,
        tax_amount=0,  # Will be calculated by AFIP for AR
        total_amount=amount,
        plan_name=plan.name,
        billing_period_start=period_start,
        billing_period_end=period_end,
    )
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    return invoice


# =============================================================================
# Bank Transfer Order Helpers
# =============================================================================

async def generate_bank_transfer_order(
    db: AsyncSession,
    user,
    subscription,
    plan,
    amount: float,
    currency: str,
    billing_cycle: str,
) -> "BankTransferPayment":
    """Generate a professional bank transfer payment order."""
    from app.domains.subscriptions.models import BankTransferPayment, BankTransferStatus
    from app.core.config import get_settings
    from sqlalchemy import func

    settings = get_settings()

    # Generate order number
    now = datetime.now(timezone.utc)
    prefix = f"SELL-{now.year}{now.month:02d}"
    result = await db.execute(
        select(func.count(BankTransferPayment.id)).where(
            BankTransferPayment.order_number.like(f"{prefix}-%")
        )
    )
    count = result.scalar() or 0
    order_number = f"{prefix}-{count + 1:05d}"

    # Build instructions
    alias = settings.CREATOR_COCO_ALIAS or settings.CREATOR_MP_ALIAS
    cbu = settings.CREATOR_CBU
    holder = settings.CREATOR_FULL_NAME or "SellIA"

    instructions = (
        f"Orden de pago #{order_number}\n\n"
        f"Monto: {amount} {currency}\n"
        f"Plan: {plan.name} ({billing_cycle})\n\n"
        f"Realizá la transferencia a:\n"
        f"Titular: {holder}\n"
    )
    if alias:
        instructions += f"Alias: {alias}\n"
    if cbu:
        instructions += f"CBU: {cbu}\n"
    instructions += (
        f"\nUna vez realizada, volvé a esta pantalla y confirmá el pago. "
        f"Tenés 48 horas para completarlo."
    )

    order = BankTransferPayment(
        user_id=user.id,
        subscription_id=subscription.id,
        plan_id=plan.id,
        amount=amount,
        currency=currency,
        order_number=order_number,
        alias=alias,
        cbu=cbu,
        account_holder=holder,
        instructions=instructions,
        status=BankTransferStatus.PENDING.value,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    # Send confirmation email
    if getattr(user, "email", None):
        from app.core.email_service import send_email
        from app.domains.subscriptions.email_templates import transfer_order_created
        subject, html, text = transfer_order_created(
            order_number=order.order_number,
            plan_name=plan.name,
            amount=float(order.amount),
            currency=order.currency,
            alias=order.alias or "",
            cbu=order.cbu,
            holder=order.account_holder or "SellIA",
            expires_at=order.expires_at.strftime("%d/%m/%Y %H:%M") if order.expires_at else "",
        )
        await send_email(user.email, subject, html, text)

    return order
