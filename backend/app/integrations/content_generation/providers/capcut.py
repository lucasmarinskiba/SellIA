"""CapCut Provider — Video Editing & Templates

Pricing: Free tier available
Strengths: Auto-captions, effects, viral templates, mobile-first
"""

from typing import Dict, Any

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType

settings = get_settings()


class CapCutProvider(BaseProvider):
    """Proveedor de edición de video usando CapCut API."""

    name = "CapCut AI"
    slug = "capcut"
    supports = [ContentType.VIDEO]

    @property
    def is_available(self) -> bool:
        return bool(settings.CAPCUT_API_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        return 0.0

    def get_pricing_table(self) -> Dict[str, float]:
        return {"capcut-edit": 0.0}

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(success=False, error_message="CAPCUT_API_KEY no configurada")

        try:
            import aiohttp

            headers = {
                "Authorization": f"Bearer {settings.CAPCUT_API_KEY}",
                "Content-Type": "application/json",
            }

            payload = {
                "template": config.prompt,
                "media_urls": config.extra_params.get("media_urls", []),
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.capcut.com/v1/edits",
                    headers=headers,
                    json=payload,
                ) as resp:
                    data = await resp.json()

            video_url = data.get("video", {}).get("url") if isinstance(data.get("video"), dict) else data.get("url")
            if not video_url:
                return GenerationResult(success=False, error_message="CapCut no devolvió video")

            return GenerationResult(
                success=True,
                url=video_url,
                cost_usd=0.0,
                model_used="capcut-ai",
                quality_tier=config.quality,
                duration_seconds=config.duration_seconds,
                metadata={},
            )

        except Exception as e:
            return GenerationResult(success=False, error_message=str(e))
