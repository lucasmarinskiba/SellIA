"""Facebook Messenger Web Platform Script — Browser automation"""

from typing import List, Dict, Any
from .base import PlatformScript, ScriptStep


class FacebookMessengerScript(PlatformScript):
    domain = "messenger.com"
    platform_name = "Facebook Messenger"
    login_url = "https://www.messenger.com/"
    dashboard_url = "https://www.messenger.com/"

    def get_task_steps(self, task_type: str, params: Dict[str, Any]) -> List[ScriptStep]:
        if task_type == "respond_message":
            return self._respond_message(params)
        elif task_type == "send_message":
            return self._send_message(params)
        elif task_type == "check_unread":
            return self._check_unread(params)
        return super().get_task_steps(task_type, params)

    def _respond_message(self, params: Dict[str, Any]) -> List[ScriptStep]:
        """Respond to Facebook Messenger message."""
        customer_name = params.get("customer_name", "")
        response_text = params.get("response_text", "")

        return [
            ScriptStep(action="navigate", target="https://www.messenger.com/", description="Navigate to Facebook Messenger"),
            ScriptStep(action="wait", wait_ms=3000, description="Wait for page load"),

            # Search for contact
            ScriptStep(action="click", target="input[placeholder*='Search'], [role='searchbox']", description="Click search box"),
            ScriptStep(action="type", target="input[placeholder*='Search'], [role='searchbox']", value=customer_name, description=f"Search for {customer_name}"),
            ScriptStep(action="wait", wait_ms=1500, description="Wait for search results"),

            # Click first result
            ScriptStep(action="click", target="[role='option']:first-child", description="Click contact"),
            ScriptStep(action="wait", wait_ms=2000, description="Wait for conversation to load"),

            # Type message
            ScriptStep(action="click", target="[contenteditable='true'], textarea[placeholder*='Aa']", description="Click message input"),
            ScriptStep(action="type", target="[contenteditable='true'], textarea[placeholder*='Aa']", value=response_text, description="Type response message"),
            ScriptStep(action="wait", wait_ms=500),

            # Send message
            ScriptStep(action="click", target="button[aria-label*='Send'], svg[role='img'][aria-label*='Send']", description="Click send button"),
            ScriptStep(action="wait", wait_ms=2000, description="Wait for message to send"),

            ScriptStep(action="screenshot", description="Verify message sent"),
        ]

    def _send_message(self, params: Dict[str, Any]) -> List[ScriptStep]:
        """Send message to specific contact."""
        customer_id = params.get("customer_id", "")
        message_text = params.get("message_text", "")

        return [
            ScriptStep(action="navigate", target=f"https://www.messenger.com/t/{customer_id}", description=f"Open conversation"),
            ScriptStep(action="wait", wait_ms=3000, description="Wait for conversation to load"),

            # Type message
            ScriptStep(action="click", target="[contenteditable='true'], textarea[placeholder*='Aa']", description="Click message input"),
            ScriptStep(action="type", target="[contenteditable='true'], textarea[placeholder*='Aa']", value=message_text, description="Type message"),
            ScriptStep(action="wait", wait_ms=500),

            # Send
            ScriptStep(action="click", target="button[aria-label*='Send'], svg[role='img'][aria-label*='Send']", description="Click send button"),
            ScriptStep(action="wait", wait_ms=2000, description="Wait for message to send"),

            ScriptStep(action="screenshot", description="Verify message sent"),
        ]

    def _check_unread(self, params: Dict[str, Any]) -> List[ScriptStep]:
        """Check unread messages."""
        return [
            ScriptStep(action="navigate", target="https://www.messenger.com/", description="Navigate to Facebook Messenger"),
            ScriptStep(action="wait", wait_ms=3000, description="Wait for page load"),

            ScriptStep(action="screenshot", description="Take screenshot of unread messages"),
        ]
