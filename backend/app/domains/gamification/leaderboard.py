"""Social Leaderboard Service

Makes competition feel warm and supportive — "estamos en esto juntos".
Dopamine-driven: podiums, streak flames, near-overtake messaging.
"""

import uuid
from typing import List, Optional, Dict, Any
from decimal import Decimal

from sqlalchemy import select, func, desc, over
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.gamification.models import UserGamificationProfile
from app.domains.users.models import User
from app.domains.security.models import BusinessUserRole
from app.domains.businesses.models import Business


# Valid metrics for ranking
VALID_METRICS = {
    "total_xp",
    "total_sales_closed",
    "total_revenue_generated",
    "total_referrals_generated",
    "current_login_streak",
    "total_achievements",
}

DEFAULT_METRIC = "total_xp"


class LeaderboardService:
    """Service for social leaderboards within a business."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _get_order_column(self, metric: str):
        """Map metric string to model column."""
        mapping = {
            "total_xp": UserGamificationProfile.total_xp,
            "total_sales_closed": UserGamificationProfile.total_sales_closed,
            "total_revenue_generated": UserGamificationProfile.total_revenue_generated,
            "total_referrals_generated": UserGamificationProfile.total_referrals_generated,
            "current_login_streak": UserGamificationProfile.current_login_streak,
            "total_achievements": UserGamificationProfile.total_achievements,
        }
        return mapping.get(metric, UserGamificationProfile.total_xp)

    async def _check_business_access(
        self, business_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        """Check if user has access to the business."""
        # Superuser bypass
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user and user.is_superuser:
            return True

        # Check BusinessUserRole
        result = await self.db.execute(
            select(BusinessUserRole).where(
                BusinessUserRole.user_id == user_id,
                BusinessUserRole.business_id == business_id,
                BusinessUserRole.is_active == True,
            )
        )
        if result.scalar_one_or_none():
            return True

        # Check business ownership
        result = await self.db.execute(
            select(Business).where(
                Business.id == business_id,
                Business.user_id == user_id,
            )
        )
        if result.scalar_one_or_none():
            return True

        return False

    async def get_leaderboard(
        self,
        business_id: uuid.UUID,
        metric: str = DEFAULT_METRIC,
        period: str = "all_time",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get ranked leaderboard for a business."""
        if metric not in VALID_METRICS:
            metric = DEFAULT_METRIC

        order_col = self._get_order_column(metric)

        # Build query: active BusinessUserRole -> user -> gamification profile
        stmt = (
            select(
                User.id.label("user_id"),
                User.full_name.label("full_name"),
                User.email.label("email"),
                UserGamificationProfile.level.label("level"),
                UserGamificationProfile.total_xp.label("total_xp"),
                UserGamificationProfile.total_sales_closed.label("total_sales_closed"),
                UserGamificationProfile.total_revenue_generated.label("total_revenue_generated"),
                UserGamificationProfile.total_referrals_generated.label("total_referrals_generated"),
                UserGamificationProfile.current_login_streak.label("current_login_streak"),
                UserGamificationProfile.total_achievements.label("total_achievements"),
            )
            .select_from(BusinessUserRole)
            .join(User, BusinessUserRole.user_id == User.id)
            .outerjoin(
                UserGamificationProfile,
                (UserGamificationProfile.user_id == User.id)
                & (UserGamificationProfile.business_id == business_id),
            )
            .where(
                BusinessUserRole.business_id == business_id,
                BusinessUserRole.is_active == True,
                User.is_active == True,
            )
            .order_by(desc(order_col), desc(UserGamificationProfile.total_xp))
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        leaderboard = []
        for rank, row in enumerate(rows, start=1):
            leaderboard.append({
                "rank": rank,
                "user_id": str(row.user_id),
                "full_name": row.full_name or "Sin nombre",
                "email": row.email or "",
                "level": row.level or 1,
                "total_xp": row.total_xp or 0,
                "total_sales_closed": row.total_sales_closed or 0,
                "total_revenue_generated": float(row.total_revenue_generated or 0),
                "total_referrals_generated": row.total_referrals_generated or 0,
                "current_login_streak": row.current_login_streak or 0,
                "total_achievements": row.total_achievements or 0,
            })

        return leaderboard

    async def get_user_rank(
        self,
        business_id: uuid.UUID,
        user_id: uuid.UUID,
        metric: str = DEFAULT_METRIC,
    ) -> Dict[str, Any]:
        """Get a specific user's rank and stats."""
        if metric not in VALID_METRICS:
            metric = DEFAULT_METRIC

        order_col = self._get_order_column(metric)

        # Get all active members ordered by metric
        stmt = (
            select(
                User.id.label("user_id"),
                User.full_name.label("full_name"),
                User.email.label("email"),
                UserGamificationProfile.level.label("level"),
                UserGamificationProfile.total_xp.label("total_xp"),
                UserGamificationProfile.total_sales_closed.label("total_sales_closed"),
                UserGamificationProfile.total_revenue_generated.label("total_revenue_generated"),
                UserGamificationProfile.total_referrals_generated.label("total_referrals_generated"),
                UserGamificationProfile.current_login_streak.label("current_login_streak"),
                UserGamificationProfile.total_achievements.label("total_achievements"),
            )
            .select_from(BusinessUserRole)
            .join(User, BusinessUserRole.user_id == User.id)
            .outerjoin(
                UserGamificationProfile,
                (UserGamificationProfile.user_id == User.id)
                & (UserGamificationProfile.business_id == business_id),
            )
            .where(
                BusinessUserRole.business_id == business_id,
                BusinessUserRole.is_active == True,
                User.is_active == True,
            )
            .order_by(desc(order_col), desc(UserGamificationProfile.total_xp))
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        for rank, row in enumerate(rows, start=1):
            if row.user_id == user_id:
                return {
                    "rank": rank,
                    "total_members": len(rows),
                    "user_id": str(row.user_id),
                    "full_name": row.full_name or "Sin nombre",
                    "email": row.email or "",
                    "level": row.level or 1,
                    "total_xp": row.total_xp or 0,
                    "total_sales_closed": row.total_sales_closed or 0,
                    "total_revenue_generated": float(row.total_revenue_generated or 0),
                    "total_referrals_generated": row.total_referrals_generated or 0,
                    "current_login_streak": row.current_login_streak or 0,
                    "total_achievements": row.total_achievements or 0,
                }

        # User not found in leaderboard — return empty but graceful
        return {
            "rank": None,
            "total_members": len(rows),
            "user_id": str(user_id),
            "full_name": "Sin nombre",
            "email": "",
            "level": 1,
            "total_xp": 0,
            "total_sales_closed": 0,
            "total_revenue_generated": 0.0,
            "total_referrals_generated": 0,
            "current_login_streak": 0,
            "total_achievements": 0,
        }

    async def get_nearby_users(
        self,
        business_id: uuid.UUID,
        user_id: uuid.UUID,
        metric: str = DEFAULT_METRIC,
        radius: int = 2,
    ) -> Dict[str, Any]:
        """Get users ranked near the current user (±radius positions)."""
        if metric not in VALID_METRICS:
            metric = DEFAULT_METRIC

        order_col = self._get_order_column(metric)

        stmt = (
            select(
                User.id.label("user_id"),
                User.full_name.label("full_name"),
                User.email.label("email"),
                UserGamificationProfile.level.label("level"),
                UserGamificationProfile.total_xp.label("total_xp"),
                UserGamificationProfile.total_sales_closed.label("total_sales_closed"),
                UserGamificationProfile.total_revenue_generated.label("total_revenue_generated"),
                UserGamificationProfile.total_referrals_generated.label("total_referrals_generated"),
                UserGamificationProfile.current_login_streak.label("current_login_streak"),
                UserGamificationProfile.total_achievements.label("total_achievements"),
            )
            .select_from(BusinessUserRole)
            .join(User, BusinessUserRole.user_id == User.id)
            .outerjoin(
                UserGamificationProfile,
                (UserGamificationProfile.user_id == User.id)
                & (UserGamificationProfile.business_id == business_id),
            )
            .where(
                BusinessUserRole.business_id == business_id,
                BusinessUserRole.is_active == True,
                User.is_active == True,
            )
            .order_by(desc(order_col), desc(UserGamificationProfile.total_xp))
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        user_index = None
        for idx, row in enumerate(rows):
            if row.user_id == user_id:
                user_index = idx
                break

        if user_index is None:
            return {"user_rank": None, "nearby": []}

        start = max(0, user_index - radius)
        end = min(len(rows), user_index + radius + 1)
        nearby_rows = rows[start:end]

        nearby = []
        for offset, row in enumerate(nearby_rows, start=start):
            nearby.append({
                "rank": offset + 1,
                "user_id": str(row.user_id),
                "full_name": row.full_name or "Sin nombre",
                "email": row.email or "",
                "level": row.level or 1,
                "total_xp": row.total_xp or 0,
                "total_sales_closed": row.total_sales_closed or 0,
                "total_revenue_generated": float(row.total_revenue_generated or 0),
                "total_referrals_generated": row.total_referrals_generated or 0,
                "current_login_streak": row.current_login_streak or 0,
                "total_achievements": row.total_achievements or 0,
            })

        return {
            "user_rank": user_index + 1,
            "metric": metric,
            "nearby": nearby,
        }

    async def get_team_stats(
        self,
        business_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Aggregate stats for the whole business team."""
        # Count active members
        count_stmt = (
            select(func.count(BusinessUserRole.id))
            .join(User, BusinessUserRole.user_id == User.id)
            .where(
                BusinessUserRole.business_id == business_id,
                BusinessUserRole.is_active == True,
                User.is_active == True,
            )
        )
        result = await self.db.execute(count_stmt)
        total_members = result.scalar() or 0

        # Aggregate gamification stats
        agg_stmt = (
            select(
                func.coalesce(func.sum(UserGamificationProfile.total_sales_closed), 0).label("total_sales"),
                func.coalesce(func.sum(UserGamificationProfile.total_revenue_generated), 0).label("total_revenue"),
                func.coalesce(func.avg(UserGamificationProfile.current_login_streak), 0).label("avg_streak"),
            )
            .select_from(BusinessUserRole)
            .join(User, BusinessUserRole.user_id == User.id)
            .outerjoin(
                UserGamificationProfile,
                (UserGamificationProfile.user_id == User.id)
                & (UserGamificationProfile.business_id == business_id),
            )
            .where(
                BusinessUserRole.business_id == business_id,
                BusinessUserRole.is_active == True,
                User.is_active == True,
            )
        )
        result = await self.db.execute(agg_stmt)
        agg = result.one()

        # Top performer by XP
        top_stmt = (
            select(
                User.full_name.label("full_name"),
                UserGamificationProfile.total_xp.label("total_xp"),
            )
            .select_from(BusinessUserRole)
            .join(User, BusinessUserRole.user_id == User.id)
            .outerjoin(
                UserGamificationProfile,
                (UserGamificationProfile.user_id == User.id)
                & (UserGamificationProfile.business_id == business_id),
            )
            .where(
                BusinessUserRole.business_id == business_id,
                BusinessUserRole.is_active == True,
                User.is_active == True,
            )
            .order_by(desc(UserGamificationProfile.total_xp))
            .limit(1)
        )
        result = await self.db.execute(top_stmt)
        top = result.one_or_none()

        return {
            "total_members": total_members,
            "total_sales": int(agg.total_sales or 0),
            "total_revenue": float(agg.total_revenue or 0),
            "avg_streak": round(float(agg.avg_streak or 0), 1),
            "top_performer_name": top.full_name if top else None,
            "top_performer_xp": int(top.total_xp or 0) if top else 0,
        }
