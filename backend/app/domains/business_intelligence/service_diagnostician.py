"""Phase 12: Product/service diagnostics and competitive analysis."""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PMFStatus(str, Enum):
    STRONG_PRODUCT_STRONG_MARKETING = "strong_product_strong_marketing"
    STRONG_PRODUCT_WEAK_MARKETING = "strong_product_weak_marketing"
    WEAK_PRODUCT_STRONG_MARKETING = "weak_product_strong_marketing"
    WEAK_PRODUCT_WEAK_MARKETING = "weak_product_weak_marketing"
    UNCLEAR = "unclear"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Improvement:
    issue: str
    impact: str
    fix: str
    effort_level: str  # low, medium, high
    time_to_fix_days: int
    expected_lead_increase_percent: int
    priority: Severity = Severity.MEDIUM


@dataclass
class Diagnosis:
    pmf_status: PMFStatus
    pmf_score: float  # 0-1
    product_quality_score: float  # 0-1
    marketing_quality_score: float  # 0-1
    visibility_score: float  # 0-1
    positioning_score: float  # 0-1

    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    threats: List[str] = field(default_factory=list)

    improvements: List[Improvement] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)

    estimated_revenue_impact_30days: str = "moderate"
    estimated_revenue_impact_90days: str = "significant"


class ServiceDiagnostician:
    """Diagnose product-market fit and service quality"""

    def diagnose(self, business_description: str, business_model: str = "") -> Diagnosis:
        """Analyze product-market fit"""

        # Mock analysis - en producción scrapeamos reviews, competencia, etc
        pmf_score = 0.7

        diagnosis = Diagnosis(
            pmf_status=PMFStatus.STRONG_PRODUCT_WEAK_MARKETING,
            pmf_score=pmf_score,
            product_quality_score=0.8,
            marketing_quality_score=0.4,
            visibility_score=0.3,
            positioning_score=0.5,

            strengths=[
                "Producto con buena reputación",
                "Precio competitivo",
                "Atención al cliente responsiva",
                "Experiencia probada en el mercado"
            ],

            weaknesses=[
                "Visibilidad muy baja en Internet",
                "No aparece en Google Maps",
                "Comunicación confusa/genérica",
                "Público objetivo mal definido",
                "No tiene presencia en redes sociales",
                "Website desactualizado o inexistente"
            ],

            opportunities=[
                "Expandir a nuevos canales de venta",
                "Mejorar presencia online",
                "Crear comunidad de clientes",
                "Ofrecer servicios complementarios",
                "Automatizar follow-ups"
            ],

            threats=[
                "Competencia agresiva en redes",
                "Cambios en algoritmos de búsqueda",
                "Nuevos competidores mejor posicionados",
                "Cambios en preferencias de clientes"
            ],

            improvements=[
                Improvement(
                    issue="No apareces en Google Maps",
                    impact="Pierdes 60% de clientes que buscan localmente",
                    fix="Crear perfil GMB, solicitar 20+ reviews, posts regulares",
                    effort_level="low",
                    time_to_fix_days=3,
                    expected_lead_increase_percent=40,
                    priority=Severity.CRITICAL
                ),
                Improvement(
                    issue="Website desactualizado o no existe",
                    impact="Pierdes credibilidad, no rankeas en Google",
                    fix="Crear website moderno con SEO básico",
                    effort_level="medium",
                    time_to_fix_days=14,
                    expected_lead_increase_percent=30,
                    priority=Severity.HIGH
                ),
                Improvement(
                    issue="Copy genérico/confuso",
                    impact="Visitantes no entienden tu valor",
                    fix="Reescribir proposición de valor + copy por página",
                    effort_level="low",
                    time_to_fix_days=2,
                    expected_lead_increase_percent=25,
                    priority=Severity.HIGH
                ),
                Improvement(
                    issue="No tienes presencia en redes",
                    impact="Pierdes leads de audiencias jóvenes",
                    fix="Setup Instagram + 4 posts/semana + engagement diario",
                    effort_level="low",
                    time_to_fix_days=1,
                    expected_lead_increase_percent=15,
                    priority=Severity.MEDIUM
                ),
                Improvement(
                    issue="No recopilas reviews",
                    impact="Bajos ratings, baja confianza",
                    fix="Sistema automático para solicitar reviews",
                    effort_level="low",
                    time_to_fix_days=1,
                    expected_lead_increase_percent=20,
                    priority=Severity.MEDIUM
                )
            ],

            recommended_actions=[
                "Semana 1: Crear/Optimizar perfil Google Maps + WhatsApp Business",
                "Semana 2: Reescribir copy + crear landing page básica",
                "Semana 3: Setup Instagram + content calendar",
                "Semana 4: Implementar auto-follow-up con agentes IA",
                "Mes 2: Expandir a otros canales relevantes (LinkedIn, TikTok, etc)"
            ],

            estimated_revenue_impact_30days="moderate",
            estimated_revenue_impact_90days="significant"
        )

        logger.info(f"Diagnosis complete. PMF Score: {pmf_score}")
        return diagnosis


class CompetitiveAnalyzer:
    """Analyze competitive landscape"""

    def analyze(self, business_name: str, industry: str = "") -> Dict[str, Any]:
        """Analyze competitors"""

        # Mock competitive analysis
        return {
            "market_position": "COMPETITIVE",
            "competitor_count": 5,
            "market_concentration": "moderate",
            "barriers_to_entry": "low",
            "differentiation_opportunities": [
                "Mejor atención al cliente",
                "Proceso más rápido",
                "Precio más competitivo",
                "Mejor presencia online",
                "Más opciones de personalización"
            ],
            "competitor_pricing_avg": 1200,
            "your_pricing_position": "average",
            "pricing_recommendation": "Competitive or slight premium",
            "gaps_in_market": [
                "Falta servicio 24/7",
                "No ofrecen garantía extendida",
                "Mala atención al cliente",
                "Presencia online débil"
            ],
            "market_size": "estimated 10,000+ potential customers in area",
            "growth_rate": "moderate (5-10% annually)"
        }
