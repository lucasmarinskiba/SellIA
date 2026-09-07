"""Attribution API."""

from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.attribution.attribution_service import AttributionService

router = APIRouter(prefix="/api/v1", tags=["attribution"])


async def _get_business_for_user(business_id: UUID, user: User, db: AsyncSession) -> Business:
    """Same convention as websites.py/catalog.py/channels.py/payments.py.
    All 4 routes below had zero authentication until this fix."""
    result = await db.execute(
        select(Business).where(Business.id == business_id, Business.user_id == user.id)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    return business


class LogTouchpointRequest(BaseModel):
    channel: str
    source: Optional[str] = None
    interaction_type: str


class AttributeRevenueRequest(BaseModel):
    order_id: UUID
    order_value: float
    attribution_model: str


@router.post("/customers/{customer_id}/touchpoints")
async def log_touchpoint(
    customer_id: UUID,
    business_id: UUID,
    request: LogTouchpointRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    return await AttributionService.log_touchpoint(
        business_id, customer_id, request.channel, request.source or "", request.interaction_type, db
    )


@router.post("/businesses/{business_id}/attribute-revenue")
async def attribute_revenue(
    business_id: UUID,
    request: AttributeRevenueRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    return await AttributionService.attribute_revenue(request.order_id, business_id, request.order_value, request.attribution_model, db)


@router.get("/businesses/{business_id}/channel-performance")
async def get_channel_performance(
    business_id: UUID,
    days: int = Query(30),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    return await AttributionService.get_channel_performance(business_id, days, db)


@router.get("/businesses/{business_id}/attribution/metrics")
async def get_metrics(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    return await AttributionService.get_metrics(business_id, db)
