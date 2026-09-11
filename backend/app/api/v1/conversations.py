from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
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
    platform: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List real conversations for a business -- this is what proves the AI
    reply bot is actually running on each connected channel (WhatsApp,
    Instagram, MercadoLibre questions, Amazon, Hotmart, ...): each item
    shows the real platform, whether the AI has replied at all
    (ai_responded), and whether the LAST message is still waiting on a
    reply (last_direction == "inbound") or was already answered.
    """
    from app.domains.channels.models import ChannelConnection

    await _get_business_for_user(business_id, current_user, db)
    query = (
        select(Conversation, ChannelConnection)
        # Eager-load: the loop below reads conv.messages, and a lazy load in an
        # async request raises MissingGreenlet (SQLAlchemy refuses to do IO
        # from the sync attribute-access path). This endpoint answered 500 for
        # every account that actually had a conversation.
        .options(selectinload(Conversation.messages))
        .outerjoin(ChannelConnection, Conversation.channel_connection_id == ChannelConnection.id)
        .where(
            Conversation.business_id == business_id,
            Conversation.is_active == True,
        )
    )
    if status:
        query = query.where(Conversation.status == status)
    if platform:
        query = query.where(ChannelConnection.platform == platform)
    query = query.order_by(Conversation.last_message_at.desc().nullslast())
    result = await db.execute(query)
    rows = result.all()

    response = []
    for conv, channel in rows:
        msgs = conv.messages
        msg_count = len(msgs)
        last_preview = None
        last_direction = None
        if msgs:
            last_msg = msgs[-1]
            last_preview = last_msg.content[:100] if last_msg.content else None
            last_direction = last_msg.direction.value if hasattr(last_msg.direction, "value") else last_msg.direction
        ai_responded = any(
            (m.direction.value if hasattr(m.direction, "value") else m.direction) == "outbound"
            for m in msgs
        )
        response.append(ConversationListResponse(
            **ConversationResponse.model_validate(conv).model_dump(),
            message_count=msg_count,
            last_message_preview=last_preview,
            platform=channel.platform.value if channel and channel.platform else None,
            last_direction=last_direction,
            ai_responded=ai_responded,
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
            await send_outbound_message(
                db, conversation_id, message_in.content, message_in.content_type,
                # Credits the reply to whoever is logged in, so a team can
                # see who is actually answering customers.
                sent_by_user_id=current_user.id,
            )
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Failed to send outbound message: {e}")

    return message
