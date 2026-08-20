"""Phase 3: Channel Routing Endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from app.core.database import get_db
from app.domains.channel_routing.service import ChannelRoutingService


router = APIRouter(prefix="/api/v1/channel-routing", tags=["channel-routing"])


@router.post("/route-message")
async def route_message(
    business_id: UUID,
    customer_id: UUID,
    message_template_id: UUID,
    force_channel: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Route message to optimal channel based on customer affinity."""
    result = await ChannelRoutingService.route_message(
        db, business_id, customer_id, message_template_id, force_channel
    )
    return result


@router.post("/update-affinity")
async def update_affinity(
    business_id: UUID,
    customer_id: UUID,
    channel: str,
    was_delivered: bool,
    was_opened: bool = False,
    was_clicked: bool = False,
    response_time_seconds: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update channel affinity based on message performance."""
    affinity = await ChannelRoutingService.update_channel_affinity(
        db, business_id, customer_id, channel, was_delivered, was_opened, was_clicked, response_time_seconds
    )
    return {
        "customer_id": customer_id,
        "email_affinity": round(affinity.email_score, 2),
        "sms_affinity": round(affinity.sms_score, 2),
        "whatsapp_affinity": round(affinity.whatsapp_score, 2),
        "recommended_primary": affinity.recommended_primary,
        "recommended_secondary": affinity.recommended_secondary,
    }


@router.get("/channel-performance")
async def get_channel_performance(
    business_id: UUID,
    channel: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get channel performance metrics."""
    return await ChannelRoutingService.get_channel_performance(db, business_id, channel)


@router.get("/strategy-recommendation")
async def recommend_channel_strategy(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Recommend optimal channel strategy for business."""
    return await ChannelRoutingService.recommend_channel_strategy(db, business_id)
