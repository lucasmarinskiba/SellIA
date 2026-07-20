"""Mission WebSocket Endpoint"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional

from app.core.deps import get_current_user_ws
from app.domains.missions.websocket_manager import mission_ws_manager

router = APIRouter(tags=["Mission WebSocket"])


@router.websocket("/ws/missions")
async def mission_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """WebSocket for real-time mission progress updates.
    
    Connect with: wss://host/ws/missions?token=<jwt>
    
    Incoming messages:
    - {"type": "ping"} -> pong response
    - {"type": "approve_step", "mission_id": "...", "step_id": "..."} -> approve a waiting step
    
    Outgoing messages:
    - {"type": "mission_progress", "mission_id": "...", "step_id": "...", "status": "..."}
    - {"type": "mission_status", "mission_id": "...", "status": "...", "message": "..."}
    - {"type": "step_approval_request", "mission_id": "...", "step_id": "...", "step_title": "..."}
    """
    # Authenticate via token query param
    try:
        user = await get_current_user_ws(token)
        if not user:
            await websocket.close(code=4001, reason="Unauthorized")
            return
    except Exception:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    user_id = str(user.id)
    await mission_ws_manager.connect(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "timestamp": str(__import__('datetime').datetime.utcnow())})

            elif msg_type == "approve_step":
                # Handle step approval via websocket
                mission_id = data.get("mission_id")
                step_id = data.get("step_id")
                # Import here to avoid circular dependencies
                from app.core.database import AsyncSessionLocal
                from app.domains.missions.services import MissionService
                from app.domains.missions.schemas import MissionStepUpdate
                async with AsyncSessionLocal() as db:
                    service = MissionService(db)
                    await service.update_step(
                        mission_id=__import__('uuid').UUID(mission_id),
                        step_id=__import__('uuid').UUID(step_id),
                        user_id=user.id,
                        data=MissionStepUpdate(status="completed", approved_by_user=True),
                    )
                await mission_ws_manager.broadcast(user_id, {
                    "type": "step_approved",
                    "mission_id": mission_id,
                    "step_id": step_id,
                })

    except WebSocketDisconnect:
        mission_ws_manager.disconnect(user_id, websocket)
    except Exception as e:
        mission_ws_manager.disconnect(user_id, websocket)
        try:
            await websocket.close(code=1011, reason=str(e))
        except Exception:
            pass
