"""Location-based inventory models — per-location stock tracking."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Numeric, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class StockStatus(str, Enum):
    """Stock level status."""
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"


class FulfillmentMethod(str, Enum):
    """How to fulfill orders from this location."""
    SHIP_FROM_LOCATION = "ship_from_location"
    LOCAL_PICKUP = "local_pickup"
    DEMO_ONLY = "demo_only"  # Location has demo unit but can't ship


class LocationInventory(Base):
    """Product inventory at a specific location."""
    __tablename__ = "location_inventory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Product ref
    product_id = Column(String(255), nullable=False, index=True)  # SKU or product catalog ID
    product_name = Column(String(255), nullable=False)
    product_category = Column(String(100), nullable=True)

    # Stock levels
    quantity_on_hand = Column(Integer, default=0, nullable=False)
    quantity_reserved = Column(Integer, default=0)  # Reserved for pending orders
    quantity_available = Column(Integer, default=0)  # on_hand - reserved
    reorder_point = Column(Integer, default=5)  # Alert when quantity_available <= this

    # Pricing (can override central catalog)
    unit_price = Column(Numeric(10, 2), nullable=False)
    location_price_override = Column(Numeric(10, 2), nullable=True)  # If location has custom pricing

    # Fulfillment config
    fulfillment_method = Column(SQLEnum(FulfillmentMethod), default=FulfillmentMethod.SHIP_FROM_LOCATION)
    shipping_lead_days = Column(Integer, default=2)  # Days to ship from this location

    # Status
    status = Column(SQLEnum(StockStatus), default=StockStatus.IN_STOCK)
    is_demo_unit = Column(Boolean, default=False)  # Location has physical demo (can't ship)
    last_stock_check = Column(DateTime(timezone=True), nullable=True)
    last_reorder_date = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    notes = Column(String(1000), nullable=True)
    metadata = Column(JSONB, default=dict, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    location = relationship("Location", foreign_keys=[location_id])

    __table_args__ = (
        Index("idx_location_product", "location_id", "product_id"),
        Index("idx_business_status", "business_id", "status"),
    )


class StockMovement(Base):
    """Audit trail for inventory changes."""
    __tablename__ = "stock_movements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    inventory_id = Column(UUID(as_uuid=True), ForeignKey("location_inventory.id", ondelete="SET NULL"), nullable=True)

    # Movement details
    movement_type = Column(String(50), nullable=False)  # stock_in, stock_out, demo_checked, reorder, adjustment
    quantity_changed = Column(Integer, nullable=False)
    quantity_before = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)

    # Reason
    reason = Column(String(255), nullable=True)  # e.g., "Customer demo", "Physical stock take", "Online order #123"
    related_order_id = Column(String(255), nullable=True)  # If from online order
    related_checkin_id = Column(UUID(as_uuid=True), nullable=True)  # If from visitor demo

    # Who moved it
    moved_by_staff_id = Column(UUID(as_uuid=True), nullable=True)  # Staff member
    moved_by_system = Column(Boolean, default=False)  # Automated movement

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    location = relationship("Location", foreign_keys=[location_id])

    __table_args__ = (
        Index("idx_location_movement_type", "location_id", "movement_type"),
    )


class LowStockAlert(Base):
    """Track low-stock conditions per location."""
    __tablename__ = "low_stock_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    inventory_id = Column(UUID(as_uuid=True), ForeignKey("location_inventory.id", ondelete="SET NULL"), nullable=True)

    product_id = Column(String(255), nullable=False)
    product_name = Column(String(255), nullable=False)
    quantity_available = Column(Integer, nullable=False)
    reorder_point = Column(Integer, nullable=False)

    # Resolution
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(UUID(as_uuid=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)

    reorder_initiated = Column(Boolean, default=False)
    reorder_quantity = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    location = relationship("Location", foreign_keys=[location_id])

    __table_args__ = (
        Index("idx_location_acknowledged", "location_id", "acknowledged"),
    )


class FulfillmentRoute(Base):
    """Determine which location fulfills online orders based on inventory + location."""
    __tablename__ = "fulfillment_routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    product_id = Column(String(255), nullable=False, index=True)
    order_location_lat = Column(String(50), nullable=False)  # Customer's lat (or warehouse region)
    order_location_lng = Column(String(50), nullable=False)
    order_location_region = Column(String(100), nullable=True)  # e.g., "North", "South", "LATAM"

    # Preferred fulfillment location (ranked)
    fulfillment_location_id_1 = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    fulfillment_location_id_2 = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    fulfillment_location_id_3 = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)

    # Fallback (central warehouse)
    fallback_warehouse_id = Column(String(255), nullable=True)

    # Metrics
    avg_ship_days = Column(Integer, default=2)
    last_used = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_product", "business_id", "product_id"),
    )
