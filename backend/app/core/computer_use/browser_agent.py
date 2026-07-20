"""
Browser automation orchestrator — Computer Use via Playwright/Selenium.

Sistema controla navegador del usuario automáticamente.
Manipula cualquier plataforma (MercadoLibre, Shopify, Meta, etc) vía UI.
No necesita APIs. Escalable infinito.
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class PlatformAction(str, Enum):
    """Acciones en plataformas."""
    NAVIGATE = "navigate"  # Ir a URL
    FILL_FORM = "fill_form"  # Llenar formulario
    CLICK = "click"  # Click botón
    EXTRACT_DATA = "extract_data"  # Scrape datos
    WAIT = "wait"  # Esperar elemento
    SCREENSHOT = "screenshot"  # Captura pantalla


class BrowserAgent:
    """Computer Use agent — Controla navegador."""

    def __init__(self, user_browser_path: Optional[str] = None):
        """
        user_browser_path: ruta ejecutable navegador (chrome, firefox, safari, edge)
        Si None: detectar automáticamente del usuario
        """
        self.browser_path = user_browser_path
        self.browser = None
        self.page = None
        self.action_history: List[Dict[str, Any]] = []

    async def start_browser(self):
        """Inicia navegador del usuario."""
        try:
            from playwright.async_api import async_playwright

            p = await async_playwright().start()

            # Detectar navegador si no especificado
            if not self.browser_path:
                # Intentar Firefox primero (abierto, menos memory)
                try:
                    self.browser = await p.firefox.launch()
                except:
                    # Fallback a Chrome
                    try:
                        self.browser = await p.chromium.launch()
                    except:
                        # Fallback a Safari (macOS)
                        self.browser = await p.webkit.launch()
            else:
                # Usar ruta específica
                self.browser = await p.chromium.launch(executable_path=self.browser_path)

            self.page = await self.browser.new_page()
            logger.info("Browser started successfully")

        except Exception as e:
            logger.error(f"Error starting browser: {str(e)}")
            raise

    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta acción en navegador.

        action: {
            "type": "navigate" | "fill_form" | "click" | "extract_data" | "wait" | "screenshot",
            "params": { ... }
        }
        """

        try:
            action_type = action.get("type", "").upper()

            if action_type == PlatformAction.NAVIGATE.value.upper():
                result = await self._navigate(action["params"])
            elif action_type == PlatformAction.FILL_FORM.value.upper():
                result = await self._fill_form(action["params"])
            elif action_type == PlatformAction.CLICK.value.upper():
                result = await self._click(action["params"])
            elif action_type == PlatformAction.EXTRACT_DATA.value.upper():
                result = await self._extract_data(action["params"])
            elif action_type == PlatformAction.WAIT.value.upper():
                result = await self._wait(action["params"])
            elif action_type == PlatformAction.SCREENSHOT.value.upper():
                result = await self._screenshot(action["params"])
            else:
                result = {"status": "error", "message": f"Unknown action: {action_type}"}

            self.action_history.append({"action": action, "result": result})
            return result

        except Exception as e:
            logger.error(f"Error executing action: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _navigate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navega a URL."""
        url = params.get("url")
        try:
            await self.page.goto(url, timeout=30000)
            logger.info(f"Navigated to {url}")
            return {"status": "success", "url": url}
        except Exception as e:
            logger.error(f"Navigation failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _fill_form(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Llena formulario."""
        fields = params.get("fields", {})  # {"selector": "value", ...}
        try:
            for selector, value in fields.items():
                await self.page.fill(selector, str(value))
                logger.info(f"Filled {selector} with {value}")
            return {"status": "success", "fields_filled": len(fields)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Click en elemento."""
        selector = params.get("selector")
        try:
            await self.page.click(selector)
            await asyncio.sleep(1)  # Esperar a que cargue
            logger.info(f"Clicked {selector}")
            return {"status": "success", "clicked": selector}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _extract_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae datos vía CSS selector."""
        selector = params.get("selector")
        attribute = params.get("attribute", "innerText")  # innerText, href, src, etc
        try:
            elements = await self.page.query_selector_all(selector)
            data = []
            for el in elements:
                if attribute == "innerText":
                    text = await el.inner_text()
                    data.append(text)
                else:
                    attr = await el.get_attribute(attribute)
                    data.append(attr)
            logger.info(f"Extracted {len(data)} elements from {selector}")
            return {"status": "success", "data": data, "count": len(data)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _wait(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Espera a que elemento esté disponible."""
        selector = params.get("selector")
        timeout = params.get("timeout", 10000)  # ms
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            logger.info(f"Element {selector} appeared")
            return {"status": "success", "selector": selector}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Captura pantalla."""
        filename = params.get("filename", "screenshot.png")
        try:
            path = f"/tmp/{filename}"
            await self.page.screenshot(path=path)
            logger.info(f"Screenshot saved: {path}")
            return {"status": "success", "path": path}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def run_automation_script(self, script: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ejecuta secuencia de acciones (guión automático)."""
        logger.info(f"Running automation script with {len(script)} actions")

        results = []
        for i, action in enumerate(script):
            logger.info(f"Action {i+1}/{len(script)}: {action.get('type')}")
            result = await self.execute_action(action)
            results.append(result)

            # Si acción falla, parar
            if result.get("status") == "error":
                logger.error(f"Script stopped at action {i+1}")
                break

        return {
            "status": "completed" if all(r.get("status") == "success" for r in results) else "partial",
            "actions_total": len(script),
            "actions_completed": len(results),
            "results": results,
        }

    async def close(self):
        """Cierra navegador."""
        try:
            if self.browser:
                await self.browser.close()
                logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")
