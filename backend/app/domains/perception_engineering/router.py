"""Phase X7: Perception Engineering Agent API."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Dict, List, Optional
from app.core.database import get_db
from app.domains.perception_engineering.service import PerceptionEngineeringAgent
from app.domains.perception_engineering.models import PerceptionDimension, PerceptionShiftTechnique


router = APIRouter(prefix="/api/v1/perception-engineering", tags=["perception-engineering"])


@router.post("/analyze-gap")
async def analyze_perception_gap(
    business_id: UUID,
    product_id: UUID,
    current_perception: Dict[str, float],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Analyze gap between current and desired customer perception."""
    perception = await PerceptionEngineeringAgent.analyze_perception_gap(
        db, business_id, product_id, current_perception
    )

    # Calculate gaps
    gaps = {
        "quality_gap": perception.target_quality - perception.quality_score,
        "value_gap": perception.target_value - perception.value_score,
        "trust_gap": perception.target_trust - perception.trust_score,
        "exclusivity_gap": perception.target_exclusivity - perception.exclusivity_score,
    }

    return {
        "perception_id": perception.id,
        "current_scores": {
            "quality": perception.quality_score,
            "value": perception.value_score,
            "trust": perception.trust_score,
            "exclusivity": perception.exclusivity_score,
        },
        "gaps": gaps,
        "largest_opportunity": max(gaps, key=gaps.get),
    }


@router.post("/generate-shift-campaign")
async def generate_shift_campaign(
    business_id: UUID,
    product_id: UUID,
    target_dimension: PerceptionDimension,
    current_score: float,
    target_score: float,
    customer_segment: str = "general",
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate AI-powered perception shift campaign."""
    campaign = await PerceptionEngineeringAgent.generate_perception_shift_campaign(
        db, business_id, product_id, target_dimension, current_score, target_score, customer_segment
    )

    return {
        "campaign_id": campaign.id,
        "target_dimension": campaign.target_dimension,
        "technique": campaign.technique,
        "headline": campaign.headline,
        "narrative": campaign.narrative,
        "social_proof": campaign.social_proof,
        "call_to_action": campaign.call_to_action,
        "cognitive_bias": campaign.cognitive_bias_leveraged,
        "emotional_trigger": campaign.emotional_trigger,
        "target_segment": campaign.target_audience_segment,
    }


@router.post("/optimize-value")
async def optimize_value_perception(
    business_id: UUID,
    product_id: UUID,
    base_price: float,
    current_perceived_value: float,
    competitor_prices: List[float],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Optimize perceived value using psychological techniques."""
    optimizer = await PerceptionEngineeringAgent.optimize_value_perception(
        db, business_id, product_id, base_price, current_perceived_value, competitor_prices
    )

    return {
        "optimizer_id": optimizer.id,
        "current_perceived_value": optimizer.perceived_value,
        "value_gap": round(optimizer.value_gap, 2),
        "anchoring_high_price": optimizer.anchoring_high_price,
        "bundled_value_add": optimizer.bundled_value_add,
        "reframe_as_investment": optimizer.reframe_as_investment,
        "optimized_perception": round(optimizer.optimized_perception, 2),
        "recommended_price": round(optimizer.recommended_price, 2),
        "expected_conversion_increase": f"{optimizer.expected_conversion_increase*100:.1f}%",
    }


@router.post("/generate-narrative")
async def generate_narrative(
    business_id: UUID,
    product_id: UUID,
    product_name: str,
    customer_transformation: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate compelling narrative that shifts perception."""
    narrative = await PerceptionEngineeringAgent.generate_perception_narrative(
        db, business_id, product_id, product_name, customer_transformation
    )

    return {
        "narrative_id": narrative.id,
        "hero": narrative.hero,
        "villain": narrative.villain,
        "transformation": narrative.transformation,
        "proof_points": narrative.proof_points,
        "emotional_appeal": narrative.emotional_appeal,
        "call_to_identity": narrative.call_to_identity,
        "primary_narrative": narrative.primary_narrative,
        "segment_variants": narrative.narrative_variants,
    }


@router.get("/predict-impact")
async def predict_impact(
    current_perception: float,
    technique: PerceptionShiftTechnique,
    campaign_budget: float = 10000,
) -> dict:
    """Predict sales impact of perception shift campaign."""
    impact = PerceptionEngineeringAgent.predict_perception_shift_impact(
        current_perception, technique, campaign_budget
    )

    return {
        "technique": technique,
        "conversion_lift": impact["conversion_lift_percent"],
        "revenue_impact": impact["revenue_impact_percent"],
        "predicted_perception_score": impact["perception_increase"],
        "roi_estimate": f"{impact['roi_estimate']:.1f}x",
        "recommendation": "High ROI potential" if impact["conversion_lift_percent"] > 25 else "Moderate potential",
    }
