"""Phase 5C: Channel Integration Service."""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from app.domains.channel_integration.models import (
    GoogleBusinessProfileConnection,
    GoogleMapsLocation,
    LocationMessage,
    LocationMessageExecution,
    LocationReview,
)


class ChannelIntegrationService:
    @staticmethod
    async def connect_google_business_profile(
        db: AsyncSession,
        business_id: UUID,
        location_id: UUID,
        google_business_id: str,
        account_name: str,
        access_token: str,
    ) -> GoogleBusinessProfileConnection:
        conn = GoogleBusinessProfileConnection(
            business_id=business_id,
            location_id=location_id,
            google_business_id=google_business_id,
            account_name=account_name,
            access_token=access_token,
        )
        db.add(conn)
        await db.commit()
        await db.refresh(conn)
        return conn

    @staticmethod
    async def create_location_message(
        db: AsyncSession,
        business_id: UUID,
        location_id: UUID,
        channel: str,
        trigger_type: str,
        template: str,
    ) -> LocationMessage:
        msg = LocationMessage(
            business_id=business_id,
            location_id=location_id,
            channel=channel,
            trigger_type=trigger_type,
            template=template,
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg

    @staticmethod
    async def send_location_message(
        db: AsyncSession,
        business_id: UUID,
        location_id: UUID,
        message_id: UUID,
        user_id: Optional[UUID] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        content: Optional[str] = None,
    ) -> LocationMessageExecution:
        result = await db.execute(select(LocationMessage).where(LocationMessage.id == message_id))
        msg = result.scalar()
        if not msg:
            return None

        execution = LocationMessageExecution(
            business_id=business_id,
            location_id=location_id,
            message_id=message_id,
            user_id=user_id,
            phone=phone,
            email=email,
            channel=msg.channel,
            message_content=content or msg.template,
            status="sent",
        )
        db.add(execution)
        await db.commit()
        await db.refresh(execution)
        return execution

    @staticmethod
    async def get_location_reviews(
        db: AsyncSession,
        business_id: UUID,
        location_id: UUID,
    ) -> List[LocationReview]:
        result = await db.execute(
            select(LocationReview).where(
                and_(
                    LocationReview.business_id == business_id,
                    LocationReview.location_id == location_id,
                )
            ).order_by(LocationReview.review_date.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def sync_google_maps_location(
        db: AsyncSession,
        business_id: UUID,
        location_id: UUID,
        place_id: str,
        rating: float = 0,
        review_count: int = 0,
        phone: Optional[str] = None,
        website: Optional[str] = None,
    ) -> GoogleMapsLocation:
        result = await db.execute(
            select(GoogleMapsLocation).where(
                and_(
                    GoogleMapsLocation.location_id == location_id,
                    GoogleMapsLocation.business_id == business_id,
                )
            )
        )
        existing = result.scalar()

        if existing:
            existing.place_id = place_id
            existing.rating = rating
            existing.review_count = review_count
            existing.phone = phone
            existing.website = website
            existing.last_updated = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(existing)
            return existing

        maps_loc = GoogleMapsLocation(
            business_id=business_id,
            location_id=location_id,
            place_id=place_id,
            rating=rating,
            review_count=review_count,
            phone=phone,
            website=website,
        )
        db.add(maps_loc)
        await db.commit()
        await db.refresh(maps_loc)
        return maps_loc

    @staticmethod
    async def add_location_review(
        db: AsyncSession,
        business_id: UUID,
        location_id: UUID,
        reviewer_name: str,
        rating: float,
        review_text: Optional[str] = None,
        platform: str = "google",
        review_date: Optional[datetime] = None,
    ) -> LocationReview:
        review = LocationReview(
            business_id=business_id,
            location_id=location_id,
            reviewer_name=reviewer_name,
            rating=rating,
            review_text=review_text,
            platform=platform,
            review_date=review_date or datetime.now(timezone.utc),
        )
        db.add(review)
        await db.commit()
        await db.refresh(review)
        return review
