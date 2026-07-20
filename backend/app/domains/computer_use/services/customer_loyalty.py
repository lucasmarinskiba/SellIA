"""Customer Loyalty Engine — Email sequences, upsells, win-backs, lifetime value.

Fase 12: Fideliza clientes → upsell → retención → aumenta LTV.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class EmailSequenceType(str, Enum):
    """Tipos de secuencias de email."""
    WELCOME = "welcome"  # Post-compra
    ONBOARDING = "onboarding"  # Introducción
    UPSELL = "upsell"  # Vender más
    WIN_BACK = "win_back"  # Re-engagement
    VIP = "vip"  # Retención premium


class CustomerSegment(str, Enum):
    """Segmentación de clientes."""
    NEW = "new"  # <30 days
    ACTIVE = "active"  # Recent activity
    AT_RISK = "at_risk"  # Inactivos
    CHURNED = "churned"  # Nunca compran


class EmailSequence:
    """Secuencia automática de emails."""

    def __init__(
        self,
        sequence_id: str,
        name: str,
        sequence_type: EmailSequenceType,
        emails: List[Dict[str, str]],  # [{delay_days, subject, body}, ...]
    ):
        self.sequence_id = sequence_id
        self.name = name
        self.sequence_type = sequence_type
        self.emails = emails

        self.status = "active"  # active, paused
        self.created_at = datetime.utcnow()
        self.stats = {
            "sent": 0,
            "opened": 0,
            "clicked": 0,
            "conversions": 0,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sequence_id": self.sequence_id,
            "name": self.name,
            "type": self.sequence_type.value,
            "email_count": len(self.emails),
            "stats": self.stats,
        }


class UpsellOpportunity:
    """Oportunidad de upsell/cross-sell."""

    def __init__(
        self,
        customer_id: str,
        product_purchased: str,
        upsell_product: str,
        discount: float = 0.1,  # 10%
        urgency_hours: int = 24,
    ):
        self.customer_id = customer_id
        self.product_purchased = product_purchased
        self.upsell_product = upsell_product
        self.discount = discount
        self.urgency_hours = urgency_hours

        self.score = self._calculate_upsell_score()
        self.created_at = datetime.utcnow()
        self.expires_at = self.created_at + timedelta(hours=urgency_hours)
        self.sent = False

    def _calculate_upsell_score(self) -> float:
        """Calcula probabilidad de aceptar upsell."""
        # Mock: basaría en histórico de compras, LTV, etc
        return 0.65

    def to_dict(self) -> Dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "from_product": self.product_purchased,
            "to_product": self.upsell_product,
            "discount": f"{self.discount*100:.0f}%",
            "score": self.score,
            "expires_at": self.expires_at.isoformat(),
        }


class CustomerLoyaltyEngine:
    """Gestiona retención + upsells + loyalty."""

    # Email sequences predefinidas
    WELCOME_SEQUENCE = [
        {
            "delay_days": 0,
            "subject": "¡Bienvenido! Aquí está tu acceso",
            "body": "Hola {name},\n\nGracias por comprar. Aquí está tu acceso...",
        },
        {
            "delay_days": 2,
            "subject": "3 tips para maximizar tu compra",
            "body": "Hi {name},\n\n3 cosas que deberías hacer ahora...",
        },
        {
            "delay_days": 5,
            "subject": "¿Necesitas ayuda? Acá estoy",
            "body": "How's it going? Any questions?",
        },
    ]

    UPSELL_SEQUENCE = [
        {
            "delay_days": 0,
            "subject": "Eleva tu juego: {upsell_product}",
            "body": "Hey {name},\n\nViste que compraste {product}.\nLe falta {upsell_product}...",
        },
        {
            "delay_days": 3,
            "subject": "Oferta especial expira hoy: 10% OFF",
            "body": "¡Últimas horas! {upsell_product} solo ${price}",
        },
    ]

    WIN_BACK_SEQUENCE = [
        {
            "delay_days": 0,
            "subject": "Te extrañamos - 20% OFF para volver",
            "body": "Hey {name},\n\nNo vemos actividad... aquí va 20% OFF para que vuelvas",
        },
        {
            "delay_days": 7,
            "subject": "Última oportunidad: vuelve con nosotros",
            "body": "Last chance para el 20% OFF",
        },
    ]

    def __init__(self):
        self.logger = logger
        self.sequences: Dict[str, EmailSequence] = {}
        self.upsell_queue: List[UpsellOpportunity] = []

    async def create_email_sequence(
        self,
        name: str,
        sequence_type: EmailSequenceType,
        emails: Optional[List[Dict[str, str]]] = None,
    ) -> EmailSequence:
        """Crea secuencia de emails automática."""
        try:
            sequence_id = f"seq_{sequence_type.value}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            # Usar template default
            if not emails:
                if sequence_type == EmailSequenceType.WELCOME:
                    emails = self.WELCOME_SEQUENCE
                elif sequence_type == EmailSequenceType.UPSELL:
                    emails = self.UPSELL_SEQUENCE
                elif sequence_type == EmailSequenceType.WIN_BACK:
                    emails = self.WIN_BACK_SEQUENCE
                else:
                    emails = []

            sequence = EmailSequence(
                sequence_id=sequence_id,
                name=name,
                sequence_type=sequence_type,
                emails=emails,
            )

            self.sequences[sequence_id] = sequence

            self.logger.info(f"Email sequence created: {name} ({len(emails)} emails)")

            return sequence

        except Exception as e:
            self.logger.error(f"Error creating sequence: {e}")
            raise

    async def trigger_welcome_sequence(
        self,
        customer_id: str,
        customer_name: str,
        customer_email: str,
        product: str,
    ) -> Tuple[bool, str]:
        """Inicia secuencia de bienvenida post-compra."""
        try:
            # Obtener o crear sequence
            welcome_seq = list(self.sequences.values())
            if not welcome_seq or welcome_seq[0].sequence_type != EmailSequenceType.WELCOME:
                welcome_seq = await self.create_email_sequence(
                    name="Welcome Sequence",
                    sequence_type=EmailSequenceType.WELCOME,
                )
            else:
                welcome_seq = welcome_seq[0]

            # Enviar primer email
            first_email = welcome_seq.emails[0]

            subject = first_email["subject"]
            body = first_email["body"].format(name=customer_name, product=product)

            success = await self._send_email(customer_email, subject, body)

            if success:
                welcome_seq.stats["sent"] += 1
                self.logger.info(f"Welcome sequence triggered for {customer_email}")

            return success, welcome_seq.sequence_id

        except Exception as e:
            self.logger.error(f"Error triggering welcome: {e}")
            return False, ""

    async def create_upsell_offer(
        self,
        customer_id: str,
        product_purchased: str,
        upsell_product: str,
        discount: float = 0.1,
    ) -> UpsellOpportunity:
        """Crea oportunidad de upsell."""
        try:
            opportunity = UpsellOpportunity(
                customer_id=customer_id,
                product_purchased=product_purchased,
                upsell_product=upsell_product,
                discount=discount,
            )

            self.upsell_queue.append(opportunity)

            self.logger.info(f"Upsell opportunity created for {customer_id}")

            return opportunity

        except Exception as e:
            self.logger.error(f"Error creating upsell: {e}")
            raise

    async def send_upsell_email(
        self,
        opportunity: UpsellOpportunity,
        customer_email: str,
        customer_name: str,
    ) -> bool:
        """Envía email de upsell."""
        try:
            upsell_template = self.UPSELL_SEQUENCE[0]

            subject = upsell_template["subject"].format(
                upsell_product=opportunity.upsell_product
            )

            body = upsell_template["body"].format(
                name=customer_name,
                product=opportunity.product_purchased,
                upsell_product=opportunity.upsell_product,
            )

            success = await self._send_email(customer_email, subject, body)

            if success:
                opportunity.sent = True
                self.logger.info(f"Upsell email sent to {customer_email}")

            return success

        except Exception as e:
            self.logger.error(f"Error sending upsell: {e}")
            return False

    async def detect_at_risk_customers(
        self,
        customers: List[Any],
        days_inactive: int = 30,
    ) -> List[Any]:
        """Detecta clientes en riesgo de churn."""
        at_risk = []

        for customer in customers:
            # Mock: basaría en fecha última actividad
            days_since_activity = 35  # placeholder

            if days_since_activity > days_inactive and not customer.get("churned"):
                at_risk.append(customer)

        return at_risk

    async def send_win_back_campaign(
        self,
        customers: List[Any],
    ) -> Dict[str, int]:
        """Envía campaña win-back a at-risk customers."""
        try:
            stats = {"sent": 0, "failed": 0}

            for customer in customers:
                # Enviar win-back email
                subject = "Te extrañamos - 20% OFF para volver"
                body = f"Hey {customer.get('name')}, no te hemos visto...\n\nAqui va 20% OFF"

                success = await self._send_email(customer.get("email"), subject, body)

                if success:
                    stats["sent"] += 1
                else:
                    stats["failed"] += 1

            self.logger.info(f"Win-back campaign: {stats['sent']} sent, {stats['failed']} failed")

            return stats

        except Exception as e:
            self.logger.error(f"Error in win-back: {e}")
            return {"sent": 0, "failed": len(customers)}

    async def calculate_lifetime_value(
        self,
        customer_id: str,
        purchases: List[Dict[str, float]],
        churn_probability: float = 0.1,
    ) -> Dict[str, Any]:
        """Calcula lifetime value del cliente."""
        try:
            # LTV = (Avg Purchase Value × Purchase Frequency) / Churn Rate
            total_spent = sum(p.get("amount", 0) for p in purchases)
            avg_purchase = total_spent / len(purchases) if purchases else 0
            purchase_frequency = len(purchases) / 12  # per month (assuming 1 year history)

            ltv = (avg_purchase * purchase_frequency) / (churn_probability or 0.1)

            return {
                "customer_id": customer_id,
                "total_spent": total_spent,
                "avg_purchase": avg_purchase,
                "purchase_frequency": purchase_frequency,
                "ltv_estimate": ltv,
                "retention_score": 1 - churn_probability,
            }

        except Exception as e:
            self.logger.error(f"Error calculating LTV: {e}")
            return {}

    async def _send_email(
        self,
        to: str,
        subject: str,
        body: str,
    ) -> bool:
        """Envía email (mock)."""
        # En prod: usar SendGrid, Mailgun, etc
        self.logger.info(f"Email queued: {to} | {subject}")
        return True


def get_customer_loyalty_engine() -> CustomerLoyaltyEngine:
    return CustomerLoyaltyEngine()
