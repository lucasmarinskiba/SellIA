"""Amazon Seller Central Platform Script"""

from typing import List, Dict, Any
from .base import PlatformScript, ScriptStep


class AmazonScript(PlatformScript):
    domain = "sellercentral.amazon.com"
    platform_name = "Amazon Seller Central"
    login_url = "https://sellercentral.amazon.com/signin"
    dashboard_url = "https://sellercentral.amazon.com/home"

    def get_task_steps(self, task_type: str, params: Dict[str, Any]) -> List[ScriptStep]:
        if task_type == "create_product_listing":
            return self._create_listing(params)
        elif task_type == "manage_inventory":
            return self._manage_inventory(params)
        elif task_type == "respond_to_buyer_messages":
            return self._respond_messages(params)
        return super().get_task_steps(task_type, params)

    def _create_listing(self, params: Dict[str, Any]) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target="https://sellercentral.amazon.com/listing/create", description="Navigate to create listing"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="type", target="input[name='itemName'], [data-testid='item-name']", value=params.get("title", ""), description="Enter product title"),
            ScriptStep(action="type", target="textarea[name='description'], [data-testid='description']", value=params.get("description", ""), description="Enter product description"),
            ScriptStep(action="type", target="input[name='quantity'], [data-testid='quantity']", value=str(params.get("quantity", "1")), description="Enter quantity"),
            ScriptStep(action="click", target="button:contains('Save and finish'), button:contains('Submit')", description="Save listing", fallback="button"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="screenshot", description="Verify listing created"),
        ]

    def _manage_inventory(self, params: Dict[str, Any]) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target="https://sellercentral.amazon.com/inventory", description="Navigate to inventory"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="screenshot", description="Check inventory levels"),
        ]

    def _respond_messages(self, params: Dict[str, Any]) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target="https://sellercentral.amazon.com/messaging", description="Navigate to buyer messages"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="screenshot", description="Check buyer messages"),
        ]
