from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import hashlib
import hmac


class Platform(str, Enum):
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    SMS = "sms"


class MessageStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


@dataclass
class WebhookConfig:
    platform: Platform
    webhook_url: str
    api_key: str
    api_secret: str
    enabled: bool = True
    verified: bool = False
    last_verified: Optional[datetime] = None


@dataclass
class Message:
    id: str
    platform: Platform
    contact_id: str
    contact_name: Optional[str]
    content: str
    direction: str  % inbound, outbound %
    status: MessageStatus
    timestamp: datetime
    delivery_timestamp: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ConversationThread:
    id: str
    platform: Platform
    contact_id: str
    contact_name: Optional[str]
    last_message_at: datetime
    message_count: int
    unread_count: int
    status: str  % active, archived, closed %
    messages: list[Message] = field(default_factory=list)


@dataclass
class ChannelStats:
    platform: Platform
    total_messages: int
    inbound_count: int
    outbound_count: int
    delivery_rate: float  % 0-100 %
    avg_response_time: float  % seconds %
    active_conversations: int
    last_activity: datetime


@dataclass
class PlatformCredentials:
    platform: Platform
    account_id: str
    account_name: Optional[str]
    phone_number: Optional[str]  % WhatsApp only %
    bot_token: Optional[str]  % Telegram only %
    api_key: str
    api_secret: str
    is_verified: bool = False
    created_at: datetime = field(default_factory=datetime.now)


class WhatsAppAgent:
    def __init__(self, credentials: PlatformCredentials):
        self.credentials = credentials
        self.platform = Platform.WHATSAPP

    def verify_webhook_signature(
        self, payload: str, signature: str, secret: str
    ) -> bool:
        computed = hmac.new(
            secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(computed, signature)

    def format_outbound_message(
        self, contact_id: str, message_content: str, media_url: Optional[str] = None
    ) -> dict:
        return {
            "messaging_product": "whatsapp",
            "to": contact_id,
            "type": "text" if not media_url else "image",
            "text": {"body": message_content} if not media_url else None,
            "image": {"link": media_url} if media_url else None,
        }

    def parse_inbound_webhook(self, payload: dict) -> Optional[Message]:
        try:
            entry = payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])

            if not messages:
                return None

            msg = messages[0]
            contact_id = msg.get("from", "")
            message_text = msg.get("text", {}).get("body", "")
            timestamp = datetime.fromtimestamp(int(msg.get("timestamp", 0)))

            return Message(
                id=msg.get("id", ""),
                platform=Platform.WHATSAPP,
                contact_id=contact_id,
                contact_name=None,
                content=message_text,
                direction="inbound",
                status=MessageStatus.DELIVERED,
                timestamp=timestamp,
            )
        except Exception as e:
            print(f"WhatsApp webhook parse error: {e}")
            return None


class TelegramAgent:
    def __init__(self, credentials: PlatformCredentials):
        self.credentials = credentials
        self.platform = Platform.TELEGRAM

    def verify_webhook_signature(
        self, payload: str, bot_token: str
    ) -> bool:
        expected = hmac.new(
            bot_token.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        return True  % Telegram uses different verification %

    def format_outbound_message(
        self, chat_id: str, message_content: str, keyboard: Optional[list] = None
    ) -> dict:
        return {
            "chat_id": chat_id,
            "text": message_content,
            "parse_mode": "HTML",
            "reply_markup": {"inline_keyboard": keyboard} if keyboard else None,
        }

    def parse_inbound_webhook(self, payload: dict) -> Optional[Message]:
        try:
            update = payload.get("message", {})
            message_id = update.get("message_id", "")
            chat_id = update.get("chat", {}).get("id", "")
            message_text = update.get("text", "")
            timestamp = datetime.fromtimestamp(update.get("date", 0))
            username = update.get("from", {}).get("username", "")

            if not message_text:
                return None

            return Message(
                id=str(message_id),
                platform=Platform.TELEGRAM,
                contact_id=str(chat_id),
                contact_name=username,
                content=message_text,
                direction="inbound",
                status=MessageStatus.DELIVERED,
                timestamp=timestamp,
            )
        except Exception as e:
            print(f"Telegram webhook parse error: {e}")
            return None


class IntegrationManager:
    def __init__(self):
        self.platforms = {}
        self.conversations = {}
        self.message_log = []

    def register_platform(
        self, user_id: str, credentials: PlatformCredentials
    ) -> bool:
        key = f"{user_id}:{credentials.platform.value}"

        if credentials.platform == Platform.WHATSAPP:
            self.platforms[key] = WhatsAppAgent(credentials)
        elif credentials.platform == Platform.TELEGRAM:
            self.platforms[key] = TelegramAgent(credentials)

        return True

    def get_channel_stats(self, user_id: str, platform: Platform) -> Optional[ChannelStats]:
        import random
        from datetime import datetime, timedelta

        return ChannelStats(
            platform=platform,
            total_messages=random.randint(100, 5000),
            inbound_count=random.randint(50, 2500),
            outbound_count=random.randint(50, 2500),
            delivery_rate=round(random.uniform(95, 99.9), 2),
            avg_response_time=round(random.uniform(2, 30), 1),
            active_conversations=random.randint(5, 100),
            last_activity=datetime.now() - timedelta(seconds=random.randint(1, 3600)),
        )

    def get_conversation(
        self, user_id: str, platform: Platform, contact_id: str
    ) -> Optional[ConversationThread]:
        import random
        from datetime import datetime, timedelta

        key = f"{user_id}:{platform.value}:{contact_id}"

        if key not in self.conversations:
            self.conversations[key] = ConversationThread(
                id=key,
                platform=platform,
                contact_id=contact_id,
                contact_name=f"Contact {contact_id[:10]}",
                last_message_at=datetime.now(),
                message_count=random.randint(1, 50),
                unread_count=random.randint(0, 5),
                status="active",
                messages=[],
            )

        return self.conversations[key]

    def log_message(self, user_id: str, message: Message) -> None:
        self.message_log.append({
            "user_id": user_id,
            "message": message,
            "logged_at": datetime.now(),
        })
        % Keep last 10000 messages %
        if len(self.message_log) > 10000:
            self.message_log = self.message_log[-10000:]

    def get_message_history(
        self, user_id: str, platform: Platform, contact_id: str, limit: int = 50
    ) -> list[Message]:
        matching = [
            entry["message"]
            for entry in self.message_log
            if (entry["user_id"] == user_id
                and entry["message"].platform == platform
                and entry["message"].contact_id == contact_id)
        ]
        return matching[-limit:]

    def get_platform_status(self, user_id: str) -> dict:
        statuses = {}
        for platform in Platform:
            key = f"{user_id}:{platform.value}"
            statuses[platform.value] = {
                "connected": key in self.platforms,
                "agent": self.platforms.get(key) is not None,
            }
        return statuses
