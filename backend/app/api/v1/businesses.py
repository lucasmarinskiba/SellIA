import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Any

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.businesses.models import Business, DEFAULT_CONFIGS
from app.domains.businesses.schemas import BusinessCreate, BusinessUpdate, BusinessResponse
from app.domains.subscriptions.services import track_usage

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health():
    """Health check - no dependencies."""
    return {"status": "ok", "service": "businesses"}


@router.post("/test", tags=["debug"])
async def test_endpoint():
    """Minimal test - no dependencies."""
    return {"status": "ok", "endpoint": "business_create_test"}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_business(
    business_in: BusinessCreate,
):
    """Create business - no auth or DB for now to debug dependency issue."""
    return {
        "id": "test-id",
        "user_id": "test-user",
        "name": business_in.name,
        "type": business_in.type,
        "description": business_in.description,
        "config": business_in.config or {},
        "localization_model": "online_only",
        "is_active": True,
        "created_at": "2026-08-25T23:00:00Z",
        "updated_at": "2026-08-25T23:00:00Z"
    }


@router.get("/")
async def list_businesses():
    """List businesses - no auth/DB for debugging."""
    return []


@router.get("/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id,
        )
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    return business


@router.put("/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: UUID,
    business_in: BusinessUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id,
        )
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    update_data = business_in.model_dump(exclude_unset=True)
    if "config" in update_data and business.config:
        update_data["config"] = {**business.config, **update_data["config"]}

    for field, value in update_data.items():
        setattr(business, field, value)

    await db.commit()
    await db.refresh(business)
    return business


@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id,
        )
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    business.is_active = False
    await db.commit()
    return None
