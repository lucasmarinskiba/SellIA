"""Memory Engine Service

Handles semantic storage and retrieval of conversation chunks and customer facts.
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from sqlalchemy import select, delete, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.embeddings import EmbeddingService
from app.domains.memory.models import ConversationMemoryChunk, CustomerMemory


class MemoryEngine:
    """Service layer for the Memory Engine."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Conversation chunks
    # ------------------------------------------------------------------

    async def store_message(
        self,
        conversation_id: uuid.UUID,
        business_id: Optional[uuid.UUID],
        user_id: Optional[uuid.UUID],
        agent_id: Optional[uuid.UUID],
        role: str,
        content: str,
        chunk_index: int,
    ) -> ConversationMemoryChunk:
        """Store a conversation message with its embedding."""
        try:
            embedding = await EmbeddingService.embed_text(content)
        except NotImplementedError:
            embedding = None

        chunk = ConversationMemoryChunk(
            conversation_id=conversation_id,
            business_id=business_id,
            user_id=user_id,
            agent_id=agent_id,
            role=role,
            content=content,
            embedding=embedding,
            chunk_index=chunk_index,
        )
        self.db.add(chunk)
        await self.db.commit()
        await self.db.refresh(chunk)
        return chunk

    async def retrieve_relevant(
        self,
        query: str,
        conversation_id: Optional[uuid.UUID] = None,
        business_id: Optional[uuid.UUID] = None,
        customer_id: Optional[uuid.UUID] = None,
        k: int = 5,
    ) -> List[ConversationMemoryChunk]:
        """Semantic search over conversation memory chunks."""
        try:
            query_vec = await EmbeddingService.embed_text(query)
        except NotImplementedError:
            # Fallback: return recent chunks filtered by criteria
            stmt = select(ConversationMemoryChunk).order_by(
                ConversationMemoryChunk.created_at.desc()
            ).limit(k)
            if conversation_id:
                stmt = stmt.where(ConversationMemoryChunk.conversation_id == conversation_id)
            if business_id:
                stmt = stmt.where(ConversationMemoryChunk.business_id == business_id)
            if customer_id:
                stmt = stmt.where(ConversationMemoryChunk.user_id == customer_id)
            result = await self.db.execute(stmt)
            return result.scalars().all()

        # Use cosine distance via raw text ordering
        distance_expr = text("embedding <=> :qvec").bindparams(qvec=str(query_vec))
        stmt = (
            select(ConversationMemoryChunk)
            .order_by(distance_expr)
            .limit(k)
        )

        if conversation_id:
            stmt = stmt.where(ConversationMemoryChunk.conversation_id == conversation_id)
        if business_id:
            stmt = stmt.where(ConversationMemoryChunk.business_id == business_id)
        if customer_id:
            stmt = stmt.where(ConversationMemoryChunk.user_id == customer_id)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_conversation_summary(
        self,
        conversation_id: uuid.UUID,
    ) -> List[ConversationMemoryChunk]:
        """Return all chunks for a conversation ordered by chunk_index."""
        result = await self.db.execute(
            select(ConversationMemoryChunk)
            .where(ConversationMemoryChunk.conversation_id == conversation_id)
            .order_by(ConversationMemoryChunk.chunk_index.asc())
        )
        return result.scalars().all()

    # ------------------------------------------------------------------
    # Customer facts
    # ------------------------------------------------------------------

    async def store_customer_fact(
        self,
        business_id: uuid.UUID,
        customer_id: uuid.UUID,
        memory_type: str,
        content: str,
        confidence: float,
        source_conversation_id: Optional[uuid.UUID] = None,
    ) -> CustomerMemory:
        """Store an extracted customer fact with its embedding."""
        try:
            embedding = await EmbeddingService.embed_text(content)
        except NotImplementedError:
            embedding = None

        fact = CustomerMemory(
            business_id=business_id,
            customer_id=customer_id,
            memory_type=memory_type,
            content=content,
            embedding=embedding,
            confidence=confidence,
            source_conversation_id=source_conversation_id,
        )
        self.db.add(fact)
        await self.db.commit()
        await self.db.refresh(fact)
        return fact

    async def get_customer_profile(
        self,
        customer_id: uuid.UUID,
    ) -> Dict[str, List[CustomerMemory]]:
        """Return all CustomerMemory records for a customer grouped by type."""
        result = await self.db.execute(
            select(CustomerMemory)
            .where(CustomerMemory.customer_id == customer_id)
            .order_by(CustomerMemory.created_at.desc())
        )
        memories = result.scalars().all()
        grouped: Dict[str, List[CustomerMemory]] = {}
        for mem in memories:
            grouped.setdefault(mem.memory_type, []).append(mem)
        return grouped

    async def search_customer_memories(
        self,
        query: str,
        customer_id: uuid.UUID,
        k: int = 5,
    ) -> List[CustomerMemory]:
        """Semantic search over a customer's memories."""
        try:
            query_vec = await EmbeddingService.embed_text(query)
        except NotImplementedError:
            # Fallback: return recent memories
            result = await self.db.execute(
                select(CustomerMemory)
                .where(CustomerMemory.customer_id == customer_id)
                .order_by(CustomerMemory.created_at.desc())
                .limit(k)
            )
            return result.scalars().all()

        distance_expr = text("embedding <=> :qvec").bindparams(qvec=str(query_vec))
        result = await self.db.execute(
            select(CustomerMemory)
            .where(CustomerMemory.customer_id == customer_id)
            .order_by(distance_expr)
            .limit(k)
        )
        return result.scalars().all()

    # ------------------------------------------------------------------
    # Admin / cleanup
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Customer Profile Builder
    # ------------------------------------------------------------------

    async def extract_facts_from_conversation(
        self,
        conversation_id: uuid.UUID,
    ) -> List[CustomerMemory]:
        """
        1. Get conversation messages from memory chunks.
        2. Build prompt and call LLM for fact extraction.
        3. Parse JSON response.
        4. Store each fact as CustomerMemory with embedding.
        """
        import json
        from app.domains.agents.ai_reply import generate_raw_ai_response

        chunks = await self.get_conversation_summary(conversation_id)
        if not chunks:
            return []

        conversation_text = "\n".join(f"{c.role}: {c.content}" for c in chunks)
        business_id = chunks[0].business_id
        customer_id = chunks[0].user_id

        if not business_id or not customer_id:
            return []

        prompt = (
            "Extrae hechos clave de este cliente: preferencias, objeciones, presupuesto, "
            "canal preferido, horario ideal, historial de compras, pain points. "
            'Devuelve JSON con formato: {"facts": [{"type": "...", "content": "...", "confidence": 0.9}]}\n\n'
            f"Conversación:\n{conversation_text}\n\nJSON:"
        )

        facts_json = await generate_raw_ai_response(
            db=self.db,
            business_id=business_id,
            system_prompt=(
                "Eres un extractor de datos de ventas. Extrae hechos clave del cliente "
                "en JSON válido. Usa tipos: preference, objection, budget, channel, "
                "schedule, purchase_history, pain_point."
            ),
            user_prompt=prompt,
            max_tokens=1200,
            temperature=0.2,
        )

        if not facts_json:
            return []

        try:
            data = json.loads(facts_json)
            facts = data.get("facts", [])
        except json.JSONDecodeError:
            return []

        stored: List[CustomerMemory] = []
        for fact in facts:
            mem_type = fact.get("type", "preference")
            content = str(fact.get("content", "")).strip()
            confidence = float(fact.get("confidence", 0.7))
            if content:
                mem = await self.store_customer_fact(
                    business_id=business_id,
                    customer_id=customer_id,
                    memory_type=mem_type,
                    content=content,
                    confidence=confidence,
                    source_conversation_id=conversation_id,
                )
                stored.append(mem)
        return stored

    async def get_customer_profile_summary(self, customer_id: uuid.UUID) -> str:
        """Return a formatted profile text suitable for injection into agent prompts."""
        grouped = await self.get_customer_profile(customer_id)
        if not grouped:
            return ""

        lines = ["## Perfil del Cliente"]
        for mem_type, memories in grouped.items():
            lines.append(f"\n### {mem_type.replace('_', ' ').title()}")
            for mem in memories[:5]:  # top 5 per type
                lines.append(f"- {mem.content} (confianza: {mem.confidence:.0%})")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Admin / cleanup
    # ------------------------------------------------------------------

    async def delete_chunk(self, chunk_id: uuid.UUID) -> bool:
        """Delete a conversation memory chunk by ID."""
        result = await self.db.execute(
            delete(ConversationMemoryChunk).where(
                ConversationMemoryChunk.id == chunk_id
            )
        )
        await self.db.commit()
        return result.rowcount > 0
