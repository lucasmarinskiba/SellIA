"""One async Claude call that returns a JSON object, or None.

Harvey proper shells out to the operator's Claude/Codex CLI (a personal
subscription). A multi-tenant service can't do that, so this uses SellIA's
Anthropic API key. A missing key or a failed call returns None; callers decide
the fallback (drafting is skipped, never faked).
"""

from __future__ import annotations

import json
import os
from typing import Any

from app.core.logger import get_logger

logger = get_logger(__name__)

_MODEL = os.getenv("HARVEY_MODEL", "claude-sonnet-5-5")
_TIMEOUT = 90
_KEY_ENV_NAMES = ("ANTHROPIC_API_KEY", "CLAUDE_API_KEY", "ANTHROPIC_KEY")


def _api_key() -> str | None:
    try:
        from app.core.config import get_settings

        key = getattr(get_settings(), "ANTHROPIC_API_KEY", None)
        if key:
            return key
    except Exception:
        pass
    for name in _KEY_ENV_NAMES:
        if os.environ.get(name):
            return os.environ[name]
    return None


def llm_available() -> bool:
    return _api_key() is not None


def parse_json_object(text: str) -> dict[str, Any] | None:
    start, end = text.find("{"), text.rfind("}") + 1
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start:end])
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


async def ask_json(system: str, prompt: str, *, max_tokens: int = 900) -> dict[str, Any] | None:
    key = _api_key()
    if not key:
        logger.warning("harvey: no Anthropic API key configured; skipping model call")
        return None
    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=key)
        msg = await client.messages.create(
            model=_MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            timeout=_TIMEOUT,
        )
        text = next((b.text for b in msg.content if getattr(b, "type", None) == "text"), "")
        return parse_json_object(text)
    except Exception as e:
        logger.warning("harvey: model call failed: %s", str(e)[:200])
        return None
