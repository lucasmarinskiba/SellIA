"""Shipments API Router"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.domains.users.models import User
from app.domains.shipments import services as shipment_services
from app.domains.shipments.models import Shipment, ShipmentConfig, ShipmentTrackingEvent
from app.domains.shipments.schemas import (
    ShipmentCreate, ShipmentUpdate, ShipmentResponse, ShipmentDetailResponse,
    ShipmentConfigCreate, ShipmentConfigUpdate, ShipmentConfigResponse,
    RefreshTrackingResponse, NotifyCustomerResponse, CarrierInfo,
)

router = APIRouter()


# ========== Carriers Info ==========

@router.get("/carriers", response_model=list[CarrierInfo])
async def list_carriers(
    current_user: User = Depends(get_current_active_user),
):
    """List all available shipping carriers with metadata."""
    return shipment_services.get_carriers_info()


# ========== Shipment Configs ==========

@router.get("/configs", response_model=list[ShipmentConfigResponse])
async def list_configs(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List shipment configurations for a business."""
    return await shipment_services.list_shipment_configs(db, business_id)


@router.post("/configs", response_model=ShipmentConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_config(
    business_id: UUID,
    data: ShipmentConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a carrier configuration for a business."""
    config = await shipment_services.create_shipment_config(db, business_id, data.model_dump())
    return config


@router.patch("/configs/{config_id}", response_model=ShipmentConfigResponse)
async def update_config(
    config_id: UUID,
    data: ShipmentConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a carrier configuration."""
    config = await shipment_services.get_shipment_config(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return await shipment_services.update_shipment_config(db, config, data.model_dump(exclude_unset=True))


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a carrier configuration."""
    config = await shipment_services.get_shipment_config(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    await shipment_services.delete_shipment_config(db, config)
    return None


@router.post("/configs/{config_id}/test")
async def test_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Test a carrier configuration connection."""
    config = await shipment_services.get_shipment_config(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return await shipment_services.test_shipment_config(db, config)


# ========== Shipments ==========

@router.get("", response_model=dict)
async def list_shipments(
    business_id: UUID,
    status: Optional[str] = None,
    carrier: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List shipments for a business with filters."""
    items, total = await shipment_services.list_shipments(db, business_id, status, carrier, search, limit, offset)
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_shipment(
    data: ShipmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new shipment for an order."""
    try:
        shipment = await shipment_services.create_shipment(db, data.order_id, data.model_dump())
        return shipment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).exception("Error creating shipment")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{shipment_id}", response_model=ShipmentDetailResponse)
async def get_shipment(
    shipment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get shipment details with tracking events."""
    shipment = await shipment_services.get_shipment_with_events(db, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    return shipment


@router.patch("/{shipment_id}", response_model=ShipmentResponse)
async def update_shipment(
    shipment_id: UUID,
    data: ShipmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update shipment details (tracking, status, etc.)."""
    shipment = await shipment_services.get_shipment(db, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    return await shipment_services.update_shipment(db, shipment, data.model_dump(exclude_unset=True))


@router.delete("/{shipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shipment(
    shipment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Cancel / soft-delete a shipment."""
    shipment = await shipment_services.get_shipment(db, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    await shipment_services.cancel_shipment(db, shipment)
    return None


@router.post("/{shipment_id}/refresh-tracking", response_model=RefreshTrackingResponse)
async def refresh_tracking(
    shipment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Refresh tracking info from carrier."""
    shipment = await shipment_services.get_shipment(db, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    return await shipment_services.refresh_tracking(db, shipment)


@router.post("/{shipment_id}/notify-customer", response_model=NotifyCustomerResponse)
async def notify_customer(
    shipment_id: UUID,
    channel: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Send shipping notification to customer."""
    shipment = await shipment_services.get_shipment(db, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    return await shipment_services.notify_customer(db, shipment, channel)
