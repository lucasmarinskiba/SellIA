"""Order detail endpoints."""

from fastapi import APIRouter, Query

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/{order_id}")
async def get_order_detail(order_id: str, user_id: str = Query(...)):
    """Get detailed information for a specific order."""
    return {
        "user_id": user_id,
        "order_id": order_id,
        "date": "2025-01-15",
        "status": "Entregado",
        "customer": {
            "name": "Juan López",
            "email": "juan@example.com",
            "phone": "+54 9 11 1234-5678",
        },
        "items": [
            {
                "id": 1,
                "name": "iPhone 15 Pro",
                "sku": "IPHONE-15-PRO",
                "qty": 1,
                "price": "$999",
                "total": "$999"
            }
        ],
        "shipping": {
            "address": "Calle Principal 123, CABA, Argentina",
            "method": "Envío express",
            "cost": "$50",
            "carrier": "Andreani",
            "tracking_number": "AR123456789"
        },
        "timeline": [
            {"date": "2025-01-15 14:30", "status": "Entregado"},
            {"date": "2025-01-15 10:00", "status": "En tránsito"},
            {"date": "2025-01-14 16:00", "status": "Enviado"},
            {"date": "2025-01-15 08:00", "status": "Pagado"},
        ],
        "summary": {
            "subtotal": "$999",
            "shipping": "$50",
            "tax": "$224.75",
            "total": "$1,273.75"
        }
    }


@router.post("/{order_id}/notes")
async def add_order_note(order_id: str, note: str = Query(...), user_id: str = Query(...)):
    """Add internal note to order."""
    return {
        "order_id": order_id,
        "note": note,
        "added_at": "2025-01-15T15:00:00Z",
        "message": "Note added successfully"
    }


@router.post("/{order_id}/resend-confirmation")
async def resend_confirmation(order_id: str, user_id: str = Query(...)):
    """Resend order confirmation to customer."""
    return {
        "order_id": order_id,
        "message": "Confirmation email sent to customer",
        "status": "sent"
    }


@router.post("/{order_id}/cancel")
async def cancel_order(order_id: str, user_id: str = Query(...)):
    """Cancel an order."""
    return {
        "order_id": order_id,
        "message": "Order cancelled successfully",
        "status": "cancelled"
    }
