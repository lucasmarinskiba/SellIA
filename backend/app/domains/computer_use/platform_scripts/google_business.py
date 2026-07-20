"""Google Business Profile Platform Script"""

from typing import List, Dict, Any
from .base import PlatformScript, ScriptStep


class GoogleBusinessScript(PlatformScript):
    domain = "business.google.com"
    platform_name = "Google Business Profile"
    login_url = "https://business.google.com/signin"
    dashboard_url = "https://business.google.com/locations"

    def get_task_steps(self, task_type: str, params: Dict[str, Any]) -> List[ScriptStep]:
        if task_type == "optimize_profile":
            return self._optimize_profile(params)
        elif task_type == "request_reviews":
            return self._request_reviews(params)
        elif task_type == "add_posts":
            return self._add_posts(params)
        elif task_type == "add_local_keywords":
            return self._add_keywords(params)
        return super().get_task_steps(task_type, params)

    def _optimize_profile(self, params: Dict[str, Any]) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target="https://business.google.com/locations", description="Navigate to Google Business locations"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target="a:contains('Edit profile'), button:contains('Edit profile')", description="Edit profile", fallback="button"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="type", target="textarea[placeholder*='Business description'], [data-testid='description']", value=params.get("description", ""), description="Enter business description"),
            ScriptStep(action="click", target="button:contains('Save'), button:contains('Guardar')", description="Save changes", fallback="button"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="screenshot", description="Verify profile updated"),
        ]

    def _request_reviews(self, params: Dict[str, Any]) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target="https://business.google.com/locations", description="Navigate to locations"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target="a:contains('Get more reviews'), button:contains('Get more reviews')", description="Get review link", fallback="button"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="screenshot", description="Capture review request URL"),
        ]

    def _add_posts(self, params: Dict[str, Any]) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target="https://business.google.com/locations", description="Navigate to locations"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target="a:contains('Add update'), button:contains('Add update')", description="Add new post", fallback="button"),
            ScriptStep(action="type", target="textarea[placeholder*='Write a post'], [data-testid='post-text']", value=params.get("text", ""), description="Enter post text"),
            ScriptStep(action="click", target="button:contains('Publish'), button:contains('Publicar')", description="Publish post", fallback="button"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="screenshot", description="Verify post published"),
        ]

    def _add_keywords(self, params: Dict[str, Any]) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target="https://business.google.com/locations", description="Navigate to locations"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target="a:contains('Services'), button:contains('Services')", description="Open services tab", fallback="button"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="click", target="button:contains('Add service'), button:contains('Nuevo servicio')", description="Add service", fallback="button"),
            ScriptStep(action="type", target="input[placeholder*='Service name'], [data-testid='service-name']", value=params.get("service_name", ""), description="Enter service with local keywords"),
            ScriptStep(action="click", target="button:contains('Save'), button:contains('Guardar')", description="Save service", fallback="button"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="screenshot", description="Verify service added"),
        ]
