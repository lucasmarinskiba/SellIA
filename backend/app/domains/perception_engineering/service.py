"""Phase X7: Perception Engineering Agent Service."""
from datetime import datetime, timezone
from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.domains.perception_engineering.models import (
    ProductPerception, PerceptionShiftCampaign, ValuePerceptionOptimizer,
    PerceptionNarrative, PerceptionDimension, PerceptionShiftTechnique
)


class PerceptionEngineeringAgent:
    """AI Agent that changes how customers perceive products to increase sales."""

    @staticmethod
    async def analyze_perception_gap(
        db: AsyncSession,
        business_id: UUID,
        product_id: UUID,
        current_perception: Dict[str, float],
    ) -> ProductPerception:
        """Analyze gap between current and desired perception."""
        perception = ProductPerception(
            business_id=business_id,
            product_id=product_id,
            quality_score=current_perception.get("quality", 5.0),
            value_score=current_perception.get("value", 5.0),
            trust_score=current_perception.get("trust", 5.0),
            exclusivity_score=current_perception.get("exclusivity", 5.0),
            innovation_score=current_perception.get("innovation", 5.0),
            emotional_score=current_perception.get("emotional", 5.0),
            authority_score=current_perception.get("authority", 5.0),
            belonging_score=current_perception.get("belonging", 5.0),
        )
        db.add(perception)
        await db.commit()
        await db.refresh(perception)
        return perception

    @staticmethod
    async def generate_perception_shift_campaign(
        db: AsyncSession,
        business_id: UUID,
        product_id: UUID,
        target_dimension: PerceptionDimension,
        current_score: float,
        target_score: float,
        customer_segment: str = "general",
    ) -> PerceptionShiftCampaign:
        """Generate AI-powered perception shift campaign using psychology."""

        # Select best technique based on gap
        gap = target_score - current_score
        technique = PerceptionEngineeringAgent._select_best_technique(target_dimension, gap)

        # Generate messaging
        headline, narrative, social_proof, call_to_action = (
            PerceptionEngineeringAgent._generate_messaging(
                target_dimension, technique, gap, customer_segment
            )
        )

        campaign = PerceptionShiftCampaign(
            business_id=business_id,
            product_id=product_id,
            target_dimension=target_dimension,
            technique=technique,
            perception_score_before=current_score,
            perception_score_target=target_score,
            headline=headline,
            narrative=narrative,
            social_proof=social_proof,
            call_to_action=call_to_action,
            target_audience_segment=customer_segment,
            cognitive_bias_leveraged=PerceptionEngineeringAgent._get_cognitive_bias(technique),
            emotional_trigger=PerceptionEngineeringAgent._get_emotional_trigger(target_dimension),
        )
        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)
        return campaign

    @staticmethod
    def _select_best_technique(dimension: PerceptionDimension, gap: float) -> PerceptionShiftTechnique:
        """AI selects best psychological technique based on target dimension."""
        technique_map = {
            PerceptionDimension.QUALITY: PerceptionShiftTechnique.AUTHORITY,
            PerceptionDimension.VALUE: PerceptionShiftTechnique.ANCHORING,
            PerceptionDimension.TRUST: PerceptionShiftTechnique.SOCIAL_PROOF,
            PerceptionDimension.EXCLUSIVITY: PerceptionShiftTechnique.SCARCITY,
            PerceptionDimension.INNOVATION: PerceptionShiftTechnique.STORYTELLING,
            PerceptionDimension.EMOTIONAL: PerceptionShiftTechnique.STORYTELLING,
            PerceptionDimension.AUTHORITY: PerceptionShiftTechnique.AUTHORITY,
            PerceptionDimension.BELONGING: PerceptionShiftTechnique.SOCIAL_PROOF,
        }
        return technique_map.get(dimension, PerceptionShiftTechnique.REFRAMING)

    @staticmethod
    def _generate_messaging(
        dimension: PerceptionDimension,
        technique: PerceptionShiftTechnique,
        gap: float,
        segment: str,
    ) -> tuple:
        """Generate psychologically optimized messaging."""

        messaging_templates = {
            (PerceptionDimension.QUALITY, PerceptionShiftTechnique.AUTHORITY): (
                "Award-Winning Quality Recognized by Experts",
                "Our product has been certified by 3 international quality standards...",
                "Trusted by 50,000+ professionals",
                "Upgrade your standards now"
            ),
            (PerceptionDimension.VALUE, PerceptionShiftTechnique.ANCHORING): (
                "Premium Value at a Fair Price",
                f"While competitors charge 2-3x more for similar features, we deliver the same quality at {gap*100:.0f}% better value...",
                "Saves customers $5,000+ annually",
                "Get premium quality affordably"
            ),
            (PerceptionDimension.TRUST, PerceptionShiftTechnique.SOCIAL_PROOF): (
                "Trusted by Industry Leaders",
                "Join 100,000+ satisfied customers who rely on us daily for their most critical needs...",
                "4.9/5 stars from 10,000+ verified reviews",
                "Join the trusted majority"
            ),
            (PerceptionDimension.EXCLUSIVITY, PerceptionShiftTechnique.SCARCITY): (
                "Exclusive Access - Limited Availability",
                "This premium offering is reserved for committed customers who demand excellence...",
                "Only available to 1,000 select members",
                "Claim your exclusive access"
            ),
            (PerceptionDimension.EMOTIONAL, PerceptionShiftTechnique.STORYTELLING): (
                "Transform Your Life - Join Those Who Did",
                "Real customers share how this changed their lives: improved confidence, freedom, success...",
                "See transformation stories from real users",
                "Start your transformation today"
            ),
        }

        default_msg = (
            f"Perception Shift: {dimension.value}",
            f"Strategic repositioning to increase {dimension.value} perception...",
            "Join others in discovering true value",
            "Experience the difference"
        )

        return messaging_templates.get((dimension, technique), default_msg)

    @staticmethod
    def _get_cognitive_bias(technique: PerceptionShiftTechnique) -> str:
        """Return the cognitive bias being leveraged."""
        bias_map = {
            PerceptionShiftTechnique.ANCHORING: "anchoring_bias",
            PerceptionShiftTechnique.SOCIAL_PROOF: "consensus_bias",
            PerceptionShiftTechnique.AUTHORITY: "authority_bias",
            PerceptionShiftTechnique.SCARCITY: "scarcity_bias",
            PerceptionShiftTechnique.LOSS_AVERSION: "loss_aversion_bias",
            PerceptionShiftTechnique.STORYTELLING: "availability_bias",
        }
        return bias_map.get(technique, "confirmation_bias")

    @staticmethod
    def _get_emotional_trigger(dimension: PerceptionDimension) -> str:
        """Return the emotional trigger to activate."""
        emotion_map = {
            PerceptionDimension.QUALITY: "pride",
            PerceptionDimension.VALUE: "satisfaction",
            PerceptionDimension.TRUST: "security",
            PerceptionDimension.EXCLUSIVITY: "status",
            PerceptionDimension.INNOVATION: "aspiration",
            PerceptionDimension.EMOTIONAL: "desire",
            PerceptionDimension.AUTHORITY: "confidence",
            PerceptionDimension.BELONGING: "community",
        }
        return emotion_map.get(dimension, "desire")

    @staticmethod
    async def optimize_value_perception(
        db: AsyncSession,
        business_id: UUID,
        product_id: UUID,
        base_price: float,
        current_perceived_value: float,
        competitor_prices: List[float],
    ) -> ValuePerceptionOptimizer:
        """Optimize how much value customers perceive in the product."""

        # Calculate anchoring high price
        anchoring_high = max(competitor_prices) * 1.3 if competitor_prices else base_price * 2

        # Value gap analysis
        value_gap = current_perceived_value - base_price

        # Optimize perceived value using psychology
        optimizer = ValuePerceptionOptimizer(
            business_id=business_id,
            product_id=product_id,
            base_price=base_price,
            perceived_value=current_perceived_value,
            value_gap=value_gap,
            anchoring_high_price=anchoring_high,
            bundled_value_add="+ Free onboarding + 1-year support + 30-day guarantee",
            comparison_competitors=[
                {"competitor": "Leading Alternative", "price": anchoring_high}
            ],
            reframe_as_investment="Think of this as an investment in your efficiency, not an expense",
            reframe_as_time_saved="Saves 20 hours/month = $5,000+ value annually",
            reframe_as_risk_reduction="Protects you against costly mistakes and downtime",
        )

        # Calculate optimization
        bundled_value_increase = 500  # Arbitrary bundled value
        optimizer.optimized_perception = current_perceived_value + bundled_value_increase
        optimizer.recommended_price = base_price * (optimizer.optimized_perception / current_perceived_value)
        optimizer.expected_conversion_increase = min(0.4, value_gap * 0.1)  # 40% max increase

        db.add(optimizer)
        await db.commit()
        await db.refresh(optimizer)
        return optimizer

    @staticmethod
    async def generate_perception_narrative(
        db: AsyncSession,
        business_id: UUID,
        product_id: UUID,
        product_name: str,
        customer_transformation: str,
    ) -> PerceptionNarrative:
        """Generate compelling narrative that shifts customer perception."""

        narrative = PerceptionNarrative(
            business_id=business_id,
            product_id=product_id,
            hero="Your best self after using this",
            villain="Inefficiency, waste, and missed opportunities",
            transformation=customer_transformation,
            proof_points=[
                "95% customer satisfaction rate",
                "Used by 50,000+ professionals",
                "Endorsed by industry experts",
                "Proven ROI: 3:1 return within 6 months"
            ],
            emotional_appeal="aspiration",
            call_to_identity=f"Be someone who demands excellence and gets {product_name}",
            primary_narrative=f"""
            {product_name} isn't just a product—it's a transformation.

            Imagine going from struggling with inefficiency to thriving with clarity.
            That's the {product_name} difference.

            Join the leaders who've already made the shift.
            Your best work is waiting.
            """,
            backup_narrative=f"""
            Smart companies choose {product_name}.

            Because when you invest in quality, you get quality back.
            Join the experts.
            """,
        )

        # Add segment-specific variants
        narrative.narrative_variants = [
            {
                "segment": "luxury_buyers",
                "narrative": f"Exclusively designed for discerning professionals who demand the finest."
            },
            {
                "segment": "budget_conscious",
                "narrative": f"Premium quality at prices that make sense. Finally."
            },
            {
                "segment": "early_adopters",
                "narrative": f"The innovation leaders are already here. Are you next?"
            }
        ]

        db.add(narrative)
        await db.commit()
        await db.refresh(narrative)
        return narrative

    @staticmethod
    async def predict_perception_shift_impact(
        current_perception: float,
        technique: PerceptionShiftTechnique,
        campaign_budget: float,
    ) -> Dict[str, float]:
        """Predict sales impact of perception shift campaign."""

        # Base conversion lift from perception shift
        technique_effectiveness = {
            PerceptionShiftTechnique.AUTHORITY: 0.25,  # 25% lift
            PerceptionShiftTechnique.SOCIAL_PROOF: 0.35,  # 35% lift
            PerceptionShiftTechnique.STORYTELLING: 0.30,  # 30% lift
            PerceptionShiftTechnique.ANCHORING: 0.20,  # 20% lift
            PerceptionShiftTechnique.SCARCITY: 0.40,  # 40% lift (most effective)
            PerceptionShiftTechnique.REFRAMING: 0.15,  # 15% lift
        }

        base_lift = technique_effectiveness.get(technique, 0.2)

        # Budget impact (diminishing returns)
        budget_multiplier = min(1.5, 1.0 + (campaign_budget / 10000))

        total_conversion_lift = base_lift * budget_multiplier
        revenue_impact = total_conversion_lift * 0.8  # Assume 80% of conversion lift = revenue

        return {
            "conversion_lift_percent": round(total_conversion_lift * 100, 1),
            "revenue_impact_percent": round(revenue_impact * 100, 1),
            "perception_increase": round((current_perception + (10 - current_perception) * total_conversion_lift), 1),
            "roi_estimate": round(revenue_impact / (campaign_budget / 10000), 1) if campaign_budget > 0 else 0,
        }
