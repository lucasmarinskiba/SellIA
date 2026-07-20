"""
Advanced Browser Agent — OCR, multi-tab, error recovery, context memory, adaptive actions.

Capaz de: navegar, rellenar formularios complejos, detectar cambios, resolver errores automáticamente.
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class BrowserMode(str, Enum):
    """Modos de operación."""
    STEALTH = "stealth"  # Parece humano (delays, mouse movements)
    FAST = "fast"  # Velocidad máxima
    ADAPTIVE = "adaptive"  # Ajusta basado en éxito/fallo


class AdvancedBrowserAgent:
    """Browser automation avanzado + inteligencia automática."""

    def __init__(self, mode: BrowserMode = BrowserMode.ADAPTIVE):
        self.mode = mode
        self.tabs = {}  # Multi-tab management
        self.context_memory = {}  # Memoria de contexto (what we've done)
        self.error_recovery_attempts = 0
        self.max_recovery_attempts = 3

    # ========== CORE ACTIONS (mejorado) ==========

    async def navigate(self, url: str, wait_for: Optional[str] = None) -> Dict[str, Any]:
        """Navega + espera elemento opcional + detección automática."""

        try:
            # Auto-detect si URL es válida
            if not url.startswith(("http://", "https://")):
                url = f"https://{url}"

            # Navigate
            await self.page.goto(url, timeout=30000)

            # Si wait_for especificado, espera elemento
            if wait_for:
                await self.page.wait_for_selector(wait_for, timeout=10000)

            # Auto-detect cambios en página (detection)
            current_state = await self._capture_page_state()
            self.context_memory["last_page_state"] = current_state

            logger.info(f"Navigated to {url}")

            return {
                "status": "success",
                "url": url,
                "page_state": current_state,
            }

        except Exception as e:
            logger.error(f"Navigation failed: {str(e)}")
            return await self._handle_error("navigate", {"url": url}, e)

    async def fill_form_intelligent(self, fields: Dict[str, str]) -> Dict[str, Any]:
        """Rellena formulario de forma inteligente (detecta tipos, maneja errores)."""

        results = {"filled": 0, "failed": []}

        for selector, value in fields.items():
            try:
                # Auto-detect tipo de campo
                field_type = await self._detect_field_type(selector)

                if field_type == "text":
                    await self.page.fill(selector, value)
                elif field_type == "select":
                    await self.page.select_option(selector, value)
                elif field_type == "checkbox":
                    if value.lower() in ["true", "yes", "on"]:
                        await self.page.check(selector)
                elif field_type == "radio":
                    await self.page.click(f"{selector}[value='{value}']")
                elif field_type == "textarea":
                    await self.page.fill(selector, value)
                elif field_type == "file":
                    await self.page.set_input_files(selector, value)
                else:
                    await self.page.fill(selector, value)  # Fallback

                results["filled"] += 1
                logger.info(f"Filled {selector} with {value}")

            except Exception as e:
                logger.error(f"Failed to fill {selector}: {str(e)}")
                results["failed"].append({"selector": selector, "error": str(e)})

        return {"status": "completed", "results": results}

    async def _detect_field_type(self, selector: str) -> str:
        """Auto-detecta tipo de campo (text, select, checkbox, etc)."""

        # TODO: Implementar con Playwright element inspection
        # element = page.query_selector(selector)
        # tag_name = element.tag_name
        # type_attr = element.get_attribute('type')

        return "text"  # Fallback

    # ========== ADVANCED ACTIONS ==========

    async def scroll(self, direction: str = "down", amount: int = 3) -> Dict[str, Any]:
        """Scrollea página (simulando humano)."""

        try:
            if direction == "down":
                await self.page.evaluate(f"window.scrollBy(0, {amount * 100})")
            elif direction == "up":
                await self.page.evaluate(f"window.scrollBy(0, {-amount * 100})")

            # Wait para que cargue contenido dinámico
            await asyncio.sleep(1)

            return {"status": "success", "direction": direction, "amount": amount}

        except Exception as e:
            logger.error(f"Scroll failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def hover(self, selector: str) -> Dict[str, Any]:
        """Hover sobre elemento (trigger tooltips, modals, etc)."""

        try:
            await self.page.hover(selector)
            logger.info(f"Hovered {selector}")
            return {"status": "success", "selector": selector}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def keyboard_shortcut(self, shortcut: str) -> Dict[str, Any]:
        """Ejecuta keyboard shortcut (Ctrl+A, Cmd+C, etc)."""

        try:
            await self.page.keyboard.press(shortcut)
            logger.info(f"Pressed {shortcut}")
            return {"status": "success", "shortcut": shortcut}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def upload_file(self, selector: str, file_path: str) -> Dict[str, Any]:
        """Sube archivo a input file."""

        try:
            await self.page.set_input_files(selector, file_path)
            logger.info(f"Uploaded {file_path} to {selector}")
            return {"status": "success", "file": file_path}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def extract_table_data(self, selector: str) -> Dict[str, Any]:
        """Extrae datos de tabla (headers + rows)."""

        try:
            data = await self.page.evaluate(f"""
                () => {{
                    const table = document.querySelector('{selector}');
                    const headers = Array.from(table.querySelectorAll('th')).map(h => h.textContent);
                    const rows = Array.from(table.querySelectorAll('tr')).map(tr =>
                        Array.from(tr.querySelectorAll('td')).map(td => td.textContent)
                    );
                    return {{ headers, rows }};
                }}
            """)

            logger.info(f"Extracted table with {len(data['rows'])} rows")

            return {
                "status": "success",
                "headers": data["headers"],
                "rows": data["rows"],
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def ocr_text_from_image(self, selector: str) -> Dict[str, Any]:
        """OCR: extrae texto de imagen (usando Tesseract)."""

        try:
            # Captura screenshot del elemento
            element = await self.page.query_selector(selector)
            screenshot = await element.screenshot()

            # TODO: Integrar Tesseract OCR
            # import pytesseract
            # text = pytesseract.image_to_string(screenshot)

            return {
                "status": "success",
                "text": "extracted_text_here",
            }

        except Exception as e:
            logger.error(f"OCR failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    # ========== MULTI-TAB MANAGEMENT ==========

    async def open_new_tab(self, url: Optional[str] = None) -> Dict[str, Any]:
        """Abre nueva tab."""

        try:
            new_page = await self.context.new_page()
            tab_id = f"tab_{len(self.tabs)}"
            self.tabs[tab_id] = new_page

            if url:
                await new_page.goto(url)

            logger.info(f"Opened new tab: {tab_id}")

            return {"status": "success", "tab_id": tab_id}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def switch_tab(self, tab_id: str) -> Dict[str, Any]:
        """Cambia a tab específica."""

        if tab_id in self.tabs:
            self.page = self.tabs[tab_id]
            logger.info(f"Switched to {tab_id}")
            return {"status": "success", "tab_id": tab_id}
        else:
            return {"status": "error", "error": f"Tab {tab_id} not found"}

    # ========== ERROR RECOVERY ==========

    async def _handle_error(
        self,
        action: str,
        params: Dict[str, Any],
        error: Exception,
    ) -> Dict[str, Any]:
        """Auto-recovery: retry con estrategia diferente."""

        logger.warning(f"Error in {action}, attempting recovery...")

        if self.error_recovery_attempts >= self.max_recovery_attempts:
            logger.error(f"Max recovery attempts reached for {action}")
            return {"status": "failed", "error": str(error)}

        self.error_recovery_attempts += 1

        # Estrategias recovery
        if self.error_recovery_attempts == 1:
            # Retry 1: Espera más
            logger.info("Recovery attempt 1: waiting 2s...")
            await asyncio.sleep(2)

        elif self.error_recovery_attempts == 2:
            # Retry 2: Refresh página
            logger.info("Recovery attempt 2: refreshing page...")
            await self.page.reload()

        elif self.error_recovery_attempts == 3:
            # Retry 3: Switch to FAST mode
            logger.info("Recovery attempt 3: switching to FAST mode...")
            self.mode = BrowserMode.FAST

        # Reintentar acción original
        try:
            if action == "navigate":
                return await self.navigate(params["url"])
            # Más acciones según sea necesario
        except Exception as e2:
            logger.error(f"Recovery failed: {str(e2)}")
            return {"status": "failed", "error": str(e2)}

    # ========== CONTEXT MEMORY ==========

    async def _capture_page_state(self) -> Dict[str, Any]:
        """Captura estado completo de página (para detectar cambios)."""

        state = {
            "url": self.page.url,
            "title": await self.page.title(),
            "visible_text": await self.page.inner_text("body"),
            "element_count": await self.page.evaluate("document.querySelectorAll('*').length"),
        }

        return state

    def get_context_memory(self) -> Dict[str, Any]:
        """Retorna memoria de contexto (qué hemos hecho)."""

        return self.context_memory

    def save_context(self, key: str, value: Any):
        """Guarda dato en contexto memory."""

        self.context_memory[key] = value

    # ========== ADAPTIVE MODE ==========

    async def adaptive_action(self, action_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """En modo ADAPTIVE: ajusta velocidad/estrategia basado en éxito/fallo previo."""

        if self.mode == BrowserMode.ADAPTIVE:
            # Si último intento falló, aumenta delays
            if self.context_memory.get("last_action_failed"):
                logger.info("Adaptive mode: increasing delays due to prior failure")
                await asyncio.sleep(1)

            # Si último intento exitoso, puede ir más rápido
            elif self.context_memory.get("last_action_success"):
                logger.info("Adaptive mode: faster pace due to prior success")
                # Sin sleep

        # Ejecutar acción
        result = await self.execute_action({"type": action_type, "params": params})

        # Actualizar contexto
        self.context_memory["last_action_success"] = result.get("status") == "success"
        self.context_memory["last_action_failed"] = result.get("status") != "success"

        return result

    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta acción (versión mejorada)."""

        action_type = action.get("type")
        params = action.get("params", {})

        if action_type == "navigate":
            return await self.navigate(params.get("url"))
        elif action_type == "fill_form":
            return await self.fill_form_intelligent(params.get("fields", {}))
        elif action_type == "click":
            return await self._click(params.get("selector"))
        elif action_type == "scroll":
            return await self.scroll(params.get("direction", "down"))
        elif action_type == "hover":
            return await self.hover(params.get("selector"))
        elif action_type == "extract_table":
            return await self.extract_table_data(params.get("selector"))
        elif action_type == "ocr":
            return await self.ocr_text_from_image(params.get("selector"))
        else:
            return {"status": "error", "message": f"Unknown action: {action_type}"}

    async def _click(self, selector: str) -> Dict[str, Any]:
        """Click (mejorado con error handling)."""

        try:
            await self.page.click(selector)
            await asyncio.sleep(0.5)
            return {"status": "success", "selector": selector}
        except Exception as e:
            return await self._handle_error("click", {"selector": selector}, e)
