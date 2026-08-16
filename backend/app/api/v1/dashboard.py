"""Dashboard endpoints - home, orders, listings, analytics, settings."""

from fastapi import APIRouter, Query

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(user_id: str = Query(...)):
    """Get dashboard statistics (home page)."""
    return {
        "user_id": user_id,
        "stats": [
            {"label": "Ingresos (30d)", "value": "$47,300", "change": "+12%", "icon": "dollar-sign"},
            {"label": "Órdenes", "value": "234", "change": "+8%", "icon": "shopping-cart"},
            {"label": "Listings activos", "value": "89", "change": "+3%", "icon": "package"},
            {"label": "Tasa de conversión", "value": "4.2%", "change": "+0.5%", "icon": "trending-up"},
        ],
        "recent_orders": [
            {"id": "ORD-001", "product": "iPhone 15 Pro", "platform": "Mercado Libre", "amount": "$999", "status": "Entregado"},
            {"id": "ORD-002", "product": "AirPods Pro", "platform": "Amazon", "amount": "$249", "status": "En tránsito"},
            {"id": "ORD-003", "product": "MacBook Air M3", "platform": "Hotmart", "amount": "$1,299", "status": "Pendiente"},
        ]
    }


@router.get("/orders")
async def get_orders(user_id: str = Query(...), skip: int = 0, limit: int = 10):
    """Get user orders list."""
    orders = [
        {"id": "ORD-001", "date": "2025-01-15", "product": "iPhone 15 Pro", "customer": "Juan López", "platform": "Mercado Libre", "amount": "$999", "status": "Entregado"},
        {"id": "ORD-002", "date": "2025-01-14", "product": "AirPods Pro", "customer": "María García", "platform": "Amazon", "amount": "$249", "status": "En tránsito"},
        {"id": "ORD-003", "date": "2025-01-13", "product": "MacBook Air M3", "customer": "Carlos Rodríguez", "platform": "Hotmart", "amount": "$1,299", "status": "Pendiente"},
        {"id": "ORD-004", "date": "2025-01-12", "product": "iPad Pro 12.9\"", "customer": "Ana Martínez", "platform": "Mercado Libre", "amount": "$799", "status": "Entregado"},
        {"id": "ORD-005", "date": "2025-01-11", "product": "Apple Watch S9", "customer": "Pedro Sánchez", "platform": "Amazon", "amount": "$399", "status": "Entregado"},
    ]
    return {
        "user_id": user_id,
        "total": len(orders),
        "orders": orders[skip : skip + limit]
    }


@router.get("/listings")
async def get_listings(user_id: str = Query(...)):
    """Get user listings."""
    return {
        "user_id": user_id,
        "listings": [
            {"id": "LST-001", "product": "iPhone 15 Pro", "platform": "Mercado Libre", "price": "$999", "stock": 12, "views": 1234, "rating": 4.8},
            {"id": "LST-002", "product": "AirPods Pro", "platform": "Amazon", "price": "$249", "stock": 45, "views": 856, "rating": 4.6},
            {"id": "LST-003", "product": "MacBook Air M3", "platform": "Hotmart", "price": "$1,299", "stock": 5, "views": 432, "rating": 4.9},
            {"id": "LST-004", "product": "iPad Pro 12.9\"", "platform": "Mercado Libre", "price": "$799", "stock": 8, "views": 567, "rating": 4.7},
        ]
    }


@router.get("/analytics")
async def get_analytics(user_id: str = Query(...)):
    """Get analytics metrics."""
    return {
        "user_id": user_id,
        "metrics": [
            {"label": "Ingresos (30d)", "value": "$47,300", "trend": "+12%", "icon": "trending-up"},
            {"label": "Clientes únicos", "value": "234", "trend": "+8%", "icon": "users"},
            {"label": "Tiempo promedio", "value": "2.3h", "trend": "-5%", "icon": "clock"},
            {"label": "Performance", "value": "94%", "trend": "+3%", "icon": "zap"},
        ],
        "trends": {
            "period": "30d",
            "data": [
                {"date": "2025-01-01", "revenue": 1200},
                {"date": "2025-01-02", "revenue": 1500},
                {"date": "2025-01-03", "revenue": 1300},
                {"date": "2025-01-04", "revenue": 1800},
                {"date": "2025-01-05", "revenue": 2100},
            ]
        }
    }


@router.get("/user/settings")
async def get_user_settings(user_id: str = Query(...)):
    """Get user profile settings."""
    return {
        "user_id": user_id,
        "seller_name": "Juan Pérez",
        "business_name": "Tienda de Electrónica Juan",
        "email": "juan@tiendaelectronica.com",
        "phone": "+54 9 11 1234-5678",
        "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=Juan",
    }


@router.put("/user/settings")
async def update_user_settings(user_id: str = Query(...), seller_name: str = None, business_name: str = None):
    """Update user profile settings."""
    return {
        "user_id": user_id,
        "message": "Settings updated successfully",
        "seller_name": seller_name or "Juan Pérez",
        "business_name": business_name or "Tienda de Electrónica Juan",
    }
