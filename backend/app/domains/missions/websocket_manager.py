"""Mission WebSocket Manager — real-time progress broadcasting."""

import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class MissionWebSocketManager:
    """Manages WebSocket connections per user for mission progress updates."""

    def __init__(self):
        # user_id -> list of active websockets
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def broadcast(self, user_id: str, message: dict):
        """Broadcast a message to all connections for a user."""
        if user_id not in self.active_connections:
            return
        dead_sockets = []
        for ws in self.active_connections[user_id]:
            try:
                await ws.send_json(message)
            except Exception:
                logger.exception("broadcast: error inesperado")
                dead_sockets.append(ws)
        for ws in dead_sockets:
            self.disconnect(user_id, ws)

    async def broadcast_mission_progress(
        self,
        user_id: str,
        mission_id: str,
        step_id: str,
        status: str,
        data: dict[str, Any] | None = None,
    ):
        """Convenience method to broadcast mission step progress."""
        await self.broadcast(
            user_id,
            {
                "type": "mission_progress",
                "mission_id": mission_id,
                "step_id": step_id,
                "status": status,
                "data": data or {},
                "timestamp": str(__import__("datetime").utc_now()),
            },
        )

    async def broadcast_mission_status(
        self,
        user_id: str,
        mission_id: str,
        status: str,
        message: str = "",
    ):
        """Broadcast overall mission status change."""
        await self.broadcast(
            user_id,
            {
                "type": "mission_status",
                "mission_id": mission_id,
                "status": status,
                "message": message,
                "timestamp": str(__import__("datetime").utc_now()),
            },
        )

    async def broadcast_step_approval_request(
        self,
        user_id: str,
        mission_id: str,
        step_id: str,
        step_title: str,
    ):
        """Broadcast when a step requires user approval."""
        await self.broadcast(
            user_id,
            {
                "type": "step_approval_request",
                "mission_id": mission_id,
                "step_id": step_id,
                "step_title": step_title,
                "message": f"El paso '{step_title}' requiere tu aprobación para continuar.",
            },
        )


# Singleton instance
mission_ws_manager = MissionWebSocketManager()
