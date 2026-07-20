"""MercadoLibre Platform Script"""

from typing import List, Dict, Any
from .base import PlatformScript, ScriptStep


class MercadoLibreScript(PlatformScript):
    domain = "mercadolibre.com"
    platform_name = "MercadoLibre"
    login_url = "https://www.mercadolibre.com/jms/mla/lgz/login"
    dashboard_url = "https://www.mercadolibre.com.ar/resumen"

    def get_task_steps(self, task_type: str, params: Dict[str, Any]) -> List[ScriptStep]:
        if task_type == "create_listing":
            return self._create_listing(params)
        elif task_type == "respond_questions":
            return self._respond_questions(params)
        elif task_type == "manage_orders":
            return self._manage_orders(params)
        return super().get_task_steps(task_type, params)

    def _create_listing(self, params: Dict[str, Any]) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target="https://www.mercadolibre.com.ar/publicar", description="Navigate to publish page"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="type", target="input[placeholder*='Título'], input[name='title'], [data-testid='title-input']", value=params.get("title", "Producto SellIA"), description="Enter listing title"),
            ScriptStep(action="type", target="textarea[placeholder*='Descripción'], [data-testid='description']", value=params.get("description", ""), description="Enter description"),
            ScriptStep(action="type", target="input[placeholder*='Precio'], input[name='price'], [data-testid='price-input']", value=str(params.get("price", "0")), description="Enter price"),
            ScriptStep(action="click", target="button:contains('Continuar'), button:contains('Publicar')", description="Continue to publish", fallback="button"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="screenshot", description="Verify listing created"),
        ]

    def _respond_questions(self, params: Dict[str, Any]) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target="https://www.mercadolibre.com.ar/preguntas", description="Navigate to questions"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="screenshot", description="Check unanswered questions"),
        ]

    def _manage_orders(self, params: Dict[str, Any]) -> List[ScriptStep]:
        return [
            ScriptStep(action="navigate", target="https://www.mercadolibre.com.ar/ventas", description="Navigate to sales/orders"),
            ScriptStep(action="wait", wait_ms=3000),
            ScriptStep(action="click", target="button:contains('Preparar envío'), a:contains('Preparar envío')", description="Prepare shipping", fallback="button"),
            ScriptStep(action="wait", wait_ms=2000),
            ScriptStep(action="screenshot", description="Check orders status"),
        ]
