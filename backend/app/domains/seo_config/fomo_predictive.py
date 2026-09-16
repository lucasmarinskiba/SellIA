"""Predictive FOMO scoring using Claude AI."""

from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.core.logger import get_logger
from app.domains.seo_config.models import PublicationLink, PublicationLinkFOMO
from app.domains.seo_config.analytics_models import PublicationLinkMetrics

logger = get_logger(__name__)


class FOMAPredictor:
    """Predict FOMO copy effectiveness using ML patterns."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute_fomo_score(
        self,
        fomo: PublicationLinkFOMO,
    ) -> dict:
        """Compute FOMO effectiveness score (0-100).

        Based on:
        - Urgency trigger type (limited_stock, ending_soon, best_seller)
        - Social proof presence
        - Scarcity message clarity
        - CTA strength
        """
        score = 0.0
        breakdown = {}

        # Urgency trigger weight (40%)
        urgency_score = 0.0
        if fomo.urgency_trigger:
            if fomo.urgency_trigger == "limited_stock":
                urgency_score = 40.0  # Strongest trigger
            elif fomo.urgency_trigger == "ending_soon":
                urgency_score = 35.0
            elif fomo.urgency_trigger == "best_seller":
                urgency_score = 30.0
            else:
                urgency_score = 20.0
        breakdown["urgency"] = urgency_score

        # Social proof (25%)
        social_proof_score = 0.0
        if fomo.social_proof_element:
            # Length of social proof message as proxy
            if len(fomo.social_proof_element) > 50:
                social_proof_score = 25.0
            elif len(fomo.social_proof_element) > 30:
                social_proof_score = 18.0
            else:
                social_proof_score = 12.0
        breakdown["social_proof"] = social_proof_score

        # Scarcity message (20%)
        scarcity_score = 0.0
        if fomo.scarcity_message:
            # Numbers in scarcity = stronger
            if any(char.isdigit() for char in fomo.scarcity_message):
                scarcity_score = 20.0
            else:
                scarcity_score = 14.0
        breakdown["scarcity"] = scarcity_score

        # CTA strength (15%)
        cta_score = 15.0  # All CTAs are non-empty
        if fomo.call_to_action:
            cta_lower = fomo.call_to_action.lower()
            urgent_words = ["now", "today", "before", "hurry", "asap", "immediately"]
            if any(word in cta_lower for word in urgent_words):
                cta_score = 15.0
            else:
                cta_score = 10.0
        breakdown["cta"] = cta_score

        score = sum(breakdown.values())
        return {
            "score": float(min(100.0, score)),
            "breakdown": breakdown,
            "confidence": 0.75,  # Static for now, could be dynamic
        }

    async def predict_conversion_probability(
        self,
        link_id: UUID,
        fomo_id: UUID,
    ) -> dict:
        """Predict probability that this FOMO copy converts.

        Uses historical data from similar links + current metrics.
        Returns: {"probability": 0.0-1.0, "confidence": 0.0-1.0, "reasoning": str}
        """
        fomo = await self.db.execute(
            select(PublicationLinkFOMO).where(PublicationLinkFOMO.id == fomo_id)
        )
        fomo_obj = fomo.scalar_one_or_none()
        if not fomo_obj:
            return {"probability": 0.5, "confidence": 0.0, "reasoning": "FOMO not found"}

        link = await self.db.execute(
            select(PublicationLink).where(PublicationLink.id == link_id)
        )
        link_obj = link.scalar_one_or_none()
        if not link_obj:
            return {"probability": 0.5, "confidence": 0.0, "reasoning": "Link not found"}

        # Get avg CTR for this platform/trigger combo
        result = await self.db.execute(
            select(func.avg(PublicationLinkMetrics.ctr).label("avg_ctr"))
            .join(
                PublicationLinkFOMO,
                PublicationLinkFOMO.link_id == PublicationLinkMetrics.link_id,
            )
            .where(
                PublicationLinkMetrics.platform_name == link_obj.platform_source,
                PublicationLinkFOMO.urgency_trigger == fomo_obj.urgency_trigger,
            )
        )
        platform_ctr = result.scalar() or 0.0

        # Compute FOMO score
        fomo_score_result = await self.compute_fomo_score(fomo_obj)
        fomo_score = fomo_score_result["score"] / 100.0

        # Simple formula: CTR baseline * FOMO multiplier
        baseline_prob = min(0.3, platform_ctr / 100.0) if platform_ctr else 0.15
        predicted_prob = baseline_prob * (1.0 + (fomo_score * 0.5))

        confidence = 0.65 if platform_ctr else 0.45

        return {
            "probability": float(min(0.95, max(0.05, predicted_prob))),
            "confidence": float(confidence),
            "reasoning": f"Platform avg CTR {platform_ctr:.1f}% + FOMO score {fomo_score_result['score']:.0f}/100",
        }

    async def get_credibility_assessment(
        self,
        fomo: PublicationLinkFOMO,
    ) -> dict:
        """Assess if FOMO copy sounds credible or manipulative.

        Red flags:
        - Extreme urgency + no facts
        - Too many exclamation marks
        - Fake scarcity (no numbers)
        """
        credibility = 100.0
        flags = []

        # Check for excessive urgency without proof
        if fomo.urgency_trigger and not fomo.scarcity_message:
            credibility -= 15.0
            flags.append("Urgency without scarcity details")

        # Exclamation mark count
        if fomo.generated_copy:
            exclamation_count = fomo.generated_copy.count("!")
            if exclamation_count > 3:
                credibility -= 10.0
                flags.append(f"Too many exclamation marks ({exclamation_count})")

        # Fake scarcity (vague, no numbers)
        if fomo.scarcity_message:
            has_number = any(char.isdigit() for char in fomo.scarcity_message)
            if not has_number and "left" in fomo.scarcity_message.lower():
                credibility -= 12.0
                flags.append("Vague scarcity (no specific number)")

        # Social proof without context
        if not fomo.social_proof_element and fomo.urgency_trigger == "best_seller":
            credibility -= 8.0
            flags.append("Bestseller claim without proof")

        return {
            "credibility_score": float(max(0.0, credibility)),
            "rating": "trustworthy" if credibility >= 75 else "borderline" if credibility >= 50 else "suspicious",
            "red_flags": flags,
        }
