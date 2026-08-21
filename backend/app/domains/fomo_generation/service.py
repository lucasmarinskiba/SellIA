"""Phase X10: FOMO Generation Agent Service."""
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.fomo_generation.models import FOMOCampaign, CountdownTrigger


class FOMOGenerationAgent:
    """AI agent for generating personalized FOMO campaigns."""

    @staticmethod
    async def generate_scarcity_fomo(
        db: AsyncSession,
        user_id: str,
        email: str,
        personality_type: str,
        available_slots: int = 3,
        product_name: str = "SellIA Pro",
    ) -> FOMOCampaign:
        """Create scarcity-based FOMO campaign."""

        if personality_type == "skeptic":
            subject = f"Urgent: {available_slots} enterprise seats remaining in cohort"
            body = f"Only {available_slots} slots left for hands-on implementation training. Enterprise clients are filling fast. Dedicated success manager included."
            cta = "Reserve my seat"
        elif personality_type == "impulse_buyer":
            subject = f"⏰ {available_slots} SPOTS LEFT (closes Friday at 5pm)"
            body = f"💥 FLASH: {available_slots} founding members at 60% off. Next cohort: regular price. Claim yours now before they're gone."
            cta = "Grab spot before sold out"
        else:
            subject = f"Last {available_slots} seats: Limited cohort availability"
            body = f"This cohort fills fast. Only {available_slots} spots remain for Q4. Next one isn't until Q1."
            cta = "Secure your spot"

        campaign = FOMOCampaign(
            user_id=user_id,
            email=email,
            fomo_type="scarcity",
            fomo_strategy=f"only_{available_slots}_seats_left",
            subject_line=subject,
            body_message=body,
            cta_text=cta,
            urgency_level=9,
            triggered_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
            time_until_deadline_hours=48,
            personality_type=personality_type,
            motivation_type="exclusivity",
            scarcity_metric=f"{available_slots} seats",
        )
        db.add(campaign)
        await db.commit()
        return campaign

    @staticmethod
    async def generate_social_proof_fomo(
        db: AsyncSession,
        user_id: str,
        email: str,
        personality_type: str,
        total_customers: int = 150,
        product_name: str = "SellIA",
    ) -> FOMOCampaign:
        """Create social-proof-based FOMO."""

        if personality_type == "social_proof_seeker":
            subject = f"Join {total_customers} companies: Slack, HubSpot, Calendly using {product_name}"
            body = f"You're in great company. {total_customers} fast-growing teams already use {product_name} to 3x their sales. See how →"
            cta = "See who's using it"
        else:
            subject = f"{total_customers} companies growing faster with {product_name}"
            body = f"From startups to enterprises, {total_customers} companies trust {product_name}. Don't fall behind."
            cta = "See case studies"

        campaign = FOMOCampaign(
            user_id=user_id,
            email=email,
            fomo_type="social_proof",
            fomo_strategy=f"{total_customers}_companies_using",
            subject_line=subject,
            body_message=body,
            cta_text=cta,
            urgency_level=6,
            triggered_at=datetime.now(timezone.utc),
            personality_type=personality_type,
            motivation_type="belonging",
            social_proof_stat=f"{total_customers} companies",
        )
        db.add(campaign)
        await db.commit()
        return campaign

    @staticmethod
    async def generate_price_increase_fomo(
        db: AsyncSession,
        user_id: str,
        email: str,
        current_price: float = 99,
        future_price: float = 299,
        days_until_increase: int = 2,
    ) -> FOMOCampaign:
        """Create loss-aversion FOMO from price increase."""

        subject = f"Founding price expires in {days_until_increase} days: ${current_price}/mo → ${future_price}/mo"
        body = f"""Only {days_until_increase} days left at founding member price.

Current: ${current_price}/mo
After {days_until_increase} days: ${future_price}/mo
Your annual savings: ${(future_price - current_price) * 12:,.0f}

Lock in the lower price now before it expires."""
        cta = "Lock in $99/mo now"

        campaign = FOMOCampaign(
            user_id=user_id,
            email=email,
            fomo_type="loss_aversion",
            fomo_strategy=f"pricing_increases_in_{days_until_increase}_days",
            subject_line=subject,
            body_message=body,
            cta_text=cta,
            urgency_level=10,
            triggered_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=days_until_increase),
            time_until_deadline_hours=days_until_increase * 24,
            motivation_type="cost_reduction",
            scarcity_metric=f"${current_price}/mo expires in {days_until_increase} days",
        )
        db.add(campaign)
        await db.commit()
        return campaign

    @staticmethod
    async def create_countdown_sequence(
        db: AsyncSession,
        user_id: str,
        trigger_event: str,
        deadline_hours: int = 48,
    ) -> CountdownTrigger:
        """Create multi-touch countdown sequence (24h, 6h, 1h reminders)."""

        now = datetime.now(timezone.utc)
        countdown = CountdownTrigger(
            user_id=user_id,
            trigger_type="pricing_expires",
            trigger_event=trigger_event,
            countdown_start=now,
            countdown_end=now + timedelta(hours=deadline_hours),
            hours_remaining=deadline_hours,
        )
        db.add(countdown)
        await db.commit()
        await db.refresh(countdown)
        return countdown

    @staticmethod
    def get_fomo_effectiveness_score(campaign: FOMOCampaign) -> float:
        """Rate how effective this FOMO campaign was (0-1.0)."""
        if not campaign.sent_at:
            return 0

        # Email engagement → conversion
        opened = 1.0 if campaign.opened_at else 0.5
        clicked = 1.0 if campaign.clicked_at else 0.7 if campaign.opened_at else 0.3
        converted = 2.0 if campaign.converted else 1.0

        # Score = (open + click + conversion) / 4.0
        score = (opened + clicked + converted) / 4.0
        return min(score, 1.0)
