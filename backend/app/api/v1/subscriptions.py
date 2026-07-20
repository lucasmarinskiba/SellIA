import os
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Any
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.subscriptions.models import (
    SubscriptionPlan, Subscription, UserAPIKey, SubscriptionStatus,
    PaymentTransaction, Invoice, PaymentStatus, PaymentProvider,
)
from app.domains.subscriptions.schemas import (
    SubscriptionPlanResponse, SubscriptionWithPlanResponse,
    UserAPIKeyCreate, UserAPIKeyResponse, CheckLimitResponse,
    CheckoutRequest, CheckoutResponse,
    CryptoPaymentRequest, CryptoPaymentResponse, CryptoPaymentStatusResponse,
    RegionDetectResponse, UserRegionUpdate,
    BillingDetailsUpdate, BillingDetailsResponse,
    PaymentTransactionResponse, InvoiceResponse,
    BankTransferOrderCreate, BankTransferOrderResponse,
    BankTransferConfirmRequest, BankTransferConfirmResponse,
    BankTransferAdminApproveRequest,
    CancellationRequest, CancellationFeedbackResponse,
    PreapprovalCreateRequest, PreapprovalResponse, PreapprovalStatusResponse,
    RetentionSummary, RevenueSummary, AdminSubscriptionResponse, AdminBankTransferFilter,
)
from app.domains.subscriptions.services import (
    get_or_create_subscription, check_subscription_limit, create_default_plans, track_usage,
    get_region_from_country, get_plan_price, generate_invoice_number, create_invoice,
    REGION_MAP,
)
from app.domains.subscriptions.billing import (
    create_checkout_preference, create_preapproval, get_preapproval_status,
    cancel_preapproval, process_preapproval_webhook, process_mercadopago_webhook,
)
from app.domains.subscriptions.stripe_billing import (
    construct_webhook_event, process_stripe_webhook,
)
from app.domains.security.models import WebhookEventLog
from app.domains.subscriptions.models import (
    PaymentTransaction, Invoice, PaymentStatus, PaymentProvider,
    BankTransferPayment, BankTransferStatus, CancellationFeedback,
)
from app.domains.subscriptions.crypto_billing import (
    generate_crypto_payment, check_crypto_payment_status, verify_crypto_payment, get_usdt_contract_address
)
from app.core.security import get_password_hash
from app.core.encryption import encrypt_value

router = APIRouter()


@router.get("/plans", response_model=list[SubscriptionPlanResponse])
async def list_plans(
    region: str = Query(None, description="AR | LATAM | INTL"),
    cycle: str = Query("monthly", description="monthly | yearly"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.is_active == True).order_by(SubscriptionPlan.display_order)
    )
    plans = result.scalars().all()

    if region:
        region_upper = region.upper()
        plans = [p for p in plans if region_upper in (p.target_regions or [])]

    if cycle:
        plans = [p for p in plans if cycle in (p.billing_cycle_options or [])]

    return plans


@router.get("/my-subscription", response_model=SubscriptionWithPlanResponse)
async def get_my_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = await get_or_create_subscription(db, current_user.id)
    # Eager load plan
    result = await db.execute(
        select(Subscription, SubscriptionPlan)
        .join(SubscriptionPlan)
        .where(Subscription.id == sub.id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")
    sub_obj, plan = row
    return SubscriptionWithPlanResponse(
        **{c.name: getattr(sub_obj, c.name) for c in sub_obj.__table__.columns},
        plan=SubscriptionPlanResponse.model_validate(plan),
    )


@router.get("/my-usage")
async def get_my_usage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current usage for all limited metrics."""
    from app.domains.subscriptions.models import UsageTracking
    from sqlalchemy import func
    from datetime import datetime, timezone

    current_month = datetime.now(timezone.utc).strftime("%Y-%m")

    # Get user's subscription plan
    sub = await get_or_create_subscription(db, current_user.id)
    plan = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == sub.plan_id))
    plan = plan.scalar_one_or_none()
    limits = plan.limits or {} if plan else {}

    # Aggregate usage per metric
    result = await db.execute(
        select(UsageTracking.metric_type, func.coalesce(func.sum(UsageTracking.quantity), 0))
        .where(
            UsageTracking.user_id == current_user.id,
            UsageTracking.period_month == current_month,
        )
        .group_by(UsageTracking.metric_type)
    )
    usage_map = {row[0]: row[1] for row in result.all()}

    metrics = ["conversations_per_month", "channels", "products", "agents", "storage_mb", "ai_tokens_monthly"]
    usage_report = []
    for metric in metrics:
        limit = limits.get(metric, 0)
        used = usage_map.get(metric, 0)
        usage_report.append({
            "metric": metric,
            "used": used,
            "limit": limit,
            "unlimited": limit == -1,
            "remaining": "unlimited" if limit == -1 else max(0, limit - used),
        })

    return {"period_month": current_month, "plan_slug": plan.slug if plan else "free", "usage": usage_report}


@router.get("/check-limit/{metric_type}", response_model=CheckLimitResponse)
async def check_limit(
    metric_type: str,
    quantity: int = 1,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await check_subscription_limit(db, current_user.id, metric_type, quantity)
    return CheckLimitResponse(**result)


# ========== Checkout ==========

@router.post("/create-checkout", response_model=CheckoutResponse)
async def create_checkout(
    data: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a checkout session for upgrading to a plan."""
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.slug == data.plan_slug, SubscriptionPlan.is_active == True)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    sub = await get_or_create_subscription(db, current_user.id)
    user_region = get_region_from_country(current_user.country_code)
    price, currency = get_plan_price(plan, user_region, data.billing_cycle)

    if data.payment_provider == PaymentProvider.MERCADOPAGO.value:
        if currency != "ARS":
            raise HTTPException(status_code=400, detail="MercadoPago solo disponible para pagos en ARS")

        try:
            preference = await create_checkout_preference(
                plan_name=plan.name,
                plan_slug=plan.slug,
                price_ars=price,
                user_id=str(current_user.id),
                subscription_id=str(sub.id),
            )
            sub.mercadopago_preference_id = preference.get("id")
            sub.billing_cycle = data.billing_cycle
            await db.commit()

            return CheckoutResponse(
                preference_id=preference.get("id"),
                init_point=preference.get("init_point"),
                sandbox_init_point=preference.get("sandbox_init_point"),
            )
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).exception("Error creating checkout")
            raise HTTPException(status_code=500, detail="Internal server error")

    elif data.payment_provider == "bank_transfer":
        # Create a bank transfer order (Cocos Capital / manual transfer)
        from app.domains.subscriptions.services import generate_bank_transfer_order
        try:
            order = await generate_bank_transfer_order(
                db=db,
                user=current_user,
                subscription=sub,
                plan=plan,
                amount=price,
                currency=currency,
                billing_cycle=data.billing_cycle,
            )
            sub.billing_cycle = data.billing_cycle
            sub.payment_provider = "bank_transfer"
            await db.commit()

            return CheckoutResponse(
                preference_id=str(order.id),
                init_point=f"/dashboard/transferencia/{order.id}",  # Frontend route
            )
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).exception("Error creating bank transfer order")
            raise HTTPException(status_code=500, detail="Internal server error")

    elif data.payment_provider == PaymentProvider.CRYPTO.value:
        raise HTTPException(status_code=400, detail="Crypto usa el endpoint /create-crypto-payment")

    else:
        raise HTTPException(status_code=400, detail="Proveedor de pago no soportado")


# ========== MercadoPago Preapproval ==========

@router.post("/preapproval", response_model=PreapprovalResponse)
async def create_preapproval_subscription(
    data: PreapprovalCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a MercadoPago preapproval for automatic recurring billing (ARS only)."""
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.slug == data.plan_slug, SubscriptionPlan.is_active == True)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    sub = await get_or_create_subscription(db, current_user.id)
    user_region = get_region_from_country(current_user.country_code)
    price, currency = get_plan_price(plan, user_region, data.billing_cycle)

    if currency != "ARS":
        raise HTTPException(status_code=400, detail="Preapproval solo disponible para pagos en ARS")

    if not current_user.email:
        raise HTTPException(status_code=400, detail="El usuario no tiene email configurado")

    try:
        preapproval = await create_preapproval(
            plan_name=plan.name,
            plan_slug=plan.slug,
            price_ars=price,
            user_id=str(current_user.id),
            subscription_id=str(sub.id),
            user_email=current_user.email,
            billing_cycle=data.billing_cycle,
        )
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).exception("Error creating preapproval")
        raise HTTPException(status_code=500, detail="Internal server error")

    sub.mercadopago_preapproval_id = preapproval.get("preapproval_id")
    sub.billing_cycle = data.billing_cycle
    sub.payment_provider = "mercadopago"
    sub.auto_renew = True
    await db.commit()

    return PreapprovalResponse(
        preapproval_id=preapproval.get("preapproval_id"),
        init_point=preapproval.get("init_point"),
        sandbox_init_point=preapproval.get("sandbox_init_point"),
        status=preapproval.get("status", "pending"),
    )


@router.get("/preapproval/{preapproval_id}/status", response_model=PreapprovalStatusResponse)
async def get_preapproval(
    preapproval_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get MercadoPago preapproval status."""
    try:
        status = await get_preapproval_status(preapproval_id)
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).exception("Error querying MercadoPago")
        raise HTTPException(status_code=500, detail="Internal server error")

    external_ref = status.get("external_reference", "")
    plan_slug = ""
    billing_cycle = "monthly"
    if ":" in external_ref:
        parts = external_ref.split(":")
        if len(parts) >= 3:
            plan_slug = parts[2]
        if len(parts) >= 4:
            billing_cycle = parts[3]

    return PreapprovalStatusResponse(
        preapproval_id=preapproval_id,
        status=status.get("status", "unknown"),
        plan_slug=plan_slug,
        billing_cycle=billing_cycle,
        next_payment_date=status.get("next_payment_date"),
    )


@router.delete("/preapproval/{preapproval_id}")
async def delete_preapproval(
    preapproval_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a MercadoPago preapproval."""
    sub_result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.mercadopago_preapproval_id == preapproval_id,
        )
    )
    sub = sub_result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Preapproval no encontrado")

    try:
        await cancel_preapproval(preapproval_id)
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).exception("Error cancelling preapproval")
        raise HTTPException(status_code=500, detail="Internal server error")

    sub.auto_renew = False
    sub.mercadopago_preapproval_id = None
    await db.commit()

    return {"status": "cancelled"}


# ========== Crypto Payments ==========

@router.post("/create-crypto-payment", response_model=CryptoPaymentResponse)
async def create_crypto_payment(
    data: CryptoPaymentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.slug == data.plan_slug, SubscriptionPlan.is_active == True)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    sub = await get_or_create_subscription(db, current_user.id)
    user_region = get_region_from_country(current_user.country_code)
    price, currency = get_plan_price(plan, user_region, data.billing_cycle)

    if currency != "USD":
        raise HTTPException(status_code=400, detail="Crypto solo disponible para pagos en USD")

    try:
        crypto = generate_crypto_payment(
            plan_slug=plan.slug,
            price_usd=price,
            user_id=str(current_user.id),
            subscription_id=str(sub.id),
            network=data.crypto_network,
        )
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).exception("Error generating crypto payment")
        raise HTTPException(status_code=500, detail="Internal server error")

    tx = PaymentTransaction(
        id=UUID(crypto["transaction_id"]),
        user_id=current_user.id,
        subscription_id=sub.id,
        plan_id=plan.id,
        amount=price,
        currency="USD",
        provider=PaymentProvider.CRYPTO.value,
        status=PaymentStatus.PENDING.value,
        billing_cycle=data.billing_cycle,
        crypto_network=crypto["network"],
        crypto_from_address=crypto["wallet_address"],
        metadata={
            "plan_slug": plan.slug,
            "wallet_address": crypto["wallet_address"],
            "amount_usdt": crypto["amount_usdt"],
            "expires_at": crypto["expires_at"].isoformat(),
        },
    )
    db.add(tx)
    await db.commit()

    return CryptoPaymentResponse(
        transaction_id=tx.id,
        wallet_address=crypto["wallet_address"],
        amount_usdt=crypto["amount_usdt"],
        network=crypto["network"],
        expires_at=crypto["expires_at"],
        status="pending",
    )


@router.get("/crypto-payment/{transaction_id}/status", response_model=CryptoPaymentStatusResponse)
async def get_crypto_payment_status(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PaymentTransaction).where(
            PaymentTransaction.id == transaction_id,
            PaymentTransaction.user_id == current_user.id,
        )
    )
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")

    # If we have an on-chain tx hash, query the network for fresh status
    if tx.crypto_tx_hash and tx.crypto_network:
        try:
            onchain = await check_crypto_payment_status(tx.crypto_tx_hash, tx.crypto_network)
            return CryptoPaymentStatusResponse(
                transaction_id=tx.id,
                status=onchain.get("status", tx.status),
                confirmations=onchain.get("confirmations", tx.crypto_confirmations),
                tx_hash=tx.crypto_tx_hash,
                completed_at=tx.completed_at,
                amount_received=onchain.get("amount"),
            )
        except Exception:
            pass

    return CryptoPaymentStatusResponse(
        transaction_id=tx.id,
        status=tx.status,
        confirmations=tx.crypto_confirmations,
        tx_hash=tx.crypto_tx_hash,
        completed_at=tx.completed_at,
        amount_received=None,
    )


# ========== Webhooks ==========

def _verify_mercadopago_signature(request: Request, body: dict) -> bool:
    """Verify MercadoPago webhook signature (X-Signature header).

    Format: X-Signature: ts=timestamp,v1=signature
    The signature is HMAC-SHA256 of 'id:<data.id>;type:<type>' using the webhook secret.
    If no signature header is present, we fall back to API callback validation.
    """
    import hashlib
    import hmac
    x_signature = request.headers.get("X-Signature", "")
    if not x_signature:
        return True  # Legacy IPN may not have signature; rely on API callback
    secret = settings.MERCADOPAGO_ACCESS_TOKEN or os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")
    if not secret:
        return False
    data_id = body.get("data", {}).get("id") if body.get("data") else body.get("id")
    topic = body.get("topic") or body.get("type")
    if not data_id or not topic:
        return False
    template = f"id:{data_id};topic:{topic}"
    expected = hmac.new(secret.encode(), template.encode(), hashlib.sha256).hexdigest()
    parts = x_signature.split(",")
    sig_map = {}
    for part in parts:
        if "=" in part:
            k, v = part.split("=", 1)
            sig_map[k.strip()] = v.strip()
    received = sig_map.get("v1", "")
    return hmac.compare_digest(received, expected)


@router.post("/webhook/mercadopago")
async def mercadopago_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive MercadoPago IPN/webhook notifications."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    topic = body.get("topic") or body.get("type")
    data_id = body.get("data", {}).get("id") if body.get("data") else body.get("id")

    if not topic or not data_id:
        topic = request.query_params.get("topic") or request.query_params.get("type")
        data_id = request.query_params.get("id") or request.query_params.get("data.id")

    if not topic or not data_id:
        raise HTTPException(status_code=400, detail="Missing topic or data_id")

    event_id = f"{topic}:{data_id}"

    # Deduplication
    existing = await db.execute(
        select(WebhookEventLog).where(
            WebhookEventLog.provider == "mercadopago",
            WebhookEventLog.event_id == event_id,
        )
    )
    if existing.scalar_one_or_none():
        return {"status": "already_processed"}

    # Verify signature
    if not _verify_mercadopago_signature(request, body):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        # === Preapproval webhook ===
        if topic in ("preapproval", "subscription_preapproval"):
            preapproval_info = await process_preapproval_webhook(data_id)
            user_id_str = preapproval_info.get("user_id")
            plan_slug = preapproval_info.get("plan_slug")
            billing_cycle = preapproval_info.get("billing_cycle", "monthly")
            preapproval_status = preapproval_info.get("status")

            if user_id_str and plan_slug:
                user_id = UUID(user_id_str)

                result = await db.execute(
                    select(Subscription).where(Subscription.user_id == user_id).with_for_update()
                )
                sub = result.scalar_one_or_none()
                if sub:
                    sub.mercadopago_preapproval_id = preapproval_info.get("preapproval_id")

                    if preapproval_status == "authorized":
                        plan_result = await db.execute(
                            select(SubscriptionPlan).where(SubscriptionPlan.slug == plan_slug)
                        )
                        new_plan = plan_result.scalar_one_or_none()
                        if new_plan:
                            sub.plan_id = new_plan.id
                            sub.status = SubscriptionStatus.ACTIVE
                            sub.billing_cycle = billing_cycle
                            sub.payment_provider = "mercadopago"
                            sub.auto_renew = True
                            sub.current_period_start = datetime.now(timezone.utc)
                            sub.current_period_end = datetime.now(timezone.utc) + timedelta(days=30 if billing_cycle == "monthly" else 365)
                            sub.next_billing_date = preapproval_info.get("next_payment_date")

                            user_result = await db.execute(select(User).where(User.id == user_id))
                            user_obj = user_result.scalar_one_or_none()
                            if user_obj and user_obj.email:
                                from app.core.email_service import send_email
                                from app.domains.subscriptions.email_templates import preapproval_activated
                                price, currency = get_plan_price(new_plan, get_region_from_country(user_obj.country_code), billing_cycle)
                                subject, html, text = preapproval_activated(
                                    plan_name=new_plan.name,
                                    amount=price,
                                    currency=currency,
                                    next_payment=sub.current_period_end.strftime("%d/%m/%Y") if sub.current_period_end else "",
                                )
                                await send_email(user_obj.email, subject, html, text)

                    elif preapproval_status in ("paused", "cancelled"):
                        sub.auto_renew = False
                        sub.status = SubscriptionStatus.PAST_DUE
                        user_result = await db.execute(select(User).where(User.id == user_id))
                        user_obj = user_result.scalar_one_or_none()
                        if user_obj and user_obj.email:
                            from app.core.email_service import send_email
                            from app.domains.subscriptions.email_templates import preapproval_payment_failed
                            plan_result = await db.execute(
                                select(SubscriptionPlan).where(SubscriptionPlan.id == sub.plan_id)
                            )
                            plan_obj = plan_result.scalar_one_or_none()
                            subject, html, text = preapproval_payment_failed(
                                plan_name=plan_obj.name if plan_obj else "SellIA",
                            )
                            await send_email(user_obj.email, subject, html, text)

                    await db.commit()

            # Log processed event
            db.add(WebhookEventLog(provider="mercadopago", event_id=event_id, event_type=topic))
            await db.commit()
            return {"status": "processed", "preapproval_status": preapproval_status}

        # === Payment webhook (one-time checkout) ===
        payment_info = await process_mercadopago_webhook(topic, data_id, data_id)

        if payment_info.get("status") == "ignored":
            db.add(WebhookEventLog(provider="mercadopago", event_id=event_id, event_type=topic))
            await db.commit()
            return {"status": "ignored"}

        user_id_str = payment_info.get("user_id")
        plan_slug = payment_info.get("plan_slug")
        payment_status = payment_info.get("status")

        if user_id_str and plan_slug:
            user_id = UUID(user_id_str)

            result = await db.execute(
                select(Subscription).where(Subscription.user_id == user_id).with_for_update()
            )
            sub = result.scalar_one_or_none()
            if sub:
                sub.mercadopago_payment_id = payment_info.get("payment_id")

                if payment_status in ("approved", "authorized"):
                    plan_result = await db.execute(
                        select(SubscriptionPlan).where(SubscriptionPlan.slug == plan_slug)
                    )
                    new_plan = plan_result.scalar_one_or_none()
                    if new_plan:
                        sub.plan_id = new_plan.id
                        sub.status = SubscriptionStatus.ACTIVE
                        sub.current_period_start = datetime.now(timezone.utc)
                        sub.current_period_end = datetime.now(timezone.utc) + timedelta(days=30)
                elif payment_status in ("rejected", "cancelled", "refunded"):
                    sub.status = SubscriptionStatus.PAST_DUE

                await db.commit()

        db.add(WebhookEventLog(provider="mercadopago", event_id=event_id, event_type=topic))
        await db.commit()
        return {"status": "processed", "payment_status": payment_status}
    except HTTPException:
        raise
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).exception("MercadoPago webhook error")
        return {"status": "error", "detail": "Internal server error"}


@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive Stripe webhook notifications."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = construct_webhook_event(payload, sig_header)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    event_id = event.id
    event_type = event.type

    # Deduplication
    existing = await db.execute(
        select(WebhookEventLog).where(
            WebhookEventLog.provider == "stripe",
            WebhookEventLog.event_id == event_id,
        )
    )
    if existing.scalar_one_or_none():
        return {"status": "already_processed"}

    try:
        result = process_stripe_webhook(event)

        if result.get("processed"):
            user_id_str = result.get("user_id")
            plan_slug = result.get("plan_slug")

            if user_id_str and plan_slug:
                user_id = UUID(user_id_str)

                sub_result = await db.execute(
                    select(Subscription).where(Subscription.user_id == user_id).with_for_update()
                )
                sub = sub_result.scalar_one_or_none()
                if sub:
                    if event_type == "checkout.session.completed":
                        sub.stripe_subscription_id = result.get("stripe_subscription_id")
                        sub.stripe_customer_id = result.get("stripe_customer_id")
                        plan_result = await db.execute(
                            select(SubscriptionPlan).where(SubscriptionPlan.slug == plan_slug)
                        )
                        new_plan = plan_result.scalar_one_or_none()
                        if new_plan:
                            sub.plan_id = new_plan.id
                            sub.status = SubscriptionStatus.ACTIVE
                            sub.current_period_start = datetime.now(timezone.utc)
                            sub.current_period_end = datetime.now(timezone.utc) + timedelta(days=30 if result.get("billing_cycle") == "monthly" else 365)
                    elif event_type == "invoice.payment_failed":
                        sub.status = SubscriptionStatus.PAST_DUE
                    elif event_type == "customer.subscription.deleted":
                        sub.status = SubscriptionStatus.CANCELLED
                        sub.auto_renew = False

                    await db.commit()

        db.add(WebhookEventLog(provider="stripe", event_id=event_id, event_type=event_type))
        await db.commit()
        return {"status": "processed", "event_type": event_type}
    except HTTPException:
        raise
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).exception("Stripe webhook error")
        return {"status": "error", "detail": "Internal server error"}


# =============================================================================
# Bank Transfer (Cocos Capital / Manual)
# =============================================================================

@router.post("/create-bank-transfer", response_model=BankTransferOrderResponse)
async def create_bank_transfer_order(
    data: BankTransferOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a bank transfer payment order."""
    from app.domains.subscriptions.services import generate_bank_transfer_order

    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.slug == data.plan_slug, SubscriptionPlan.is_active == True)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    sub = await get_or_create_subscription(db, current_user.id)
    user_region = get_region_from_country(current_user.country_code)
    price, currency = get_plan_price(plan, user_region, data.billing_cycle)

    order = await generate_bank_transfer_order(
        db=db,
        user=current_user,
        subscription=sub,
        plan=plan,
        amount=price,
        currency=currency,
        billing_cycle=data.billing_cycle,
    )

    return BankTransferOrderResponse.model_validate(order)


@router.post("/confirm-bank-transfer/{order_id}", response_model=BankTransferConfirmResponse)
async def confirm_bank_transfer(
    order_id: UUID,
    data: BankTransferConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """User confirms they have made the bank transfer."""
    result = await db.execute(
        select(BankTransferPayment).where(
            BankTransferPayment.id == order_id,
            BankTransferPayment.user_id == current_user.id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    if order.status != BankTransferStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"Orden ya está {order.status}")

    order.status = BankTransferStatus.PAID.value
    order.paid_at = datetime.now(timezone.utc)
    if data.proof_image_url:
        order.proof_image_url = data.proof_image_url

    await db.commit()

    # Notify user
    if current_user.email:
        from app.core.email_service import send_email
        from app.domains.subscriptions.email_templates import transfer_confirmed
        subject, html, text = transfer_confirmed(
            order_number=order.order_number,
            plan_name=current_user.preferred_currency or "SellIA",
        )
        await send_email(current_user.email, subject, html, text)

    return BankTransferConfirmResponse(
        status="waiting_confirmation",
        message="Transferencia registrada. Estamos verificando tu pago.",
    )


@router.post("/admin/approve-bank-transfer/{order_id}")
async def approve_bank_transfer(
    order_id: UUID,
    data: BankTransferAdminApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin approves a bank transfer payment."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Solo administradores")

    result = await db.execute(
        select(BankTransferPayment).where(BankTransferPayment.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    if order.status != BankTransferStatus.PAID.value:
        raise HTTPException(status_code=400, detail="La orden no está en estado 'paid'")

    if data.approved:
        order.status = BankTransferStatus.CONFIRMED.value
        order.confirmed_by_admin_at = datetime.now(timezone.utc)
        order.confirmed_by_admin_id = current_user.id

        # Activate subscription
        if order.subscription_id and order.plan_id:
            sub_result = await db.execute(select(Subscription).where(Subscription.id == order.subscription_id))
            sub = sub_result.scalar_one_or_none()
            plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == order.plan_id))
            plan = plan_result.scalar_one_or_none()
            if sub and plan:
                sub.plan_id = plan.id
                sub.status = SubscriptionStatus.ACTIVE
                sub.payment_provider = "bank_transfer"
                sub.current_period_start = datetime.now(timezone.utc)
                sub.current_period_end = datetime.now(timezone.utc) + timedelta(days=30 if order.billing_cycle == "monthly" else 365)
                sub.billing_cycle = order.billing_cycle or "monthly"
    else:
        order.status = BankTransferStatus.CANCELLED.value

    await db.commit()

    # Notify user
    user_result = await db.execute(select(User).where(User.id == order.user_id))
    order_user = user_result.scalar_one_or_none()
    if order_user and order_user.email:
        from app.core.email_service import send_email
        from app.domains.subscriptions.email_templates import transfer_approved, transfer_rejected
        if data.approved:
            plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == order.plan_id))
            plan = plan_result.scalar_one_or_none()
            subject, html, text = transfer_approved(
                order_number=order.order_number,
                plan_name=plan.name if plan else "SellIA",
                period_end=sub.current_period_end.strftime("%d/%m/%Y") if sub and sub.current_period_end else "",
            )
        else:
            subject, html, text = transfer_rejected(
                order_number=order.order_number,
                plan_name=plan.name if plan else "SellIA",
                reason=data.notes,
            )
        await send_email(order_user.email, subject, html, text)

    return {"status": order.status, "approved": data.approved}


@router.get("/admin/pending-transfers", response_model=list[BankTransferOrderResponse])
async def list_pending_transfers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all pending bank transfers (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Solo administradores")

    result = await db.execute(
        select(BankTransferPayment)
        .where(BankTransferPayment.status == BankTransferStatus.PAID.value)
        .order_by(BankTransferPayment.paid_at.desc())
    )
    return result.scalars().all()


# =============================================================================
# Cancellation with Feedback
# =============================================================================

@router.post("/cancel", response_model=CancellationFeedbackResponse)
async def cancel_subscription(
    data: CancellationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel subscription with mandatory feedback."""
    sub = await get_or_create_subscription(db, current_user.id)

    # Save feedback
    feedback = CancellationFeedback(
        user_id=current_user.id,
        subscription_id=sub.id,
        reason_category=data.reason_category.value,
        reason_text=data.reason_text,
        competitor_name=data.competitor_name,
        improvement_suggestion=data.improvement_suggestion,
        rating_nps=data.rating_nps,
    )
    db.add(feedback)

    # Mark subscription for cancellation
    sub.cancel_at_period_end = True

    # If free plan, cancel immediately
    plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == sub.plan_id))
    plan = plan_result.scalar_one_or_none()
    if plan and plan.slug == "free":
        sub.status = SubscriptionStatus.CANCELLED

    await db.commit()
    await db.refresh(feedback)

    # Notify user
    if current_user.email and plan:
        from app.core.email_service import send_email
        from app.domains.subscriptions.email_templates import subscription_cancelled
        subject, html, text = subscription_cancelled(
            plan_name=plan.name,
            period_end=sub.current_period_end.strftime("%d/%m/%Y") if sub.current_period_end else "próximos días",
        )
        await send_email(current_user.email, subject, html, text)

    return CancellationFeedbackResponse.model_validate(feedback)


# =============================================================================
# Retention Dashboard (Admin)
# =============================================================================

@router.get("/admin/retention", response_model=RetentionSummary)
async def get_retention_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get cancellation analytics (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Solo administradores")

    from sqlalchemy import func
    from datetime import datetime, timezone, timedelta

    # Total cancellations
    total_result = await db.execute(select(func.count(CancellationFeedback.id)))
    total = total_result.scalar() or 0

    # This month
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_result = await db.execute(
        select(func.count(CancellationFeedback.id))
        .where(CancellationFeedback.cancelled_at >= month_start)
    )
    month_count = month_result.scalar() or 0

    # Average NPS
    nps_result = await db.execute(
        select(func.avg(CancellationFeedback.rating_nps))
        .where(CancellationFeedback.rating_nps.isnot(None))
    )
    avg_nps = nps_result.scalar()

    # Top reasons
    reasons_result = await db.execute(
        select(CancellationFeedback.reason_category, func.count(CancellationFeedback.id))
        .group_by(CancellationFeedback.reason_category)
        .order_by(func.count(CancellationFeedback.id).desc())
        .limit(5)
    )
    top_reasons = [
        {"reason": row[0], "count": row[1]} for row in reasons_result.all()
    ]

    # Top competitors
    competitors_result = await db.execute(
        select(CancellationFeedback.competitor_name, func.count(CancellationFeedback.id))
        .where(CancellationFeedback.competitor_name.isnot(None))
        .group_by(CancellationFeedback.competitor_name)
        .order_by(func.count(CancellationFeedback.id).desc())
        .limit(5)
    )
    top_competitors = [
        {"name": row[0], "count": row[1]} for row in competitors_result.all()
    ]

    # Churn rate: cancellations / total active users
    active_result = await db.execute(
        select(func.count(Subscription.id))
        .where(Subscription.status == SubscriptionStatus.ACTIVE)
    )
    active_count = active_result.scalar() or 1
    churn_rate = (month_count / active_count) * 100 if active_count > 0 else 0

    return RetentionSummary(
        total_cancellations=total,
        cancellations_this_month=month_count,
        churn_rate_percent=round(churn_rate, 2),
        avg_nps=round(float(avg_nps), 2) if avg_nps else None,
        top_reasons=top_reasons,
        top_competitors=top_competitors,
    )


@router.get("/admin/feedbacks", response_model=list[CancellationFeedbackResponse])
async def list_cancellation_feedbacks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all cancellation feedbacks (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Solo administradores")

    result = await db.execute(
        select(CancellationFeedback).order_by(CancellationFeedback.cancelled_at.desc())
    )
    return result.scalars().all()


@router.get("/admin/revenue", response_model=RevenueSummary)
async def get_admin_revenue(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get revenue metrics (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Solo administradores")

    from sqlalchemy import func
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Total revenue this month from confirmed bank transfers
    transfer_revenue = await db.execute(
        select(func.coalesce(func.sum(BankTransferPayment.amount), 0))
        .where(
            BankTransferPayment.status == BankTransferStatus.CONFIRMED.value,
            BankTransferPayment.confirmed_by_admin_at >= month_start,
        )
    )
    transfer_total = float(transfer_revenue.scalar() or 0)

    # Total revenue this month from MP payments (one-time + preapproval)
    mp_revenue = await db.execute(
        select(func.coalesce(func.sum(PaymentTransaction.amount), 0))
        .where(
            PaymentTransaction.provider == PaymentProvider.MERCADOPAGO.value,
            PaymentTransaction.status == PaymentStatus.COMPLETED.value,
            PaymentTransaction.created_at >= month_start,
        )
    )
    mp_total = float(mp_revenue.scalar() or 0)

    # Crypto revenue
    crypto_revenue = await db.execute(
        select(func.coalesce(func.sum(PaymentTransaction.amount), 0))
        .where(
            PaymentTransaction.provider == PaymentProvider.CRYPTO.value,
            PaymentTransaction.status == PaymentStatus.COMPLETED.value,
            PaymentTransaction.created_at >= month_start,
        )
    )
    crypto_total = float(crypto_revenue.scalar() or 0)

    revenue_this_month = transfer_total + mp_total + crypto_total

    # MRR = sum of active subscriptions with auto_renew (approximate using plan prices)
    mrr_result = await db.execute(
        select(func.coalesce(func.sum(SubscriptionPlan.price_monthly_ars), 0))
        .select_from(Subscription)
        .join(SubscriptionPlan)
        .where(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.auto_renew == True,
        )
    )
    mrr = float(mrr_result.scalar() or 0)

    # Pending transfers count
    pending_count_result = await db.execute(
        select(func.count(BankTransferPayment.id))
        .where(BankTransferPayment.status == BankTransferStatus.PAID.value)
    )
    pending_count = pending_count_result.scalar() or 0

    # Active subscriptions count
    active_count_result = await db.execute(
        select(func.count(Subscription.id))
        .where(Subscription.status == SubscriptionStatus.ACTIVE)
    )
    active_count = active_count_result.scalar() or 0

    return RevenueSummary(
        mrr=round(mrr, 2),
        arr=round(mrr * 12, 2),
        revenue_this_month=round(revenue_this_month, 2),
        revenue_by_provider={
            "mercadopago": round(mp_total, 2),
            "bank_transfer": round(transfer_total, 2),
            "crypto": round(crypto_total, 2),
        },
        pending_transfers_count=pending_count,
        active_subscriptions_count=active_count,
    )


@router.get("/admin/bank-transfers", response_model=list[BankTransferOrderResponse])
async def list_admin_bank_transfers(
    status: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all bank transfers with filters (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Solo administradores")

    query = select(BankTransferPayment).order_by(BankTransferPayment.created_at.desc())

    if status:
        query = query.where(BankTransferPayment.status == status)
    if date_from:
        from datetime import datetime as dt
        try:
            df = dt.fromisoformat(date_from)
            query = query.where(BankTransferPayment.created_at >= df)
        except ValueError:
            pass
    if date_to:
        from datetime import datetime as dt
        try:
            dt_to = dt.fromisoformat(date_to)
            query = query.where(BankTransferPayment.created_at <= dt_to)
        except ValueError:
            pass

    offset = (page - 1) * limit
    result = await db.execute(query.offset(offset).limit(limit))
    return result.scalars().all()


@router.get("/admin/subscriptions", response_model=list[AdminSubscriptionResponse])
async def list_admin_subscriptions(
    plan_slug: str = Query(None),
    provider: str = Query(None),
    status: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all subscriptions with user info (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Solo administradores")

    query = (
        select(Subscription, User, SubscriptionPlan)
        .join(User, Subscription.user_id == User.id)
        .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
        .order_by(Subscription.created_at.desc())
    )

    if plan_slug:
        query = query.where(SubscriptionPlan.slug == plan_slug)
    if provider:
        query = query.where(Subscription.payment_provider == provider)
    if status:
        query = query.where(Subscription.status == status)

    offset = (page - 1) * limit
    result = await db.execute(query.offset(offset).limit(limit))

    rows = []
    for sub, user, plan in result.all():
        rows.append(AdminSubscriptionResponse(
            id=sub.id,
            user_id=sub.user_id,
            user_email=user.email,
            user_full_name=user.full_name,
            plan_id=sub.plan_id,
            plan_name=plan.name,
            plan_slug=plan.slug,
            status=sub.status.value if hasattr(sub.status, "value") else str(sub.status),
            billing_cycle=sub.billing_cycle,
            payment_provider=sub.payment_provider,
            next_billing_date=sub.next_billing_date,
            current_period_end=sub.current_period_end,
            auto_renew=sub.auto_renew,
            created_at=sub.created_at,
        ))
    return rows


# ========== Invoices ==========

@router.get("/invoices", response_model=list[InvoiceResponse])
async def list_invoices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Invoice).where(Invoice.user_id == current_user.id).order_by(Invoice.created_at.desc())
    )
    return result.scalars().all()


@router.get("/invoices/{invoice_id}/download")
async def download_invoice(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == current_user.id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    if invoice.pdf_url:
        return {"pdf_url": invoice.pdf_url}

    raise HTTPException(status_code=404, detail="PDF no disponible aún")


# ========== Billing Details ==========

@router.put("/billing-details", response_model=BillingDetailsResponse)
async def update_billing_details(
    data: BillingDetailsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.tax_id is not None:
        current_user.tax_id = data.tax_id
    if data.billing_address is not None:
        current_user.billing_address = data.billing_address
    if data.full_name is not None:
        current_user.full_name = data.full_name

    await db.commit()
    await db.refresh(current_user)

    return BillingDetailsResponse(
        tax_id=current_user.tax_id,
        billing_address=current_user.billing_address or {},
        full_name=current_user.full_name,
        country_code=current_user.country_code,
        preferred_currency=current_user.preferred_currency,
    )


# ========== Region Detection ==========

@router.get("/region-detect", response_model=RegionDetectResponse)
async def detect_region(request: Request):
    client_host = request.client.host if request.client else None

    detected_country = None
    if client_host and client_host not in ("127.0.0.1", "localhost", "::1"):
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"http://ip-api.com/json/{client_host}?fields=status,country,countryCode")
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") == "success":
                        detected_country = data.get("countryCode")
        except Exception:
            detected_country = None

    region = get_region_from_country(detected_country)
    suggested_currency = "ARS" if region == "AR" else "USD"

    return RegionDetectResponse(
        detected_country=detected_country,
        detected_region=region,
        suggested_currency=suggested_currency,
    )


# ========== User Region ==========

@router.put("/user-region", response_model=BillingDetailsResponse)
async def update_user_region(
    data: UserRegionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.country_code = data.country_code
    current_user.preferred_currency = data.preferred_currency
    if data.timezone is not None:
        current_user.timezone = data.timezone

    await db.commit()
    await db.refresh(current_user)

    return BillingDetailsResponse(
        tax_id=current_user.tax_id,
        billing_address=current_user.billing_address or {},
        full_name=current_user.full_name,
        country_code=current_user.country_code,
        preferred_currency=current_user.preferred_currency,
    )


# ========== API Keys ==========

@router.post("/api-keys", response_model=UserAPIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_in: UserAPIKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    encrypted_hash = get_password_hash(key_in.api_key)[:255]
    encrypted_fernet = encrypt_value(key_in.api_key)

    api_key = UserAPIKey(
        user_id=current_user.id,
        provider=key_in.provider,
        encrypted_key=encrypted_hash,
        api_key_fernet=encrypted_fernet,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return api_key


@router.get("/api-keys", response_model=list[UserAPIKeyResponse])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(UserAPIKey).where(
            UserAPIKey.user_id == current_user.id,
            UserAPIKey.is_active == True,
        )
    )
    return result.scalars().all()


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(UserAPIKey).where(
            UserAPIKey.id == key_id,
            UserAPIKey.user_id == current_user.id,
        )
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key no encontrada")
    key.is_active = False
    await db.commit()
    return None
