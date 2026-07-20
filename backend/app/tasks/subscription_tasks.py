"""Subscription Background Tasks

Tareas de Celery para gestión de suscripciones, pagos crypto,
recordatorios de renovación, alerts de uso, y downgrade automático.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from celery import shared_task

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from sqlalchemy import select, func

logger = get_logger(__name__)


@shared_task
def check_expiring_subscriptions():
    """Verifica suscripciones que vencen pronto y envía recordatorios."""
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.domains.subscriptions.models import Subscription, SubscriptionStatus, SubscriptionPlan
            from app.domains.users.models import User

            now = datetime.now(timezone.utc)

            # Recordatorio a 7 días
            reminder_7d = now + timedelta(days=7)
            result = await db.execute(
                select(Subscription, User)
                .join(User)
                .where(
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.auto_renew == True,
                    Subscription.current_period_end <= reminder_7d,
                    Subscription.current_period_end > now + timedelta(days=6),
                )
            )
            for sub, user in result.all():
                logger.info(f"Recordatorio 7d: usuario {user.id}, plan {sub.plan_id}")
                # TODO: Enviar email de recordatorio

            # Recordatorio a 1 día
            reminder_1d = now + timedelta(days=1)
            result = await db.execute(
                select(Subscription, User)
                .join(User)
                .where(
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.auto_renew == True,
                    Subscription.current_period_end <= reminder_1d,
                    Subscription.current_period_end > now,
                )
            )
            for sub, user in result.all():
                logger.info(f"Recordatorio 1d: usuario {user.id}, plan {sub.plan_id}")
                # TODO: Enviar email de último recordatorio

            # Suscripciones vencidas -> downgrade a Free
            result = await db.execute(
                select(Subscription, User)
                .join(User)
                .where(
                    Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]),
                    Subscription.current_period_end < now,
                    Subscription.grace_period_end < now if Subscription.grace_period_end else True,
                )
            )
            for sub, user in result.all():
                # Buscar plan Free
                free_plan = await db.execute(
                    select(SubscriptionPlan).where(SubscriptionPlan.slug == "free")
                )
                free_plan = free_plan.scalar_one_or_none()
                if free_plan:
                    sub.plan_id = free_plan.id
                    sub.status = SubscriptionStatus.ACTIVE
                    sub.billing_cycle = "monthly"
                    sub.payment_provider = None
                    sub.stripe_subscription_id = None
                    sub.mercadopago_preference_id = None
                    sub.next_billing_date = None
                    logger.info(f"Downgrade a Free: usuario {user.id}")

            await db.commit()

    asyncio.run(_run())


@shared_task
def process_crypto_pending_payments():
    """Consulta blockchain para pagos crypto pendientes."""
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.domains.subscriptions.models import PaymentTransaction, PaymentStatus, Subscription, SubscriptionStatus, SubscriptionPlan
            from app.domains.subscriptions.crypto_billing import check_crypto_payment_status, verify_crypto_payment

            now = datetime.now(timezone.utc)
            ttl = now - timedelta(minutes=30)

            result = await db.execute(
                select(PaymentTransaction)
                .where(
                    PaymentTransaction.status == PaymentStatus.PENDING,
                    PaymentTransaction.provider == "crypto",
                    PaymentTransaction.created_at > ttl,
                )
            )
            transactions = result.scalars().all()

            for tx in transactions:
                if not tx.crypto_tx_hash or not tx.crypto_network:
                    continue

                try:
                    status = await check_crypto_payment_status(tx.crypto_tx_hash, tx.crypto_network)
                    tx.crypto_confirmations = status.get("confirmations", 0)

                    if status.get("status") == "completed" and tx.crypto_confirmations >= 12:
                        # Verificar monto
                        verified = await verify_crypto_payment(
                            tx.crypto_tx_hash,
                            float(tx.amount),
                            tx.crypto_from_address or "",
                            tx.crypto_network,
                        )

                        if verified.get("verified"):
                            tx.status = PaymentStatus.COMPLETED
                            tx.completed_at = now

                            # Activar suscripción
                            if tx.subscription_id:
                                sub_result = await db.execute(
                                    select(Subscription).where(Subscription.id == tx.subscription_id)
                                )
                                sub = sub_result.scalar_one_or_none()
                                if sub and tx.plan_id:
                                    sub.plan_id = tx.plan_id
                                    sub.status = SubscriptionStatus.ACTIVE
                                    sub.current_period_start = now
                                    sub.current_period_end = now + timedelta(days=30 if tx.billing_cycle == "monthly" else 365)
                                    sub.payment_provider = "crypto"
                                    sub.crypto_network = tx.crypto_network
                                    logger.info(f"Crypto payment completed: tx {tx.id}, sub {sub.id}")

                    await db.commit()
                except Exception as e:
                    logger.error(f"Error checking crypto tx {tx.id}: {e}")

    asyncio.run(_run())


@shared_task
def cleanup_expired_crypto_payments():
    """Marca como expirados los pagos crypto que superaron el TTL."""
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.domains.subscriptions.models import PaymentTransaction, PaymentStatus

            now = datetime.now(timezone.utc)
            ttl = now - timedelta(minutes=30)

            result = await db.execute(
                select(PaymentTransaction)
                .where(
                    PaymentTransaction.status == PaymentStatus.PENDING,
                    PaymentTransaction.provider == "crypto",
                    PaymentTransaction.created_at < ttl,
                )
            )
            for tx in result.scalars().all():
                tx.status = PaymentStatus.EXPIRED
                logger.info(f"Crypto payment expired: tx {tx.id}")

            await db.commit()

    asyncio.run(_run())


@shared_task
def check_usage_alerts():
    """Verifica uso de suscripciones y envía alerts al 80% y 100%."""
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.domains.subscriptions.models import (
                Subscription, SubscriptionPlan, UsageTracking, UsageAlert, SubscriptionStatus,
            )
            from app.domains.users.models import User
            from sqlalchemy import func

            current_month = datetime.now(timezone.utc).strftime("%Y-%m")

            result = await db.execute(
                select(Subscription, SubscriptionPlan, User)
                .join(SubscriptionPlan)
                .join(User)
                .where(Subscription.status == SubscriptionStatus.ACTIVE)
            )

            for sub, plan, user in result.all():
                limits = plan.limits or {}

                for metric, limit in limits.items():
                    if limit <= 0 or limit == -1:
                        continue

                    # Get usage
                    usage_result = await db.execute(
                        select(func.coalesce(func.sum(UsageTracking.quantity), 0))
                        .where(
                            UsageTracking.user_id == user.id,
                            UsageTracking.metric_type == metric,
                            UsageTracking.period_month == current_month,
                        )
                    )
                    used = usage_result.scalar() or 0
                    percent = (used / limit) * 100

                    for threshold in [80, 100]:
                        if percent >= threshold:
                            # Check if alert already sent
                            existing = await db.execute(
                                select(UsageAlert)
                                .where(
                                    UsageAlert.user_id == user.id,
                                    UsageAlert.metric_type == metric,
                                    UsageAlert.threshold_percent == threshold,
                                    UsageAlert.sent_at >= datetime.now(timezone.utc) - timedelta(days=7),
                                )
                            )
                            if not existing.scalar_one_or_none():
                                alert = UsageAlert(
                                    user_id=user.id,
                                    metric_type=metric,
                                    threshold_percent=threshold,
                                )
                                db.add(alert)
                                logger.info(f"Usage alert {threshold}%: {metric} para usuario {user.id}")
                                # TODO: Enviar email/push

            await db.commit()

    asyncio.run(_run())


@shared_task
def generate_recurring_invoices():
    """Genera invoices para suscripciones con renovación automática."""
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.domains.subscriptions.models import Subscription, SubscriptionStatus, SubscriptionPlan
            from app.domains.subscriptions.services import create_invoice

            now = datetime.now(timezone.utc)

            result = await db.execute(
                select(Subscription, SubscriptionPlan)
                .join(SubscriptionPlan)
                .where(
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.auto_renew == True,
                    Subscription.next_billing_date <= now + timedelta(days=1),
                )
            )

            for sub, plan in result.all():
                from app.domains.subscriptions.services import get_plan_price, get_region_from_country
                from app.domains.users.models import User

                user_result = await db.execute(select(User).where(User.id == sub.user_id))
                user = user_result.scalar_one_or_none()
                if not user:
                    continue

                region = get_region_from_country(user.country_code)
                price, currency = get_plan_price(plan, region, sub.billing_cycle or "monthly")

                try:
                    await create_invoice(
                        db=db,
                        user_id=user.id,
                        transaction_id=None,
                        plan=plan,
                        amount=price,
                        currency=currency,
                        billing_cycle=sub.billing_cycle or "monthly",
                        region=region,
                    )
                    logger.info(f"Invoice generada para usuario {user.id}, plan {plan.slug}")
                except Exception as e:
                    logger.error(f"Error generando invoice para {user.id}: {e}")

    asyncio.run(_run())



@shared_task
def send_transfer_reminders():
    """Envía recordatorios de transferencias pendientes que están por vencer."""
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.domains.subscriptions.models import BankTransferPayment, BankTransferStatus
            from app.domains.users.models import User
            from app.core.email_service import send_email
            from app.domains.subscriptions.email_templates import transfer_reminder

            now = datetime.now(timezone.utc)
            reminder_threshold = now + timedelta(hours=24)

            result = await db.execute(
                select(BankTransferPayment, User)
                .join(User)
                .where(
                    BankTransferPayment.status == BankTransferStatus.PENDING.value,
                    BankTransferPayment.expires_at <= reminder_threshold,
                    BankTransferPayment.expires_at > now,
                )
            )

            for order, user in result.all():
                if not user.email:
                    continue
                hours_left = int((order.expires_at - now).total_seconds() // 3600)
                subject, html, text = transfer_reminder(
                    order_number=order.order_number,
                    plan_name=user.preferred_currency or "SellIA",
                    amount=float(order.amount),
                    currency=order.currency,
                    hours_left=max(hours_left, 1),
                )
                await send_email(user.email, subject, html, text)
                logger.info(f"Reminder enviado: orden {order.order_number}, usuario {user.id}")

    asyncio.run(_run())


@shared_task
def expire_pending_transfers():
    """Marca como expiradas las transferencias que superaron las 48h."""
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.domains.subscriptions.models import BankTransferPayment, BankTransferStatus
            from app.domains.users.models import User
            from app.core.email_service import send_email
            from app.domains.subscriptions.email_templates import transfer_expired

            now = datetime.now(timezone.utc)

            result = await db.execute(
                select(BankTransferPayment, User)
                .join(User)
                .where(
                    BankTransferPayment.status == BankTransferStatus.PENDING.value,
                    BankTransferPayment.expires_at < now,
                )
            )

            for order, user in result.all():
                order.status = BankTransferStatus.EXPIRED.value
                if user.email:
                    subject, html, text = transfer_expired(
                        order_number=order.order_number,
                        plan_name=user.preferred_currency or "SellIA",
                    )
                    await send_email(user.email, subject, html, text)
                logger.info(f"Orden expirada: {order.order_number}, usuario {user.id}")

            await db.commit()

    asyncio.run(_run())



@shared_task
def sync_mercadopago_preapprovals():
    """Sincroniza estados de preapprovals con MercadoPago (resiliencia ante webhooks perdidos)."""
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.domains.subscriptions.models import Subscription, SubscriptionStatus
            from app.domains.users.models import User
            from app.domains.subscriptions.billing import get_preapproval_status
            from app.core.email_service import send_email
            from app.domains.subscriptions.email_templates import preapproval_payment_failed

            result = await db.execute(
                select(Subscription, User)
                .join(User)
                .where(
                    Subscription.mercadopago_preapproval_id.isnot(None),
                    Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]),
                )
            )

            for sub, user in result.all():
                if not sub.mercadopago_preapproval_id:
                    continue
                try:
                    status = await get_preapproval_status(sub.mercadopago_preapproval_id)
                    mp_status = status.get("status")

                    if mp_status in ("paused", "cancelled"):
                        sub.auto_renew = False
                        sub.status = SubscriptionStatus.PAST_DUE
                        if user.email:
                            from app.domains.subscriptions.models import SubscriptionPlan
                            plan_result = await db.execute(
                                select(SubscriptionPlan).where(SubscriptionPlan.id == sub.plan_id)
                            )
                            plan = plan_result.scalar_one_or_none()
                            subject, html, text = preapproval_payment_failed(
                                plan_name=plan.name if plan else "SellIA",
                            )
                            await send_email(user.email, subject, html, text)
                        logger.info(f"Preapproval pausado/cancelado: sub {sub.id}, user {user.id}")

                    elif mp_status == "authorized":
                        sub.auto_renew = True
                        next_payment = status.get("next_payment_date")
                        if next_payment:
                            from datetime import datetime as dt
                            if isinstance(next_payment, str):
                                try:
                                    sub.next_billing_date = dt.fromisoformat(next_payment.replace("Z", "+00:00"))
                                except ValueError:
                                    pass

                    await db.commit()
                except Exception as e:
                    logger.error(f"Error sync preapproval {sub.mercadopago_preapproval_id}: {e}")

    asyncio.run(_run())
