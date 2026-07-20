"""Pika Labs Provider — Stylized AI Video

Pricing: ~$0.08/second
Strengths: Anime, effects, style transfer, creative video
"""

from typing import Dict, Any

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType

settings = get_settings()


class PikaProvider(BaseProvider):
    """Proveedor de video estilizado usando Pika Labs API."""

    name = "Pika Labs"
    slug = "pika"
    supports = [ContentType.VIDEO]

    @property
    def is_available(self) -> bool:
        return bool(settings.PIKA_API_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        duration = config.duration_seconds or 5
        return 0.08 * duration

    def get_pricing_table(self) -> Dict[str, float]:
        return {"pika-video": 0.08}

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(success=False, error_message="PIKA_API_KEY no configurada")

        try:
            import aiohttp

            headers = {"Authorization": f"Bearer {settings.PIKA_API_KEY}"}

            payload = {
                "prompt": config.prompt,
                "duration": min(config.duration_seconds or 5, 10),
            }

            if config.reference_image_url:
                payload["image"] = config.reference_image_url

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.pika.art/generate",
                    headers=headers,
                    json=payload,
                ) as resp:
                    data = await resp.json()

            video_url = data.get("video", {}).get("url") if isinstance(data.get("video"), dict) else data.get("url")
            if not video_url:
                return GenerationResult(success=False, error_message="Pika no devolvió video")

            duration = config.duration_seconds or 5
            return GenerationResult(
                success=True,
                url=video_url,
                cost_usd=self.estimate_cost(config),
                model_used="pika-1.5",
                quality_tier=config.quality,
                duration_seconds=duration,
                metadata={},
            )

        except Exception as e:
            return GenerationResult(success=False, error_message=str(e))
