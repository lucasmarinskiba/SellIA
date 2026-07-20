"""
Computer Use Orchestrator — Gestiona workflows complejos, multi-sitio, multi-acción.

Ejecuta scripts completos (visit sitio1 → action1 → action2 → visit sitio2 → action3, etc).
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ComputerUseOrchestrator:
    """Orquesta workflows Computer Use complejos + tracking + reporting."""

    def __init__(self, browser_agent):
        self.browser_agent = browser_agent
        self.workflow_history = []
        self.current_workflow = None

    # ========== WORKFLOW EXECUTION ==========

    async def execute_workflow(
        self,
        workflow_name: str,
        actions: List[Dict[str, Any]],
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Ejecuta workflow completo (secuencia de acciones).

        Ejemplo workflow:
        [
            {"type": "navigate", "params": {"url": "https://mercadolibre.com"}},
            {"type": "click", "params": {"selector": "a[href*='vender']"}},
            {"type": "fill_form", "params": {"fields": {...}}},
            {"type": "click", "params": {"selector": "button[type='submit']"}},
            {"type": "screenshot", "params": {"filename": "listing_created.png"}},
        ]
        """

        logger.info(f"Starting workflow: {workflow_name}")

        self.current_workflow = {
            "name": workflow_name,
            "started_at": datetime.utcnow().isoformat(),
            "actions": len(actions),
            "completed": 0,
            "failed": 0,
            "results": [],
        }

        for i, action in enumerate(actions):
            logger.info(f"Action {i+1}/{len(actions)}: {action.get('type')}")

            try:
                result = await self.browser_agent.execute_action(action)

                self.current_workflow["results"].append({
                    "action": i + 1,
                    "type": action.get("type"),
                    "status": result.get("status"),
                    "error": result.get("error"),
                })

                if result.get("status") == "success":
                    self.current_workflow["completed"] += 1
                else:
                    self.current_workflow["failed"] += 1
                    logger.warning(f"Action {i+1} failed: {result.get('error')}")

            except Exception as e:
                logger.error(f"Action {i+1} exception: {str(e)}")
                self.current_workflow["failed"] += 1
                self.current_workflow["results"].append({
                    "action": i + 1,
                    "type": action.get("type"),
                    "status": "error",
                    "error": str(e),
                })

                # Si es crítico, parar
                if action.get("critical", False):
                    logger.error(f"Critical action failed, stopping workflow")
                    break

        self.current_workflow["completed_at"] = datetime.utcnow().isoformat()

        # Log workflow
        self.workflow_history.append(self.current_workflow)

        logger.info(
            f"Workflow {workflow_name} completed: {self.current_workflow['completed']}/{len(actions)}"
        )

        return self.current_workflow

    # ========== PREDEFINED WORKFLOWS ==========

    async def list_product_everywhere(
        self,
        product: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Workflow: Publica producto en todas plataformas (paralelo + secuencial).

        Visita MercadoLibre, Shopify, Amazon, eBay, etc.
        Rellena formularios automáticamente.
        """

        actions = [
            # ========== MercadoLibre ==========
            {"type": "navigate", "params": {"url": "https://www.mercadolibre.com.ar"}, "site": "mercadolibre"},
            {"type": "click", "params": {"selector": "a[href*='vender']"}},
            {"type": "fill_form", "params": {"fields": {
                "input[name='titulo']": product.get("name"),
                "input[name='precio']": str(product.get("price")),
                "textarea[name='descripcion']": product.get("description"),
            }}},
            {"type": "click", "params": {"selector": "button[type='submit']"}},
            {"type": "screenshot", "params": {"filename": "mercadolibre_listed.png"}},

            # ========== Shopify (si tiene tienda) ==========
            {"type": "navigate", "params": {"url": "https://admin.shopify.com/products"}},
            {"type": "click", "params": {"selector": "button:has-text('Add product')"}},
            {"type": "fill_form", "params": {"fields": {
                "input[name='title']": product.get("name"),
                "input[name='price']": str(product.get("price")),
            }}},
            {"type": "click", "params": {"selector": "button:has-text('Save')"}},

            # ========== eBay ==========
            {"type": "navigate", "params": {"url": "https://sell.ebay.com/"}},
            {"type": "click", "params": {"selector": "a[href*='create']"}},
            {"type": "fill_form", "params": {"fields": {
                "input[placeholder*='title']": product.get("name"),
                "input[placeholder*='price']": str(product.get("price")),
            }}},
        ]

        return await self.execute_workflow(f"list_product_{product.get('id')}", actions)

    async def send_message_multi_channel(
        self,
        recipient: str,
        message: str,
    ) -> Dict[str, Any]:
        """
        Workflow: Envía mensaje por múltiples canales (WhatsApp, email, LinkedIn, etc).
        """

        actions = [
            # ========== WhatsApp Web ==========
            {"type": "navigate", "params": {"url": "https://web.whatsapp.com"}},
            {"type": "click", "params": {"selector": "span:has-text('Nuevo chat')"}},
            {"type": "fill_form", "params": {"fields": {
                "input[placeholder*='Buscar']": recipient,
            }}},
            {"type": "click", "params": {"selector": f"span:has-text('{recipient}')"}},
            {"type": "fill_form", "params": {"fields": {
                "footer input[aria-label*='Mensaje']": message,
            }}},
            {"type": "keyboard_shortcut", "params": {"shortcut": "Enter"}},
            {"type": "screenshot", "params": {"filename": "whatsapp_sent.png"}},

            # ========== Gmail ==========
            {"type": "navigate", "params": {"url": "https://mail.google.com"}},
            {"type": "click", "params": {"selector": "a:has-text('Redactar')"}},
            {"type": "fill_form", "params": {"fields": {
                "input[aria-label='Para']": recipient,
                "input[aria-label='Asunto']": "Mensaje importante",
                "div[contenteditable='true']": message,
            }}},
            {"type": "keyboard_shortcut", "params": {"shortcut": "Tab+Enter"}},  # Send

            # ========== LinkedIn ==========
            {"type": "navigate", "params": {"url": "https://linkedin.com/messaging"}},
            {"type": "fill_form", "params": {"fields": {
                "input[placeholder*='Buscar']": recipient,
            }}},
            {"type": "click", "params": {"selector": f"button:has-text('{recipient}')"}},
            {"type": "fill_form", "params": {"fields": {
                "div[contenteditable='true']": message,
            }}},
            {"type": "keyboard_shortcut", "params": {"shortcut": "Enter"}},
        ]

        return await self.execute_workflow(f"send_message_to_{recipient}", actions)

    async def complete_sales_funnel(
        self,
        product: Dict[str, Any],
        buyer: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Workflow: Ciclo venta COMPLETO end-to-end (list → message → negotiate → close → deliver).
        """

        actions = []

        # 1. List on MercadoLibre
        actions.extend([
            {"type": "navigate", "params": {"url": "https://mercadolibre.com/vender"}},
            {"type": "fill_form", "params": {"fields": {
                "input[name='titulo']": product.get("name"),
                "input[name='precio']": str(product.get("price")),
            }}},
            {"type": "click", "params": {"selector": "button[type='submit']"}},
            {"type": "screenshot", "params": {"filename": "step1_listed.png"}},
        ])

        # 2. Message buyer on WhatsApp
        actions.extend([
            {"type": "navigate", "params": {"url": "https://web.whatsapp.com"}},
            {"type": "fill_form", "params": {"fields": {
                "input[placeholder*='Buscar']": buyer.get("phone"),
            }}},
            {"type": "fill_form", "params": {"fields": {
                "div[contenteditable='true']": f"Hola! Te interesa {product.get('name')}?",
            }}},
            {"type": "keyboard_shortcut", "params": {"shortcut": "Enter"}},
        ])

        # 3. Send checkout link via WhatsApp
        actions.extend([
            {"type": "fill_form", "params": {"fields": {
                "div[contenteditable='true']": f"Aquí está el link: https://checkout.example.com/{product.get('id')}",
            }}},
            {"type": "keyboard_shortcut", "params": {"shortcut": "Enter"}},
        ])

        # 4. Confirmation screenshot
        actions.extend([
            {"type": "screenshot", "params": {"filename": "step4_confirmed.png"}},
        ])

        return await self.execute_workflow(
            f"complete_funnel_{product.get('id')}_{buyer.get('email')}",
            actions,
        )

    # ========== REPORTING ==========

    def get_workflow_report(self, workflow_name: Optional[str] = None) -> Dict[str, Any]:
        """Retorna reporte de workflows ejecutados."""

        if workflow_name:
            workflows = [w for w in self.workflow_history if w["name"] == workflow_name]
        else:
            workflows = self.workflow_history

        total_workflows = len(workflows)
        total_actions = sum(w.get("actions", 0) for w in workflows)
        successful_actions = sum(w.get("completed", 0) for w in workflows)
        failed_actions = sum(w.get("failed", 0) for w in workflows)

        success_rate = (successful_actions / total_actions * 100) if total_actions > 0 else 0

        return {
            "total_workflows": total_workflows,
            "total_actions": total_actions,
            "successful_actions": successful_actions,
            "failed_actions": failed_actions,
            "success_rate": f"{success_rate:.1f}%",
            "workflows": workflows[-10:],  # Últimas 10
        }
