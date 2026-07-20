"""
Problem detector — Identifica qué falla en ventas, dónde, por qué.

Inputs: Product data + market analysis + performance metrics.
Output: Lista de problemas específicos + severity + root cause.
"""

import logging
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ProblemSeverity(str, Enum):
    """Severidad problema."""
    CRITICAL = "critical"  # Venta = 0%
    HIGH = "high"  # Venta < 1%
    MEDIUM = "medium"  # Venta 1-3%
    LOW = "low"  # Venta 3-5%


@dataclass
class DetectedProblem:
    """Problema detectado."""
    id: str
    name: str
    severity: ProblemSeverity
    description: str
    root_cause: str
    affected_stage: str  # awareness, consideration, decision, retention
    metrics_affected: List[str]
    business_impact: str


class ProblemDetector:
    """Detecta problemas ventas."""

    @staticmethod
    def analyze(
        product_name: str,
        market_analysis: Dict[str, Any],
        performance_data: Dict[str, Any],
        strategy: Dict[str, Any],
    ) -> List[DetectedProblem]:
        """
        Analiza sistema completo, identifica problemas.

        Checklist de 50+ problemas posibles:
        1. No awareness (nadie sabe del producto)
        2. Wrong positioning (posicionamiento equivocado)
        3. High price (precio demasiado alto vs mercado)
        4. Low quality (producto no cumple promesa)
        5. Bad landing page (UX pobre)
        6. No social proof (sin reviews/testimonios)
        7. Slow response (tarde en responder leads)
        8. Weak CTA (call-to-action débil)
        9. Complex checkout (muchos pasos a pagar)
        10. No email follow-up (no secuencias automation)
        ... etc
        """

        problems = []

        # Problema 1: Awareness bajo
        if performance_data.get("visitors_per_day", 0) < 10:
            problems.append(
                DetectedProblem(
                    id="prob_001",
                    name="Awareness bajo (casi nadie ve producto)",
                    severity=ProblemSeverity.CRITICAL,
                    description="Menos de 10 visitantes/día → No hay tráfico",
                    root_cause="Sin marketing, sin SEO, sin ads, sin social media",
                    affected_stage="awareness",
                    metrics_affected=["visitors", "impressions", "reach"],
                    business_impact="0 conversiones posible si no hay leads",
                )
            )

        # Problema 2: Positioning débil
        positioning = market_analysis.get("recommended_positioning", "")
        if not positioning or positioning == "unknown":
            problems.append(
                DetectedProblem(
                    id="prob_002",
                    name="Posicionamiento no claro",
                    severity=ProblemSeverity.HIGH,
                    description="Cliente no entiende por qué comprar esto vs competencia",
                    root_cause="Falta diferenciación clara, UVP débil o inexistente",
                    affected_stage="consideration",
                    metrics_affected=["bounce_rate", "time_on_page"],
                    business_impact="Clientes van a competencia",
                )
            )

        # Problema 3: Precio problemático
        user_price = performance_data.get("price", 0)
        market_price = market_analysis.get("price_range", {}).get("avg", 0)
        if market_price > 0:
            price_ratio = user_price / market_price
            if price_ratio > 1.5:
                problems.append(
                    DetectedProblem(
                        id="prob_003",
                        name="Precio muy alto vs mercado",
                        severity=ProblemSeverity.HIGH,
                        description=f"Tu precio ${user_price} vs mercado ${market_price} (+50%)",
                        root_cause="Posicionamiento premium pero sin justificación (branding, calidad, servicio)",
                        affected_stage="decision",
                        metrics_affected=["conversion_rate", "cart_abandonment"],
                        business_impact="Clientes ven alternativa más barata",
                    )
                )

        # Problema 4: Conversión baja
        conversion = performance_data.get("conversion_rate", 0)
        if conversion < 1:
            problems.append(
                DetectedProblem(
                    id="prob_004",
                    name="Conversión muy baja (<1%)",
                    severity=ProblemSeverity.CRITICAL,
                    description="De 100 visitantes, menos de 1 compra",
                    root_cause="Landing page débil, UX pobre, CTA no clara, falta social proof, confianza baja",
                    affected_stage="decision",
                    metrics_affected=["conversion_rate", "cpc"],
                    business_impact="Cada visitante cuesta dinero, no convierte",
                )
            )

        # Problema 5: No hay social proof
        reviews = performance_data.get("reviews_count", 0)
        if reviews < 5:
            problems.append(
                DetectedProblem(
                    id="prob_005",
                    name="Falta social proof (sin reviews/testimonios)",
                    severity=ProblemSeverity.HIGH,
                    description=f"Solo {reviews} reviews → Cliente no confía",
                    root_cause="Producto nuevo, no pide reviews a clientes, sin testimonios visibles",
                    affected_stage="consideration",
                    metrics_affected=["conversion_rate", "trust_score"],
                    business_impact="Cliente desconfía, va a competencia con 100+ reviews",
                )
            )

        # Problema 6: Response time lento
        response_time = performance_data.get("avg_response_time_hours", 24)
        if response_time > 4:
            problems.append(
                DetectedProblem(
                    id="prob_006",
                    name="Response time lento",
                    severity=ProblemSeverity.HIGH,
                    description=f"Demora {response_time}h en responder leads",
                    root_cause="Sin automation, respuestas manuales, equipo pequeño o distraído",
                    affected_stage="awareness",
                    metrics_affected=["lead_response_rate", "conversion_rate"],
                    business_impact="Lead muere esperando, compra competencia",
                )
            )

        # Problema 7: Checkout complejo
        checkout_steps = performance_data.get("checkout_steps", 1)
        cart_abandonment = performance_data.get("cart_abandonment_rate", 0)
        if checkout_steps > 5 or cart_abandonment > 50:
            problems.append(
                DetectedProblem(
                    id="prob_007",
                    name="Checkout complejo (abandono alto)",
                    severity=ProblemSeverity.MEDIUM,
                    description=f"{checkout_steps} pasos → {cart_abandonment}% abandono",
                    root_cause="Demasiados campos, crear cuenta forzada, opciones confusas",
                    affected_stage="decision",
                    metrics_affected=["cart_abandonment", "conversion_rate"],
                    business_impact="50%+ carritos sin completar",
                )
            )

        # Problema 8: No hay email follow-up
        email_sequences = performance_data.get("email_sequences_active", 0)
        if email_sequences == 0:
            problems.append(
                DetectedProblem(
                    id="prob_008",
                    name="No hay email automation",
                    severity=ProblemSeverity.HIGH,
                    description="Sin welcome sequences, sin cart abandonment recovery, sin nurture",
                    root_cause="No configuradas, no usa herramientas, falta tiempo",
                    affected_stage="consideration",
                    metrics_affected=["lifetime_value", "repeat_purchase"],
                    business_impact="70% carritos abandonados no recuperados = 30% revenue perdido",
                )
            )

        # Problema 9: Churn alto
        churn = performance_data.get("monthly_churn_rate", 0)
        if churn > 5:
            problems.append(
                DetectedProblem(
                    id="prob_009",
                    name="Churn alto (clientes se van)",
                    severity=ProblemSeverity.HIGH,
                    description=f"{churn}% clientes se van cada mes",
                    root_cause="Producto no cumple promesa, soporte pobre, sin engagement post-venta",
                    affected_stage="retention",
                    metrics_affected=["ltv", "nrr", "repeat_purchase"],
                    business_impact="Tenés que vender 100 nuevos para reemplazar 5 que se van",
                )
            )

        # Problema 10: Competencia abrumadora
        competition = market_analysis.get("competition_level", "Media")
        if competition == "Alta" and strategy.get("segment") != "premium":
            problems.append(
                DetectedProblem(
                    id="prob_010",
                    name="Mercado saturado sin diferenciación",
                    severity=ProblemSeverity.HIGH,
                    description="Alta competencia + posicionamiento genérico",
                    root_cause="Competencia tiene ventaja (brand, price, features)",
                    affected_stage="awareness",
                    metrics_affected=["market_share", "conversion_rate"],
                    business_impact="Invisible en mercado ruidoso",
                )
            )

        logger.info(f"Detectados {len(problems)} problemas para: {product_name}")

        return sorted(problems, key=lambda p: p.severity.value)  # Critical primero


class ProblemSolver:
    """Resuelve problemas usando conocimiento de grandes mentes."""

    @staticmethod
    def solve(problem: DetectedProblem, business_minds: List[str]) -> Dict[str, Any]:
        """
        Resuelve problema usando frameworks de grandes mentes.

        business_minds: lista de mentes a consultar
        (ej: ["buffett", "belfort", "hermozi", "jobs"])
        """

        solutions = []

        # Mapeo problema -> mentes relevantes
        problem_to_minds = {
            "prob_001": ["jobs", "hermozi"],  # Awareness → Jobs (marketing), Hermozi (growth)
            "prob_002": ["jobs", "ries"],  # Positioning → Jobs (clarity), Ries (positioning)
            "prob_003": ["buffett", "jobs"],  # Precio → Buffett (value), Jobs (premium)
            "prob_004": ["hermozi", "belfort"],  # Conversion → Hermozi (CRO), Belfort (closer)
            "prob_005": ["cialdini", "belfort"],  # Social proof → Cialdini, Belfort
            "prob_006": ["cardone", "hermozi"],  # Speed → Cardone (aggressive), Hermozi (velocity)
            "prob_007": ["hermozi", "ux_expert"],  # Checkout → Hermozi (CRO)
            "prob_008": ["hermozi", "belfort"],  # Email → Hermozi (sequences), Belfort (follow-up)
            "prob_009": ["amazon", "jobs"],  # Retention → Amazon (obsession), Jobs (quality)
            "prob_010": ["jobs", "buffett"],  # Competencia → Jobs (differentiate), Buffett (moat)
        }

        minds_to_use = problem_to_minds.get(problem.id, ["hermozi"])

        # Generar soluciones por mente
        if "hermozi" in minds_to_use:
            solutions.append({
                "mind": "Andrew Hermozi (Growth Expert)",
                "framework": "Growth loops + Funnel optimization",
                "solution": f"Optimiza {problem.affected_stage} → A/B test → Double winners → Escala",
                "action": "Identifica lever clave (price, copy, channel) → test → scale",
            })

        if "belfort" in minds_to_use:
            solutions.append({
                "mind": "Jordan Belfort (Closer Master)",
                "framework": "Straight line selling (Rapport → Diagnosis → Reframe → Close)",
                "solution": "Mapa psicológico cliente → Objeción anticipada → Cierre inevitable",
                "action": "Refactor messaging hacia certeza emocional, no lógica",
            })

        if "jobs" in minds_to_use:
            solutions.append({
                "mind": "Steve Jobs (Clarity + Quality)",
                "framework": "Simplify + Obsess quality",
                "solution": "Claridad extrema en propuesta + calidad sin compromiso",
                "action": "Una frase > 10 párrafos. Producto debe brillar solo",
            })

        if "buffett" in minds_to_use:
            solutions.append({
                "mind": "Warren Buffett (Moat + Value)",
                "framework": "Competitive advantage + Fair value",
                "solution": "Define moat único (calidad, servicio, relación) + precio justo",
                "action": "Por qué nadie puede competir? Enfatiza eso",
            })

        if "cialdini" in minds_to_use:
            solutions.append({
                "mind": "Robert Cialdini (Persuasion Science)",
                "framework": "Social proof + Scarcity + Authority + Reciprocity",
                "solution": "Activa levers psicológicos: reviews, urgencia, expertise, generosidad",
                "action": "Muestra reviews, stock limitado, autoridad (premios, clientes famosos), regalo",
            })

        if "cardone" in minds_to_use:
            solutions.append({
                "mind": "Grant Cardone (Aggressive Growth)",
                "framework": "10X thinking + Relentless follow-up",
                "solution": "Objetivo 10x (10k leads, 1k closed) + 10x follow-up",
                "action": "Contact infinito, ofertas constantes, no asumir no",
            })

        return {
            "problem": problem.name,
            "severity": problem.severity.value,
            "root_cause": problem.root_cause,
            "solutions_by_mind": solutions,
            "recommended_priority": 1 if problem.severity == ProblemSeverity.CRITICAL else 2 if problem.severity == ProblemSeverity.HIGH else 3,
        }
