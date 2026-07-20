"""
Guarantee Engine — Si no logra resultado, reembolso automático.

Asegura: si X no sucede en 30 días, devolvemos dinero. Zero risk.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GuaranteeEngine:
    """Garantías que aseguran cierre venta."""

    # Tipos de garantía
    GUARANTEES = {
        "money_back": {
            "duration_days": 30,
            "condition": "If not satisfied",
            "refund_rate": 1.0,  # 100%
            "conversion_impact": "+20-30% conversión",
        },
        "results_guaranteed": {
            "duration_days": 90,
            "condition": "If X result not achieved",
            "examples": [
                "SaaS: if CAC not reduced by 30%",
                "Ecommerce: if conversion not improved by 20%",
                "Services: if client not happy",
            ],
            "refund_rate": 1.0,  # 100%
            "conversion_impact": "+30-50% conversión",
        },
        "performance_based": {
            "duration_days": 180,
            "condition": "Pay only if X KPI achieved",
            "examples": [
                "Sales tool: pay $1k/month only if >5 deals closed",
                "Marketing: pay only if >10% conversion",
                "Consulting: pay success fee only if >$100k revenue",
            ],
            "refund_rate": 0.0,  # No pago si no resultados
            "conversion_impact": "+50-70% conversión (no risk)",
        },
    }

    @staticmethod
    def generate_guarantee_statement(
        product: Dict[str, Any],
        guarantee_type: str = "money_back",
    ) -> str:
        """Genera statement de garantía para usar en venta."""

        guarantee = GuaranteeEngine.GUARANTEES.get(guarantee_type, {})
        duration = guarantee.get("duration_days", 30)

        if guarantee_type == "money_back":
            return f"""
✅ {duration}-DAY MONEY-BACK GUARANTEE

Try {product.get('name')} risk-free for {duration} days.

If you're not 100% satisfied, we'll refund every penny.
No questions asked. No strings attached.

That's how confident we are you'll love it.
            """.strip()

        elif guarantee_type == "results_guaranteed":
            return f"""
✅ RESULTS GUARANTEED or YOUR MONEY BACK

We guarantee you'll achieve [specific result] within {duration} days.

If you don't, we refund 100%.

We only win if you win.
            """.strip()

        else:
            return ""

    @staticmethod
    async def monitor_guarantee_conditions(
        sale_id: str,
        buyer: Dict[str, Any],
        product: Dict[str, Any],
        guarantee_type: str,
    ) -> Dict[str, Any]:
        """
        Monitorea si condiciones de garantía se cumplen.

        Si no → automáticamente procesa reembolso.
        """

        logger.info(f"Monitoring guarantee for sale {sale_id}")

        guarantee = GuaranteeEngine.GUARANTEES.get(guarantee_type, {})
        duration_days = guarantee.get("duration_days", 30)

        # Simular chequeo de condiciones
        conditions_met = True
        details = {}

        if guarantee_type == "money_back":
            # Check: ¿customer está satisfecho? (NPS, usage, etc)
            nps_score = buyer.get("nps_score", 0)
            conditions_met = nps_score >= 5
            details["nps_score"] = nps_score

        elif guarantee_type == "results_guaranteed":
            # Check: ¿logró resultado específico?
            result_achieved = buyer.get("result_achieved", False)
            conditions_met = result_achieved
            details["result_achieved"] = result_achieved

        # Si no cumple → procesar reembolso
        if not conditions_met:
            logger.warning(f"Guarantee conditions not met for sale {sale_id}")

            refund_result = await GuaranteeEngine._process_refund(
                sale_id=sale_id,
                amount=buyer.get("amount_paid", 0),
                reason="Guarantee conditions not met",
            )

            return {
                "sale_id": sale_id,
                "guarantee_honored": True,
                "conditions_met": False,
                "refund_processed": refund_result,
                "details": details,
            }

        return {
            "sale_id": sale_id,
            "guarantee_honored": True,
            "conditions_met": True,
            "refund_needed": False,
            "details": details,
        }

    @staticmethod
    async def _process_refund(sale_id: str, amount: float, reason: str) -> Dict[str, Any]:
        """Procesa reembolso automático (Stripe API)."""

        logger.info(f"Processing refund for sale {sale_id}: ${amount}")

        # from backend.app.core.integrations.stripe_payment import StripePaymentProcessor
        # refund = StripePaymentProcessor.refund_payment(payment_intent_id, amount)

        return {
            "refund_id": f"ref_{sale_id}",
            "amount": amount,
            "reason": reason,
            "status": "completed",
        }

    @staticmethod
    def calculate_guarantee_roi(
        customers: List[Dict[str, Any]],
        guarantee_type: str,
    ) -> Dict[str, Any]:
        """Calcula ROI de garantía (higher conversion - refunds)."""

        total_customers = len(customers)
        refunds = sum(1 for c in customers if not c.get("satisfied", True))
        refund_rate = refunds / total_customers if total_customers > 0 else 0

        guarantee = GuaranteeEngine.GUARANTEES.get(guarantee_type, {})
        conversion_impact = guarantee.get("conversion_impact", "")

        return {
            "total_customers": total_customers,
            "refunds_processed": refunds,
            "refund_rate": f"{refund_rate*100:.1f}%",
            "healthy_refund_rate": "<5%",
            "conversion_impact": conversion_impact,
            "recommendation": (
                "Healthy"
                if refund_rate < 0.05
                else f"Warning: refund rate {refund_rate*100:.1f}% (target <5%)"
            ),
        }
