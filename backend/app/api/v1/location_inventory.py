"""Location inventory API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from pydantic import BaseModel
from typing import Optional, List

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.inventory.inventory_service import LocationInventoryService, FulfillmentRoutingService
from app.domains.inventory.inventory_models import LocationInventory

router = APIRouter(prefix="", tags=["inventory"])


class InventoryItem(BaseModel):
    product_id: str
    product_name: str
    quantity_on_hand: int
    quantity_available: int
    reorder_point: int
    status: str
    is_demo_unit: bool = False


class StockUpdateRequest(BaseModel):
    location_id: UUID
    product_id: str
    quantity_change: int
    movement_type: str  # stock_in, stock_out, demo_checked, reorder, adjustment
    reason: Optional[str] = None
    staff_id: Optional[UUID] = None


class DemoCheckRequest(BaseModel):
    location_id: UUID
    product_id: str
    checkin_id: UUID


class FulfillmentRequest(BaseModel):
    business_id: UUID
    product_id: str
    customer_lat: float
    customer_lng: float


class OrderReservationRequest(BaseModel):
    location_id: UUID
    product_id: str
    quantity: int
    order_id: str


@router.get("/locations/{location_id}/inventory")
async def get_location_inventory(
    location_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get all inventory at location."""
    try:
        inventory_list = LocationInventoryService.get_location_inventory(location_id, db)

        items = [
            {
                "inventory_id": str(item.id),
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity_on_hand": item.quantity_on_hand,
                "quantity_available": item.quantity_available,
                "quantity_reserved": item.quantity_reserved,
                "reorder_point": item.reorder_point,
                "status": item.status.value,
                "is_demo_unit": item.is_demo_unit,
                "fulfillment_method": item.fulfillment_method.value,
                "unit_price": float(item.unit_price),
                "last_stock_check": item.last_stock_check.isoformat() if item.last_stock_check else None,
            }
            for item in inventory_list
        ]

        return {
            "location_id": str(location_id),
            "total_items": len(items),
            "inventory": items
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations/{location_id}/inventory/{product_id}")
async def get_product_stock(
    location_id: UUID,
    product_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get stock level for specific product."""
    try:
        inventory = LocationInventoryService.get_product_at_location(location_id, product_id, db)

        if not inventory:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found at location")

        return {
            "location_id": str(location_id),
            "product_id": product_id,
            "product_name": inventory.product_name,
            "quantity_on_hand": inventory.quantity_on_hand,
            "quantity_available": inventory.quantity_available,
            "quantity_reserved": inventory.quantity_reserved,
            "reorder_point": inventory.reorder_point,
            "status": inventory.status.value,
            "is_demo_unit": inventory.is_demo_unit,
            "unit_price": float(inventory.unit_price),
            "fulfillment_method": inventory.fulfillment_method.value,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/inventory/update-stock")
async def update_stock(
    request: StockUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update stock level (restock, manual adjustment, demo usage)."""
    try:
        result = LocationInventoryService.update_stock(
            location_id=request.location_id,
            product_id=request.product_id,
            quantity_change=request.quantity_change,
            movement_type=request.movement_type,
            reason=request.reason,
            staff_id=request.staff_id,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/locations/{location_id}/check-demo-availability")
async def check_demo_stock(
    location_id: UUID,
    request: DemoCheckRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Check if product available for demo during visitor checkin."""
    try:
        result = LocationInventoryService.check_stock_for_demo(
            location_id=request.location_id,
            product_id=request.product_id,
            checkin_id=request.checkin_id,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations/{location_id}/stock-movements")
async def get_stock_history(
    location_id: UUID,
    product_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get stock movement audit trail."""
    try:
        movements = LocationInventoryService.get_stock_movement_history(
            location_id=location_id,
            product_id=product_id,
            days=days,
            db=db
        )

        history = [
            {
                "movement_id": str(m.id),
                "movement_type": m.movement_type,
                "quantity_changed": m.quantity_changed,
                "quantity_before": m.quantity_before,
                "quantity_after": m.quantity_after,
                "reason": m.reason,
                "related_order_id": m.related_order_id,
                "created_at": m.created_at.isoformat(),
            }
            for m in movements
        ]

        return {
            "location_id": str(location_id),
            "product_id": product_id,
            "period_days": days,
            "total_movements": len(history),
            "movements": history
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations/{location_id}/low-stock-alerts")
async def get_low_stock_alerts(
    location_id: UUID,
    acknowledged: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get low-stock alerts for location."""
    try:
        from app.domains.inventory.inventory_models import LowStockAlert

        query = db.query(LowStockAlert).filter(LowStockAlert.location_id == location_id)

        if acknowledged is not None:
            query = query.filter(LowStockAlert.acknowledged == acknowledged)

        alerts = query.all()

        alert_list = [
            {
                "alert_id": str(a.id),
                "product_id": a.product_id,
                "product_name": a.product_name,
                "quantity_available": a.quantity_available,
                "reorder_point": a.reorder_point,
                "acknowledged": a.acknowledged,
                "reorder_initiated": a.reorder_initiated,
                "reorder_quantity": a.reorder_quantity,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ]

        return {
            "location_id": str(location_id),
            "total_alerts": len(alert_list),
            "alerts": alert_list
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/inventory/acknowledge-alert")
async def acknowledge_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark low-stock alert as acknowledged."""
    try:
        result = LocationInventoryService.acknowledge_low_stock_alert(
            alert_id=alert_id,
            staff_id=current_user.id,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/fulfillment/find-location")
async def find_fulfillment_location(
    request: FulfillmentRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Find best location to fulfill online order."""
    try:
        from app.domains.locations.models import Location

        locations = db.query(Location).filter(Location.business_id == request.business_id).all()

        result = FulfillmentRoutingService.find_best_fulfillment_location(
            business_id=request.business_id,
            product_id=request.product_id,
            customer_lat=request.customer_lat,
            customer_lng=request.customer_lng,
            locations=locations,
            db=db
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/orders/reserve-inventory")
async def reserve_inventory(
    request: OrderReservationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Reserve inventory for online order."""
    try:
        result = FulfillmentRoutingService.reserve_inventory_for_order(
            location_id=request.location_id,
            product_id=request.product_id,
            quantity=request.quantity,
            order_id=request.order_id,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/orders/{order_id}/shipped")
async def mark_order_shipped(
    order_id: str,
    location_id: UUID,
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark order as shipped from location."""
    try:
        result = FulfillmentRoutingService.mark_order_shipped(
            location_id=location_id,
            product_id=product_id,
            order_id=order_id,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
