"""
Semantic Cache for LLM Responses (Vector-based v2)

Stores cached queries as embeddings in PostgreSQL with pgvector.
Matching uses cosine similarity for true semantic retrieval.

Typical savings: 30-50% on FAQ-style queries.

Two rules make it safe to turn on:

* **Per business.** An entry is only ever served to the business that produced it. The cache
  used to be global, so at similarity >= 0.92 one tenant's answer (built from its catalog,
  prices, policies) could be returned to another. Without a ``business_id`` nothing is read or
  stored.
* **Real TTL.** ``ttl_seconds`` was documented but never applied, so an answer lived forever.
  Lookups ignore entries older than the TTL and ``store`` deletes the expired ones.

It also degrades quietly: when no embedding provider is reachable (no Ollama, no OpenAI key)
the cache switches itself off for ``UNAVAILABLE_BACKOFF_SECONDS`` after one notice, instead of
trying Ollama/OpenAI and logging three warnings on every LLM call.
"""

import time
import uuid
from datetime import UTC, datetime, timedelta

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    delete,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import AsyncSessionLocal, Base
from app.core.embeddings import embedding_service
from app.core.logger import get_logger

logger = get_logger(__name__)

DEFAULT_THRESHOLD = 0.92
DEFAULT_TTL_SECONDS = 86400  # 24h
UNAVAILABLE_BACKOFF_SECONDS = (
    600  # 10 min without retrying embeddings after they all failed
)


class SemanticCacheEmbedding(Base):
    """PostgreSQL-backed semantic cache using pgvector."""

    __tablename__ = "semantic_cache_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    query_text = Column(Text, nullable=False)
    query_embedding = Column(Vector(768), nullable=False)
    response_text = Column(Text, nullable=False)
    model_used = Column(String(100), nullable=False, default="unknown")
    hit_count = Column(Integer, default=0, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    last_accessed = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )


class SemanticCache:
    """Vector-based semantic cache for LLM responses."""

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self.ttl = ttl_seconds
        self._unavailable_until = (
            0.0  # time.monotonic() deadline while embeddings are down
        )

    async def _embed(self, query: str) -> list[float] | None:
        """The query's embedding, or None when no provider can produce one (backs off)."""
        if time.monotonic() < self._unavailable_until:
            return None
        try:
            return await embedding_service.embed_text(query)
        # the cache must never break an LLM call
        except Exception as e:  # noqa: BLE001
            self._unavailable_until = time.monotonic() + UNAVAILABLE_BACKOFF_SECONDS
            logger.info(
                "Semantic cache paused for %ss: no embedding provider available (%s)",
                UNAVAILABLE_BACKOFF_SECONDS,
                str(e)[:100],
            )
            return None

    def _cutoff(self) -> datetime:
        return datetime.now(UTC) - timedelta(seconds=self.ttl)

    async def get_similar(
        self,
        query: str,
        business_id: uuid.UUID | None = None,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> str | None:
        """A semantically similar cached response of THIS business, not older than the TTL."""
        if business_id is None:
            return None
        embedding = await self._embed(query)
        if embedding is None:
            return None

        async with AsyncSessionLocal() as db:
            stmt = (
                select(
                    SemanticCacheEmbedding,
                    (
                        1
                        - SemanticCacheEmbedding.query_embedding.cosine_distance(
                            embedding
                        )
                    ).label("similarity"),
                )
                .where(
                    SemanticCacheEmbedding.business_id == business_id,
                    SemanticCacheEmbedding.created_at >= self._cutoff(),
                )
                .order_by(
                    SemanticCacheEmbedding.query_embedding.cosine_distance(embedding)
                )
                .limit(1)
            )
            result = await db.execute(stmt)
            row = result.first()

            if row is None:
                return None

            match, similarity = row
            if similarity is None:
                return None

            if similarity >= threshold:
                match.hit_count += 1
                match.last_accessed = datetime.now(UTC)
                await db.commit()
                logger.info(f"Semantic cache HIT (similarity={similarity:.3f})")
                return match.response_text

        return None

    async def store(
        self,
        query: str,
        response: str,
        model_used: str = "unknown",
        business_id: uuid.UUID | None = None,
    ) -> None:
        """Cache a query/response pair of ``business_id`` with its embedding."""
        if business_id is None:
            return
        embedding = await self._embed(query)
        if embedding is None:
            return

        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(SemanticCacheEmbedding).where(
                    SemanticCacheEmbedding.business_id == business_id,
                    SemanticCacheEmbedding.created_at < self._cutoff(),
                )
            )
            db.add(
                SemanticCacheEmbedding(
                    business_id=business_id,
                    query_text=query,
                    query_embedding=embedding,
                    response_text=response,
                    model_used=model_used,
                )
            )
            await db.commit()
            logger.info("Semantic cache STORE")

    # ------------------------------------------------------------------
    # Aliases used by llm_provider.py
    # ------------------------------------------------------------------

    async def get(
        self, prompt: str, business_id: uuid.UUID | None = None
    ) -> str | None:
        """Alias for get_similar with default threshold."""
        return await self.get_similar(
            prompt, business_id=business_id, threshold=DEFAULT_THRESHOLD
        )

    async def set(
        self,
        prompt: str,
        response: str,
        ttl: int | None = None,
        business_id: uuid.UUID | None = None,
    ) -> None:
        """Alias for store (ttl is ignored; the cache-wide TTL applies)."""
        await self.store(
            prompt, response, model_used="unknown", business_id=business_id
        )

    async def invalidate(
        self, pattern: str = "", business_id: uuid.UUID | None = None
    ) -> int:
        """Invalidate cached entries whose query_text contains the pattern (one business, or all)."""
        async with AsyncSessionLocal() as db:
            stmt = select(SemanticCacheEmbedding).where(
                SemanticCacheEmbedding.query_text.ilike(f"%{pattern}%")
            )
            if business_id is not None:
                stmt = stmt.where(SemanticCacheEmbedding.business_id == business_id)
            entries = (await db.execute(stmt)).scalars().all()
            for entry in entries:
                await db.delete(entry)
            await db.commit()
            return len(entries)

    async def stats(self) -> dict:
        """Return basic cache stats."""
        async with AsyncSessionLocal() as db:
            count_result = await db.execute(func.count(SemanticCacheEmbedding.id))
            total = count_result.scalar() or 0
            return {
                "cached_prompts": total,
                "threshold": DEFAULT_THRESHOLD,
                "ttl_seconds": self.ttl,
            }


# Convenience singleton
semantic_cache = SemanticCache()
