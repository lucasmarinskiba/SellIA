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
from app.domains.subscriptions.services import check_subscription_limit, track_usage

router = APIRouter()


@router.post("/", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED)
async def create_business(
    business_in: BusinessCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check multi-business limit
    existing_count = await db.execute(
        select(Business).where(Business.user_id == current_user.id, Business.is_active == True)
    )
    business_count = len(existing_count.scalars().all())

    limit_check = await check_subscription_limit(db, current_user.id, "multi_business", quantity=1)
    # multi_business is a boolean limit: if False, only 1 business allowed
    # We treat it as: allowed if business_count < 1 OR limit == -1 (unlimited)
    if limit_check["limit"] != -1 and business_count >= 1 and not limit_check["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu plan no permite múltiples negocios. Actualizá a Pro o Enterprise."
        )

    config = business_in.config or {}
    default_config = DEFAULT_CONFIGS.get(business_in.type, {})
    merged_config = {**default_config, **config}

    business = Business(
        user_id=current_user.id,
        name=business_in.name,
        type=business_in.type,
        description=business_in.description,
        config=merged_config,
    )
    db.add(business)
    await db.commit()
    await db.refresh(business)

    await track_usage(db, current_user.id, "multi_business", quantity=1, business_id=business.id)
    return business


@router.get("/", response_model=list[BusinessResponse])
async def list_businesses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Business).where(Business.user_id == current_user.id, Business.is_active == True)
    )
    return result.scalars().all()


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
