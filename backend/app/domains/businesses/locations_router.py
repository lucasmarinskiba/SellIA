"""API routes for location management.

Endpoints:
- POST /api/v1/businesses/{business_id}/locations
- GET /api/v1/businesses/{business_id}/locations
- GET /api/v1/locations/{location_id}
- PATCH /api/v1/locations/{location_id}
- DELETE /api/v1/locations/{location_id}
"""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.businesses.location_models import (
    Location, LocationCreate, LocationResponse, LocationUpdate, LocationProfileResponse
)
from app.domains.businesses.localization import BusinessLocalizationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["locations"])


@router.post(
    "/businesses/{business_id}/locations",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_location(
    business_id: UUID = Path(...),
    location_data: LocationCreate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LocationResponse:
    """Create new physical location for business."""

    # Verify business ownership
    result = await db.execute(
        select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id
        )
    )
    business = result.scalar_one_or_none()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    # Create location
    location = Location(
        business_id=business_id,
        **location_data.model_dump()
    )

    db.add(location)
    await db.flush()

    # Auto-detect localization model based on new location count
    all_locs_result = await db.execute(
        select(Location).where(
            Location.business_id == business_id,
            Location.is_active == True
        )
    )
    all_locations = all_locs_result.scalars().all()

    detected_model = BusinessLocalizationService.detect_model(business, list(all_locations))
    if detected_model != business.localization_model:
        business.localization_model = detected_model
        logger.info(f"Auto-updated business {business_id} localization to {detected_model}")

    await db.commit()
    await db.refresh(location)

    return LocationResponse.model_validate(location)


@router.get(
    "/businesses/{business_id}/locations",
    response_model=List[LocationResponse],
)
async def list_locations(
    business_id: UUID = Path(...),
    active_only: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[LocationResponse]:
    """List all locations for a business."""

    # Verify business ownership
    result = await db.execute(
        select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id
        )
    )
    business = result.scalar_one_or_none()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    # Query locations
    query = select(Location).where(Location.business_id == business_id)
    if active_only:
        query = query.where(Location.is_active == True)

    locs_result = await db.execute(query)
    locations = locs_result.scalars().all()

    return [LocationResponse.model_validate(loc) for loc in locations]


@router.get(
    "/locations/{location_id}",
    response_model=LocationProfileResponse,
)
async def get_location(
    location_id: UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LocationProfileResponse:
    """Get location with traffic metrics."""

    result = await db.execute(select(Location).where(Location.id == location_id))
    location = result.scalar_one_or_none()

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )

    # Verify user owns this location's business
    biz_result = await db.execute(
        select(Business).where(Business.id == location.business_id)
    )
    business = biz_result.scalar_one_or_none()

    if not business or business.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    location_resp = LocationResponse.model_validate(location)
    return LocationProfileResponse(location=location_resp)


@router.patch(
    "/locations/{location_id}",
    response_model=LocationResponse,
)
async def update_location(
    location_id: UUID = Path(...),
    location_data: LocationUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LocationResponse:
    """Update location details."""

    result = await db.execute(select(Location).where(Location.id == location_id))
    location = result.scalar_one_or_none()

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )

    # Verify ownership
    biz_result = await db.execute(
        select(Business).where(Business.id == location.business_id)
    )
    business = biz_result.scalar_one_or_none()

    if not business or business.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Update fields
    update_data = location_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(location, field, value)

    await db.commit()
    await db.refresh(location)

    return LocationResponse.model_validate(location)


@router.delete(
    "/locations/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_location(
    location_id: UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete location (mark inactive)."""

    result = await db.execute(select(Location).where(Location.id == location_id))
    location = result.scalar_one_or_none()

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )

    # Verify ownership
    biz_result = await db.execute(
        select(Business).where(Business.id == location.business_id)
    )
    business = biz_result.scalar_one_or_none()

    if not business or business.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    location.is_active = False
    await db.commit()
