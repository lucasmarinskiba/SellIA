"""Market API — Endpoints for market detection & agent management."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.brain.brain_orchestrator_v3 import BrainOrchestratorV3
from app.core.clock import utc_now
from app.core.market import (
    AgentLoader,
    ContinuousLearner,
    MarketDetector,
    MarketRulesEngine,
)

router = APIRouter(prefix="/api/v1/market", tags=["market"])
logger = logging.getLogger(__name__)

orchestrator = BrainOrchestratorV3()
learner = ContinuousLearner()


class DetectMarketRequest(BaseModel):
    user_input: str
    company_data: dict[str, Any] | None = None


class DetectMarketResponse(BaseModel):
    industry: str
    business_model: str
    buyer_motivation: str
    market_type: str
    confidence_score: float
    recommended_agents: list[str]
    keywords: list[str]


@router.post("/detect")
async def detect_market(request: DetectMarketRequest) -> DetectMarketResponse:
    """Detect market type from user input."""
    try:
        profile = MarketDetector.detect_market(request.user_input, request.company_data)
        return DetectMarketResponse(
            industry=profile.industry.value,
            business_model=profile.business_model.value,
            buyer_motivation=profile.buyer_motivation.value,
            market_type=profile.market_type,
            confidence_score=profile.confidence_score,
            recommended_agents=profile.recommended_agents,
            keywords=profile.keywords,
        )
    except Exception as e:
        logger.exception("Market detection failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def get_available_agents(market: str | None = None) -> dict[str, Any]:
    """Get available agents for market."""
    if market:
        from app.core.market import Industry

        try:
            ind = Industry[market.upper()]
            agents = AgentLoader._recommend_agents(ind, None)
            return {
                "market": market,
                "agents": AgentLoader.load_agents_for_market(
                    type("MarketProfile", (), {"recommended_agents": agents})()
                ),
            }
        except Exception as e:
            logger.exception("get_available_agents: error inesperado")
            raise HTTPException(status_code=400, detail=f"Invalid market: {e}")
    return {"agents": AgentLoader.get_loaded_agents()}


@router.get("/rules/{market}")
async def get_market_rules(market: str) -> dict[str, Any]:
    """Get rules for market."""
    try:
        from app.core.market import Industry

        ind = Industry[market.upper()]
        rules_file = MarketDetector._get_rules_file(ind)
        rules = MarketRulesEngine.load_rules(market, rules_file)
        return {
            "market": market,
            "phases": MarketRulesEngine.get_sales_phases(rules),
            "cycle": MarketRulesEngine.get_sales_cycle_timeline(rules),
            "pricing": MarketRulesEngine.get_pricing_rules(rules),
            "payment": MarketRulesEngine.get_payment_rules(rules),
        }
    except Exception as e:
        logger.exception("get_market_rules: error inesperado")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sync")
async def sync_external_systems() -> dict[str, Any]:
    """Manually trigger sync from external systems."""
    try:
        result = orchestrator.sync_external_systems()
        return {
            "status": "success",
            "synced": result["new_agents"],
            "timestamp": utc_now().isoformat(),
        }
    except Exception as e:
        logger.exception("Sync failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_market_status() -> dict[str, Any]:
    """Get market system status."""
    try:
        return {
            "orchestrator": orchestrator.get_orchestrator_status(),
            "learner": learner.get_learning_status(),
            "timestamp": utc_now().isoformat(),
        }
    except Exception as e:
        logger.exception("Status check failed")
        raise HTTPException(status_code=500, detail=str(e))
