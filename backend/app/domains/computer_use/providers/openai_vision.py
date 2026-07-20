"""OpenAI Vision Provider for Computer Use.

Usa GPT-4o / GPT-4.5 / GPT-4o-mini con visión para analizar screenshots
y devolver acciones en formato JSON.
"""

import json
import re
from typing import List, Dict, Any, Optional

from langchain_core.messages import SystemMessage, HumanMessage

from app.core.config import get_settings
from app.core.logger import get_logger
from app.domains.computer_use.schemas import ComputerUseAction
from app.domains.computer_use.prompts import COMPUTER_USE_SYSTEM_PROMPT, COMPUTER_USE_SUMMARY_PROMPT
from .base import ComputerUseProvider

logger = get_logger(__name__)


class OpenAIVisionProvider(ComputerUseProvider):
    """Provider de visión usando OpenAI GPT-4o."""

    provider_name = "openai"
    supports_vision = True

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.settings = get_settings()

    def _build_messages(
        self,
        screenshot_base64: str,
        task: str,
        history: List[Dict[str, Any]],
        user_message: Optional[str],
        page_info: Optional[Dict[str, str]],
    ) -> List:
        """Construye mensajes para GPT-4o con visión."""
        messages = [SystemMessage(content=COMPUTER_USE_SYSTEM_PROMPT)]

        history_text = ""
        if history:
            history_text = "\n".join(
                f"Step {i+1}: {h.get('action_type', 'unknown')} — {h.get('reason', '')}"
                for i, h in enumerate(history[-5:])
            )

        page_context = ""
        if page_info:
            page_context = f"\nCurrent URL: {page_info.get('url', 'unknown')}\nCurrent Title: {page_info.get('title', 'unknown')}"
            if page_info.get("elements_text"):
                page_context += "\n" + page_info["elements_text"]
            if page_info.get("skill_brief"):
                page_context += "\n" + page_info["skill_brief"]

        user_content = f"""Task: {task}

Previous actions:
{history_text or "None yet"}
{page_context}
"""
        if user_message:
            user_content += f"\nUser feedback: {user_message}\n"

        human_msg = HumanMessage(
            content=[
                {"type": "text", "text": user_content},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{screenshot_base64}",
                        "detail": "high",
                    },
                },
            ]
        )
        messages.append(human_msg)
        return messages

    def _parse_action(self, text: str) -> ComputerUseAction:
        """Parsea acción desde respuesta JSON del LLM."""
        text = text.strip()

        # Try direct JSON parse
        try:
            data = json.loads(text)
            return self._normalize_action(data)
        except json.JSONDecodeError:
            pass

        # Try JSON from markdown code block
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

        logger.warning(f"Could not parse action from OpenAI: {text[:200]}")
        return ComputerUseAction(
            action_type="error",
            params={"message": f"Could not parse: {text[:500]}"},
            reason="Parse error",
        )

    def _normalize_action(self, data: dict) -> ComputerUseAction:
        """Normaliza una acción al formato interno."""
        action_type = data.get("action_type", "error")
        params = data.get("params", {})
        reason = data.get("reason", "")

        # Map some common alternative names
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

        return ComputerUseAction(action_type=action_type, params=params, reason=reason)

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
        messages = self._build_messages(screenshot_base64, task, history, user_message, page_info)

        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=self.model,
                api_key=self.api_key,
                temperature=0.2,
                max_tokens=1500,
            )
            response = await llm.ainvoke(messages)
            return self._parse_action(response.content)
        except Exception as e:
            logger.error(f"OpenAI vision call failed: {e}")
            return ComputerUseAction(
                action_type="error",
                params={"message": str(e)[:200]},
                reason="OpenAI API error",
            )

    async def generate_summary(self, actions_log: List[Dict[str, Any]]) -> str:
        actions_text = "\n".join(
            f"Step {a.get('step_number', i+1)}: {a.get('action_type')} — {a.get('reason', '')}"
            for i, a in enumerate(actions_log)
        )
        prompt = COMPUTER_USE_SUMMARY_PROMPT.format(actions_log=actions_text)
        messages = [SystemMessage(content=prompt)]

        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=self.api_key,
                temperature=0.3,
                max_tokens=500,
            )
            response = await llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return "Sesión completada."
