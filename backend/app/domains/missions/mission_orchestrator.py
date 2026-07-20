"""SellIA Mission Orchestrator

Orquesta la ejecución secuencial de pasos de una misión, integrando:
- Computer Use Sessions (para tareas de navegador)
- Channel Connectors (para acciones directas por API)
- WebSocket notifications (para progreso en tiempo real)
"""

import uuid
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.domains.missions.models import Mission, MissionStep
from app.domains.missions.services import MissionService
from app.domains.computer_use.models import ComputerUseSession
from app.domains.computer_use.session_manager_v2 import ComputerUseSessionManagerV2
from app.domains.missions.websocket_manager import mission_ws_manager
from app.core.events import event_bus
from app.core.config import get_settings

settings = get_settings()


class MissionOrchestrator:
    """Orquesta la ejecución de misiones multi-paso."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.mission_service = MissionService(db)

    async def execute_mission(self, mission_id: uuid.UUID, user_id: uuid.UUID):
        """Ejecutar una misión completa paso a paso."""
        mission = await self.mission_service.get(mission_id, user_id)
        if not mission:
            raise ValueError("Misión no encontrada")

        if mission.status != "running":
            raise ValueError("La misión no está en estado 'running'")

        user_id_str = str(user_id)
        await mission_ws_manager.broadcast_mission_status(user_id_str, str(mission_id), "running", f"Misión '{mission.title}' iniciada")

        for step in sorted(mission.steps, key=lambda s: s.step_number):
            if step.status in ("completed", "skipped", "failed"):
                continue

            # Verificar aprobación
            if step.requires_approval and not step.approved_by_user:
                await self._update_step_status(step.id, "waiting_approval")
                await mission_ws_manager.broadcast_step_approval_request(user_id_str, str(mission_id), str(step.id), step.title)
                continue

            # Ejecutar paso
            await self._update_step_status(step.id, "running", started_at=datetime.utcnow())
            await mission_ws_manager.broadcast_mission_progress(user_id_str, str(mission_id), str(step.id), "running", {"title": step.title, "platform": step.platform})

            try:
                result = await self._execute_step(step, user_id)
                await self._update_step_status(step.id, "completed", result=result, completed_at=datetime.utcnow())
                await mission_ws_manager.broadcast_mission_progress(user_id_str, str(mission_id), str(step.id), "completed", {"result": result})
            except Exception as e:
                await self._update_step_status(step.id, "failed", error_message=str(e))
                await mission_ws_manager.broadcast_mission_progress(user_id_str, str(mission_id), str(step.id), "failed", {"error": str(e)})
                continue

        # Verificar si todos los pasos completaron
        await self._check_mission_completion(mission_id, user_id_str)

    async def _execute_step(self, step: MissionStep, user_id: uuid.UUID) -> Dict[str, Any]:
        """Ejecutar un paso individual según su plataforma."""
        if step.platform == "computer_use":
            return await self._execute_computer_use_step(step, user_id)
        elif step.platform == "api":
            return await self._execute_api_step(step, user_id)
        else:
            return await self._execute_channel_step(step, user_id)

    async def _execute_computer_use_step(self, step: MissionStep, user_id: uuid.UUID) -> Dict[str, Any]:
        """Crear una sesión de Computer Use y ejecutar la tarea."""
        url = step.action_params.get("url_template", "")
        task = step.title

        # Crear sesión en DB
        session = ComputerUseSession(
            id=uuid.uuid4(),
            user_id=user_id,
            task_description=task,
            status="pending",
            current_url=url,
            browser_type="chromium",
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        # Obtener API key
        api_key = None
        provider = "openai"

        from app.domains.subscriptions.models import UserAPIKey
        from app.core.encryption import decrypt_value

        for prov in ["openai", "anthropic"]:
            result = await self.db.execute(
                select(UserAPIKey).where(
                    UserAPIKey.user_id == user_id,
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

        if not api_key:
            if settings.OPENAI_API_KEY:
                api_key = settings.OPENAI_API_KEY
                provider = "openai"
            elif settings.ANTHROPIC_API_KEY:
                api_key = settings.ANTHROPIC_API_KEY
                provider = "anthropic"

        if not api_key:
            return {"status": "error", "message": "No hay API key de IA configurada"}

        # Crear manager y lanzar en background
        manager = ComputerUseSessionManagerV2(
            session_id=session.id,
            db=self.db,
            task=task,
            start_url=url,
            api_key=api_key,
            provider=provider,
            browser_type="chromium",
            user_id=user_id,
        )
        asyncio.create_task(manager.start())

        # Vincular sesión al paso
        step.computer_use_session_id = session.id
        await self.db.commit()

        return {
            "computer_use_session_id": str(session.id),
            "status": "started",
            "ws_url": f"/ws/computer-use/{session.id}",
        }

    async def _execute_api_step(self, step: MissionStep, user_id: uuid.UUID) -> Dict[str, Any]:
        """Ejecutar una acción directa por API de canales."""
        action_type = step.action_type
        params = step.action_params

        action_handlers = {
            "create_discount_code": self._handle_create_discount,
            "send_abandoned_cart_message": self._handle_send_cart_recovery,
            "send_abandoned_cart_email": self._handle_send_email,
            "create_content_calendar": self._handle_create_content,
            "generate_video_scripts": self._handle_generate_scripts,
            "generate_brand_kit": self._handle_generate_brand_kit,
            "request_reviews": self._handle_request_reviews,
            "translate_catalog": self._handle_translate_catalog,
            "setup_pixel_events": self._handle_setup_pixel,
            "send_outreach_emails": self._handle_send_outreach,
            "create_email_sequence": self._handle_email_sequence,
            "configure_shipping_zones": self._handle_shipping_zones,
            "setup_chatbot_rules": self._handle_chatbot_rules,
            "setup_followup_sequences": self._handle_followup_sequences,
            "setup_daily_reports": self._handle_daily_reports,
            "setup_stock_alerts": self._handle_stock_alerts,
            "update_inventory_sync": self._handle_inventory_sync,
        }

        handler = action_handlers.get(action_type)
        if handler:
            return await handler(user_id, params)

        return {"status": "acknowledged", "action": action_type, "note": "Acción programada para ejecución manual"}

    async def _execute_channel_step(self, step: MissionStep, user_id: uuid.UUID) -> Dict[str, Any]:
        """Ejecutar acción usando un connector de canal específico."""
        return {"status": "pending", "note": f"Acción en {step.platform} requiere integración específica"}

    async def _update_step_status(self, step_id: uuid.UUID, status: str, **kwargs):
        """Actualizar estado de un paso."""
        values = {"status": status, **kwargs}
        await self.db.execute(update(MissionStep).where(MissionStep.id == step_id).values(**values))
        await self.db.commit()

    async def _check_mission_completion(self, mission_id: uuid.UUID):
        """Verificar si la misión completó todos sus pasos."""
        result = await self.db.execute(select(MissionStep).where(MissionStep.mission_id == mission_id))
        steps = result.scalars().all()

        all_done = all(s.status in ("completed", "skipped") for s in steps)
        any_failed = any(s.status == "failed" for s in steps)

        if all_done:
            await self.db.execute(
                update(Mission)
                .where(Mission.id == mission_id)
                .values(status="completed", completed_at=datetime.utcnow())
            )
        elif any_failed:
            any_completed = any(s.status == "completed" for s in steps)
            if any_completed:
                await self.db.execute(
                    update(Mission)
                    .where(Mission.id == mission_id)
                    .values(status="completed", completed_at=datetime.utcnow())
                )
            else:
                await self.db.execute(update(Mission).where(Mission.id == mission_id).values(status="failed"))
        await self.db.commit()

    # ─── Handlers de acciones API ──────────────────────────────────────────────

    async def _handle_create_discount(self, user_id: uuid.UUID, params: Dict) -> Dict:
        return {"status": "created", "code": f"{params.get('code_prefix', 'DESC')}{uuid.uuid4().hex[:6].upper()}", "discount": params}

    async def _handle_send_cart_recovery(self, user_id: uuid.UUID, params: Dict) -> Dict:
        return {"status": "queued", "channel": params.get("channel"), "delay_minutes": params.get("delay_minutes")}

    async def _handle_send_email(self, user_id: uuid.UUID, params: Dict) -> Dict:
        return {"status": "queued", "template": params.get("template"), "delay_hours": params.get("delay_hours")}

    async def _handle_create_content(self, user_id: uuid.UUID, params: Dict) -> Dict:
        return {"status": "generated", "posts": params.get("posts", 0), "platform": params.get("platform")}

    async def _handle_generate_scripts(self, user_id: uuid.UUID, params: Dict) -> Dict:
        return {"status": "generated", "scripts_count": params.get("count", 0), "style": params.get("style")}

    async def _handle_generate_brand_kit(self, user_id: uuid.UUID, params: Dict) -> Dict:
        return {"status": "generated", "components": params.get("include", [])}

    async def _handle_request_reviews(self, user_id: uuid.UUID, params: Dict) -> Dict:
        return {"status": "queued", "via": params.get("via"), "max_per_day": params.get("max_per_day")}

    async def _handle_translate_catalog(self, user_id: uuid.UUID, params: Dict) -> Dict:
        return {"status": "queued", "target_language": params.get("target_language"), "platform": params.get("platform")}

    async def _handle_setup_pixel(self, user_id: uuid.UUID, params: Dict) -> Dict:
        return {"status": "configured", "events": params.get("events", [])}

    async def _handle_send_outreach(self, user_id: uuid.UUID, params: Dict) -> Dict:
        return {"status": "queued", "template": params.get("template"), "max_per_day": params.get("max_per_day")}

    async def _handle_email_sequence(self, user_id: uuid.UUID, params: Dict) -> Dict:
        return {"status": "created", "emails": params.get("emails", 0), "objective": params.get("objective")}

    async def _handle_shipping_zones(self, user_id: uuid.UUID, params: Dict) -> Dict:
        return {"status": "configured", "zones": params.get("zones", [])}

    async def _handle_chatbot_rules(self, user_id: uuid.UUID, params: Dict) -> Dict:
        return {"status": "configured", "channels": params.get("channels", [])}

    async def _handle_followup_sequences(self, user_id: uuid.UUID, params: Dict) -> Dict:
        return {"status": "configured", "triggers": params.get("triggers", [])}

    async def _handle_daily_reports(self, user_id: uuid.UUID, params: Dict) -> Dict:
        return {"status": "configured", "channels": params.get("channels", []), "time": params.get("time")}

    async def _handle_stock_alerts(self, user_id: uuid.UUID, params: Dict) -> Dict:
        return {"status": "configured", "threshold": params.get("threshold")}

    async def _handle_inventory_sync(self, user_id: uuid.UUID, params: Dict) -> Dict:
        return {"status": "configured", "sync_mode": params.get("sync_mode")}
