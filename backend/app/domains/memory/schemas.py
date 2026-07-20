"""Memory Engine Schemas"""

from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, ConfigDict


class MemoryChunkBase(BaseModel):
    conversation_id: UUID
    business_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    role: str
    content: str
    chunk_index: int = 0


class MemoryChunkCreate(MemoryChunkBase):
    pass


class MemoryChunkResponse(MemoryChunkBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerMemoryBase(BaseModel):
    business_id: UUID
    customer_id: UUID
    memory_type: str
    content: str
    confidence: float = 0.0
    source_conversation_id: Optional[UUID] = None


class CustomerMemoryCreate(CustomerMemoryBase):
    pass


class CustomerMemoryResponse(CustomerMemoryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerProfileResponse(BaseModel):
    customer_id: UUID
    memories: Dict[str, List[CustomerMemoryResponse]]
