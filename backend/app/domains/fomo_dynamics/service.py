"""Phase X6: FOMO Dynamics Service - Ultra-Potent Psychology-Driven FOMO."""
import math
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.domains.fomo_dynamics.models import (
    DynamicOffer, PriceElasticity, FOMOBadge, SocialProofReal, PersonalizedFOMO, FOMOStrategy
)


class FOMODynamicsService:
    @staticmethod
    async def create_dynamic_offer(
        db: AsyncSession,
        business_id: UUID,
        product_id: UUID,
        strategy: FOMOStrategy,
        base_price: float,
        total_stock: Optional[int] = None,
        ends_at: Optional[datetime] = None,
        headline: str = "",
    ) -> DynamicOffer:
        """Create psychological FOMO offer with automatic strategy optimization."""
        offer = DynamicOffer(
            business_id=business_id,
            product_id=product_id,
            strategy=strategy,
            base_price=base_price,
            current_price=base_price,
            total_stock=total_stock,
            ends_at=ends_at,
            headline=headline or FOMODynamicsService._generate_headline(strategy),
            stock_threshold_alert=max(1, (total_stock or 10) // 3),  # Alert at 1/3 remaining
        )
        db.add(offer)
        await db.commit()
        await db.refresh(offer)
        return offer

    @staticmethod
    async def update_price_based_on_demand(
        db: AsyncSession,
        offer_id: UUID,
        purchases_count: int,
    ) -> float:
        """Dynamic pricing: Higher demand = Higher price (scarcity psychology)."""
        offer = await db.get(DynamicOffer, offer_id)
        if not offer:
            return 0

        # Price elasticity: Increase by 2% per 10 purchases
        price_multiplier = 1.0 + (purchases_count / 10) * 0.02
        offer.current_price = round(offer.base_price * price_multiplier, 2)
        offer.price_multiplier = price_multiplier
        offer.discount_percent = ((offer.base_price - offer.current_price) / offer.base_price) * 100

        await db.commit()
        return offer.current_price

    @staticmethod
    async def get_urgency_badge(
        db: AsyncSession,
        offer_id: UUID,
    ) -> Optional[FOMOBadge]:
        """Generate psychological urgency badge."""
        offer = await db.get(DynamicOffer, offer_id)
        if not offer:
            return None

        now = datetime.now(timezone.utc)
        badge_type = None
        badge_text = ""
        urgency_level = 1
        animation_type = "pulse"

        # Stock scarcity (highest urgency)
        if offer.total_stock and offer.stock_taken:
            remaining = offer.total_stock - offer.stock_taken
            if remaining <= (offer.total_stock * 0.1):  # < 10%
                badge_type = "stock_alert"
                badge_text = f"Only {remaining} left in stock!"
                urgency_level = 5
                animation_type = "shake"
            elif remaining <= (offer.total_stock * 0.25):  # < 25%
                badge_type = "stock_alert"
                badge_text = f"Only {remaining} remaining"
                urgency_level = 4
                animation_type = "blink"

        # Time urgency
        elif offer.ends_at:
            time_left = offer.ends_at - now
            hours_left = time_left.total_seconds() / 3600
            if hours_left < 1:
                badge_type = "time_alert"
                badge_text = "Ends in less than 1 hour!"
                urgency_level = 5
                animation_type = "shake"
            elif hours_left < 6:
                badge_type = "time_alert"
                badge_text = f"Ends in {int(hours_left)}h"
                urgency_level = 4
                animation_type = "blink"

        # Price increasing
        elif offer.price_multiplier > 1.1:
            badge_type = "price_increase"
            increase_percent = int((offer.price_multiplier - 1) * 100)
            badge_text = f"Price increased {increase_percent}%"
            urgency_level = 3

        if not badge_type:
            return None

        badge = FOMOBadge(
            offer_id=offer_id,
            badge_type=badge_type,
            urgency_level=urgency_level,
            badge_text=badge_text,
            badge_color="red" if urgency_level >= 4 else "orange",
            animation_type=animation_type,
            animate=urgency_level >= 3,
        )
        db.add(badge)
        await db.commit()
        return badge

    @staticmethod
    async def update_social_proof(
        db: AsyncSession,
        offer_id: UUID,
        new_purchase: bool = False,
        viewer_increment: int = 1,
    ) -> SocialProofReal:
        """Update real-time social proof: "N people bought this today"."""
        offer = await db.get(DynamicOffer, offer_id)
        if not offer:
            return None

        # Get or create social proof
        result = await db.execute(
            select(SocialProofReal).where(SocialProofReal.product_id == offer.product_id)
        )
        proof = result.scalar()
        if not proof:
            proof = SocialProofReal(business_id=offer.business_id, product_id=offer.product_id)
            db.add(proof)

        if new_purchase:
            proof.today_sales += 1
            proof.week_sales += 1
            offer.purchases_count += 1
            offer.stock_taken += 1

            # Auto-update social proof message
            offer.social_proof_message = f"{proof.today_sales} people bought this today"

            # Calculate velocity (units per hour)
            proof.sales_velocity = proof.today_sales  # Simplified

            # Mark as bestseller if velocity high
            if proof.sales_velocity >= 5:
                proof.is_bestseller = True

        proof.recent_views += viewer_increment
        offer.viewers_count += viewer_increment

        await db.commit()
        await db.refresh(proof)
        return proof

    @staticmethod
    async def get_personalized_fomo(
        db: AsyncSession,
        business_id: UUID,
        user_id: UUID,
        product_id: UUID,
        browse_count: int = 1,
    ) -> PersonalizedFOMO:
        """Psychology: Tailor FOMO message based on individual user behavior."""
        # Get or create personalization
        result = await db.execute(
            select(PersonalizedFOMO).where(
                and_(
                    PersonalizedFOMO.business_id == business_id,
                    PersonalizedFOMO.user_id == user_id,
                    PersonalizedFOMO.product_id == product_id,
                )
            )
        )
        fomo = result.scalar()
        if not fomo:
            fomo = PersonalizedFOMO(
                business_id=business_id,
                user_id=user_id,
                product_id=product_id,
            )
            db.add(fomo)

        fomo.browse_count += browse_count

        # Psychology: Different message based on behavior
        if fomo.browse_count >= 3 and not fomo.cart_abandoned:
            fomo.trigger_type = "back_in_stock"
            fomo.persuasion_angle = "scarcity"
            fomo.trigger_message = "⚠️ This item is flying off shelves. Secure yours before it's gone."
            fomo.conversion_probability = 0.65

        elif fomo.cart_abandoned:
            fomo.trigger_type = "abandoned_cart"
            fomo.persuasion_angle = "urgency"
            fomo.trigger_message = "🔥 You left this in your cart. Price increased 5% in the last hour."
            fomo.conversion_probability = 0.75

        elif fomo.previously_purchased:
            fomo.trigger_type = "repeat_buyer"
            fomo.persuasion_angle = "quality"
            fomo.trigger_message = "⭐ Your favorite brand has a new item. Limited quantity available."
            fomo.conversion_probability = 0.55

        elif fomo.browse_count == 1:
            fomo.trigger_type = "trending"
            fomo.persuasion_angle = "social_proof"
            fomo.trigger_message = "🔥 Trending now: {product_name} is #{rank} on our platform"
            fomo.conversion_probability = 0.35

        await db.commit()
        await db.refresh(fomo)
        return fomo

    @staticmethod
    def _generate_headline(strategy: FOMOStrategy) -> str:
        """Psychologically optimized headlines by strategy."""
        headlines = {
            FOMOStrategy.SCARCITY: "Grab yours before stock runs out!",
            FOMOStrategy.URGENCY: "Limited time offer - act now!",
            FOMOStrategy.SOCIAL_PROOF: "Join thousands who love this!",
            FOMOStrategy.EXCLUSIVITY: "VIP access - exclusive offer inside",
            FOMOStrategy.DYNAMIC_PRICING: "Price changing - grab it while available",
            FOMOStrategy.FLASH_SALE: "⚡ Flash Sale! Up to 50% off",
            FOMOStrategy.COUNTDOWN: "⏰ Countdown started - Limited time!",
            FOMOStrategy.PERSONALIZED: "Recommended for you - Don't miss out",
        }
        return headlines.get(strategy, "Don't miss this opportunity!")

    @staticmethod
    async def calculate_conversion_probability(
        db: AsyncSession,
        user_id: UUID,
        product_id: UUID,
        offer_id: UUID,
    ) -> float:
        """ML-inspired: Predict likelihood of purchase based on FOMO signals."""
        offer = await db.get(DynamicOffer, offer_id)
        fomo = await db.execute(
            select(PersonalizedFOMO).where(
                and_(
                    PersonalizedFOMO.user_id == user_id,
                    PersonalizedFOMO.product_id == product_id,
                )
            )
        )
        fomo_record = fomo.scalar()

        probability = 0.3  # Base 30%

        if offer:
            # Scarcity adds urgency
            if offer.total_stock and offer.stock_taken:
                remaining = offer.total_stock - offer.stock_taken
                if remaining < 5:
                    probability += 0.25  # +25%
                elif remaining < 10:
                    probability += 0.15  # +15%

            # Time pressure
            if offer.ends_at:
                time_left = offer.ends_at - datetime.now(timezone.utc)
                hours_left = time_left.total_seconds() / 3600
                if hours_left < 1:
                    probability += 0.25
                elif hours_left < 6:
                    probability += 0.15

            # Social proof
            if offer.purchases_count > 10:
                probability += 0.2

        if fomo_record:
            probability += fomo_record.conversion_probability * 0.5

        return min(1.0, probability)
