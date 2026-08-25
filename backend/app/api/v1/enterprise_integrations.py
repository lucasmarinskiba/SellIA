from fastapi import APIRouter, Query, Body
from datetime import datetime
from app.domains.enterprise.integrations import (
    IntegrationManager,
    Platform,
    PlatformCredentials,
    Message,
)

router = APIRouter(tags=["integrations"])
integration_manager = IntegrationManager()


@router.post("/integrations/connect")
async def connect_platform(
    user_id: str = Query(..., description="User ID"),
    platform: str = Query(..., description="whatsapp or telegram"),
    account_id: str = Query(...),
    api_key: str = Query(...),
    api_secret: str = Query(...),
    phone_number: str = Query(None, description="WhatsApp only"),
    bot_token: str = Query(None, description="Telegram only"),
):
    """Connect WhatsApp or Telegram platform."""
    try:
        platform_enum = Platform(platform)
        credentials = PlatformCredentials(
            platform=platform_enum,
            account_id=account_id,
            phone_number=phone_number,
            bot_token=bot_token,
            api_key=api_key,
            api_secret=api_secret,
            is_verified=True,
        )

        success = integration_manager.register_platform(user_id, credentials)

        return {
            "status": "connected" if success else "failed",
            "platform": platform,
            "account_id": account_id,
            "message": f"{platform.title()} integration connected successfully",
        }
    except ValueError:
        return {"status": "error", "message": f"Invalid platform: {platform}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/integrations/status/{user_id}")
async def get_platform_status(user_id: str):
    """Get connection status for all platforms."""
    status = integration_manager.get_platform_status(user_id)

    return {
        "user_id": user_id,
        "platforms": {
            "whatsapp": status.get("whatsapp", {"connected": False}),
            "telegram": status.get("telegram", {"connected": False}),
        },
    }


@router.get("/integrations/stats/{user_id}")
async def get_integration_stats(
    user_id: str, platform: str = Query("whatsapp", description="Platform name")
):
    """Get statistics for platform activity."""
    try:
        platform_enum = Platform(platform)
        stats = integration_manager.get_channel_stats(user_id, platform_enum)

        return {
            "platform": platform,
            "stats": {
                "total_messages": stats.total_messages,
                "inbound": stats.inbound_count,
                "outbound": stats.outbound_count,
                "delivery_rate": f"{stats.delivery_rate}%",
                "avg_response_time": f"{stats.avg_response_time}s",
                "active_conversations": stats.active_conversations,
                "last_activity": stats.last_activity.isoformat(),
            },
        }
    except ValueError:
        return {"status": "error", "message": f"Invalid platform: {platform}"}


@router.get("/integrations/conversations/{user_id}")
async def list_conversations(
    user_id: str,
    platform: str = Query("whatsapp"),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
):
    """List active conversations on platform."""
    try:
        platform_enum = Platform(platform)

        # Mock conversation list
        conversations = []
        for i in range(limit):
            contact_id = f"contact_{offset + i}"
            conv = integration_manager.get_conversation(
                user_id, platform_enum, contact_id
            )
            conversations.append({
                "contact_id": conv.contact_id,
                "contact_name": conv.contact_name,
                "last_message_at": conv.last_message_at.isoformat(),
                "message_count": conv.message_count,
                "unread_count": conv.unread_count,
                "status": conv.status,
            })

        return {
            "platform": platform,
            "total": 100 + offset,
            "limit": limit,
            "offset": offset,
            "conversations": conversations,
        }
    except ValueError:
        return {"status": "error", "message": f"Invalid platform: {platform}"}


@router.get("/integrations/messages/{user_id}")
async def get_conversation_messages(
    user_id: str,
    platform: str = Query("whatsapp"),
    contact_id: str = Query(...),
    limit: int = Query(50, le=100),
):
    """Get message history for conversation."""
    try:
        platform_enum = Platform(platform)
        messages = integration_manager.get_message_history(
            user_id, platform_enum, contact_id, limit
        )

        return {
            "platform": platform,
            "contact_id": contact_id,
            "message_count": len(messages),
            "messages": [
                {
                    "id": msg.id,
                    "direction": msg.direction,
                    "content": msg.content,
                    "status": msg.status.value,
                    "timestamp": msg.timestamp.isoformat(),
                }
                for msg in messages
            ],
        }
    except ValueError:
        return {"status": "error", "message": f"Invalid platform: {platform}"}


@router.post("/integrations/send-message")
async def send_message(
    user_id: str = Query(...),
    platform: str = Query(...),
    contact_id: str = Query(...),
    content: str = Body(..., description="Message content"),
):
    """Send message via integrated platform."""
    try:
        platform_enum = Platform(platform)
        key = f"{user_id}:{platform_enum.value}"

        if key not in integration_manager.platforms:
            return {"status": "error", "message": f"Platform not connected"}

        agent = integration_manager.platforms[key]

        # Create message record
        message = Message(
            id=f"msg_{datetime.now().timestamp()}",
            platform=platform_enum,
            contact_id=contact_id,
            contact_name=None,
            content=content,
            direction="outbound",
            status="sent",
            timestamp=datetime.now(),
        )

        integration_manager.log_message(user_id, message)

        return {
            "status": "sent",
            "platform": platform,
            "contact_id": contact_id,
            "message_id": message.id,
            "timestamp": message.timestamp.isoformat(),
        }
    except ValueError:
        return {"status": "error", "message": f"Invalid platform: {platform}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/integrations/webhook/{platform}")
async def receive_webhook(
    platform: str,
    user_id: str = Query(...),
    payload: dict = Body(...),
):
    """Receive incoming messages via webhooks."""
    try:
        platform_enum = Platform(platform)
        key = f"{user_id}:{platform_enum.value}"

        if key not in integration_manager.platforms:
            return {"status": "error", "message": "Platform not configured"}

        agent = integration_manager.platforms[key]
        message = agent.parse_inbound_webhook(payload)

        if message:
            integration_manager.log_message(user_id, message)
            return {
                "status": "received",
                "message_id": message.id,
                "contact_id": message.contact_id,
                "platform": platform,
            }
        else:
            return {"status": "no_message"}
    except ValueError:
        return {"status": "error", "message": f"Invalid platform: {platform}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
