"""Visual Confirmation — Verify Action Success

Responsibilities:
- Verify action succeeded (did button click work?)
- Detect errors (error messages, validation highlights)
- Detect success states (checkmarks, green highlights)
- Detect loading states (spinners, progress bars)
- Detect popups/modals that need dismissal

No selectors needed. Pure visual verification.
"""

import logging
import base64
import json
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ActionResult(Enum):
    """Resultado de una acción."""
    SUCCESS = "success"
    ERROR = "error"
    LOADING = "loading"
    MODAL_APPEARED = "modal_appeared"
    REDIRECT = "redirect"
    UNKNOWN = "unknown"


@dataclass
class Confirmation:
    """Confirmación de resultado de acción."""
    result: ActionResult
    confidence: float
    message: str
    details: Optional[Dict[str, Any]] = None
    error_messages: Optional[List[str]] = None
    loading_indicators: Optional[List[str]] = None
    modal_present: bool = False


class VisualConfirmation:
    """Verifica si las acciones tuvieron efecto usando visión."""

    def __init__(self, anthropic_client=None, visual_analyzer=None):
        self.anthropic = anthropic_client
        self.analyzer = visual_analyzer

    async def verify_action_succeeded(
        self,
        before_screenshot: bytes,
        after_screenshot: bytes,
        action_description: str,
        expected_indicators: Optional[List[str]] = None
    ) -> Confirmation:
        """Verifica si una acción tuvo éxito comparando screenshots.

        Args:
            before_screenshot: Screenshot antes de la acción
            after_screenshot: Screenshot después de la acción
            action_description: Qué acción se ejecutó (ej: "Clicked submit button")
            expected_indicators: Indicadores visuales esperados

        Returns:
            Confirmation con resultado
        """
        if self.anthropic:
            return await self._verify_with_claude(
                before_screenshot,
                after_screenshot,
                action_description,
                expected_indicators
            )
        else:
            raise ValueError("Anthropic client required for verification")

    async def _verify_with_claude(
        self,
        before_screenshot: bytes,
        after_screenshot: bytes,
        action_description: str,
        expected_indicators: Optional[List[str]] = None
    ) -> Confirmation:
        """Usa Claude Vision para comparar y verificar."""
        logger.info(f"Verifying action: {action_description}")

        before_b64 = base64.standard_b64encode(before_screenshot).decode("utf-8")
        after_b64 = base64.standard_b64encode(after_screenshot).decode("utf-8")

        prompt = f"""Compara estos dos screenshots para verificar si la acción fue exitosa.

ACCIÓN REALIZADA: {action_description}

{f'INDICADORES ESPERADOS: {", ".join(expected_indicators)}' if expected_indicators else ''}

Analiza qué cambió entre ANTES y DESPUÉS:
1. ¿La página se recargó? ¿Cambió la URL?
2. ¿Hay un loading spinner/progress bar?
3. ¿Aparece un modal/popup?
4. ¿Hay mensajes de error (rojo, iconos de error)?
5. ¿Hay confirmación de éxito (verde, checkmark, success message)?
6. ¿Cambió algo en el contenido/layout?
7. ¿Se desapareció un elemento?

Responde SOLO en JSON:
{{
  "result": "success|error|loading|modal_appeared|redirect|unknown",
  "confidence": 0.95,
  "message": "Descripción corta del resultado",
  "details": {{"change": "La acción completó exitosamente"}},
  "error_messages": [],
  "loading_indicators": [],
  "modal_present": false,
  "visual_differences": ["El botón desapareció", "Aparece un success message", ...]
}}"""

        try:
            response = await asyncio.to_thread(
                self.anthropic.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "ANTES (antes de la acción):"
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": before_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": "DESPUÉS (después de la acción):"
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": after_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            response_text = response.content[0].text
            data = json.loads(response_text)

            return self._parse_confirmation_response(data)

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            raise

    async def detect_errors(
        self,
        screenshot_bytes: bytes
    ) -> List[str]:
        """Detecta mensajes de error en pantalla."""
        logger.info("Detecting error messages")

        screenshot_b64 = base64.standard_b64encode(screenshot_bytes).decode("utf-8")

        prompt = """Encuentra TODOS los mensajes de error visibles en esta pantalla.

Busca:
- Texto rojo
- Iconos de error (X, !, etc)
- Campos destacados en rojo
- Banners de error
- Popups de error

Responde SOLO con JSON:
{
  "errors": ["Error message 1", "Error message 2", ...],
  "error_locations": ["Campo 'email'", "Botón de envío", ...],
  "has_errors": true|false
}"""

        try:
            response = await asyncio.to_thread(
                self.anthropic.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": screenshot_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            response_text = response.content[0].text
            data = json.loads(response_text)

            return data.get("errors", [])

        except Exception as e:
            logger.error(f"Error detection failed: {e}")
            return []

    async def detect_success_state(
        self,
        screenshot_bytes: bytes
    ) -> bool:
        """Detecta si hay un estado de éxito visible."""
        logger.info("Detecting success state")

        screenshot_b64 = base64.standard_b64encode(screenshot_bytes).decode("utf-8")

        prompt = """¿Hay un indicador visual de éxito en esta pantalla?

Busca:
- Texto verde o success message
- Checkmark/tick icons
- Success banners
- "Enviado exitosamente", "Guardado", "Completado", etc
- Green highlight en elementos
- Progress bars al 100%

Responde SOLO: {"has_success": true|false, "message": "...", "confidence": 0.95}"""

        try:
            response = await asyncio.to_thread(
                self.anthropic.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": screenshot_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            response_text = response.content[0].text
            data = json.loads(response_text)

            return data.get("has_success", False)

        except Exception as e:
            logger.error(f"Success detection failed: {e}")
            return False

    async def detect_loading_state(
        self,
        screenshot_bytes: bytes
    ) -> bool:
        """Detecta si hay un loading spinner/progress bar."""
        logger.info("Detecting loading state")

        screenshot_b64 = base64.standard_b64encode(screenshot_bytes).decode("utf-8")

        prompt = """¿Hay un indicador de loading/progress visible?

Busca:
- Spinners/loaders animados
- Progress bars (parcialmente llenos)
- "Cargando..." texto
- Overlay semitransparente
- Disabled buttons (indica processing)

Responde SOLO: {"is_loading": true|false, "type": "spinner|progress|text|overlay", "confidence": 0.9}"""

        try:
            response = await asyncio.to_thread(
                self.anthropic.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": screenshot_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            response_text = response.content[0].text
            data = json.loads(response_text)

            return data.get("is_loading", False)

        except Exception as e:
            logger.error(f"Loading state detection failed: {e}")
            return False

    async def detect_modal_popup(
        self,
        screenshot_bytes: bytes
    ) -> Dict[str, Any]:
        """Detecta si hay un modal/popup abierto."""
        logger.info("Detecting modal/popup")

        screenshot_b64 = base64.standard_b64encode(screenshot_bytes).decode("utf-8")

        prompt = """¿Hay un modal/popup/dialog visible?

Busca:
- Overlay/backdrop (fondo oscuro)
- Dialog box/centered content
- Close button (X, "Cancel", etc)
- Modal header/title
- Buttons dentro del modal

Responde SOLO: {
  "has_modal": true|false,
  "modal_type": "alert|confirm|form|custom|none",
  "title": "...",
  "close_button_present": true|false,
  "buttons": ["OK", "Cancel", ...],
  "content": "Main modal content/message"
}"""

        try:
            response = await asyncio.to_thread(
                self.anthropic.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": screenshot_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            response_text = response.content[0].text
            return json.loads(response_text)

        except Exception as e:
            logger.error(f"Modal detection failed: {e}")
            return {"has_modal": False}

    async def detect_form_validation_errors(
        self,
        screenshot_bytes: bytes
    ) -> Dict[str, Any]:
        """Detecta errores de validación en campos de formulario."""
        logger.info("Detecting form validation errors")

        screenshot_b64 = base64.standard_b64encode(screenshot_bytes).decode("utf-8")

        prompt = """Detecta errores de validación en este formulario.

Busca:
- Campos destacados en rojo/naranja
- Mensajes de error bajo campos
- Bordes rojos en inputs
- Asteriscos rojos (campos requeridos vacíos)
- Error icons (X, !, etc)

Responde SOLO: {
  "has_validation_errors": true|false,
  "fields_with_errors": [
    {"field_name": "email", "error_message": "Invalid email"},
    ...
  ],
  "total_errors": 2,
  "confidence": 0.9
}"""

        try:
            response = await asyncio.to_thread(
                self.anthropic.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=600,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": screenshot_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            response_text = response.content[0].text
            return json.loads(response_text)

        except Exception as e:
            logger.error(f"Form validation detection failed: {e}")
            return {"has_validation_errors": False}

    def _parse_confirmation_response(self, data: Dict[str, Any]) -> Confirmation:
        """Parsea respuesta de verificación."""
        result_str = data.get("result", "unknown").lower()
        result_map = {
            "success": ActionResult.SUCCESS,
            "error": ActionResult.ERROR,
            "loading": ActionResult.LOADING,
            "modal_appeared": ActionResult.MODAL_APPEARED,
            "redirect": ActionResult.REDIRECT,
            "unknown": ActionResult.UNKNOWN,
        }

        return Confirmation(
            result=result_map.get(result_str, ActionResult.UNKNOWN),
            confidence=data.get("confidence", 0.5),
            message=data.get("message", ""),
            details=data.get("details"),
            error_messages=data.get("error_messages", []),
            loading_indicators=data.get("loading_indicators", []),
            modal_present=data.get("modal_present", False)
        )

    async def wait_for_condition(
        self,
        screenshot_getter,
        condition_checker,
        timeout_seconds: float = 30,
        poll_interval: float = 0.5
    ) -> bool:
        """Espera hasta que se cumpla una condición visual.

        Args:
            screenshot_getter: Función async que retorna screenshot
            condition_checker: Función async que verifica condición
            timeout_seconds: Segundos máximo de espera
            poll_interval: Segundos entre chequeos

        Returns:
            True si se cumplió, False si timeout
        """
        import time
        start = time.time()

        while time.time() - start < timeout_seconds:
            screenshot = await screenshot_getter()
            if await condition_checker(screenshot):
                logger.info(f"Condition met after {time.time() - start:.2f}s")
                return True

            await asyncio.sleep(poll_interval)

        logger.warning(f"Condition not met within {timeout_seconds}s")
        return False
