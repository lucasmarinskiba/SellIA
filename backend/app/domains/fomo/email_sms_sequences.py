"""Email + SMS Campaign Sequences - Multi-touch automation"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional
from uuid import UUID

from app.domains.notifications.service import email_service, sms_service


class SequenceType(str, Enum):
    CART_ABANDONMENT = "cart_abandonment"
    CHURN_RECOVERY = "churn_recovery"
    FEATURE_LAUNCH = "feature_launch"
    UPGRADE_NUDGE = "upgrade_nudge"
    TRIAL_EXPIRATION = "trial_expiration"


class EmailSequence:
    SEQUENCES = {
        "cart_abandoned_1": {
            "subject": "😱 Olvidaste tu carrito...",
            "delay_hours": 0,
            "channel": "email",
        },
        "cart_abandoned_sms": {
            "message": "🔥 Carrito expira HOY. Checkout: {url}. {code}",
            "delay_hours": 2,
            "channel": "sms",
        },
        "cart_abandoned_2": {
            "subject": "⏰ Última oportunidad: {product_name} se acaba",
            "delay_hours": 24,
            "channel": "email",
        },
        "churn_check_in": {
            "message": "Hola! 👋 ¿Necesitas ayuda? Responde o llama 24/7",
            "delay_hours": 0,
            "channel": "sms",
        },
        "churn_help": {
            "subject": "Queremos ayudarte a vender MÁS 💪",
            "delay_hours": 2,
            "channel": "email",
        },
        "churn_exclusive": {
            "message": "🎁 VUELVE30 = 30% OFF Plan Pro. Válido solo hoy",
            "delay_hours": 24,
            "channel": "sms",
        },
        "feature_launch": {
            "subject": "✨ Acabamos de soltar {feature} (SOLO para ti)",
            "delay_hours": 0,
            "channel": "email",
        },
        "upgrade_introduce": {
            "subject": "Estás cerca del límite del plan Free",
            "delay_hours": 0,
            "channel": "email",
        },
        "trial_expiration_7d": {
            "subject": "Trial expira en 7 días - 50% OFF si activas ahora",
            "delay_hours": -168,  # 7 days before
            "channel": "email",
        },
    }

    @staticmethod
    async def start_cart_abandonment_sequence(
        user_email: str,
        user_phone: str,
        cart_value: float,
        items: list,
    ):
        """3-touch sequence: Email → SMS → Email"""

        # Email 1: Immediate
        await email_service.send(
            to=user_email,
            subject="😱 Olvidaste tu carrito...",
            template="cart_abandoned_1",
            context={
                "items": items,
                "total": cart_value,
                "offer": "COMPLETA15",
                "discount": "15% OFF",
            }
        )

        # SMS 2: After 2 hours
        await asyncio.sleep(7200)
        await sms_service.send(
            to=user_phone,
            message=f"🔥 ${cart_value} de tu carrito expira HOY. Usa COMPLETA15"
        )

        # Email 3: After 24 hours
        await asyncio.sleep(82800)
        await email_service.send(
            to=user_email,
            subject=f"⏰ Última oportunidad",
            template="cart_abandoned_2",
            context={
                "items": items,
                "total": cart_value,
                "offer": "20% OFF",
                "countdown": "6 horas",
            }
        )

    @staticmethod
    async def start_churn_recovery_sequence(
        user_email: str,
        user_phone: str,
        days_inactive: int,
    ):
        """4-touch escalating rescue sequence"""

        steps = [
            {"delay": 0, "channel": "sms", "message": "¿Necesitas ayuda? Responde o llama"},
            {"delay": 7200, "channel": "email", "subject": "Queremos ayudarte a vender MÁS"},
            {"delay": 86400, "channel": "sms", "message": "VUELVE30 = 30% OFF Pro"},
            {"delay": 172800, "channel": "email", "subject": "Último intento: 40% OFF"},
        ]

        for step in steps:
            await asyncio.sleep(step["delay"])
            if step["channel"] == "sms":
                await sms_service.send(to=user_phone, message=step["message"])
            else:
                await email_service.send(
                    to=user_email,
                    subject=step["subject"],
                    template="churn_sequence"
                )

    @staticmethod
    async def start_feature_launch_sequence(
        user_email: str,
        user_phone: str,
        feature_name: str,
        feature_url: str,
    ):
        """3-touch feature launch announcement"""

        # Email 1: Announce
        await email_service.send(
            to=user_email,
            subject=f"✨ {feature_name} (Early access para ti)",
            template="feature_launch",
            context={
                "feature": feature_name,
                "url": feature_url,
                "benefit": "Automatiza aún más tu negocio",
            }
        )

        # SMS 2: After 3 hours
        await asyncio.sleep(10800)
        await sms_service.send(
            to=user_phone,
            message=f"✨ {feature_name} ya disponible para Pro"
        )

        # Email 3: Tutorial
        await asyncio.sleep(86400)
        await email_service.send(
            to=user_email,
            subject=f"Tutorial: Cómo usar {feature_name}",
            template="feature_tutorial",
            context={
                "feature": feature_name,
                "video_url": f"{feature_url}/tutorial",
            }
        )

    @staticmethod
    async def start_trial_expiration_sequence(
        user_email: str,
        user_phone: str,
        trial_expires_at: datetime,
    ):
        """
        Time-based sequence:
        - 7 days before: soft reminder
        - 6 hours before: urgent SMS
        - At expiration: final email
        """

        hours_until_expiration = (trial_expires_at - datetime.now(timezone.utc)).total_seconds() / 3600

        # Email 1: 7 days before
        await asyncio.sleep(max(0, (hours_until_expiration - 168) * 3600))
        await email_service.send(
            to=user_email,
            subject="Trial expira en 7 días",
            template="trial_expiration_7d",
            context={"discount": "50% OFF primer mes"}
        )

        # SMS 2: 6 hours before
        await asyncio.sleep(max(0, 162 * 3600))
        await sms_service.send(
            to=user_phone,
            message="Trial expira HOY. Activa Pro para no perder acceso 🚨 TRIAL50"
        )

        # Email 3: At expiration
        await asyncio.sleep(max(0, 6 * 3600))
        await email_service.send(
            to=user_email,
            subject="¿Fue útil SellIA?",
            template="trial_expired",
            context={"discount": "60% OFF por 3 meses"}
        )


import asyncio
