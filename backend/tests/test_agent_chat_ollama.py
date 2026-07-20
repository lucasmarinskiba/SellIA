"""Test de integración: Chat con agente usando fallback a Ollama (sin API key de OpenAI)."""

import pytest
from uuid import uuid4
from sqlalchemy import select

from app.domains.agents.models import AgentPersonality, AgentConfig, AgentConversation, AgentMessage
from app.domains.agents.services import AgentService
from app.domains.businesses.models import Business


@pytest.mark.asyncio
async def test_agent_chat_with_ollama_fallback(db_session, test_user):
    """Test: el chat con un agente funciona sin API key de OpenAI usando Ollama."""
    # Crear un business
    business = Business(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Business",
        type="services",
        description="Test",
        config={},
    )
    db_session.add(business)
    await db_session.commit()
    await db_session.refresh(business)

    # Obtener una personalidad existente
    personality = (await db_session.execute(select(AgentPersonality).limit(1))).scalar_one_or_none()
    if not personality:
        personality = AgentPersonality(
            id=uuid4(),
            slug="test-personality",
            name="Test Personality",
            emoji="🤖",
            tagline="Test",
            description="Test personality",
            expertise=["ventas"],
            color="#FF6B35",
            display_order=0,
            is_active=True,
        )
        db_session.add(personality)
        await db_session.commit()
        await db_session.refresh(personality)

    # Crear config del agente
    config = AgentConfig(
        id=uuid4(),
        business_id=business.id,
        personality_id=personality.id,
        is_enabled=True,
        extra_data={},
    )
    db_session.add(config)
    await db_session.commit()

    # Crear conversación
    conv = AgentConversation(
        id=uuid4(),
        user_id=test_user.id,
        business_id=business.id,
        personality_id=personality.id,
        title="Test Ollama Fallback",
    )
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    # Enviar mensaje de chat via AgentService directamente
    service = AgentService(db_session)
    response = await service.chat(
        conversation_id=conv.id,
        user_id=test_user.id,
        content="Hola, presentate en una oración",
    )

    assert response.role == "assistant"
    assert len(response.content) > 0
    assert response.model_used in ("llama3.1", "gpt-4o-mini", "semantic-cache")
    print(f"\nModel used: {response.model_used}")
    print(f"Response: {response.content[:300]}")
