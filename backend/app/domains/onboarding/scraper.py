"""Onboarding Mágico — Scraper con Playwright"""

import re
from typing import Optional
from playwright.async_api import async_playwright
from app.core.logger import get_logger

logger = get_logger(__name__)


class OnboardingScraper:
    """Scrapea Instagram o sitios web para extraer información de negocio."""

    def __init__(self):
        self._playwright = None
        self._browser = None

    async def _start(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
        )

    async def _stop(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    def _is_instagram(self, source: str) -> bool:
        return source.startswith("@") or "instagram.com" in source

    def _build_url(self, source: str) -> str:
        if source.startswith("@"):
            handle = source.lstrip("@")
            return f"https://www.instagram.com/{handle}/"
        if not source.startswith("http"):
            return f"https://{source}"
        return source

    async def scrape(self, source: str, max_chars: int = 8000) -> str:
        """Extrae texto visible de la página."""
        await self._start()
        try:
            context = await self._browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
            )
            page = await context.new_page()
            url = self._build_url(source)

            logger.info(f"Scrapeando onboarding source: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2500)

            # Intentar cerrar popups de cookies comunes
            for btn_text in ["Aceptar", "Accept", "Aceptar todo", "Accept all", "Entendido", "OK"]:
                try:
                    btn = page.locator(f"button:has-text('{btn_text}')").first
                    if await btn.is_visible(timeout=500):
                        await btn.click(timeout=1000)
                        await page.wait_for_timeout(500)
                except Exception:
                    pass

            # Extraer texto visible
            text = await page.evaluate("""
                () => {
                    const scripts = document.querySelectorAll('script, style, nav, footer, iframe');
                    scripts.forEach(el => el.remove());
                    return document.body.innerText;
                }
            """)

            # Limpiar
            text = re.sub(r"\n{3,}", "\n\n", text.strip())
            text = re.sub(r"\s{2,}", " ", text)

            if len(text) > max_chars:
                text = text[:max_chars] + "\n...[truncado]"

            return text
        except Exception as e:
            logger.error(f"Error scrapeando {source}: {e}")
            raise
        finally:
            await self._stop()
