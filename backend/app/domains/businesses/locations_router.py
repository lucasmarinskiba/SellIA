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
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.auth.models import User
from app.domains.businesses.models import Business
from app.domains.businesses.location_models import Location, LocationCreate, LocationResponse, LocationUpdate, LocationHoursWeekly
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
    db: Session = Depends(get_db),
) -> LocationResponse:
    """Create new physical location for business."""

    # Verify business ownership
    business = db.query(Business).filter(
        Business.id == business_id,
        Business.user_id == current_user.id
    ).first()

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
    db.commit()
    db.refresh(location)

    # Auto-detect localization model based on new location count
    all_locations = db.query(Location).filter(
        Location.business_id == business_id,
        Location.is_active == True
    ).all()

    detected_model = BusinessLocalizationService.detect_model(business, all_locations, db)
    if detected_model != business.localization_model:
        business.localization_model = detected_model
        db.commit()
        logger.info(f"Auto-updated business {business_id} localization to {detected_model}")

    return LocationResponse.model_validate(location)


@router.get(
    "/businesses/{business_id}/locations",
    response_model=List[LocationResponse],
)
async def list_locations(
    business_id: UUID = Path(...),
    active_only: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[LocationResponse]:
    """List all locations for a business."""

    # Verify business ownership
    business = db.query(Business).filter(
        Business.id == business_id,
        Business.user_id == current_user.id
    ).first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    query = db.query(Location).filter(Location.business_id == business_id)

    if active_only:
        query = query.filter(Location.is_active == True)

    locations = query.order_by(Location.created_at.desc()).all()

    return [LocationResponse.model_validate(loc) for loc in locations]


@router.get(
    "/locations/{location_id}",
    response_model=LocationResponse,
)
async def get_location(
    location_id: UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LocationResponse:
    """Get location details."""

    location = db.query(Location).filter(Location.id == location_id).first()

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )

    # Verify user owns the business
    business = db.query(Business).filter(
        Business.id == location.business_id,
        Business.user_id == current_user.id
    ).first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this location"
        )

    return LocationResponse.model_validate(location)


@router.patch(
    "/locations/{location_id}",
    response_model=LocationResponse,
)
async def update_location(
    location_id: UUID = Path(...),
    location_data: LocationUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LocationResponse:
    """Update location details."""

    location = db.query(Location).filter(Location.id == location_id).first()

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )

    # Verify user owns the business
    business = db.query(Business).filter(
        Business.id == location.business_id,
        Business.user_id == current_user.id
    ).first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this location"
        )

    # Update fields
    update_data = location_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(location, key, value)

    db.commit()
    db.refresh(location)

    return LocationResponse.model_validate(location)


@router.delete(
    "/locations/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_location(
    location_id: UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Soft-delete location (sets is_active=False)."""

    location = db.query(Location).filter(Location.id == location_id).first()

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )

    # Verify user owns the business
    business = db.query(Business).filter(
        Business.id == location.business_id,
        Business.user_id == current_user.id
    ).first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this location"
        )

    # Soft delete
    location.is_active = False
    db.commit()

    # Re-detect localization model
    active_locations = db.query(Location).filter(
        Location.business_id == business.id,
        Location.is_active == True
    ).all()

    detected_model = BusinessLocalizationService.detect_model(business, active_locations, db)
    if detected_model != business.localization_model:
        business.localization_model = detected_model
        db.commit()
        logger.info(f"Auto-updated business {business.id} localization to {detected_model} after location deletion")
