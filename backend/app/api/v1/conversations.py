from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from typing import Any

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.channels.models import (
    Conversation, Message, ConversationStatus, MessageDirection, MessageStatus
)
from app.domains.channels.schemas import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    ConversationListResponse, MessageCreate, MessageResponse,
)

router = APIRouter()


async def _get_business_for_user(
    business_id: UUID, user: User, db: AsyncSession
) -> Business:
    result = await db.execute(
        select(Business).where(
            Business.id == business_id,
            Business.user_id == user.id,
            Business.is_active == True,
        )
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    return business


@router.get("/{business_id}/conversations", response_model=list[ConversationListResponse])
async def list_conversations(
    business_id: UUID,
    status: ConversationStatus | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    query = select(Conversation).where(
        Conversation.business_id == business_id,
        Conversation.is_active == True,
    )
    if status:
        query = query.where(Conversation.status == status)
    query = query.order_by(Conversation.last_message_at.desc().nullslast())
    result = await db.execute(query)
    conversations = result.scalars().all()

    response = []
    for conv in conversations:
        msg_count = len(conv.messages)
        last_preview = None
        if conv.messages:
            last_preview = conv.messages[-1].content[:100] if conv.messages[-1].content else None
        response.append(ConversationListResponse(
            **ConversationResponse.model_validate(conv).model_dump(),
            message_count=msg_count,
            last_message_preview=last_preview,
        ))
    return response


@router.get("/{business_id}/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    business_id: UUID,
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.business_id == business_id,
            Conversation.is_active == True,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return conversation


@router.put("/{business_id}/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    business_id: UUID,
    conversation_id: UUID,
    conv_in: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.business_id == business_id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    update_data = conv_in.model_dump(exclude_unset=True)
    if "extra_data" in update_data and conversation.extra_data:
        update_data["extra_data"] = {**conversation.extra_data, **update_data["extra_data"]}

    for field, value in update_data.items():
        setattr(conversation, field, value)

    await db.commit()
    await db.refresh(conversation)
    return conversation


@router.get("/{business_id}/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    business_id: UUID,
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    result = await db.execute(
        select(Message).where(
            Message.conversation_id == conversation_id,
        ).order_by(Message.created_at.asc())
    )
    return result.scalars().all()


@router.post("/{business_id}/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    business_id: UUID,
    conversation_id: UUID,
    message_in: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.business_id == business_id,
            Conversation.is_active == True,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    message = Message(
        conversation_id=conversation_id,
        direction=message_in.direction,
        content=message_in.content,
        content_type=message_in.content_type,
        extra_data=message_in.extra_data or {},
    )
    db.add(message)

    conversation.last_message_at = message.created_at
    await db.commit()
    await db.refresh(message)

    # Send outbound message via channel connector
    if message_in.direction == MessageDirection.OUTBOUND:
        try:
            from app.domains.channels.services import send_outbound_message
            await send_outbound_message(db, conversation_id, message_in.content, message_in.content_type)
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Failed to send outbound message: {e}")

    return message
