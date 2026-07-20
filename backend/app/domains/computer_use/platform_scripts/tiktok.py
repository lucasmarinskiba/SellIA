"""TikTok Business / Ads / Shop Platform Script"""

from typing import List, Dict, Any
from .base import PlatformScript, ScriptStep


class TikTokScript(PlatformScript):
    domain = "tiktok.com"
    platform_name = "TikTok"
    login_url = "https://www.tiktok.com/login"
    dashboard_url = "https://www.tiktok.com/business"

    def get_task_steps(self, task_type: str, params: Dict[str, Any]) -> List[ScriptStep]:
        if task_type == "setup_business_account":
            return self._setup_business(params)
        elif task_type == "create_tiktok_campaign":
            return self._create_campaign(params)
        elif task_type == "connect_tiktok_shop":
            return self._connect_shop(params)
        elif task_type == "schedule_videos":
            return self._schedule_videos(params)
        return super().get_task_steps(task_type, params)

    def _setup_business(self, params: Dict[str, Any]) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target="https://www.tiktok.com/business", description="Navigate to TikTok for Business"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target="button:contains('Get Started'), a:contains('Get Started')", description="Start business setup", fallback="button"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="screenshot", description="Check business account setup state"),
        ]

    def _create_campaign(self, params: Dict[str, Any]) -> List[ScriptStep]:
        objective = params.get("objective", "CONVERSIONS")
        budget = params.get("budget", 30)
        return [
            ScriptStep(action="navigate", target="https://ads.tiktok.com/i18n/home", description="Navigate to TikTok Ads"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target="button:contains('Create'), a:contains('Create Campaign')", description="Create new campaign"),
            ScriptStep(action="click", target=f"[data-value='{objective}'], [aria-label='{objective}']", description=f"Select {objective} objective"),
            ScriptStep(action="click", target="button:contains('Continue'), button:contains('Next')", description="Continue"),
            ScriptStep(action="type", target="input[placeholder*='Campaign name'], [data-testid='campaign-name']", value=params.get("campaign_name", "SellIA TikTok"), description="Enter campaign name"),
            ScriptStep(action="type", target="input[placeholder*='Budget'], [data-testid='budget']", value=str(budget), description=f"Set budget to ${budget}"),
            ScriptStep(action="click", target="button:contains('Submit'), button:contains('Launch')", description="Launch campaign", fallback="button"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="screenshot", description="Verify campaign created"),
        ]

    def _connect_shop(self, params: Dict[str, Any]) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target="https://seller.tiktok.com/", description="Navigate to TikTok Seller Center"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target="button:contains('Sign Up'), a:contains('Get Started')", description="Start seller registration", fallback="button"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="screenshot", description="Check TikTok Shop setup"),
        ]

    def _schedule_videos(self, params: Dict[str, Any]) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target="https://www.tiktok.com/creator-center/content", description="Navigate to Creator Center"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target="button:contains('Upload'), a:contains('Upload')", description="Click upload"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="screenshot", description="Check upload interface"),
        ]
