"""Business Document RAG Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentChunkResponse(BaseModel):
    id: UUID
    chunk_index: int
    page_number: int | None = None
    content: str
    chunk_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BusinessDocumentBase(BaseModel):
    title: str
    file_type: str
    file_size: int = 0
    status: str = "processing"
    chunk_count: int = 0
    extra_data: dict[str, Any] = Field(default_factory=dict)


class BusinessDocumentCreate(BaseModel):
    title: str


class BusinessDocumentResponse(BusinessDocumentBase):
    id: UUID
    business_id: UUID
    file_path: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BusinessDocumentDetailResponse(BusinessDocumentResponse):
    chunks: list[DocumentChunkResponse] = Field(default_factory=list)


class DocumentSearchRequest(BaseModel):
    query: str
    k: int = Field(default=5, ge=1, le=50)


class DocumentSearchResult(BaseModel):
    chunk_id: UUID
    document_id: UUID
    title: str
    content: str
    chunk_index: int
    page_number: int | None = None
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentSearchResponse(BaseModel):
    query: str
    results: list[DocumentSearchResult] = Field(default_factory=list)
