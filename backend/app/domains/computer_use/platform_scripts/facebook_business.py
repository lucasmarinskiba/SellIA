"""Meta Business Suite / Ads Manager Platform Script"""

from typing import List, Dict, Any
from .base import PlatformScript, ScriptStep


class FacebookBusinessScript(PlatformScript):
    domain = "business.facebook.com"
    platform_name = "Meta Business Suite"
    login_url = "https://business.facebook.com/login"
    dashboard_url = "https://business.facebook.com/"

    def get_task_steps(self, task_type: str, params: Dict[str, Any]) -> List[ScriptStep]:
        if task_type == "create_ad_campaign":
            return self._create_ad_campaign(params)
        elif task_type == "setup_pixel":
            return self._setup_pixel(params)
        elif task_type == "manage_page":
            return self._manage_page(params)
        return super().get_task_steps(task_type, params)

    def _create_ad_campaign(self, params: Dict[str, Any]) -> List[ScriptStep]:
        objective = params.get("objective", "AWARENESS")
        budget = params.get("budget", 10)
        return [
            ScriptStep(action="navigate", target="https://business.facebook.com/adsmanager/creation", description="Navigate to Ads Manager"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target=f"[data-testid='objective-{objective}'], [value='{objective}']", description=f"Select {objective} objective", fallback="[data-testid='objective-AWARENESS']"),
            ScriptStep(action="click", target="button:contains('Continue'), [data-testid='continue-button']", description="Click continue"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="type", target="input[placeholder*='Campaign name'], [data-testid='campaign-name-input']", value=params.get("campaign_name", "SellIA Campaign"), description="Enter campaign name"),
            ScriptStep(action="type", target="input[placeholder*='Budget'], [data-testid='budget-input']", value=str(budget), description=f"Set budget to ${budget}"),
            ScriptStep(action="click", target="button:contains('Publish'), [data-testid='publish-button']", description="Publish campaign", fallback="button[type='submit']"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="screenshot", description="Verify campaign created"),
        ]

    def _setup_pixel(self, params: Dict[str, Any]) -> List[ScriptStep]:
        events = params.get("events", ["PageView", "ViewContent", "AddToCart", "Purchase"])
        return [
            ScriptStep(action="navigate", target="https://business.facebook.com/events_manager", description="Navigate to Events Manager"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target="button:contains('Connect Data Sources'), a:contains('Connect Data Sources')", description="Connect data source", fallback="button"),
            ScriptStep(action="click", target="button:contains('Web'), [aria-label='Web']", description="Select Web"),
            ScriptStep(action="click", target="button:contains('Connect'), button:contains('Next')", description="Continue setup"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="screenshot", description=f"Check pixel setup for events: {', '.join(events)}"),
        ]

    def _manage_page(self, params: Dict[str, Any]) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target="https://business.facebook.com/latest/home", description="Navigate to Business Suite home"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target="a:contains('Create Post'), button:contains('Create Post')", description="Click create post", fallback="button"),
            ScriptStep(action="wait", wait_ms=1500),
            ScriptStep(action="screenshot", description="Check posting interface"),
        ]
