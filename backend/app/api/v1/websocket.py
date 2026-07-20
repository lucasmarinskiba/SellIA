"""WebSocket Endpoint - Real-time updates for Brain Controller."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

# Active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")

    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send to specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal: {e}")


manager = ConnectionManager()


@router.websocket("/ws/brain")
async def websocket_brain(websocket: WebSocket):
    """WebSocket endpoint for Brain real-time updates."""
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                msg_type = message.get("type")
                payload = message.get("payload", {})

                # Handle different message types
                if msg_type == "ping":
                    await manager.send_personal(websocket, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    })

                elif msg_type == "subscribe_metrics":
                    # Client wants metrics updates
                    await manager.send_personal(websocket, {
                        "type": "subscribed",
                        "channel": "metrics",
                        "timestamp": datetime.utcnow().isoformat(),
                    })

                elif msg_type == "subscribe_phases":
                    # Client wants phase updates
                    await manager.send_personal(websocket, {
                        "type": "subscribed",
                        "channel": "phases",
                        "timestamp": datetime.utcnow().isoformat(),
                    })

                else:
                    logger.warning(f"Unknown message type: {msg_type}")

            except json.JSONDecodeError:
                await manager.send_personal(websocket, {
                    "type": "error",
                    "message": "Invalid JSON",
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def broadcast_phase_update(phase: str, status: str, data: dict = None):
    """Broadcast phase update to all clients."""
    await manager.broadcast({
        "type": "phase_update",
        "phase": phase,
        "status": status,
        "data": data or {},
        "timestamp": datetime.utcnow().isoformat(),
    })


async def broadcast_metrics_update(metrics: dict):
    """Broadcast metrics update to all clients."""
    await manager.broadcast({
        "type": "metrics_update",
        "metrics": metrics,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def broadcast_system_event(event_type: str, message: str, data: dict = None):
    """Broadcast system event to all clients."""
    await manager.broadcast({
        "type": "system_event",
        "event_type": event_type,
        "message": message,
        "data": data or {},
        "timestamp": datetime.utcnow().isoformat(),
    })
