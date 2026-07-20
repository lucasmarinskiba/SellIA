"""
Intelligence API — Market analysis + Strategy generation + Optimization.

Endpoints:
- POST /analyze-market: Analiza mercado producto
- POST /generate-strategy: Genera estrategia
- POST /optimize-strategy: Optimiza según performance
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging

from backend.app.core.intelligence.market_analyzer import MarketAnalyzer, MarketAnalysis
from backend.app.core.intelligence.strategy_generator import StrategyGenerator, StrategyOptimizer

router = APIRouter(prefix="/api/v1/intelligence", tags=["intelligence"])
logger = logging.getLogger(__name__)


class ProductInput(BaseModel):
    """Información producto para análisis."""
    product_name: str
    product_description: str
    price: float
    business_goals: Optional[List[str]] = None


class PerformanceInput(BaseModel):
    """Datos performance para optimización."""
    conversion_rate: float
    mrr: float
    reviews_avg: float
    channel_performance: Dict[str, float]
    customer_feedback: Optional[str] = None


class IntelligenceReport(BaseModel):
    """Reporte completo inteligencia."""
    market_analysis: Dict[str, Any]
    strategy: Dict[str, Any]
    recommendations: List[str]
    next_actions: List[str]


@router.post("/analyze-market", tags=["market"])
async def analyze_market(product: ProductInput):
    """
    Analiza mercado producto.

    Retorna:
    - Market size, demand, competition
    - Precio range, competidores
    - Trends, opportunities, threats
    - Posicionamiento recomendado
    """

    try:
        logger.info(f"Analizando mercado para: {product.product_name}")

        analysis = MarketAnalyzer.analyze(
            product_name=product.product_name,
            product_description=product.product_description,
            price=product.price,
        )

        # Convertir a dict
        analysis_dict = {
            "product": analysis.product,
            "category": analysis.category,
            "market_size": analysis.market_size,
            "demand_level": analysis.demand_level,
            "competition_level": analysis.competition_level,
            "price_range": analysis.price_range,
            "top_competitors": analysis.top_competitors,
            "market_trends": analysis.market_trends,
            "opportunities": analysis.opportunities,
            "threats": analysis.threats,
            "recommended_positioning": analysis.recommended_positioning,
            "confidence": analysis.confidence,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

        return {
            "status": "analyzed",
            "analysis": analysis_dict,
        }

    except Exception as e:
        logger.error(f"Error analizando mercado: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-strategy", tags=["strategy"])
async def generate_strategy(product: ProductInput):
    """
    Genera estrategia específica producto.

    Retorna:
    - Segment (premium/budget/growth/hybrid)
    - Canales recomendados
    - Tácticas 90 días
    - KPIs success
    """

    try:
        logger.info(f"Generando estrategia para: {product.product_name}")

        # Primero analizar mercado
        analysis = MarketAnalyzer.analyze(
            product_name=product.product_name,
            product_description=product.product_description,
            price=product.price,
        )

        # Generar estrategia
        strategy = StrategyGenerator.generate_strategy(
            product_name=product.product_name,
            category=analysis.category,
            market_size=analysis.market_size,
            demand=analysis.demand_level,
            competition=analysis.competition_level,
            price=product.price,
            price_avg_market=analysis.price_range["avg"],
            business_goals=product.business_goals,
        )

        # Generar recommendations
        recommendations = [
            f"Posicionamiento: {analysis.recommended_positioning}",
            f"Segmento: {strategy['segment']}",
            f"Canales primarios: {strategy['recommended_channels'].get('primary', 'N/A')}",
        ] + analysis.opportunities

        next_actions = [
            "1. Validar posicionamiento con 5-10 clientes potenciales",
            "2. Crear landing page con value prop clara",
            "3. Configurar email sequences (welcome, nurture, offer)",
            "4. Lanzar en canal primario",
            "5. Trackear conversion rate diariamente",
        ]

        return {
            "status": "strategy_generated",
            "market_analysis": {
                "category": analysis.category,
                "demand": analysis.demand_level,
                "competition": analysis.competition_level,
            },
            "strategy": strategy,
            "recommendations": recommendations,
            "next_actions": next_actions,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error generando estrategia: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-strategy", tags=["optimization"])
async def optimize_strategy(
    product_name: str,
    current_strategy: Dict[str, Any],
    performance: PerformanceInput,
    iteration: int = 1,
):
    """
    Optimiza estrategia basada en performance.

    Input: Estrategia actual + datos performance real.
    Output: Cambios recomendados, nuevas tácticas, escalación plan.
    """

    try:
        logger.info(f"Optimizando estrategia para: {product_name}, iteración {iteration}")

        performance_data = {
            "conversion_rate": performance.conversion_rate,
            "mrr": performance.mrr,
            "review_score_avg": performance.reviews_avg,
            "channel_performance": performance.channel_performance,
        }

        optimized = StrategyOptimizer.optimize(
            current_strategy=current_strategy,
            performance_data=performance_data,
            iteration=iteration,
        )

        # Generar escalation plan
        if performance.mrr > 5000:
            escalation = "Escalar: duplicar ad spend, expand a 2do canal"
        elif performance.mrr > 1000:
            escalation = "Crecer: optimizar conversiones, reducir CAC"
        else:
            escalation = "Validar: revisar posicionamiento, mejora UX"

        return {
            "status": "optimized",
            "optimization_iteration": iteration,
            "current_performance": {
                "conversion_rate": f"{performance.conversion_rate * 100:.1f}%",
                "mrr": f"${performance.mrr:.2f}",
                "review_avg": f"{performance.reviews_avg}/5",
            },
            "recommended_changes": optimized.get("changes_recommended", []),
            "escalation_plan": escalation,
            "next_iteration_focus": (
                "A/B test messaging" if performance.conversion_rate < 2
                else "Scale winners" if performance.mrr > 3000
                else "Improve retention"
            ),
            "optimized_strategy": optimized,
        }

    except Exception as e:
        logger.error(f"Error optimizando estrategia: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/intelligence-report", tags=["report"])
async def generate_full_report(product: ProductInput):
    """
    Reporte completo: análisis + estrategia + recomendaciones.

    Usarlo al onboard nuevo vendedor.
    """

    try:
        # Market analysis
        market_analysis = MarketAnalyzer.analyze(
            product_name=product.product_name,
            product_description=product.product_description,
            price=product.price,
        )

        # Strategy generation
        strategy = StrategyGenerator.generate_strategy(
            product_name=product.product_name,
            category=market_analysis.category,
            market_size=market_analysis.market_size,
            demand=market_analysis.demand_level,
            competition=market_analysis.competition_level,
            price=product.price,
            price_avg_market=market_analysis.price_range["avg"],
            business_goals=product.business_goals,
        )

        # Recomendaciones
        recommendations = [
            f"🎯 Posicionamiento: {market_analysis.recommended_positioning}",
            f"📊 Segment: {strategy['segment']}",
            f"📱 Canales: {strategy['recommended_channels'].get('primary')} → {strategy['recommended_channels'].get('secondary')}",
        ]

        # Oportunidades específicas
        recommendations.extend(market_analysis.opportunities)

        # Next actions
        next_actions = [
            "Semana 1: Validar posicionamiento + Landing page",
            "Semana 2: Email sequences + Social proof setup",
            "Semana 3: Ejecutar tácticas, recolectar data",
            "Semana 4+: Optimizar, iterar, escalar",
        ]

        logger.info(f"Reporte completo generado para: {product.product_name}")

        return {
            "status": "report_generated",
            "product": product.product_name,
            "market_analysis": {
                "category": market_analysis.category,
                "market_size": market_analysis.market_size,
                "demand": market_analysis.demand_level,
                "competition": market_analysis.competition_level,
                "price_positioning": market_analysis.price_range["vs_avg"],
                "top_competitor_avg_price": market_analysis.price_range["avg"],
            },
            "strategy": {
                "segment": strategy["segment"],
                "channels": strategy["recommended_channels"],
                "key_tactics": [t["name"] for t in strategy["tactics"]],
                "kpis": strategy["success_kpis"],
            },
            "opportunities": market_analysis.opportunities,
            "threats": market_analysis.threats,
            "recommendations": recommendations,
            "roadmap_90_days": strategy["roadmap_90days"],
            "next_actions": next_actions,
            "report_generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error generando reporte: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
