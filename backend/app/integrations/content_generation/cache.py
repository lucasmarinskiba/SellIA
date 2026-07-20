"""Redis-based caching for content generation.

Estrategia de caché:
1. Prompt cache: Cachea los prompts generados por el LLM para evitar
   re-generarlos (ahorro de tokens GPT-4o-mini).
2. Result cache: Cachea resultados de generación por hash de prompt.
   Si alguien pide exactamente lo mismo, devolvemos el URL cacheado.
3. Image cache: Cachea URLs de imágenes generadas.

TTLs:
- Prompts: 7 días (poco cambian para el mismo producto)
- Results draft: 3 días (los previews cambian frecuentemente)
- Results standard: 14 días
- Results premium: 30 días (los assets premium se reutilizan)
"""

import hashlib
import json
from typing import Optional
from datetime import timedelta

import redis.asyncio as redis
from app.core.config import get_settings

settings = get_settings()

# TTLs por tier de calidad
TTL_MAP = {
    "draft": timedelta(days=3),
    "standard": timedelta(days=14),
    "premium": timedelta(days=30),
}

PROMPT_TTL = timedelta(days=7)


class ContentCache:
    """Cache manager para generación de contenido."""

    _instance = None
    _redis: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def _get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    def _hash_key(self, data: dict) -> str:
        """Genera un hash determinístico para una configuración."""
        canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]

    # ========== Prompt Cache ==========

    async def get_cached_prompt(
        self,
        catalog_item_id: str,
        content_type: str,
        purpose: str,
    ) -> Optional[str]:
        """Obtiene un prompt cacheado para un producto y propósito."""
        r = await self._get_redis()
        key = f"prompt:{catalog_item_id}:{content_type}:{purpose}"
        cached = await r.get(key)
        return cached

    async def cache_prompt(
        self,
        catalog_item_id: str,
        content_type: str,
        purpose: str,
        prompt: str,
    ):
        """Cachea un prompt generado."""
        r = await self._get_redis()
        key = f"prompt:{catalog_item_id}:{content_type}:{purpose}"
        await r.setex(key, int(PROMPT_TTL.total_seconds()), prompt)

    # ========== Result Cache ==========

    async def get_cached_result(
        self,
        provider: str,
        config: dict,
    ) -> Optional[dict]:
        """Obtiene resultado cacheado por hash de config."""
        r = await self._get_redis()
        config_hash = self._hash_key({"provider": provider, **config})
        key = f"result:{config_hash}"
        cached = await r.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def cache_result(
        self,
        provider: str,
        config: dict,
        result: dict,
        quality: str = "standard",
    ):
        """Cachea un resultado de generación."""
        r = await self._get_redis()
        config_hash = self._hash_key({"provider": provider, **config})
        key = f"result:{config_hash}"
        ttl = int(TTL_MAP.get(quality, TTL_MAP["standard"]).total_seconds())
        await r.setex(key, ttl, json.dumps(result, ensure_ascii=False))

    # ========== URL Cache ==========

    async def get_cached_url(self, url_hash: str) -> Optional[str]:
        """Obtiene URL cacheada de asset generado."""
        r = await self._get_redis()
        key = f"url:{url_hash}"
        return await r.get(key)

    async def cache_url(self, url_hash: str, url: str, ttl_days: int = 30):
        """Cachea URL de asset."""
        r = await self._get_redis()
        key = f"url:{url_hash}"
        await r.setex(key, ttl_days * 86400, url)

    # ========== Rate Limit / Budget Cache ==========

    async def get_daily_spend(self, business_id: str, provider: str) -> float:
        """Obtiene gasto diario de un negocio en un proveedor."""
        r = await self._get_redis()
        key = f"budget:{business_id}:{provider}:{self._today()}"
        val = await r.get(key)
        return float(val) if val else 0.0

    async def increment_spend(self, business_id: str, provider: str, amount: float):
        """Incrementa gasto diario."""
        r = await self._get_redis()
        key = f"budget:{business_id}:{provider}:{self._today()}"
        await r.incrbyfloat(key, amount)
        # TTL hasta fin de día
        await r.expire(key, 86400)

    async def get_daily_generations(self, business_id: str, content_type: str) -> int:
        """Obtiene cantidad de generaciones diarias por tipo."""
        r = await self._get_redis()
        key = f"gen_count:{business_id}:{content_type}:{self._today()}"
        val = await r.get(key)
        return int(val) if val else 0

    async def increment_generation(self, business_id: str, content_type: str):
        """Incrementa contador de generaciones diarias."""
        r = await self._get_redis()
        key = f"gen_count:{business_id}:{content_type}:{self._today()}"
        await r.incr(key)
        await r.expire(key, 86400)

    def _today(self) -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # ========== Bulk Operations ==========

    async def invalidate_for_business(self, business_id: str):
        """Invalida toda la caché de un negocio (útil para cambios de branding)."""
        r = await self._get_redis()
        # Buscar y eliminar keys por pattern
        cursor = 0
        patterns = [
            f"prompt:{business_id}:*",
            f"budget:{business_id}:*",
            f"gen_count:{business_id}:*",
        ]
        for pattern in patterns:
            while True:
                cursor, keys = await r.scan(cursor, match=pattern, count=100)
                if keys:
                    await r.delete(*keys)
                if cursor == 0:
                    break

    async def close(self):
        if self._redis:
            await self._redis.close()
            self._redis = None
