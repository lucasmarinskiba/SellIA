"""Ollama Local Vision Provider for Computer Use.

Usa modelos locales via Ollama (llava, bakllava, moondream, etc.)
para computer use sin dependencia de APIs cloud.

Nota: Los modelos locales de visión son generalmente menos precisos
para coordenadas de click que GPT-4o o Claude. Este provider está
diseñado para tareas simples o como último fallback.

Requiere: Ollama corriendo localmente con un modelo de visión cargado.
"""

import json
import re
from typing import List, Dict, Any, Optional

from app.core.config import get_settings
from app.core.logger import get_logger
from app.domains.computer_use.schemas import ComputerUseAction
from app.domains.computer_use.prompts import COMPUTER_USE_SYSTEM_PROMPT, COMPUTER_USE_SUMMARY_PROMPT
from .base import ComputerUseProvider

logger = get_logger(__name__)

# Recommended vision models for Ollama
VISION_MODELS = [
    "llava",          # General vision
    "bakllava",       # Better performance
    "moondream",      # Small and fast
    "llava-phi3",     # Good balance
]


class OllamaVisionProvider(ComputerUseProvider):
    """Provider de visión usando Ollama local.

    Envía screenshots a Ollama y espera respuestas JSON con acciones.
    """

    provider_name = "ollama"
    supports_vision = True

    def __init__(self, base_url: str = None, model: str = "llava"):
        self.base_url = (base_url or get_settings().OLLAMA_BASE_URL).rstrip("/")
        self.model = model
        self.settings = get_settings()

    async def _call_ollama(
        self,
        prompt: str,
        image_base64: str,
    ) -> Optional[str]:
        """Llama a Ollama /api/generate con imagen."""
        try:
            import aiohttp

            payload = {
                "model": self.model,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 800,
                },
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(f"Ollama returned {resp.status}: {text}")
                        return None
                    data = await resp.json()

            return data.get("response", "")

        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            return None

    def _parse_action(self, text: str) -> ComputerUseAction:
        """Parsea acción desde respuesta de Ollama."""
        text = text.strip()

        # Try direct JSON
        try:
            data = json.loads(text)
            return self._normalize_action(data)
        except json.JSONDecodeError:
            pass

        # Try JSON from markdown
        for pattern in [r"```json\s*(.*?)\s*```", r"```\s*(.*?)\s*```"]:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1).strip())
                    return self._normalize_action(data)
                except json.JSONDecodeError:
                    pass

        # Try finding JSON between braces
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            data = json.loads(text[start:end])
            return self._normalize_action(data)
        except (ValueError, json.JSONDecodeError):
            pass

        # Ollama sometimes returns text responses - try to infer action
        text_lower = text.lower()
        if "click" in text_lower and "coordinate" in text_lower:
            # Try to extract coordinates
            coord_match = re.search(r"coordinate.*?\[(\d+)[,\s]+(\d+)\]", text_lower)
            if coord_match:
                return ComputerUseAction(
                    action_type="click",
                    params={"x": int(coord_match.group(1)), "y": int(coord_match.group(2))},
                    reason=text[:200],
                )

        if re.search(r"\bdone\b", text_lower) or re.search(r"\bcomplete\b", text_lower):
            return ComputerUseAction(
                action_type="done",
                params={"summary": text[:500]},
                reason="Ollama indicated completion",
            )

        logger.warning(f"Could not parse Ollama response: {text[:200]}")
        return ComputerUseAction(
            action_type="error",
            params={"message": f"Ollama response not parseable: {text[:500]}"},
            reason="Parse error",
        )

    def _normalize_action(self, data: dict) -> ComputerUseAction:
        """Normaliza acción al formato interno."""
        action_type = data.get("action_type", data.get("action", "error"))
        params = data.get("params", data.get("input", {}))
        reason = data.get("reason", data.get("thought", ""))

        type_map = {
            "left_click": "click",
            "left-click": "click",
            "mouse_click": "click",
            "keypress": "type",
            "keys": "type",
            "goto": "navigate",
            "open": "navigate",
            "sleep": "wait",
            "finish": "done",
            "complete": "done",
        }
        action_type = type_map.get(action_type, action_type)

        return ComputerUseAction(action_type=action_type, params=params, reason=reason or f"Ollama {action_type}")

    async def decide_action(
        self,
        screenshot_bytes: bytes,
        task: str,
        history: List[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        page_info: Optional[Dict[str, str]] = None,
    ) -> ComputerUseAction:
        if history is None:
            history = []

        screenshot_base64 = self._encode_image(screenshot_bytes)

        # Build prompt
        history_text = ""
        if history:
            history_text = "\n".join(
                f"Step {i+1}: {h.get('action_type', 'unknown')}"
                for i, h in enumerate(history[-3:])  # Shorter history for local models
            )

        page_context = ""
        if page_info:
            page_context = f"URL: {page_info.get('url', '')}\nTitle: {page_info.get('title', '')}"
            if page_info.get("elements_text"):
                page_context += "\n" + page_info["elements_text"]
            if page_info.get("skill_brief"):
                page_context += "\n" + page_info["skill_brief"]

        prompt = f"""{COMPUTER_USE_SYSTEM_PROMPT}

Task: {task}

Previous actions:
{history_text or "None yet"}
{page_context}

IMPORTANT: Respond ONLY with a single JSON object in this exact format:
{{"action_type": "click|type|scroll|navigate|wait|screenshot|done|error", "params": {{...}}, "reason": "why"}}

For click: {{"action_type": "click", "params": {{"x": 120, "y": 340}}, "reason": "Clicking button"}}
For type: {{"action_type": "type", "params": {{"text": "hello"}}, "reason": "Entering text"}}
For done: {{"action_type": "done", "params": {{"summary": "Task completed"}}, "reason": "Finished"}}
"""
        if user_message:
            prompt += f"\nUser feedback: {user_message}\n"

        response = await self._call_ollama(prompt, screenshot_base64)

        if not response:
            return ComputerUseAction(
                action_type="error",
                params={"message": "Ollama did not return a response"},
                reason="Ollama offline or model not loaded",
            )

        return self._parse_action(response)

    async def generate_summary(self, actions_log: List[Dict[str, Any]]) -> str:
        actions_text = "\n".join(
            f"Step {a.get('step_number', i+1)}: {a.get('action_type')}"
            for i, a in enumerate(actions_log)
        )
        prompt = f"""{COMPUTER_USE_SUMMARY_PROMPT}

Actions:
{actions_text}

Provide a 2-sentence summary."""

        response = await self._call_ollama(prompt, "")  # No image needed for summary
        return response or "Sesión completada."
