"""Writesonic Provider — SEO + Ads + Blog Copy

Pricing: ~$0.008/generation
Strengths: SEO optimization, ad scoring, landing pages, blog posts
"""

from typing import Dict, Any

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType

settings = get_settings()


class WritesonicProvider(BaseProvider):
    """Proveedor de copy SEO usando Writesonic API."""

    name = "Writesonic"
    slug = "writesonic"
    supports = [ContentType.COPY]

    @property
    def is_available(self) -> bool:
        return bool(settings.WRITESONIC_API_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        return 0.008

    def get_pricing_table(self) -> Dict[str, float]:
        return {"writesonic-generation": 0.008}

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(success=False, error_message="WRITESONIC_API_KEY no configurada")

        try:
            import aiohttp

            headers = {
                "Authorization": f"Bearer {settings.WRITESONIC_API_KEY}",
                "Content-Type": "application/json",
            }

            payload = {
                "prompt": config.prompt,
                "language": config.extra_params.get("language", "es"),
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.writesonic.com/v1/business/content/chat-generate",
                    headers=headers,
                    json=payload,
                ) as resp:
                    data = await resp.json()

            text = data.get("message")
            if not text:
                return GenerationResult(success=False, error_message="Writesonic no devolvió texto")

            return GenerationResult(
                success=True,
                text_content=text,
                cost_usd=0.008,
                model_used="writesonic-gpt4",
                quality_tier=config.quality,
                metadata={},
            )

        except Exception as e:
            return GenerationResult(success=False, error_message=str(e))
