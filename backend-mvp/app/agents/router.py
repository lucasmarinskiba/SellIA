"""AI Router · cascade local → cheap → premium based on task complexity.

Tier rules:
  - SIMPLE   · FAQ, classification, short replies (<200 tokens out)
              → Ollama llama3.3 (local · $0) · fallback Groq
  - MEDIUM   · listing optimization, copy gen, summaries (<1k out)
              → Groq llama3.3-70B · fallback Anthropic Haiku
  - COMPLEX  · multi-step reasoning, deals, legal, custom propos.
              → Anthropic Claude Sonnet 4.5
  - CUA      · Computer Use sessions
              → Anthropic Claude Sonnet 4.5 (only one supporting CUA)
"""
import enum
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)


class ModelTier(enum.Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    CUA = "cua"


@dataclass
class CompletionResult:
    text: str
    provider: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0


PRICING_PER_M_TOK = {
    "ollama:llama3.3":          (0.0, 0.0),
    "groq:llama-3.3-70b":       (0.59, 0.79),
    "anthropic:haiku-3.5":      (0.80, 4.00),
    "anthropic:sonnet-4.5":     (3.00, 15.00),
}


class AIRouter:
    """Pick provider · execute · track cost."""

    async def complete(
        self,
        prompt: str,
        *,
        tier: ModelTier = ModelTier.SIMPLE,
        system: str | None = None,
        max_tokens: int = 1024,
    ) -> CompletionResult:
        """Run completion against best-fit provider · auto-fallback on failure."""
        attempts = self._provider_order(tier)
        last_err: Exception | None = None

        for provider in attempts:
            try:
                return await self._call(provider, prompt, system, max_tokens)
            except Exception as e:
                logger.warning("ai_provider_failed", extra={"provider": provider, "error": str(e)})
                last_err = e
                continue

        raise RuntimeError(f"All AI providers failed: {last_err}")

    def _provider_order(self, tier: ModelTier) -> list[str]:
        match tier:
            case ModelTier.SIMPLE:   return ["ollama:llama3.3", "groq:llama-3.3-70b", "anthropic:haiku-3.5"]
            case ModelTier.MEDIUM:   return ["groq:llama-3.3-70b", "anthropic:haiku-3.5", "anthropic:sonnet-4.5"]
            case ModelTier.COMPLEX:  return ["anthropic:sonnet-4.5", "anthropic:haiku-3.5"]
            case ModelTier.CUA:      return ["anthropic:sonnet-4.5"]

    async def _call(self, provider: str, prompt: str, system: str | None, max_tokens: int) -> CompletionResult:
        if provider == "ollama:llama3.3":
            return await self._ollama(prompt, system, max_tokens)
        if provider == "groq:llama-3.3-70b":
            return await self._groq(prompt, system, max_tokens)
        if provider.startswith("anthropic:"):
            model_name = provider.split(":", 1)[1]
            return await self._anthropic(model_name, prompt, system, max_tokens)
        raise ValueError(f"Unknown provider: {provider}")

    async def _ollama(self, prompt: str, system: str | None, max_tokens: int) -> CompletionResult:
        async with httpx.AsyncClient(timeout=60.0) as c:
            r = await c.post(
                f"{settings.OLLAMA_URL}/api/generate",
                json={
                    "model": "llama3.3",
                    "prompt": prompt,
                    "system": system,
                    "stream": False,
                    "options": {"num_predict": max_tokens},
                },
            )
            r.raise_for_status()
            data = r.json()
        return CompletionResult(
            text=data.get("response", "").strip(),
            provider="ollama",
            model="llama3.3",
            tokens_in=data.get("prompt_eval_count", 0),
            tokens_out=data.get("eval_count", 0),
            cost_usd=0.0,
        )

    async def _groq(self, prompt: str, system: str | None, max_tokens: int) -> CompletionResult:
        api_key = getattr(settings, "GROQ_API_KEY", None)
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        async with httpx.AsyncClient(timeout=30.0) as c:
            r = await c.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile", "messages": messages, "max_tokens": max_tokens},
            )
            r.raise_for_status()
            data = r.json()
        usage = data.get("usage", {})
        ti, to_ = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
        cost_in, cost_out = PRICING_PER_M_TOK["groq:llama-3.3-70b"]
        return CompletionResult(
            text=data["choices"][0]["message"]["content"],
            provider="groq",
            model="llama-3.3-70b-versatile",
            tokens_in=ti,
            tokens_out=to_,
            cost_usd=(ti / 1_000_000) * cost_in + (to_ / 1_000_000) * cost_out,
        )

    async def _anthropic(self, model: str, prompt: str, system: str | None, max_tokens: int) -> CompletionResult:
        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        model_id = {
            "haiku-3.5":  "claude-haiku-3-5-20241022",
            "sonnet-4.5": "claude-sonnet-4-5-20250929",
        }.get(model, model)

        resp = await client.messages.create(
            model=model_id,
            max_tokens=max_tokens,
            system=system or "You are a helpful sales assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        ti = resp.usage.input_tokens
        to_ = resp.usage.output_tokens
        cost_in, cost_out = PRICING_PER_M_TOK.get(f"anthropic:{model}", (3.0, 15.0))
        return CompletionResult(
            text=resp.content[0].text,
            provider="anthropic",
            model=model_id,
            tokens_in=ti,
            tokens_out=to_,
            cost_usd=(ti / 1_000_000) * cost_in + (to_ / 1_000_000) * cost_out,
        )
