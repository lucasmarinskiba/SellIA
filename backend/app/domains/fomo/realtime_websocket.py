"""Real-time WebSocket Manager - Live FOMO widget updates"""

from datetime import datetime
from typing import Dict, List, Set, Optional, Any
import asyncio
import json
from enum import Enum


class WebSocketEventType(str, Enum):
    VISITOR_COUNT_UPDATED = "visitor_count_updated"
    PURCHASE_NOTIFICATION = "purchase_notification"
    COUNTDOWN_TICK = "countdown_tick"
    STOCK_UPDATED = "stock_updated"
    CONVERSION_MILESTONE = "conversion_milestone"
    REVENUE_UPDATE = "revenue_update"
    WIDGET_CLICK = "widget_click"
    CAMPAIGN_STATUS = "campaign_status"
    ANALYTICS_SYNC = "analytics_sync"


class WebSocketConnectionPool:
    """Manage WebSocket connections for real-time updates"""

    def __init__(self):
        self.connections: Dict[str, Set[Any]] = {}  # campaign_id -> set of connections
        self.user_subscriptions: Dict[str, Set[str]] = {}  # user_id -> set of campaign_ids

    async def register_connection(
        self,
        campaign_id: str,
        user_id: str,
        connection: Any
    ) -> Dict[str, Any]:
        """Register new WebSocket connection"""
        if campaign_id not in self.connections:
            self.connections[campaign_id] = set()

        self.connections[campaign_id].add(connection)

        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()

        self.user_subscriptions[user_id].add(campaign_id)

        return {
            "status": "connected",
            "campaign_id": campaign_id,
            "active_connections": len(self.connections[campaign_id]),
        }

    async def unregister_connection(
        self,
        campaign_id: str,
        user_id: str,
        connection: Any
    ):
        """Unregister WebSocket connection"""
        if campaign_id in self.connections:
            self.connections[campaign_id].discard(connection)

        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(campaign_id)

    async def broadcast_to_campaign(
        self,
        campaign_id: str,
        event: Dict[str, Any]
    ):
        """Broadcast event to all connections for a campaign"""
        if campaign_id not in self.connections:
            return

        disconnected = []
        for connection in self.connections[campaign_id]:
            try:
                await connection.send_json(event)
            except Exception:
                disconnected.append(connection)

        # Clean up disconnected connections
        for conn in disconnected:
            self.connections[campaign_id].discard(conn)

    async def get_active_connections_count(self, campaign_id: str) -> int:
        """Get number of active connections for a campaign"""
        return len(self.connections.get(campaign_id, set()))


class RealtimeDataStreamer:
    """Stream real-time FOMO data via WebSocket"""

    @staticmethod
    def create_visitor_update(
        campaign_id: str,
        visitor_count: int,
        trend: str = "up"
    ) -> Dict[str, Any]:
        """Create visitor count update"""
        return {
            "type": WebSocketEventType.VISITOR_COUNT_UPDATED.value,
            "campaign_id": campaign_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "visitor_count": visitor_count,
                "trend": trend,
                "updated_at": datetime.utcnow().isoformat(),
            }
        }

    @staticmethod
    def create_purchase_notification(
        campaign_id: str,
        customer_name: str,
        product_name: str,
        price: float,
        minutes_ago: int = 0
    ) -> Dict[str, Any]:
        """Create purchase notification"""
        return {
            "type": WebSocketEventType.PURCHASE_NOTIFICATION.value,
            "campaign_id": campaign_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "customer_name": customer_name,
                "product_name": product_name,
                "price": price,
                "time_display": f"{minutes_ago}m ago" if minutes_ago > 0 else "just now",
                "anonymized": False,
            }
        }

    @staticmethod
    def create_countdown_tick(
        campaign_id: str,
        time_remaining_seconds: int,
        stage: str  # "active" | "warning" | "critical"
    ) -> Dict[str, Any]:
        """Create countdown timer tick"""
        hours = time_remaining_seconds // 3600
        minutes = (time_remaining_seconds % 3600) // 60
        seconds = time_remaining_seconds % 60

        return {
            "type": WebSocketEventType.COUNTDOWN_TICK.value,
            "campaign_id": campaign_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "time_remaining_seconds": time_remaining_seconds,
                "time_display": f"{hours}h {minutes}m {seconds}s",
                "stage": stage,
                "percentage_remaining": (time_remaining_seconds / (24 * 3600)) * 100,
            }
        }

    @staticmethod
    def create_stock_update(
        campaign_id: str,
        current_stock: int,
        original_stock: int
    ) -> Dict[str, Any]:
        """Create stock level update"""
        percentage_sold = ((original_stock - current_stock) / original_stock) * 100
        stage = "plenty" if current_stock > 20 else ("medium" if current_stock > 5 else "critical")

        return {
            "type": WebSocketEventType.STOCK_UPDATED.value,
            "campaign_id": campaign_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "current_stock": current_stock,
                "original_stock": original_stock,
                "percentage_sold": percentage_sold,
                "stage": stage,
                "message": {
                    "plenty": f"{current_stock} in stock",
                    "medium": f"Only {current_stock} left!",
                    "critical": f"LAST {current_stock}! Hurry!",
                }.get(stage)
            }
        }

    @staticmethod
    def create_conversion_milestone(
        campaign_id: str,
        milestone_number: int,
        total_revenue: float
    ) -> Dict[str, Any]:
        """Create conversion milestone alert"""
        return {
            "type": WebSocketEventType.CONVERSION_MILESTONE.value,
            "campaign_id": campaign_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "milestone_conversions": milestone_number,
                "total_revenue": total_revenue,
                "message": f"🎉 {milestone_number} conversions reached!",
                "milestone_reached_at": datetime.utcnow().isoformat(),
            }
        }

    @staticmethod
    def create_analytics_sync(
        campaign_id: str,
        analytics_snapshot: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create analytics snapshot for sync"""
        return {
            "type": WebSocketEventType.ANALYTICS_SYNC.value,
            "campaign_id": campaign_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "impressions": analytics_snapshot.get("impressions", 0),
                "clicks": analytics_snapshot.get("clicks", 0),
                "conversions": analytics_snapshot.get("conversions", 0),
                "revenue": analytics_snapshot.get("revenue", 0),
                "ctr": analytics_snapshot.get("ctr", 0),
                "conversion_rate": analytics_snapshot.get("conversion_rate", 0),
                "roi": analytics_snapshot.get("roi", 0),
            }
        }


class RealtimeMetricsAggregator:
    """Aggregate and stream real-time metrics"""

    @staticmethod
    def calculate_live_metrics(
        impressions: int,
        clicks: int,
        conversions: int,
        revenue: float
    ) -> Dict[str, Any]:
        """Calculate live performance metrics"""
        return {
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "revenue": revenue,
            "ctr": clicks / impressions if impressions > 0 else 0,
            "conversion_rate": conversions / clicks if clicks > 0 else 0,
            "aov": revenue / conversions if conversions > 0 else 0,
            "revenue_per_impression": revenue / impressions if impressions > 0 else 0,
            "updated_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def create_hourly_summary(
        hour: str,  # "2026-08-28T14:00:00Z"
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create hourly performance summary"""
        return {
            "hour": hour,
            "metrics": metrics,
            "comparison_to_previous_hour": {
                "impressions_change": "+12%",
                "conversions_change": "+18%",
                "revenue_change": "+15%",
            }
        }

    @staticmethod
    def create_live_dashboard_update(
        campaign_id: str,
        current_hour_metrics: Dict[str, Any],
        top_products: List[Dict[str, Any]],
        top_locations: List[Dict[str, Any]],
        referral_sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create comprehensive live dashboard update"""
        return {
            "type": "dashboard_update",
            "campaign_id": campaign_id,
            "timestamp": datetime.utcnow().isoformat(),
            "current_hour": current_hour_metrics,
            "top_3_products": top_products[:3],
            "top_3_locations": top_locations[:3],
            "referral_sources": referral_sources,
            "active_visitors": current_hour_metrics.get("impressions", 0),
            "conversion_streak": "15 conversions in last 30 min",
            "alerts": [
                {"type": "success", "message": "Conversion rate at 1.8% (goal: 1.5%)"},
                {"type": "info", "message": "Traffic peak detected - 28% above average"},
            ]
        }


class WebSocketHeartbeat:
    """Maintain WebSocket connections with heartbeats"""

    @staticmethod
    async def send_heartbeat(
        connection: Any,
        campaign_id: str,
        connection_duration_seconds: int
    ):
        """Send periodic heartbeat to keep connection alive"""
        heartbeat = {
            "type": "heartbeat",
            "campaign_id": campaign_id,
            "timestamp": datetime.utcnow().isoformat(),
            "connection_duration_seconds": connection_duration_seconds,
            "status": "alive"
        }
        try:
            await connection.send_json(heartbeat)
        except Exception:
            pass

    @staticmethod
    async def start_heartbeat_loop(
        connection: Any,
        campaign_id: str,
        interval_seconds: int = 30
    ):
        """Start periodic heartbeat"""
        start_time = datetime.utcnow()
        while True:
            try:
                duration = (datetime.utcnow() - start_time).total_seconds()
                await WebSocketHeartbeat.send_heartbeat(
                    connection,
                    campaign_id,
                    int(duration)
                )
                await asyncio.sleep(interval_seconds)
            except Exception:
                break


class WebSocketBroadcaster:
    """Broadcast FOMO events to multiple campaigns"""

    def __init__(self):
        self.pool = WebSocketConnectionPool()
        self.event_queue: asyncio.Queue = asyncio.Queue()

    async def broadcast_visitor_event(
        self,
        campaign_id: str,
        visitor_count: int,
        trend: str = "up"
    ):
        """Broadcast visitor count update"""
        event = RealtimeDataStreamer.create_visitor_update(campaign_id, visitor_count, trend)
        await self.pool.broadcast_to_campaign(campaign_id, event)

    async def broadcast_purchase_event(
        self,
        campaign_id: str,
        customer_name: str,
        product_name: str,
        price: float
    ):
        """Broadcast purchase notification"""
        event = RealtimeDataStreamer.create_purchase_notification(
            campaign_id, customer_name, product_name, price
        )
        await self.pool.broadcast_to_campaign(campaign_id, event)

    async def broadcast_countdown_tick(
        self,
        campaign_id: str,
        time_remaining_seconds: int,
        stage: str
    ):
        """Broadcast countdown update"""
        event = RealtimeDataStreamer.create_countdown_tick(
            campaign_id, time_remaining_seconds, stage
        )
        await self.pool.broadcast_to_campaign(campaign_id, event)

    async def broadcast_analytics_update(
        self,
        campaign_id: str,
        analytics: Dict[str, Any]
    ):
        """Broadcast analytics snapshot"""
        event = RealtimeDataStreamer.create_analytics_sync(campaign_id, analytics)
        await self.pool.broadcast_to_campaign(campaign_id, event)
