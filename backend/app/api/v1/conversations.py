from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
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

    now = datetime.now(timezone.utc)
    # Taken before anything can roll back. A rollback expires every loaded
    # instance, so reading current_user.id afterwards lazy-loads inside async
    # code and raises MissingGreenlet — which is what it did, at the line that
    # records who wrote the reply.
    author_id = current_user.id

    # An outbound reply is written by send_outbound_message, which sends it AND
    # records the row — including who typed it. This endpoint used to create its
    # own row first and then call that function, so every manually typed reply
    # was stored TWICE: the history showed each message doubled and every count
    # built on messages (the team board, the bot stats, the analyst's reply
    # counts) was inflated. One writer now.
    if message_in.direction == MessageDirection.OUTBOUND:
        from app.domains.channels.services import send_outbound_message

        try:
            await send_outbound_message(
                db, conversation_id, message_in.content, message_in.content_type,
                # Credits the reply to whoever is logged in, so a team can see
                # who is actually answering customers.
                sent_by_user_id=author_id,
            )
            result = await db.execute(
                select(Message)
                .where(
                    Message.conversation_id == conversation_id,
                    Message.direction == MessageDirection.OUTBOUND,
                )
                .order_by(Message.created_at.desc())
                .limit(1)
            )
            sent = result.scalar_one_or_none()
            if sent is not None:
                return sent
        except Exception as e:
            from app.core.logger import get_logger

            get_logger(__name__).error(f"Failed to send outbound message: {e}")
            await db.rollback()
            # The rollback expires every loaded instance, so `conversation` has
            # to be read again before it is touched: reading an attribute off the
            # expired one lazy-loads inside async code and raises MissingGreenlet
            # — which is exactly how this endpoint started answering 500.
            conversation = await db.get(Conversation, conversation_id)
            if conversation is None:
                raise HTTPException(status_code=404, detail="Conversación no encontrada")
            # The send failed, but the seller's words are not thrown away: the
            # row is kept, attributed, and flagged as undelivered so the inbox
            # can show that it never reached the customer.
            extra = dict(message_in.extra_data or {})
            extra["sent_by_user_id"] = str(author_id)
            extra["delivery_failed"] = str(e)[:300]
            message = Message(
                conversation_id=conversation_id,
                direction=MessageDirection.OUTBOUND,
                content=message_in.content,
                content_type=message_in.content_type,
                status=MessageStatus.FAILED,
                extra_data=extra,
                created_at=now,
            )
            db.add(message)
            conversation.last_message_at = now
            await db.commit()
            await db.refresh(message)
            return message

    # Inbound messages logged by hand (a call, a walk-in) are written here.
    message = Message(
        conversation_id=conversation_id,
        direction=message_in.direction,
        content=message_in.content,
        content_type=message_in.content_type,
        extra_data=message_in.extra_data or {},
        created_at=now,
    )
    db.add(message)
    # Explicit timestamp: message.created_at is still None before the flush, so
    # assigning it here used to leave last_message_at empty.
    conversation.last_message_at = now
    await db.commit()
    await db.refresh(message)
    return message
