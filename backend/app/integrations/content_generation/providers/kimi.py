"""Kimi (Moonshot AI) Provider — Ultra-low-cost Copy Generation

Pricing: $0.60/M input tokens, $2.50/M output tokens
Strengths: 256K context, Spanish-native, OpenAI-compatible API,
           automatic context caching (up to 75% savings)
"""

from typing import Dict, Any

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType

settings = get_settings()


class KimiProvider(BaseProvider):
    """Proveedor de copy usando Kimi (Moonshot AI) API."""

    name = "Kimi (Moonshot AI)"
    slug = "kimi"
    supports = [ContentType.COPY]

    @property
    def is_available(self) -> bool:
        return bool(settings.KIMI_API_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        """Estima costo basado en tokens del prompt (~$0.60/M input + $2.50/M output)."""
        # Heurística: ~150 tokens por cada 100 caracteres de prompt
        # Output estimado: 2x el tamaño del prompt en tokens
        prompt_chars = len(config.prompt)
        estimated_input_tokens = prompt_chars // 4
        estimated_output_tokens = estimated_input_tokens * 2
        cost = (estimated_input_tokens * 0.60 + estimated_output_tokens * 2.50) / 1_000_000
        return max(cost, 0.0001)

    def get_pricing_table(self) -> Dict[str, float]:
        return {
            "input_tokens_per_1m": 0.60,
            "output_tokens_per_1m": 2.50,
            "cached_input_tokens_per_1m": 0.10,
        }

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(
                success=False,
                error_message="KIMI_API_KEY no configurada. Obtén una en https://platform.moonshot.cn/",
            )

        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage, SystemMessage

            model = config.extra_params.get("model", "kimi-k2-5")
            temperature = config.extra_params.get("temperature", 0.7)
            max_tokens = config.extra_params.get("max_tokens", 1500)
            system_prompt = config.extra_params.get("system_prompt", "")

            llm = ChatOpenAI(
                model=model,
                api_key=settings.KIMI_API_KEY,
                base_url="https://api.moonshot.cn/v1",
                temperature=temperature,
                max_tokens=max_tokens,
            )

            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=config.prompt))

            response = await llm.ainvoke(messages)
            text = response.content

            # Estimar costo real basado en usage si está disponible
            usage = response.usage_metadata if hasattr(response, "usage_metadata") else {}
            input_tokens = usage.get("input_tokens", len(config.prompt) // 4)
            output_tokens = usage.get("output_tokens", len(text) // 4)
            cost = (input_tokens * 0.60 + output_tokens * 2.50) / 1_000_000

            return GenerationResult(
                success=True,
                text_content=text,
                cost_usd=cost,
                model_used=model,
                quality_tier=config.quality,
                metadata={
                    "provider": "kimi",
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "temperature": temperature,
                },
            )

        except Exception as e:
            return GenerationResult(success=False, error_message=str(e))
