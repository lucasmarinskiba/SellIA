"""
Computer Vision Engine — 100% integrado en Computer Use.

Lee interfaz FeedIA (screenshots) → entiende qué hacer → ejecuta automático.

APIs:
- Claude Vision API (built-in, gratis con Anthropic)
- Google Cloud Vision (backup, OCR + object detection)
- Tesseract OCR (local, offline)
"""

import logging
import base64
import httpx
from typing import Dict, List, Any, Optional
import anthropic

logger = logging.getLogger(__name__)


class ComputerVisionEngine:
    """Computer Vision para entender interfaces web automáticamente."""

    def __init__(self, anthropic_api_key: str, google_vision_api_key: Optional[str] = None):
        self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.google_api_key = google_vision_api_key
        self.http_client = httpx.AsyncClient(timeout=30)

    # ========== SCREENSHOT ANALYSIS ==========

    async def analyze_feedia_interface(
        self,
        screenshot_bytes: bytes,
    ) -> Dict[str, Any]:
        """
        Claude Vision analiza screenshot de FeedIA.

        Lee: botones, campos, opciones disponibles, estado actual
        Retorna: qué se ve, qué se puede hacer, recomendación de acción
        """

        logger.info("Analyzing FeedIA interface with Computer Vision")

        # Convertir screenshot a base64
        screenshot_b64 = base64.standard_b64encode(screenshot_bytes).decode("utf-8")

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
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
                                "text": """Analiza esta interfaz de FeedIA.

Identifica y describe:
1. Título/sección actual
2. Botones disponibles (qué hace cada uno)
3. Campos de entrada (qué tipos, validaciones)
4. Opciones/dropdowns (qué opciones hay)
5. Estado actual (completado, error, en progreso?)
6. Siguiente paso lógico

Responde en JSON: {
  "current_section": "...",
  "available_actions": [{"button": "...", "action": "...", "selector": "..."}],
  "input_fields": [{"label": "...", "type": "...", "value": "..."}],
  "dropdowns": [{"label": "...", "options": [...]}],
  "status": "...",
  "next_recommended_action": "...",
  "confidence": 0.95
}""",
                            },
                        ],
                    }
                ],
            )

            import json
            import re

            response_text = response.content[0].text

            try:
                analysis = json.loads(response_text)
            except json.JSONDecodeError:
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                analysis = json.loads(json_match.group(0)) if json_match else {"raw": response_text}

            return {
                "status": "success",
                "analysis": analysis,
                "model": "claude-vision",
            }

        except Exception as e:
            logger.error(f"Claude Vision analysis failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    # ========== BUTTON DETECTION ==========

    async def detect_clickable_elements(
        self,
        screenshot_bytes: bytes,
    ) -> Dict[str, Any]:
        """
        Detecta botones, links, campos clickeables con sus posiciones.

        Retorna: {button_name, action, bounding_box, selector}
        """

        logger.info("Detecting clickable elements")

        screenshot_b64 = base64.standard_b64encode(screenshot_bytes).decode("utf-8")

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
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
                                "text": """Detecta todos los elementos clickeables en esta interfaz.

Para cada botón/link/input/dropdown:
- Nombre (texto que dice)
- Acción (qué hace si lo clickeo)
- Posición aproximada (arriba, centro, abajo; izq, centro, der)
- Tipo (button, link, input, dropdown, tab)
- Selector CSS probable

Responde en JSON:
{
  "elements": [
    {
      "name": "Crear Carrusel",
      "action": "Opens carousel creation wizard",
      "position": {"x": "center", "y": "top"},
      "type": "button",
      "selector": "button[data-action='create-carousel']",
      "priority": 1
    }
  ]
}""",
                            },
                        ],
                    }
                ],
            )

            import json
            import re

            response_text = response.content[0].text

            try:
                detection = json.loads(response_text)
            except json.JSONDecodeError:
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                detection = json.loads(json_match.group(0)) if json_match else {"raw": response_text}

            return {
                "status": "success",
                "elements": detection.get("elements", []),
            }

        except Exception as e:
            logger.error(f"Element detection failed: {str(e)}")
            return {"status": "error"}

    # ========== TEXT RECOGNITION (OCR) ==========

    async def extract_text_from_screenshot(
        self,
        screenshot_bytes: bytes,
    ) -> Dict[str, Any]:
        """
        Extrae TODO el texto visible en screenshot.

        Útil para: leer mensajes de error, validar contenido completado, etc.
        """

        logger.info("Extracting text from screenshot")

        screenshot_b64 = base64.standard_b64encode(screenshot_bytes).decode("utf-8")

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
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
                                "text": "Extrae TODO el texto visible. Responde en JSON: {\"text\": \"...\", \"sections\": [{\"heading\": \"...\", \"content\": \"...\"}]}",
                            },
                        ],
                    }
                ],
            )

            import json
            import re

            response_text = response.content[0].text

            try:
                extraction = json.loads(response_text)
            except json.JSONDecodeError:
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                extraction = json.loads(json_match.group(0)) if json_match else {"text": response_text}

            return {"status": "success", "extraction": extraction}

        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            return {"status": "error"}

    # ========== GOOGLE CLOUD VISION (BACKUP) ==========

    async def detect_with_google_vision(
        self,
        screenshot_bytes: bytes,
        features: List[str] = ["TEXT_DETECTION", "LABEL_DETECTION", "OBJECT_LOCALIZATION"],
    ) -> Dict[str, Any]:
        """
        Google Cloud Vision API como backup/complemento.

        features: TEXT_DETECTION, LABEL_DETECTION, OBJECT_LOCALIZATION, etc
        """

        if not self.google_api_key:
            logger.warning("Google Vision API key not configured")
            return {"status": "error", "message": "Google Vision API key not configured"}

        logger.info(f"Detecting with Google Vision: {features}")

        screenshot_b64 = base64.standard_b64encode(screenshot_bytes).decode("utf-8")

        try:
            payload = {
                "requests": [
                    {
                        "image": {"content": screenshot_b64},
                        "features": [{"type": feature} for feature in features],
                    }
                ]
            }

            response = await self.http_client.post(
                f"https://vision.googleapis.com/v1/images:annotate?key={self.google_api_key}",
                json=payload,
            )

            if response.status_code == 200:
                return {
                    "status": "success",
                    "detection": response.json(),
                }
            else:
                return {"status": "error", "code": response.status_code}

        except Exception as e:
            logger.error(f"Google Vision detection failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    # ========== INTELLIGENT ACTION SUGGESTION ==========

    async def suggest_next_action(
        self,
        screenshot_bytes: bytes,
        goal: str,
    ) -> Dict[str, Any]:
        """
        Computer Vision lee interfaz + entiende objetivo → sugiere qué hacer.

        goal: "crear carrusel de producto", "generar reel", "crear contenido TikTok"
        """

        logger.info(f"Suggesting action for goal: {goal}")

        screenshot_b64 = base64.standard_b64encode(screenshot_bytes).decode("utf-8")

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
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
                                "text": f"""Veo esta interfaz FeedIA. Mi objetivo es: "{goal}"

¿Cuál es el siguiente paso EXACTO que debo hacer?

Considera:
1. Dónde estoy actualmente en el flujo
2. Qué botón/campo debo interactuar
3. Qué dato debo ingresar
4. Cuál es el selector CSS o posición
5. Alternativas si el elemento no existe

Responde en JSON: {{
  "current_step": "...",
  "next_action": "...",
  "target": {{"selector": "...", "type": "button/input/dropdown"}},
  "input_data": "...",
  "error_handling": "...",
  "success_indicator": "...",
  "confidence": 0.95
}}""",
                            },
                        ],
                    }
                ],
            )

            import json
            import re

            response_text = response.content[0].text

            try:
                suggestion = json.loads(response_text)
            except json.JSONDecodeError:
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                suggestion = json.loads(json_match.group(0)) if json_match else {"recommendation": response_text}

            return {"status": "success", "suggestion": suggestion}

        except Exception as e:
            logger.error(f"Action suggestion failed: {str(e)}")
            return {"status": "error"}

    # ========== VERIFY COMPLETION ==========

    async def verify_task_completion(
        self,
        screenshot_bytes: bytes,
        expected_result: str,
    ) -> Dict[str, Any]:
        """
        Verifica si tarea se completó exitosamente.

        expected_result: "carrusel creado", "contenido publicado", "post en schedule"
        """

        logger.info(f"Verifying task completion: {expected_result}")

        screenshot_b64 = base64.standard_b64encode(screenshot_bytes).decode("utf-8")

        try:
            response = self.anthropic_client.messages.create(
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
                                "text": f"""¿Se completó exitosamente: "{expected_result}"?

Analiza la pantalla y responde:
- ¿Veo confirmación de éxito? (success message, redirect, etc)
- ¿Hay errores visibles?
- ¿Qué cambió en la interfaz?

Responde en JSON: {{
  "completed": true/false,
  "success_indicators": ["..."],
  "errors": ["..."],
  "confidence": 0.95
}}""",
                            },
                        ],
                    }
                ],
            )

            import json
            import re

            response_text = response.content[0].text

            try:
                verification = json.loads(response_text)
            except json.JSONDecodeError:
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                verification = json.loads(json_match.group(0)) if json_match else {"result": response_text}

            return {"status": "success", "verification": verification}

        except Exception as e:
            logger.error(f"Task verification failed: {str(e)}")
            return {"status": "error"}

    async def close(self):
        """Cierra conexión HTTP."""
        await self.http_client.aclose()
