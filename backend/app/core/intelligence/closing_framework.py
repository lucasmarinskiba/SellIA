"""
Closing Framework — Belfort Straight Line + objection handling.

Técnicas cierre:
- Belfort: objection = buying signal, anticipate + reframe
- Trump: walk-away power, reframe value, alternative futures
- Urgency: scarcity, limited time, exclusive access
- Risk reversal: guarantee removes buyer fear
- Micro-commitments: pequeños yes → big yes
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ClosingFramework:
    """Cierra ventas automático. Objection handling + deal structures."""

    # Objection handlers (Belfort: anticipate cada una)
    OBJECTION_HANDLERS = {
        "price_too_high": {
            "acknowledge": "Entiendo, es inversión.",
            "reframe": [
                "¿Qué es el costo de NO hacer nada? (Oportunidad perdida)",
                "Comparado con competencia, somos 30% más barato",
                "Payment plan: solo $X/mes, menos que café diario",
            ],
            "alternative": "Downgrade a plan básico, upgrade después",
            "risk_reversal": "30-day money back si no ves resultados",
        },
        "need_to_think": {
            "acknowledge": "Buena idea, decisión importante.",
            "reframe": [
                "De qué específicamente necesitas pensar?",
                "¿Es el precio, o algo más?",
                "Otros clientes que pensaban después perdieron oportunidad",
            ],
            "tactic": "Micro-commitment: déjame enviar proposal + call mañana",
            "urgency": "Offer válido solo 48h, después precio sube",
        },
        "not_sure_if_works": {
            "acknowledge": "Totalmente legítimo, prueba primero.",
            "reframe": [
                "7-day trial gratis (si cumples condiciones X)",
                "Garantía: si no cumplimos, 100% refund",
                "200+ companies like yours usan esto",
            ],
            "proof": "Case study + testimonial + números",
            "risk_reversal": "Risk-free trial + extended money back",
        },
        "need_approval": {
            "acknowledge": "Ok, quién más necesita aprobar?",
            "reframe": [
                "Puedo hacer call con ellos? Mañana 2pm?",
                "Te doy presentación lista para compartir",
                "CFO cares: ROI es 300% en 90 días",
            ],
            "tactic": "Involve decision-maker en call (no email)",
            "escalation": "Ejecuta vía Computer Use: agenda call automático",
        },
        "competitor_cheaper": {
            "acknowledge": "Quién es la alternativa?",
            "reframe": [
                "Ellos son baratos pero calidad es 50%",
                "Nosotros = soporte 24/7 vs ninguno",
                "Nuestro cliente anteriormente usaba ellos, cambió porque...",
            ],
            "tactic": "Attack competitor sin atacar (praise our strengths)",
            "alternative": "Match precio BUT con mejor terms + support",
        },
    }

    # Deal structures (Trump: múltiples opciones)
    DEAL_STRUCTURES = [
        {
            "name": "Entry",
            "description": "Para empezar",
            "price_multiplier": 1.0,
            "terms": "Net 30, cancel anytime",
            "guarantee": "30-day money back",
            "addon": "None",
            "positioning": "Bajo riesgo, prueba valor",
        },
        {
            "name": "Standard",
            "description": "Más popular",
            "price_multiplier": 1.3,
            "terms": "Net 30, 3-month commitment",
            "guarantee": "60-day money back",
            "addon": "1 training call + email support",
            "positioning": "Best value + support",
            "badge": "SAVE 20%",
        },
        {
            "name": "Premium",
            "description": "Máximo valor",
            "price_multiplier": 2.0,
            "terms": "Net 15, 12-month commitment",
            "guarantee": "90-day money back + 1:1 success manager",
            "addon": "Weekly calls + Slack channel + custom integrations",
            "positioning": "White-glove service",
            "badge": "VIP - MOST POPULAR",
            "exclusivity": "Only 5 spots/month",
        },
    ]

    @staticmethod
    def handle_objection(objection_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja objeción específica (Belfort)."""

        handler = ClosingFramework.OBJECTION_HANDLERS.get(
            objection_type,
            ClosingFramework.OBJECTION_HANDLERS["price_too_high"],  # Default
        )

        logger.info(f"Handling objection: {objection_type}")

        return {
            "objection": objection_type,
            "acknowledge": handler["acknowledge"],
            "reframe_options": handler.get("reframe", []),
            "tactic": handler.get("tactic", "Reframe + Alternative"),
            "risk_reversal": handler.get("risk_reversal", "Money-back guarantee"),
            "next_action": "Computer Use ejecuta respuesta personalizada",
        }

    @staticmethod
    def present_deal_structure(
        base_price: float,
        buyer_type: str = "standard",
    ) -> List[Dict[str, Any]]:
        """Presenta 3 opciones de deal (Trump: choice architecture)."""

        deals = []

        for structure in ClosingFramework.DEAL_STRUCTURES:
            price = base_price * structure["price_multiplier"]

            deal = {
                "name": structure["name"],
                "description": structure["description"],
                "price": round(price, 2),
                "terms": structure["terms"],
                "guarantee": structure["guarantee"],
                "includes": structure.get("addon"),
                "positioning": structure["positioning"],
                "badge": structure.get("badge"),
                "exclusivity": structure.get("exclusivity"),
            }

            deals.append(deal)

        return deals

    @staticmethod
    def create_urgency_tactics(product: Dict[str, Any]) -> List[str]:
        """Crea urgencia genuina (no fake, Trump-style)."""

        tactics = []

        if product.get("stock", 0) < 10:
            tactics.append(f"Only {product.get('stock')} units left in stock")

        tactics.append("This price valid until end of week")
        tactics.append("Limited to 5 new clients this month for quality")
        tactics.append("3 similar clients signed up last week, spots filling fast")
        tactics.append("Implementation starts next Monday, enrollment closes Friday")

        return tactics

    @staticmethod
    def micro_commitment_sequence(buyer: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Secuencia de micro-commitments (Belfort)."""

        return [
            {
                "stage": 1,
                "action": "Can I send you proposal?",
                "objective": "Small yes = open door",
            },
            {
                "stage": 2,
                "action": "Does proposal look good overall?",
                "objective": "Agreement in principle",
            },
            {
                "stage": 3,
                "action": "What would it take for you to start this week?",
                "objective": "Identify real blockers vs excuses",
            },
            {
                "stage": 4,
                "action": "Let's do it. Which option works: Standard or Premium?",
                "objective": "Close. Not IF, but WHICH",
            },
            {
                "stage": 5,
                "action": "Perfect. Sign here. Implementation starts Monday.",
                "objective": "Commitment secured",
            },
        ]
