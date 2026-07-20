"""
Negotiation Engine — Trump dealmaking + Belfort closing.

Técnicas:
- Trump: leverage, timing, walk away, brand power, reframe value
- Belfort: Straight Line (objection handling, micro-commitments, psychological close)
- Cialdini: reciprocity, scarcity, authority, social proof, urgency, commitment
- Reframing: repositionar producto según buyer psychology
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class NegotiationStage(str, Enum):
    """Etapas negociación."""
    OPENING = "opening"  # Presentación + rapport
    DISCOVERY = "discovery"  # Entender needs + pain points
    POSITIONING = "positioning"  # Reframe value según buyer
    OBJECTION_HANDLING = "objection_handling"  # Superar objeciones
    CLOSING = "closing"  # Cierre + deal structure
    FOLLOW_UP = "follow_up"  # Micro-commitments + urgency


class NegotiationEngine:
    """Negocia + cierra ventas automático."""

    def __init__(self):
        self.negotiation_log: List[Dict[str, Any]] = []
        self.buyer_profile_cache: Dict[str, Any] = {}

    async def generate_negotiation_strategy(
        self,
        product: Dict[str, Any],
        buyer: Dict[str, Any],
        price: float,
    ) -> Dict[str, Any]:
        """
        Genera estrategia negociación personalizada.

        Inputs: producto, perfil buyer, precio base.
        Output: tácticas específicas + secuencia.
        """

        logger.info(f"Generating negotiation strategy for {buyer.get('email')}")

        # Analizar buyer profile
        buyer_type = self._classify_buyer(buyer)
        pain_points = self._extract_pain_points(buyer, product)
        objections_likely = self._predict_objections(buyer_type, product, price)

        # Estrategia Trump: leverage + timing + value reposition
        leverage_points = self._identify_leverage(product, buyer, price)
        walk_away_signal = self._calculate_walk_away_threshold(buyer, price)

        # Secuencia negociación
        sequence = self._build_negotiation_sequence(
            buyer_type=buyer_type,
            pain_points=pain_points,
            leverage=leverage_points,
            objections=objections_likely,
            price=price,
        )

        return {
            "status": "strategy_generated",
            "buyer_type": buyer_type,
            "pain_points": pain_points,
            "leverage_points": leverage_points,
            "likely_objections": objections_likely,
            "walk_away_threshold": walk_away_signal,
            "sequence": sequence,
        }

    def _classify_buyer(self, buyer: Dict[str, Any]) -> str:
        """Clasifica buyer psychology (impulsor, analítico, autoridad, etc)."""

        behavior = buyer.get("behavior", "")
        budget_level = buyer.get("budget_level", 0)

        if "urgent" in behavior.lower() or "immediate" in behavior.lower():
            return "impulsor"  # Compra rápido, responde urgencia
        elif "research" in behavior.lower() or "compare" in behavior.lower():
            return "analítico"  # Necesita números, comparación, datos
        elif budget_level > 10000:
            return "autoridad"  # Decisor, necesita credibilidad + risk reversal
        else:
            return "pragmático"  # Precio + rapidez

    def _extract_pain_points(self, buyer: Dict[str, Any], product: Dict[str, Any]) -> List[str]:
        """Extrae dolor del buyer (qué problema tienen)."""

        pain_points = []

        # Señales desde buyer profile
        if buyer.get("business_stage") == "survival":
            pain_points.append("cash_flow_crisis")
        if "slow_growth" in buyer.get("description", "").lower():
            pain_points.append("stagnation")
        if buyer.get("team_size", 0) < 5:
            pain_points.append("lack_resources")

        # Producto soluciona?
        product_benefits = product.get("solves", [])
        pain_points.extend(product_benefits)

        return pain_points

    def _predict_objections(
        self,
        buyer_type: str,
        product: Dict[str, Any],
        price: float,
    ) -> List[Dict[str, Any]]:
        """Predice objeciones (Belfort: saber de antemano)."""

        objections = []

        # Análitico: siempre pide proof
        if buyer_type == "analítico":
            objections.append({
                "type": "proof_required",
                "likely": True,
                "handling": "case_study + numbers + testimonials",
            })

        # Precio: siempre aparece
        objections.append({
            "type": "price_objection",
            "likely": True,
            "handling": "value_reframe + payment_plan + comparison",
        })

        # Timing: "voy a pensarlo"
        objections.append({
            "type": "timing_delay",
            "likely": True,
            "handling": "scarcity + micro_commitment + follow_up",
        })

        # Autoridad: "quiero consejo de otro experto"
        if buyer_type == "autoridad":
            objections.append({
                "type": "authority_seek",
                "likely": True,
                "handling": "social_proof + partnerships + guarantee",
            })

        return objections

    def _identify_leverage(
        self,
        product: Dict[str, Any],
        buyer: Dict[str, Any],
        price: float,
    ) -> List[str]:
        """Trump: identifica puntos de leverage en negociación."""

        leverage = []

        # Scarcity: inventory limited?
        if product.get("stock", 0) < 10:
            leverage.append("scarcity_inventory")

        # Time: deal expira soon?
        if buyer.get("deadline_pressure"):
            leverage.append("buyer_time_pressure")

        # Brand: tenemos brand power?
        if product.get("reviews_avg", 0) > 4.5:
            leverage.append("strong_social_proof")

        # Alternatives: competencia weak?
        if product.get("competition_level") == "low":
            leverage.append("weak_alternatives")

        # Walk-away: tenemos otros buyers?
        if buyer.get("urgency_level") == "low":
            leverage.append("we_can_walk_away")

        return leverage

    def _calculate_walk_away_threshold(self, buyer: Dict[str, Any], price: float) -> Dict[str, Any]:
        """Trump: cuándo caminar. Si buyer no valora → walk away."""

        # Si buyer regatea >30% del precio = walk away
        min_acceptable_price = price * 0.7

        # Si buyer pide términos irracionales = walk away
        unreasonable_terms = [
            "90_day_free_trial",
            "no_upfront_payment",
            "monthly_cancel_anytime",
        ]

        return {
            "min_price": min_acceptable_price,
            "unreasonable_terms": unreasonable_terms,
            "walk_away_signal": "If objections > 3 AND concessions < 2 → we walk",
        }

    def _build_negotiation_sequence(
        self,
        buyer_type: str,
        pain_points: List[str],
        leverage: List[str],
        objections: List[Dict[str, Any]],
        price: float,
    ) -> List[Dict[str, Any]]:
        """Construye secuencia de negociación (Belfort Straight Line)."""

        sequence = []

        # 1. OPENING: Rapport + credibilidad
        sequence.append({
            "stage": NegotiationStage.OPENING.value,
            "action": "establish_rapport",
            "content": "Personalizado según buyer type",
            "goal": "Trusted advisor, not salesman",
        })

        # 2. DISCOVERY: Entender needs
        sequence.append({
            "stage": NegotiationStage.DISCOVERY.value,
            "action": "ask_questions",
            "questions": [
                "¿Cuál es tu biggest pain right now?",
                "Si solucionáramos eso, ¿qué cambiaría para ti?",
                "¿Cuánto tiempo llevas batallando con esto?",
            ],
            "goal": "Map pain → product fit",
        })

        # 3. POSITIONING: Reframe value (Trump: repositiona según buyer)
        if buyer_type == "analítico":
            value_pitch = "Numbers + ROI proof + case studies"
        elif buyer_type == "impulsor":
            value_pitch = "Scarcity + urgency + speed to results"
        else:
            value_pitch = "Balanced: value + proof + risk reversal"

        sequence.append({
            "stage": NegotiationStage.POSITIONING.value,
            "action": "reframe_product",
            "pitch": value_pitch,
            "tactics": leverage,
            "goal": "Buyer sees value > price",
        })

        # 4. OBJECTION HANDLING (Belfort: saber de antemano)
        for obj in objections:
            sequence.append({
                "stage": NegotiationStage.OBJECTION_HANDLING.value,
                "objection_type": obj["type"],
                "response": obj["handling"],
                "tactic": "Acknowledge → Reframe → Offer alternative",
            })

        # 5. CLOSING: Deal structure + urgency
        sequence.append({
            "stage": NegotiationStage.CLOSING.value,
            "action": "present_deal",
            "deal_options": [
                {
                    "name": "Standard",
                    "price": price,
                    "terms": "Net 30",
                    "guarantee": "30-day money back",
                },
                {
                    "name": "Payment Plan",
                    "price": price,
                    "terms": "3x installments",
                    "guarantee": "30-day money back per installment",
                },
                {
                    "name": "Premium Bundle",
                    "price": price * 1.5,
                    "terms": "Net 15 + priority support",
                    "guarantee": "60-day money back",
                },
            ],
            "urgency_tactic": "Only 3 spots left this month",
            "goal": "Buyer picks option, commits",
        })

        # 6. MICRO-COMMITMENTS (Belfort: small yes → big yes)
        sequence.append({
            "stage": NegotiationStage.FOLLOW_UP.value,
            "action": "micro_commitments",
            "commitments": [
                "Can I send you a proposal? (Yes = micro-commit)",
                "If numbers look good, you'd be interested? (Yes = stronger)",
                "Can I block time for implementation? (Yes = almost done)",
            ],
            "goal": "Each yes makes next yes easier",
        })

        return sequence

    async def execute_negotiation(
        self,
        buyer: Dict[str, Any],
        product: Dict[str, Any],
        price: float,
        current_stage: str = "opening",
    ) -> Dict[str, Any]:
        """Ejecuta negociación según secuencia (via Computer Use)."""

        logger.info(f"Executing negotiation for {buyer.get('email')} at stage {current_stage}")

        strategy = await self.generate_negotiation_strategy(product, buyer, price)

        # Selecciona acción siguiente de sequence
        sequence = strategy["sequence"]
        current_action = next(
            (s for s in sequence if s["stage"] == current_stage),
            None,
        )

        if not current_action:
            return {"status": "error", "message": f"Unknown stage: {current_stage}"}

        # Computer Use ejecutaría la acción
        result = {
            "status": "executing",
            "stage": current_stage,
            "action": current_action.get("action"),
            "content": current_action,
            "next_stage": self._get_next_stage(current_stage),
        }

        self.negotiation_log.append(result)

        return result

    def _get_next_stage(self, current_stage: str) -> str:
        """Retorna siguiente stage."""

        stages_order = [
            NegotiationStage.OPENING.value,
            NegotiationStage.DISCOVERY.value,
            NegotiationStage.POSITIONING.value,
            NegotiationStage.OBJECTION_HANDLING.value,
            NegotiationStage.CLOSING.value,
            NegotiationStage.FOLLOW_UP.value,
        ]

        try:
            current_idx = stages_order.index(current_stage)
            return stages_order[current_idx + 1]
        except (ValueError, IndexError):
            return NegotiationStage.FOLLOW_UP.value
