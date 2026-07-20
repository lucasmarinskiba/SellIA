"""
SellIA ↔ FeedIA Workflow — Abre FeedIA, usa Computer Vision, ejecuta automático.

Flujo:
1. SellIA identifica oportunidad de venta
2. Abre FeedIA en browser via Computer Use
3. Computer Vision analiza interfaz
4. Ejecuta herramientas FeedIA (crear carousel, reel, TikTok)
5. Publica contenido automático
6. Monitorea resultado
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SellIAFeedIAWorkflow:
    """Workflow automatizado: SellIA → abre FeedIA → CV controla → ejecuta."""

    def __init__(self, intelligent_browser_agent, computer_vision_engine):
        self.browser = intelligent_browser_agent
        self.cv = computer_vision_engine

    # ========== MAIN WORKFLOW ==========

    async def create_and_publish_product_content(
        self,
        product: Dict[str, Any],
        account_id: str,
        platforms: List[str],  # ["instagram", "tiktok"]
    ) -> Dict[str, Any]:
        """
        Workflow completo: SellIA → FeedIA → crea contenido → publica.

        platforms: qué redes sociales donde publicar
        """

        logger.info(f"Starting SellIA→FeedIA workflow for product: {product.get('name')}")

        workflow_result = {
            "product_id": product.get("id"),
            "account_id": account_id,
            "platforms": platforms,
            "steps": [],
            "started_at": datetime.utcnow().isoformat(),
        }

        try:
            # PASO 1: Abrir FeedIA
            logger.info("Step 1: Opening FeedIA")
            open_result = await self._open_feedia()
            workflow_result["steps"].append({"step": 1, "action": "open_feedia", "status": open_result["status"]})

            if open_result["status"] != "success":
                return {"status": "error", "error": "Could not open FeedIA"}

            # PASO 2: Navegar a sección de creación de contenido
            logger.info("Step 2: Navigate to content creation")
            nav_result = await self._navigate_content_creation()
            workflow_result["steps"].append({"step": 2, "action": "navigate_content_creation", "status": nav_result["status"]})

            # PASO 3: Crear contenido (carousel/reel/tiktok según platform)
            if "instagram" in platforms:
                logger.info("Step 3a: Creating Instagram carousel")
                carousel_result = await self._create_carousel_on_feedia(product)
                workflow_result["steps"].append({"step": "3a", "action": "create_carousel", "status": carousel_result["status"], "result": carousel_result})

            if "tiktok" in platforms:
                logger.info("Step 3b: Creating TikTok video")
                tiktok_result = await self._create_tiktok_on_feedia(product)
                workflow_result["steps"].append({"step": "3b", "action": "create_tiktok", "status": tiktok_result["status"], "result": tiktok_result})

            # PASO 4: Publicar contenido
            logger.info("Step 4: Publishing content")
            publish_result = await self._publish_content_feedia(platforms)
            workflow_result["steps"].append({"step": 4, "action": "publish_content", "status": publish_result["status"]})

            workflow_result["status"] = "success"
            workflow_result["completed_at"] = datetime.utcnow().isoformat()

            return workflow_result

        except Exception as e:
            logger.error(f"Workflow failed: {str(e)}")
            workflow_result["status"] = "error"
            workflow_result["error"] = str(e)
            return workflow_result

    # ========== STEP IMPLEMENTATIONS ==========

    async def _open_feedia(self) -> Dict[str, Any]:
        """Abre FeedIA en navegador."""

        actions = [
            {"type": "navigate", "params": {"url": "https://feedia.vercel.app"}},
            {"type": "wait_for_selector", "params": {"selector": "button[data-action='create-content']", "timeout": 10000}},
            {"type": "screenshot", "params": {"filename": "feedia_opened.png"}},
        ]

        result = await self.browser.browser.execute_workflow("open_feedia", actions)
        return {"status": "success" if result.get("completed", 0) > 0 else "error"}

    async def _navigate_content_creation(self) -> Dict[str, Any]:
        """Navega a sección de creación de contenido en FeedIA."""

        # Captura screenshot
        screenshot = await self.browser.browser.take_screenshot()

        # CV analiza interfaz
        cv_analysis = await self.cv.analyze_feedia_interface(screenshot)

        if cv_analysis["status"] != "success":
            return {"status": "error"}

        # Detecta botón "crear contenido"
        elements = cv_analysis["analysis"].get("available_actions", [])

        # Busca botón de crear contenido
        create_button = next(
            (e for e in elements if "crear" in e.get("button", "").lower() or "create" in e.get("action", "").lower()),
            None,
        )

        if not create_button:
            logger.warning("Create button not found, trying default selector")
            selector = "button[data-action='create-content']"
        else:
            selector = create_button.get("selector", "button[data-action='create-content']")

        # Clickea botón
        click_actions = [
            {"type": "click", "params": {"selector": selector}},
            {"type": "wait_for_selector", "params": {"selector": "div[data-section='carousel-creator'], div[data-section='reel-creator']", "timeout": 5000}},
            {"type": "screenshot", "params": {"filename": "feedia_create_menu.png"}},
        ]

        result = await self.browser.browser.execute_workflow("navigate_create", click_actions)

        return {"status": "success" if result.get("completed", 0) > 0 else "error"}

    async def _create_carousel_on_feedia(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Crea carrusel en FeedIA via Computer Vision + CV dirección."""

        logger.info("Creating carousel on FeedIA")

        # CV lee interfaz
        screenshot = await self.browser.browser.take_screenshot()
        cv_suggestion = await self.cv.suggest_next_action(screenshot, goal="crear carrusel de producto")

        if cv_suggestion["status"] != "success":
            return {"status": "error"}

        suggestion = cv_suggestion["suggestion"]

        # Sigue instrucción de CV para llegar a carousel creator
        actions = [
            {"type": "click", "params": {"selector": suggestion.get("target", {}).get("selector", "button[data-action='create-carousel']")}},
            {"type": "wait_for_selector", "params": {"selector": "div[data-carousel='editor']", "timeout": 5000}},
            {"type": "screenshot", "params": {"filename": "feedia_carousel_editor.png"}},
        ]

        await self.browser.browser.execute_workflow("navigate_carousel", actions)

        # CV determina qué campos rellenar
        screenshot = await self.browser.browser.take_screenshot()
        cv_analysis = await self.cv.analyze_feedia_interface(screenshot)

        input_fields = cv_analysis["analysis"].get("input_fields", [])

        # Llena campos automáticamente
        fill_actions = []

        for field in input_fields:
            label = field.get("label", "").lower()
            field_type = field.get("type", "text")

            if "titulo" in label or "title" in label:
                fill_actions.append({"type": "fill_form", "params": {"fields": {field.get("selector"): product.get("name")}}})

            elif "descripcion" in label or "description" in label:
                fill_actions.append({"type": "fill_form", "params": {"fields": {field.get("selector"): product.get("description")}}})

            elif "precio" in label or "price" in label:
                fill_actions.append({"type": "fill_form", "params": {"fields": {field.get("selector"): str(product.get("price"))}}})

        # Ejecuta llenado
        if fill_actions:
            await self.browser.browser.execute_workflow("fill_carousel", fill_actions)

        # Clickea botón de guardar/publicar
        screenshot = await self.browser.browser.take_screenshot()
        cv_suggestion = await self.cv.suggest_next_action(screenshot, goal="guardar y publicar carrusel")

        save_actions = [
            {"type": "click", "params": {"selector": cv_suggestion["suggestion"].get("target", {}).get("selector", "button[data-action='save-carousel']")}},
            {"type": "wait_for_selector", "params": {"selector": "div[data-status='success'], div[data-status='published']", "timeout": 5000}},
            {"type": "screenshot", "params": {"filename": "feedia_carousel_saved.png"}},
        ]

        result = await self.browser.browser.execute_workflow("save_carousel", save_actions)

        # Verifica completación
        screenshot = await self.browser.browser.take_screenshot()
        verification = await self.cv.verify_task_completion(screenshot, "carrusel creado")

        return {
            "status": "success" if verification["verification"].get("completed") else "error",
            "verification": verification,
        }

    async def _create_tiktok_on_feedia(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Crea video TikTok en FeedIA via Computer Vision."""

        logger.info("Creating TikTok video on FeedIA")

        # Similar a carousel pero para TikTok
        screenshot = await self.browser.browser.take_screenshot()
        cv_suggestion = await self.cv.suggest_next_action(screenshot, goal="crear video TikTok")

        # Navega a TikTok creator
        actions = [
            {"type": "click", "params": {"selector": cv_suggestion["suggestion"].get("target", {}).get("selector", "button[data-action='create-tiktok']")}},
            {"type": "wait_for_selector", "params": {"selector": "div[data-tiktok='editor']", "timeout": 5000}},
            {"type": "screenshot", "params": {"filename": "feedia_tiktok_editor.png"}},
        ]

        await self.browser.browser.execute_workflow("navigate_tiktok", actions)

        # CV analiza campos
        screenshot = await self.browser.browser.take_screenshot()
        cv_analysis = await self.cv.analyze_feedia_interface(screenshot)

        # Llena automáticamente
        input_fields = cv_analysis["analysis"].get("input_fields", [])

        fill_actions = []
        for field in input_fields:
            label = field.get("label", "").lower()

            if "titulo" in label or "title" in label:
                fill_actions.append({"type": "fill_form", "params": {"fields": {field.get("selector"): f"NUEVO: {product.get('name')} 🔥"}}})

            elif "descripcion" in label or "description" in label:
                fill_actions.append({"type": "fill_form", "params": {"fields": {field.get("selector"): product.get("description")}}})

        if fill_actions:
            await self.browser.browser.execute_workflow("fill_tiktok", fill_actions)

        # Publica
        screenshot = await self.browser.browser.take_screenshot()
        cv_suggestion = await self.cv.suggest_next_action(screenshot, goal="publicar video TikTok")

        publish_actions = [
            {"type": "click", "params": {"selector": cv_suggestion["suggestion"].get("target", {}).get("selector", "button[data-action='publish-tiktok']")}},
            {"type": "wait_for_selector", "params": {"selector": "div[data-status='published']", "timeout": 5000}},
            {"type": "screenshot", "params": {"filename": "feedia_tiktok_published.png"}},
        ]

        result = await self.browser.browser.execute_workflow("publish_tiktok", publish_actions)

        # Verifica
        screenshot = await self.browser.browser.take_screenshot()
        verification = await self.cv.verify_task_completion(screenshot, "video TikTok publicado")

        return {
            "status": "success" if verification["verification"].get("completed") else "error",
            "verification": verification,
        }

    async def _publish_content_feedia(self, platforms: List[str]) -> Dict[str, Any]:
        """Publica contenido a redes sociales desde FeedIA."""

        logger.info(f"Publishing to platforms: {platforms}")

        screenshot = await self.browser.browser.take_screenshot()
        cv_suggestion = await self.cv.suggest_next_action(screenshot, goal="publicar a todas las redes sociales")

        publish_actions = [
            {"type": "click", "params": {"selector": "button[data-action='publish-all']"}},
            {"type": "wait_for_selector", "params": {"selector": "div[data-status='all-published']", "timeout": 10000}},
            {"type": "screenshot", "params": {"filename": "feedia_all_published.png"}},
        ]

        result = await self.browser.browser.execute_workflow("publish_all", publish_actions)

        return {"status": "success" if result.get("completed", 0) > 0 else "error"}
