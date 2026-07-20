"""
Fase 3: Unified Dashboard API — agregados multi-plataforma, KPIs, alertas.

Endpoints: GET /dashboard (resumen), /inventory (sync status), /analytics (all platforms), /influencers (performance), /health (sentiment).
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/dashboard", tags=["unified_dashboard"])


@router.get("/overview")
async def get_dashboard_overview(db=Depends()) -> Dict[str, Any]:
    """
    Dashboard overview: inventory, sales, analytics, influencers, sentiment.

    Agregado de todas plataformas en un solo endpoint.
    """

    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)
    last_week = now - timedelta(days=7)

    # Inventory summary
    inventory = await db.query("""
        SELECT
            COUNT(*) as total_skus,
            SUM(quantity) as total_stock,
            COUNT(CASE WHEN quantity = 0 THEN 1 END) as out_of_stock_skus,
            COUNT(CASE WHEN quantity < reorder_point THEN 1 END) as understock_skus
        FROM inventory WHERE enabled = true
    """)

    # Sales summary
    sales_24h = await db.query("""
        SELECT
            COUNT(*) as sales_count,
            SUM(amount) as total_revenue,
            AVG(amount) as avg_order_value
        FROM orders WHERE created_at > %s
    """, [yesterday])

    sales_7d = await db.query("""
        SELECT
            COUNT(*) as sales_count,
            SUM(amount) as total_revenue
        FROM orders WHERE created_at > %s
    """, [last_week])

    # Platform breakdown
    platform_sales = await db.query("""
        SELECT
            platform,
            COUNT(*) as sales,
            SUM(amount) as revenue,
            AVG(amount) as avg_order
        FROM orders
        WHERE created_at > %s
        GROUP BY platform
        ORDER BY revenue DESC
    """, [yesterday])

    # Influencer performance
    influencer_data = await db.query("""
        SELECT
            inf.name,
            COUNT(o.id) as sales,
            SUM(o.amount) as revenue,
            (inf.commission_rate * SUM(o.amount)) as commission_owed
        FROM influencers inf
        LEFT JOIN orders o ON o.promo_code = inf.promo_code AND o.created_at > %s
        WHERE inf.active = true
        GROUP BY inf.id, inf.name
        ORDER BY revenue DESC
    """, [last_week])

    # Sentiment analysis (last 7 days)
    sentiment = await db.query("""
        SELECT
            sentiment,
            COUNT(*) as count
        FROM reviews
        WHERE created_at > %s
        GROUP BY sentiment
    """, [last_week])

    sentiment_dict = {
        "positive": next((s["count"] for s in sentiment if s["sentiment"] == "positive"), 0),
        "neutral": next((s["count"] for s in sentiment if s["sentiment"] == "neutral"), 0),
        "negative": next((s["count"] for s in sentiment if s["sentiment"] == "negative"), 0),
    }

    return {
        "timestamp": now.isoformat(),
        "inventory": {
            "total_skus": inventory[0]["total_skus"] if inventory else 0,
            "total_stock": inventory[0]["total_stock"] if inventory else 0,
            "out_of_stock": inventory[0]["out_of_stock_skus"] if inventory else 0,
            "understock": inventory[0]["understock_skus"] if inventory else 0,
        },
        "sales": {
            "sales_24h": sales_24h[0]["sales_count"] if sales_24h else 0,
            "revenue_24h": float(sales_24h[0]["total_revenue"] or 0) if sales_24h else 0,
            "avg_order_24h": float(sales_24h[0]["avg_order_value"] or 0) if sales_24h else 0,
            "sales_7d": sales_7d[0]["sales_count"] if sales_7d else 0,
            "revenue_7d": float(sales_7d[0]["total_revenue"] or 0) if sales_7d else 0,
        },
        "platform_breakdown": [
            {
                "platform": p["platform"],
                "sales": p["sales"],
                "revenue": float(p["revenue"] or 0),
                "avg_order": float(p["avg_order"] or 0),
            }
            for p in platform_sales
        ],
        "top_influencers": [
            {
                "name": i["name"],
                "sales": i["sales"],
                "revenue": float(i["revenue"] or 0),
                "commission_owed": float(i["commission_owed"] or 0),
            }
            for i in influencer_data[:5]
        ],
        "sentiment": sentiment_dict,
        "health": calculate_health_score(
            inventory[0] if inventory else None,
            sales_24h[0] if sales_24h else None,
            sentiment_dict,
        ),
    }


@router.get("/inventory-sync-status")
async def get_inventory_sync_status(db=Depends()) -> Dict[str, Any]:
    """
    Estado de sincronización de inventario por plataforma.
    """

    sync_status = await db.query("""
        SELECT
            platform,
            COUNT(*) as total_listings,
            COUNT(CASE WHEN last_sync > NOW() - INTERVAL 30 MINUTE THEN 1 END) as synced_last_30m,
            MAX(last_sync) as last_sync_time
        FROM listings
        GROUP BY platform
    """)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "platforms": [
            {
                "platform": s["platform"],
                "total_listings": s["total_listings"],
                "synced_last_30m": s["synced_last_30m"],
                "sync_percentage": (s["synced_last_30m"] / s["total_listings"] * 100) if s["total_listings"] > 0 else 0,
                "last_sync": s["last_sync_time"].isoformat() if s["last_sync_time"] else None,
                "status": "healthy" if (s["synced_last_30m"] / s["total_listings"] > 0.9) if s["total_listings"] > 0 else True else "warning",
            }
            for s in sync_status
        ],
    }


@router.get("/analytics")
async def get_platform_analytics(
    platform: Optional[str] = None,
    days: int = 7,
    db=Depends() = None,
) -> Dict[str, Any]:
    """
    Analytics por plataforma (últimos N días).

    platform: filtrar por una sola (opcional)
    days: cuántos días atrás (default 7)
    """

    cutoff = datetime.utcnow() - timedelta(days=days)

    query = """
        SELECT
            DATE(created_at) as date,
            platform,
            COUNT(*) as sales,
            SUM(amount) as revenue,
            COUNT(DISTINCT customer_id) as unique_customers
        FROM orders
        WHERE created_at > %s
    """

    params = [cutoff]

    if platform:
        query += " AND platform = %s"
        params.append(platform)

    query += " GROUP BY DATE(created_at), platform ORDER BY date DESC"

    analytics = await db.query(query, params)

    # Aggregate by platform
    platform_totals = {}
    for row in analytics:
        plat = row["platform"]
        if plat not in platform_totals:
            platform_totals[plat] = {
                "sales": 0,
                "revenue": 0,
                "customers": 0,
                "daily": [],
            }
        platform_totals[plat]["sales"] += row["sales"]
        platform_totals[plat]["revenue"] += row["revenue"]
        platform_totals[plat]["customers"] += row["unique_customers"]
        platform_totals[plat]["daily"].append({
            "date": row["date"].isoformat(),
            "sales": row["sales"],
            "revenue": float(row["revenue"] or 0),
        })

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "period_days": days,
        "platforms": {
            plat: {
                "total_sales": data["sales"],
                "total_revenue": float(data["revenue"] or 0),
                "unique_customers": data["customers"],
                "avg_order_value": float(data["revenue"] / data["sales"]) if data["sales"] > 0 else 0,
                "daily_breakdown": data["daily"][:days],
            }
            for plat, data in platform_totals.items()
        },
    }


@router.get("/alerts")
async def get_active_alerts(db=Depends()) -> Dict[str, Any]:
    """
    Alertas activas: stockouts, understock, negative reviews, churn signals, sync issues.
    """

    # Stockout alerts
    stockouts = await db.query("SELECT COUNT(*) as count FROM inventory WHERE quantity = 0 AND enabled = true")

    # Understock alerts
    understock = await db.query("SELECT COUNT(*) as count FROM inventory WHERE quantity < reorder_point AND quantity > 0")

    # Negative reviews (últimas 24h)
    negative_reviews = await db.query(
        "SELECT COUNT(*) as count FROM reviews WHERE sentiment = 'negative' AND created_at > NOW() - INTERVAL 1 DAY"
    )

    # Churn signals
    churn_signals = await db.query(
        "SELECT COUNT(*) as count FROM reviews WHERE churn_signal = true AND created_at > NOW() - INTERVAL 7 DAY"
    )

    # Sync failures (últimas 24h)
    sync_failures = await db.query(
        "SELECT COUNT(*) as count FROM sync_logs WHERE status = 'failed' AND created_at > NOW() - INTERVAL 1 DAY"
    )

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "alerts": [
            {
                "type": "STOCKOUT",
                "severity": "CRITICAL",
                "count": stockouts[0]["count"] if stockouts else 0,
                "action": "Reorder immediately",
            },
            {
                "type": "UNDERSTOCK",
                "severity": "WARNING",
                "count": understock[0]["count"] if understock else 0,
                "action": "Monitor inventory levels",
            },
            {
                "type": "NEGATIVE_REVIEWS",
                "severity": "MEDIUM",
                "count": negative_reviews[0]["count"] if negative_reviews else 0,
                "action": "Auto-respond to negative reviews",
            },
            {
                "type": "CHURN_SIGNAL",
                "severity": "MEDIUM",
                "count": churn_signals[0]["count"] if churn_signals else 0,
                "action": "Intervene with customers at risk",
            },
            {
                "type": "SYNC_FAILURE",
                "severity": "HIGH",
                "count": sync_failures[0]["count"] if sync_failures else 0,
                "action": "Check inventory sync configuration",
            },
        ],
    }


def calculate_health_score(
    inventory: Optional[Dict],
    sales: Optional[Dict],
    sentiment: Dict[str, int],
) -> Dict[str, Any]:
    """
    Calcula score de salud general (0-100).

    Factores:
    - Inventory: out of stock = -20
    - Sales: revenue trend
    - Sentiment: % positive reviews
    """

    score = 100

    # Inventory factor
    if inventory:
        if inventory.get("out_of_stock_skus", 0) > 0:
            score -= 20
        if inventory.get("understock_skus", 0) > 5:
            score -= 10

    # Sentiment factor
    total_reviews = sum(sentiment.values())
    if total_reviews > 0:
        negative_pct = sentiment.get("negative", 0) / total_reviews
        if negative_pct > 0.3:  # >30% negative = red flag
            score -= 20
        elif negative_pct > 0.15:  # 15-30% = warning
            score -= 10

    return {
        "score": max(0, score),
        "status": "healthy" if score > 80 else ("warning" if score > 50 else "critical"),
        "trends": ["inventory_healthy", "sales_positive", "sentiment_positive"][:min(score // 40, 3)],
    }
