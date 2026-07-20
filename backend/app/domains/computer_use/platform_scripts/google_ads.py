"""Google Ads Platform Script"""

from typing import List, Dict, Any
from .base import PlatformScript, ScriptStep


class GoogleAdsScript(PlatformScript):
    domain = "ads.google.com"
    platform_name = "Google Ads"
    login_url = "https://ads.google.com/aw/login"
    dashboard_url = "https://ads.google.com/aw/overview"

    def get_task_steps(self, task_type: str, params: Dict[str, Any]) -> List[ScriptStep]:
        if task_type == "create_search_campaign":
            return self._create_search_campaign(params)
        elif task_type == "setup_conversion_tracking":
            return self._setup_conversion(params)
        elif task_type == "research_keywords":
            return self._research_keywords(params)
        return super().get_task_steps(task_type, params)

    def _create_search_campaign(self, params: Dict[str, Any]) -> List[ScriptStep]:
        budget = params.get("budget_daily", 20)
        return [
            ScriptStep(action="navigate", target="https://ads.google.com/aw/campaigns/new", description="Navigate to new campaign"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target="[data-value='SEARCH'], [aria-label='Search']", description="Select Search campaign"),
            ScriptStep(action="click", target="button:contains('Continue'), [data-testid='continue-button']", description="Click continue"),
            ScriptStep(action="type", target="input[placeholder*='Campaign name'], [data-testid='campaign-name']", value=params.get("campaign_name", "SellIA Search"), description="Enter campaign name"),
            ScriptStep(action="type", target="input[placeholder*='Budget'], [data-testid='budget-input']", value=str(budget), description=f"Set daily budget to ${budget}"),
            ScriptStep(action="click", target="button:contains('Save and continue'), button:contains('Next')", description="Save and continue"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="screenshot", description="Verify campaign setup"),
        ]

    def _setup_conversion(self, params: Dict[str, Any]) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target="https://ads.google.com/aw/conversions", description="Navigate to conversions"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target="button:contains('New conversion action'), a:contains('New conversion action')", description="Add new conversion", fallback="button"),
            ScriptStep(action="click", target="[data-value='WEBSITE'], button:contains('Website')", description="Select website conversion"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="screenshot", description="Check conversion setup"),
        ]

    def _research_keywords(self, params: Dict[str, Any]) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target="https://ads.google.com/aw/keywordplanner", description="Navigate to Keyword Planner"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target="button:contains('Discover new keywords'), a:contains('Discover new keywords')", description="Discover keywords"),
            ScriptStep(action="type", target="textarea[placeholder*='Enter keywords'], input[placeholder*='Enter keywords']", value=params.get("seed_keywords", "producto online"), description="Enter seed keywords"),
            ScriptStep(action="click", target="button:contains('Get results'), button:contains('Search')", description="Get keyword results"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="screenshot", description="Capture keyword ideas"),
        ]
