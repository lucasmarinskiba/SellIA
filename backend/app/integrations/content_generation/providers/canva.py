"""Canva Provider — Design Templates & AI Graphics

Pricing: Free tier available, Pro ~$12.99/mo
Strengths: Templates, brand kits, social graphics, quick designs
"""

from typing import Dict, Any

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType

settings = get_settings()


class CanvaProvider(BaseProvider):
    """Proveedor de diseño gráfico usando Canva API."""

    name = "Canva AI"
    slug = "canva"
    supports = [ContentType.IMAGE]

    @property
    def is_available(self) -> bool:
        return bool(settings.CANVA_API_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        return 0.0  # Free tier or plan-based

    def get_pricing_table(self) -> Dict[str, float]:
        return {"canva-design": 0.0}

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(success=False, error_message="CANVA_API_KEY no configurada")

        try:
            import aiohttp

            headers = {
                "Authorization": f"Bearer {settings.CANVA_API_KEY}",
                "Content-Type": "application/json",
            }

            payload = {
                "query": config.prompt,
                "type": config.extra_params.get("design_type", "social_media"),
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.canva.com/rest/v1/designs",
                    headers=headers,
                    json=payload,
                ) as resp:
                    data = await resp.json()

            design_url = data.get("design", {}).get("url") if isinstance(data.get("design"), dict) else data.get("url")
            if not design_url:
                return GenerationResult(success=False, error_message="Canva no devolvió diseño")

            return GenerationResult(
                success=True,
                url=design_url,
                cost_usd=0.0,
                model_used="canva-ai",
                quality_tier=config.quality,
                metadata={},
            )

        except Exception as e:
            return GenerationResult(success=False, error_message=str(e))
