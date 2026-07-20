"""
Super Seller API — El mejor empleado de ventas del mundo.

Endpoints:
- POST /diagnose: Analiza producto, detecta problemas, sugiere soluciones
- POST /complete-plan: Plan venta completo 90 días
- POST /execute-now: Comienza a vender HOY
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging

from backend.app.core.intelligence.market_analyzer import MarketAnalyzer
from backend.app.core.intelligence.strategy_generator import StrategyGenerator
from backend.app.core.intelligence.problem_detector import ProblemDetector, ProblemSolver
from backend.app.core.intelligence.sales_executor import SalesExecutor

router = APIRouter(prefix="/api/v1/super-seller", tags=["super_seller"])
logger = logging.getLogger(__name__)


class ProductDiagnosis(BaseModel):
    """Diagnóstico de producto."""
    product_name: str
    product_description: str
    price: float
    current_conversion_rate: Optional[float] = None
    current_mrr: Optional[float] = None
    current_reviews_count: Optional[int] = 0
    current_email_sequences: Optional[int] = 0


@router.post("/diagnose", tags=["diagnosis"])
async def diagnose_product(diagnosis: ProductDiagnosis):
    """
    Diagnóstico completo: qué está mal, por qué, cómo arreglarlo.

    Retorna: Lista problemas + severidad + soluciones específicas desde grandes mentes.
    """

    try:
        logger.info(f"Diagnosticando producto: {diagnosis.product_name}")

        # 1. Market analysis
        market_analysis = MarketAnalyzer.analyze(
            product_name=diagnosis.product_name,
            product_description=diagnosis.product_description,
            price=diagnosis.price,
        )

        # 2. Strategy
        strategy = StrategyGenerator.generate_strategy(
            product_name=diagnosis.product_name,
            category=market_analysis.category,
            market_size=market_analysis.market_size,
            demand=market_analysis.demand_level,
            competition=market_analysis.competition_level,
            price=diagnosis.price,
            price_avg_market=market_analysis.price_range["avg"],
        )

        # 3. Performance data
        performance_data = {
            "price": diagnosis.price,
            "visitors_per_day": 5,  # TODO: actual data from tracking
            "conversion_rate": diagnosis.current_conversion_rate or 0.5,
            "mrr": diagnosis.current_mrr or 0,
            "reviews_count": diagnosis.current_reviews_count or 0,
            "review_score_avg": 4.0 if diagnosis.current_reviews_count > 0 else 0,
            "avg_response_time_hours": 12,  # TODO: actual
            "email_sequences_active": diagnosis.current_email_sequences or 0,
            "monthly_churn_rate": 3,  # TODO: actual
            "checkout_steps": 5,  # TODO: actual
            "cart_abandonment_rate": 65,  # TODO: actual
        }

        # 4. Detectar problemas
        problems = ProblemDetector.analyze(
            product_name=diagnosis.product_name,
            market_analysis=market_analysis.__dict__ if hasattr(market_analysis, '__dict__') else market_analysis,
            performance_data=performance_data,
            strategy=strategy,
        )

        # 5. Soluciones por problema (usando grandes mentes)
        solutions = []
        for problem in problems:
            solution = ProblemSolver.solve(problem, business_minds=["hermozi", "belfort", "jobs", "buffett"])
            solutions.append(solution)

        logger.info(f"Diagnóstico completado: {len(problems)} problemas detectados")

        return {
            "status": "diagnosed",
            "product": diagnosis.product_name,
            "market": {
                "category": market_analysis.category,
                "competition": market_analysis.competition_level,
                "demand": market_analysis.demand_level,
            },
            "problems_detected": [
                {
                    "name": p.name,
                    "severity": p.severity.value,
                    "description": p.description,
                    "root_cause": p.root_cause,
                    "affected_stage": p.affected_stage,
                    "business_impact": p.business_impact,
                }
                for p in problems
            ],
            "solutions_by_problem": solutions,
            "urgent_actions": [s["recommended_priority"] for s in solutions if s.get("recommended_priority") == 1],
            "diagnosed_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error en diagnóstico: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complete-plan", tags=["planning"])
async def generate_complete_plan(diagnosis: ProductDiagnosis):
    """
    Plan venta completo 90 días.

    Fase 1: Captura 100+ leads
    Fase 2: Nurture 50% qualified
    Fase 3: Close 5-10% conversión
    Fase 4: Deliver con aha moment
    Fase 5: Retain + upsell + referrals

    Cada fase incluye tácticas específicas + KPIs.
    """

    try:
        logger.info(f"Generando plan completo: {diagnosis.product_name}")

        # 1. Market analysis
        market_analysis = MarketAnalyzer.analyze(
            product_name=diagnosis.product_name,
            product_description=diagnosis.product_description,
            price=diagnosis.price,
        )

        # 2. Strategy
        strategy = StrategyGenerator.generate_strategy(
            product_name=diagnosis.product_name,
            category=market_analysis.category,
            market_size=market_analysis.market_size,
            demand=market_analysis.demand_level,
            competition=market_analysis.competition_level,
            price=diagnosis.price,
            price_avg_market=market_analysis.price_range["avg"],
        )

        # 3. Problems detection
        performance_data = {
            "price": diagnosis.price,
            "visitors_per_day": 5,
            "conversion_rate": diagnosis.current_conversion_rate or 0.5,
            "mrr": diagnosis.current_mrr or 0,
            "reviews_count": diagnosis.current_reviews_count or 0,
            "review_score_avg": 4.0 if diagnosis.current_reviews_count > 0 else 0,
            "avg_response_time_hours": 12,
            "email_sequences_active": diagnosis.current_email_sequences or 0,
            "monthly_churn_rate": 3,
            "checkout_steps": 5,
            "cart_abandonment_rate": 65,
        }

        problems = ProblemDetector.analyze(
            product_name=diagnosis.product_name,
            market_analysis=market_analysis.__dict__ if hasattr(market_analysis, '__dict__') else market_analysis,
            performance_data=performance_data,
            strategy=strategy,
        )

        problems_dict = [
            {
                "id": p.id,
                "name": p.name,
                "severity": p.severity.value,
            }
            for p in problems
        ]

        # 4. Generar plan completo
        complete_plan = SalesExecutor.build_complete_sales_plan(
            product=diagnosis.product_name,
            category=market_analysis.category,
            market_analysis=market_analysis.__dict__ if hasattr(market_analysis, '__dict__') else market_analysis,
            strategy=strategy,
            problems=problems_dict,
        )

        logger.info(f"Plan generado: {diagnosis.product_name}, 5 fases, 90 días")

        return {
            "status": "plan_generated",
            "product": diagnosis.product_name,
            "timeline": "90 days",
            "phases": {
                "1_capture": complete_plan["phase_1_capture"],
                "2_nurture": complete_plan["phase_2_nurture"],
                "3_close": complete_plan["phase_3_close"],
                "4_deliver": complete_plan["phase_4_deliver"],
                "5_retain": complete_plan["phase_5_retain"],
            },
            "kpis": complete_plan["kpis_by_phase"],
            "success_criteria": {
                "week_2": "100+ leads captured",
                "week_5": "50% leads in consideration",
                "week_8": "25 customers (5-10% conversion)",
                "week_9": "80%+ aha moment rate",
                "week_12": "<2% churn, >100% NRR",
            },
            "plan_generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error generando plan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute-now", tags=["execution"])
async def execute_immediately(diagnosis: ProductDiagnosis):
    """
    Comienza a vender AHORA. Genera plan + acciones inmediatas (hoy, mañana, esta semana).

    Retorna: Plan + primeras acciones concretas que ejecutar.
    """

    try:
        logger.info(f"Ejecutando ventas para: {diagnosis.product_name}")

        # Generar plan completo
        market_analysis = MarketAnalyzer.analyze(
            product_name=diagnosis.product_name,
            product_description=diagnosis.product_description,
            price=diagnosis.price,
        )

        strategy = StrategyGenerator.generate_strategy(
            product_name=diagnosis.product_name,
            category=market_analysis.category,
            market_size=market_analysis.market_size,
            demand=market_analysis.demand_level,
            competition=market_analysis.competition_level,
            price=diagnosis.price,
            price_avg_market=market_analysis.price_range["avg"],
        )

        # Acciones inmediatas
        immediate_actions = {
            "today": [
                "✅ Define UVP clara (1 frase por qué cliente debe comprar)",
                "✅ Crea landing page simplificado (headline + 3 beneficios + CTA)",
                "✅ Setup email automation (welcome sequence 3 emails)",
            ],
            "tomorrow": [
                "✅ Configura Google Analytics / pixel tracking",
                "✅ Lanza email a lista (friends + network)",
                "✅ Publica en redes (TikTok, Instagram, LinkedIn según producto)",
            ],
            "this_week": [
                "✅ Setup Stripe / payment gateway",
                "✅ Crear checkout simplificado (1-2 pasos max)",
                "✅ Pedir reviews a primeros 5 customers (con incentivo)",
                "✅ Setup helpdesk (Zendesk, Intercom, o simple email)",
                "✅ Configurar follow-up automático (24h sin respuesta → email reminder)",
            ],
        }

        logger.info(f"Plan de ejecución inmediata generado")

        return {
            "status": "execution_ready",
            "product": diagnosis.product_name,
            "go_live_date": datetime.utcnow().isoformat(),
            "segment": strategy.get("segment"),
            "channels": strategy.get("recommended_channels"),
            "immediate_actions": immediate_actions,
            "first_week_goal": "10+ leads, 1-2 sales",
            "first_month_goal": f"100+ leads, 5-10 sales, 3+ reviews (conversion {5 if strategy.get('segment') == 'budget' else 2}%+)",
            "resources_needed": {
                "landing_page": "Vercel + Next.js (free) or Webflow ($15/mo)",
                "email": "Brevo free tier (300/day) or Mailchimp",
                "payment": "Stripe (2.9% + $0.30)",
                "analytics": "Google Analytics (free)",
                "support": "Notion or Google Sheets (free) for now",
                "total_cost_week_1": "$0-20 (paid ads optional)",
            },
            "success_looks_like_week_1": {
                "visitors": "20-50/day",
                "emails_opened": "30-50%",
                "leads_qualified": "3-5",
                "conversions": "0-1",
            },
            "next_review": "7 days - analyze metrics, iterate",
        }

    except Exception as e:
        logger.error(f"Error en ejecución: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
