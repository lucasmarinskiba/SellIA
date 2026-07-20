"""Anthropic Claude Native Computer Use Provider.

Usa la API nativa de Anthropic para computer use (beta).
Esta API es especial porque Claude devuelve acciones estructuradas
como tool_use blocks con coordenadas precisas, diseñadas
específicamente para controlar un navegador.

Requiere: pip install anthropic
API: https://docs.anthropic.com/en/docs/build-with-claude/computer-use
"""

import json
from typing import List, Dict, Any, Optional

from app.core.config import get_settings
from app.core.logger import get_logger
from app.domains.computer_use.schemas import ComputerUseAction
from app.domains.computer_use.prompts import COMPUTER_USE_SUMMARY_PROMPT
from .base import ComputerUseProvider

logger = get_logger(__name__)

# Tool definition for Anthropic Computer Use API
COMPUTER_TOOL_DEFINITION = {
    "type": "computer_20241022",
    "name": "computer",
    "display_width_px": 1280,
    "display_height_px": 720,
    "display_number": 1,
}


class AnthropicNativeProvider(ComputerUseProvider):
    """Provider nativo de Anthropic Computer Use.

    Usa la API directa de Anthropic (no LangChain) con el tool
    computer_20241022 para acciones de navegador nativas.
    """

    provider_name = "anthropic_native"
    supports_vision = True

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.model = model
        self.settings = get_settings()
        self._client = None

    def _get_client(self):
        """Lazy import y creación del cliente Anthropic."""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                logger.error("anthropic package not installed. Run: pip install anthropic")
                raise
        return self._client

    def _build_messages(
        self,
        screenshot_base64: str,
        task: str,
        history: List[Dict[str, Any]],
        user_message: Optional[str],
        page_info: Optional[Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        """Construye mensajes en formato nativo de Anthropic."""
        # Build context
        history_text = ""
        if history:
            history_text = "\n".join(
                f"Step {i+1}: {h.get('action_type', 'unknown')} — {h.get('reason', '')}"
                for i, h in enumerate(history[-5:])
            )

        page_context = ""
        if page_info:
            page_context = f"Current URL: {page_info.get('url', 'unknown')}\nCurrent Title: {page_info.get('title', 'unknown')}"
            if page_info.get("elements_text"):
                page_context += "\n" + page_info["elements_text"]
            if page_info.get("skill_brief"):
                page_context += "\n" + page_info["skill_brief"]

        content = f"""Task: {task}

Previous actions:
{history_text or "None yet"}
{page_context}
"""
        if user_message:
            content += f"\nUser feedback: {user_message}\n"

        messages = []

        # If there's history, add it as previous turns
        # For simplicity, we keep a single-turn approach with history in context
        # The Anthropic API handles multi-turn with tool_use/tool_result
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": content},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": screenshot_base64,
                    },
                },
            ],
        })

        return messages

    def _parse_tool_use(self, content_blocks: List[Dict[str, Any]]) -> ComputerUseAction:
        """Parsea tool_use blocks de Anthropic a ComputerUseAction."""
        for block in content_blocks:
            if block.get("type") == "tool_use" and block.get("name") == "computer":
                input_data = block.get("input", {})
                action = input_data.get("action", "error")
                params = {}
                reason = f"Anthropic computer action: {action}"

                # Map Anthropic actions to internal format
                if action == "screenshot":
                    return ComputerUseAction(action_type="screenshot", params={}, reason=reason)

                elif action in ("left_click", "click"):
                    coord = input_data.get("coordinate", [0, 0])
                    params = {"x": coord[0], "y": coord[1]}
                    return ComputerUseAction(action_type="click", params=params, reason=reason)

                elif action == "right_click":
                    coord = input_data.get("coordinate", [0, 0])
                    params = {"x": coord[0], "y": coord[1]}
                    return ComputerUseAction(action_type="right_click", params=params, reason=reason)

                elif action == "double_click":
                    coord = input_data.get("coordinate", [0, 0])
                    params = {"x": coord[0], "y": coord[1]}
                    return ComputerUseAction(action_type="double_click", params=params, reason=reason)

                elif action == "type":
                    params = {"text": input_data.get("text", "")}
                    return ComputerUseAction(action_type="type", params=params, reason=reason)

                elif action == "key":
                    # Map common keys
                    key_map = {
                        "Return": "Enter",
                        "Escape": "Escape",
                        "Tab": "Tab",
                        "BackSpace": "Backspace",
                    }
                    key = input_data.get("text", "")
                    mapped = key_map.get(key, key)
                    params = {"text": mapped}
                    return ComputerUseAction(action_type="type", params=params, reason=f"Key press: {mapped}")

                elif action == "scroll":
                    coord = input_data.get("coordinate", [0, 0])
                    scroll_amount = input_data.get("scroll_amount", 3)
                    direction = "down" if scroll_amount > 0 else "up"
                    params = {"direction": direction, "amount": abs(scroll_amount) * 100}
                    return ComputerUseAction(action_type="scroll", params=params, reason=reason)

                elif action == "wait":
                    params = {"seconds": input_data.get("duration", 2)}
                    return ComputerUseAction(action_type="wait", params=params, reason=reason)

                elif action == "cursor_position":
                    # Just take another screenshot
                    return ComputerUseAction(action_type="screenshot", params={}, reason="Checking cursor position")

            elif block.get("type") == "text":
                # Claude responded with text - might be done or error
                text = block.get("text", "")
                if "done" in text.lower() or "complete" in text.lower() or "finished" in text.lower():
                    return ComputerUseAction(
                        action_type="done",
                        params={"summary": text[:500]},
                        reason="Claude indicated task completion",
                    )

        # No tool use found - treat as done if it looks like completion
        text_content = " ".join(
            block.get("text", "") for block in content_blocks if block.get("type") == "text"
        )
        if text_content and len(text_content) > 10:
            return ComputerUseAction(
                action_type="done",
                params={"summary": text_content[:500]},
                reason="Claude response without tool use",
            )

        return ComputerUseAction(
            action_type="error",
            params={"message": "No valid tool_use block found in response"},
            reason="Invalid Anthropic response format",
        )

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

        try:
            client = self._get_client()
        except ImportError:
            return ComputerUseAction(
                action_type="error",
                params={"message": "anthropic package not installed"},
                reason="Missing dependency",
            )

        screenshot_base64 = self._encode_image(screenshot_bytes)
        messages = self._build_messages(screenshot_base64, task, history, user_message, page_info)

        try:
            response = await client.messages.create(
                model=self.model,
                max_tokens=4096,
                tools=[COMPUTER_TOOL_DEFINITION],
                messages=messages,
            )

            return self._parse_tool_use(response.content)

        except Exception as e:
            logger.error(f"Anthropic native API failed: {e}")
            # Fallback: try standard Anthropic via LangChain
            return await self._fallback_to_langchain(
                screenshot_bytes, task, history, user_message, page_info
            )

    async def _fallback_to_langchain(
        self,
        screenshot_bytes: bytes,
        task: str,
        history: List[Dict[str, Any]],
        user_message: Optional[str],
        page_info: Optional[Dict[str, str]],
    ) -> ComputerUseAction:
        """Fallback al provider OpenAI-style cuando la API nativa falla."""
        logger.warning("Falling back to LangChain Anthropic provider")
        from .openai_vision import OpenAIVisionProvider

        # Anthropic via LangChain uses similar format to OpenAI
        provider = OpenAIVisionProvider(api_key=self.api_key, model=self.model)
        # Override to use Anthropic model
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import SystemMessage, HumanMessage

        screenshot_base64 = self._encode_image(screenshot_bytes)

        from app.domains.computer_use.prompts import COMPUTER_USE_SYSTEM_PROMPT
        system_prompt = COMPUTER_USE_SYSTEM_PROMPT
        messages = [SystemMessage(content=system_prompt)]

        history_text = ""
        if history:
            history_text = "\n".join(
                f"Step {i+1}: {h.get('action_type', 'unknown')}"
                for i, h in enumerate(history[-5:])
            )

        page_context = ""
        if page_info:
            page_context = f"\nURL: {page_info.get('url', '')}\nTitle: {page_info.get('title', '')}"
            if page_info.get("elements_text"):
                page_context += "\n" + page_info["elements_text"]
            if page_info.get("skill_brief"):
                page_context += "\n" + page_info["skill_brief"]

        user_content = f"Task: {task}\n\nHistory:\n{history_text}{page_context}"
        if user_message:
            user_content += f"\nFeedback: {user_message}"

        human_msg = HumanMessage(
            content=[
                {"type": "text", "text": user_content},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": screenshot_base64,
                    },
                },
            ]
        )
        messages.append(human_msg)

        try:
            llm = ChatAnthropic(
                model=self.model,
                api_key=self.api_key,
                temperature=0.2,
                max_tokens=1500,
            )
            response = await llm.ainvoke(messages)
            return provider._parse_action(response.content)
        except Exception as e2:
            logger.error(f"Anthropic fallback also failed: {e2}")
            return ComputerUseAction(
                action_type="error",
                params={"message": f"Anthropic failed: {str(e2)[:200]}"},
                reason="Both native and fallback failed",
            )

    async def generate_summary(self, actions_log: List[Dict[str, Any]]) -> str:
        actions_text = "\n".join(
            f"Step {a.get('step_number', i+1)}: {a.get('action_type')} — {a.get('reason', '')}"
            for i, a in enumerate(actions_log)
        )
        prompt = COMPUTER_USE_SUMMARY_PROMPT.format(actions_log=actions_text)

        try:
            client = self._get_client()
            response = await client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            text_blocks = [b for b in response.content if b.type == "text"]
            return text_blocks[0].text if text_blocks else "Sesión completada."
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return "Sesión completada."
