"""Business Document RAG Models"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.types import UserDefinedType

from app.core.database import Base


class Vector(UserDefinedType):
    """Custom SQLAlchemy type for pgvector VECTOR(dim)."""

    def __init__(self, dim: int):
        self.dim = dim

    def get_col_spec(self):
        return f"VECTOR({self.dim})"

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            return f"[{','.join(str(v) for v in value)}]"
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            if isinstance(value, str):
                # Postgres returns vector as string like '[1,2,3]'
                value = value.strip("[]")
                return [float(v) for v in value.split(",")] if value else []
            if isinstance(value, list):
                return [float(v) for v in value]
            return value
        return process


class BusinessDocument(Base):
    __tablename__ = "business_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, txt, docx, csv
    file_size = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="processing")  # processing, ready, error
    chunk_count = Column(Integer, nullable=False, default=0)
    extra_data = Column(JSONB, default=dict, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("business_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=True)
    chunk_index = Column(Integer, nullable=False, default=0)
    page_number = Column(Integer, nullable=True)
    chunk_metadata = Column(JSONB, default=dict, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    document = relationship("BusinessDocument", back_populates="chunks")

    __table_args__ = (
        Index("ix_document_chunks_business_id_embedding", "business_id"),
    )
