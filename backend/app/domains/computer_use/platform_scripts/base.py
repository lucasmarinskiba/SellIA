"""Base class for platform-specific Computer Use scripts."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ScriptStep:
    action: str  # navigate, click, type, scroll, screenshot, wait, assert, select
    target: Optional[str] = None  # CSS selector or URL
    value: Optional[str] = None  # text to type
    description: str = ""  # human-readable for LLM
    fallback: Optional[str] = None  # alternative selector
    wait_ms: int = 1000  # milliseconds to wait after step


class PlatformScript:
    """Base class that all platform scripts inherit from."""

    domain: str = ""
    platform_name: str = ""
    login_url: str = ""
    dashboard_url: str = ""

    def get_login_steps(self, username: str, password: str) -> List[ScriptStep]:
        """Steps to log into the platform."""
        return [
            ScriptStep(action="navigate", target=self.login_url, description=f"Navigate to {self.platform_name} login"),
            ScriptStep(action="wait", wait_ms=2000, description="Wait for page to load"),
            ScriptStep(action="type", target="input[type='email'], input[name='email'], input[name='username'], #email", value=username, description="Enter username/email", fallback="input[type='text']"),
            ScriptStep(action="type", target="input[type='password'], input[name='password'], #password", value=password, description="Enter password"),
            ScriptStep(action="click", target="button[type='submit'], button:contains('Log In'), button:contains('Sign In'), .login-button", description="Click login button", fallback="button"),
            ScriptStep(action="wait", wait_ms=3000, description="Wait for login to complete"),
            ScriptStep(action="screenshot", description="Verify login success"),
        ]

    def get_task_steps(self, task_type: str, params: Dict[str, Any]) -> List[ScriptStep]:
        """Override in subclasses for platform-specific tasks."""
        return [ScriptStep(action="navigate", target=self.dashboard_url, description=f"Navigate to {self.platform_name} dashboard")]

    def to_dict(self) -> List[Dict[str, Any]]:
        """Convert steps to serializable dicts."""
        return []
