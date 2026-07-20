"""Computer Use — Session Manager v2

Versión mejorada con: Browser Pool, Action Validator, Retry Handler,
CAPTCHA Detector, Screenshot Comparator, y Webhook notifications.
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
from app.domains.computer_use.services.browser_pool import get_browser_pool, BrowserPoolManager
from app.domains.computer_use.services.action_validator import ActionValidator
from app.domains.computer_use.services.retry_handler import RetryHandler, get_circuit_breaker
from app.domains.computer_use.services.captcha_detector import CaptchaDetector
from app.domains.computer_use.services.screenshot_compare import ScreenshotComparator
from app.domains.computer_use.services.webhook_service import WebhookService
from app.domains.computer_use.services.credential_manager import CredentialManager
from app.domains.computer_use.services.sellia_brain_service import (
    get_brain_service,
    ActionContext,
    SalesStage,
    Platform,
)
from app.domains.computer_use.skills import (
    AutopilotPolicy,
    AutopilotMode,
    build_skill_brief,
)
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

_active_sessions: Dict[str, "ComputerUseSessionManagerV2"] = {}


def get_session_manager(session_id: str) -> Optional["ComputerUseSessionManagerV2"]:
    return _active_sessions.get(session_id)


def remove_session_manager(session_id: str) -> None:
    _active_sessions.pop(session_id, None)


class ComputerUseSessionManagerV2:
    """Session manager mejorado con todas las capacidades nuevas."""

    def __init__(
        self,
        session_id: UUID,
        db: AsyncSession,
        task: str,
        start_url: Optional[str] = None,
        api_key: Optional[str] = None,
        provider: str = "openai",
        browser_type: str = "chromium",
        profile: Optional[dict] = None,
        proxy: Optional[dict] = None,
        webhooks: Optional[list] = None,
        user_id: Optional[UUID] = None,
        mode: str = "supervised",
    ):
        self.session_id = str(session_id)
        self.db = db
        self.task = task
        self.start_url = start_url
        self.api_key = api_key
        self.provider = provider
        self.browser_type = browser_type
        self.profile = profile
        self.proxy = proxy
        self.webhooks = webhooks or []
        self.user_id = user_id
        try:
            self.mode = AutopilotMode(mode)
        except ValueError:
            self.mode = AutopilotMode.SUPERVISED
        self.policy = AutopilotPolicy(self.mode)
        self._skill_brief: Optional[str] = None  # cacheado en el primer paso

        # Services
        self.browser = BrowserService()
        self.vision = VisionAgent(api_key=api_key, provider=provider)
        self.validator = ActionValidator()
        self.retry_handler = RetryHandler()
        self.captcha_detector = CaptchaDetector()
        self.comparator = ScreenshotComparator()
        self.webhook_service = WebhookService()
        self.credential_manager = CredentialManager(db_session=db, user_id=str(user_id) if user_id else None)
        self.brain_service = get_brain_service()

        self.status = "pending"
        self.current_step = 0
        self.max_steps = settings.COMPUTER_USE_MAX_STEPS
        self.history: List[Dict[str, Any]] = []
        self.user_chat_queue: List[str] = []
        self._previous_screenshot: Optional[bytes] = None

        self._pause_event = asyncio.Event()
        self._pause_event.set()
        self._stop_event = asyncio.Event()

        self._screenshots_dir = os.path.join(os.getcwd(), "storage", "screenshots", self.session_id)
        os.makedirs(self._screenshots_dir, exist_ok=True)
        self._cleanup_done = False
        self._session_start_time = None
        self._provider_name = "unknown"

    async def _send_ws(self, message: dict):
        try:
            await ws_manager.send_message(self.session_id, message)
        except Exception as e:
            logger.warning(f"WS send failed for session {self.session_id}: {e}")

    async def start(self) -> None:
        self._session_start_time = time.time()
        try:
            await self.browser.start(headless=True)
            self.status = "running"
            _active_sessions[self.session_id] = self

            try:
                self._provider_name = getattr(self.vision.provider, "provider_name", "unknown")
            except Exception:
                pass

            COMPUTER_USE_SESSIONS_CREATED.labels(provider=self._provider_name).inc()
            COMPUTER_USE_ACTIVE_SESSIONS.inc()
            await self._update_session_status("running")

            await self._send_ws({
                "type": "status",
                "data": {"status": "running", "message": "Sesión iniciada", "step": 0, "total_steps": self.max_steps},
            })

            if self.start_url:
                nav_result = await self.retry_handler.execute(self.browser.navigate, self.start_url)
                if not nav_result.get("success"):
                    await self._fail(f"No se pudo navegar a {self.start_url}: {nav_result.get('error')}")
                    return

                # Auto-login con Credential Manager si hay credenciales guardadas
                try:
                    login_result = await self.credential_manager.attempt_login(
                        self.browser.page, self.start_url
                    )
                    if login_result.get("success"):
                        await self._send_ws({
                            "type": "message",
                            "data": {"role": "system", "content": f"✅ Auto-login exitoso en {self.start_url}"},
                        })
                except Exception as e:
                    logger.warning(f"Auto-login failed for {self.start_url}: {e}")

            await self._run_loop()

        except Exception as e:
            logger.exception(f"Session {self.session_id} failed to start")
            await self._fail(str(e))
        finally:
            await self._cleanup()

    async def _run_loop(self) -> None:
        try:
            while self.current_step < self.max_steps:
                if self._stop_event.is_set():
                    await self._stop()
                    return

                if not self._pause_event.is_set():
                    await self._send_ws({
                        "type": "status",
                        "data": {"status": "paused", "message": "Sesión pausada", "step": self.current_step, "total_steps": self.max_steps},
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

                # Screenshot with retry
                try:
                    screenshot_bytes = await self.retry_handler.execute(self.browser.screenshot)
                except Exception as e:
                    await self._fail(f"Screenshot error: {e}")
                    return

                # Save screenshot
                screenshot_path = os.path.join(self._screenshots_dir, f"step_{self.current_step}.jpg")
                with open(screenshot_path, "wb") as f:
                    f.write(screenshot_bytes)
                relative_path = f"screenshots/{self.session_id}/step_{self.current_step}.jpg"

                # Detect stale state
                if self._previous_screenshot:
                    comp = self.comparator.compare(self._previous_screenshot, screenshot_bytes)
                    if not comp.changed and self.current_step > 1:
                        logger.info(f"Session {self.session_id}: stale state detected at step {self.current_step}")
                        await self._send_ws({
                            "type": "status",
                            "data": {"status": "running", "message": f"⚠️ Estado sin cambios (similitud: {comp.similarity:.1%})", "step": self.current_step, "total_steps": self.max_steps},
                        })
                self._previous_screenshot = screenshot_bytes

                # CAPTCHA detection
                try:
                    is_captcha, confidence, reason = await self.captcha_detector.detect_from_page(self.browser._page)
                    if is_captcha:
                        await self._send_ws({
                            "type": "status",
                            "data": {"status": "paused", "message": self.captcha_detector.get_user_message(confidence), "step": self.current_step, "total_steps": self.max_steps},
                        })
                        await self.pause()
                        # Notify webhooks
                        for wh in self.webhooks:
                            await self.webhook_service.notify_captcha_detected(
                                wh["url"], self.session_id, confidence, reason, wh.get("secret")
                            )
                        await self._pause_event.wait()
                except Exception as e:
                    logger.warning(f"CAPTCHA detection error: {e}")

                page_info = await self.browser.get_page_info()

                # Interactive-element map → precise clicks (DOM coords beat pixel guessing)
                try:
                    elements = await self.browser.get_interactive_elements(limit=50)
                    if elements:
                        lines = [
                            f"- [{e['role']}] \"{e['label']}\" @ ({e['x']},{e['y']})"
                            for e in elements if e.get("label")
                        ]
                        if lines:
                            page_info["elements_text"] = (
                                "Interactive elements (role, label, click center x,y):\n"
                                + "\n".join(lines[:40])
                            )
                except Exception as e:
                    logger.debug(f"interactive elements snapshot skipped: {e}")

                # Expert sales-agent knowledge → richer, on-domain decisions.
                try:
                    if self._skill_brief is None:
                        self._skill_brief = build_skill_brief(self.task, page_info.get("url"))
                    if self._skill_brief:
                        page_info["skill_brief"] = self._skill_brief
                except Exception as e:
                    logger.debug(f"skill brief skipped: {e}")

                # Send screenshot
                await self._send_ws({
                    "type": "screenshot",
                    "data": {
                        "image_base64": base64.b64encode(screenshot_bytes).decode("utf-8"),
                        "step": self.current_step,
                        "url": page_info.get("url", ""),
                    },
                })

                # User chat
                user_message = None
                if self.user_chat_queue:
                    user_message = self.user_chat_queue.pop(0)
                    await self._send_ws({
                        "type": "chat",
                        "data": {"role": "user", "content": user_message},
                    })
                    await self._save_message("user", user_message)

                # Vision agent with circuit breaker
                try:
                    cb = get_circuit_breaker(f"vision_{self._provider_name}")
                    action = await cb.call(
                        self.vision.decide_action,
                        screenshot_bytes=screenshot_bytes,
                        task=self.task,
                        history=self.history,
                        user_message=user_message,
                        page_info=page_info,
                    )
                except Exception as e:
                    await self._fail(f"Vision agent error: {e}")
                    return

                # Validate action
                is_valid, error_msg = self.validator.validate_action(
                    action.action_type, action.params, page_info.get("url")
                )
                if not is_valid:
                    logger.warning(f"Invalid action blocked: {error_msg}")
                    await self._send_ws({
                        "type": "error",
                        "data": {"message": f"Acción bloqueada: {error_msg}"},
                    })
                    # Try to recover with a safe action
                    action = ComputerUseAction(action_type="screenshot", params={}, reason=f"Acción anterior bloqueada: {error_msg}")

                # Autopilot / supervised governance: gate risky actions.
                if action.action_type not in ("done", "error", "screenshot"):
                    decision = self.policy.evaluate(action.action_type, action.params, action.reason)
                    if decision.require_confirmation:
                        await self._send_ws({
                            "type": "confirmation_required",
                            "data": {
                                "step": self.current_step,
                                "risk": decision.risk.value,
                                "reason": decision.reason,
                                "action_type": action.action_type,
                                "params": action.params,
                                "mode": self.mode.value,
                                "message": f"⚠️ {decision.reason} Aprueba (reanudar) o detén la sesión.",
                            },
                        })
                        for wh in self.webhooks:
                            try:
                                await self.webhook_service.notify_captcha_detected(
                                    wh["url"], self.session_id,
                                    1.0, f"confirmation_required: {decision.reason}", wh.get("secret"),
                                )
                            except Exception as e:
                                logger.debug(f"confirm webhook skipped: {e}")
                        await self.pause()
                        await self._pause_event.wait()  # resume = aprobación humana
                        if self._stop_event.is_set():
                            await self._stop()
                            return
                    elif decision.risk.value in ("high", "critical"):
                        # Autopilot ejecuta pero deja rastro de auditoría.
                        await self._send_ws({
                            "type": "message",
                            "data": {"role": "system", "content": f"🤖 [auto] {decision.reason}"},
                        })

                # Send action
                await self._send_ws({
                    "type": "action",
                    "data": {
                        "action_type": action.action_type,
                        "params": action.params,
                        "reason": action.reason,
                        "step": self.current_step,
                    },
                })

                # Save step
                await self._save_step(
                    step_number=self.current_step,
                    screenshot_path=relative_path,
                    action=action,
                    page_url=page_info.get("url"),
                )

                # Execute action with retry
                try:
                    execution_result = await self.retry_handler.execute(self._execute_action, action)
                except Exception as e:
                    execution_result = f"Error tras reintentos: {e}"

                await self._update_step_result(self.current_step, execution_result)

                self.history.append({
                    "step_number": self.current_step,
                    "action_type": action.action_type,
                    "params": action.params,
                    "reason": action.reason,
                    "result": execution_result,
                })

                if action.action_type == "done":
                    summary = action.params.get("summary", "")
                    if not summary:
                        summary = await self.vision.generate_summary(self.history)
                    await self._complete(summary)
                    return

                if action.action_type == "error":
                    await self._fail(action.params.get("message", "Error del agente"))
                    return

                await self._update_session_progress(page_info.get("url"))
                COMPUTER_USE_STEPS_TOTAL.labels(action_type=action.action_type).inc()
                COMPUTER_USE_STEP_DURATION.observe(time.time() - step_start)
                await asyncio.sleep(1.0)

            summary = await self.vision.generate_summary(self.history)
            await self._complete(f"{summary}\n\n(Límite de {self.max_steps} pasos alcanzado)")

        except asyncio.CancelledError:
            logger.info(f"Session {self.session_id} cancelled")
            await self._stop()
        except Exception as e:
            logger.exception(f"Session {self.session_id} loop error")
            await self._fail(str(e))

    async def _execute_action(self, action: ComputerUseAction) -> str:
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
            elif action.action_type == "press_key":
                result = await self.browser.press_key(params["key"])
            # ── DOM-precise actions (higher accuracy than coordinates) ──
            elif action.action_type == "click_selector":
                result = await self.browser.click_selector(params["selector"])
            elif action.action_type == "click_text":
                result = await self.browser.click_text(params["text"], params.get("exact", False))
            elif action.action_type == "fill":
                result = await self.browser.fill(params["selector"], params["value"])
            elif action.action_type == "wait_for_selector":
                result = await self.browser.wait_for_selector(params["selector"], params.get("timeout_ms"))
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
        if self.status == "running":
            self.status = "paused"
            self._pause_event.clear()
            await self._update_session_status("paused")
            logger.info(f"Session {self.session_id} paused")

    async def resume(self) -> None:
        if self.status == "paused":
            self.status = "running"
            self._pause_event.set()
            await self._update_session_status("running")
            logger.info(f"Session {self.session_id} resumed")

    async def stop(self) -> None:
        self._stop_event.set()
        self._pause_event.set()
        logger.info(f"Session {self.session_id} stop requested")

    async def _stop(self) -> None:
        self.status = "stopped"
        await self._cleanup()
        await self._update_session_status("stopped")
        COMPUTER_USE_SESSIONS_STOPPED.inc()
        if self._session_start_time:
            COMPUTER_USE_SESSION_DURATION.observe(time.time() - self._session_start_time)
        await self._send_ws({
            "type": "status",
            "data": {"status": "stopped", "message": "Sesión detenida", "step": self.current_step, "total_steps": self.max_steps},
        })

    async def _complete(self, summary: str) -> None:
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
        # Notify webhooks
        session_data = {"id": self.session_id, "total_steps": self.current_step, "task_description": self.task, "result_data": {"summary": summary}}
        for wh in self.webhooks:
            await self.webhook_service.notify_session_completed(wh["url"], session_data, wh.get("secret"))

    async def _fail(self, error_message: str) -> None:
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
        # Notify webhooks
        session_data = {"id": self.session_id, "total_steps": self.current_step, "task_description": self.task}
        for wh in self.webhooks:
            await self.webhook_service.notify_session_failed(wh["url"], session_data, error_message, wh.get("secret"))

    async def _cleanup(self) -> None:
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
        self.user_chat_queue.append(message)
        await self._send_ws({
            "type": "chat",
            "data": {"role": "user", "content": message},
        })
        await self._save_message("user", message)

    # DB helpers
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

    async def _save_step(self, step_number: int, screenshot_path: str, action: ComputerUseAction, page_url: Optional[str]) -> None:
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
                step.execution_ms = 0
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

    async def _enrich_vision_prompt_with_brain_strategy(
        self,
        base_prompt: str,
        customer_profile: Optional[dict] = None,
        conversation_history: Optional[list] = None,
    ) -> str:
        """
        Enriquece el prompt del vision agent con estrategia del Brain.

        Lee contexto actual → consulta SellIA Brain → injeta estrategia óptima.
        """
        try:
            # 1. Detectar plataforma (assumption: estamos en mercadolibre, shopify, etc)
            platform = self._detect_platform_from_context()

            # 2. Detectar etapa de venta (awareness, decision, closure, etc)
            stage = self._detect_sales_stage(conversation_history or [])

            # 3. Crear contexto para Brain
            context = ActionContext(
                platform=platform,
                stage=stage,
                customer_profile=customer_profile or {},
                conversation_history=conversation_history or [],
            )

            # 4. Consultar Brain por estrategia óptima
            strategy = await self.brain_service.get_strategy(context)

            if not strategy:
                return base_prompt

            # 5. Enriquecer prompt con estrategia
            enriched_prompt = f"""{base_prompt}

## SellIA Brain Strategy Injection

Strategy: {strategy.strategy_name}
Confidence: {strategy.confidence:.0%}
Tactics: {', '.join(strategy.tactics)}

Reasoning: {strategy.reasoning}

Apply this strategy to your next action:
- Use tactics: {', '.join(strategy.tactics)}
- Maintain the approach: {strategy.strategy_name}
- Keep confidence: {strategy.confidence:.0%}

Template guidance:
{strategy.prompt_template}
"""
            logger.debug(
                f"Vision prompt enriched with strategy: {strategy.strategy_name} "
                f"(confidence: {strategy.confidence:.0%})"
            )

            return enriched_prompt

        except Exception as e:
            logger.error(f"Error enriching prompt with brain strategy: {e}")
            return base_prompt

    def _detect_platform_from_context(self) -> Platform:
        """Detecta plataforma del contexto de URL o task."""
        url = self.start_url or ""
        task = self.task.lower()

        if "mercadolibre" in url or "ml" in task:
            return Platform.MERCADOLIBRE
        elif "amazon" in url:
            return Platform.AMAZON
        elif "instagram" in url or "instagram" in task:
            return Platform.INSTAGRAM
        elif "tiktok" in url or "tiktok" in task:
            return Platform.TIKTOK
        elif "whatsapp" in url or "whatsapp" in task:
            return Platform.WHATSAPP
        elif "email" in task:
            return Platform.EMAIL
        elif "linkedin" in url or "linkedin" in task:
            return Platform.LINKEDIN

        return Platform.WEBSITE

    def _detect_sales_stage(self, conversation_history: List[Dict[str, Any]]) -> SalesStage:
        """Detecta etapa de venta basada en conversación."""
        if len(conversation_history) == 0:
            return SalesStage.AWARENESS

        # Analizar últimos mensajes para detectar etapa
        last_messages = conversation_history[-3:] if len(conversation_history) >= 3 else conversation_history

        message_text = " ".join([msg.get("content", "").lower() for msg in last_messages])

        # Señales de cierre
        if any(word in message_text for word in ["precio", "cuánto", "costo", "descuento", "oferta"]):
            return SalesStage.DECISION

        if any(word in message_text for word in ["cuándo", "entregar", "envío", "shipping", "entrega"]):
            return SalesStage.NEGOTIATION

        if any(word in message_text for word in ["confirmar", "listo", "acuerdo", "confirmed", "ready"]):
            return SalesStage.CLOSURE

        # Por defecto consideration
        return SalesStage.CONSIDERATION
