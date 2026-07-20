"""Instagram Business Platform Script"""

from typing import List, Dict, Any
from .base import PlatformScript, ScriptStep


class InstagramScript(PlatformScript):
    domain = "instagram.com"
    platform_name = "Instagram"
    login_url = "https://www.instagram.com/accounts/login/"
    dashboard_url = "https://www.instagram.com/"

    def get_task_steps(self, task_type: str, params: Dict[str, Any]) -> List[ScriptStep]:
        if task_type == "optimize_profile":
            return self._optimize_profile(params)
        elif task_type == "connect_shopping":
            return self._connect_shopping(params)
        elif task_type == "schedule_posts":
            return self._schedule_posts(params)
        elif task_type == "respond_dms":
            return self._respond_dms(params)
        elif task_type == "publish_post":
            return self._publish_post(params)
        return super().get_task_steps(task_type, params)

    def _optimize_profile(self, params: Dict[str, Any]) -> List[ScriptStep]:
        bio = params.get("bio", "")
        link = params.get("link", "")
        return [
            ScriptStep(action="navigate", target="https://www.instagram.com/accounts/edit/", description="Navigate to profile edit"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="click", target="textarea[name='biography'], [aria-label='Bio']", description="Click bio field", fallback="textarea"),
            ScriptStep(action="type", target="textarea[name='biography'], [aria-label='Bio']", value=bio, description="Enter new bio text"),
            ScriptStep(action="click", target="input[name='external_url'], [aria-label='Website']", description="Click website field"),
            ScriptStep(action="type", target="input[name='external_url'], [aria-label='Website']", value=link, description="Enter website link"),
            ScriptStep(action="click", target="button:contains('Submit'), button[type='submit']", description="Save profile changes", fallback="button"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="screenshot", description="Verify profile updated"),
        ]

    def _connect_shopping(self, params: Dict[str, Any]) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target="https://business.facebook.com/commerce", description="Navigate to Meta Commerce Manager"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target="a:contains('Get Started'), button:contains('Get Started')", description="Start shop setup", fallback="button"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="screenshot", description="Check shop setup state"),
        ]

    def _schedule_posts(self, params: Dict[str, Any]) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target="https://business.facebook.com/creatorstudio", description="Navigate to Creator Studio"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target="a:contains('Instagram'), [aria-label='Instagram']", description="Select Instagram tab"),
            ScriptStep(action="click", target="button:contains('Create Post'), button:contains('New Post')", description="Click create post"),
            ScriptStep(action="wait", wait_ms=1500),
        ]

    def _respond_dms(self, params: Dict[str, Any]) -> List[ScriptStep]:
        """Respond to Instagram DM."""
        customer_username = params.get("customer_username", "")
        response_text = params.get("response_text", "")

        return [
            ScriptStep(action="navigate", target="https://www.instagram.com/direct/inbox/", description="Navigate to DM inbox"),
            ScriptStep(action="wait", wait_ms=3000, description="Wait for inbox to load"),

            # Search for conversation (if needed)
            if customer_username else None,
            ScriptStep(action="click", target="input[placeholder*='Search'], [role='searchbox']", description="Click search box") if customer_username else None,
            ScriptStep(action="type", target="input[placeholder*='Search'], [role='searchbox']", value=customer_username, description=f"Search for {customer_username}") if customer_username else None,
            ScriptStep(action="wait", wait_ms=1500, description="Wait for search results") if customer_username else None,

            # Click first conversation
            ScriptStep(action="click", target="div[role='listitem']:first-child, a[href*='/direct/t/']", description="Click conversation"),
            ScriptStep(action="wait", wait_ms=2000, description="Wait for DM to open"),

            # Click message input
            ScriptStep(action="click", target="textarea[aria-label*='Message'], div[contenteditable='true']", description="Click message input"),
            ScriptStep(action="type", target="textarea[aria-label*='Message'], div[contenteditable='true']", value=response_text, description="Type response message"),
            ScriptStep(action="wait", wait_ms=500),

            # Send message
            ScriptStep(action="click", target="button[aria-label*='Send'], svg[aria-label*='Send']", description="Click send button"),
            ScriptStep(action="wait", wait_ms=2000, description="Wait for message to send"),

            ScriptStep(action="screenshot", description="Verify message sent"),
        ]

    def _publish_post(self, params: Dict[str, Any]) -> List[ScriptStep]:
        caption = params.get("caption", "")
        return [
            ScriptStep(action="navigate", target="https://www.instagram.com/", description="Navigate to Instagram"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="click", target="[aria-label='New post'], svg[aria-label='New post']", description="Click new post button"),
            ScriptStep(action="wait", wait_ms=1500),
            ScriptStep(action="click", target="button:contains('Select from computer')", description="Click select from computer"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="click", target="[aria-label='Next'], button:contains('Next')", description="Click next"),
            ScriptStep(action="wait", wait_ms=1500),
            ScriptStep(action="type", target="textarea[placeholder*='Write a caption'], [aria-label='Write a caption']", value=caption, description="Enter caption"),
            ScriptStep(action="click", target="[aria-label='Share'], button:contains('Share')", description="Click share"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="screenshot", description="Verify post published"),
        ]
