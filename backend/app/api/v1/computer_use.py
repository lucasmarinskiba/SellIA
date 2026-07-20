"""Computer Use Agents — API Router

Endpoints REST para gestión de sesiones + WebSocket bidireccional
para streaming en tiempo real de screenshots y acciones.
"""

import json
import os
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.security import decode_access_token
from app.core.config import get_settings
import asyncio

from app.core.logger import get_logger
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.computer_use.models import ComputerUseSession, ComputerUseStep, ComputerUseMessage
from app.domains.computer_use.schemas import (
    ComputerUseSessionCreate,
    ComputerUseSessionResponse,
    ComputerUseSessionListResponse,
    ComputerUseStepResponse,
    ComputerUseMessageResponse,
    ComputerUseOrchestratorResult,
)
from app.domains.computer_use.session_manager import ComputerUseSessionManager, get_session_manager, remove_session_manager
from app.domains.computer_use.ws_manager import ws_manager

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter()


# ========== Helpers ==========

async def _get_session_or_404(db: AsyncSession, session_id: UUID, user_id: UUID) -> ComputerUseSession:
    result = await db.execute(
        select(ComputerUseSession).where(
            ComputerUseSession.id == session_id,
            ComputerUseSession.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return session


async def _auth_ws_token(token: str) -> Optional[dict]:
    """Valida token JWT para WebSocket."""
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        return None
    return payload


# ========== REST Endpoints ==========

@router.post("/sessions", response_model=ComputerUseSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: ComputerUseSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Crea una nueva sesión de Computer Use."""
    if not settings.COMPUTER_USE_ENABLED:
        raise HTTPException(status_code=403, detail="Computer Use está deshabilitado")

    # Rate limit: max 3 concurrent sessions per user
    result = await db.execute(
        select(func.count()).where(
            ComputerUseSession.user_id == current_user.id,
            ComputerUseSession.status.in_(["pending", "running", "paused"]),
        )
    )
    active_count = result.scalar() or 0
    if active_count >= 3:
        raise HTTPException(status_code=429, detail="Tenés 3 sesiones activas. Detené una antes de crear otra.")

    # Verify business if provided
    if data.business_id:
        result = await db.execute(
            select(Business).where(Business.id == data.business_id, Business.owner_id == current_user.id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Negocio no encontrado")

    session = ComputerUseSession(
        user_id=current_user.id,
        business_id=data.business_id,
        task_description=data.task_description,
        status="pending",
        current_url=data.start_url,
        total_steps=0,
        browser_type=data.browser_type or "chromium",
        result_data={"mode": data.mode or "supervised"},
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return session


@router.get("/sessions", response_model=ComputerUseSessionListResponse)
async def list_sessions(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Lista las sesiones de Computer Use del usuario actual."""
    result = await db.execute(
        select(ComputerUseSession)
        .where(ComputerUseSession.user_id == current_user.id)
        .order_by(desc(ComputerUseSession.created_at))
        .limit(limit)
        .offset(offset)
    )
    sessions = result.scalars().all()

    count_result = await db.execute(
        select(func.count()).where(ComputerUseSession.user_id == current_user.id)
    )
    total = count_result.scalar()

    return ComputerUseSessionListResponse(
        items=[ComputerUseSessionResponse.model_validate(s) for s in sessions],
        total=total,
    )


@router.get("/sessions/{session_id}", response_model=ComputerUseSessionResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Obtiene detalle de una sesión."""
    session = await _get_session_or_404(db, session_id, current_user.id)
    return session


@router.get("/sessions/{session_id}/steps", response_model=list[ComputerUseStepResponse])
async def list_session_steps(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Lista los pasos de una sesión."""
    session = await _get_session_or_404(db, session_id, current_user.id)
    result = await db.execute(
        select(ComputerUseStep)
        .where(ComputerUseStep.session_id == session_id)
        .order_by(ComputerUseStep.step_number)
    )
    steps = result.scalars().all()
    return [ComputerUseStepResponse.model_validate(s) for s in steps]


@router.get("/sessions/{session_id}/messages", response_model=list[ComputerUseMessageResponse])
async def list_session_messages(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Lista los mensajes de chat de supervisión de una sesión."""
    session = await _get_session_or_404(db, session_id, current_user.id)
    result = await db.execute(
        select(ComputerUseMessage)
        .where(ComputerUseMessage.session_id == session_id)
        .order_by(ComputerUseMessage.created_at)
    )
    messages = result.scalars().all()
    return [ComputerUseMessageResponse.model_validate(m) for m in messages]


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Elimina una sesión y sus datos asociados."""
    session = await _get_session_or_404(db, session_id, current_user.id)

    # Stop if running
    manager = get_session_manager(str(session_id))
    if manager:
        await manager.stop()

    await db.delete(session)
    await db.commit()
    return {"message": "Sesión eliminada"}


@router.post("/sessions/{session_id}/start")
async def start_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Inicia una sesión de Computer Use (debe conectarse vía WebSocket después)."""
    session = await _get_session_or_404(db, session_id, current_user.id)

    if session.status not in ("pending", "paused"):
        raise HTTPException(status_code=400, detail=f"No se puede iniciar una sesión en estado '{session.status}'")

    # Determine API key and provider
    api_key = None
    provider = "openai"

    # Try to get user's API key
    from app.domains.subscriptions.models import UserAPIKey
    from app.core.encryption import decrypt_value

    for prov in ["openai", "anthropic"]:
        result = await db.execute(
            select(UserAPIKey).where(
                UserAPIKey.user_id == current_user.id,
                UserAPIKey.provider == prov,
                UserAPIKey.is_active == True,
            )
        )
        key_record = result.scalar_one_or_none()
        if key_record and key_record.api_key_fernet:
            try:
                api_key = decrypt_value(key_record.api_key_fernet)
                provider = prov
                break
            except Exception:
                pass

    # Fallback to global settings
    if not api_key:
        if settings.OPENAI_API_KEY:
            api_key = settings.OPENAI_API_KEY
            provider = "openai"
        elif settings.ANTHROPIC_API_KEY:
            api_key = settings.ANTHROPIC_API_KEY
            provider = "anthropic"
        else:
            raise HTTPException(status_code=400, detail="No hay API key de IA configurada para Computer Use")

    # Create session manager (V2 with all enhancements)
    from app.domains.computer_use.session_manager_v2 import ComputerUseSessionManagerV2
    from app.domains.computer_use.services.browser_pool import get_browser_pool

    # Load profile if set
    profile = None
    if session.profile_id:
        from app.domains.computer_use.models_extended import ComputerUseBrowserProfile
        profile_result = await db.execute(
            select(ComputerUseBrowserProfile).where(ComputerUseBrowserProfile.id == session.profile_id)
        )
        profile_row = profile_result.scalar_one_or_none()
        if profile_row:
            profile = {
                "viewport_width": profile_row.viewport_width,
                "viewport_height": profile_row.viewport_height,
                "user_agent": profile_row.user_agent,
                "locale": profile_row.locale,
                "timezone_id": profile_row.timezone_id,
                "cookies": profile_row.cookies,
                "local_storage": profile_row.local_storage,
                "geolocation": profile_row.geolocation,
            }

    # Load proxy if set
    proxy = None
    if session.proxy_config_id:
        from app.domains.computer_use.models_extended import ComputerUseProxyConfig
        from app.core.encryption import decrypt_value
        proxy_result = await db.execute(
            select(ComputerUseProxyConfig).where(ComputerUseProxyConfig.id == session.proxy_config_id)
        )
        proxy_row = proxy_result.scalar_one_or_none()
        if proxy_row:
            proxy = {
                "server": f"{proxy_row.proxy_type}://{proxy_row.host}:{proxy_row.port}",
            }
            if proxy_row.username:
                proxy["username"] = proxy_row.username
            if proxy_row.password_encrypted:
                try:
                    proxy["password"] = decrypt_value(proxy_row.password_encrypted)
                except Exception:
                    pass

    # Load webhooks
    webhooks = []
    try:
        from app.domains.computer_use.models_extended import ComputerUseWebhook
        wh_result = await db.execute(
            select(ComputerUseWebhook).where(
                ComputerUseWebhook.user_id == current_user.id,
                ComputerUseWebhook.is_active == True,
            )
        )
        for wh in wh_result.scalars().all():
            webhooks.append({"url": wh.url, "secret": wh.secret, "events": wh.events})
    except Exception:
        pass

    manager = ComputerUseSessionManagerV2(
        session_id=session_id,
        db=db,
        task=session.task_description,
        start_url=session.current_url,
        api_key=api_key,
        provider=provider,
        browser_type=session.browser_type or "chromium",
        profile=profile,
        proxy=proxy,
        webhooks=webhooks,
        mode=(session.result_data or {}).get("mode", "supervised"),
    )

    # Start in background (user must connect via WS)
    import asyncio
    asyncio.create_task(manager.start())

    ws_url = f"/api/v1/ws/computer-use/{session_id}"

    return {
        "session_id": session_id,
        "ws_url": ws_url,
        "status": "starting",
        "message": "Conectate vía WebSocket para ver la automatización en tiempo real",
    }


# ========== Orchestrator Integration ==========

async def create_computer_use_from_orchestrator(
    db: AsyncSession,
    user_id: UUID,
    business_id: Optional[UUID],
    task: str,
    start_url: Optional[str] = None,
) -> ComputerUseOrchestratorResult:
    """Crea una sesión de Computer Use desde el orchestrator y devuelve datos de conexión."""
    session = ComputerUseSession(
        user_id=user_id,
        business_id=business_id,
        task_description=task,
        status="pending",
        current_url=start_url,
        total_steps=0,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    ws_url = f"/api/v1/ws/computer-use/{session.id}"

    return ComputerUseOrchestratorResult(
        action="COMPUTER_USE",
        response=f"Voy a usar el navegador para: {task}",
        session_id=session.id,
        ws_url=ws_url,
        task=task,
    )


# ========== Screenshot Serving ==========

from fastapi.responses import FileResponse

@router.get("/sessions/{session_id}/screenshots/{step_number}")
async def get_screenshot(
    session_id: UUID,
    step_number: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Sirve un screenshot de un paso específico."""
    session = await _get_session_or_404(db, session_id, current_user.id)
    screenshot_path = os.path.join(
        os.getcwd(), "storage", "screenshots", str(session_id), f"step_{step_number}.jpg"
    )
    if not os.path.exists(screenshot_path):
        raise HTTPException(status_code=404, detail="Screenshot no encontrado")
    return FileResponse(screenshot_path, media_type="image/jpeg")


# ========== WebSocket Endpoint ==========

@router.websocket("/ws/computer-use/{session_id}")
async def computer_use_websocket(
    websocket: WebSocket,
    session_id: UUID,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """WebSocket bidireccional para supervisión en tiempo real de Computer Use.

    Protocolo:
    - Cliente → Servidor: {"type": "control", "action": "pause|resume|stop"}
    - Cliente → Servidor: {"type": "chat", "message": "..."}
    - Servidor → Cliente: {"type": "screenshot", "data": {"image_base64": "...", "step": 3, "url": "..."}}
    - Servidor → Cliente: {"type": "action", "data": {"action_type": "click", "params": {...}, "reason": "...", "step": 3}}
    - Servidor → Cliente: {"type": "status", "data": {"status": "running", "message": "...", "step": 3, "total_steps": 30}}
    - Servidor → Cliente: {"type": "chat", "data": {"role": "agent", "content": "..."}}
    - Servidor → Cliente: {"type": "error", "data": {"message": "..."}}
    - Servidor → Cliente: {"type": "completed", "data": {"result": "...", "total_steps": 10}}
    """
    # Authenticate
    payload = await _auth_ws_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Token inválido")
        return

    user_id = UUID(payload["sub"])

    # Verify session ownership
    try:
        session = await _get_session_or_404(db, session_id, user_id)
    except HTTPException:
        await websocket.close(code=4004, reason="Sesión no encontrada")
        return

    await websocket.accept()
    logger.info(f"WebSocket connected for session {session_id}, user {user_id}")

    # Register with WebSocket Manager
    await ws_manager.connect(str(session_id), websocket)

    # Find or create session manager
    manager = get_session_manager(str(session_id))

    if not manager:
        if session.status == "pending":
            await websocket.send_json({
                "type": "status",
                "data": {"status": "pending", "message": "Iniciando sesión...", "step": 0, "total_steps": settings.COMPUTER_USE_MAX_STEPS},
            })
            try:
                await start_session(session_id, db, type("User", (), {"id": user_id})())
                for _ in range(10):
                    await asyncio.sleep(0.5)
                    manager = get_session_manager(str(session_id))
                    if manager:
                        break
            except Exception as e:
                logger.error(f"Auto-start failed: {e}")
                await websocket.send_json({"type": "error", "data": {"message": f"No se pudo iniciar: {str(e)}"}})
                await ws_manager.disconnect(str(session_id))
                await websocket.close()
                return

    if not manager:
        await websocket.send_json({"type": "error", "data": {"message": "No se pudo iniciar el gestor de sesión"}})
        await ws_manager.disconnect(str(session_id))
        await websocket.close()
        return

    # Send current status
    await websocket.send_json({
        "type": "status",
        "data": {
            "status": manager.status,
            "message": "Conectado a la Caja de Cristal",
            "step": manager.current_step,
            "total_steps": settings.COMPUTER_USE_MAX_STEPS,
        },
    })

    # Listen for client messages
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "data": {"message": "Mensaje JSON inválido"}})
                continue

            msg_type = msg.get("type")

            if msg_type == "control":
                action = msg.get("action")
                if action == "pause":
                    await manager.pause()
                elif action == "resume":
                    await manager.resume()
                elif action == "stop":
                    await manager.stop()
                    await websocket.send_json({
                        "type": "status",
                        "data": {"status": "stopped", "message": "Sesión detenida", "step": manager.current_step, "total_steps": settings.COMPUTER_USE_MAX_STEPS},
                    })
                else:
                    await websocket.send_json({"type": "error", "data": {"message": f"Control desconocido: {action}"}})

            elif msg_type == "chat":
                message = msg.get("message", "").strip()
                if message:
                    await manager.send_chat_message(message)
                    await websocket.send_json({
                        "type": "chat",
                        "data": {"role": "system", "content": "Mensaje enviado al agente"},
                    })

            else:
                await websocket.send_json({"type": "error", "data": {"message": f"Tipo de mensaje desconocido: {msg_type}"}})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        await ws_manager.disconnect(str(session_id))
        logger.info(f"WebSocket closed for session {session_id}")
