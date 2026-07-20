"""ElevenLabs Provider — AI Voice Generation

Pricing (2025-2026):
- Text-to-Speech: ~$0.10-0.30 / 1000 caracteres
- Voice Cloning: plan-based
- Sound Effects: ~$0.20 / generación

Usado para voiceovers en videos y audio para Reels/ads.
"""

from typing import Dict, Any, Optional

from app.core.config import get_settings
from ..base import BaseProvider, GenerationConfig, GenerationResult, ContentQuality, ContentType

settings = get_settings()

# Costos por 1000 caracteres
ELEVENLABS_COSTS = {
    "tts-standard": 0.10,
    "tts-premium": 0.30,
    "sound-effects": 0.20,
}

# Voces recomendadas por idioma/locale
DEFAULT_VOICES = {
    "es": "Xb7hH8MSUJpSbSDYk0k2",  # Spanish narrator
    "es-LA": "Xb7hH8MSUJpSbSDYk0k2",
    "en": "21m00Tcm4TlvDq8ikWAM",  # Rachel
    "en-US": "21m00Tcm4TlvDq8ikWAM",
    "pt": "z9fAn5pzNw8Sh8T0J8q1",  # Portuguese
}


class ElevenLabsProvider(BaseProvider):
    """Proveedor de audio/voz usando ElevenLabs API."""

    name = "ElevenLabs"
    slug = "elevenlabs"
    supports = [ContentType.AUDIO]

    @property
    def is_available(self) -> bool:
        return bool(settings.ELEVENLABS_API_KEY)

    def estimate_cost(self, config: GenerationConfig) -> float:
        text = config.prompt
        char_count = len(text)
        cost_per_1k = ELEVENLABS_COSTS["tts-premium"] if config.quality == ContentQuality.PREMIUM else ELEVENLABS_COSTS["tts-standard"]
        return (char_count / 1000) * cost_per_1k

    def get_pricing_table(self) -> Dict[str, float]:
        return ELEVENLABS_COSTS

    async def generate(self, config: GenerationConfig) -> GenerationResult:
        if not self.is_available:
            return GenerationResult(
                success=False,
                error_message="ELEVENLABS_API_KEY no configurada",
            )

        try:
            from elevenlabs import ElevenLabs

            client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)

            text = config.prompt
            language = config.extra_params.get("language", "es")
            voice_id = config.extra_params.get("voice_id", DEFAULT_VOICES.get(language, DEFAULT_VOICES["es"]))
            model = config.extra_params.get("model", "eleven_multilingual_v2")

            # Generar audio
            audio = client.generate(
                text=text,
                voice=voice_id,
                model=model,
            )

            # Convertir a bytes
            audio_bytes = b"".join(audio)

            # Subir a storage temporal (o devolver bytes)
            # Por ahora, devolvemos metadata
            cost = self.estimate_cost(config)

            return GenerationResult(
                success=True,
                local_path=audio_bytes,
                cost_usd=cost,
                model_used=model,
                quality_tier=config.quality,
                duration_seconds=None,  # Podríamos calcularlo del audio
                metadata={
                    "voice_id": voice_id,
                    "language": language,
                    "char_count": len(text),
                    "audio_size_bytes": len(audio_bytes),
                },
            )

        except Exception as e:
            return GenerationResult(
                success=False,
                error_message=str(e),
            )
