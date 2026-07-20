"""
Embedding Service for SellIA

Primary: Ollama (nomic-embed-text, 768-dim)
Fallback: OpenAI (text-embedding-3-small, 1536-dim -> projected to 768)

Embeddings are cached in Redis with TTL 24h.
"""

import hashlib
import json
from typing import Optional, List

import httpx
import redis.asyncio as redis

from app.core.config import get_settings
from app.core.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

OLLAMA_EMBED_MODEL = "nomic-embed-text"
OPENAI_EMBED_MODEL = "text-embedding-3-small"
REDIS_TTL_SECONDS = 86400  # 24h


class EmbeddingService:
    """Generates text embeddings with Ollama primary + OpenAI fallback."""

    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._http: Optional[httpx.AsyncClient] = None

    async def _get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )
        return self._redis

    async def _get_http(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
        return self._http

    @staticmethod
    def _cache_key(text: str) -> str:
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]
        return f"emb:{h}"

    async def _get_cached(self, text: str) -> Optional[List[float]]:
        r = await self._get_redis()
        key = self._cache_key(text)
        cached = await r.get(key)
        if cached is not None:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                return None
        return None

    async def _set_cached(self, text: str, embedding: List[float]) -> None:
        r = await self._get_redis()
        key = self._cache_key(text)
        await r.setex(key, REDIS_TTL_SECONDS, json.dumps(embedding))

    async def _embed_ollama(self, text: str) -> Optional[List[float]]:
        base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        http = await self._get_http()
        try:
            resp = await http.post(
                f"{base_url}/api/embeddings",
                json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
            )
            resp.raise_for_status()
            data = resp.json()
            embedding = data.get("embedding")
            if embedding and len(embedding) == 768:
                return embedding
            logger.warning(
                f"Ollama embedding unexpected dimension: {len(embedding) if embedding else 'none'}"
            )
            return None
        except Exception as e:
            logger.warning(f"Ollama embedding failed: {e}")
            return None

    async def _embed_openai(self, text: str) -> Optional[List[float]]:
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            logger.warning("OpenAI API key not configured for embeddings")
            return None
        http = await self._get_http()
        try:
            resp = await http.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": OPENAI_EMBED_MODEL, "input": text},
            )
            resp.raise_for_status()
            data = resp.json()
            embedding = data["data"][0]["embedding"]
            if len(embedding) == 1536:
                # Project 1536-dim OpenAI embedding down to 768-dim
                # by averaging adjacent pairs so it lives in the same space
                # as the primary nomic-embed-text cache.
                projected = [
                    (embedding[i] + embedding[i + 1]) / 2.0
                    for i in range(0, 1536, 2)
                ]
                return projected
            return embedding
        except Exception as e:
            logger.warning(f"OpenAI embedding failed: {e}")
            return None

    async def embed_text(self, text: str) -> List[float]:
        """Generate a 768-dim embedding for a single text."""
        cached = await self._get_cached(text)
        if cached is not None:
            return cached

        embedding = await self._embed_ollama(text)
        if embedding is not None:
            await self._set_cached(text, embedding)
            return embedding

        embedding = await self._embed_openai(text)
        if embedding is not None:
            await self._set_cached(text, embedding)
            return embedding

        raise RuntimeError("All embedding providers failed (Ollama and OpenAI)")

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        results: List[List[float]] = []
        for text in texts:
            results.append(await self.embed_text(text))
        return results

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
        if self._http is not None:
            await self._http.aclose()
            self._http = None


# Singleton instance
embedding_service = EmbeddingService()
