"""Memory Engine API Router"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.memory.service import MemoryEngine
from app.domains.memory.schemas import (
    MemoryChunkResponse,
    CustomerMemoryResponse,
    CustomerMemoryCreate,
    CustomerProfileResponse,
)

router = APIRouter(prefix="/memory", tags=["memory"])


# ========== Conversation Memory Chunks ==========

@router.get("/chunks", response_model=list[MemoryChunkResponse])
async def retrieve_relevant_chunks(
    query: str = Query(..., description="Query text for semantic search"),
    conversation_id: Optional[UUID] = Query(None),
    business_id: Optional[UUID] = Query(None),
    customer_id: Optional[UUID] = Query(None),
    k: int = Query(5, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = MemoryEngine(db)
    return await engine.retrieve_relevant(
        query=query,
        conversation_id=conversation_id,
        business_id=business_id,
        customer_id=customer_id,
        k=k,
    )


@router.delete("/chunks/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chunk(
    chunk_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = MemoryEngine(db)
    deleted = await engine.delete_chunk(chunk_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chunk no encontrado")
    return None


# ========== Customer Memories ==========

@router.get("/customer/{customer_id}", response_model=CustomerProfileResponse)
async def get_customer_profile(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = MemoryEngine(db)
    grouped = await engine.get_customer_profile(customer_id)
    # Wrap ORM objects into response schemas
    from app.domains.memory.schemas import CustomerMemoryResponse
    serialized: dict = {
        mem_type: [CustomerMemoryResponse.model_validate(m) for m in items]
        for mem_type, items in grouped.items()
    }
    return CustomerProfileResponse(customer_id=customer_id, memories=serialized)


@router.post("/customer-fact", response_model=CustomerMemoryResponse, status_code=status.HTTP_201_CREATED)
async def store_customer_fact(
    data: CustomerMemoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = MemoryEngine(db)
    fact = await engine.store_customer_fact(
        business_id=data.business_id,
        customer_id=data.customer_id,
        memory_type=data.memory_type,
        content=data.content,
        confidence=data.confidence,
        source_conversation_id=data.source_conversation_id,
    )
    return fact


# ------------------------------------------------------------------
# Summarization
# ------------------------------------------------------------------

@router.post("/summarize/{conversation_id}", status_code=status.HTTP_202_ACCEPTED)
async def trigger_summarization(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger asynchronous summarization for a conversation."""
    from app.domains.memory.tasks import summarize_conversation_task
    summarize_conversation_task.delay(str(conversation_id))
    return {"status": "scheduled", "conversation_id": conversation_id}


# ------------------------------------------------------------------
# Customer Profile Text
# ------------------------------------------------------------------

@router.get("/customer/{customer_id}/profile-text")
async def get_customer_profile_text(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a formatted profile text for injection into agent prompts."""
    engine = MemoryEngine(db)
    profile = await engine.get_customer_profile_summary(customer_id)
    return {"customer_id": customer_id, "profile_text": profile}
