"""Platform Automation Engine — Execute browser scripts on messaging platforms.

Unifica WhatsApp Web, Instagram, Facebook Messenger, TikTok, etc.
Automatiza envío de respuestas sin dependencia de Computer Use.
"""

import logging
from typing import Optional, Dict, Any, Tuple
from enum import Enum

from app.domains.computer_use.platform_scripts.registry import get_script_for_task
from app.domains.computer_use.browser_service import BrowserService

logger = logging.getLogger(__name__)


class PlatformAutomationType(str, Enum):
    """Tipos de automation disponibles."""
    WHATSAPP_WEB = "whatsapp_web"
    FACEBOOK_MESSENGER = "messenger"
    INSTAGRAM_DM = "instagram_dm"
    TIKTOK_DM = "tiktok_dm"
    FACEBOOK_COMMENT = "facebook_comment"
    MERCADOLIBRE_MESSAGE = "mercadolibre_message"


class PlatformAutomationEngine:
    """Ejecuta scripts de automatización en plataformas de mensajería."""

    def __init__(self, browser_service: Optional[BrowserService] = None):
        self.browser_service = browser_service or BrowserService()
        self.logger = logger

    async def send_response(
        self,
        platform: PlatformAutomationType,
        recipient_identifier: str,  # nombre, usuario, teléfono, etc
        response_text: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Envía respuesta via browser automation.

        recipient_identifier: nombre (WhatsApp/IG), usuario (IG/TikTok), teléfono (WhatsApp), etc
        response_text: texto a enviar

        Retorna: (success, message_id o error)
        """
        try:
            # Obtener script para plataforma
            script = get_script_for_task(platform.value, "respond_message")

            if not script:
                self.logger.error(f"No script found for platform {platform.value}")
                return False, None

            # Preparar parámetros según plataforma
            params = self._prepare_params(platform, recipient_identifier, response_text)

            # Obtener steps de automación
            steps = script.get_task_steps("respond_message", params)

            # Ejecutar steps en navegador
            await self.browser_service.start(headless=False)  # No headless para user browser

            success = await self._execute_steps(steps)

            await self.browser_service.stop()

            if success:
                self.logger.info(f"Message sent to {recipient_identifier} via {platform.value}")
                return True, f"sent_{platform.value}_{recipient_identifier}"
            else:
                return False, None

        except Exception as e:
            self.logger.error(f"Error sending response: {e}")
            return False, None

    async def respond_to_comment(
        self,
        platform: PlatformAutomationType,
        post_id: str,
        comment_text: str,
        response_text: str,
    ) -> Tuple[bool, Optional[str]]:
        """Responde a comentarios en posts."""
        try:
            script = get_script_for_task(platform.value, "respond_comment")

            if not script:
                self.logger.warning(f"No comment response script for {platform.value}")
                return False, None

            params = {
                "post_id": post_id,
                "comment_text": comment_text,
                "response_text": response_text,
            }

            steps = script.get_task_steps("respond_comment", params)

            await self.browser_service.start(headless=False)
            success = await self._execute_steps(steps)
            await self.browser_service.stop()

            if success:
                self.logger.info(f"Comment response posted to {post_id} via {platform.value}")
                return True, f"replied_{platform.value}_{post_id}"

            return False, None

        except Exception as e:
            self.logger.error(f"Error responding to comment: {e}")
            return False, None

    # ── Private ──────────────────────────────────────────────

    def _prepare_params(
        self,
        platform: PlatformAutomationType,
        recipient_identifier: str,
        response_text: str,
    ) -> Dict[str, Any]:
        """Prepara parámetros según plataforma."""
        if platform == PlatformAutomationType.WHATSAPP_WEB:
            # recipient_identifier puede ser nombre o número
            if recipient_identifier.isdigit():
                return {"phone_number": recipient_identifier, "message_text": response_text}
            else:
                return {"customer_name": recipient_identifier, "response_text": response_text}

        elif platform == PlatformAutomationType.FACEBOOK_MESSENGER:
            return {"customer_name": recipient_identifier, "response_text": response_text}

        elif platform == PlatformAutomationType.INSTAGRAM_DM:
            return {"customer_username": recipient_identifier, "response_text": response_text}

        elif platform == PlatformAutomationType.TIKTOK_DM:
            return {"creator_username": recipient_identifier, "message_text": response_text}

        else:
            return {"recipient": recipient_identifier, "message": response_text}

    async def _execute_steps(self, steps: list) -> bool:
        """Ejecuta pasos de script en navegador."""
        try:
            for i, step in enumerate(steps):
                if step is None:
                    continue

                action = step.action
                target = step.target
                value = step.value if hasattr(step, 'value') else None
                wait_ms = step.wait_ms if hasattr(step, 'wait_ms') else None
                description = step.description

                self.logger.debug(f"Step {i + 1}: {description}")

                # Ejecutar acción
                if action == "navigate":
                    await self.browser_service.navigate(target)

                elif action == "wait":
                    import asyncio
                    await asyncio.sleep((wait_ms or 1000) / 1000.0)

                elif action == "click":
                    await self.browser_service.click(target)

                elif action == "type":
                    await self.browser_service.type_text(target, value)

                elif action == "screenshot":
                    await self.browser_service.screenshot()

                else:
                    self.logger.warning(f"Unknown action: {action}")

            return True

        except Exception as e:
            self.logger.error(f"Error executing steps: {e}")
            return False


def get_platform_automation_engine(
    browser_service: Optional[BrowserService] = None,
) -> PlatformAutomationEngine:
    return PlatformAutomationEngine(browser_service)
