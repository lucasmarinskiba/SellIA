"""Business Document RAG Schemas"""

from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class DocumentChunkResponse(BaseModel):
    id: UUID
    chunk_index: int
    page_number: Optional[int] = None
    content: str
    chunk_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BusinessDocumentBase(BaseModel):
    title: str
    file_type: str
    file_size: int = 0
    status: str = "processing"
    chunk_count: int = 0
    extra_data: Dict[str, Any] = Field(default_factory=dict)


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
    chunks: List[DocumentChunkResponse] = Field(default_factory=list)


class DocumentSearchRequest(BaseModel):
    query: str
    k: int = Field(default=5, ge=1, le=50)


class DocumentSearchResult(BaseModel):
    chunk_id: UUID
    document_id: UUID
    title: str
    content: str
    chunk_index: int
    page_number: Optional[int] = None
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentSearchResponse(BaseModel):
    query: str
    results: List[DocumentSearchResult] = Field(default_factory=list)
