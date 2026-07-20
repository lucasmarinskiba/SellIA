"""
Sales executor — Ejecuta venta completa end-to-end (lead → close → deliver → retain).

5 fases:
1. Capture: Atrae lead
2. Nurture: Convence
3. Close: Cierra
4. Deliver: Cumple promesa
5. Retain: Mantiene + upsell
"""

import logging
from typing import Dict, List, Any
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class SalesPhase(str, Enum):
    """Fase del ciclo venta."""
    CAPTURE = "capture"  # Atrae leads
    NURTURE = "nurture"  # Convence
    CLOSE = "close"  # Cierra
    DELIVER = "deliver"  # Cumple
    RETAIN = "retain"  # Mantiene


class SalesExecutor:
    """Ejecuta venta completa."""

    @staticmethod
    def build_complete_sales_plan(
        product: str,
        category: str,
        market_analysis: Dict[str, Any],
        strategy: Dict[str, Any],
        problems: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Construye plan venta completo 90 días.

        Integra: Market analysis + Strategy + Problems + Solutions + Minds.
        """

        plan = {
            "product": product,
            "phase_1_capture": SalesExecutor._phase_capture(category, strategy),
            "phase_2_nurture": SalesExecutor._phase_nurture(strategy, problems),
            "phase_3_close": SalesExecutor._phase_close(strategy),
            "phase_4_deliver": SalesExecutor._phase_deliver(product, category),
            "phase_5_retain": SalesExecutor._phase_retain(product),
            "kpis_by_phase": SalesExecutor._define_kpis(),
            "timeline": "90 días",
        }

        return plan

    @staticmethod
    def _phase_capture(category: str, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Fase 1: Captura de leads (Semanas 1-2)."""

        channels = strategy.get("recommended_channels", {})

        return {
            "phase": "Capture (Weeks 1-2)",
            "goal": "100+ qualified leads",
            "tactics": [
                {
                    "channel": channels.get("primary", "email"),
                    "action": "Launch campaign primario",
                    "details": "Landing page + email list + ads (si budget)",
                },
                {
                    "channel": "social_media",
                    "action": "Presencia + organic reach",
                    "details": "Post diarios, engage comentarios, build audience",
                },
                {
                    "channel": "partnerships",
                    "action": "Referral network",
                    "details": "Contacta 20 partners complementarios, pide referidos",
                },
            ],
            "success_metrics": {
                "leads_captured": "100+",
                "cost_per_lead": "<$10" if category == "ecommerce" else "<$50",
                "lead_quality": "35%+ qualified (real intent)",
            },
        }

    @staticmethod
    def _phase_nurture(strategy: Dict[str, Any], problems: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fase 2: Nutrición de leads (Semanas 3-5)."""

        return {
            "phase": "Nurture (Weeks 3-5)",
            "goal": "50% leads → consideration stage",
            "tactics": [
                {
                    "tactic": "Email sequences",
                    "action": "Welcome (day 0) → Value (day 1) → Objection (day 3) → Offer (day 5)",
                    "details": "Educate, build trust, anticipate doubts",
                },
                {
                    "tactic": "Social proof",
                    "action": "Publicar testimonios, reviews, case studies",
                    "details": "Cialdini: si 10+ reviews, +25% conversión",
                },
                {
                    "tactic": "Personalized outreach",
                    "action": "1-on-1 follow-up a top leads (de la lista qualified)",
                    "details": "Call o email personalizado, directamente el vendedor",
                },
                {
                    "tactic": "Handle objections",
                    "action": "Anticipate + responde objecciones comunes",
                    "details": "Si problema 'precio alto' → responde con value prop clara",
                },
            ],
            "success_metrics": {
                "email_open_rate": "25%+",
                "click_through": "5%+",
                "lead_advancement": "50% → consideration",
            },
        }

    @staticmethod
    def _phase_close(strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Fase 3: Cierre (Semanas 6-8)."""

        segment = strategy.get("segment", "growth")

        return {
            "phase": "Close (Weeks 6-8)",
            "goal": "25-50% leads → customers",
            "segment_strategy": {
                "premium": {
                    "approach": "High-touch, personal demo, relationship",
                    "closer": "Belfort (Straight line) + Jobs (clarity)",
                    "steps": "1-on-1 call → Demo → Objection handling → Signature",
                },
                "budget": {
                    "approach": "Urgency + scarcity, one-click checkout",
                    "closer": "Cardone (aggressive) + Hermozi (CRO)",
                    "steps": "Email CTA → Landing page → Checkout (1-step)",
                },
                "growth": {
                    "approach": "Mix: email + personal follow-up, trial free",
                    "closer": "Hermozi (optimization) + Belfort (conviction)",
                    "steps": "Email campaign → Qualified call → Trial → Conversion",
                },
            },
            "tactics": [
                {
                    "tactic": "Trial / Demo / POC",
                    "action": "Ofrecer acceso limitado (trial free 14d, demo, pilot)",
                    "details": "Reduce risk perception, let them experience",
                },
                {
                    "tactic": "Scarcity + Urgency",
                    "action": "Limited time offer (expires 48h), limited stock",
                    "details": "Cialdini: crea decisión urgente",
                },
                {
                    "tactic": "Final objection handling",
                    "action": "Belfort technique: 'Qué te detiene de decidir HOY?'",
                    "details": "Surface final objection, resolve, cierre",
                },
                {
                    "tactic": "Guarantee",
                    "action": "Ofrecer garantía (money-back 30d, satisfaction guarantee)",
                    "details": "Risk reversal: tú asumes riesgo, no cliente",
                },
            ],
            "success_metrics": {
                "conversion_rate": "5-10%",
                "average_deal_size": "Según precio",
                "sales_cycle": "5-7 días",
            },
        }

    @staticmethod
    def _phase_deliver(product: str, category: str) -> Dict[str, Any]:
        """Fase 4: Entrega (Semana 9)."""

        return {
            "phase": "Deliver (Week 9)",
            "goal": "100% clientes satisfechos, Aha moment en día 1-7",
            "tactics": [
                {
                    "tactic": "Onboarding perfecto",
                    "action": "Welcome email + tutorial video + check-in call",
                    "details": "Day 1: email + video. Day 3: check-in. Day 7: success metric hit?",
                },
                {
                    "tactic": "Aha moment",
                    "action": "Cliente debe ver valor en día 7",
                    "details": "Si aha moment = 90% retención. Sin = 50%+",
                },
                {
                    "tactic": "Quality assurance",
                    "action": "Cumple 100% promesa del marketing",
                    "details": "Si marketing dice 'x resultado', producto debe entregar 'x'",
                },
                {
                    "tactic": "Support activo",
                    "action": "Respuesta <2h a queries, proactivo help",
                    "details": "No esperar cliente pida. Ofrecer ayuda.",
                },
            ],
            "success_metrics": {
                "nps_score": "50+",
                "day_7_aha_rate": "80%+",
                "support_satisfaction": "95%+",
            },
        }

    @staticmethod
    def _phase_retain(product: str) -> Dict[str, Any]:
        """Fase 5: Retención + Growth (Semanas 10-12)."""

        return {
            "phase": "Retain & Grow (Weeks 10-12+)",
            "goal": "Churn <2%, LTV 3-5x CAC, upsell 30%",
            "tactics": [
                {
                    "tactic": "Engagement loops",
                    "action": "Email semanal (tips, updates, showcase customer wins)",
                    "details": "Mantiene top-of-mind, builds community",
                },
                {
                    "tactic": "QBR (Quarterly Business Review)",
                    "action": "Call mensual con top customers, review ROI",
                    "details": "Asegura satisfacción, identifica upsell",
                },
                {
                    "tactic": "Upsell / Cross-sell",
                    "action": "Ofrecer upgrade (Pro tier, add-ons, complementarios)",
                    "details": "70%+ usage de feature → eligible upsell",
                },
                {
                    "tactic": "Referral program",
                    "action": "Cliente satisfecho refiere 3+ amigos = comisión",
                    "details": "Cardone: referidos son CAC $0, highest quality",
                },
                {
                    "tactic": "Win-back",
                    "action": "Alert si customer inactivo >30d, outreach immediatamente",
                    "details": "Salva antes de churn, ofrece win-back incentivo",
                },
            ],
            "success_metrics": {
                "churn_rate": "<2%/month",
                "nrr": ">100%",
                "customer_ltv": "3-5x CAC",
                "referral_rate": "20%+ customers refieren",
            },
        }

    @staticmethod
    def _define_kpis() -> Dict[str, Any]:
        """Define KPIs por fase."""

        return {
            "capture": {
                "leads": "100+",
                "cpl": "<$10-50",
                "qualification_rate": "35%+",
            },
            "nurture": {
                "email_open": "25%+",
                "click_through": "5%+",
                "advancement": "50%",
            },
            "close": {
                "conversion": "5-10%",
                "deal_size": "Según precio",
                "cycle": "5-7 días",
            },
            "deliver": {
                "nps": "50+",
                "aha_rate": "80%+",
                "support_satisfaction": "95%+",
            },
            "retain": {
                "churn": "<2%",
                "nrr": ">100%",
                "ltv": "3-5x",
            },
            "overall_business": {
                "mrr": "Target depends on CAC + LTV",
                "payback_period": "<6 months",
                "profit_margin": ">30% after COGS",
            },
        }
