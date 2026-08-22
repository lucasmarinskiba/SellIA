"""User Memory Service"""

from datetime import datetime, timezone
from uuid import UUID
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert
from sqlalchemy.orm import sessionmaker

from app.domains.user_memory.models import UserMemory, UserMemoryEvent, UserPreference
from app.domains.user_memory.schemas import UserMemoryUpdate, UserMemoryEventCreate, UserPreferenceUpdate


class UserMemoryService:
    """Servicio para gestionar la memoria persistente del usuario"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, user_id: UUID) -> UserMemory:
        """Get o crea UserMemory para un usuario"""
        result = await self.db.execute(
            select(UserMemory).where(UserMemory.user_id == user_id)
        )
        memory = result.scalar_one_or_none()

        if not memory:
            memory = UserMemory(user_id=user_id)
            self.db.add(memory)
            await self.db.commit()
            await self.db.refresh(memory)

        return memory

    async def get_memory(self, user_id: UUID) -> Optional[UserMemory]:
        """Get UserMemory del usuario"""
        result = await self.db.execute(
            select(UserMemory).where(UserMemory.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_memory(self, user_id: UUID, update_data: UserMemoryUpdate) -> UserMemory:
        """Update UserMemory con nuevos datos"""
        memory = await self.get_or_create(user_id)

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)

        for key, value in update_dict.items():
            if value is not None:
                setattr(memory, key, value)

        memory.updated_at = datetime.now(timezone.utc)
        memory.last_activity_at = datetime.now(timezone.utc)

        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)

        return memory

    async def log_event(self, user_id: UUID, event_data: UserMemoryEventCreate) -> UserMemoryEvent:
        """Log un evento de memoria (mensaje, acción, etc.)"""
        event = UserMemoryEvent(
            user_id=user_id,
            event_type=event_data.event_type,
            event_data=event_data.event_data,
            conversation_id=UUID(event_data.conversation_id) if event_data.conversation_id else None,
            business_id=UUID(event_data.business_id) if event_data.business_id else None,
            agent_id=UUID(event_data.agent_id) if event_data.agent_id else None,
        )
        self.db.add(event)

        # También actualizar contador de mensajes en UserMemory
        memory = await self.get_or_create(user_id)
        if event_data.event_type == "message_sent":
            memory.total_messages += 1
        elif event_data.event_type == "conversation_started":
            memory.total_conversations += 1

        await self.db.commit()
        await self.db.refresh(event)

        return event

    async def add_interest(self, user_id: UUID, interest: str) -> UserMemory:
        """Add un interés a key_interests (si no existe)"""
        memory = await self.get_or_create(user_id)

        if interest not in memory.key_interests:
            memory.key_interests.append(interest)
            memory.updated_at = datetime.now(timezone.utc)
            self.db.add(memory)
            await self.db.commit()
            await self.db.refresh(memory)

        return memory

    async def add_challenge(self, user_id: UUID, challenge: str) -> UserMemory:
        """Add un desafío a key_challenges"""
        memory = await self.get_or_create(user_id)

        if challenge not in memory.key_challenges:
            memory.key_challenges.append(challenge)
            memory.updated_at = datetime.now(timezone.utc)
            self.db.add(memory)
            await self.db.commit()
            await self.db.refresh(memory)

        return memory

    async def add_favorite_agent(self, user_id: UUID, agent_id: UUID, agent_name: str) -> UserMemory:
        """Track favorite agent usage"""
        memory = await self.get_or_create(user_id)

        # Find or create agent entry in favorite_agents
        agent_entry = next((a for a in memory.favorite_agents if a.get("agent_id") == str(agent_id)), None)

        if agent_entry:
            agent_entry["count"] = agent_entry.get("count", 0) + 1
            agent_entry["last_used"] = datetime.now(timezone.utc).isoformat()
        else:
            memory.favorite_agents.append({
                "agent_id": str(agent_id),
                "agent_name": agent_name,
                "count": 1,
                "first_used": datetime.now(timezone.utc).isoformat(),
                "last_used": datetime.now(timezone.utc).isoformat(),
            })

        memory.updated_at = datetime.now(timezone.utc)
        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)

        return memory

    async def update_engagement_score(self, user_id: UUID, delta: float) -> UserMemory:
        """Update engagement score (0-1)"""
        memory = await self.get_or_create(user_id)

        new_score = min(1.0, max(0.0, memory.engagement_score + delta))
        memory.engagement_score = new_score

        memory.updated_at = datetime.now(timezone.utc)
        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)

        return memory

    async def set_preference(self, user_id: UUID, preference_key: str, preference_value: Dict[str, Any]) -> UserPreference:
        """Set o update una preferencia granular"""
        result = await self.db.execute(
            select(UserPreference).where(
                UserPreference.user_id == user_id,
                UserPreference.preference_key == preference_key,
            )
        )
        pref = result.scalar_one_or_none()

        if pref:
            pref.preference_value = preference_value
            pref.updated_at = datetime.now(timezone.utc)
        else:
            pref = UserPreference(
                user_id=user_id,
                preference_key=preference_key,
                preference_value=preference_value,
            )
            self.db.add(pref)

        await self.db.commit()
        await self.db.refresh(pref)

        return pref

    async def get_preference(self, user_id: UUID, preference_key: str) -> Optional[UserPreference]:
        """Get una preferencia granular"""
        result = await self.db.execute(
            select(UserPreference).where(
                UserPreference.user_id == user_id,
                UserPreference.preference_key == preference_key,
            )
        )
        return result.scalar_one_or_none()

    async def get_recent_events(self, user_id: UUID, limit: int = 50) -> List[UserMemoryEvent]:
        """Get últimos eventos del usuario"""
        result = await self.db.execute(
            select(UserMemoryEvent)
            .where(UserMemoryEvent.user_id == user_id)
            .order_by(UserMemoryEvent.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
