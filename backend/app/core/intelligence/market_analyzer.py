"""
Market analyzer — Investigar mercado, competencia, tendencias.

Input: producto/servicio del usuario.
Output: Análisis competencia, precios, demanda, tendencias, oportunidades.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MarketAnalysis:
    """Resultado análisis mercado."""
    product: str
    category: str
    market_size: str  # Pequeño, Medio, Grande
    demand_level: str  # Bajo, Medio, Alto
    competition_level: str  # Baja, Media, Alta
    price_range: Dict[str, float]  # min, max, avg
    top_competitors: List[Dict[str, Any]]
    market_trends: List[str]
    opportunities: List[str]
    threats: List[str]
    recommended_positioning: str
    confidence: float  # 0-1


class MarketAnalyzer:
    """Analiza mercado para producto dado."""

    @staticmethod
    def analyze(product_name: str, product_description: str, price: float) -> MarketAnalysis:
        """
        Analiza mercado del producto.

        En producción:
        - Conectar a APIs reales (SimilarWeb, Shopify stores, Amazon, etc)
        - Scrape competencia (nombre, precio, reviews, posicionamiento)
        - Google Trends API (demanda, seasonality)
        - Reddit/Twitter sentiment analysis
        - SEO difficulty (competencia content marketing)
        """

        logger.info(f"Analizando mercado para: {product_name} (${price})")

        # Mock analysis basado en keywords producto
        category = MarketAnalyzer._detect_category(product_description)
        market_size = MarketAnalyzer._estimate_market_size(category, product_description)
        demand = MarketAnalyzer._estimate_demand(product_description)
        competition = MarketAnalyzer._estimate_competition(category)
        price_range = MarketAnalyzer._estimate_price_range(category, price)

        # Competidores simulados
        competitors = [
            {
                "name": "Competitor A",
                "price": price_range["avg"] * 0.9,
                "positioning": "Premium quality",
                "reviews": 4.5,
                "review_count": 1200,
            },
            {
                "name": "Competitor B",
                "price": price_range["avg"] * 1.1,
                "positioning": "Budget friendly",
                "reviews": 4.2,
                "review_count": 800,
            },
        ]

        # Trends por categoría
        trends = MarketAnalyzer._get_trends(category)

        # Oportunidades
        opportunities = MarketAnalyzer._identify_opportunities(
            category, demand, competition, price
        )

        # Threats
        threats = MarketAnalyzer._identify_threats(category, competition)

        # Posicionamiento recomendado
        positioning = MarketAnalyzer._recommend_positioning(
            category, competition, price_range, price
        )

        return MarketAnalysis(
            product=product_name,
            category=category,
            market_size=market_size,
            demand_level=demand,
            competition_level=competition,
            price_range=price_range,
            top_competitors=competitors,
            market_trends=trends,
            opportunities=opportunities,
            threats=threats,
            recommended_positioning=positioning,
            confidence=0.75,
        )

    @staticmethod
    def _detect_category(description: str) -> str:
        """Detecta categoría producto."""
        keywords = {
            "saas": ["software", "app", "cloud", "web", "platform"],
            "ecommerce": ["tienda", "producto", "shop", "venta", "ropa", "electrónica"],
            "servicios": ["consultoría", "consultor", "agencia", "diseño", "marketing"],
            "bienes_raíces": ["casa", "departamento", "propiedad", "inmueble"],
            "educación": ["curso", "coaching", "formación", "educación", "universidad"],
        }

        desc_lower = description.lower()
        for category, kws in keywords.items():
            if any(kw in desc_lower for kw in kws):
                return category

        return "general"

    @staticmethod
    def _estimate_market_size(category: str, description: str) -> str:
        """Estima tamaño mercado."""
        # Mock: basado en categoría
        market_sizes = {
            "saas": "Grande",
            "ecommerce": "Grande",
            "servicios": "Medio",
            "bienes_raíces": "Grande",
            "educación": "Medio",
        }
        return market_sizes.get(category, "Medio")

    @staticmethod
    def _estimate_demand(description: str) -> str:
        """Estima nivel demanda."""
        # Mock: basado en keywords relevancia
        high_demand_kws = ["urgente", "rápido", "problema", "solución", "necesario"]
        if any(kw in description.lower() for kw in high_demand_kws):
            return "Alto"
        return "Medio"

    @staticmethod
    def _estimate_competition(category: str) -> str:
        """Estima nivel competencia."""
        high_comp = {"saas": "Alta", "ecommerce": "Alta", "servicios": "Media"}
        return high_comp.get(category, "Media")

    @staticmethod
    def _estimate_price_range(category: str, user_price: float) -> Dict[str, float]:
        """Estima rango de precios mercado."""
        # Mock: basado en categoría
        ranges = {
            "saas": {"min": 29, "max": 999},
            "ecommerce": {"min": 10, "max": 500},
            "servicios": {"min": 50, "max": 2000},
            "bienes_raíces": {"min": 50000, "max": 1000000},
        }

        range_data = ranges.get(category, {"min": 50, "max": 1000})
        avg = (range_data["min"] + range_data["max"]) / 2

        return {
            "min": range_data["min"],
            "max": range_data["max"],
            "avg": avg,
            "user_price": user_price,
            "vs_avg": "competitivo" if abs(user_price - avg) / avg < 0.2 else "premium" if user_price > avg else "budget",
        }

    @staticmethod
    def _get_trends(category: str) -> List[str]:
        """Tendencias mercado."""
        trends = {
            "saas": [
                "AI/ML integration rising",
                "Compliance automation (SOC2, GDPR)",
                "Usage-based pricing gaining traction",
            ],
            "ecommerce": [
                "Free shipping expectations (competitive)",
                "Video product demos critical",
                "Same-day delivery in major cities",
            ],
            "servicios": [
                "Hourly → fixed-price projects",
                "Personal branding (founder authority)",
                "White-label partnerships",
            ],
        }
        return trends.get(category, ["Market evolving rapidly"])

    @staticmethod
    def _identify_opportunities(
        category: str, demand: str, competition: str, price: float
    ) -> List[str]:
        """Oportunidades para usuario."""
        opps = []

        if competition == "Alta":
            opps.append("Diferenciación clara necesaria (posicionamiento único)")

        if demand == "Alto":
            opps.append("Demanda alta → escalar rápido, antes que competencia")

        if category == "saas":
            opps.append("Free trial + freemium model (viral acquisition)")

        if category == "ecommerce":
            opps.append("User-generated content (reviews, testimonials, video)")

        if category == "servicios":
            opps.append("Authority building (LinkedIn, webinars, case studies)")

        opps.append("Early customer feedback → evolucionar rápido")

        return opps[:3]  # Top 3

    @staticmethod
    def _identify_threats(category: str, competition: str) -> List[str]:
        """Threats."""
        threats = []

        if competition == "Alta":
            threats.append("Established players con brand/resources")
            threats.append("Price wars posible si differentiation unclear")

        if category in ["saas", "ecommerce"]:
            threats.append("Customer acquisition cost rising (ad inflation)")

        threats.append("Market saturation if product not unique")

        return threats[:2]

    @staticmethod
    def _recommend_positioning(
        category: str, competition: str, price_range: Dict[str, float], user_price: float
    ) -> str:
        """Recomendación posicionamiento."""

        vs_comp = price_range["vs_avg"]

        if competition == "Alta":
            if vs_comp == "competitivo":
                return "Diferenciación por features/quality (premium quality at competitive price)"
            elif vs_comp == "premium":
                return "Posicionamiento luxury/enterprise (exclusivity, white-glove service)"
            else:
                return "Posicionamiento budget-friendly (value + volume)"
        else:
            return "Capturable premium positioning (new market, less competition)"


class MarketComparator:
    """Compara estrategias entre productos/competidores."""

    @staticmethod
    def compare_strategies(
        user_product_analysis: MarketAnalysis, competitor_analysis: MarketAnalysis
    ) -> Dict[str, Any]:
        """Compara estrategias vs competidor."""

        return {
            "user_positioning": user_product_analysis.recommended_positioning,
            "competitor_positioning": competitor_analysis.recommended_positioning,
            "positioning_gap": "Diferenciación posible" if user_product_analysis.recommended_positioning != competitor_analysis.recommended_positioning else "Competing on same positioning",
            "price_gap_pct": (
                (user_product_analysis.price_range["user_price"] - competitor_analysis.price_range["avg"])
                / competitor_analysis.price_range["avg"]
                * 100
            ),
            "recommendation": "Diferenciarse o cambiar positioning" if user_product_analysis.recommended_positioning == competitor_analysis.recommended_positioning else "Posicionamiento claro diferente",
        }
