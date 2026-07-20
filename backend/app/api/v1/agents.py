"""Agentes IA — API Router

Endpoints para gestionar agentes expertos, conversaciones y chat.
"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.domains.subscriptions.services import check_subscription_limit, track_usage
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.agents.models import AgentPersonality, AgentConversation, AgentMessage, AgentConfig
from app.domains.agents.schemas import (
    AgentPersonalityResponse,
    AgentConversationCreate,
    AgentConversationResponse,
    AgentConversationDetailResponse,
    AgentMessageCreate,
    AgentMessageResponse,
    AgentChatResponse,
    AutopilotVoiceConfig,
    AutopilotVoiceConfigResponse,
    AgentConfigResponse,
    AgentConfigCreate,
    AgentConfigUpdate,
    ReactChatRequest,
    ReactChatResponse,
    PlanRequest,
    PlanResponse,
    PlanStepResponse,
)
from app.domains.agents.services import AgentService
from app.domains.subscriptions.services import check_subscription_limit
from app.domains.subscriptions.models import UserAPIKey

router = APIRouter()


# ========== Personalities ==========

@router.get("/personalities", response_model=list[AgentPersonalityResponse])
async def list_personalities(
    db: AsyncSession = Depends(get_db),
):
    """Listar todas las personalidades de agentes disponibles."""
    service = AgentService(db)
    personalities = await service.get_personalities(active_only=True)
    return personalities


@router.post("/personalities/seed", status_code=status.HTTP_201_CREATED)
async def seed_personalities(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Sembrar personalidades predefinidas (solo admin)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Solo superusuarios pueden sembrar personalidades")
    service = AgentService(db)
    await service.seed_personalities()
    return {"message": "Personalidades sembradas correctamente"}


# ========== Conversations ==========

@router.get("/conversations", response_model=list[AgentConversationResponse])
async def list_conversations(
    business_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Listar conversaciones del usuario actual."""
    service = AgentService(db)
    conversations = await service.list_conversations(current_user.id, business_id)
    return conversations


@router.post("/conversations", response_model=AgentConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: AgentConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Crear una nueva conversación con un agente."""
    # Verify business belongs to user
    result = await db.execute(
        select(Business).where(Business.id == data.business_id).where(Business.user_id == current_user.id)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    # Verify personality exists
    result = await db.execute(
        select(AgentPersonality).where(AgentPersonality.id == data.personality_id)
    )
    personality = result.scalar_one_or_none()
    if not personality:
        raise HTTPException(status_code=404, detail="Personalidad no encontrada")

    service = AgentService(db)
    conv = await service.create_conversation(
        user_id=current_user.id,
        business_id=data.business_id,
        personality_id=data.personality_id,
        title=data.title,
    )
    # Eager load personality for response
    conv.personality = personality
    return conv


@router.get("/conversations/{conversation_id}", response_model=AgentConversationDetailResponse)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Obtener una conversación con todos sus mensajes."""
    service = AgentService(db)
    conv = await service.get_conversation(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    messages = await service.get_messages(conversation_id)

    # Eager load personality
    result = await db.execute(
        select(AgentPersonality).where(AgentPersonality.id == conv.personality_id)
    )
    conv.personality = result.scalar_one_or_none()

    return {
        "id": conv.id,
        "user_id": conv.user_id,
        "business_id": conv.business_id,
        "personality_id": conv.personality_id,
        "title": conv.title,
        "message_count": conv.message_count,
        "is_active": conv.is_active,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
        "personality": conv.personality,
        "messages": messages,
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Eliminar (soft-delete) una conversación."""
    service = AgentService(db)
    deleted = await service.delete_conversation(conversation_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return {"message": "Conversación eliminada"}


# ========== Chat ==========

@router.post("/conversations/{conversation_id}/chat", response_model=AgentChatResponse)
async def chat_with_agent(
    conversation_id: UUID,
    data: AgentMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Enviar un mensaje al agente y obtener respuesta."""

    # Check AI token limit
    limit_check = await check_subscription_limit(db, current_user.id, "ai_tokens", quantity=1)
    if not limit_check["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Límite de tokens IA alcanzado. Usados: {limit_check['used']}/{limit_check['limit']}"
        )

    service = AgentService(db)

    # Verify conversation
    conv = await service.get_conversation(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    # Get user's API key (will be resolved in service)
    result = await db.execute(
        select(UserAPIKey).where(
            UserAPIKey.user_id == current_user.id,
            UserAPIKey.provider == "openai",
            UserAPIKey.is_active == True,
        )
    )
    api_key_record = result.scalar_one_or_none()

    if not api_key_record or not api_key_record.api_key_fernet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tienes una API key de OpenAI configurada. Ve a Configuración > API Keys para agregar tu clave."
        )

    # Get personality
    result = await db.execute(
        select(AgentPersonality).where(AgentPersonality.id == conv.personality_id)
    )
    personality = result.scalar_one_or_none()

    # Get business context
    result = await db.execute(
        select(Business).where(Business.id == conv.business_id)
    )
    business = result.scalar_one_or_none()

    business_context = {}
    if business:
        business_context = {
            "name": business.name,
            "type": business.business_type,
            "description": business.description or "",
        }

    # Get custom instructions if any
    from app.domains.agents.models import AgentConfig
    result = await db.execute(
        select(AgentConfig).where(
            AgentConfig.business_id == conv.business_id,
            AgentConfig.personality_id == conv.personality_id,
        )
    )
    agent_config = result.scalar_one_or_none()
    custom_instructions = agent_config.custom_instructions if agent_config else None

    try:
        assistant_msg = await service.chat(
            conversation_id=conversation_id,
            user_id=current_user.id,
            content=data.content,
            business_context=business_context,
            custom_instructions=custom_instructions,
        )
    except Exception:
        from app.core.logger import get_logger
        get_logger(__name__).exception("Agent execution error")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    # Track token usage
    await track_usage(db, current_user.id, "ai_tokens", quantity=assistant_msg.tokens_used or 1)

    return AgentChatResponse(
        message=AgentMessageResponse.model_validate(assistant_msg),
        conversation_id=conversation_id,
        tokens_used=assistant_msg.tokens_used or 0,
    )


# ========== Agent Configs (Voice & Customization) ==========

# Functional auto-pilot slugs that can have voice overrides
AUTOPILOT_SLUGS = ["captador", "cualificador", "vendedor", "post-venta"]


@router.get("/configs", response_model=list[AgentConfigResponse])
async def list_agent_configs(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Listar configuraciones de agentes para un negocio."""
    result = await db.execute(
        select(Business).where(Business.id == business_id).where(Business.user_id == current_user.id)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    result = await db.execute(
        select(AgentConfig).where(AgentConfig.business_id == business_id)
    )
    configs = result.scalars().all()

    # Eager load personalities
    response = []
    for config in configs:
        result = await db.execute(
            select(AgentPersonality).where(AgentPersonality.id == config.personality_id)
        )
        config.personality = result.scalar_one_or_none()
        if config.voice_personality_id:
            result = await db.execute(
                select(AgentPersonality).where(AgentPersonality.id == config.voice_personality_id)
            )
            config.voice_personality = result.scalar_one_or_none()
        response.append(AgentConfigResponse.model_validate(config))

    return response


@router.post("/configs", response_model=AgentConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_agent_config(
    business_id: UUID,
    data: AgentConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Crear o actualizar configuración de un agente para un negocio."""
    result = await db.execute(
        select(Business).where(Business.id == business_id).where(Business.user_id == current_user.id)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    # Verify personality exists
    result = await db.execute(
        select(AgentPersonality).where(AgentPersonality.id == data.personality_id)
    )
    personality = result.scalar_one_or_none()
    if not personality:
        raise HTTPException(status_code=404, detail="Personalidad no encontrada")

    # Verify voice personality if provided
    if data.voice_personality_id:
        result = await db.execute(
            select(AgentPersonality).where(AgentPersonality.id == data.voice_personality_id)
        )
        voice = result.scalar_one_or_none()
        if not voice:
            raise HTTPException(status_code=404, detail="Voz experta no encontrada")

    # Find existing config
    result = await db.execute(
        select(AgentConfig).where(
            AgentConfig.business_id == business_id,
            AgentConfig.personality_id == data.personality_id,
        )
    )
    config = result.scalar_one_or_none()

    if config:
        # Update
        config.custom_instructions = data.custom_instructions
        config.tone_override = data.tone_override
        config.voice_personality_id = data.voice_personality_id
        config.extra_data = data.extra_data
        config.is_enabled = True
    else:
        # Create
        config = AgentConfig(
            business_id=business_id,
            personality_id=data.personality_id,
            custom_instructions=data.custom_instructions,
            tone_override=data.tone_override,
            voice_personality_id=data.voice_personality_id,
            extra_data=data.extra_data,
            is_enabled=True,
        )
        db.add(config)

    await db.commit()
    await db.refresh(config)

    # Eager load
    config.personality = personality
    if config.voice_personality_id:
        result = await db.execute(
            select(AgentPersonality).where(AgentPersonality.id == config.voice_personality_id)
        )
        config.voice_personality = result.scalar_one_or_none()

    return AgentConfigResponse.model_validate(config)


@router.get("/autopilot-voices", response_model=AutopilotVoiceConfigResponse)
async def get_autopilot_voices(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Obtener configuración de voz experta para cada agente de auto-piloto."""
    result = await db.execute(
        select(Business).where(Business.id == business_id).where(Business.user_id == current_user.id)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    # Get all personalities (by slug and by id)
    result = await db.execute(select(AgentPersonality))
    all_personalities = result.scalars().all()
    personalities_by_slug = {p.slug: p for p in all_personalities}
    personalities_by_id = {p.id: p for p in all_personalities}

    # Build configs for each auto-pilot slug
    configs = {}
    for slug in AUTOPILOT_SLUGS:
        personality = personalities_by_slug.get(slug)
        voice_slug = None
        custom_instructions = None

        if personality:
            result = await db.execute(
                select(AgentConfig).where(
                    AgentConfig.business_id == business_id,
                    AgentConfig.personality_id == personality.id,
                )
            )
            config = result.scalar_one_or_none()
            if config:
                custom_instructions = config.custom_instructions
                if config.voice_personality_id:
                    voice_personality = personalities_by_id.get(config.voice_personality_id)
                    if voice_personality:
                        voice_slug = voice_personality.slug

        configs[slug] = AutopilotVoiceConfig(
            personality_slug=slug,
            voice_personality_slug=voice_slug,
            custom_instructions=custom_instructions,
        )

    return AutopilotVoiceConfigResponse(configs=configs)


# ========== ReAct Orchestrator ==========

@router.post("/react-chat", response_model=ReactChatResponse)
async def react_chat(
    data: ReactChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Chat using the ReAct orchestrator with tool use."""
    from app.domains.agents.react_orchestrator import ReActOrchestrator

    orchestrator = ReActOrchestrator(
        db=db,
        user_id=current_user.id,
        business_id=data.business_id,
    )
    result = await orchestrator.process(
        user_input=data.message,
        conversation_history=data.conversation_history,
    )
    return ReactChatResponse(
        response=result["final_answer"],
        iterations=result["iterations"],
        tool_calls=result.get("tool_calls", []),
        tokens_used=result.get("tokens_used", 0),
        model=result.get("model"),
        provider=result.get("provider"),
    )


@router.post("/plan", response_model=PlanResponse)
async def create_and_execute_plan(
    data: PlanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a plan for a complex task and execute it via ReAct."""
    from app.domains.agents.planning_agent import PlanningAgent
    from app.domains.agents.react_orchestrator import ReActOrchestrator

    planner = PlanningAgent(
        db=db,
        user_id=current_user.id,
        business_id=data.business_id,
    )
    plan = await planner.create_plan(
        task_description=data.task_description,
        context=data.context,
    )

    react = ReActOrchestrator(
        db=db,
        user_id=current_user.id,
        business_id=data.business_id,
    )
    execution = await planner.execute_plan(plan, react)

    return PlanResponse(
        plan=[PlanStepResponse.model_validate(s) for s in plan.sub_tasks],
        results=execution["results"],
        status="completed" if execution["failed_steps"] == 0 else "partial",
        completed_steps=execution["completed_steps"],
        failed_steps=execution["failed_steps"],
    )


# ========== Sales Playbooks ==========

@router.post("/{business_id}/playbooks/generate", status_code=status.HTTP_201_CREATED)
async def generate_playbook(
    business_id: UUID,
    voice_slug: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate an AI-powered sales playbook for a business."""
    result = await db.execute(
        select(Business).where(Business.id == business_id).where(Business.user_id == current_user.id)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    from app.domains.agents.playbooks import generate_sales_playbook

    playbook = await generate_sales_playbook(
        db=db,
        business_id=business_id,
        voice_slug=voice_slug,
    )

    if not playbook:
        raise HTTPException(status_code=500, detail="No se pudo generar el playbook")

    # Store playbook reference in business config
    if not business.config:
        business.config = {}
    business.config["last_playbook"] = playbook
    await db.commit()

    return {"playbook": playbook, "message": "Playbook generado correctamente"}
