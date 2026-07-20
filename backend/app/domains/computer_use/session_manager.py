"""Computer Use — Session Manager

Gestiona el ciclo de vida de una sesión de computer use:
- Loop de percepción-acción
- Comunicación bidireccional con el frontend vía WebSocket Manager (Redis)
- Estados: pending → running → paused / completed / failed / stopped
- Cleanup robusto garantizado
"""

import asyncio
import base64
import os
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logger import get_logger
from app.domains.computer_use.browser_service import BrowserService
from app.domains.computer_use.vision_agent import VisionAgent
from app.domains.computer_use.models import ComputerUseSession, ComputerUseStep, ComputerUseMessage
from app.domains.computer_use.schemas import ComputerUseAction
from app.domains.computer_use.ws_manager import ws_manager
from app.core.metrics import (
    COMPUTER_USE_SESSIONS_CREATED,
    COMPUTER_USE_SESSIONS_COMPLETED,
    COMPUTER_USE_SESSIONS_FAILED,
    COMPUTER_USE_SESSIONS_STOPPED,
    COMPUTER_USE_STEPS_TOTAL,
    COMPUTER_USE_STEP_DURATION,
    COMPUTER_USE_SESSION_DURATION,
    COMPUTER_USE_ACTIVE_SESSIONS,
)

logger = get_logger(__name__)
settings = get_settings()

# In-memory registry of active sessions
_active_sessions: Dict[str, "ComputerUseSessionManager"] = {}


def get_session_manager(session_id: str) -> Optional["ComputerUseSessionManager"]:
    return _active_sessions.get(session_id)


def remove_session_manager(session_id: str) -> None:
    _active_sessions.pop(session_id, None)


class ComputerUseSessionManager:
    """Gestiona una sesión de computer use en tiempo real."""

    def __init__(
        self,
        session_id: UUID,
        db: AsyncSession,
        task: str,
        start_url: Optional[str] = None,
        api_key: Optional[str] = None,
        provider: str = "openai",
    ):
        self.session_id = str(session_id)
        self.db = db
        self.task = task
        self.start_url = start_url
        self.api_key = api_key
        self.provider = provider

        self.browser = BrowserService()
        self.vision = VisionAgent(api_key=api_key, provider=provider)

        self.status = "pending"
        self.current_step = 0
        self.max_steps = settings.COMPUTER_USE_MAX_STEPS
        self.history: List[Dict[str, Any]] = []
        self.user_chat_queue: List[str] = []

        # Events for pause/resume synchronization
        self._pause_event = asyncio.Event()
        self._pause_event.set()
        self._stop_event = asyncio.Event()

        # Screenshot storage
        self._screenshots_dir = os.path.join(os.getcwd(), "storage", "screenshots", self.session_id)
        os.makedirs(self._screenshots_dir, exist_ok=True)
        self._cleanup_done = False
        self._session_start_time = None
        self._provider_name = "unknown"

    async def _send_ws(self, message: dict):
        """Envía mensaje al frontend vía WebSocket Manager (Redis multi-worker)."""
        try:
            await ws_manager.send_message(self.session_id, message)
        except Exception as e:
            logger.warning(f"WS send failed for session {self.session_id}: {e}")

    async def start(self) -> None:
        """Inicia la sesión de computer use."""
        self._session_start_time = time.time()
        try:
            await self.browser.start(headless=True)
            self.status = "running"
            _active_sessions[self.session_id] = self

            # Detect provider name for metrics
            try:
                provider = await self.vision._get_provider()
                self._provider_name = getattr(provider, "provider_name", "unknown")
            except Exception:
                pass

            # Metrics
            COMPUTER_USE_SESSIONS_CREATED.labels(provider=self._provider_name).inc()
            COMPUTER_USE_ACTIVE_SESSIONS.inc()

            # Update DB status
            await self._update_session_status("running")

            await self._send_ws({
                "type": "status",
                "data": {"status": "running", "message": "Sesión iniciada", "step": 0, "total_steps": self.max_steps},
            })

            if self.start_url:
                nav_result = await self.browser.navigate(self.start_url)
                if not nav_result.get("success"):
                    await self._fail(f"No se pudo navegar a {self.start_url}: {nav_result.get('error')}")
                    return

            # Run the main loop
            await self._run_loop()

        except Exception as e:
            logger.exception(f"Session {self.session_id} failed to start")
            await self._fail(str(e))
        finally:
            # Ensure cleanup always runs
            await self._cleanup()

    async def _run_loop(self) -> None:
        """Loop principal de percepción-acción."""
        try:
            while self.current_step < self.max_steps:
                # Check if stopped
                if self._stop_event.is_set():
                    await self._stop()
                    return

                # Check if paused
                if not self._pause_event.is_set():
                    await self._send_ws({
                        "type": "status",
                        "data": {"status": "paused", "message": "Sesión pausada por el usuario", "step": self.current_step, "total_steps": self.max_steps},
                    })
                    await self._pause_event.wait()
                    await self._send_ws({
                        "type": "status",
                        "data": {"status": "running", "message": "Sesión reanudada", "step": self.current_step, "total_steps": self.max_steps},
                    })
                    if self._stop_event.is_set():
                        await self._stop()
                        return

                self.current_step += 1
                step_start = time.time()

                # 1. Take screenshot
                try:
                    screenshot_bytes = await self.browser.screenshot()
                except Exception as e:
                    await self._fail(f"Screenshot error: {e}")
                    return

                # Save screenshot to disk
                screenshot_path = os.path.join(self._screenshots_dir, f"step_{self.current_step}.jpg")
                with open(screenshot_path, "wb") as f:
                    f.write(screenshot_bytes)
                relative_path = f"screenshots/{self.session_id}/step_{self.current_step}.jpg"

                # 2. Get page info
                page_info = await self.browser.get_page_info()

                # 3. Send screenshot to frontend
                await self._send_ws({
                    "type": "screenshot",
                    "data": {
                        "image_base64": base64.b64encode(screenshot_bytes).decode("utf-8"),
                        "step": self.current_step,
                        "url": page_info.get("url", ""),
                    },
                })

                # 4. Check user chat messages
                user_message = None
                if self.user_chat_queue:
                    user_message = self.user_chat_queue.pop(0)
                    await self._send_ws({
                        "type": "chat",
                        "data": {"role": "user", "content": user_message},
                    })
                    await self._save_message("user", user_message)

                # 5. Call vision agent
                action = await self.vision.decide_action(
                    screenshot_bytes=screenshot_bytes,
                    task=self.task,
                    history=self.history,
                    user_message=user_message,
                    page_info=page_info,
                )

                # 6. Send action to frontend
                await self._send_ws({
                    "type": "action",
                    "data": {
                        "action_type": action.action_type,
                        "params": action.params,
                        "reason": action.reason,
                        "step": self.current_step,
                    },
                })

                # 7. Save step to DB
                await self._save_step(
                    step_number=self.current_step,
                    screenshot_path=relative_path,
                    action=action,
                    page_url=page_info.get("url"),
                )

                # 8. Execute action
                execution_result = await self._execute_action(action)

                # Update step with execution result
                await self._update_step_result(self.current_step, execution_result)

                # Add to history
                self.history.append({
                    "step_number": self.current_step,
                    "action_type": action.action_type,
                    "params": action.params,
                    "reason": action.reason,
                    "result": execution_result,
                })

                # 9. Check if done or error
                if action.action_type == "done":
                    summary = action.params.get("summary", "")
                    if not summary:
                        summary = await self.vision.generate_summary(self.history)
                    await self._complete(summary)
                    return

                if action.action_type == "error":
                    await self._fail(action.params.get("message", "Error desconocido del agente"))
                    return

                # Update session progress
                await self._update_session_progress(page_info.get("url"))

                # Metrics: step completed
                COMPUTER_USE_STEPS_TOTAL.labels(action_type=action.action_type).inc()
                COMPUTER_USE_STEP_DURATION.observe(time.time() - step_start)

                # Small delay between steps
                await asyncio.sleep(1.0)

            # Max steps reached
            summary = await self.vision.generate_summary(self.history)
            await self._complete(f"{summary}\n\n(Límite de {self.max_steps} pasos alcanzado)")

        except asyncio.CancelledError:
            logger.info(f"Session {self.session_id} cancelled")
            await self._stop()
        except Exception as e:
            logger.exception(f"Session {self.session_id} loop error")
            await self._fail(str(e))

    async def _execute_action(self, action: ComputerUseAction) -> str:
        """Ejecuta una acción en el navegador."""
        params = action.params
        result = {"success": False, "error": "Unknown action"}

        try:
            if action.action_type == "click":
                result = await self.browser.click(params["x"], params["y"])
            elif action.action_type == "double_click":
                result = await self.browser.double_click(params["x"], params["y"])
            elif action.action_type == "right_click":
                result = await self.browser.right_click(params["x"], params["y"])
            elif action.action_type == "type":
                result = await self.browser.type(params["text"])
            elif action.action_type == "scroll":
                result = await self.browser.scroll(params.get("direction", "down"), params.get("amount", 500))
            elif action.action_type == "navigate":
                result = await self.browser.navigate(params["url"])
            elif action.action_type == "wait":
                result = await self.browser.wait(params.get("seconds", 2))
            elif action.action_type == "screenshot":
                result = {"success": True}
            elif action.action_type in ("done", "error"):
                result = {"success": True}
            else:
                result = {"success": False, "error": f"Acción no soportada: {action.action_type}"}
        except Exception as e:
            result = {"success": False, "error": str(e)}

        return "success" if result.get("success") else result.get("error", "Error desconocido")

    async def pause(self) -> None:
        """Pausa la sesión."""
        if self.status == "running":
            self.status = "paused"
            self._pause_event.clear()
            await self._update_session_status("paused")
            logger.info(f"Session {self.session_id} paused")

    async def resume(self) -> None:
        """Reanuda la sesión pausada."""
        if self.status == "paused":
            self.status = "running"
            self._pause_event.set()
            await self._update_session_status("running")
            logger.info(f"Session {self.session_id} resumed")

    async def stop(self) -> None:
        """Detiene la sesión permanentemente."""
        self._stop_event.set()
        self._pause_event.set()
        logger.info(f"Session {self.session_id} stop requested")

    async def _stop(self) -> None:
        """Finaliza la sesión con estado stopped."""
        self.status = "stopped"
        await self._cleanup()
        await self._update_session_status("stopped")
        COMPUTER_USE_SESSIONS_STOPPED.inc()
        if self._session_start_time:
            COMPUTER_USE_SESSION_DURATION.observe(time.time() - self._session_start_time)
        await self._send_ws({
            "type": "status",
            "data": {"status": "stopped", "message": "Sesión detenida por el usuario", "step": self.current_step, "total_steps": self.max_steps},
        })

    async def _complete(self, summary: str) -> None:
        """Marca la sesión como completada."""
        self.status = "completed"
        await self._cleanup()
        await self._update_session_status("completed", result_data={"summary": summary})
        COMPUTER_USE_SESSIONS_COMPLETED.labels(provider=self._provider_name).inc()
        if self._session_start_time:
            COMPUTER_USE_SESSION_DURATION.observe(time.time() - self._session_start_time)
        await self._send_ws({
            "type": "completed",
            "data": {"result": summary, "total_steps": self.current_step},
        })
        await self._send_ws({
            "type": "status",
            "data": {"status": "completed", "message": summary, "step": self.current_step, "total_steps": self.max_steps},
        })

    async def _fail(self, error_message: str) -> None:
        """Marca la sesión como fallida."""
        self.status = "failed"
        await self._cleanup()
        await self._update_session_status("failed", error_message=error_message)
        COMPUTER_USE_SESSIONS_FAILED.labels(provider=self._provider_name, reason=error_message[:50]).inc()
        if self._session_start_time:
            COMPUTER_USE_SESSION_DURATION.observe(time.time() - self._session_start_time)
        await self._send_ws({
            "type": "error",
            "data": {"message": error_message},
        })
        await self._send_ws({
            "type": "status",
            "data": {"status": "failed", "message": error_message, "step": self.current_step, "total_steps": self.max_steps},
        })

    async def _cleanup(self) -> None:
        """Limpia recursos del navegador. Garantizado idempotente."""
        if self._cleanup_done:
            return
        self._cleanup_done = True
        remove_session_manager(self.session_id)
        COMPUTER_USE_ACTIVE_SESSIONS.dec()
        try:
            await self.browser.stop()
        except Exception as e:
            logger.warning(f"Browser cleanup error: {e}")

    async def send_chat_message(self, message: str) -> None:
        """Recibe un mensaje de chat del usuario."""
        self.user_chat_queue.append(message)
        await self._send_ws({
            "type": "chat",
            "data": {"role": "user", "content": message},
        })
        await self._save_message("user", message)

    # Database helpers

    async def _update_session_status(self, status: str, result_data: Optional[Dict] = None, error_message: Optional[str] = None) -> None:
        try:
            from sqlalchemy import select
            result = await self.db.execute(
                select(ComputerUseSession).where(ComputerUseSession.id == UUID(self.session_id))
            )
            session = result.scalar_one_or_none()
            if session:
                session.status = status
                session.total_steps = self.current_step
                if result_data:
                    session.result_data = result_data
                if error_message:
                    session.error_message = error_message
                if status in ("completed", "failed", "stopped"):
                    session.completed_at = datetime.now(timezone.utc)
                if status == "running" and not session.started_at:
                    session.started_at = datetime.now(timezone.utc)
                await self.db.commit()
        except Exception as e:
            logger.error(f"DB update error: {e}")

    async def _update_session_progress(self, current_url: Optional[str]) -> None:
        try:
            from sqlalchemy import select
            result = await self.db.execute(
                select(ComputerUseSession).where(ComputerUseSession.id == UUID(self.session_id))
            )
            session = result.scalar_one_or_none()
            if session:
                session.total_steps = self.current_step
                if current_url:
                    session.current_url = current_url
                await self.db.commit()
        except Exception as e:
            logger.error(f"DB progress update error: {e}")

    async def _save_step(
        self,
        step_number: int,
        screenshot_path: str,
        action: ComputerUseAction,
        page_url: Optional[str],
    ) -> None:
        try:
            step = ComputerUseStep(
                session_id=UUID(self.session_id),
                step_number=step_number,
                screenshot_path=screenshot_path,
                llm_prompt="",
                llm_response=action.reason,
                action_type=action.action_type,
                action_params=action.params,
                executed_at=datetime.now(timezone.utc),
            )
            self.db.add(step)
            await self.db.commit()
        except Exception as e:
            logger.error(f"DB save step error: {e}")
            await self.db.rollback()

    async def _update_step_result(self, step_number: int, execution_result: str) -> None:
        try:
            from sqlalchemy import select
            result = await self.db.execute(
                select(ComputerUseStep).where(
                    ComputerUseStep.session_id == UUID(self.session_id),
                    ComputerUseStep.step_number == step_number,
                )
            )
            step = result.scalar_one_or_none()
            if step:
                step.execution_result = execution_result
                await self.db.commit()
        except Exception as e:
            logger.error(f"DB update step error: {e}")

    async def _save_message(self, role: str, content: str) -> None:
        try:
            msg = ComputerUseMessage(
                session_id=UUID(self.session_id),
                role=role,
                content=content,
            )
            self.db.add(msg)
            await self.db.commit()
        except Exception as e:
            logger.error(f"DB save message error: {e}")
            await self.db.rollback()
