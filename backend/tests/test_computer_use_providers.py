"""Tests para Computer Use Providers.

Testea la creación, fallback y parseo de acciones de cada provider.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.domains.computer_use.schemas import ComputerUseAction
from app.domains.computer_use.providers.base import ComputerUseProvider
from app.domains.computer_use.providers.openai_vision import OpenAIVisionProvider
from app.domains.computer_use.providers.factory import (
    create_provider,
    create_provider_with_fallback,
    FallbackComputerUseProvider,
    _is_ollama_available,
)


class FakeProvider(ComputerUseProvider):
    """Provider fake para tests."""
    provider_name = "fake"

    def __init__(self, name="fake"):
        self.provider_name = name

    async def decide_action(self, screenshot_bytes, task, history=None, user_message=None, page_info=None):
        return ComputerUseAction(action_type="click", params={"x": 100, "y": 200}, reason="test")

    async def generate_summary(self, actions_log):
        return "Summary"


# ========== OpenAI Provider ==========

@pytest.mark.asyncio
async def test_openai_provider_parse_action():
    """Test: parseo de acciones JSON de OpenAI."""
    provider = OpenAIVisionProvider(api_key="test")

    # Direct JSON
    action = provider._parse_action('{"action_type": "click", "params": {"x": 120, "y": 340}, "reason": "test"}')
    assert action.action_type == "click"
    assert action.params["x"] == 120

    # Markdown block
    action = provider._parse_action('```json\n{"action_type": "type", "params": {"text": "hello"}}\n```')
    assert action.action_type == "type"

    # Alternative names mapping
    action = provider._parse_action('{"action_type": "left_click", "params": {"x": 1, "y": 2}}')
    assert action.action_type == "click"

    action = provider._parse_action('{"action_type": "goto", "params": {"url": "https://x.com"}}')
    assert action.action_type == "navigate"


@pytest.mark.asyncio
async def test_openai_provider_parse_error():
    """Test: fallback a error cuando no se puede parsear."""
    provider = OpenAIVisionProvider(api_key="test")
    action = provider._parse_action("not json at all")
    assert action.action_type == "error"
    assert "not parseable" in action.params["message"].lower() or "parse" in action.params["message"].lower()


# ========== Factory ==========

@pytest.mark.asyncio
async def test_create_provider_openai():
    """Test: crear provider OpenAI."""
    provider = create_provider("openai", api_key="sk-test")
    assert provider is not None
    assert provider.provider_name == "openai"


@pytest.mark.asyncio
async def test_create_provider_ollama():
    """Test: crear provider Ollama."""
    provider = create_provider("ollama")
    assert provider is not None
    assert provider.provider_name == "ollama"


@pytest.mark.asyncio
async def test_create_provider_unknown():
    """Test: provider desconocido devuelve None."""
    provider = create_provider("unknown")
    assert provider is None


@pytest.mark.asyncio
async def test_create_provider_no_key():
    """Test: crear provider sin API key devuelve None."""
    with patch("app.domains.computer_use.providers.factory.get_settings") as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.OPENAI_API_KEY = ""
        mock_settings.ANTHROPIC_API_KEY = ""
        mock_get_settings.return_value = mock_settings
        provider = create_provider("openai", api_key=None)
        assert provider is None


@pytest.mark.asyncio
async def test_fallback_provider():
    """Test: FallbackComputerUseProvider intenta múltiples providers."""
    p1 = FakeProvider("p1")
    p2 = FakeProvider("p2")

    fallback = FallbackComputerUseProvider([p1, p2])
    result = await fallback.decide_action(b"", "task")

    assert result.action_type == "click"


@pytest.mark.asyncio
async def test_fallback_provider_all_fail():
    """Test: FallbackComputerUseProvider cuando todos fallan."""

    class FailingProvider(ComputerUseProvider):
        provider_name = "failing"

        async def decide_action(self, *args, **kwargs):
            raise Exception("fail")

        async def generate_summary(self, *args, **kwargs):
            return ""

    fallback = FallbackComputerUseProvider([FailingProvider(), FailingProvider()])
    result = await fallback.decide_action(b"", "task")

    assert result.action_type == "error"
    assert "All providers failed" in result.params["message"]


# ========== Anthropic Native Provider ==========

@pytest.mark.asyncio
async def test_anthropic_native_parse_tool_use():
    """Test: parseo de tool_use blocks de Anthropic."""
    from app.domains.computer_use.providers.anthropic_native import AnthropicNativeProvider

    provider = AnthropicNativeProvider(api_key="test")

    # Screenshot action
    result = provider._parse_tool_use([{
        "type": "tool_use",
        "name": "computer",
        "input": {"action": "screenshot"},
    }])
    assert result.action_type == "screenshot"

    # Left click
    result = provider._parse_tool_use([{
        "type": "tool_use",
        "name": "computer",
        "input": {"action": "left_click", "coordinate": [120, 340]},
    }])
    assert result.action_type == "click"
    assert result.params["x"] == 120
    assert result.params["y"] == 340

    # Type
    result = provider._parse_tool_use([{
        "type": "tool_use",
        "name": "computer",
        "input": {"action": "type", "text": "hello"},
    }])
    assert result.action_type == "type"
    assert result.params["text"] == "hello"

    # Scroll
    result = provider._parse_tool_use([{
        "type": "tool_use",
        "name": "computer",
        "input": {"action": "scroll", "coordinate": [100, 100], "scroll_amount": 3},
    }])
    assert result.action_type == "scroll"
    assert result.params["direction"] == "down"

    # Wait
    result = provider._parse_tool_use([{
        "type": "tool_use",
        "name": "computer",
        "input": {"action": "wait", "duration": 5},
    }])
    assert result.action_type == "wait"
    assert result.params["seconds"] == 5

    # Done (text response)
    result = provider._parse_tool_use([{
        "type": "text",
        "text": "I have completed the task. The banner is ready.",
    }])
    assert result.action_type == "done"


# ========== Ollama Provider ==========

@pytest.mark.asyncio
async def test_ollama_provider_parse_action():
    """Test: parseo de respuestas de Ollama."""
    from app.domains.computer_use.providers.ollama_vision import OllamaVisionProvider

    provider = OllamaVisionProvider()

    # Direct JSON
    action = provider._parse_action('{"action_type": "click", "params": {"x": 50, "y": 100}}')
    assert action.action_type == "click"

    # Alternative format
    action = provider._parse_action('{"action": "navigate", "input": {"url": "https://google.com"}}')
    assert action.action_type == "navigate"

    # Done inference
    action = provider._parse_action("The task is done and complete.")
    assert action.action_type == "done"

    # Error fallback
    action = provider._parse_action("random text without json or anything")
    assert action.action_type == "error"
