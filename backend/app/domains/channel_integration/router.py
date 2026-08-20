"""Phase 5C: Channel Integration Endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.core.database import get_db
from app.domains.channel_integration.service import ChannelIntegrationService
from app.domains.channel_integration.models import LocationReview


router = APIRouter(prefix="/api/v1/channel-integration", tags=["channel-integration"])


class LocationMessageCreateRequest(BaseModel):
    channel: str  # sms, whatsapp, email
    trigger_type: str  # proximity, visit_reminder, post_visit, offer
    template: str


class LocationMessageExecuteRequest(BaseModel):
    message_id: UUID
    user_id: Optional[UUID] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    content: Optional[str] = None


class LocationReviewResponse(BaseModel):
    id: UUID
    reviewer_name: str
    rating: float
    review_text: Optional[str]
    platform: str
    review_date: Optional[datetime]
    response_text: Optional[str]

    class Config:
        from_attributes = True


@router.post("/google-business-connect")
def connect_google_business(
    business_id: UUID,
    location_id: UUID,
    google_business_id: str,
    account_name: str,
    access_token: str,
    db: Session = Depends(get_db),
) -> dict:
    """Connect Google Business Profile to location."""
    conn = ChannelIntegrationService.connect_google_business_profile(
        db=db,
        business_id=business_id,
        location_id=location_id,
        google_business_id=google_business_id,
        account_name=account_name,
        access_token=access_token,
    )
    return {
        "id": conn.id,
        "account_name": conn.account_name,
        "is_verified": conn.is_verified,
        "message": "Google Business Profile connected",
    }


@router.post("/location-message/create")
def create_location_message(
    business_id: UUID,
    location_id: UUID,
    req: LocationMessageCreateRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Create location-triggered message template."""
    msg = ChannelIntegrationService.create_location_message(
        db=db,
        business_id=business_id,
        location_id=location_id,
        channel=req.channel,
        trigger_type=req.trigger_type,
        template=req.template,
    )
    return {
        "id": msg.id,
        "channel": msg.channel,
        "trigger_type": msg.trigger_type,
        "message": "Location message created",
    }


@router.post("/location-message/send")
def send_location_message(
    business_id: UUID,
    location_id: UUID,
    req: LocationMessageExecuteRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Execute location message send."""
    execution = ChannelIntegrationService.send_location_message(
        db=db,
        business_id=business_id,
        location_id=location_id,
        message_id=req.message_id,
        user_id=req.user_id,
        phone=req.phone,
        email=req.email,
        content=req.content,
    )
    if not execution:
        return {"error": "Message not found"}
    return {
        "id": execution.id,
        "channel": execution.channel,
        "status": execution.status,
        "sent_at": execution.sent_at,
        "message": "Message sent",
    }


@router.get("/location-reviews")
def get_location_reviews(
    business_id: UUID,
    location_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    """Get all reviews for location."""
    reviews = ChannelIntegrationService.get_location_reviews(db, business_id, location_id)
    avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0
    return {
        "location_id": location_id,
        "total_reviews": len(reviews),
        "avg_rating": round(avg_rating, 2),
        "reviews": [LocationReviewResponse.from_orm(r) for r in reviews],
    }


@router.post("/google-maps-sync")
def sync_google_maps(
    business_id: UUID,
    location_id: UUID,
    place_id: str,
    rating: float = 0,
    review_count: int = 0,
    phone: Optional[str] = None,
    website: Optional[str] = None,
    db: Session = Depends(get_db),
) -> dict:
    """Sync Google Maps location data."""
    maps_loc = ChannelIntegrationService.sync_google_maps_location(
        db=db,
        business_id=business_id,
        location_id=location_id,
        place_id=place_id,
        rating=rating,
        review_count=review_count,
        phone=phone,
        website=website,
    )
    return {
        "id": maps_loc.id,
        "place_id": maps_loc.place_id,
        "rating": maps_loc.rating,
        "review_count": maps_loc.review_count,
        "message": "Google Maps location synced",
    }


@router.post("/add-review")
def add_review(
    business_id: UUID,
    location_id: UUID,
    reviewer_name: str,
    rating: float,
    review_text: Optional[str] = None,
    platform: str = "google",
    db: Session = Depends(get_db),
) -> dict:
    """Add location review."""
    review = ChannelIntegrationService.add_location_review(
        db=db,
        business_id=business_id,
        location_id=location_id,
        reviewer_name=reviewer_name,
        rating=rating,
        review_text=review_text,
        platform=platform,
    )
    return {
        "id": review.id,
        "reviewer_name": review.reviewer_name,
        "rating": review.rating,
        "message": "Review added",
    }
