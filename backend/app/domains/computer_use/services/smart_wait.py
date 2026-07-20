"""Computer Use — Smart Wait

Espera inteligente basada en condiciones del DOM en lugar de sleeps fijos.
Mejora la velocidad y robustez de las sesiones.
"""

import asyncio
from typing import Optional, Callable

from app.core.logger import get_logger

logger = get_logger(__name__)


class SmartWait:
    """Espera inteligente con múltiples estrategias."""

    DEFAULT_TIMEOUT = 10000  # ms
    POLL_INTERVAL = 100  # ms

    async def wait_for_element(
        self,
        page,
        selector: str,
        state: str = "visible",
        timeout: int = DEFAULT_TIMEOUT,
    ) -> bool:
        """Espera a que un elemento esté visible/oculto/enabled."""
        try:
            if state == "visible":
                await page.wait_for_selector(selector, state="visible", timeout=timeout)
            elif state == "hidden":
                await page.wait_for_selector(selector, state="hidden", timeout=timeout)
            elif state == "attached":
                await page.wait_for_selector(selector, state="attached", timeout=timeout)
            elif state == "detached":
                await page.wait_for_selector(selector, state="detached", timeout=timeout)
            return True
        except Exception as e:
            logger.warning(f"SmartWait: element {selector} not {state}: {e}")
            return False

    async def wait_for_navigation(
        self,
        page,
        url_pattern: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> bool:
        """Espera a que ocurra una navegación."""
        try:
            if url_pattern:
                await page.wait_for_url(url_pattern, timeout=timeout)
            else:
                await page.wait_for_load_state("networkidle", timeout=timeout)
            return True
        except Exception as e:
            logger.warning(f"SmartWait: navigation timeout: {e}")
            return False

    async def wait_for_text(
        self,
        page,
        text: str,
        selector: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> bool:
        """Espera a que aparezca un texto en la página."""
        import time
        start = time.time() * 1000
        while (time.time() * 1000 - start) < timeout:
            try:
                if selector:
                    element = await page.query_selector(selector)
                    if element:
                        content = await element.text_content()
                        if content and text in content:
                            return True
                else:
                    content = await page.content()
                    if text in content:
                        return True
            except Exception:
                pass
            await asyncio.sleep(self.POLL_INTERVAL / 1000)
        logger.warning(f"SmartWait: text '{text}' not found")
        return False

    async def wait_for_stable(
        self,
        page,
        stability_duration: float = 500,  # ms
        timeout: int = DEFAULT_TIMEOUT,
    ) -> bool:
        """Espera a que el DOM esté estable (sin cambios por N ms)."""
        import time
        start = time.time() * 1000
        last_html = ""
        stable_since = None

        while (time.time() * 1000 - start) < timeout:
            try:
                current_html = await page.content()
                if current_html == last_html:
                    if stable_since is None:
                        stable_since = time.time() * 1000
                    elif (time.time() * 1000 - stable_since) >= stability_duration:
                        return True
                else:
                    stable_since = None
                    last_html = current_html
            except Exception:
                pass
            await asyncio.sleep(self.POLL_INTERVAL / 1000)

        logger.warning("SmartWait: DOM never stabilized")
        return False

    async def wait_for_request(
        self,
        page,
        url_pattern: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> bool:
        """Espera a que se dispare un request específico."""
        try:
            async with page.expect_request(url_pattern, timeout=timeout):
                pass
            return True
        except Exception as e:
            logger.warning(f"SmartWait: request {url_pattern} not seen: {e}")
            return False

    async def wait_for_console_message(
        self,
        page,
        text_pattern: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> bool:
        """Espera un mensaje en la consola del navegador."""
        try:
            async with page.expect_console_message(
                lambda msg: text_pattern in msg.text, timeout=timeout
            ):
                pass
            return True
        except Exception as e:
            logger.warning(f"SmartWait: console message not seen: {e}")
            return False
