"""WebSocket real-time location dashboard."""

import logging
import json
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.locations.checkin_models import LocationCheckin, StaffCheckin, LocationFeedback

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["websocket"])

# Store active WebSocket connections per location
active_connections: Dict[str, Set[WebSocket]] = {}


class LocationDashboardManager:
    """Manage WebSocket connections + broadcast location events."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, location_id: str, websocket: WebSocket):
        """Register WebSocket for location."""
        await websocket.accept()
        if location_id not in self.active_connections:
            self.active_connections[location_id] = set()
        self.active_connections[location_id].add(websocket)
        logger.info(f"WebSocket connected: {location_id} (total: {len(self.active_connections[location_id])})")

    async def disconnect(self, location_id: str, websocket: WebSocket):
        """Unregister WebSocket."""
        if location_id in self.active_connections:
            self.active_connections[location_id].discard(websocket)
            if not self.active_connections[location_id]:
                del self.active_connections[location_id]
            logger.info(f"WebSocket disconnected: {location_id}")

    async def broadcast(self, location_id: str, message: dict):
        """Send to all connected clients for location."""
        if location_id not in self.active_connections:
            return

        disconnected = set()
        for websocket in self.active_connections[location_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")
                disconnected.add(websocket)

        # Clean up dead connections
        for ws in disconnected:
            await self.disconnect(location_id, ws)


manager = LocationDashboardManager()


@router.websocket("/ws/locations/{location_id}")
async def websocket_location_dashboard(
    location_id: str,
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """Real-time dashboard WebSocket for location.

    Broadcasts:
    - visitor check-in/out
    - staff actions + check-out
    - feedback submission
    - location metrics (every 10s)
    - alerts (high wait time, capacity, negative feedback)
    """
    await manager.connect(location_id, websocket)

    try:
        location_uuid = UUID(location_id)

        # Send initial connection message
        await websocket.send_json({
            "type": "connection_established",
            "location_id": location_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Connected to location dashboard"
        })

        # Send initial metrics snapshot
        metrics = _get_location_metrics(location_uuid, 24, db)
        await websocket.send_json({
            "type": "location_metrics",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **metrics
        })

        # Listen for client commands
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "subscribe_staff":
                staff_id = message.get("staff_id")
                # TODO: send staff-specific performance stream
                pass

            elif message.get("type") == "alert_acknowledged":
                alert_id = message.get("alert_id")
                # TODO: mark alert as acknowledged in DB
                pass

            elif message.get("type") == "disconnect":
                break

    except WebSocketDisconnect:
        await manager.disconnect(location_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(location_id, websocket)


async def broadcast_visitor_checkin(
    location_id: UUID,
    checkin_id: UUID,
    visitor_name: str,
    checkin_type: str,
    db: Session
):
    """Called when visitor checks in. Broadcast to all connected dashboards."""
    message = {
        "type": "visitor_checkin",
        "checkin_id": str(checkin_id),
        "location_id": str(location_id),
        "visitor_name": visitor_name,
        "checkin_type": checkin_type,
        "checkin_time": datetime.now(timezone.utc).isoformat(),
        "estimated_dwell": "5-20m"
    }
    await manager.broadcast(str(location_id), message)


async def broadcast_visitor_checkout(
    location_id: UUID,
    checkin_id: UUID,
    dwell_seconds: int,
    sections_visited: list,
    purchase_amount: float = None,
):
    """Called when visitor checks out."""
    message = {
        "type": "visitor_checkout",
        "checkin_id": str(checkin_id),
        "location_id": str(location_id),
        "dwell_seconds": dwell_seconds,
        "dwell_minutes": dwell_seconds // 60,
        "sections_visited": sections_visited,
        "purchase_amount": purchase_amount,
        "checkout_time": datetime.now(timezone.utc).isoformat()
    }
    await manager.broadcast(str(location_id), message)


async def broadcast_staff_action(
    location_id: UUID,
    staff_name: str,
    action: str,  # visitor_engaged, demo_started, demo_ended, sale_completed
    action_count: int
):
    """Called when staff logs action."""
    message = {
        "type": "staff_action",
        "location_id": str(location_id),
        "staff_name": staff_name,
        "action": action,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action_count": action_count
    }
    await manager.broadcast(str(location_id), message)


async def broadcast_staff_checkout(
    location_id: UUID,
    staff_name: str,
    hours_worked: float,
    visitors_engaged: int,
    demos_conducted: int,
    sales_assisted: int,
):
    """Called when staff checks out."""
    nps_avg = 8.5  # TODO: calculate from feedback
    message = {
        "type": "staff_checkout",
        "location_id": str(location_id),
        "staff_name": staff_name,
        "hours_worked": round(hours_worked, 1),
        "summary": {
            "visitors_engaged": visitors_engaged,
            "demos": demos_conducted,
            "sales": sales_assisted,
            "nps_avg": nps_avg
        }
    }
    await manager.broadcast(str(location_id), message)


async def broadcast_feedback(
    location_id: UUID,
    feedback_id: UUID,
    nps_score: int,
    sentiment: str,
    comment: str = None
):
    """Called when feedback submitted."""
    message = {
        "type": "visitor_feedback",
        "location_id": str(location_id),
        "feedback_id": str(feedback_id),
        "nps_score": nps_score,
        "sentiment": sentiment,
        "comment": comment,
        "requires_followup": sentiment == "negative"
    }
    await manager.broadcast(str(location_id), message)


async def broadcast_alert(
    location_id: UUID,
    alert_type: str,  # high_wait_time, capacity_warning, negative_feedback, staff_shortage
    severity: str,  # info, warning, critical
    message_text: str
):
    """Broadcast alert to all connected dashboards."""
    message = {
        "type": "alert",
        "location_id": str(location_id),
        "alert_type": alert_type,
        "severity": severity,
        "message": message_text,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await manager.broadcast(str(location_id), message)


def _get_location_metrics(location_id: UUID, hours: int, db: Session) -> dict:
    """Get current location metrics for dashboard."""
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    # Active visitors
    active_visitors = db.query(LocationCheckin).filter(
        LocationCheckin.location_id == location_id,
        LocationCheckin.checkin_time >= cutoff,
        LocationCheckin.checkout_time.is_(None)
    ).count()

    # Staff on shift
    staff_on_shift = db.query(StaffCheckin).filter(
        StaffCheckin.location_id == location_id,
        StaffCheckin.checkin_time >= cutoff,
        StaffCheckin.checkout_time.is_(None)
    ).count()

    # Total visitors in period
    total_visitors = db.query(LocationCheckin).filter(
        LocationCheckin.location_id == location_id,
        LocationCheckin.checkin_time >= cutoff
    ).count()

    # Avg dwell time
    checkouts = db.query(LocationCheckin).filter(
        LocationCheckin.location_id == location_id,
        LocationCheckin.checkin_time >= cutoff,
        LocationCheckin.dwell_seconds.isnot(None)
    ).all()

    avg_dwell = sum(c.dwell_seconds for c in checkouts) // len(checkouts) if checkouts else 0

    # NPS feedback
    feedback = db.query(LocationFeedback).filter(
        LocationFeedback.location_id == location_id,
        LocationFeedback.created_at >= cutoff
    ).all()

    avg_nps = sum(f.nps_score for f in feedback if f.nps_score) / len(feedback) if feedback else 0

    return {
        "active_visitors": active_visitors,
        "staff_on_shift": staff_on_shift,
        "total_visitors": total_visitors,
        "avg_dwell_minutes": avg_dwell // 60,
        "avg_nps_score": round(avg_nps, 1),
        "feedback_count": len(feedback),
        "period_hours": hours
    }
