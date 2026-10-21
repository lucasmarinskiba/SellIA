"""Inventory domain — location-based stock management."""

from .inventory_models import (
    FulfillmentMethod,
    FulfillmentRoute,
    LocationInventory,
    LowStockAlert,
    StockMovement,
    StockStatus,
)
from .inventory_service import FulfillmentRoutingService, LocationInventoryService

__all__ = [
    "FulfillmentMethod",
    "FulfillmentRoute",
    "FulfillmentRoutingService",
    "LocationInventory",
    "LocationInventoryService",
    "LowStockAlert",
    "StockMovement",
    "StockStatus"
]
