"""WhatsApp Web Platform Script — Browser automation for WhatsApp Web"""

from typing import List, Dict, Any
from .base import PlatformScript, ScriptStep


class WhatsAppWebScript(PlatformScript):
    domain = "web.whatsapp.com"
    platform_name = "WhatsApp Web"
    login_url = "https://web.whatsapp.com/"
    dashboard_url = "https://web.whatsapp.com/"

    def get_task_steps(self, task_type: str, params: Dict[str, Any]) -> List[ScriptStep]:
        if task_type == "respond_message":
            return self._respond_message(params)
        elif task_type == "send_message":
            return self._send_message(params)
        elif task_type == "check_unread":
            return self._check_unread(params)
        return super().get_task_steps(task_type, params)

    def _respond_message(self, params: Dict[str, Any]) -> List[ScriptStep]:
        """Respond to specific WhatsApp message."""
        customer_name = params.get("customer_name", "")
        response_text = params.get("response_text", "")

        return [
            ScriptStep(action="navigate", target="https://web.whatsapp.com/", description="Navigate to WhatsApp Web"),
            ScriptStep(action="wait", wait_ms=3000, description="Wait for page load"),

            # Search for contact
            ScriptStep(action="click", target="[title*='Search'], div[role='search']", description="Click search box"),
            ScriptStep(action="type", target="[title*='Search'], input[placeholder*='Search']", value=customer_name, description=f"Search for {customer_name}"),
            ScriptStep(action="wait", wait_ms=1500, description="Wait for search results"),

            # Click first result
            ScriptStep(action="click", target="div[role='listitem']:first-child", description="Click contact"),
            ScriptStep(action="wait", wait_ms=2000, description="Wait for chat to open"),

            # Find message input and type
            ScriptStep(action="click", target="footer [title='Add a message'], div[contenteditable='true']", description="Click message input"),
            ScriptStep(action="type", target="footer [title='Add a message'], div[contenteditable='true']", value=response_text, description="Type response message"),
            ScriptStep(action="wait", wait_ms=500),

            # Send message
            ScriptStep(action="click", target="button[aria-label='Send'], span[aria-label='Send']", description="Click send button"),
            ScriptStep(action="wait", wait_ms=2000, description="Wait for message to send"),

            ScriptStep(action="screenshot", description="Verify message sent"),
        ]

    def _send_message(self, params: Dict[str, Any]) -> List[ScriptStep]:
        """Send message to specific contact."""
        phone_number = params.get("phone_number", "")
        message_text = params.get("message_text", "")

        return [
            ScriptStep(action="navigate", target=f"https://web.whatsapp.com/send?phone={phone_number}", description=f"Open chat with {phone_number}"),
            ScriptStep(action="wait", wait_ms=3000, description="Wait for chat to load"),

            # Type message
            ScriptStep(action="click", target="footer [title='Add a message'], div[contenteditable='true']", description="Click message input"),
            ScriptStep(action="type", target="footer [title='Add a message'], div[contenteditable='true']", value=message_text, description="Type message"),
            ScriptStep(action="wait", wait_ms=500),

            # Send
            ScriptStep(action="click", target="button[aria-label='Send'], span[aria-label='Send']", description="Click send button"),
            ScriptStep(action="wait", wait_ms=2000, description="Wait for message to send"),

            ScriptStep(action="screenshot", description="Verify message sent"),
        ]

    def _check_unread(self, params: Dict[str, Any]) -> List[ScriptStep]:
        """Check unread messages."""
        return [
            ScriptStep(action="navigate", target="https://web.whatsapp.com/", description="Navigate to WhatsApp Web"),
            ScriptStep(action="wait", wait_ms=3000, description="Wait for page load"),

            ScriptStep(action="screenshot", description="Take screenshot of unread messages"),
        ]
