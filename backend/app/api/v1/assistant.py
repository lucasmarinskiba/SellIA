"""SellIA Assistant — API Router

Endpoints para el asistente conversacional SellIA que orquesta
agentes y ejecuta acciones basadas en lenguaje natural.
"""

from datetime import datetime, timezone
from uuid import UUID
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.agents.orchestrator import SellIAOrchestrator
from app.domains.agents.services import AgentService
from app.domains.agents.schemas import AgentPersonalityResponse
from app.domains.agents.models import SellIAConversation

router = APIRouter()


# ───────────────────────────────────────────────
# SellIA Conversations (persistent history)
# ───────────────────────────────────────────────

@router.get("/conversations", response_model=list[dict])
async def list_assistant_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all SellIA Assistant conversations for the current user."""
    result = await db.execute(
        select(SellIAConversation)
        .where(
            SellIAConversation.user_id == current_user.id,
            SellIAConversation.is_active == True,
        )
        .order_by(desc(SellIAConversation.updated_at))
    )
    convs = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "title": c.title or "Nueva conversación",
            "message_count": len(c.messages) if c.messages else 0,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in convs
    ]


@router.get("/conversations/{conversation_id}", response_model=dict)
async def get_assistant_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a single SellIA conversation with all messages."""
    result = await db.execute(
        select(SellIAConversation).where(
            SellIAConversation.id == conversation_id,
            SellIAConversation.user_id == current_user.id,
            SellIAConversation.is_active == True,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {
        "id": str(conv.id),
        "title": conv.title or "Nueva conversación",
        "messages": conv.messages or [],
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
        "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
    }


@router.post("/conversations", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_assistant_conversation(
    title: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new SellIA conversation."""
    conv = SellIAConversation(
        user_id=current_user.id,
        title=title or "Nueva conversación",
        messages=[],
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return {
        "id": str(conv.id),
        "title": conv.title,
        "messages": [],
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
        "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
    }


@router.delete("/conversations/{conversation_id}", response_model=dict)
async def delete_assistant_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Soft-delete a SellIA conversation."""
    result = await db.execute(
        select(SellIAConversation).where(
            SellIAConversation.id == conversation_id,
            SellIAConversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conv.is_active = False
    await db.commit()
    return {"success": True, "message": "Conversation deleted"}


# ───────────────────────────────────────────────
# Chat endpoint
# ───────────────────────────────────────────────

@router.post("/chat", response_model=dict)
async def assistant_chat(
    message: str,
    business_id: Optional[UUID] = None,
    context: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    conversation_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Chat with SellIA Assistant to get agent suggestions and actions.

    - **message**: User's natural language input
    - **business_id**: Optional business context
    - **context**: Additional context (e.g., current page, selected agent)
    - **conversation_history**: Previous messages in the conversation (optional, used if no conversation_id)
    - **conversation_id**: Optional persistent conversation ID to load/save history
    """
    orchestrator = SellIAOrchestrator(db)

    # Load persistent conversation if provided
    sellia_conv = None
    persistent_history = []
    if conversation_id:
        result = await db.execute(
            select(SellIAConversation).where(
                SellIAConversation.id == conversation_id,
                SellIAConversation.user_id == current_user.id,
                SellIAConversation.is_active == True,
            )
        )
        sellia_conv = result.scalar_one_or_none()
        if sellia_conv and sellia_conv.messages:
            persistent_history = sellia_conv.messages[-20:]  # last 20 messages

    # Merge histories: persistent takes precedence
    merged_history = persistent_history if persistent_history else (conversation_history or [])

    result = await orchestrator.process_intent(
        user_input=message,
        user_id=current_user.id,
        business_id=str(business_id) if business_id else None,
        conversation_history=merged_history,
    )

    # If action is CREATE_CONVERSATION, actually create it
    if result.get("action") == "CREATE_CONVERSATION":
        agent_slug = result.get("agent_slug")
        if agent_slug and business_id:
            service = AgentService(db)
            # Find personality by slug
            personalities = await service.get_personalities(active_only=True)
            personality = next((p for p in personalities if p.slug == agent_slug), None)

            if personality:
                try:
                    conv = await service.create_conversation(
                        user_id=current_user.id,
                        business_id=business_id,
                        personality_id=UUID(str(personality.id)),
                        title=f"SellIA: {personality.name}",
                    )
                    result["conversation_id"] = str(conv.id)
                    result["personality"] = AgentPersonalityResponse.model_validate(personality).model_dump()
                except Exception as e:
                    result["action"] = "ASK_CLARIFICATION"
                    result["response"] = f"No pude crear la conversación. ¿Probás de nuevo? ({str(e)[:100]})"
                    result.pop("conversation_id", None)

    # Persist messages
    if sellia_conv:
        if not sellia_conv.messages:
            sellia_conv.messages = []
        sellia_conv.messages.append({
            "role": "user",
            "content": message,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        sellia_conv.messages.append({
            "role": "assistant",
            "content": result.get("response", ""),
            "action": result.get("action"),
            "suggested_agents": result.get("suggested_agents"),
            "agent_slug": result.get("agent_slug"),
            "target": result.get("target"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        # Auto-title on first exchange
        if len(sellia_conv.messages) <= 2 and (not sellia_conv.title or sellia_conv.title == "Nueva conversación"):
            sellia_conv.title = message[:60] + ("..." if len(message) > 60 else "")
        await db.commit()
        await db.refresh(sellia_conv)
        result["sellia_conversation_id"] = str(sellia_conv.id)

    return result


@router.post("/chat/stream")
async def assistant_chat_stream(
    message: str,
    business_id: Optional[UUID] = None,
    context: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    conversation_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Stream chat with SellIA Assistant using Server-Sent Events.

    Yields SSE events with JSON payload:
    - event: token → {"type": "token", "content": "..."}
    - event: action → {"type": "action", "data": {...}}
    - event: error → {"type": "error", "message": "..."}
    """
    from fastapi.responses import StreamingResponse

    orchestrator = SellIAOrchestrator(db)

    # Load persistent conversation if provided
    sellia_conv = None
    persistent_history = []
    if conversation_id:
        result = await db.execute(
            select(SellIAConversation).where(
                SellIAConversation.id == conversation_id,
                SellIAConversation.user_id == current_user.id,
                SellIAConversation.is_active == True,
            )
        )
        sellia_conv = result.scalar_one_or_none()
        if sellia_conv and sellia_conv.messages:
            persistent_history = sellia_conv.messages[-20:]

    merged_history = persistent_history if persistent_history else (conversation_history or [])

    async def event_generator():
        full_response = ""
        action_data = None

        async for event in orchestrator.process_intent_stream(
            user_input=message,
            user_id=current_user.id,
            business_id=str(business_id) if business_id else None,
            conversation_history=merged_history,
        ):
            data = json.loads(event)

            if data.get("type") == "token":
                full_response += data.get("content", "")
                yield f"event: token\ndata: {event}\n\n"
            elif data.get("type") == "action":
                action_data = data.get("data", {})
                yield f"event: action\ndata: {event}\n\n"
            elif data.get("type") == "error":
                yield f"event: error\ndata: {event}\n\n"

        # Persist messages after streaming completes
        if sellia_conv:
            if not sellia_conv.messages:
                sellia_conv.messages = []
            sellia_conv.messages.append({
                "role": "user",
                "content": message,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            sellia_conv.messages.append({
                "role": "assistant",
                "content": full_response or (action_data.get("response", "") if action_data else ""),
                "action": action_data.get("action") if action_data else None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            if len(sellia_conv.messages) <= 2 and (not sellia_conv.title or sellia_conv.title == "Nueva conversación"):
                sellia_conv.title = message[:60] + ("..." if len(message) > 60 else "")
            await db.commit()
            await db.refresh(sellia_conv)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/agents-summary", response_model=list[AgentPersonalityResponse])
async def get_agents_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a compact summary of all available agents for the assistant context."""
    service = AgentService(db)
    personalities = await service.get_personalities(active_only=True)
    return [AgentPersonalityResponse.model_validate(p) for p in personalities]
