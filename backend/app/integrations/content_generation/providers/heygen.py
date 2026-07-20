"""HeyGen Provider — AI Avatar Video Generation

Pricing: ~$2/min video
Strengths: Realistic avatars, multilingual, lip sync
"""

from typing import Dict, Any

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType

settings = get_settings()


class HeyGenProvider(BaseProvider):
    """Proveedor de video con avatares AI usando HeyGen API."""

    name = "HeyGen"
    slug = "heygen"
    supports = [ContentType.VIDEO]

    @property
    def is_available(self) -> bool:
        return bool(settings.HEYGEN_API_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        duration = config.duration_seconds or 30
        return (duration / 60) * 2.0  # ~$2/min

    def get_pricing_table(self) -> Dict[str, float]:
        return {"heygen-avatar": 2.0}  # per minute

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(success=False, error_message="HEYGEN_API_KEY no configurada")

        try:
            import aiohttp

            headers = {
                "X-Api-Key": settings.HEYGEN_API_KEY,
                "Content-Type": "application/json",
            }

            payload = {
                "video_inputs": [{
                    "character": {"type": "avatar", "avatar_id": "Daisy-inskirt-20220818"},
                    "voice": {"type": "text", "input_text": config.prompt, "voice_id": "2d5b0e6cf36f460aa7fc47e3eb5a4b66"},
                }],
                "dimension": {"width": 1080, "height": 1920},
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.heygen.com/v2/video/generate",
                    headers=headers,
                    json=payload,
                ) as resp:
                    data = await resp.json()

            video_id = data.get("data", {}).get("video_id")
            if not video_id:
                return GenerationResult(success=False, error_message="HeyGen no devolvió video_id")

            # Poll
            video_url = None
            for _ in range(40):
                import asyncio
                await asyncio.sleep(5)
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"https://api.heygen.com/v1/video_status.get?video_id={video_id}",
                        headers=headers,
                    ) as poll_resp:
                        poll_data = await poll_resp.json()
                        status = poll_data.get("data", {}).get("status")
                        if status == "completed":
                            video_url = poll_data.get("data", {}).get("video_url")
                            break

            if not video_url:
                return GenerationResult(success=False, error_message="HeyGen timeout")

            duration = config.duration_seconds or 30
            cost = self.estimate_cost(config)

            return GenerationResult(
                success=True,
                url=video_url,
                cost_usd=cost,
                model_used="heygen-avatar",
                quality_tier=config.quality,
                duration_seconds=duration,
                metadata={"video_id": video_id},
            )

        except Exception as e:
            return GenerationResult(success=False, error_message=str(e))
