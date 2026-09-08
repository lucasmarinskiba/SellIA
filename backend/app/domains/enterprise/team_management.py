"""Team management -- backed by the real BusinessMember/DealDelegation
models (app.domains.businesses.team_models) and real Deal assignment
(Deal.assigned_to_user_id), not in-memory dicts keyed by string
concatenation.

Rewrite history: TeamManager used to be a module-level singleton storing
everything in plain dicts (self.members, self.assignments, self.delegations)
keyed by f"{user_id}:{id}" strings -- shared across every business in the
app, lost on every restart. Worse, the app had NO multi-user-per-business
concept at all before this: Business.user_id is a single owner column, and
subscriptions/models.py's pricing tiers already reference a "team_members"
limit that nothing enforced.

Also dropped the original "AgentType" concept (LEAD_SCOUT/CLOSER_BOT/
COACH_AGENT/ANALYTICS_ENGINE assigned to a person, with fabricated
performance numbers via `random.uniform(...)`) -- nothing else in the app
tracks or executes those AI-agent roles, so "assigning" one to a team
member had no real system underneath it. Replaced with the concept that
IS real and already exists: assigning actual Deal ownership
(Deal.assigned_to_user_id) to a team member, and computing performance
metrics FROM those deals' real outcomes (DealOutcome) instead of inventing
numbers. Metrics with no real data source anywhere in the app yet
(avg_response_time, customer_satisfaction, tasks_completed in the general
sense) are returned as None with an honest label rather than a random
number that looks real.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.businesses.team_models import BusinessMember, BusinessMemberRole, DealDelegation
from app.domains.businesses.models import Business
from app.domains.users.models import User
from app.domains.crm.models import Deal, LeadStage


class TeamManager:
    @staticmethod
    async def add_team_member(business_id: UUID, user_id: UUID, role: BusinessMemberRole, db: AsyncSession) -> BusinessMember:
        result = await db.execute(
            select(BusinessMember).where(BusinessMember.business_id == business_id, BusinessMember.user_id == user_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.role = role
            existing.is_active = True
            await db.commit()
            await db.refresh(existing)
            return existing

        member = BusinessMember(business_id=business_id, user_id=user_id, role=role)
        db.add(member)
        await db.commit()
        await db.refresh(member)
        return member

    @staticmethod
    async def remove_team_member(business_id: UUID, user_id: UUID, db: AsyncSession) -> bool:
        result = await db.execute(
            select(BusinessMember).where(BusinessMember.business_id == business_id, BusinessMember.user_id == user_id)
        )
        member = result.scalar_one_or_none()
        if not member:
            return False
        member.is_active = False
        await db.commit()
        return True

    @staticmethod
    async def get_team_members(business_id: UUID, db: AsyncSession) -> list[dict]:
        """Owner (Business.user_id) plus every active BusinessMember row, joined with User for name/email."""
        biz_result = await db.execute(select(Business).where(Business.id == business_id))
        business = biz_result.scalar_one_or_none()
        if not business:
            return []

        owner_result = await db.execute(select(User).where(User.id == business.user_id))
        owner = owner_result.scalar_one_or_none()

        members_result = await db.execute(
            select(BusinessMember, User)
            .join(User, User.id == BusinessMember.user_id)
            .where(BusinessMember.business_id == business_id, BusinessMember.is_active == True)
        )

        result = []
        if owner:
            result.append({
                "user_id": str(owner.id), "name": owner.full_name, "email": owner.email,
                "role": "owner", "joined_at": None,
            })
        for member, user in members_result.all():
            result.append({
                "user_id": str(user.id), "name": user.full_name, "email": user.email,
                "role": member.role.value, "joined_at": member.joined_at.isoformat() if member.joined_at else None,
            })
        return result

    @staticmethod
    async def get_member_role(business_id: UUID, user_id: UUID, db: AsyncSession) -> Optional[str]:
        biz_result = await db.execute(select(Business).where(Business.id == business_id))
        business = biz_result.scalar_one_or_none()
        if business and business.user_id == user_id:
            return "owner"
        result = await db.execute(
            select(BusinessMember).where(
                BusinessMember.business_id == business_id, BusinessMember.user_id == user_id, BusinessMember.is_active == True
            )
        )
        member = result.scalar_one_or_none()
        return member.role.value if member else None

    @staticmethod
    async def assign_deal(business_id: UUID, deal_id: UUID, member_user_id: UUID, db: AsyncSession) -> bool:
        result = await db.execute(select(Deal).where(Deal.id == deal_id, Deal.business_id == business_id))
        deal = result.scalar_one_or_none()
        if not deal:
            return False
        deal.assigned_to_user_id = member_user_id
        await db.commit()
        return True

    @staticmethod
    async def unassign_deal(business_id: UUID, deal_id: UUID, db: AsyncSession) -> bool:
        result = await db.execute(select(Deal).where(Deal.id == deal_id, Deal.business_id == business_id))
        deal = result.scalar_one_or_none()
        if not deal:
            return False
        deal.assigned_to_user_id = None
        await db.commit()
        return True

    @staticmethod
    async def get_member_deals(business_id: UUID, member_user_id: UUID, db: AsyncSession) -> list[Deal]:
        result = await db.execute(
            select(Deal).where(Deal.business_id == business_id, Deal.assigned_to_user_id == member_user_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_member_performance(business_id: UUID, member_user_id: UUID, db: AsyncSession) -> dict:
        """Real metrics computed from Deal + DealOutcome. avg_response_time
        and customer_satisfaction have no data source anywhere in the app
        yet (no per-message response-time log, no CSAT survey feature) --
        returned as None rather than a fabricated number.
        """
        from app.domains.enterprise.forecasting_models import DealOutcome

        deals = await TeamManager.get_member_deals(business_id, member_user_id, db)
        open_deals = [d for d in deals if d.stage not in (LeadStage.CLOSED_WON, LeadStage.CLOSED_LOST)]
        won_deals = [d for d in deals if d.stage == LeadStage.CLOSED_WON]

        outcomes = []
        if deals:
            outcomes_result = await db.execute(
                select(DealOutcome).where(
                    DealOutcome.business_id == business_id, DealOutcome.deal_id.in_([d.id for d in deals])
                )
            )
            outcomes = outcomes_result.scalars().all()

        revenue_generated = sum(float(d.value) for d in won_deals if d.value is not None)

        return {
            "member_user_id": str(member_user_id),
            "deals_assigned": len(deals),
            "deals_open": len(open_deals),
            "deals_won": len(won_deals),
            "win_rate": (len(won_deals) / len(deals)) if deals else None,
            "revenue_generated": revenue_generated,
            "forecast_accuracy": (
                float(sum(o.forecast_accuracy for o in outcomes) / len(outcomes)) if outcomes else None
            ),
            "avg_response_time_seconds": None,  # no per-message response-time tracking exists yet
            "customer_satisfaction": None,  # no CSAT survey feature exists yet
        }

    @staticmethod
    async def get_team_metrics(business_id: UUID, db: AsyncSession) -> dict:
        members = await TeamManager.get_team_members(business_id, db)
        performances = [await TeamManager.get_member_performance(business_id, UUID(m["user_id"]), db) for m in members]

        total_deals_assigned = sum(p["deals_assigned"] for p in performances)
        total_revenue = sum(p["revenue_generated"] for p in performances)
        top_performer = max(performances, key=lambda p: p["revenue_generated"], default=None)

        return {
            "total_members": len(members),
            "total_deals_assigned": total_deals_assigned,
            "total_revenue_generated": total_revenue,
            "top_performer_user_id": top_performer["member_user_id"] if top_performer and top_performer["revenue_generated"] > 0 else None,
            "top_performer_revenue": top_performer["revenue_generated"] if top_performer else 0.0,
        }

    @staticmethod
    async def get_workload_distribution(business_id: UUID, db: AsyncSession) -> dict:
        members = await TeamManager.get_team_members(business_id, db)
        distribution = {}
        for m in members:
            deals = await TeamManager.get_member_deals(business_id, UUID(m["user_id"]), db)
            open_deals = [d for d in deals if d.stage not in (LeadStage.CLOSED_WON, LeadStage.CLOSED_LOST)]
            distribution[m["user_id"]] = {"name": m["name"], "open_deals": len(open_deals), "role": m["role"]}
        return distribution

    @staticmethod
    async def rebalance_unassigned_deals(business_id: UUID, db: AsyncSession) -> dict:
        """Round-robin assign every currently-unassigned open deal across
        active (non-owner-only) team members. Real operation on real data --
        the original mock's "rebalance" reassigned fake in-memory
        AgentAssignment objects with no actual effect on anything.
        """
        members = await TeamManager.get_team_members(business_id, db)
        if not members:
            return {"status": "no_members"}

        result = await db.execute(
            select(Deal).where(
                Deal.business_id == business_id, Deal.assigned_to_user_id.is_(None),
                Deal.stage.notin_([LeadStage.CLOSED_WON, LeadStage.CLOSED_LOST]),
            )
        )
        unassigned_deals = result.scalars().all()

        for i, deal in enumerate(unassigned_deals):
            deal.assigned_to_user_id = UUID(members[i % len(members)]["user_id"])
        await db.commit()

        return {
            "status": "rebalanced",
            "deals_assigned": len(unassigned_deals),
            "members": len(members),
        }

    @staticmethod
    async def create_delegation(
        business_id: UUID, from_user_id: UUID, to_user_id: UUID, deal_ids: list[UUID], reason: str, db: AsyncSession,
        duration_hours: int = 24,
    ) -> DealDelegation:
        from datetime import timedelta

        delegation = DealDelegation(
            business_id=business_id, from_user_id=from_user_id, to_user_id=to_user_id,
            deal_ids=[str(d) for d in deal_ids], reason=reason,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=duration_hours),
        )
        db.add(delegation)
        await db.commit()
        await db.refresh(delegation)
        return delegation

    @staticmethod
    async def decide_delegation(business_id: UUID, delegation_id: UUID, decision: str, db: AsyncSession) -> bool:
        result = await db.execute(
            select(DealDelegation).where(DealDelegation.id == delegation_id, DealDelegation.business_id == business_id)
        )
        delegation = result.scalar_one_or_none()
        if not delegation:
            return False
        delegation.status = decision
        delegation.decided_at = datetime.now(timezone.utc)
        if decision == "approved":
            for deal_id_str in delegation.deal_ids:
                deal_result = await db.execute(select(Deal).where(Deal.id == UUID(deal_id_str)))
                deal = deal_result.scalar_one_or_none()
                if deal:
                    deal.assigned_to_user_id = delegation.to_user_id
        await db.commit()
        return True

    @staticmethod
    async def get_pending_delegations(business_id: UUID, to_user_id: UUID, db: AsyncSession) -> list[DealDelegation]:
        result = await db.execute(
            select(DealDelegation).where(
                DealDelegation.business_id == business_id, DealDelegation.to_user_id == to_user_id,
                DealDelegation.status == "pending",
            )
        )
        return list(result.scalars().all())
