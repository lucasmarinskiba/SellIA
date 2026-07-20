"""Anthropic Computer Use client · agent loop with screenshot + tool actions.

Anthropic CUA spec:
  - Tools: computer · text_editor · bash
  - Model: claude-sonnet-4-5 with beta header `computer-use-2025-01-24`
  - Loop: send task + screenshot → receive tool_use → execute via Playwright → return tool_result → repeat

This client handles the brain side (Anthropic).
Playwright execution lives in app/agents/playwright_executor.py.
"""
import asyncio
import base64
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

from app.core.config import settings


logger = logging.getLogger(__name__)


COMPUTER_USE_BETA_HEADER = "computer-use-2025-01-24"
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"


@dataclass
class ToolAction:
    """One tool invocation from the model."""
    tool: str  # 'computer' | 'text_editor' | 'bash'
    action: str  # 'screenshot' | 'click' | 'type' | 'key' | 'scroll' | etc.
    params: dict[str, Any] = field(default_factory=dict)
    tool_use_id: str = ""


@dataclass
class ToolResult:
    """Response back to model after executing tool."""
    tool_use_id: str
    content: str | None = None
    image_base64: str | None = None  # screenshot base64
    is_error: bool = False


@dataclass
class CUASession:
    """Session state · model conversation + viewport."""
    messages: list[dict] = field(default_factory=list)
    viewport_width: int = 1280
    viewport_height: int = 800
    task: str = ""
    max_steps: int = 30
    current_step: int = 0
    finished: bool = False
    final_response: str = ""


ExecutorFn = Callable[[ToolAction], Awaitable[ToolResult]]


class CUAClient:
    """Drives Anthropic Computer Use loop.

    Caller provides an executor coroutine that runs ToolActions against a real browser/desktop.
    Returns when model emits text-only response or max_steps reached.
    """

    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY required for CUAClient")
        self.model = model

    async def run(
        self,
        task: str,
        executor: ExecutorFn,
        *,
        max_steps: int = 30,
        viewport: tuple[int, int] = (1280, 800),
        system_prompt: str | None = None,
    ) -> CUASession:
        """Run agent loop until completion or step limit."""
        try:
            from anthropic import AsyncAnthropic
        except ImportError as e:
            raise RuntimeError("anthropic SDK not installed") from e

        client = AsyncAnthropic(api_key=self.api_key)

        sess = CUASession(task=task, max_steps=max_steps, viewport_width=viewport[0], viewport_height=viewport[1])
        sess.messages = [{"role": "user", "content": task}]

        tools = self._tool_definitions(viewport)
        system = system_prompt or (
            "You are SellIA, an autonomous sales agent. "
            "Use the computer tool to navigate websites, fill forms, send messages, and close sales. "
            "Be precise. Confirm before destructive actions. "
            "When task is complete, respond with a final summary (no more tool calls)."
        )

        while sess.current_step < sess.max_steps and not sess.finished:
            sess.current_step += 1

            try:
                response = await client.beta.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=system,
                    tools=tools,
                    messages=sess.messages,
                    betas=[COMPUTER_USE_BETA_HEADER],
                )
            except Exception as e:
                logger.exception("anthropic_call_failed", extra={"step": sess.current_step, "error": str(e)})
                sess.final_response = f"Error calling Anthropic: {e}"
                break

            # Collect tool_use blocks · finish if only text
            tool_uses: list[ToolAction] = []
            assistant_blocks: list[dict] = []
            text_parts: list[str] = []

            for block in response.content:
                btype = getattr(block, "type", None)
                if btype == "tool_use":
                    tool_uses.append(ToolAction(
                        tool=block.name,
                        action=block.input.get("action", ""),
                        params={k: v for k, v in block.input.items() if k != "action"},
                        tool_use_id=block.id,
                    ))
                    assistant_blocks.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
                elif btype == "text":
                    text_parts.append(block.text)
                    assistant_blocks.append({"type": "text", "text": block.text})

            sess.messages.append({"role": "assistant", "content": assistant_blocks})

            if not tool_uses:
                # Model returned only text · task complete
                sess.finished = True
                sess.final_response = "\n".join(text_parts)
                logger.info("cua_session_complete", extra={"steps": sess.current_step, "final": sess.final_response[:120]})
                break

            # Execute every tool_use in parallel · gather results
            results = await asyncio.gather(
                *[executor(action) for action in tool_uses],
                return_exceptions=True,
            )

            user_content = []
            for action, result in zip(tool_uses, results):
                if isinstance(result, Exception):
                    user_content.append({
                        "type": "tool_result",
                        "tool_use_id": action.tool_use_id,
                        "content": f"Execution error: {result}",
                        "is_error": True,
                    })
                    continue

                content_blocks: list[dict] = []
                if result.content:
                    content_blocks.append({"type": "text", "text": result.content})
                if result.image_base64:
                    content_blocks.append({
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/png", "data": result.image_base64},
                    })

                user_content.append({
                    "type": "tool_result",
                    "tool_use_id": result.tool_use_id,
                    "content": content_blocks if content_blocks else "ok",
                    "is_error": result.is_error,
                })

            sess.messages.append({"role": "user", "content": user_content})

        if not sess.finished and sess.current_step >= sess.max_steps:
            logger.warning("cua_max_steps_reached", extra={"task": task[:80], "steps": sess.current_step})
            sess.final_response = f"Reached max steps ({max_steps}) without completion"

        return sess

    @staticmethod
    def _tool_definitions(viewport: tuple[int, int]) -> list[dict]:
        return [
            {
                "type": "computer_20250124",
                "name": "computer",
                "display_width_px": viewport[0],
                "display_height_px": viewport[1],
                "display_number": 1,
            },
            {"type": "text_editor_20250124", "name": "str_replace_editor"},
            {"type": "bash_20250124", "name": "bash"},
        ]


# ─── Stub executor for tests ────────────────────────────────────────────────


async def stub_executor(action: ToolAction) -> ToolResult:
    """No-op executor · returns blank screenshot for screenshots, "ok" otherwise. For tests."""
    logger.info("stub_executor", extra={"tool": action.tool, "action": action.action, "params": str(action.params)[:120]})
    if action.action == "screenshot":
        # 1x1 transparent PNG
        blank = base64.b64encode(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xfa\xcf\x00\x00\x00\x02\x00\x01\xe2!\xbc\x33\x00\x00\x00\x00IEND\xaeB`\x82"
        ).decode()
        return ToolResult(tool_use_id=action.tool_use_id, image_base64=blank, content="screenshot")
    return ToolResult(tool_use_id=action.tool_use_id, content="ok")
