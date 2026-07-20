"""Shopify Admin Platform Script"""

from typing import List, Dict, Any
from .base import PlatformScript, ScriptStep


class ShopifyScript(PlatformScript):
    domain = "myshopify.com"
    platform_name = "Shopify"
    login_url = "https://accounts.shopify.com/store-login"
    dashboard_url = "https://admin.shopify.com/"

    def get_task_steps(self, task_type: str, params: Dict[str, Any]) -> List[ScriptStep]:
        store = params.get("store_domain", "")
        base = f"https://admin.shopify.com/store/{store.replace('.myshopify.com', '')}" if store else self.dashboard_url
        if task_type == "add_product":
            return self._add_product(params, base)
        elif task_type == "configure_shipping_zones":
            return self._configure_shipping(params, base)
        elif task_type == "setup_payment_gateway":
            return self._setup_payments(params, base)
        elif task_type == "edit_theme":
            return self._edit_theme(params, base)
        return super().get_task_steps(task_type, params)

    def _add_product(self, params: Dict[str, Any], base: str) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target=f"{base}/products/new", description="Navigate to new product page"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="type", target="input[name='product[title]'], [data-testid='product-title']", value=params.get("title", "New Product"), description="Enter product title"),
            ScriptStep(action="type", target="textarea[name='product[body_html]'], [data-testid='product-description']", value=params.get("description", ""), description="Enter product description"),
            ScriptStep(action="type", target="input[name='product[variants][0][price]'], [data-testid='product-price']", value=str(params.get("price", "0.00")), description="Enter product price"),
            ScriptStep(action="click", target="button:contains('Save'), [data-testid='save-button']", description="Save product", fallback="button[type='submit']"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="screenshot", description="Verify product saved"),
        ]

    def _configure_shipping(self, params: Dict[str, Any], base: str) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target=f"{base}/settings/shipping", description="Navigate to shipping settings"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target="button:contains('Manage rates'), a:contains('Manage rates')", description="Manage shipping rates"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="screenshot", description="Check shipping zones"),
        ]

    def _setup_payments(self, params: Dict[str, Any], base: str) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target=f"{base}/settings/payments", description="Navigate to payments settings"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target="button:contains('Activate'), a:contains('Activate')", description="Activate payment provider", fallback="button"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="screenshot", description="Check payment setup"),
        ]

    def _edit_theme(self, params: Dict[str, Any], base: str) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target=f"{base}/themes", description="Navigate to themes"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target="button:contains('Customize'), a:contains('Customize')", description="Click customize theme"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="screenshot", description="Check theme editor"),
        ]
