"""Memory Engine Models

Stores conversation memory chunks (with embeddings) and persistent customer facts.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Float, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import UserDefinedType

from app.core.database import Base


class Vector(UserDefinedType):
    """Custom SQLAlchemy type for PostgreSQL pgvector VECTOR(dim)."""

    def __init__(self, dim: int):
        self.dim = dim

    def get_col_spec(self):
        return f"VECTOR({self.dim})"


class ConversationMemoryChunk(Base):
    """A chunk of a conversation with its vector embedding for semantic retrieval."""

    __tablename__ = "conversation_memory_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    business_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # the customer
    agent_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=True)
    chunk_index = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index(
            "ix_memory_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


class CustomerMemory(Base):
    """A persistent fact about a customer extracted from conversations."""

    __tablename__ = "customer_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    memory_type = Column(
        String(50),
        nullable=False,
        index=True,
    )  # 'preference', 'objection', 'budget', 'channel', 'schedule', 'purchase_history', 'pain_point'
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)
    source_conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index(
            "ix_customer_memories_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
