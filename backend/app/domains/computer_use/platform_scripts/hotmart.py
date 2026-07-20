"""Hotmart Platform Script"""

from typing import List, Dict, Any
from .base import PlatformScript, ScriptStep


class HotmartScript(PlatformScript):
    domain = "hotmart.com"
    platform_name = "Hotmart"
    login_url = "https://app.hotmart.com/login"
    dashboard_url = "https://app.hotmart.com/dashboard"

    def get_task_steps(self, task_type: str, params: Dict[str, Any]) -> List[ScriptStep]:
        if task_type == "create_product":
            return self._create_product(params)
        elif task_type == "configure_affiliates":
            return self._configure_affiliates(params)
        elif task_type == "setup_sales_page":
            return self._setup_sales_page(params)
        return super().get_task_steps(task_type, params)

    def _create_product(self, params: Dict[str, Any]) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target="https://app.hotmart.com/products/create", description="Navigate to create product"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="type", target="input[name='name'], [data-testid='product-name']", value=params.get("name", "Producto SellIA"), description="Enter product name"),
            ScriptStep(action="type", target="textarea[name='description'], [data-testid='product-description']", value=params.get("description", ""), description="Enter description"),
            ScriptStep(action="type", target="input[name='price'], [data-testid='product-price']", value=str(params.get("price", "0")), description="Enter price"),
            ScriptStep(action="click", target="button:contains('Crear'), button:contains('Salvar')", description="Create product", fallback="button"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="screenshot", description="Verify product created"),
        ]

    def _configure_affiliates(self, params: Dict[str, Any]) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target="https://app.hotmart.com/affiliates", description="Navigate to affiliates"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target="button:contains('Configurar'), a:contains('Configurar')", description="Configure affiliate program", fallback="button"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="screenshot", description="Check affiliate settings"),
        ]

    def _setup_sales_page(self, params: Dict[str, Any]) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target="https://app.hotmart.com/pages", description="Navigate to sales pages"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target="button:contains('Nova página'), a:contains('Nova página')", description="Create new sales page", fallback="button"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="screenshot", description="Check page builder"),
        ]
