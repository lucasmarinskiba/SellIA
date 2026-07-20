"""Lead Scoring API Router

Endpoints para evaluar leads:
- POST /leads/score — calcular score de un lead
- GET /leads/by-temperature — filtrar por hot/warm/cold
- GET /leads/priority — ordenar por priority
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.logger import get_logger
from app.domains.users.models import User
from app.domains.computer_use.services.lead_scorer import (
    get_lead_scoring_service,
    LeadScoringService,
    LeadTemperature,
)

logger = get_logger(__name__)
router = APIRouter()


# ========== Models ==========


class MessageHistory(BaseModel):
    """Mensaje en historial."""

    content: str
    timestamp: str = Field(..., description="ISO format datetime")
    role: str = Field(default="customer", description="customer | agent")


class LeadScoringRequest(BaseModel):
    """Request para score un lead."""

    lead_id: str
    lead_name: str
    conversation_history: List[MessageHistory]
    customer_profile: dict = Field(default_factory=dict)
    product_info: dict = Field(default_factory=dict)


class LeadScoreBreakdownResponse(BaseModel):
    """Desglose de score."""

    engagement: float
    intent: float
    personality: float
    stage: float
    recency: float
    total: float


class LeadScoreResponse(BaseModel):
    """Respuesta con score de lead."""

    lead_id: str
    lead_name: str
    score: float  # 0-100
    temperature: str  # hot | warm | cold
    breakdown: LeadScoreBreakdownResponse
    next_action: str
    scored_at: str


# ========== Endpoints ==========


@router.post("/leads/score", response_model=LeadScoreResponse)
async def score_lead(
    request: LeadScoringRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Calcula score automático de un lead.

    Retorna: score (0-100), temperatura, breakdown, acción recomendada.
    """
    try:
        service = get_lead_scoring_service()

        # Convertir MessageHistory a dict
        conv_history = [
            {
                "content": msg.content,
                "timestamp": msg.timestamp,
                "role": msg.role,
            }
            for msg in request.conversation_history
        ]

        score = await service.score_lead(
            lead_id=request.lead_id,
            lead_name=request.lead_name,
            conversation_history=conv_history,
            customer_profile=request.customer_profile,
            product_info=request.product_info,
        )

        return LeadScoreResponse(
            lead_id=score.lead_id,
            lead_name=score.lead_name,
            score=score.score,
            temperature=score.temperature.value,
            breakdown=LeadScoreBreakdownResponse(**score.breakdown.to_dict()),
            next_action=score.next_action,
            scored_at=score.scored_at.isoformat(),
        )

    except Exception as e:
        logger.error(f"Error scoring lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/leads/batch-score", response_model=List[LeadScoreResponse])
async def batch_score_leads(
    requests: List[LeadScoringRequest],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Calcula scores para múltiples leads de una vez.

    Retorna lista de scores ordenados por temperatura (hot → warm → cold).
    """
    try:
        service = get_lead_scoring_service()
        scores = []

        for req in requests:
            conv_history = [
                {
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "role": msg.role,
                }
                for msg in req.conversation_history
            ]

            score = await service.score_lead(
                lead_id=req.lead_id,
                lead_name=req.lead_name,
                conversation_history=conv_history,
                customer_profile=req.customer_profile,
                product_info=req.product_info,
            )

            scores.append(score)

        # Ordenar por temperature + score
        scores_sorted = await service.prioritize_leads(scores)

        return [
            LeadScoreResponse(
                lead_id=s.lead_id,
                lead_name=s.lead_name,
                score=s.score,
                temperature=s.temperature.value,
                breakdown=LeadScoreBreakdownResponse(**s.breakdown.to_dict()),
                next_action=s.next_action,
                scored_at=s.scored_at.isoformat(),
            )
            for s in scores_sorted
        ]

    except Exception as e:
        logger.error(f"Error batch scoring leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leads/by-temperature")
async def get_leads_by_temperature(
    temperature: str = Query(..., description="hot | warm | cold"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retorna info sobre acciones recomendadas por temperatura.

    Útil para routing automático de leads.
    """
    try:
        if temperature not in ["hot", "warm", "cold"]:
            raise HTTPException(status_code=400, detail="Invalid temperature")

        recommendations = {
            "hot": {
                "temperature": "hot",
                "score_range": "70-100",
                "description": "Ready to close",
                "recommended_actions": [
                    "Use Sales Closer immediately",
                    "Apply closing techniques",
                    "Offer limited-time deal",
                    "Fast-track to order",
                ],
                "pipeline_stage": "closure",
                "expected_conversion": "High (>70%)",
            },
            "warm": {
                "temperature": "warm",
                "score_range": "40-69",
                "description": "Interested, nurturing phase",
                "recommended_actions": [
                    "Send value-packed follow-up",
                    "Answer objections",
                    "Share social proof",
                    "Offer low-risk trial",
                ],
                "pipeline_stage": "negotiation/consideration",
                "expected_conversion": "Medium (30-70%)",
            },
            "cold": {
                "temperature": "cold",
                "score_range": "0-39",
                "description": "Early stage, low engagement",
                "recommended_actions": [
                    "Re-engage with fresh angle",
                    "Share educational content",
                    "Build relationship",
                    "Trigger FOMO (limited offer)",
                ],
                "pipeline_stage": "awareness",
                "expected_conversion": "Low (<30%)",
            },
        }

        return recommendations.get(temperature)

    except Exception as e:
        logger.error(f"Error getting temperature info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leads/scoring-factors")
async def get_scoring_factors(
    current_user: User = Depends(get_current_active_user),
):
    """
    Retorna explicación de factores de scoring.

    Educación del usuario sobre cómo se calcula score.
    """
    return {
        "total_possible": 100,
        "factors": {
            "engagement": {
                "max_points": 25,
                "description": "Message frequency + response velocity",
                "indicators": [
                    "5+ messages = high engagement",
                    "2-4 messages = medium",
                    "0-1 messages = low",
                    "Multi-day span = penalty",
                ],
            },
            "intent": {
                "max_points": 30,
                "description": "Buying keywords + purchase signals",
                "indicators": [
                    "Strong: 'compramos', 'confirmen', 'facturación'",
                    "Medium: 'interesa', 'cuándo', 'precio'",
                    "Weak: 'qué es', 'cómo funciona'",
                ],
            },
            "personality": {
                "max_points": 15,
                "description": "Buyer personality fit",
                "indicators": [
                    "Driver (ASAP, results) = 15 pts",
                    "Expressive (emotional) = 12 pts",
                    "Analytical (details) = 10 pts",
                    "Neutral = 7.5 pts",
                ],
            },
            "stage": {
                "max_points": 20,
                "description": "Pipeline stage (awareness → closure)",
                "indicators": [
                    "Closure ('confirmo') = 20 pts",
                    "Negotiation ('precio') = 15 pts",
                    "Consideration ('interesa') = 10 pts",
                    "Awareness ('qué es') = 5 pts",
                ],
            },
            "recency": {
                "max_points": 10,
                "description": "Message recency (older = colder)",
                "indicators": [
                    "Today = 10 pts",
                    "Yesterday = 8 pts",
                    "Within 3 days = 6 pts",
                    "Within week = 3 pts",
                    "Older = 0 pts",
                ],
            },
        },
        "temperature_thresholds": {
            "hot": "70-100 (ready to close)",
            "warm": "40-69 (interested, nurturing)",
            "cold": "0-39 (early stage)",
        },
    }
