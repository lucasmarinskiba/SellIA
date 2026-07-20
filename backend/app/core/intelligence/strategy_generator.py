"""
Strategy generator — Genera estrategias específicas para producto.

Input: Market analysis + product context + business goals.
Output: Estrategia única, adaptada, evoluciona con performance.
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class StrategyType(str, Enum):
    """Tipos estrategia."""
    GROWTH = "growth"  # Adquisición agresiva
    PREMIUM = "premium"  # Posicionamiento luxury
    BUDGET = "budget"  # Volumen, bajo precio
    HYBRID = "hybrid"  # Mix equilibrado


class StrategyGenerator:
    """Genera estrategias específicas producto."""

    @staticmethod
    def generate_strategy(
        product_name: str,
        category: str,
        market_size: str,
        demand: str,
        competition: str,
        price: float,
        price_avg_market: float,
        business_goals: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Genera estrategia completa para producto.

        Algoritmo:
        1. Detecta segmento (premium/budget/growth)
        2. Selecciona canales por categoria
        3. Define tácticas específicas
        4. Genera roadmap 90 días
        5. Define KPIs success
        """

        logger.info(f"Generando estrategia para: {product_name} ({category})")

        # 1. Detectar segmento
        segment = StrategyGenerator._detect_segment(price, price_avg_market, competition)

        # 2. Seleccionar canales
        channels = StrategyGenerator._select_channels(category, segment, demand)

        # 3. Tácticas específicas
        tactics = StrategyGenerator._generate_tactics(
            category, segment, demand, competition, price
        )

        # 4. Roadmap 90 días
        roadmap = StrategyGenerator._generate_roadmap(segment, channels, tactics)

        # 5. KPIs
        kpis = StrategyGenerator._define_kpis(segment, category, price_avg_market)

        return {
            "product": product_name,
            "segment": segment,
            "recommended_channels": channels,
            "tactics": tactics,
            "roadmap_90days": roadmap,
            "success_kpis": kpis,
            "adaptability_score": 0.8,  # Qué tan flexible es estrategia
            "generated_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def _detect_segment(price: float, market_avg: float, competition: str) -> str:
        """Detecta segmento estrategia."""

        price_ratio = price / market_avg if market_avg > 0 else 1.0

        if price_ratio > 1.3:
            return "premium"  # Premium positioning
        elif price_ratio < 0.7:
            return "budget"  # Budget/volume
        elif competition == "Alta":
            return "growth"  # Crecimiento agresivo si alta competencia
        else:
            return "hybrid"  # Equilibrado

    @staticmethod
    def _select_channels(category: str, segment: str, demand: str) -> Dict[str, str]:
        """Selecciona canales por categoría + segmento."""

        channels = {
            "saas": {
                "primary": "content_marketing_seo",  # Blog, SEO, demos
                "secondary": "paid_ads_google",  # SEM
                "tertiary": "partner_integrations",
            },
            "ecommerce": {
                "primary": "marketplace_mercadolibre",  # MercadoLibre, Amazon
                "secondary": "social_media_instagram",  # Instagram, TikTok
                "tertiary": "email_marketing",
            },
            "servicios": {
                "primary": "LinkedIn_authority",  # LinkedIn, personal brand
                "secondary": "referral_network",  # Referidos
                "tertiary": "email_sequences",
            },
        }

        base = channels.get(category, {"primary": "owned_channels", "secondary": "paid", "tertiary": "organic"})

        # Ajustar por segmento
        if segment == "premium":
            base["primary"] = "personal_outreach"  # High-touch
        elif segment == "budget":
            base["primary"] = "marketplace"  # Volume

        return base

    @staticmethod
    def _generate_tactics(
        category: str, segment: str, demand: str, competition: str, price: float
    ) -> List[Dict[str, Any]]:
        """Genera tácticas específicas."""

        tactics = []

        # Táctica 1: Pricing
        if segment == "premium":
            tactics.append({
                "name": "Premium positioning + value storytelling",
                "action": "Enfatizar quality, exclusivity, resultado",
                "channel": "email + personal demo",
                "timeline": "Día 1-7",
            })
        elif segment == "budget":
            tactics.append({
                "name": "Volume + affordability messaging",
                "action": "Marketplace + ads con 'best price'",
                "channel": "marketplace + google ads",
                "timeline": "Día 1+",
            })

        # Táctica 2: Diferenciación
        tactics.append({
            "name": "Unique value prop (UVP) clara",
            "action": f"Definir qué hace {category} distinto. Ej: 'Único con X'",
            "channel": "landing page + email",
            "timeline": "Día 1-3",
        })

        # Táctica 3: Social proof
        tactics.append({
            "name": "Early reviews + testimonials",
            "action": "Pedir reviews a primeros 10 customers (ofreciendo descuento)",
            "channel": "producto + email",
            "timeline": "Día 14+",
        })

        # Táctica 4: Content si demand alto
        if demand == "Alto":
            tactics.append({
                "name": "Educational content marketing",
                "action": "Blog posts, videos explicativos",
                "channel": "blog + youtube",
                "timeline": "Semana 2+",
            })

        # Táctica 5: Automation
        tactics.append({
            "name": "Email sequences automáticas",
            "action": "Welcome (día 0) → Value (día 1) → Offer (día 2)",
            "channel": "email",
            "timeline": "Día 1+",
        })

        return tactics[:4]  # Top 4

    @staticmethod
    def _generate_roadmap(segment: str, channels: Dict[str, str], tactics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Genera roadmap 90 días."""

        return [
            {
                "phase": "Semanas 1-2: Setup",
                "focus": "Landing page, email sequences, social proof setup",
                "goal": "Sistema listo, primeras 10 conversiones",
            },
            {
                "phase": "Semanas 3-4: Early traction",
                "focus": "Ejecutar email sequences, recolectar reviews",
                "goal": "50 conversiones, 3-5 reviews",
            },
            {
                "phase": "Semanas 5-8: Optimization",
                "focus": "A/B testing, analyze what works, double down winners",
                "goal": "100+ conversiones, 20+ reviews, clear winners en channels",
            },
            {
                "phase": "Semanas 9-12: Scale",
                "focus": "Escalar canales winners, adicionales channels",
                "goal": "300+ conversiones, 50+ reviews, revenue climb 2-3x",
            },
        ]

    @staticmethod
    def _define_kpis(segment: str, category: str, market_price_avg: float) -> Dict[str, Any]:
        """Define KPIs para medir éxito."""

        kpis = {
            "conversion_target": "2-5%" if segment == "premium" else "5-10%",
            "mrr_target": "$1000-2000" if segment == "budget" else "$5000+",
            "cac_payback": "6-12 meses" if segment == "premium" else "1-3 meses",
            "customer_reviews": "Mín 10 reviews, avg 4.5+/5",
            "email_engagement": "25%+ open rate, 5%+ click-through",
            "content_reach": "1000+ monthly views" if category == "servicios" else "N/A",
        }

        return kpis


class StrategyOptimizer:
    """Optimiza estrategia basada en performance real."""

    @staticmethod
    def optimize(
        current_strategy: Dict[str, Any],
        performance_data: Dict[str, Any],
        iteration: int = 1,
    ) -> Dict[str, Any]:
        """
        Optimiza estrategia según resultados.

        Performance data: conversion %, revenue, reviews, customer feedback.
        """

        logger.info(f"Optimizando estrategia, iteración {iteration}")

        changes = []

        # Analizar conversion rate
        conversion = performance_data.get("conversion_rate", 0)
        if conversion < 1:
            changes.append({
                "issue": "Conversion rate bajo (<1%)",
                "recommendation": "Revisar landing page UX, CTA clarity, pricing",
                "action": "A/B test headline + CTA copy",
            })

        # Analizar channel performance
        channel_perf = performance_data.get("channel_performance", {})
        worst_channel = min(channel_perf, key=channel_perf.get) if channel_perf else None
        if worst_channel and channel_perf[worst_channel] < 0.5:
            changes.append({
                "issue": f"Channel {worst_channel} underperforming",
                "recommendation": "Pause or pivot away from underperforming channel",
                "action": f"Redirect budget from {worst_channel} to top performer",
            })

        # Analizar reviews
        reviews_avg = performance_data.get("review_score_avg", 0)
        if reviews_avg < 4.0:
            changes.append({
                "issue": "Customer satisfaction low (<4.0/5)",
                "recommendation": "Onboarding, support, product improvements needed",
                "action": "Conduct customer interviews to understand pain points",
            })

        optimized_strategy = current_strategy.copy()
        optimized_strategy["optimization_iteration"] = iteration
        optimized_strategy["changes_recommended"] = changes
        optimized_strategy["optimized_at"] = datetime.utcnow().isoformat()

        return optimized_strategy
