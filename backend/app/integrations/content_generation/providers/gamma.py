"""Gamma Provider — AI Docs & Presentations

Pricing: Plan-based, ~$0.05/doc
Strengths: Interactive docs, landing pages, guides, presentations
"""

from typing import Dict, Any

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType

settings = get_settings()


class GammaProvider(BaseProvider):
    """Proveedor de docs/presentaciones usando Gamma API."""

    name = "Gamma"
    slug = "gamma"
    supports = [ContentType.COPY]

    @property
    def is_available(self) -> bool:
        return bool(settings.GAMMA_API_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        return 0.05

    def get_pricing_table(self) -> Dict[str, float]:
        return {"gamma-doc": 0.05}

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(success=False, error_message="GAMMA_API_KEY no configurada")

        try:
            import aiohttp

            headers = {
                "Authorization": f"Bearer {settings.GAMMA_API_KEY}",
                "Content-Type": "application/json",
            }

            payload = {
                "topic": config.prompt,
                "type": config.extra_params.get("doc_type", "presentation"),
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.gamma.app/v1/documents",
                    headers=headers,
                    json=payload,
                ) as resp:
                    data = await resp.json()

            doc_url = data.get("url") or data.get("document", {}).get("url")
            if not doc_url:
                return GenerationResult(success=False, error_message="Gamma no devolvió documento")

            return GenerationResult(
                success=True,
                url=doc_url,
                cost_usd=0.05,
                model_used="gamma-ai",
                quality_tier=config.quality,
                metadata={},
            )

        except Exception as e:
            return GenerationResult(success=False, error_message=str(e))
