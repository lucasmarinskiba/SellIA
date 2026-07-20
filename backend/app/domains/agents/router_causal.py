"""Causal Reasoning Router

Endpoints for objection patterns, causal analysis, and pitch recommendations.
"""

from uuid import UUID
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.agents.causal_engine import CausalAnalyzer
from app.domains.agents.models_causal import ObjectionPattern as ObjectionPatternModel
from app.domains.agents.models_causal import CausalAnalysis as CausalAnalysisModel

router = APIRouter(prefix="/causal", tags=["causal"])


@router.get("/patterns", status_code=status.HTTP_200_OK)
async def list_objection_patterns(
    business_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List objection patterns for a business."""
    target_business_id = business_id or current_user.business_id
    if not target_business_id:
        raise HTTPException(status_code=400, detail="business_id required")

    result = await db.execute(
        select(ObjectionPatternModel)
        .where(ObjectionPatternModel.business_id == target_business_id)
        .order_by(ObjectionPatternModel.frequency_percent.desc())
    )
    patterns = result.scalars().all()
    return [
        {
            "id": p.id,
            "business_id": p.business_id,
            "pattern_name": p.pattern_name,
            "objection_text": p.objection_text,
            "root_cause": p.root_cause,
            "frequency_count": p.frequency_count,
            "frequency_percent": p.frequency_percent,
            "overcome_count": p.overcome_count,
            "overcome_rate": p.overcome_rate,
            "affected_segments": p.affected_segments,
            "recommended_response": p.recommended_response,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        }
        for p in patterns
    ]


@router.get("/analysis/{conversation_id}", status_code=status.HTTP_200_OK)
async def get_causal_analysis(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get causal analysis for a specific conversation."""
    result = await db.execute(
        select(CausalAnalysisModel)
        .where(CausalAnalysisModel.conversation_id == conversation_id)
        .order_by(CausalAnalysisModel.created_at.desc())
    )
    analysis = result.scalars().first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Causal analysis not found")
    return {
        "id": analysis.id,
        "conversation_id": analysis.conversation_id,
        "business_id": analysis.business_id,
        "deal_outcome": analysis.deal_outcome,
        "surface_reason": analysis.surface_reason,
        "root_cause": analysis.root_cause,
        "contributing_factors": analysis.contributing_factors,
        "recommended_fix": analysis.recommended_fix,
        "confidence": analysis.confidence,
        "created_at": analysis.created_at,
    }


@router.post("/analyze/{conversation_id}", status_code=status.HTTP_201_CREATED)
async def trigger_causal_analysis(
    conversation_id: UUID,
    deal_outcome: str = "lost",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger causal analysis for a conversation."""
    analyzer = CausalAnalyzer(db)
    result = await analyzer.analyze_failed_deal(conversation_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not generate causal analysis (no transcript or LLM unavailable)",
        )

    business_id = await analyzer._resolve_business_id(conversation_id)
    record = await analyzer.save_causal_analysis(
        conversation_id=conversation_id,
        business_id=business_id,
        deal_outcome=deal_outcome,
        result=result,
    )
    return {
        "id": record.id,
        "conversation_id": record.conversation_id,
        "business_id": record.business_id,
        "deal_outcome": record.deal_outcome,
        "surface_reason": record.surface_reason,
        "root_cause": record.root_cause,
        "contributing_factors": record.contributing_factors,
        "recommended_fix": record.recommended_fix,
        "confidence": record.confidence,
        "created_at": record.created_at,
    }


@router.get("/recommendations", status_code=status.HTTP_200_OK)
async def get_pitch_recommendations(
    business_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get pitch recommendations based on causal analysis."""
    target_business_id = business_id or current_user.business_id
    if not target_business_id:
        raise HTTPException(status_code=400, detail="business_id required")

    analyzer = CausalAnalyzer(db)
    recommendations = await analyzer.generate_pitch_recommendations(target_business_id)
    return {
        "business_id": target_business_id,
        "recommendations": [
            {
                "segment": r.segment,
                "insight": r.insight,
                "recommended_action": r.recommended_action,
                "priority": r.priority,
            }
            for r in recommendations
        ],
    }
