"""Channel setup — what the account can connect, and what it really has connected.

app/api/v1/channels.py already does the work (create, test, OAuth, webhooks) but
it is addressed per business_id and returns raw rows, so the dashboard had no
single place to answer the question the user actually asks: "¿qué plataformas
puedo conectar, cuáles tengo andando, y qué me falta en cada una?".

Everything here is per-account and states the truth about each connection,
including which required credential is still missing (by the connector's own
definition) and whether the webhook has ever received anything.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.logger import get_logger
from app.domains.channels.catalog import catalog_entries, mask_credentials, missing_required
from app.domains.users.models import User

router = APIRouter(prefix="/channel-setup", tags=["Channel Setup"])
logger = get_logger(__name__)


@router.get("/catalog")
async def get_catalog(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Every connectable platform, merged with this account's real state."""
    from app.domains.businesses.models import Business
    from app.domains.channels.models import (
        ChannelConnection, Conversation, Message, MessageDirection,
    )

    biz_result = await db.execute(select(Business.id, Business.name).where(Business.user_id == user.id))
    businesses = biz_result.all()
    business_ids = [b[0] for b in businesses]

    connections: dict[str, dict[str, Any]] = {}
    if business_ids:
        conn_result = await db.execute(
            select(ChannelConnection).where(ChannelConnection.business_id.in_(business_ids))
        )
        for conn in conn_result.scalars().all():
            platform = conn.platform.value if hasattr(conn.platform, "value") else str(conn.platform)

            # Real traffic on this connection -- the only proof it works.
            counts = await db.execute(
                select(
                    func.count(Conversation.id.distinct()),
                    func.count(Message.id).filter(Message.direction == MessageDirection.INBOUND),
                    func.count(Message.id).filter(Message.direction == MessageDirection.OUTBOUND),
                )
                .select_from(Conversation)
                .outerjoin(Message, Message.conversation_id == Conversation.id)
                .where(Conversation.channel_connection_id == conn.id)
            )
            conversations, inbound, outbound = counts.one_or_none() or (0, 0, 0)

            connections[platform] = {
                "id": str(conn.id),
                "business_id": str(conn.business_id),
                "name": conn.name,
                "status": conn.status.value if hasattr(conn.status, "value") else str(conn.status),
                "status_message": conn.status_message,
                "is_active": bool(conn.is_active),
                "webhook_url": conn.webhook_url,
                "last_sync_at": conn.last_sync_at.isoformat() if conn.last_sync_at else None,
                "credentials": mask_credentials(conn.credentials),
                "missing_required": missing_required(platform, conn.credentials),
                "traffic": {
                    "conversations": conversations or 0,
                    "inbound_messages": inbound or 0,
                    "outbound_messages": outbound or 0,
                },
                "created_at": conn.created_at.isoformat() if conn.created_at else None,
            }

    entries = []
    for entry in catalog_entries():
        connection = connections.get(entry["platform"])
        entries.append({
            **entry,
            "connection": connection,
            # "Conectado" is not a checkbox: it means credentials complete AND
            # the platform has actually delivered or accepted a message.
            "state": _state_for(connection),
        })

    return {
        "business_id": str(business_ids[0]) if business_ids else None,
        "business_name": businesses[0][1] if businesses else None,
        "platforms": entries,
        "connected_count": sum(1 for e in entries if e["state"] == "live"),
    }


def _state_for(connection: dict[str, Any] | None) -> str:
    if connection is None:
        return "not_connected"
    if connection["missing_required"]:
        return "incomplete"
    if connection["traffic"]["inbound_messages"] or connection["traffic"]["outbound_messages"]:
        return "live"
    return "configured"
