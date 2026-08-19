"""Location inventory service — stock management, fulfillment routing."""

import logging
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional

from sqlalchemy.orm import Session

from app.domains.inventory.inventory_models import (
    LocationInventory, StockMovement, LowStockAlert, FulfillmentRoute,
    StockStatus, FulfillmentMethod
)

logger = logging.getLogger(__name__)


class LocationInventoryService:
    """Manage per-location inventory."""

    @staticmethod
    def get_location_inventory(
        location_id: UUID,
        db: Session
    ) -> list:
        """Get all inventory at location."""
        inventory = db.query(LocationInventory).filter(
            LocationInventory.location_id == location_id
        ).all()
        return inventory

    @staticmethod
    def get_product_at_location(
        location_id: UUID,
        product_id: str,
        db: Session
    ) -> Optional[LocationInventory]:
        """Get inventory for specific product at location."""
        return db.query(LocationInventory).filter(
            LocationInventory.location_id == location_id,
            LocationInventory.product_id == product_id
        ).first()

    @staticmethod
    def update_stock(
        location_id: UUID,
        product_id: str,
        quantity_change: int,
        movement_type: str,
        reason: str = None,
        related_order_id: str = None,
        related_checkin_id: UUID = None,
        staff_id: UUID = None,
        db: Session = None
    ) -> dict:
        """Update stock level + log movement.

        Returns: {success: bool, inventory_id: UUID, quantity_available: int, new_status: str}
        """
        if not db:
            raise ValueError("Database session required")

        inventory = LocationInventoryService.get_product_at_location(
            location_id, product_id, db
        )

        if not inventory:
            raise ValueError(f"Product {product_id} not found at location {location_id}")

        quantity_before = inventory.quantity_available
        inventory.quantity_available = max(0, quantity_before + quantity_change)
        inventory.quantity_on_hand = max(0, inventory.quantity_on_hand + quantity_change)
        inventory.last_stock_check = datetime.now(timezone.utc)

        # Update status
        if inventory.quantity_available <= 0:
            inventory.status = StockStatus.OUT_OF_STOCK
        elif inventory.quantity_available <= inventory.reorder_point:
            inventory.status = StockStatus.LOW_STOCK
        else:
            inventory.status = StockStatus.IN_STOCK

        # Log movement
        movement = StockMovement(
            location_id=location_id,
            business_id=inventory.business_id,
            inventory_id=inventory.id,
            movement_type=movement_type,
            quantity_changed=quantity_change,
            quantity_before=quantity_before,
            quantity_after=inventory.quantity_available,
            reason=reason,
            related_order_id=related_order_id,
            related_checkin_id=related_checkin_id,
            moved_by_staff_id=staff_id,
            moved_by_system=(staff_id is None)
        )

        db.add(movement)

        # Check for low-stock alert
        if inventory.status == StockStatus.LOW_STOCK:
            existing_alert = db.query(LowStockAlert).filter(
                LowStockAlert.inventory_id == inventory.id,
                LowStockAlert.acknowledged == False
            ).first()

            if not existing_alert:
                alert = LowStockAlert(
                    location_id=location_id,
                    business_id=inventory.business_id,
                    inventory_id=inventory.id,
                    product_id=product_id,
                    product_name=inventory.product_name,
                    quantity_available=inventory.quantity_available,
                    reorder_point=inventory.reorder_point
                )
                db.add(alert)
                logger.warning(f"Low stock alert: {product_id} at {location_id}")

        db.commit()
        db.refresh(inventory)

        return {
            "success": True,
            "inventory_id": str(inventory.id),
            "product_id": product_id,
            "quantity_available": inventory.quantity_available,
            "status": inventory.status.value,
            "is_low_stock": inventory.status == StockStatus.LOW_STOCK
        }

    @staticmethod
    def check_stock_for_demo(
        location_id: UUID,
        product_id: str,
        checkin_id: UUID,
        db: Session
    ) -> dict:
        """Check if product available for demo at location. Log demo engagement."""
        inventory = LocationInventoryService.get_product_at_location(
            location_id, product_id, db
        )

        if not inventory:
            return {"available": False, "reason": "Product not found at location"}

        if inventory.quantity_available <= 0:
            return {"available": False, "reason": "Out of stock"}

        # Log demo check
        LocationInventoryService.update_stock(
            location_id=location_id,
            product_id=product_id,
            quantity_change=-1,  # Reserve for demo
            movement_type="demo_checked",
            reason=f"Visitor demo during checkin",
            related_checkin_id=checkin_id,
            db=db
        )

        return {
            "available": True,
            "product_name": inventory.product_name,
            "quantity_available": inventory.quantity_available - 1,
            "demo_unit": inventory.is_demo_unit,
            "fulfillment_method": inventory.fulfillment_method.value
        }

    @staticmethod
    def get_stock_movement_history(
        location_id: UUID,
        product_id: str = None,
        days: int = 30,
        db: Session = None
    ) -> list:
        """Get stock movement history."""
        if not db:
            raise ValueError("Database session required")

        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        query = db.query(StockMovement).filter(
            StockMovement.location_id == location_id,
            StockMovement.created_at >= cutoff
        )

        if product_id:
            query = query.filter(StockMovement.product_id == product_id)

        return query.order_by(StockMovement.created_at.desc()).all()

    @staticmethod
    def acknowledge_low_stock_alert(
        alert_id: UUID,
        staff_id: UUID,
        db: Session
    ) -> dict:
        """Mark low-stock alert as acknowledged."""
        alert = db.query(LowStockAlert).filter(LowStockAlert.id == alert_id).first()

        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        alert.acknowledged = True
        alert.acknowledged_by = staff_id
        alert.acknowledged_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(alert)

        return {
            "acknowledged": True,
            "alert_id": str(alert.id),
            "product_name": alert.product_name
        }

    @staticmethod
    def initiate_reorder(
        alert_id: UUID,
        quantity: int,
        db: Session
    ) -> dict:
        """Initiate reorder for low-stock product."""
        alert = db.query(LowStockAlert).filter(LowStockAlert.id == alert_id).first()

        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        alert.reorder_initiated = True
        alert.reorder_quantity = quantity

        # Log reorder movement
        StockMovement(
            location_id=alert.location_id,
            business_id=alert.business_id,
            inventory_id=alert.inventory_id,
            movement_type="reorder",
            quantity_changed=quantity,
            quantity_before=alert.quantity_available,
            quantity_after=alert.quantity_available,  # Will update on receipt
            reason=f"Reorder initiated for {alert.product_name}",
            moved_by_system=True
        )

        db.commit()
        db.refresh(alert)

        return {
            "reorder_initiated": True,
            "alert_id": str(alert.id),
            "quantity_ordered": quantity
        }


class FulfillmentRoutingService:
    """Determine best location to fulfill online orders."""

    @staticmethod
    def find_best_fulfillment_location(
        business_id: UUID,
        product_id: str,
        customer_lat: float,
        customer_lng: float,
        locations: list,  # List of Location objects
        db: Session = None
    ) -> dict:
        """Find best location to fulfill order based on inventory + proximity.

        Returns: {location_id: UUID, location_name: str, inventory_available: int, est_ship_days: int}
        """
        if not db or not locations:
            return {"error": "No locations available"}

        from app.domains.locations.proximity_engine import ProximityEngine, GeoPoint

        engine = ProximityEngine()
        customer_point = GeoPoint(lat=customer_lat, lng=customer_lng)

        candidates = []

        for loc in locations:
            # Check inventory at location
            inventory = db.query(LocationInventory).filter(
                LocationInventory.location_id == loc.id,
                LocationInventory.product_id == product_id,
                LocationInventory.quantity_available > 0,
                LocationInventory.fulfillment_method != FulfillmentMethod.DEMO_ONLY
            ).first()

            if not inventory:
                continue

            # Calculate distance
            loc_point = GeoPoint(lat=loc.latitude, lng=loc.longitude)
            distance_km = engine.haversine_distance(customer_point, loc_point)

            # Score: distance + inventory level
            score = (distance_km / 100) + (100 / (inventory.quantity_available + 1))

            candidates.append({
                "location_id": loc.id,
                "location_name": loc.name,
                "location_address": loc.address,
                "inventory_available": inventory.quantity_available,
                "distance_km": round(distance_km, 2),
                "est_ship_days": inventory.shipping_lead_days,
                "fulfillment_method": inventory.fulfillment_method.value,
                "score": score
            })

        if not candidates:
            return {"error": "No inventory available at any location"}

        # Sort by score (lower = better)
        best = sorted(candidates, key=lambda x: x["score"])[0]

        return {
            "location_id": str(best["location_id"]),
            "location_name": best["location_name"],
            "location_address": best["location_address"],
            "inventory_available": best["inventory_available"],
            "distance_km": best["distance_km"],
            "est_ship_days": best["est_ship_days"],
            "fulfillment_method": best["fulfillment_method"],
            "alternative_locations": candidates[1:3]  # Next 2 best options
        }

    @staticmethod
    def reserve_inventory_for_order(
        location_id: UUID,
        product_id: str,
        quantity: int,
        order_id: str,
        db: Session
    ) -> dict:
        """Reserve inventory for online order."""
        inventory = db.query(LocationInventory).filter(
            LocationInventory.location_id == location_id,
            LocationInventory.product_id == product_id
        ).first()

        if not inventory:
            raise ValueError(f"Product {product_id} not found at location")

        if inventory.quantity_available < quantity:
            raise ValueError(f"Insufficient stock. Available: {inventory.quantity_available}")

        inventory.quantity_reserved += quantity
        inventory.quantity_available -= quantity

        # Log reservation
        StockMovement(
            location_id=location_id,
            business_id=inventory.business_id,
            inventory_id=inventory.id,
            movement_type="stock_out",
            quantity_changed=-quantity,
            quantity_before=inventory.quantity_available + quantity,
            quantity_after=inventory.quantity_available,
            reason=f"Reserved for online order {order_id}",
            related_order_id=order_id,
            moved_by_system=True
        )

        db.commit()
        db.refresh(inventory)

        logger.info(f"Inventory reserved: {order_id} at {location_id}")

        return {
            "reserved": True,
            "order_id": order_id,
            "location_id": str(location_id),
            "quantity_reserved": quantity,
            "quantity_still_available": inventory.quantity_available
        }

    @staticmethod
    def mark_order_shipped(
        location_id: UUID,
        product_id: str,
        order_id: str,
        db: Session
    ) -> dict:
        """Mark order as shipped. Remove from reserved count."""
        inventory = db.query(LocationInventory).filter(
            LocationInventory.location_id == location_id,
            LocationInventory.product_id == product_id
        ).first()

        if not inventory:
            raise ValueError(f"Product {product_id} not found at location")

        inventory.quantity_reserved = max(0, inventory.quantity_reserved - 1)

        # Log shipment
        StockMovement(
            location_id=location_id,
            business_id=inventory.business_id,
            inventory_id=inventory.id,
            movement_type="stock_out",
            quantity_changed=-1,
            quantity_before=inventory.quantity_available + 1,
            quantity_after=inventory.quantity_available,
            reason=f"Order shipped: {order_id}",
            related_order_id=order_id,
            moved_by_system=True
        )

        db.commit()

        logger.info(f"Order shipped from {location_id}: {order_id}")

        return {
            "shipped": True,
            "order_id": order_id,
            "location_id": str(location_id)
        }
