"""WebSocket endpoints."""
import jwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.ws.manager import manager


router = APIRouter()


@router.websocket("")
async def ws_endpoint(ws: WebSocket, token: str = Query(...)):
    """
    Auth via JWT token (query param · WS spec doesn't support headers reliably).
    Subscribe to tenant + user channels.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        tenant_id = payload["tenant_id"]
        user_id = payload["sub"]
    except jwt.InvalidTokenError:
        await ws.close(code=4401, reason="Invalid token")
        return

    await manager.connect(ws, tenant_id, user_id)
    try:
        while True:
            msg = await ws.receive_json()
            # echo + handle client→server messages (typing indicators, etc.)
            if msg.get("type") == "ping":
                await ws.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(ws, tenant_id, user_id)
