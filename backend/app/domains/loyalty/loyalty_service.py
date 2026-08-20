"""Loyalty program service — customer retention + rewards."""

import logging
import secrets
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.domains.loyalty.loyalty_models import (
    LoyaltyProgram, LoyaltyMember, LoyaltyReward, LoyaltyTransaction,
    LoyaltyMetrics, MembershipTier, RewardType
)

logger = logging.getLogger(__name__)


class LoyaltyProgramService:
    """Manage loyalty program + member rewards."""

    @staticmethod
    def create_loyalty_program(
        business_id: UUID,
        name: str,
        points_per_dollar: Decimal = Decimal("1.0"),
        welcome_bonus: int = 50,
        db: Session = None
    ) -> dict:
        """Create loyalty program."""
        if not db:
            raise ValueError("Database session required")

        program = LoyaltyProgram(
            business_id=business_id,
            name=name,
            points_per_dollar=points_per_dollar,
            welcome_bonus_points=welcome_bonus
        )

        db.add(program)
        db.commit()
        db.refresh(program)

        logger.info(f"Loyalty program created: {name} for {business_id}")

        return {
            "program_id": str(program.id),
            "name": name,
            "points_per_dollar": float(points_per_dollar),
            "welcome_bonus": welcome_bonus
        }

    @staticmethod
    def enroll_member(
        business_id: UUID,
        customer_id: UUID,
        loyalty_program_id: UUID,
        db: Session = None
    ) -> dict:
        """Enroll customer in loyalty program."""
        if not db:
            raise ValueError("Database session required")

        # Generate member number
        member_number = f"LM{secrets.token_hex(8).upper()}"

        member = LoyaltyMember(
            business_id=business_id,
            customer_id=customer_id,
            loyalty_program_id=loyalty_program_id,
            member_number=member_number,
            current_tier=MembershipTier.BRONZE
        )

        db.add(member)
        db.commit()
        db.refresh(member)

        # Award welcome bonus
        program = db.query(LoyaltyProgram).filter(LoyaltyProgram.id == loyalty_program_id).first()
        if program and program.welcome_bonus_points > 0:
            LoyaltyProgramService.award_points(
                member_id=member.id,
                business_id=business_id,
                points=program.welcome_bonus_points,
                transaction_type="bonus",
                description="Welcome bonus",
                db=db
            )

        logger.info(f"Member enrolled: {member_number} for {customer_id}")

        return {
            "member_id": str(member.id),
            "member_number": member_number,
            "tier": "bronze",
            "current_points": program.welcome_bonus_points if program else 0
        }

    @staticmethod
    def award_points(
        member_id: UUID,
        business_id: UUID,
        points: int,
        transaction_type: str = "earn",
        description: str = None,
        order_id: str = None,
        db: Session = None
    ) -> dict:
        """Award points to member."""
        if not db:
            raise ValueError("Database session required")

        member = db.query(LoyaltyMember).filter(LoyaltyMember.id == member_id).first()
        if not member:
            raise ValueError(f"Member {member_id} not found")

        balance_before = member.current_points_balance
        balance_after = max(0, balance_before + points)

        transaction = LoyaltyTransaction(
            loyalty_member_id=member_id,
            business_id=business_id,
            transaction_type=transaction_type,
            points_change=points,
            balance_before=balance_before,
            balance_after=balance_after,
            order_id=order_id,
            description=description
        )

        member.current_points_balance = balance_after
        member.lifetime_points_earned += max(0, points)

        db.add(transaction)
        db.commit()

        logger.info(f"Points awarded: {member_id} +{points} (total: {balance_after})")

        return {
            "member_id": str(member_id),
            "points_awarded": points,
            "new_balance": balance_after
        }

    @staticmethod
    def redeem_reward(
        member_id: UUID,
        reward_id: UUID,
        business_id: UUID,
        db: Session = None
    ) -> dict:
        """Redeem reward for member."""
        if not db:
            raise ValueError("Database session required")

        member = db.query(LoyaltyMember).filter(LoyaltyMember.id == member_id).first()
        if not member:
            raise ValueError(f"Member {member_id} not found")

        reward = db.query(LoyaltyReward).filter(LoyaltyReward.id == reward_id).first()
        if not reward:
            raise ValueError(f"Reward {reward_id} not found")

        # Check eligibility
        if member.current_points_balance < reward.points_required:
            return {"redemption_successful": False, "reason": "Insufficient points"}

        if member.current_tier.value < reward.min_tier_required.value:
            return {"redemption_successful": False, "reason": "Tier not eligible"}

        # Redeem
        balance_before = member.current_points_balance
        balance_after = balance_before - reward.points_required

        transaction = LoyaltyTransaction(
            loyalty_member_id=member_id,
            business_id=business_id,
            transaction_type="redeem",
            points_change=-reward.points_required,
            balance_before=balance_before,
            balance_after=balance_after,
            reward_id=reward_id,
            description=f"Redeemed: {reward.reward_name}"
        )

        member.current_points_balance = balance_after
        member.points_redeemed_total += reward.points_required
        reward.redemptions_count += 1

        db.add(transaction)
        db.commit()

        logger.info(f"Reward redeemed: {member_id} - {reward.reward_name}")

        return {
            "redemption_successful": True,
            "reward_name": reward.reward_name,
            "points_used": reward.points_required,
            "balance_after": balance_after,
            "reward_value": {
                "type": reward.reward_type.value,
                "discount_pct": float(reward.discount_percentage) if reward.discount_percentage else None,
                "discount_amount": float(reward.discount_fixed_amount) if reward.discount_fixed_amount else None
            }
        }

    @staticmethod
    def update_member_tier(
        member_id: UUID,
        lifetime_spend: Decimal,
        db: Session = None
    ) -> dict:
        """Update member tier based on lifetime spend."""
        if not db:
            raise ValueError("Database session required")

        member = db.query(LoyaltyMember).filter(LoyaltyMember.id == member_id).first()
        if not member:
            raise ValueError(f"Member {member_id} not found")

        program = db.query(LoyaltyProgram).filter(
            LoyaltyProgram.id == member.loyalty_program_id
        ).first()

        old_tier = member.current_tier

        # Determine new tier
        if lifetime_spend >= program.platinum_threshold:
            new_tier = MembershipTier.PLATINUM
        elif lifetime_spend >= program.gold_threshold:
            new_tier = MembershipTier.GOLD
        elif lifetime_spend >= program.silver_threshold:
            new_tier = MembershipTier.SILVER
        else:
            new_tier = MembershipTier.BRONZE

        if new_tier != old_tier:
            member.current_tier = new_tier
            member.tier_since = datetime.now(timezone.utc)
            db.commit()

            logger.info(f"Tier updated: {member_id} {old_tier.value} -> {new_tier.value}")

            return {
                "tier_updated": True,
                "old_tier": old_tier.value,
                "new_tier": new_tier.value,
                "tier_multiplier": float(getattr(program, f"{new_tier.value}_bonus_points", 1))
            }

        return {"tier_updated": False, "current_tier": old_tier.value}

    @staticmethod
    def create_reward_offer(
        loyalty_program_id: UUID,
        business_id: UUID,
        reward_name: str,
        reward_type: str,
        points_required: int,
        value: Decimal = None,
        db: Session = None
    ) -> dict:
        """Create reward offer."""
        if not db:
            raise ValueError("Database session required")

        reward = LoyaltyReward(
            loyalty_program_id=loyalty_program_id,
            business_id=business_id,
            reward_name=reward_name,
            reward_type=RewardType[reward_type.upper()],
            points_required=points_required
        )

        if reward_type == "discount_percentage":
            reward.discount_percentage = value
        elif reward_type == "discount_fixed":
            reward.discount_fixed_amount = value

        db.add(reward)
        db.commit()
        db.refresh(reward)

        logger.info(f"Reward created: {reward_name} for {loyalty_program_id}")

        return {
            "reward_id": str(reward.id),
            "reward_name": reward_name,
            "points_required": points_required,
            "type": reward_type
        }

    @staticmethod
    def get_member_details(
        member_id: UUID,
        db: Session = None
    ) -> dict:
        """Get member profile + points balance."""
        if not db:
            raise ValueError("Database session required")

        member = db.query(LoyaltyMember).filter(LoyaltyMember.id == member_id).first()
        if not member:
            raise ValueError(f"Member {member_id} not found")

        # Recent transactions
        recent_txns = db.query(LoyaltyTransaction).filter(
            LoyaltyTransaction.loyalty_member_id == member_id
        ).order_by(LoyaltyTransaction.created_at.desc()).limit(10).all()

        return {
            "member_id": str(member.id),
            "member_number": member.member_number,
            "customer_id": str(member.customer_id),
            "tier": member.current_tier.value,
            "tier_since": member.tier_since.isoformat() if member.tier_since else None,
            "lifetime_spend": float(member.lifetime_spend),
            "lifetime_purchases": member.total_purchases,
            "points": {
                "current_balance": member.current_points_balance,
                "lifetime_earned": member.lifetime_points_earned,
                "lifetime_redeemed": member.points_redeemed_total
            },
            "engagement": {
                "last_purchase": member.last_purchase_date.isoformat() if member.last_purchase_date else None,
                "days_since_purchase": member.days_since_purchase,
                "referral_code": member.referral_code,
                "referrals_made": member.referral_count
            },
            "churn_risk": member.churn_risk,
            "recent_activity": [
                {
                    "type": t.transaction_type,
                    "points": t.points_change,
                    "balance": t.balance_after,
                    "date": t.created_at.isoformat()
                }
                for t in recent_txns
            ]
        }

    @staticmethod
    def calculate_loyalty_metrics(
        business_id: UUID,
        date: str = None,
        db: Session = None
    ) -> dict:
        """Calculate aggregate loyalty program metrics."""
        if not db:
            raise ValueError("Database session required")

        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Member counts
        total_members = db.query(LoyaltyMember).filter(
            LoyaltyMember.business_id == business_id
        ).count()

        active_members = db.query(LoyaltyMember).filter(
            LoyaltyMember.business_id == business_id,
            LoyaltyMember.is_active == True
        ).count()

        # Tier distribution
        tiers = db.query(LoyaltyMember.current_tier, func.count(LoyaltyMember.id)).filter(
            LoyaltyMember.business_id == business_id
        ).group_by(LoyaltyMember.current_tier).all()

        tier_dist = {t[0].value: t[1] for t in tiers}

        # Points
        points_issued = db.query(func.sum(LoyaltyTransaction.points_change)).filter(
            LoyaltyTransaction.business_id == business_id,
            LoyaltyTransaction.transaction_type == "earn"
        ).scalar() or 0

        points_redeemed = db.query(func.sum(LoyaltyTransaction.points_change)).filter(
            LoyaltyTransaction.business_id == business_id,
            LoyaltyTransaction.transaction_type == "redeem"
        ).scalar() or 0

        # Create metrics record
        metrics = LoyaltyMetrics(
            business_id=business_id,
            date=date,
            total_members=total_members,
            active_members=active_members,
            bronze_members=tier_dist.get("bronze", 0),
            silver_members=tier_dist.get("silver", 0),
            gold_members=tier_dist.get("gold", 0),
            platinum_members=tier_dist.get("platinum", 0),
            total_points_issued=int(points_issued),
            total_points_redeemed=abs(int(points_redeemed))
        )

        db.add(metrics)
        db.commit()

        logger.info(f"Loyalty metrics calculated: {business_id} - {date}")

        return {
            "metrics_calculated": True,
            "date": date,
            "members": {
                "total": total_members,
                "active": active_members,
                "bronze": tier_dist.get("bronze", 0),
                "silver": tier_dist.get("silver", 0),
                "gold": tier_dist.get("gold", 0),
                "platinum": tier_dist.get("platinum", 0)
            },
            "points": {
                "issued": int(points_issued),
                "redeemed": abs(int(points_redeemed))
            }
        }
