"""
Telegram Automation — Bot API, commands, push notifications, deep linking.

Bot Commands:
- /start → Welcome message, main menu
- /status → Order status check
- /orders → List recent orders with buttons
- /settings → User preferences
- /help → Help menu

Push Notifications:
- New orders
- Payment confirmations
- Shipment tracking
- Customer inquiries

Deep Linking:
- tg://resolve?domain=botname&start=order_12345 → Shows specific order
- Shareable product links

Rate Limit: 30 messages/second per bot
Polling fallback: If webhook fails, use polling every 30 seconds
"""

import logging
import httpx
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)


class TelegramCommandType(Enum):
    """Telegram bot commands."""
    START = "start"
    STATUS = "status"
    ORDERS = "orders"
    SETTINGS = "settings"
    HELP = "help"


class TelegramMessageType(Enum):
    """Telegram message types."""
    TEXT = "text"
    PHOTO = "photo"
    DOCUMENT = "document"
    COMMAND = "command"
    NOTIFICATION = "notification"


class TelegramAutomation:
    """Telegram bot complete automation."""

    TELEGRAM_API = "https://api.telegram.org"
    TIMEOUT = 30

    def __init__(
        self,
        bot_token: str,
        webhook_url: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        """
        Initialize Telegram automation.

        Args:
            bot_token: Telegram bot token (encrypted in production)
            webhook_url: Optional webhook URL for receiving updates
            webhook_secret: Optional secret for webhook verification
        """
        self.bot_token = bot_token
        self.webhook_url = webhook_url
        self.webhook_secret = webhook_secret
        self.http_client = httpx.AsyncClient(timeout=self.TIMEOUT)
        self.api_url = f"{self.TELEGRAM_API}/bot{self.bot_token}"

    # ========== WEBHOOK SETUP ==========

    async def set_webhook(self, webhook_url: str) -> bool:
        """
        Register webhook endpoint with Telegram.

        Args:
            webhook_url: URL where Telegram sends updates

        Returns:
            Success boolean
        """
        try:
            logger.info(f"Setting webhook: {webhook_url}")

            url = f"{self.api_url}/setWebhook"
            payload = {
                "url": webhook_url,
                "secret_token": self.webhook_secret or "",
                "allowed_updates": [
                    "message",
                    "callback_query",
                    "inline_query",
                ],
            }

            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()

            if data.get("ok"):
                logger.info("Webhook set successfully")
                return True
            else:
                logger.error(f"Webhook error: {data.get('description')}")
                return False

        except httpx.HTTPError as e:
            logger.error(f"Error setting webhook: {e}")
            return False

    async def remove_webhook(self) -> bool:
        """Remove webhook and switch to polling."""
        try:
            url = f"{self.api_url}/deleteWebhook"
            response = await self.http_client.post(url)
            response.raise_for_status()

            data = response.json()
            return data.get("ok", False)

        except httpx.HTTPError as e:
            logger.error(f"Error removing webhook: {e}")
            return False

    # ========== UPDATE HANDLING ==========

    async def handle_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming Telegram update.

        Update structure:
        {
          "update_id": 123456789,
          "message": {
            "message_id": 1,
            "from": {"id": 987654321, "username": "john_doe"},
            "chat": {"id": 987654321, "type": "private"},
            "text": "/status"
          }
        }

        Args:
            update: Telegram update payload

        Returns:
            Processing result
        """
        try:
            update_id = update.get("update_id")
            message = update.get("message")
            callback_query = update.get("callback_query")

            logger.info(f"Processing update {update_id}")

            if message:
                return await self._handle_message(message)
            elif callback_query:
                return await self._handle_callback_query(callback_query)

            return {"status": "ok"}

        except Exception as e:
            logger.error(f"Error handling update: {e}")
            return {"status": "error", "message": str(e)}

    async def _handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming message."""
        chat_id = message.get("chat", {}).get("id")
        from_user = message.get("from", {})
        text = message.get("text", "")

        logger.info(f"Message from {from_user.get('username')}: {text}")

        # Check if message is a command
        if text.startswith("/"):
            command = text.split()[0][1:]  # Remove /
            return await self.handle_command(command, chat_id, from_user)
        else:
            # Regular message - could be a response to previous prompt
            return await self._handle_regular_message(text, chat_id, from_user)

    async def _handle_regular_message(
        self,
        text: str,
        chat_id: int,
        user: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle non-command message."""
        # Could be order inquiry, search query, etc
        response = await self.send_message(
            chat_id,
            f"I didn't understand that. Type /help for available commands.",
        )
        return {"status": "ok"}

    async def _handle_callback_query(
        self,
        callback_query: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle inline button callback."""
        query_id = callback_query.get("id")
        chat_id = callback_query.get("from", {}).get("id")
        data = callback_query.get("data")

        logger.info(f"Callback query: {data}")

        # Answer callback to remove loading state
        await self._answer_callback_query(query_id)

        # Handle the action
        if data.startswith("order_"):
            order_id = data.split("_")[1]
            return await self._handle_order_query(order_id, chat_id)
        elif data.startswith("setting_"):
            setting = data.split("_")[1]
            return await self._handle_setting_update(setting, chat_id)

        return {"status": "ok"}

    # ========== COMMAND HANDLING ==========

    async def handle_command(
        self,
        command: str,
        chat_id: int,
        user: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Handle slash command.

        Args:
            command: Command name (without /)
            chat_id: Telegram chat ID
            user: User information dict

        Returns:
            Command result
        """
        try:
            logger.info(f"Processing command: /{command} from chat {chat_id}")

            if command == TelegramCommandType.START.value:
                return await self._handle_start_command(chat_id, user)
            elif command == TelegramCommandType.STATUS.value:
                return await self._handle_status_command(chat_id, user)
            elif command == TelegramCommandType.ORDERS.value:
                return await self._handle_orders_command(chat_id, user)
            elif command == TelegramCommandType.SETTINGS.value:
                return await self._handle_settings_command(chat_id, user)
            elif command == TelegramCommandType.HELP.value:
                return await self._handle_help_command(chat_id)
            else:
                return await self.send_message(
                    chat_id,
                    f"Unknown command: /{command}\nType /help for available commands.",
                )

        except Exception as e:
            logger.error(f"Error handling command: {e}")
            return await self.send_message(
                chat_id,
                f"Error processing command: {str(e)}",
            )

    async def _handle_start_command(
        self,
        chat_id: int,
        user: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle /start command."""
        first_name = user.get("first_name", "User")

        keyboard = {
            "keyboard": [
                [{"text": "Status"}, {"text": "Orders"}],
                [{"text": "Settings"}, {"text": "Help"}],
            ],
            "resize_keyboard": True,
        }

        return await self.send_message(
            chat_id,
            f"Welcome, {first_name}! 👋\n\n"
            f"I'm your order assistant. Use the buttons below or type commands:\n"
            f"/status - Check order status\n"
            f"/orders - View recent orders\n"
            f"/settings - Configure preferences\n"
            f"/help - Show all commands",
            reply_markup=keyboard,
        )

    async def _handle_status_command(
        self,
        chat_id: int,
        user: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle /status command."""
        # Fetch real status from DB
        status_text = (
            "📊 *Today's Status*\n\n"
            "📦 Orders: 5\n"
            "💰 Revenue: $250.00\n"
            "⏳ Pending: 2\n"
            "✅ Completed: 3"
        )

        return await self.send_message(
            chat_id,
            status_text,
            parse_mode="Markdown",
        )

    async def _handle_orders_command(
        self,
        chat_id: int,
        user: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle /orders command."""
        # Create inline keyboard with recent orders
        keyboard = {
            "inline_keyboard": [
                [{"text": "Order #12345 - $99.99", "callback_data": "order_12345"}],
                [{"text": "Order #12344 - $149.99", "callback_data": "order_12344"}],
                [{"text": "Order #12343 - $79.99", "callback_data": "order_12343"}],
            ],
        }

        return await self.send_message(
            chat_id,
            "📋 *Recent Orders*\n\nClick on an order to see details:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

    async def _handle_settings_command(
        self,
        chat_id: int,
        user: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle /settings command."""
        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "🔔 Notifications: ON",
                        "callback_data": "setting_notifications",
                    }
                ],
                [
                    {
                        "text": "🌍 Language: English",
                        "callback_data": "setting_language",
                    }
                ],
                [
                    {
                        "text": "⏰ Timezone: UTC",
                        "callback_data": "setting_timezone",
                    }
                ],
            ],
        }

        return await self.send_message(
            chat_id,
            "⚙️ *Settings*\n\nTap to change settings:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

    async def _handle_help_command(self, chat_id: int) -> Dict[str, Any]:
        """Handle /help command."""
        help_text = (
            "📚 *Available Commands*\n\n"
            "/start - Welcome & main menu\n"
            "/status - Check today's status\n"
            "/orders - View recent orders\n"
            "/settings - Configure preferences\n"
            "/help - Show this message"
        )

        return await self.send_message(
            chat_id,
            help_text,
            parse_mode="Markdown",
        )

    async def _handle_order_query(self, order_id: str, chat_id: int) -> Dict[str, Any]:
        """Handle order details query."""
        # Fetch order from DB
        order_text = (
            f"📦 *Order #{order_id}*\n\n"
            f"Customer: John Doe\n"
            f"Amount: $99.99\n"
            f"Status: 🚚 Shipped\n"
            f"Tracking: 1Z999AA10123456784"
        )

        return await self.send_message(
            chat_id,
            order_text,
            parse_mode="Markdown",
        )

    async def _handle_setting_update(
        self,
        setting: str,
        chat_id: int,
    ) -> Dict[str, Any]:
        """Handle setting update."""
        logger.info(f"Updating setting: {setting}")

        return await self.send_message(
            chat_id,
            f"✅ Setting '{setting}' updated!",
        )

    # ========== MESSAGE SENDING ==========

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict[str, Any]] = None,
        disable_notification: bool = False,
    ) -> Dict[str, Any]:
        """
        Send text message to user.

        Args:
            chat_id: Telegram chat ID
            text: Message text
            parse_mode: HTML or Markdown
            reply_markup: Keyboard markup
            disable_notification: Don't notify user

        Returns:
            API response
        """
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_notification": disable_notification,
            }

            if reply_markup:
                payload["reply_markup"] = reply_markup

            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Error sending message: {e}")
            return {"ok": False, "error": str(e)}

    async def send_notification(
        self,
        chat_id: int,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send notification message.

        Args:
            chat_id: Telegram chat ID
            title: Notification title
            message: Notification message
            data: Optional data to include

        Returns:
            Success boolean
        """
        try:
            text = f"🔔 *{title}*\n\n{message}"

            if data:
                for key, value in data.items():
                    text += f"\n{key}: {value}"

            result = await self.send_message(
                chat_id,
                text,
                parse_mode="Markdown",
                disable_notification=False,
            )

            return result.get("ok", False)

        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False

    async def send_order_notification(
        self,
        chat_id: int,
        order_id: str,
        status: str,
    ) -> bool:
        """Send order status notification."""
        return await self.send_notification(
            chat_id,
            "Order Update",
            f"Order #{order_id} status: {status}",
            {"Time": datetime.utcnow().isoformat()},
        )

    async def send_payment_notification(
        self,
        chat_id: int,
        amount: float,
        order_id: str,
    ) -> bool:
        """Send payment confirmation notification."""
        return await self.send_notification(
            chat_id,
            "Payment Confirmed",
            f"Payment of ${amount:.2f} received",
            {"Order": order_id},
        )

    # ========== CALLBACK HANDLING ==========

    async def _answer_callback_query(
        self,
        query_id: str,
        text: str = "Processing...",
        show_alert: bool = False,
    ) -> bool:
        """
        Answer inline button callback query.

        Shows popup/toast notification.

        Args:
            query_id: Callback query ID
            text: Notification text
            show_alert: Show as alert (True) or toast (False)

        Returns:
            Success boolean
        """
        try:
            url = f"{self.api_url}/answerCallbackQuery"
            payload = {
                "callback_query_id": query_id,
                "text": text,
                "show_alert": show_alert,
            }

            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()

            return response.json().get("ok", False)

        except httpx.HTTPError as e:
            logger.error(f"Error answering callback: {e}")
            return False

    # ========== POLLING FALLBACK ==========

    async def poll_updates(self, last_update_id: int = 0) -> List[Dict[str, Any]]:
        """
        Poll for updates (fallback if webhook unavailable).

        Args:
            last_update_id: Last processed update ID

        Returns:
            List of new updates
        """
        try:
            url = f"{self.api_url}/getUpdates"
            params = {
                "offset": last_update_id + 1,
                "timeout": 30,  # Long polling
            }

            response = await self.http_client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if data.get("ok"):
                return data.get("result", [])
            else:
                logger.error(f"Poll error: {data.get('description')}")
                return []

        except httpx.HTTPError as e:
            logger.error(f"Error polling updates: {e}")
            return []

    # ========== BOT INFO & MANAGEMENT ==========

    async def get_bot_info(self) -> Optional[Dict[str, Any]]:
        """Fetch bot information."""
        try:
            url = f"{self.api_url}/getMe"
            response = await self.http_client.post(url)
            response.raise_for_status()

            data = response.json()

            if data.get("ok"):
                return data.get("result")
            else:
                logger.error(f"Error getting bot info: {data.get('description')}")
                return None

        except httpx.HTTPError as e:
            logger.error(f"Error fetching bot info: {e}")
            return None

    async def set_commands(self, commands: List[Dict[str, str]]) -> bool:
        """
        Set bot commands menu.

        Args:
            commands: List of {command, description} dicts

        Returns:
            Success boolean
        """
        try:
            url = f"{self.api_url}/setMyCommands"
            payload = {"commands": commands}

            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()

            return response.json().get("ok", False)

        except httpx.HTTPError as e:
            logger.error(f"Error setting commands: {e}")
            return False
