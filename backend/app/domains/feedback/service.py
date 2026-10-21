"""Feedback Hub service layer."""

import uuid

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.feedback.models import (
    FeatureFlag,
    FeedbackComment,
    FeedbackStatus,
    FeedbackType,
    FeedbackVote,
    SystemImprovement,
    UserFeedback,
)
from app.domains.feedback.schemas import CommentCreate, FeedbackCreate, FeedbackUpdate


class FeedbackService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ===== Feedback =====

    async def create_feedback(
        self,
        user_id: uuid.UUID,
        data: FeedbackCreate,
        business_id: uuid.UUID | None = None,
    ) -> UserFeedback:
        feedback = UserFeedback(
            user_id=user_id,
            business_id=business_id,
            type=data.type,
            title=data.title,
            description=data.description,
            category=data.category,
            severity=data.severity,
            screenshots=data.screenshots or [],
        )
        self.db.add(feedback)
        await self.db.commit()
        await self.db.refresh(feedback)
        return feedback

    async def get_feedback(self, feedback_id: uuid.UUID) -> UserFeedback | None:
        result = await self.db.execute(
            select(UserFeedback).where(UserFeedback.id == feedback_id)
        )
        return result.scalar_one_or_none()

    async def list_feedback(
        self,
        status: FeedbackStatus | None = None,
        type: FeedbackType | None = None,
        user_id: uuid.UUID | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[UserFeedback], int]:
        query = select(UserFeedback)
        count_query = select(func.count()).select_from(UserFeedback)

        if status:
            query = query.where(UserFeedback.status == status)
            count_query = count_query.where(UserFeedback.status == status)
        if type:
            query = query.where(UserFeedback.type == type)
            count_query = count_query.where(UserFeedback.type == type)
        if user_id:
            query = query.where(UserFeedback.user_id == user_id)
            count_query = count_query.where(UserFeedback.user_id == user_id)
        if search:
            query = query.where(
                UserFeedback.title.ilike(f"%{search}%")
                | UserFeedback.description.ilike(f"%{search}%")
            )
            count_query = count_query.where(
                UserFeedback.title.ilike(f"%{search}%")
                | UserFeedback.description.ilike(f"%{search}%")
            )

        query = (
            query.order_by(
                desc(UserFeedback.votes_count), desc(UserFeedback.created_at)
            )
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(query)
        total_result = await self.db.execute(count_query)
        return list(result.scalars().all()), total_result.scalar() or 0

    async def update_feedback(
        self, feedback_id: uuid.UUID, data: FeedbackUpdate
    ) -> UserFeedback | None:
        feedback = await self.get_feedback(feedback_id)
        if not feedback:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(feedback, field, value)
        await self.db.commit()
        await self.db.refresh(feedback)
        return feedback

    # ===== Votes =====

    async def vote(self, feedback_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        # Check if already voted
        result = await self.db.execute(
            select(FeedbackVote).where(
                FeedbackVote.feedback_id == feedback_id,
                FeedbackVote.user_id == user_id,
            )
        )
        if result.scalar_one_or_none():
            return False

        vote = FeedbackVote(feedback_id=feedback_id, user_id=user_id)
        self.db.add(vote)

        feedback = await self.get_feedback(feedback_id)
        if feedback:
            feedback.votes_count += 1

        await self.db.commit()
        return True

    async def has_voted(self, feedback_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(FeedbackVote).where(
                FeedbackVote.feedback_id == feedback_id,
                FeedbackVote.user_id == user_id,
            )
        )
        return result.scalar_one_or_none() is not None

    # ===== Comments =====

    async def add_comment(
        self,
        feedback_id: uuid.UUID,
        user_id: uuid.UUID,
        data: CommentCreate,
        is_admin: bool = False,
    ) -> FeedbackComment:
        comment = FeedbackComment(
            feedback_id=feedback_id,
            user_id=user_id,
            content=data.content,
            is_admin=is_admin,
        )
        self.db.add(comment)

        feedback = await self.get_feedback(feedback_id)
        if feedback:
            feedback.comments_count += 1

        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def list_comments(self, feedback_id: uuid.UUID) -> list[FeedbackComment]:
        result = await self.db.execute(
            select(FeedbackComment)
            .where(FeedbackComment.feedback_id == feedback_id)
            .order_by(asc(FeedbackComment.created_at))
        )
        return list(result.scalars().all())

    # ===== System Improvements =====

    async def create_improvement(self, data: dict) -> SystemImprovement:
        improvement = SystemImprovement(**data)
        self.db.add(improvement)
        await self.db.commit()
        await self.db.refresh(improvement)
        return improvement

    async def list_improvements(
        self, status: str | None = None
    ) -> list[SystemImprovement]:
        query = select(SystemImprovement)
        if status:
            query = query.where(SystemImprovement.status == status)
        query = query.order_by(desc(SystemImprovement.created_at))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_roadmap(self) -> dict:
        planned = await self.db.execute(
            select(SystemImprovement)
            .where(SystemImprovement.status.in_(["proposed", "approved", "planned"]))
            .order_by(desc(SystemImprovement.created_at))
        )
        in_progress = await self.db.execute(
            select(SystemImprovement)
            .where(SystemImprovement.status == "in_progress")
            .order_by(desc(SystemImprovement.created_at))
        )
        shipped = await self.db.execute(
            select(SystemImprovement)
            .where(SystemImprovement.status.in_(["deployed"]))
            .order_by(desc(SystemImprovement.deployed_at))
        )
        return {
            "planned": list(planned.scalars().all()),
            "in_progress": list(in_progress.scalars().all()),
            "shipped": list(shipped.scalars().all()),
        }

    async def get_changelog(self, limit: int = 20) -> list[SystemImprovement]:
        result = await self.db.execute(
            select(SystemImprovement)
            .where(SystemImprovement.status == "deployed")
            .order_by(desc(SystemImprovement.deployed_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    # ===== Feature Flags =====

    async def get_feature_flags(self) -> list[FeatureFlag]:
        result = await self.db.execute(
            select(FeatureFlag).where(FeatureFlag.is_active == True)
        )
        return list(result.scalars().all())

    async def can_use_feature(
        self, user_plan: str, feature_name: str, user_id: uuid.UUID | None = None
    ) -> bool:
        result = await self.db.execute(
            select(FeatureFlag).where(
                FeatureFlag.name == feature_name, FeatureFlag.is_active == True
            )
        )
        flag = result.scalar_one_or_none()
        if not flag:
            return False

        # Check plan
        if user_plan not in flag.enabled_plans:
            return False

        # Check allowlist
        if (
            flag.user_id_allowlist
            and user_id
            and str(user_id) in flag.user_id_allowlist
        ):
            return True

        # Check rollout percentage (simple hash-based)
        if flag.rollout_percentage < 100 and user_id:
            import hashlib

            hash_val = int(
                hashlib.md5(
                    f"{feature_name}:{user_id}".encode(), usedforsecurity=False
                ).hexdigest(),
                16,
            )
            user_percentile = hash_val % 100
            return user_percentile < flag.rollout_percentage

        return True
