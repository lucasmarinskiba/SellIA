"""
Semantic Cache for LLM Responses (Vector-based v2)

Stores cached queries as embeddings in PostgreSQL with pgvector.
Matching uses cosine similarity for true semantic retrieval.

Typical savings: 30-50% on FAQ-style queries.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, DateTime, Text, Integer, select, func
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

from app.core.database import Base, AsyncSessionLocal
from app.core.embeddings import embedding_service
from app.core.logger import get_logger

logger = get_logger(__name__)

DEFAULT_THRESHOLD = 0.92
DEFAULT_TTL_SECONDS = 86400  # 24h


class SemanticCacheEmbedding(Base):
    """PostgreSQL-backed semantic cache using pgvector."""

    __tablename__ = "semantic_cache_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_text = Column(Text, nullable=False)
    query_embedding = Column(Vector(768), nullable=False)
    response_text = Column(Text, nullable=False)
    model_used = Column(String(100), nullable=False, default="unknown")
    hit_count = Column(Integer, default=0, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_accessed = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class SemanticCache:
    """Vector-based semantic cache for LLM responses."""

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self.ttl = ttl_seconds

    async def get_similar(self, query: str, threshold: float = DEFAULT_THRESHOLD) -> Optional[str]:
        """Look up a semantically similar cached response using cosine similarity."""
        try:
            embedding = await embedding_service.embed_text(query)
        except Exception as e:
            logger.warning(f"Embedding generation failed for cache lookup: {e}")
            return None

        async with AsyncSessionLocal() as db:
            stmt = (
                select(
                    SemanticCacheEmbedding,
                    (1 - SemanticCacheEmbedding.query_embedding.cosine_distance(embedding)).label(
                        "similarity"
                    ),
                )
                .order_by(SemanticCacheEmbedding.query_embedding.cosine_distance(embedding))
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
                match.last_accessed = datetime.now(timezone.utc)
                await db.commit()
                logger.info(f"Semantic cache HIT (similarity={similarity:.3f})")
                return match.response_text

        return None

    async def store(self, query: str, response: str, model_used: str = "unknown") -> None:
        """Cache a query/response pair with its embedding."""
        try:
            embedding = await embedding_service.embed_text(query)
        except Exception as e:
            logger.warning(f"Embedding generation failed for cache store: {e}")
            return

        async with AsyncSessionLocal() as db:
            cache_entry = SemanticCacheEmbedding(
                query_text=query,
                query_embedding=embedding,
                response_text=response,
                model_used=model_used,
            )
            db.add(cache_entry)
            await db.commit()
            logger.info("Semantic cache STORE")

    # ------------------------------------------------------------------
    # Backward-compatibility aliases (used by llm_provider.py)
    # ------------------------------------------------------------------

    async def get(self, prompt: str) -> Optional[str]:
        """Alias for get_similar with default threshold."""
        return await self.get_similar(prompt, threshold=DEFAULT_THRESHOLD)

    async def set(self, prompt: str, response: str, ttl: Optional[int] = None) -> None:
        """Alias for store (ttl is ignored; managed by table rows)."""
        await self.store(prompt, response, model_used="unknown")

    async def invalidate(self, pattern: str = "") -> int:
        """Invalidate cached entries whose query_text contains the pattern."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(SemanticCacheEmbedding).where(
                    SemanticCacheEmbedding.query_text.ilike(f"%{pattern}%")
                )
            )
            entries = result.scalars().all()
            for entry in entries:
                await db.delete(entry)
            await db.commit()
            return len(entries)

    async def stats(self) -> dict:
        """Return basic cache stats."""
        async with AsyncSessionLocal() as db:
            count_result = await db.execute(
                func.count(SemanticCacheEmbedding.id)
            )
            total = count_result.scalar() or 0
            return {
                "cached_prompts": total,
                "threshold": DEFAULT_THRESHOLD,
                "ttl_seconds": self.ttl,
            }


# Convenience singleton
semantic_cache = SemanticCache()
